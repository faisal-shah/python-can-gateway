#!/usr/bin/env -S python3

import asyncio
import can
import logging

log = logging.getLogger(__name__)


def rx_loop_gen(rx_bus, tx_busses):
    async def loop():
        reader = can.AsyncBufferedReader()
        loop = asyncio.get_running_loop()
        notifier = can.Notifier(rx_bus, [reader], loop=loop)
        async for msg in reader:
            for bus in tx_busses:
                bus.send(msg)

    return loop


async def run(configs):
    if len(configs) < 2:
        log.critical(f"Not enough devices specified ({len(configs)}), minimum 2 needed")
        return

    busses = []
    for cfg in configs:
        busses.append(can.Bus(**cfg))

    coroutines = []
    for i in range(0, len(busses)):
        l = rx_loop_gen(busses[i], [bus for ii, bus in enumerate(busses) if ii != i])
        coroutines.append(l())

    await asyncio.gather(*coroutines)


if __name__ == "__main__":
    import argparse
    import textwrap
    import json

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """\
        CAN gateway using python-can

        The config file (JSON) is expected to be an array of
        dictionaries - each of which represents one python-can
        bus. Each dictionary will be passed to the Bus
        constructor like so: can.Bus(**dict) .
        """
        ),
    )
    parser.add_argument("config")
    args = parser.parse_args()

    configs = None
    with open(args.config, "r") as f:
        configs = json.load(f)

    try:
        log.info("Starting Gateway")
        asyncio.run(run(configs))
    except KeyboardInterrupt:
        pass

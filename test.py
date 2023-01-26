#!/usr/bin/env -S python

import asyncio
import can

async def rx_loop_gen (bus1, bus2):
    async def loop():
        reader = can.AsyncBufferedReader()
        loop = asyncio.get_running_loop()
        notifier = can.Notifier(bus1, [reader], loop=loop)
        async for msg in reader:
            print(f"id:{msg.arbitration_id:x}, ext={msg.is_extended_id}")
            bus2.send(msg)

    return loop


async def main():
    import argparse
    parser = argparse.ArgumentParser(description='python-can to socketcand bridge')
    parser.add_argument('-i', '--interface', required=False, default='socketcan')
    parser.add_argument('-c', '--channel', required=False, default='vcan1')
    parser.add_argument('-a', '--addr', required=False, default = 'localhost')
    parser.add_argument('-p', '--port', required=False, default = 29536)
    args = parser.parse_args()

    bus_pycan = can.Bus(interface=args.interface, channel=args.channel)
    bus_socketcand = can.Bus(interface='socketcand', host=args.addr, port = args.port, channel='vcan0')

    l1 = await rx_loop_gen(bus_pycan, bus_socketcand)
    l2 = await rx_loop_gen(bus_socketcand, bus_pycan)

    await asyncio.gather(l1(), l2())

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

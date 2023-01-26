#!/usr/bin/env -S python

import asyncio
import can

def openstr(dev):
    return f"< open {dev} >"


def rawmodestr():
    return '< rawmode >'


def parse_incomming(new, acc):
    acc = acc + new
    responses = []

    while True:
        start = acc.find('<')

        if start == -1:
            acc = ''
            break

        acc = acc[start:]

        end = acc.find('>')
        if end == -1:
            break

        resp = acc[:end+1]
        acc = acc[end+1:]
        if len(resp) < 5:
            continue
        responses.append(resp)

    return acc, responses


def decode_resp(resp):
    ret = {'type': 'socketcand'}

    resp = resp[1:-1].strip()
    split = resp.split(' ')

    if len(split) < 1:
        ret['cmd'] = 'NONE'
        return ret

    if split[0] == 'hi':
        ret['cmd'] = 'HI'
    elif split[0] == 'ok':
        ret['cmd'] = 'OK'
    elif split[0] == 'frame':
        ret['cmd'] = 'FRAME'
        ret['id'] = split[1]
        ret['timestamp'] = split[2]
        datastr = split[3]
        ret['data'] = [int(datastr[i*2:i*2+2], 16) for i in range(0,int(len(datastr)/2))]

    return ret

def kvaser_tx(bus, event):
    arbitration_id = int(event['id'], 16)
    is_extended_id = arbitration_id > 0xFFF
    data = event['data']
    msg = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=is_extended_id)
    bus.send(msg)


async def socketcand_recv(reader, bus):
    accumulator = ''
    try:
        while True:
            inbytes = await reader.readuntil(b'>')
            instr = inbytes.decode('utf-8')
            accumulator, resp = parse_incomming(instr, accumulator)
            for r in resp:
                event = decode_resp(r)
                if event['cmd'] == 'FRAME':
                    kvaser_tx(bus, event)
    except KeyboardInterrupt:
        pass


async def socketcand_init_statemachine(state, writer, event):
    if state == 'START':
        if event['cmd'] == 'HI':
            writer.write(openstr('vcan0').encode('utf-8'))
            await writer.drain()
            state = 'WAIT_ACK_OPEN'
    elif state == 'WAIT_ACK_OPEN':
        if event['cmd'] == 'OK':
            writer.write(rawmodestr().encode('utf-8'))
            await writer.drain()
            state = 'WAIT_ACK_RAWMODE'
    elif state == 'WAIT_ACK_RAWMODE':
        if event['cmd'] == 'OK':
            state = 'DONE'

    return state

async def socketcand_init(reader, writer):
    accumulator = ''
    state_socketcand = 'START'
    try:
        while True:
            inbytes = await reader.readuntil(b'>')
            instr = inbytes.decode('utf-8')
            accumulator, resp = parse_incomming(instr, accumulator)
            for r in resp:
                event = decode_resp(r)
                state_socketcand = await socketcand_init_statemachine(state_socketcand, writer, event)
                print(state_socketcand)
                if state_socketcand == 'DONE':
                    raise StopIteration
    except StopIteration:
        pass


async def socketcand_client(reader, writer, bus):
    await socketcand_init(reader, writer)
    await socketcand_recv(reader, bus)


async def socketcand_tx(writer, frame):
    if frame['is_extended_id']:
        idstr = f"{frame['id']:08x}"
    else:
        idstr = f"{frame['id']:x}"

    out_str = '< send '
    out_str = out_str + ' '.join([idstr, str(len(frame['data'])), ' '.join([f"{i:02X}" for i in frame['data']])])
    out_str = out_str + ' >'
    writer.write(out_str.encode('utf-8'))
    await writer.drain()


async def kvaser_client(bus, writer):
    reader = can.AsyncBufferedReader()
    loop = asyncio.get_running_loop()
    notifier = can.Notifier(bus, [reader], loop=loop)
    async for msg in reader:
        tx_msg = {}
        tx_msg['id'] = msg.arbitration_id
        tx_msg['data'] = msg.data
        tx_msg['is_extended_id'] = msg.is_extended_id
        await socketcand_tx(writer, tx_msg)


async def main():
    import argparse
    parser = argparse.ArgumentParser(description='socketcand client')
    parser.add_argument('-a', '--addr', required=False, default = 'localhost')
    parser.add_argument('-p', '--port', required=False, default = 29536)
    parser.add_argument('-c', '--channel', required=False, default=0)
    args = parser.parse_args()

    reader,writer = await asyncio.open_connection(args.addr, args.port)
    bus = can.Bus(interface='kvaser', channel=args.channel, accept_virtual=True, single_handle=True)

    await asyncio.gather(socketcand_client(reader, writer, bus), kvaser_client(bus, writer))


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

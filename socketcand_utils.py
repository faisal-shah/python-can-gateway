#!/usr/bin/env -S python3

import socket
import select
import logging
import xml.etree.ElementTree as ET
import urllib.parse as urlparselib

log = logging.getLogger(__name__)

DEFAULT_SOCKETCAND_PORT = 42000


def detect(port=DEFAULT_SOCKETCAND_PORT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", port))
    log.info(f"Listening to port {port} on all interfaces")

    while True:
        try:
            # get all sockets that are ready (can be a list with a single value
            # being self.socket or an empty list if self.socket is not ready)
            ready_receive_sockets, _, _ = select.select([sock], [], [], 1)

            if not ready_receive_sockets:
                log.info("No advertisement received")
                continue

            msg = sock.recv(1024).decode("utf-8")
            root = ET.fromstring(msg)
            if root.tag != "CANBeacon":
                log.debug("Unexpected message received over UDP")
                continue

            det_devs = []
            det_host = None
            det_port = None
            for child in root:
                if child.tag == "Bus":
                    bus_name = child.attrib["name"]
                    det_devs.append(bus_name)
                elif child.tag == "URL":
                    url = urlparselib.urlparse(child.text)
                    det_host = url.hostname
                    det_port = url.port

            if not det_devs:
                log.info(
                    "Got advertisement, but no SocketCAN devices advertised by socketcand"
                )
                continue

            if (det_host is None) or (det_port is None):
                det_host = None
                det_port = None
                log.info(
                    "Got advertisement, but no SocketCAN URL advertised by socketcand"
                )
                continue

            log.debug(f"Found SocketCAN devices: {det_devs}")

            break

        except ET.ParseError as exc:
            log.debug("Unexpected message received over UDP")
            continue

        except Exception as exc:
            log.critical("Likely failed to recv")
            raise exc.with_traceback(exc.__traceback__)

    return det_devs, det_host, det_port


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Detect socketcand broadcasts")
    parser.add_argument("-log", "--loglevel", required=False, default="info")
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel.upper())

    devs, host, port = detect()
    if not (devs and host and port):
        log.warning("socketcand not detected")
        sys.exit(1)

    if args.device not in devs:
        log.info(f"Requested device ({args.device}) not found in advertised devices")
        sys.exit(1)

    logstr = f"Devices detected: {devs} @ {host}:{port}"
    log.info(logstr)
    print(logstr)

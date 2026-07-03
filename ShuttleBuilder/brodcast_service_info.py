import os
import signal
import socket
import time
from urllib.parse import urlparse

from zeroconf import ServiceInfo, Zeroconf



def get_primary_ipv4():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(("8.8.8.8", 80))
        return f"http://{sock.getsockname()[0]}:8000/"


def main():
    url = os.environ.get("PUBLIC_IP_URL", get_primary_ipv4())

    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port
    should_stop = False

    def stop(_signum, _frame):
        nonlocal should_stop
        should_stop = True

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    zeroconf = Zeroconf(interfaces=[host])
    service_type = "_myapp._tcp.local."
    info = ServiceInfo(
        service_type,
        f"ShuttleBuilder.{service_type}",
        addresses=[socket.inet_aton(host)],
        port=port,
        properties={},
    )

    try:
        zeroconf.register_service(info, allow_name_change=True)
        print(f"Broadcasting {info.name} at {host}:{port}")
        while not should_stop:
            time.sleep(0.2)
    finally:
        zeroconf.unregister_service(info)
        zeroconf.close()
        print("Broadcast stopped")


if __name__ == "__main__":
    main()

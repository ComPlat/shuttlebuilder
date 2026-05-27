import socket
import ipaddress
import concurrent.futures

SUBNET = "192.168.178.0/24"

def check_host(ip):
    ip = str(ip)

    ports = [5985, 5986]  # WinRM HTTP/HTTPS

    for port in ports:
        try:
            sock = socket.create_connection(
                (ip, port),
                timeout=0.5
            )
            sock.close()

            return f"{ip} -> WinRM port {port} open"

        except:
            pass

    return None


def main():
    network = ipaddress.ip_network(SUBNET)

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        results = executor.map(check_host, network.hosts())

    for result in results:
        if result:
            print(result)


if __name__ == "__main__":
    main()
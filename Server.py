import threading
import time
import struct
import sys
import random
import socket

stdout_lock = threading.Lock()

class SpeedTestServer:
    MAGIC_COOKIE = 0xabcddcba
    TYPE_OFFER = 0x2
    TYPE_REQUEST = 0x3
    TYPE_PAYLOAD = 0x4

    def __init__(self):
        self.udp_port = random.randint(20000, 30000)
        self.tcp_port = random.randint(30001, 40000)
        self.running = True
        self.broadcast_port = 13117
        self.udp_lock = threading.Lock()

    def print_safe(self, message, color="\033[0m"):
        with stdout_lock:
            print(f"{color}{message}\033[0m")

    def get_local_ip(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]

    def send_offers(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.print_safe(f"Server started, listening on IP address {self.get_local_ip()}", "\033[36m")

            offer_packet_structure = "!IBHH"
            offer_packet = struct.pack(offer_packet_structure, self.MAGIC_COOKIE, self.TYPE_OFFER, self.udp_port, self.tcp_port)

            while self.running:
                sock.sendto(offer_packet, ("<broadcast>", self.broadcast_port))
                time.sleep(1)

    def handle_tcp_request(self, conn, addr):
        try:
            data = conn.recv(1024)
            (magic, msg_type, file_size, endline_char) = struct.unpack('!IBQ1s', data)
            if magic != self.MAGIC_COOKIE or msg_type != self.TYPE_REQUEST or endline_char != b"\n":
                raise ValueError("Invalid TCP request")

            self.print_safe(f"TCP request from {addr}, file size: {file_size} bytes", "\033[92m")

            payload_msg = struct.pack("!IBQQ", self.MAGIC_COOKIE, self.TYPE_PAYLOAD, 1, 1) + b"x" * file_size
            conn.send(payload_msg)

            self.print_safe(f"TCP transfer to {addr} completed", "\033[34m")
        except (ConnectionResetError, socket.error) as e:
            self.print_safe(f"Client {addr} disconnected: {e}", "\033[41m")
        except Exception as e:
            self.print_safe(f"Error handling TCP request from {addr}: {e}", "\033[41m")
        finally:
            conn.close()

    def handle_udp_request(self, sock, addr, file_size):
        try:
            self.print_safe(f"UDP request from {addr}, file size: {file_size} bytes", "\033[92m")

            total_segments = (file_size + 1023) // 1024
            remaining_bytes = file_size

            for segment in range(total_segments):
                payload_size = min(remaining_bytes, 1024)
                packet = struct.pack("!IBQQ", self.MAGIC_COOKIE, self.TYPE_PAYLOAD, total_segments, segment + 1) + b"x" * payload_size
                remaining_bytes -= payload_size
                with self.udp_lock:
                    sock.sendto(packet, addr)

            self.print_safe(f"UDP transfer to {addr} completed", "\033[36m")
        except (ConnectionResetError, socket.error) as e:
            self.print_safe(f"Client {addr} disconnected: {e}", "\033[41m")
        except Exception as e:
            self.print_safe(f"Error handling UDP request from {addr}: {e}", "\033[41m")

    def listen_for_requests(self):
        tcp_thread = threading.Thread(target=self.listen_for_tcp_requests)
        udp_thread = threading.Thread(target=self.listen_for_udp_requests)
        tcp_thread.start()
        udp_thread.start()

    def listen_for_tcp_requests(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_sock:
            tcp_sock.bind(("", self.tcp_port))
            tcp_sock.listen()
            while self.running:
                conn, addr = tcp_sock.accept()
                threading.Thread(target=self.handle_tcp_request, args=(conn, addr), daemon=True).start()

    def listen_for_udp_requests(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:
            udp_sock.bind(("", self.udp_port))
            while self.running:
                data, addr = udp_sock.recvfrom(4096)
                threading.Thread(target=self.process_udp_request, args=(data, addr, udp_sock), daemon=True).start()

    def process_udp_request(self, data, addr, udp_sock):
        """Process an incoming UDP request from a client."""
        # Unpack the header data
        header_format = "!IBQ"
        header_size = struct.calcsize(header_format)
        if len(data) >= header_size:
            magic_cookie, message_type, file_size = struct.unpack(header_format, data[:header_size])
            if magic_cookie == self.MAGIC_COOKIE and message_type == self.TYPE_REQUEST:
                threading.Thread(
                    target=self.handle_udp_request,
                    args=(udp_sock, addr, file_size),
                    daemon=True
                ).start()
            else:
                self.print_safe(f"Invalid magic cookie or message type from {addr}", "\033[41m")
        else:
            self.print_safe(f"Incomplete UDP header received from {addr}", "\033[41m")

    def run(self):
        offer_thread = threading.Thread(target=self.send_offers)
        offer_thread.start()
        self.listen_for_requests()

if __name__ == "__main__":
    server = SpeedTestServer()
    try:
        server.run()
    except KeyboardInterrupt:
        print("\033[36mServer shutting down...\033[0m")

import threading
import time
import struct
import sys
import socket
import os

stdout_lock = threading.Lock()

class SpeedTestClient:
    BROADCAST_PORT = 13117
    MAGIC_COOKIE = 0xabcddcba
    TYPE_OFFER = 0x2
    TYPE_REQUEST = 0x3
    TYPE_PAYLOAD = 0x4
    RECIEVE_SIZE = 1024
    Payload_Packet_Header_Size = 21

    def __init__(self):
        self.server_ip = None
        self.udp_port = None
        self.tcp_port = None

    def print_safe(self, message, color="\033[0m"):
        with stdout_lock:
            print(f"{color}{message}\033[0m")

    def get_user_input(self):
        self.file_size = int(input("[95mEnter file size in bytes: [0m"))
        self.tcp_connections = int(input("[95mEnter the number of TCP connections: [0m"))
        self.udp_connections = int(input("[95mEnter the number of UDP connections: [0m"))

    def listen_for_offers(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("", self.BROADCAST_PORT))
            self.print_safe("Client started, listening for offer requests...", "\033[36m")
        
            while True:
                try:
                    data, addr = sock.recvfrom(self.RECIEVE_SIZE)
                    magic_cookie, message_type, udp_port, tcp_port = struct.unpack("!IBHH", data)
                    if magic_cookie == self.MAGIC_COOKIE and message_type == self.TYPE_OFFER:
                        self.server_ip = addr[0]
                        self.udp_port = udp_port
                        self.tcp_port = tcp_port
                        self.print_safe(f"Received offer from {self.server_ip}, UDP port: {self.udp_port}, TCP port: {self.tcp_port}", "\033[35m")
                        return
                except (ConnectionResetError, socket.error) as e:
                    self.print_safe(f"Error receiving offer: {e}", "\033[93m")

    def tcp_speed_test(self, connection_id):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.server_ip, self.tcp_port))
                request_packet = struct.pack("!IBQ1s", self.MAGIC_COOKIE, self.TYPE_REQUEST, self.file_size, b"\n")
                sock.sendall(request_packet)
                
                bytes_received = 0
                total_expected_segments = 1
                current_segment = 0
                start_time = time.time()

                while current_segment < total_expected_segments:
                    self.print_safe("Receiving data...", "\033[34m")
                    data = sock.recv(self.file_size + self.Payload_Packet_Header_Size)
                    self.print_safe("Data received.", "\033[34m")
                    (magic, msg_type, total_segments, current_received_segment) = struct.unpack('!IBQQ', data[0:self.Payload_Packet_Header_Size])

                    if magic != self.MAGIC_COOKIE or msg_type != self.TYPE_PAYLOAD:
                        raise ValueError("Invalid Payload received - magic or type error")
                        
                    if current_received_segment != current_segment + 1:
                        raise ValueError("Invalid segment received, current_received_segment != current_segment + 1")
                    
                    current_segment = current_received_segment
                    
                    if not data[self.Payload_Packet_Header_Size:]:
                        break
                    bytes_received += len(data[self.Payload_Packet_Header_Size:])
                
                elapsed_time = time.time() - start_time
                speed = (bytes_received * 8) / elapsed_time if elapsed_time > 0 else bytes_received * 8
                self.print_safe(f"TCP transfer #{connection_id} finished, total time: {elapsed_time:.2f} seconds, total speed: {speed:.2f} bits/second", "\033[32m")
        except (ConnectionResetError, socket.error) as e:
            self.print_safe(f"Error connecting to server: {e}", "\033[31m")

    def udp_speed_test(self, connection_id):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                request_packet = struct.pack("!IBQ", self.MAGIC_COOKIE, self.TYPE_REQUEST, self.file_size)
                sock.sendto(request_packet, (self.server_ip, self.udp_port))
                
                sock.settimeout(1.0)
                packets_received = 0
                packets_total = 0
                total_expected_segments = 1
                current_segment = 0
                start_time = time.time()

                try:
                    while current_segment < total_expected_segments:
                        data, _ = sock.recvfrom(4096)
                        packets_total += 1
                        magic_cookie, message_type, total_segments, current_received_segment = struct.unpack("!IBQQ", data[:self.Payload_Packet_Header_Size])
                        if magic_cookie != self.MAGIC_COOKIE or message_type != self.TYPE_PAYLOAD:
                            raise ValueError("Invalid Payload received")
                    
                        if total_expected_segments == 1:
                            total_expected_segments = total_segments
                        
                        if current_received_segment == current_segment + 1:
                            current_segment = current_received_segment
                            if magic_cookie == self.MAGIC_COOKIE and message_type == self.TYPE_PAYLOAD:
                                packets_received += 1
                except socket.timeout:
                    pass
                
                elapsed_time = time.time() - start_time
                speed = (packets_received * 8 * self.RECIEVE_SIZE) / elapsed_time if elapsed_time > 0 else packets_received * 8 * self.RECIEVE_SIZE
                packet_loss = 100 - (packets_received / packets_total * 100 if packets_total > 0 else 0)
                self.print_safe(f"UDP transfer #{connection_id} finished, total time: {elapsed_time:.2f} seconds, total speed: {speed:.2f} bits/second, percentage of packets received successfully: {100 - packet_loss:.2f}%", "\033[32m")
        except (ConnectionResetError, socket.error) as e:
            self.print_safe(f"Error connecting to server: {e}", "\033[31m")

    def run_speed_test(self):
        threads = []
        self.print_safe("Starting speed test...", "\033[34m")
        for i in range(1, self.tcp_connections + 1):
            thread = threading.Thread(target=self.tcp_speed_test, args=(i,))
            threads.append(thread)
            thread.start()
        
        for i in range(1, self.udp_connections + 1):
            thread = threading.Thread(target=self.udp_speed_test, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
        self.print_safe("All transfers complete, listening to offer requests", "\033[34m")

    def run(self):
        self.get_user_input()
        while True:
            self.listen_for_offers()
            self.run_speed_test()

if __name__ == "__main__":
    client = SpeedTestClient()
    try:
        client.run()
    except KeyboardInterrupt:
        print("\033[44mKeyboardInterrupt - Exiting...\033[0m")
        sys.exit(0)
    except ValueError:
        print("\033[41mValueError - Exiting...\033[0m")
        sys.exit(0)
1
import sys
import socket
import threading
import datetime
import queue

clients = dict()
running_threads = []

class packet:
    def __init__(self, COMMAND, seq_number, length, ack_number, window, PAYLOAD):
        self.COMMAND = COMMAND
        self.seq_number = seq_number
        self.length = length
        self.ack_number = ack_number
        self.window = window
        self.PAYLOAD = PAYLOAD

    def format(self):        
        packet = f"{self.COMMAND}\r\nSequence: {self.seq_number}\r\nLength: {self.length}\r\nAcknowledgment: {self.ack_number}\r\nWindow: {self.window}\r\n\r\n"
        packet += self.PAYLOAD        

        return packet

def print_Date():
    date = datetime.datetime.now()
    date = datetime.datetime.strftime(date, '%a %b %d %H:%M:%S PDT %Y')
    return date

def parse(data):
    packet_comps = []
    data = data.decode().split("\r\n")
    packet_comps.append(data[0])
    for comp in data[1:5]:
        packet_comps.append(int(comp.split(" ")[1]))
    packet_comps.append(data[6])
    return packet_comps

def client_handler(server, addr, server_addr):
    running_threads.append(addr)
    ## waits for other threads to finish before starting
    while True:
        if running_threads.index(addr) == 0:
            break

    window = int(sys.argv[3])
    max_payload = int(sys.argv[4])
    client_queue = clients.get(addr)
    file_found = True
    curr_file = None

    while True:
        ## if queue is empty wait for packet
        if not client_queue:
            continue

        recv_packet = client_queue[0]
        components = recv_packet.decode().split("\r\n")
        command = components[0]

        if "DAT" in command:
            get_request = components[6]
            connection = components[7]
            read_file = get_request.split("/")[1].split(" ")[0]
            try:
                f = open(read_file, 'r')
                curr_file = f
                
                http_header = "HTTP/1.0 200 OK"
                payload = http_header + "\r\n" + connection + "\n\n"
                payload_len = sys.getsizeof(payload)
                file_data = curr_file.read(max_payload - payload_len)
                payload += file_data
                payload_len = sys.getsizeof(payload)
                seq_no = int(components[1].split(" ")[1])
                ack_no = seq_no + payload_len + 1  

            except FileNotFoundError:
                file_found = False

                http_header = "HTTP/1.0 404 Not Found"
                payload = http_header + "\r\n" + connection + "\n\n"
                payload_len = sys.getsizeof(payload)
                seq_no = int(components[1].split(" ")[1])
                ack_no = seq_no + payload_len + 1
            if "SYN" in command:
                send_packet = packet("ACK|SYN|DAT", seq_no, payload_len, ack_no, window, payload).format()
            else:
                send_packet = packet("ACK|DAT", seq_no, payload_len, ack_no, window, payload).format()
            server.sendto(bytes(send_packet,"utf-8"), addr)
            print(f"{print_Date()}: {addr[0]}:{addr[1]} {get_request}; {http_header}")
            
            client_queue.pop(0) 
        elif command == "ACK":
            data = parse(recv_packet)
            ack_no = data[1]
            seq_no = data[3]

            if file_found:
                payload = curr_file.read(max_payload)
                payload_len = len(payload)
                if payload_len != 0:
                    data_packet = packet("ACK|DAT", seq_no + payload_len, payload_len, ack_no, window, payload).format()
                    server.sendto(bytes(data_packet, "utf-8"), addr)
            else:
                payload_len = 0

            if "close" in connection and payload_len == 0:
                fin_packet = packet("FIN|ACK", seq_no, 0, ack_no, window, "")
                server.sendto(bytes(fin_packet.format(), "utf-8"), addr)
            client_queue.pop(0) 
        elif command == "FIN|ACK":
            data = parse(recv_packet)
            seq_no = data[3]
            ack_no = data[1] + 1

            end_packet = packet("ACK", seq_no, 0, ack_no, window, "")
            server.sendto(bytes(end_packet.format(), "utf-8"), addr)
            client_queue.pop(0)
            break

    running_threads.pop(0) 
    del clients[addr]
    
          

def start(SERVER, PORT):
    server_addr = (SERVER, PORT)
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(server_addr)
    window = int(sys.argv[3])

    while True:
        incoming_packet, addr = server.recvfrom(window)
        if addr not in clients:
            client_packets = []
            client_packets.append(incoming_packet)
            clients[addr] = client_packets
            handle = threading.Thread(target = client_handler, args = (server, addr, server_addr), daemon=True).start()
        else:
            clients.get(addr).append(incoming_packet)
def main():
    try:
        if len(sys.argv) != 5:
            print("Invalid number of arguments:")
            print("Please run in the form 'sor-server.py server_ip_address server_udp_port_number server_buffer_size server_payload_length'")
            sys.exit()
        else:
            SERVER = sys.argv[1]
            PORT = int(sys.argv[2])
            start(SERVER,PORT)
    except (KeyboardInterrupt, SystemExit):
        sys.exit()

if __name__ == "__main__":
    main()
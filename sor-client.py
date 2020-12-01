import sys
import socket
import datetime

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

def main():
    server_addr = (sys.argv[1], int(sys.argv[2]))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('',0))
    num_files = (len(sys.argv)-5) / 2
    files = []
    cmd_location = 5
    while cmd_location < len(sys.argv):
        files.append(sys.argv[cmd_location])
        cmd_location += 2

    write_files = []
    cmd_location = 6
    while cmd_location < len(sys.argv):
        write_files.append(sys.argv[cmd_location])
        cmd_location += 2

    seq_num = 0
    ack_num = -1
    window = int(sys.argv[3])
    max_payload_len = int(sys.argv[4])

    connection = "Connection: keep-alive"
    
    i = 0
    for read_file in files:
        current_write_file = write_files[i]
        write_file = open(current_write_file, 'w')
        if i == (len(files) - 1):
            connection = "Connection: close"
        GET_request = "GET /" + read_file + " HTTP/1.0\r\n" + connection
        request_len = sys.getsizeof(GET_request)
        if i == 0:
            command = "SYN|DAT|ACK"
        else:
            command = "DAT"
        connection_packet = packet(command, seq_num, request_len, ack_num, window, GET_request)
        sock.sendto(bytes(connection_packet.format(), "utf-8"), server_addr)
        date = print_Date()
        print(f"{date}: Send; {connection_packet.COMMAND}; Sequence: {seq_num}; Length: {request_len}; Acknowledgment: {ack_num}; Window: {window}")
        
        data, addr = sock.recvfrom(window)
        data = parse(data)
        date = print_Date()
        print(f"{date}: Receive; {data[0]}; Sequence: {data[1]}; Length: {data[2]}; Acknowledgment: {data[3]}; Window: {data[4]}")

        send_packet = packet("ACK", data[3], 0, data[1] + 1, window, "")
        sock.sendto(bytes(send_packet.format(), "utf-8"), server_addr)
        seq_num = send_packet.seq_number
        length = send_packet.length
        ack_num = send_packet.ack_number
        print(f"{date}: Send; {send_packet.COMMAND}; Sequence: {seq_num}; Length: {length}; Acknowledgment: {ack_num}; Window: {window - max_payload_len}")

        if "ACK" in data[0].split("|") and "DAT" in data[0].split("|"):
            if "HTTP" in data[5] and len(data) == 7:
                file_contents = data[6].split("\n\n")
                if file_contents[1] != None:
                    write_file.write(file_contents[1])
            else:
                write_file.write(data[5])
            if "keep-alive" in connection and (sys.getsizeof(data[5]) + sys.getsizeof(data[6])) < max_payload_len:
                i += 1
                continue

        while True:
            data, addr = sock.recvfrom(window)
            data = parse(data)
            print(f"{date}: Receive; {data[0]}; Sequence: {data[1]}; Length: {data[2]}; Acknowledgment: {data[3]}; Window: {data[4]}")

            if "FIN" in data[0]:
                end_packet = packet("FIN|ACK", data[3], 0, data[1] + 1, window, "")
                sock.sendto(bytes(end_packet.format(), "utf-8"), server_addr)
                print(f"{print_Date()}: Send; {end_packet.COMMAND}; Sequence: {data[3]}; Length: 0; Acknowledgment: {data[1]+1}; Window: {window}")

            elif data[0] == "ACK":
                break
            elif "DAT" in data[0]:
                write_file.write(data[5])
                ack_packet = packet("ACK", data[3], 0, data[1] + len(data[5]), window, "")
                sock.sendto(bytes(ack_packet.format(), "utf-8"), server_addr)
                print(f"{print_Date()}: Send; {ack_packet.COMMAND}; Sequence: {data[3]}; Length: 0; Acknowledgment: {ack_packet.ack_number}; Window: {window - max_payload_len}")
                if sys.getsizeof(data[5]) < max_payload_len and "keep-alive" in connection:
                    break
        i += 1
def parse(data):
    packet_comps = []
    data = data.decode().split("\r\n")
    packet_comps.append(data[0])
    for comp in data[1:5]:
        packet_comps.append(int(comp.split(" ")[1]))
    packet_comps.append(data[6])
    if len(data) == 8:
        packet_comps.append(data[7])
    return packet_comps

if __name__ == "__main__":
    main()
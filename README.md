# Web-server-and-Client-Interaction

sor-server.py and sor-client.py communicate with each other to copy given text files to a new text file. The packet flow is displayed by sor-client.py, 
and the HTTP header response is output by sor-server.py

How to Run:
SERVER --> python sor-server.py [server_IP] [server_PORT] [server_buffer] [max_data_payload]

CLIENT --> python sor-client.py [server_IP] [server_PORT] [server_buffer] [max_data_payload] [read_file] [write_file]
*note: to copy multiple files, add more read_files with its corresponding write_file at the end

output.png shows an example output

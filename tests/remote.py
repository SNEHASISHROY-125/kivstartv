import socket , threading

s = socket.socket()
s.connect(('192.168.1.5', 9090))

def send_command(cmd):
    s.sendall(cmd.encode())
    # s.close()


def run():
	while True:
		in_ = input("Enter command: ")
		# data = s.recv(1024).decode()
		send_command(in_)
		print("send it")  #f"[SocketClient] Received: {data.strip()}")

run()

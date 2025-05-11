import socket
import threading

class RemoteSocketServer(threading.Thread):
	def __init__(self, callback_handler, set_ip_callback, set_client_ip_callback, host='0.0.0.0', port=9090):
		super().__init__()
		self.callback_handler = callback_handler
		self.set_ip = set_ip_callback
		self.set_client_ip_callback = set_client_ip_callback
		self.tv_name = ""
		self.host = host
		self.port = port
		self.running = True

	def handle_command(self, data):
		#
		command = data.strip().lower()
		if command == "enter":
			self.callback_handler("enter")
		elif command == "esc":
			self.callback_handler("esc")
		elif command == "menu":
			self.callback_handler("menu")
		elif command == "fav":
			self.callback_handler("fav")
		elif command == "forth":
			self.callback_handler("forth")
		elif command == "back":
			self.callback_handler("back")
		elif command == "up":
			self.callback_handler("up")	
		elif command == "down":
			self.callback_handler("down")
		# nums
		elif command == "1":
			self.callback_handler("1")
		elif command == "2":
			self.callback_handler("2")
		elif command == "3":
			self.callback_handler("3")
		elif command == "4":
			self.callback_handler("4")
		elif command == "5":
			self.callback_handler("5")
		elif command == "6":
			self.callback_handler("6")
		elif command == "7":
			self.callback_handler("7")
		elif command == "8":
			self.callback_handler("8")
		elif command == "9":
			self.callback_handler("9")
		elif command == "0":
			self.callback_handler("0")
		elif command == "power": 
			self.callback_handler("power")
		elif command == "-/": 
			self.callback_handler("min_volume")
		elif command == "+/": 
			self.callback_handler("max_volume")
		# send client tv details
		elif command == "tv_name":
			# send the tv name to the client
			self.client.sendall(self.tv_name.encode())
		else:
			print(f"[SocketServer] Unknown command: {command}")

	def run(self):
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
			hostname = socket.gethostbyname(socket.gethostname())
			print(f"[SocketServer] Hostname: {hostname}")
			# set the IP address to the app.local_ip
			self.set_ip(hostname)
			server.bind((self.host, self.port))
			server.listen(5) # max 5 connections
			print(f"[SocketServer] Listening on {self.host}:{self.port}")
			
			# handles input from the client
			def handler():
				# set the client IP address
				self.set_client_ip_callback(self.addr[0])
				while self.running:
					data = self.client.recv(1024).decode()
					print(f"[SocketServer] Received: {data.strip()}")
					if not self.running or not data:
						print("[SocketServer] Connection closed")
						# set the client IP address to ""
						self.set_client_ip_callback("")
						break
					self.handle_command(data)

			while self.running:
				try:
					self.client, self.addr = server.accept()
					print(f"[SocketServer] Connection from {self.addr}")
					
					# continue to handle the connection until closed
					with self.client:
						handler()

				except Exception as e:
					print(f"[SocketServer] Error: {e}")
			
			# close the server
			print("[SocketServer] Server stopped")
			self.client.close()
			server.close()

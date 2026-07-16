import socket
import struct
import os , json

import time
import mimetypes

CHUNK = 64 * 1024


def send_msg(sock, data: bytes):
    sock.sendall(struct.pack("!I", len(data)) + data)


def recv_exact(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError
        data += chunk
    return data


def recv_msg(sock):
    length = struct.unpack("!I", recv_exact(sock, 4))[0]
    return recv_exact(sock, length)

port = input("which port to connect? : ")
print("connecting ... to ", port)
sock = socket.create_connection(("localhost",  int(port)))
print("connected")

def upload_local_file(file,root:str):
    with open(file,"rb") as f:
        size = os.path.getsize(file)
        mime_type, _ = mimetypes.guess_type(file)
        if mime_type is None:
            mime_type = "application/octet-stream"
        # print(f"/upload {root} {os.path.basename(file)} {mime_type} {size}".encode())
        send_msg(sock, f"/upload {root} {os.path.basename(file)} {mime_type} {size}".encode())
        # confirmation init
        print(recv_msg(sock).decode())
        # start sending
        remaining = size
        while remaining:
            chunk = min(CHUNK,remaining)
            sock.sendall(f.read(chunk))
            remaining -= chunk  
        print("done uploading...")
        # print(recv_msg(sock).decode())

st = time.time()
# ---- LIST DIR ----
test_uri = "content://com.android.externalstorage.documents/tree/primary%3AMusic/document/primary%3AMusic%2Fjav%2Fvids"
source = "content://com.android.externalstorage.documents/tree/primary%3AEmu/document/primary%3AEmu%2FEmoji-iOS18.4-AD.ttf"
dest = test_uri
# upload_local_file("Emoji-iOS18.4-AD.ttf",test_uri)
# send_msg(sock, f"/scan {test_uri} ".encode())
# send_msg(sock, b"/move content://com.android.externalstorage.documents/tree/primary%3AEmu/document/primary%3AEmu%2FEmoji-iOS18.4-AD.ttf content://com.android.externalstorage.documents/tree/primary%3AEmu/document/primary%3AEmu content://com.android.externalstorage.documents/tree/primary%3AEmu/document/primary%3AEmu%2Fxxx%2Fvids")
# send_msg(sock, b"/copy content://com.android.externalstorage.documents/tree/primary%3AEmu/document/primary%3AEmu%2Fxxx%2Fvids%2FEmoji-iOS18.4-AD.ttf content://com.android.externalstorage.documents/tree/primary%3AEmu/document/primary%3AEmu")
# send_msg(sock, b"/rename content://com.android.externalstorage.documents/tree/primary%3AEmu/document/primary%3AEmu%2Fjav vjav")
# send_msg(sock, f"/mkdir {test_uri} jav/vids/122".encode())
# send_msg(sock, f"/docid2uri {test_uri} primary:Music/jav/vids".encode())
# send_msg(sock, b"/delete content://com.android.externalstorage.documents/tree/primary%3AEmu/document/primary%3AEmu%2F.trashed-1775146786-downloaded.gif")
file = "content://com.android.externalstorage.documents/tree/primary%3AMusic/document/primary%3AMusic%2Fjav%2Fvids%2Frotating_head.gif"
# send_msg(sock, f"/thumb normal {file} {256} {85}".encode())
def download():
    send_msg(sock, f'/download {test_uri}%2Frotating_head.gif'.encode())
    print(l:=json.loads(recv_msg(sock).decode()),)
    # print(recv_msg(sock))
    new = "test-"+ l.get("file_name")
    size = l.get("size")
    send_msg(sock, "send:now".encode())
    with open(new,'wb') as f:
        remaining = int(size)
        while remaining:
            chunk = sock.recv(min(CHUNK,remaining))
            f.write(chunk)
        # await writer.drain()
            remaining -= len(chunk)
        print(recv_msg(sock).decode())

def download_thumb():
    file = "content://com.android.externalstorage.documents/tree/primary%3AMusic/document/primary%3AMusic%2Fjav%2Fvids%2Frotating_head.gif"
    send_msg(sock, f"/thumb normal {file} {256} {85}".encode())
    print(l:=json.loads(recv_msg(sock).decode()),)
    with open("temp-thumb.jpeg", 'wb') as f:
        send_msg(sock, "send:now".encode())
        size = int(l.get("thumb-size"))
        while size:
            chunk = sock.recv(size)
            f.write(chunk)
            size -= len(chunk)

# print(f"\nlenth {len(list(l.values()))}")

# # ---- UPLOAD ----
# file = "/home/roy/Documents/y2m-pocket/uploads/rotating_head.gif"
# size = os.path.getsize(file)

### 
while True:
    print("Type Query along with comms eg: /set_volume 0.7")
    comms = input()
    # payload = json.dumps(comms)

    send_msg(sock, comms.encode())
    print(recv_msg(sock).decode())

# with open(file, "rb") as f:
#     while chunk := f.read(CHUNK):
#         sock.sendall(chunk)

# print("eof")
# print(recv_msg(sock))

# # ---- DOWNLOAD ----
# send_msg(sock, b"/download storage/dem.gif")
# size = int(recv_msg(sock).decode().split()[1])

# with open("downloaded.gif", "wb") as f:
#     remaining = size
#     while remaining:
#         chunk = sock.recv(min(CHUNK, remaining))
#         f.write(chunk)
#         remaining -= len(chunk)
# print(f"took {st - time.time()}.s")

sock.close()

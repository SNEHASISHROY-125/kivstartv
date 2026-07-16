import asyncio
import os , json
import struct , datetime ,uuid

# ROOT_DIR = "./"
CHUNK = 64 * 1024  # 64KB

async def read_exact(reader, n):
    data = b""
    while len(data) < n:
        chunk = await reader.read(n - len(data))
        if not chunk:
            raise ConnectionError("Client disconnected")
        data += chunk
    return data


async def read_message(reader):
    header = await read_exact(reader, 4)
    (length,) = struct.unpack("!I", header)
    return await read_exact(reader, length)


async def send_message(writer, data: bytes):
    writer.write(struct.pack("!I", len(data)) + data)
    await writer.drain()

def get_tree(path:str):
    '''
    'root/player/d12032026/fun.gif'\n
    (['root', 'player', 'd12032026'], 'fun.gif')
    '''
    _  = path.split('/')
    return (_[:-1] , _[-1],) if len(_) > 1 else ("." , _[-1],)

global jobs
jobs = {}

class Job:
    '''
    CROSS THREAD JOB HANDLER
    '''
    job_id = None
    job = None
    ''' job callback '''
    timeout = 100   # ~1 sec

    def __init__(self):
        pass

    def create_job(self):
        ## create job-id
        self.job_id = str(uuid.uuid4())
        ## creatte job
        self.job = self.job_handler(self.job_id)

    async def run_till_complete(self):
        ''' wait till a results are passed or timeout & return result'''
        ## loop till either times-out || value gets returned
        global jobs
        for _ in range(self.timeout):
            result = jobs.get(self.job_id)
            if result: jobs.__delitem__(self.job_id) ; break
            await asyncio.sleep(0.01)
        # print("got duration: ", duration)
        return result

    def job_handler(self, id, register=jobs, val=None): return lambda v , i=id, r=register: r.setdefault(i , v)

global _methods

async def handle_client(reader, writer):
    addr = writer.get_extra_info("peername")
    print(f"[+] Connected: {addr}")
    global _methods
    global jobs

    try:
        while True:
            msg = (await read_message(reader)).decode()
            parts = msg.split()
            # parts = json.loads(msg)

            # debug
            print("comms: ", parts)

            # match parts["comm"]:
            match parts[0]:

                # 🎬 Video
                
                case '/init':
                    _methods.get('initmpv')()
                    await send_message(writer , b'ok')

                case '/destroy':
                    _methods.get('destroympv')() 
                    await send_message(writer , b'ok')

                # ---------------- Player Controls ----------------
                case '/load':
                    url = parts[1]
                    _ = _methods.get('load')(url)
                    await send_message(writer , str(_).encode())

                # case "/set_source":
                #     _ , url , headers , prepare = parts
                #     # print(parts,headers.encode())
                #     _methods.get('setSource')(url , json.loads(headers.encode()) , True if prepare == "true" else False)
                #     await send_message(writer, b"ok")

                # case "/set_metadata":
                #     _ , title , artist , artwork = parts
                #     _methods.get("setMetadata")(title,artist,artwork)
                #     await send_message(writer, b"ok")
                
                # 📖 State Getters

                case "/play":
                    _methods.get("play")()
                    await send_message(writer, b"ok")

                case "/pause":
                    _methods.get("pause")()
                    await send_message(writer, b"ok")

                case "/stop":
                    _methods.get("stop")()
                    await send_message(writer, b"ok")

                case "/paused":
                    res = _methods.get("paused")()
                    await send_message(writer, str(res).encode())

                case "/seek":
                    _, position_ms = parts
                    _methods.get("seek")(int(position_ms))
                    await send_message(writer, b"ok")

                case "/skip":
                    _, positionMs = parts
                    _methods.get("skip")(int(positionMs))
                    await send_message(writer, b"ok")

                # ⏱️ Time / Position

                case "/pos":
                    res = _methods.get("pos")()
                    await send_message(writer, str(res).encode())

                case "/duration":
                    res = _methods.get("duration")()
                    await send_message(writer, str(res).encode())



                # 📋 Playlist / Media Items

                # 🔁 Repeat & Shuffle

                # 🔊 Audio

                case "/volume":
                    res = _methods.get("volume")()
                    await send_message(writer, str(res).encode())

                case "/volume_set":
                    _, volume = parts
                    _methods.get("volume_set")(float(volume))
                    await send_message(writer, b"ok")

                case "/is_muted":
                    res = _methods.get("mute")()
                    await send_message(writer, str(res).encode())

                case "/set_mute":
                    _, muted = parts
                    _methods.get("mute_set")(muted.lower() == "true")
                    await send_message(writer, b"ok")

                # ⚡ Speed
                case "/speed":
                    _, params = parts
                    res = _methods.get("speed")(params)
                    await send_message(writer, str(res).encode())

                case "/speed_set":
                    _, speed = parts
                    _methods.get("speed_set")(float(speed))
                    await send_message(writer, b"ok")

                case _:
                    await send_message(writer, b"error:unknown_command")

    except Exception as e:
        print(f"[!] {addr} error:", e)

    finally:
        writer.close()
        await writer.wait_closed()
        print(f"[-] Disconnected: {addr}")





import threading

TCP_PORT = 8877

def start_tcp_server(_ethods):
    def run(_ethods):
        async def main(ethods):
            global _methods
            _methods = dict(ethods)
            print(_methods)
            server = await asyncio.start_server(handle_client, "0.0.0.0", TCP_PORT)
            async with server:
                print("🚀 TCP server running on : ", TCP_PORT)
                await server.serve_forever()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(main(_ethods))
        except KeyboardInterrupt:
            pass
        finally:
            print("lOOP CLOSING...")
            loop.close()

    server_thread = threading.Thread(target=run, args=(_ethods,),daemon=True)
    # Start server in a daemon thread
    server_thread.start()

import asyncio
import os , json
import struct , datetime

# plugins
# from akasha.plugins.pdf import androidRenderer

ROOT_DIR = "./"
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


global _methods

async def handle_client(reader, writer):
    ######## DEBUG ##########
    print("new conn arrives ...")
    #########################
    addr = writer.get_extra_info("peername")
    print(f"[+] Connected: {addr}")
    global _methods

    while True:
        try:
            # {
            #     "comm" : ...,
            # }

            msg = await read_message(reader)
            parts = json.loads(msg)

            # match parts[0]:
            match parts["comm"]:

                case "/incert_ch":
                    comm = parts["chanels"]
                    ## DEBUG
                    print(comm)
                    contents = _methods.get("incert_chanels")(comm)
                    await send_message(writer, (json.dumps({"contents":contents})).encode())

                case "/update_ch":
                    comm = parts["chanels"]
                    ## DEBUG
                    print(comm)
                    contents = _methods.get("update_chanels")(comm)
                    await send_message(writer, (json.dumps({"contents":contents})).encode())

                case "/ch_count":
                    contents = _methods.get("ch_count")()
                    await send_message(writer, (json.dumps({"contents":contents})).encode())

                case "/groups":
                    contents = _methods.get("groups")()
                    await send_message(writer, (json.dumps({"contents":contents})).encode())

                case "/ch_group":
                    contents = _methods.get("chanels_group")()
                    await send_message(writer, (json.dumps({"contents":contents})).encode())

                case "/get_ch_group_id":
                    comm = parts["id"]
                    ## DEBUG
                    print(comm)
                    contents = _methods.get("chanels_group_id")(comm)
                    await send_message(writer, (json.dumps({"contents":contents})).encode())

                case "/get_ch_group_ch_id":
                    comm = parts["id"]
                    ## DEBUG
                    print(comm)
                    contents = _methods.get("chanels_group")(comm)
                    await send_message(writer, (json.dumps({"contents":contents})).encode())

                case "/fav":
                    contents = _methods.get("incert_channels")()
                    await send_message(writer, (json.dumps({"contents":contents})).encode())

                case "/add_fav":
                    comm = parts["id"]
                    ## DEBUG
                    print(comm)
                    contents = _methods.get("incert_channels")(comm)
                    await send_message(writer, (json.dumps({"contents":contents})).encode())

                case "/remove_fav":
                    comm = parts["id"]
                    ## DEBUG
                    print(comm)
                    contents = _methods.get("incert_channels")(comm)
                    await send_message(writer, (json.dumps({"contents":contents})).encode())

                case "/disconnect":
                    print(f"[-] Disconnected: {addr}")
                    break

                case "/ping":
                    print("server periodic ping")
                    # send pong
                    await send_message(writer , "pong".encode())

                case _:
                    # debug
                    print(parts)
                    await send_message(writer, b"error:unknown_command")

        except Exception as e:
            print(f"[!] {addr} error:", e)
            await send_message(writer, b"error:unknown")

        # finally:
        #     json.dumps({"s":90})
            # writer.close()
            # await writer.wait_closed()

# asyncio.run(main())
# import threading
def make_unix_socket(path):
    if os.path.exists(path+"/saf.sock") : os.remove(path+"/saf.sock")
    return path + "/saf.sock"

def start_tcp_server(_ethods , unix_socket_path , server_coroutine):
    '''
    ``server_coroutine`` [:dict] to be stored keys: ``server_coroutine`` & ``loop``
    '''
    async def main(ethods , unixSocket , coroutine_server):
        global _methods
        _methods = dict(ethods)
        # DEBUG
        # server = await asyncio.start_server(handle_client, "0.0.0.0", 9090)
        server = await asyncio.start_unix_server(handle_client, make_unix_socket(unixSocket))
        coroutine_server["server_coroutine"] = server
        async with server:
            print("🚀 TCP server running on")
            await server.serve_forever()
            # debug
            print("saf server closed!!")
        # 
        # server.close()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server_coroutine["loop"] = loop  # store loop so outside can schedule shutdown
    try:
        loop.run_until_complete(main(_ethods , unix_socket_path , server_coroutine))
    except Exception as e:
        print(e)
    finally:
        print("lOOP CLOSING...")
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        loop.close()

def stop_tcp_server(server_coroutine):
    """
    Request shutdown of the asyncio server stored in ``server_coroutine`` dict.
    Safe to call from another thread.
    """
    loop = server_coroutine.get("loop")
    srv = server_coroutine.get("server_coroutine")
    if not loop or not srv:
        return

    async def _close():
        try:
            srv.close()
            await srv.wait_closed()
        except Exception as e:
            print("error closing server:", e)
        # give loop a chance to finish other work, then stop
        loop.stop()

    # schedule close coroutine in the server's loop
    try:
        asyncio.run_coroutine_threadsafe(_close(), loop)
    except Exception as e:
        print("failed to schedule server close:", e)
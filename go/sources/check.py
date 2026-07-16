url = 'https://wurlsonypicturestv.global.transmit.live/hls/68deeb1c0238cda82df543dd/v1/spt_sonykal_1/lg_us/latest/main/hls/playlist.m3u8'

import requests

async def check_m3u_stream_safely(session , url , timeout=5):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # try:
    #     # 1. Try a HEAD request first (safest, doesn't download content)
    #     response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        
    #     # 2. If the server doesn't support HEAD (returns 405 or 400), fallback to GET safely
    #     if response.status_code in [400, 404, 405, 501]:
    #         # CRITICAL: stream=True tells requests NOT to download the body immediately
    #         response = requests.get(url, headers=headers, timeout=timeout, stream=True, allow_redirects=True)
            
    #         # We instantly close the connection after reading the status code/headers
    #         response.close() 

    #     # 3. Validate the status code
    #     if 200 <= response.status_code < 300:
    #         return f"UP (Status: {response.status_code})"
    #     else:
    #         return f"DOWN (Status: {response.status_code})"

    # except requests.exceptions.Timeout:
    #     return "DOWN (Timeout)"
    # except requests.exceptions.RequestException as e:
    #     return f"DOWN (Error: {type(e).__name__})"
    
    try:
        # 1. Try HEAD request first
        async with session.head(url, headers=headers, timeout=timeout, allow_redirects=True) as response:
            if 200 <= response.status <= 299:
                return "UP", response.status
            
            # 2. Fallback to GET if HEAD isn't allowed but stream=True equivalent (don't read body)
            if response.status in [400, 404, 405, 501]:
                async with session.get(url, headers=headers, timeout=timeout, allow_redirects=True) as get_resp:
                    # Closing immediately without reading content via get_resp.close()
                    get_resp.close()
                    if 200 <= get_resp.status <= 299:
                        return "UP", get_resp.status
                    return "DOWN", get_resp.status
                    
            return "DOWN", response.status
    except asyncio.TimeoutError:
        return "DOWN", "Timeout"
    except Exception as e:
        return "DOWN", type(e).__name__
    

# print(check_m3u_stream_safely(url))

import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))
import json , re , asyncio , aiohttp
from urllib.parse import unquote


channels = []

channels_meta = {}

def _channels_meta():

    _meta = requests.get("https://iptv-org.github.io/api/channels.json")
    channels_meta['meta'] = json.loads(_meta.content) if _meta.status_code==200 else {} # {[...]}

    # save indexes
    channels_meta['index'] = {} # {}
    _ = {}
    for i , m in enumerate(channels_meta['meta']):
        index = i
        id =  m['id']
        # append
        _[id] = index

    channels_meta['index'] = _

    return channels_meta['index']

def parse_m3u(file_path):
    channels = []
    current_channel = None
    current_options = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#EXTM3U'):
                continue
            if line.startswith('#EXTINF'):
                # Parse metadata
                match = re.match(r'#EXTINF:-?\d+\s*(.*?),(.*)', line)
                if match:
                    attrs = match.group(1)
                    name = unquote(match.group(2)).strip()
                    tvg_id = re.search(r'tvg-id="([^"]+)"', attrs)
                    logo = re.search(r'tvg-logo="([^"]+)"', attrs)
                    groups = re.search(r'group-title="([^"]+)"', attrs)
                    current_channel = {
                        'tvg_id': tvg_id.group(1) if tvg_id else None,
                        'name': name,
                        'logo': unquote(logo.group(1)) if logo else None,
                        'groups': [g.strip() for g in groups.group(1).split(';')] if groups else [],
                        'url': None,
                        'options': []
                    }
            elif line.startswith('#EXTVLCOPT:'):
                option = line[len('#EXTVLCOPT:'):].strip()
                current_options.append(option)
            elif line and not line.startswith('#'):
                if current_channel:
                    current_channel['url'] = unquote(line)
                    current_channel['options'] = current_options.copy()
                    channels.append(current_channel)
                    current_channel = None
                    current_options.clear()
    return channels


channels = parse_m3u("index.m3u")


working_channels = {}

CONCURRENT_WORKERS = 10

async def worker(worker_id, queue, session):
    """Worker loop that consumes URLs from the queue."""
    while True:
        print("worker awaking...")
        items = await queue.get()
        id , link , index = items
        print("worker "+str(worker_id)+" is in action: checking for: "+ str(index) +" / "+str(id if id else 'none'))
        try:
            state = await check_m3u_stream_safely(session, link)
            
            # Perfect Sync: Instantly write to file to prevent memory bloat/data loss
            if state[0] == "UP" and id!=None: working_channels[id] = index
            else: print(str(id) + ' is ' , state)
            
        finally:
            # tag as working with proportion to state
            queue.task_done()

async def schedule():

    queue = asyncio.Queue()
    # Create a persistent client session for connection pooling
    async with aiohttp.ClientSession() as session:
        # Create worker tasks
        tasks = []
        for i in range(CONCURRENT_WORKERS):
            task = asyncio.create_task(worker(i, queue, session))
            tasks.append(task)

        print("idle...")        
        # Populate the queue
        for index , channel in enumerate(channels):
            id = channel['tvg_id']
            link = channel['url']
            await queue.put((id,link,index,))
        
        print('channels-list' , channels.__len__() , queue.qsize())

        await asyncio.sleep(10)
        # Wait until the queue is completely empty
        await queue.join()

        # Cancel our workers since jobs are done
        for task in tasks:
            task.cancel()

# for index , channel in enumerate(channels):
#     id = channel['tvg_id']
#     link = channel['url']
#     # check for uptime
#     state = check_m3u_stream_safely(link)

#     # tag as working with proportion to state
#     if state.startswith("UP") and id!=None: working_channels[id] = index
#     else: print(str(id) + ' is ' + state)

    # channels metadata
    channels_meta = _channels_meta()

    # dump
    db = "channels1.json"

    with open(db , "wb") as f:
        _metadata = json.dumps({
            'working' : working_channels,
            'channels' : channels,
            'channels_metadata' : channels_meta,
        }).encode()
        f.write(_metadata)


asyncio.run(schedule())
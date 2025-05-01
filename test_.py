from update import main as update

# print(update.schedule_update_m3u())


import requests , os , json , datetime
import re , sqlite3 ,configparser
from urllib.parse import unquote
import create_db as cdb

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

channels = parse_m3u("jiotv.m3u8")
# # do db stuff | insert or update
res = cdb.insert_channels(channels)
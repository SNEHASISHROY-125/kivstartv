# -*- coding: utf-8 -*-
import requests , os , sys , json , datetime 
import re , sqlite3 ,configparser
from urllib.parse import unquote
import create_db as cdb

if sys.platform != "win32":
    # For Linux/macOS: use ~/.local/share or just ~/
    app_data = os.path.join(os.path.expanduser("~"), ".local", "share", "KivstarTV")
else:
    app_data = os.path.join(os.getenv("LOCALAPPDATA") or os.path.expanduser("~"), "KivstarTV")


# app .conf
config = configparser.ConfigParser()
config.read(os.path.join(app_data, 'app.conf'))

update_db = config['update']['update_db_path']
update_source = config['update']['update_source']
archive_path = config['update']['archive_path']
# debug_mode = config.getboolean('app', 'debug')
# print(update_source, update_db, archive_path)

def check_today_update():
	"""
	check if update done today or not
	"""
	try:
		with sqlite3.connect(update_db) as conn:
			c = conn.cursor()
			# Use parameterized query to prevent SQL injection
			today = datetime.datetime.now().strftime("%Y-%m-%d")
			try:
				# Use parameterized query to prevent SQL injection
				c.execute("CREATE TABLE IF NOT EXISTS updates (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, source TEXT)")
				c.execute("SELECT date FROM updates WHERE date LIKE ?", (f"{today}%",))
				rows = c.fetchall()
			except sqlite3.Error as e:
				print(f"Error fetching today's update: {e}")
				return False
			if rows:
				print("Update already done today")
				return True
			else:
				print("No update done today")
				return False
	except sqlite3.Error as e: 
		print(f"Error checking today's update: {e}")
		return False

def update_db_manager(source:str):
    """
    manages schedules update and db updates
    """
    try:
        with sqlite3.connect(update_db) as conn:
            c = conn.cursor()
			# Use parameterized query to prevent SQL injection
            c.execute("CREATE TABLE IF NOT EXISTS updates (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, source TEXT)")
			# insert the current date and time
            c.execute("INSERT INTO updates (date, source) VALUES (?, ?)", (str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")), source))
            # TESTING
			# c.execute("UPDATE updates SET date = ?, source = ?", (str('else2025-04-28_00-17-01'), source))
            conn.commit()
    except sqlite3.Error as e: print(f"Error updating database: {e}")
    return 200
	

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

# update_db_manager("archive/test.db")
# if check_today_update() : print("Update already done today")

def schedule_update_m3u() -> int:
	"""
	``200`` for sucess update | ``500`` for already updated
	- check if update done today or not
	"""
    # check first wheather done today any update or not
	if check_today_update() : return 500

	with open(update_source, "r") as f:
		sources = f.read().splitlines()

	for source in sources :
		if source.startswith("#") or not source.strip(): 
			continue
		else:
			global playlist_m3us
			playlist_m3us = []
			print("Fetching {} on UTC {}".format(source , datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
			# get the m3u file
			res = requests.get(source)
			if res.status_code == 200:
				# print(res.content.decode('utf-8'))

				# save the m3u file
				file_name = os.path.join(archive_path , f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.m3u8")
				playlist_m3us.append(file_name)
				#
				with open(file_name, "wb") as f:
					f.write(res.content)
					f.close()
			
			# perse the m3u file
			channels = parse_m3u(file_name)
	        # do db stuff | insert or update
			res = cdb.insert_channels(channels)
			print("Done updating channels {}".format(file_name)) if res == 200 else print("Error updating channels {}".format(file_name))
	        # add to updates db
			_ =update_db_manager(source)
	
	# 200 for sucess update | 500 for already updated
	return 200
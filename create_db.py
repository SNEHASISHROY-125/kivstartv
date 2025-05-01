import sqlite3 , configparser

# app .conf
config = configparser.ConfigParser()
config.read('app.conf')

# db_path = config['database']['path']
DB = config['app']['channels_db_path']

def create_tables():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # Channels table
    c.execute('''CREATE TABLE IF NOT EXISTS channels
                 (id INTEGER PRIMARY KEY,
                  tvg_id TEXT,
                  name TEXT,
                  logo_url TEXT,
                  stream_url TEXT UNIQUE)''')
    
    # Groups table (many-to-many relationship)
    c.execute('''CREATE TABLE IF NOT EXISTS groups
                 (id INTEGER PRIMARY KEY,
                  name TEXT UNIQUE)''')
    
    # Channel-Group relationship table
    c.execute('''CREATE TABLE IF NOT EXISTS channel_groups (
		channel_id INTEGER,
		group_id INTEGER,
		UNIQUE(channel_id, group_id),
		FOREIGN KEY(channel_id) REFERENCES channels(id),
		FOREIGN KEY(group_id) REFERENCES groups(id))''')

	# create favourites table
    c.execute('''CREATE TABLE IF NOT EXISTS favourites
				 (id INTEGER PRIMARY KEY,
				  channel_id INTEGER,
				  FOREIGN KEY(channel_id) REFERENCES channels(id))''')
	# create options table
    c.execute('''CREATE TABLE IF NOT EXISTS options
				 (id INTEGER PRIMARY KEY,
				  channel_id INTEGER,
				  option TEXT,
				  FOREIGN KEY(channel_id) REFERENCES channels(id))''')
    
    conn.commit()
    conn.close()
    

def insert_channels(channels:list) -> int:
	"""
	capable of ``inserting`` and ``updating`` channels | detects channels automatically if they exist or new
	"""
	conn = sqlite3.connect(DB)
	c = conn.cursor()
	
	for channel in channels:
		# Get channel ID
		try:
			# Check if channel already exists
			c.execute('SELECT id FROM channels WHERE name = ?', 
					(channel['name'],))
			channel_id = id[0] if (id := c.fetchone()) else None
		except Exception as e: 
			print(f"Error fetching channel ID: {e}")
			return 500
		# If channel doesn't exist, insert it
		if not channel_id:
			# Insert channel
			c.execute('''INSERT OR IGNORE INTO channels 
						(tvg_id, name, logo_url, stream_url)
						VALUES (?, ?, ?, ?)''',
						(channel['tvg_id'], channel['name'], 
						channel['logo'], channel['url']))
			
			# Get channel ID after insert if channel was new
			c.execute('SELECT id FROM channels WHERE stream_url = ?', 
						(channel['url'],))
			channel_id = c.fetchone()[0] if not channel_id else channel_id
			
			# Insert groups
			for group_name in channel['groups']:
				# Insert group if not exists
				# List of allowed group names
				allowed_groups = [
					'Undefined', 'Shop', 'General', 'Entertainment', 'Family',
					'Music', 'News', 'Religious', 'Animation', 'Kids',
					'Movies', 'Lifestyle', 'Series', 'Relax', 'Comedy',
					'Outdoor', 'Sports', 'Business', 'Documentary', 'Auto',
					'Classic', 'Education', 'Culture', 'Legislative', 'Weather',
					'Cooking', 'Travel', 'Science'
				]
				# Use group_name if in allowed list, else 'Undefined'
				final_group = group_name if group_name in allowed_groups else 'Undefined'
				# c.execute('INSERT OR IGNORE INTO groups (name) VALUES (?)', 
				# 		(final_group,))
				
				# Get group ID
				c.execute('SELECT id FROM groups WHERE name = ?', (final_group,))
				group_id = c.fetchone()[0]
				
				# Create relationship
				c.execute('INSERT OR IGNORE INTO channel_groups VALUES (?, ?)',
						(channel_id, group_id))
			
			# Insert options
			for option in channel['options']:
				c.execute('INSERT OR IGNORE INTO options (channel_id, option) VALUES (?, ?)',
		(channel_id, option))
		
		# If channel exists, update it | UPDATE
		else:
			try:
				# Update channel if needed
				c.execute('''UPDATE channels
							SET tvg_id = ?, name = ?, logo_url = ?, stream_url = ?
							WHERE id = ?''',
							(channel['tvg_id'], channel['name'], 
							channel['logo'], channel['url'], channel_id))
			except sqlite3.IntegrityError as e:
				print(f"Error updating channel: {e} - {channel['name']}")
				continue
			
			# Update groups
			for group_name in channel['groups']:
				# Insert group if not exists
				# List of allowed group names
				allowed_groups = [
					'Undefined', 'Shop', 'General', 'Entertainment', 'Family',
					'Music', 'News', 'Religious', 'Animation', 'Kids',
					'Movies', 'Lifestyle', 'Series', 'Relax', 'Comedy',
					'Outdoor', 'Sports', 'Business', 'Documentary', 'Auto',
					'Classic', 'Education', 'Culture', 'Legislative', 'Weather',
					'Cooking', 'Travel', 'Science'
				]
				# Use group_name if in allowed list, else 'Undefined'
				final_group = group_name if group_name in allowed_groups else 'Undefined'
				# c.execute('INSERT OR IGNORE INTO groups (name) VALUES (?)', 
				# 		(final_group,))
				
				# Get group ID
				c.execute('SELECT id FROM groups WHERE name = ?', (final_group,))
				group_id = c.fetchone()[0]
				
				# Create or update relationship
				c.execute('REPLACE INTO channel_groups (channel_id, group_id) VALUES (?, ?)',
						(channel_id, group_id))
			# Update options
			for option in channel['options']:
				# Update if exists, else insert
				c.execute('SELECT id FROM options WHERE channel_id = ?', (channel_id,))
				if c.fetchone():
					c.execute('UPDATE options SET option = ? WHERE channel_id = ?',
							(option, channel_id))
				else:
					c.execute('INSERT INTO options (channel_id, option) VALUES (?, ?)',
							(channel_id, option))
	
	conn.commit()
	conn.close()
	
	return 200

def update_channels(channels):
	conn = sqlite3.connect(DB)
	c = conn.cursor()
	
	for channel in channels:
		# Update only if tvg_id exists
		if channel['tvg_id']:
			update_fields = []
			update_values = []
			
			# Check each field and add to update if not None
			if channel['name']:
				update_fields.append('name = ?')
				update_values.append(channel['name'])
			if channel['logo']:
				update_fields.append('logo_url = ?')
				update_values.append(channel['logo'])
			if channel['url']:
				update_fields.append('stream_url = ?')
				update_values.append(channel['url'])
				
			if update_fields:
				# Add tvg_id to values for WHERE clause
				update_values.append(channel['tvg_id'])
				# Construct and execute update query
				query = f'''UPDATE channels 
						   SET {', '.join(update_fields)}
						   WHERE tvg_id = ?'''
				c.execute(query, update_values)
	
	conn.commit()
	conn.close()

def get_channel_count() -> int:
	"""
	Count of channels
	"""
	conn = sqlite3.connect(DB)
	c = conn.cursor()
	
	# Use parameterized query to prevent SQL injection
	c.execute("SELECT COUNT(*) FROM channels")
	count = c.fetchone()[0]
	conn.close()
	return count

def get_channel_by_id(id:int , conn=None) -> list:
    """
    Run in same sql thread if passing conn
    """
    conn = sqlite3.connect(DB) if not conn  else conn
    c = conn.cursor()
    
    # Use parameterized query to prevent SQL injection
    c.execute("SELECT * FROM channels WHERE id = ?", (id,))
    rows = c.fetchall()
    
    conn.close()
    return rows

def get_all_groups():
	"""
	veriety of groups by group id
	"""
	conn = sqlite3.connect(DB)
	c = conn.cursor()
	
	# Use parameterized query to prevent SQL injection
	c.execute("SELECT * FROM groups")
	rows = c.fetchall()
	conn.close()
	return rows

def get_groups_channel() -> list:
	"""
	channels by group id
	"""
	conn = sqlite3.connect(DB)
	c = conn.cursor()
	c.execute("SELECT * FROM channel_groups")
	rows = c.fetchall()
	conn.close()
	return rows

def get_channel_by_group(group_id:int):
	"""
	channels by group id
	"""
	conn = sqlite3.connect(DB)
	c = conn.cursor()
	
	# Use parameterized query to prevent SQL injection
	c.execute('''SELECT channels.id ,channels.tvg_id, channels.name, channels.logo_url, 
				 channels.stream_url 
				 FROM channel_groups 
				 JOIN channels ON channel_groups.channel_id = channels.id 
				 WHERE channel_groups.group_id = ?''', (group_id,))
	
	rows = c.fetchall()
	conn.close()
	return rows

def find_channel_group_by_channel_id(channel_id:int):
	conn = sqlite3.connect(DB)
	c = conn.cursor()
	
	# Use parameterized query to prevent SQL injection
	c.execute('''SELECT groups.name 
				 FROM channel_groups 
				 JOIN groups ON channel_groups.group_id = groups.id 
				 WHERE channel_groups.channel_id = ?''', (channel_id,))
	
	groups = c.fetchall()
	conn.close()
	return [group[0] for group in groups]

# favourites 

def get_favourites():
	conn = sqlite3.connect(DB)
	c = conn.cursor()
	
	# Use parameterized query to prevent SQL injection
	c.execute('''
		 SELECT * from favourites
		 ''')
	rows = c.fetchall()	
	conn.close()
	return rows  

def get_favourite_channels():
	conn = sqlite3.connect(DB)
	c = conn.cursor()
	
	# Use parameterized query to prevent SQL injection
	c.execute('''
		 SELECT channels.id, channels.tvg_id, channels.name, channels.logo_url,
				groups.name,
				channels.stream_url
		 FROM favourites
		 JOIN channels ON favourites.channel_id = channels.id
		 LEFT JOIN channel_groups ON channels.id = channel_groups.channel_id
		 LEFT JOIN groups ON channel_groups.group_id = groups.id
		 ''')
	rows = c.fetchall()
	conn.close()
	return rows

def add_favourite(channel_id:int):
	conn = sqlite3.connect(DB)
	c = conn.cursor()
	
	# Use parameterized query to prevent SQL injection
	c.execute('''
		 INSERT INTO favourites (channel_id) 
		 VALUES (?)''', (channel_id,))
	
	conn.commit()
	conn.close()

def remove_favourite(channel_id:int):
	conn = sqlite3.connect(DB)
	c = conn.cursor()
	
	# Use parameterized query to prevent SQL injection
	c.execute('''
		 DELETE FROM favourites 
		 WHERE channel_id = ?''', (channel_id,))
	
	conn.commit()
	conn.close()

# when importing execute these
create_tables()
# add these groups to the db at db init | first time
# check if groups table is empty

from urllib.parse import unquote
import re

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

conn = sqlite3.connect(DB)
c = conn.cursor()
if c.execute("SELECT COUNT(*) FROM groups").fetchone()[0] == 0:
	groups = [
		'Undefined', 'Shop', 'General', 'Entertainment', 'Family',
		'Music', 'News', 'Religious', 'Animation', 'Kids',
		'Movies', 'Lifestyle', 'Series', 'Relax', 'Comedy',
		'Outdoor', 'Sports', 'Business', 'Documentary', 'Auto',
		'Classic', 'Education', 'Culture', 'Legislative', 'Weather',
		'Cooking', 'Travel', 'Science'
	]
	for group in groups:
		c.execute('INSERT OR IGNORE INTO groups (name) VALUES (?)', (group,))
	conn.commit()
	
	# insert base channels
	channels = parse_m3u(config['app']['base_m3u_path'])
	insert_channels(channels)

conn.close()

# Test the database creation and insertion

# conn = sqlite3.connect(DB)
# c = conn.cursor()
# c.execute("SELECT * FROM channel_groups WHERE channel_id = 1")
# # # # # c.execute("SELECT * FROM channel_groups WHERE channel_id = 2099")
# # # # c.execute("SELECT * FROM groups")
# print(_:=c.fetchall())
# conn.close()

# # urls = [url[-1] for url in _]
# print(_)
print(
	# get_channel_by_group(20)
	# get_groups_channel()
	# get_all_groups()
	# get_channel_count()
	# get_channel_by_group(2),
	find_channel_group_by_channel_id(5416),
	# get_all_groups()
	# [chanel for i ,(id , chanel) in enumerate(get_favourites())]
	# get_favourites(),
	# get_favourite_channels(),
	# add_favourite(71)
	# create_tables(),
	"hi"
	# remove_favourite(1)
	
)

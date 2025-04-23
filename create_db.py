

import sqlite3

def create_tables():
    conn = sqlite3.connect('iptv_channels.db')
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
    c.execute('''CREATE TABLE IF NOT EXISTS channel_groups
                 (channel_id INTEGER,
                  group_id INTEGER,
                  FOREIGN KEY(channel_id) REFERENCES channels(id),
                  FOREIGN KEY(group_id) REFERENCES groups(id))''')
	# create favourites table
    c.execute('''CREATE TABLE IF NOT EXISTS favourites
				 (id INTEGER PRIMARY KEY,
				  channel_id INTEGER,
				  FOREIGN KEY(channel_id) REFERENCES channels(id))''')
    
    conn.commit()
    conn.close()
    

def insert_channels(channels:list):
	conn = sqlite3.connect('iptv_channels.db')
	c = conn.cursor()
	
	for channel in channels:
		# Insert channel
		c.execute('''INSERT OR IGNORE INTO channels 
					 (tvg_id, name, logo_url, stream_url)
					 VALUES (?, ?, ?, ?)''',
					 (channel['tvg_id'], channel['name'], 
					  channel['logo'], channel['url']))
		
		# Get channel ID
		c.execute('SELECT id FROM channels WHERE stream_url = ?', 
				 (channel['url'],))
		channel_id = c.fetchone()[0]
		
		# Insert groups
		for group_name in channel['groups']:
			# Insert group if not exists
			c.execute('INSERT OR IGNORE INTO groups (name) VALUES (?)', 
					   (group_name,))
			
			# Get group ID
			c.execute('SELECT id FROM groups WHERE name = ?', (group_name,))
			group_id = c.fetchone()[0]
			
			# Create relationship
			c.execute('INSERT OR IGNORE INTO channel_groups VALUES (?, ?)',
					  (channel_id, group_id))
	
	conn.commit()
	conn.close()

def update_channels(channels):
	conn = sqlite3.connect('iptv_channels.db')
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
	conn = sqlite3.connect('iptv_channels.db')
	c = conn.cursor()
	
	# Use parameterized query to prevent SQL injection
	c.execute("SELECT COUNT(*) FROM channels")
	count = c.fetchone()[0]
	conn.close()
	return count

def get_all_groups():
	"""
	veriety of groups by group id
	"""
	conn = sqlite3.connect('iptv_channels.db')
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
	conn = sqlite3.connect('iptv_channels.db')
	c = conn.cursor()
	c.execute("SELECT * FROM channel_groups")
	rows = c.fetchall()
	conn.close()
	return rows

def get_channel_by_group(group_id:int):
	"""
	channels by group id
	"""
	conn = sqlite3.connect('iptv_channels.db')
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
	conn = sqlite3.connect('iptv_channels.db')
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
	conn = sqlite3.connect('iptv_channels.db')
	c = conn.cursor()
	
	# Use parameterized query to prevent SQL injection
	c.execute('''
		 SELECT * from favourites
		 ''')
	rows = c.fetchall()	
	conn.close()
	return rows  

def get_favourite_channels():
	conn = sqlite3.connect('iptv_channels.db')
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
	conn = sqlite3.connect('iptv_channels.db')
	c = conn.cursor()
	
	# Use parameterized query to prevent SQL injection
	c.execute('''
		 INSERT INTO favourites (channel_id) 
		 VALUES (?)''', (channel_id,))
	
	conn.commit()
	conn.close()

def remove_favourite(channel_id:int):
	conn = sqlite3.connect('iptv_channels.db')
	c = conn.cursor()
	
	# Use parameterized query to prevent SQL injection
	c.execute('''
		 DELETE FROM favourites 
		 WHERE channel_id = ?''', (channel_id,))
	
	conn.commit()
	conn.close()
	

# Test the database creation and insertion

# conn = sqlite3.connect('iptv_channels.db')
# c = conn.cursor()
# # c.execute("SELECT tvg_id, name FROM channels")
# # c.execute("SELECT * FROM channel_groups WHERE channel_id = 2099")
# c.execute("SELECT * FROM groups")
# (_:=c.fetchall())
# conn.close()

# # urls = [url[-1] for url in _]
# print(_)
print(
	# get_channel_by_group(20)
	# get_groups_channel()
	# get_all_groups()
	# get_channel_count()
	# get_channel_by_group(20)
	# get_all_groups()
	# [chanel for i ,(id , chanel) in enumerate(get_favourites())]
	# get_favourite_channels()
	# add_favourite(71)
	"hi"
	# remove_favourite(1)
	
)

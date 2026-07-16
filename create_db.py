import sqlite3 , configparser , requests , os

# app .conf
config = configparser.ConfigParser()
config.read('app.conf')

# db_path = config['database']['path']
DB = config['app']['channels_db_path']
DB = os.path.expanduser(DB)


from asyncio import Queue
import aiosqlite

class AsyncDB:
	conn=None

	async def init(self): self.conn=await aiosqlite.connect(DB)
	async def colse(self): await self.conn.close()

	async def create_tables(self) ->None:
		# self.conn = sqlite3.connect(DB)
		# c = self.conn.cursor()
		
		# Channels table
		await self.conn.execute('''CREATE TABLE IF NOT EXISTS channels
					(id INTEGER PRIMARY KEY,
					tvg_id TEXT,
					name TEXT,
					logo_url TEXT,
					stream_url TEXT UNIQUE)''')
		
		# Groups table (many-to-many relationship)
		await self.conn.execute('''CREATE TABLE IF NOT EXISTS groups
					(id INTEGER PRIMARY KEY,
					name TEXT UNIQUE)''')
		
		# Channel-Group relationship table
		await self.conn.execute('''CREATE TABLE IF NOT EXISTS channel_groups (
			channel_id INTEGER,
			group_id INTEGER,
			UNIQUE(channel_id, group_id),
			FOREIGN KEY(channel_id) REFERENCES channels(id),
			FOREIGN KEY(group_id) REFERENCES groups(id))''')

		# create favourites table
		await self.conn.execute('''CREATE TABLE IF NOT EXISTS favourites
					(id INTEGER PRIMARY KEY,
					channel_id INTEGER,
					FOREIGN KEY(channel_id) REFERENCES channels(id))''')
		# create options table
		await self.conn.execute('''CREATE TABLE IF NOT EXISTS options
					(id INTEGER PRIMARY KEY,
					channel_id INTEGER,
					option TEXT,
					FOREIGN KEY(channel_id) REFERENCES channels(id))''')
		
		await self.conn.commit()
		# self.conn.close()
		

	async def insert_channels(self, channels:list) -> int:
		"""
		capable of ``inserting`` and ``updating`` channels | detects channels automatically if they exist or new
		"""
		# conn = sqlite3.connect(DB)
		# c = conn.cursor()
		
		for channel in channels:
			# Get channel ID
			try:
				# Check if channel already exists
				cursor = await self.conn.execute('SELECT id FROM channels WHERE name = ?', 
						(channel['name'],))
				channel_id = id[0] if (id := await cursor.fetchone()) else None
				await cursor.close()
			except Exception as e: 
				print(f"Error fetching channel ID: {e}")
				return 500
			# If channel doesn't exist, insert it
			if not channel_id:
				# Insert channel
				cursor = await self.conn.execute('''INSERT OR IGNORE INTO channels 
							(tvg_id, name, logo_url, stream_url)
							VALUES (?, ?, ?, ?)''',
							(channel['tvg_id'], channel['name'], 
							channel['logo'], channel['url']))
				await cursor.close()
				
				await self.conn.commit()
				
				# Get channel ID after insert if channel was new
				cursor = await self.conn.execute('SELECT id FROM channels WHERE stream_url = ?', 
							(channel['url'],))
				channel_id = (await cursor.fetchone())[0] if not channel_id else channel_id
				await cursor.close()
				
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
					cursor = await self.conn.execute('SELECT id FROM groups WHERE name = ?', (final_group,))
					group_id = (await cursor.fetchone())[0]
					await cursor.close()
					
					# Create relationship
					cursor = await self.conn.execute('INSERT OR IGNORE INTO channel_groups VALUES (?, ?)',
							(channel_id, group_id))
					await cursor.close()
					await self.conn.commit()
				
				# Insert options
				for option in channel['options']:
					cursor = await self.conn.execute('INSERT OR IGNORE INTO options (channel_id, option) VALUES (?, ?)',
			(channel_id, option))
					await cursor.close()
					await self.conn.commit()
			
			# If channel exists, update it | UPDATE
			else:
				try:
					# Update channel if needed
					cursor = await self.conn.execute('''UPDATE channels
								SET tvg_id = ?, name = ?, logo_url = ?, stream_url = ?
								WHERE id = ?''',
								(channel['tvg_id'], channel['name'], 
								channel['logo'], channel['url'], channel_id))
					await cursor.close()
					await self.conn.commit()
				except aiosqlite.IntegrityError as e:
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
					cursor = await self.conn.execute('SELECT id FROM groups WHERE name = ?', (final_group,))
					group_id = (await cursor.fetchone())[0]
					await cursor.close()
					
					# Create or update relationship
					cursor = await self.conn.execute('REPLACE INTO channel_groups (channel_id, group_id) VALUES (?, ?)',
							(channel_id, group_id))
					await cursor.close()
				# Update options
				for option in channel['options']:
					# Update if exists, else insert
					cursor = await self.conn.execute('SELECT id FROM options WHERE channel_id = ?', (channel_id,))
					if await cursor.fetchone():
						await cursor.close()
						cursor = await self.conn.execute('UPDATE options SET option = ? WHERE channel_id = ?',
								(option, channel_id))
						await cursor.close()
					else:
						cursor = await self.conn.execute('INSERT INTO options (channel_id, option) VALUES (?, ?)',
								(channel_id, option))
						await cursor.close()
		
		await self.conn.commit()
		# conn.close()
		
		return 200

	async def update_channels(self, channels):
		# conn = sqlite3.connect(DB)
		# c = conn.cursor()
		
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
					cursor = await self.conn.execute(query, update_values)
					await cursor.close()
		
		await self.conn.commit()
		# conn.close()

	async def get_channel_count(self) -> int:
		"""
		Count of channels
		"""
		# conn = sqlite3.connect(DB)
		# c = conn.cursor()
		
		# Use parameterized query to prevent SQL injection
		cursor = await self.conn.execute("SELECT COUNT(*) FROM channels")
		# count = await cursor.fetchone()[0]
		count = await cursor.fetchone()
		await cursor.close()
		return count[0]

	async def get_channel_by_id(self,id:int , conn=None) -> list:
		"""
		Run in same sql thread if passing conn
		"""
		# conn = sqlite3.connect(DB) if not conn  else conn
		# c = conn.cursor()
		
		# Use parameterized query to prevent SQL injection
		cursor = await self.conn.execute("SELECT * FROM channels WHERE id = ?", (id,))
		rows = await cursor.fetchall()
		await cursor.close()
		# conn.close()
		return rows

	async def get_all_groups(self) -> list:
		"""
		veriety of groups by group id
		"""
		# conn = sqlite3.connect(DB)
		# c = conn.cursor()
		
		# Use parameterized query to prevent SQL injection
		cursor = await self.conn.execute("SELECT * FROM groups")
		rows = await cursor.fetchall()
		await cursor.close()
		return rows

	async def get_groups_channel(self) -> list:
		"""
		channels by group id
		"""
		# conn = sqlite3.connect(DB)
		# c = conn.cursor()
		cursor = await self.conn.execute("SELECT * FROM channel_groups")
		rows = await cursor.fetchall()
		await cursor.close()
		return rows

	async def get_channel_by_group(self , group_id:int):
		"""
		channels by group id
		"""
		# conn = sqlite3.connect(DB)
		# c = conn.cursor()
		
		# Use parameterized query to prevent SQL injection
		cursor = await self.conn.execute('''SELECT channels.id ,channels.tvg_id, channels.name, channels.logo_url, 
					channels.stream_url 
					FROM channel_groups 
					JOIN channels ON channel_groups.channel_id = channels.id 
					WHERE channel_groups.group_id = ?''', (group_id,))
		
		rows = await cursor.fetchall()
		await cursor.close()
		return rows

	async def find_channel_group_by_channel_id(self , channel_id:int):
		# conn = sqlite3.connect(DB)
		# c = conn.cursor()
		
		# Use parameterized query to prevent SQL injection
		cursor = await self.conn.execute('''SELECT groups.name 
					FROM channel_groups 
					JOIN groups ON channel_groups.group_id = groups.id 
					WHERE channel_groups.channel_id = ?''', (channel_id,))
		
		groups = await cursor.fetchall()
		await cursor.close()
		return [group[0] for group in groups]

	# favourites 

	async def get_favourites(self):
		# conn = sqlite3.connect(DB)
		# c = conn.cursor()
		
		# Use parameterized query to prevent SQL injection
		cursor = await self.conn.execute('''
			SELECT * from favourites
			''')
		rows = await cursor.fetchall()	
		await cursor.close()
		return rows  

	async def get_favourite_channels(self):
		# conn = sqlite3.connect(DB)
		# c = conn.cursor()
		
		# Use parameterized query to prevent SQL injection
		cursor = await self.conn.execute('''
			SELECT channels.id, channels.tvg_id, channels.name, channels.logo_url,
					groups.name,
					channels.stream_url
			FROM favourites
			JOIN channels ON favourites.channel_id = channels.id
			LEFT JOIN channel_groups ON channels.id = channel_groups.channel_id
			LEFT JOIN groups ON channel_groups.group_id = groups.id
			''')
		rows = await cursor.fetchall()
		await cursor.close()
		return rows

	async def add_favourite(self, channel_id:int):
		# conn = sqlite3.connect(DB)
		# c = conn.cursor()
		
		# Use parameterized query to prevent SQL injection
		cursor = await self.conn.execute('''
			INSERT INTO favourites (channel_id) 
			VALUES (?)''', (channel_id,))
		
		await self.conn.commit()
		await cursor.close()

	async def remove_favourite(self, channel_id:int):
		# conn = sqlite3.connect(DB)
		# c = conn.cursor()
		
		# Use parameterized query to prevent SQL injection
		cursor = await self.conn.execute('''
			DELETE FROM favourites 
			WHERE channel_id = ?''', (channel_id,))
		
		await self.conn.commit()
		await cursor.close()


async def starter():
	db = AsyncDB()
	await db.init()
	# when importing execute these
	await db.create_tables()
	# add these groups to the db at db init | first time
	# check if groups table is empty

	# if not exists base.m3u create one
	if not os.path.exists(config['app']['base_m3u_path']):
		# debug 
		print(config['app']['base_m3u_path'] , 'doesnt exist!!')
		with open(config['update']['update_source'] , "r") as base: source = base.readlines()[1]
		res = requests.get(source)
		if res.status_code==200: 
			with open(config['app']['base_m3u_path'] , "wb") as base: base.write(res.content)

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

	# conn = sqlite3.connect(DB)
	# c = conn.cursor()
	cursor = await db.conn.execute("SELECT COUNT(*) FROM groups")
	res = await cursor.fetchone()
	await cursor.close()
	if res[0] == 0:
		# debug
		print("groups doesnt exist: ", res , "creating groups!")
		groups = [
			'Undefined', 'Shop', 'General', 'Entertainment', 'Family',
			'Music', 'News', 'Religious', 'Animation', 'Kids',
			'Movies', 'Lifestyle', 'Series', 'Relax', 'Comedy',
			'Outdoor', 'Sports', 'Business', 'Documentary', 'Auto',
			'Classic', 'Education', 'Culture', 'Legislative', 'Weather',
			'Cooking', 'Travel', 'Science'
		]
		for group in groups:
			cursor = await db.conn.execute('INSERT OR IGNORE INTO groups (name) VALUES (?)', (group,))
			# debug
			print("inserting group: ",  group)
			await cursor.close()
		await db.conn.commit()
		
		# insert base channels
		channels = parse_m3u(config['app']['base_m3u_path'])
		await db.insert_channels(channels)

	# conn.close()
	await db.colse()

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
	# get_channel_by_id(85),
	# find_channel_group_by_channel_id(5416),
	# get_all_groups()
	# [chanel for i ,(id , chanel) in enumerate(get_favourites())]
	# get_favourites(),
	# get_favourite_channels(),
	# add_favourite(71)
	# create_tables(),
	# remove_favourite(1)
	
)


db=AsyncDB()

async def main():
	await starter()

	await db.init()
	
	# res = await db.get_channel_count()
	res = await db.get_channel_by_id(120)
	# res = await db.get_all_groups()
	# res = await db.get_groups_channel()
	# res = await db.get_channel_by_group(3)
	# res = await db.find_channel_group_by_channel_id(1229)
	# res = await db.get_favourites()
	# res = await db.get_favourite_channels()
	# res = await db.add_favourite(2)
	# res = await db.remove_favourite(2)
	print("res: " , res)

	await db.colse()

import asyncio

asyncio.run(main())
import re
from urllib.parse import unquote

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


# print(parsed_m3u:=parse_m3u('test.m3u8'))

# import requests , json, os, create_db as m3udb

# _url = "https://iptv-org.github.io/iptv/index.m3u"

# playlist_m3u = requests.get(_url)

# if os.path.exists("index.m3u8"):
#     os.remove("index.m3u8")
# with open("index.m3u8","xb") as f: 
#     f.write(playlist_m3u.content)
#     f.close()

# parsed_m3u = parse_m3u("index.m3u8")

# # print(json.dumps(parsed_m3u, indent=4))
# # print((playlist_m3u))

# m3udb.create_tables()
# m3udb.insert_channels(parsed_m3u)



# # print(json.dumps(playlist_m3u, indent=4))

import sqlite3

def get_channel_by_name(name:str , conn=None) -> list:
    """
    Run in same sql thread if passing conn
    """
    conn = sqlite3.connect('iptv_channels.db') if not conn  else conn
    c = conn.cursor()
    
    # Use parameterized query to prevent SQL injection
    c.execute("SELECT * FROM channels WHERE name LIKE ?", ('%' + name + '%',))
    rows = c.fetchall()
    
    # conn.close()
    return rows

def get_channel_by_id(id:int , conn=None) -> list:
    """
    Run in same sql thread if passing conn
    """
    conn = sqlite3.connect('iptv_channels.db') if not conn  else conn
    c = conn.cursor()
    
    # Use parameterized query to prevent SQL injection
    c.execute("SELECT * FROM channels WHERE id = ?", (id,))
    rows = c.fetchall()
    
    # conn.close()
    return rows



# conn= sqlite3.connect("iptv_channels.db")
# cursor = conn.cursor()
# cursor.execute("SELECT * FROM channels WHERE name LIKE '%chopper%'")
# rows = cursor.fetchall()
# for row in rows:
#     print(row)

# print(get_channel_by_name("chopper", conn=conn))
# # print(get_channel_by_id(10656, conn=conn))
# conn.close()


# from kivy.app import App
# from kivy.lang import Builder
# from kivy.properties import ListProperty
# from kivy.uix.recycleview import RecycleView

# kv = '''
# BoxLayout:
#     orientation: 'vertical'
#     BoxLayout:
#         size_hint_y: None
#         height: 48
#         TextInput:
#             id: ti
#             hint_text: 'Enter Index'
#             input_filter: 'int'
#             on_text_validate: rv.jump_to_index(int(self.text))
#             multiline: False
#         Button:
#             text: 'Jump to Index'
#             on_release: rv.jump_to_index(int(ti.text))
#     RV:                          
#         id: rv
#         viewclass: 'Button'  
#         data: self.rv_data_list  
#         scroll_type: ['bars', 'content']
#         bar_width: 10
#         RecycleBoxLayout:
#             default_size: None, dp(48)   
#             default_size_hint: 1, None
#             size_hint_y: None
#             height: self.minimum_height   
#             orientation: 'vertical'
# '''


# class RV(RecycleView):
#     rv_data_list = ListProperty()

#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.rv_data_list = [{'text': f'Button {i}'} for i in range(100)]

#     def jump_to_index(self, index):
#         self.scroll_y = 1 - (index / (len(self.rv_data_list) - 1))  # index/number of widgets


# class RvJumpToApp(App):

#     def build(self):
#         return Builder.load_string(kv)


# RvJumpToApp().run()
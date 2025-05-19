#!/usr/bin/env python3

"""
IPTV Player
"""

import subprocess , requests , os , sys , time ,qrcode
os.environ['KIVY_WINDOW'] = 'sdl2'
os.environ['KIVY_VIDEO'] = 'ffpyplayer'
from kivy.config import Config
Config.set('graphics', 'fullscreen', '1')  # or '1' for true fullscreen
Config.set('graphics', 'borderless', '1')

if sys.platform != "win32":
    # For Linux/macOS: use ~/.local/share or just ~/
    app_data = os.path.join(os.path.expanduser("~"), ".local", "share", "KivstarTV")
else:
    app_data = os.path.join(os.getenv("LOCALAPPDATA") or os.path.expanduser("~"), "KivstarTV")

os.makedirs(app_data, exist_ok=True)
# check if data file exists
if not os.path.exists(os.path.join(app_data, "archive")): os.makedirs(os.path.join(app_data, "archive"), exist_ok=True)

# setting some .conf | for windows
import configparser

config = configparser.ConfigParser()
config.read('app.conf')

# if paths match then skip 
if config['app']['channels_db_path'] == 'sources/channels.db': 
    # update channels_db_path
    config['app']['channels_db_path'] = os.path.join(app_data, "channels.db")
    with open('app.conf', 'w') as configfile:
        config.write(configfile)

if config['update']['archive_path'] == 'archive/':
    # update archive directory
    config['update']['archive_path'] = os.path.join(app_data, "archive/")
    with open('app.conf', 'w') as configfile:
        config.write(configfile)

if config['update']['update_db_path'] == 'sources/update.db':
    # update update_db_path
    config['update']['update_db_path'] = os.path.join(app_data, "update.db")
    with open('app.conf', 'w') as configfile:
        config.write(configfile)


from io import StringIO
from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.video import Video
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.recycleview import RecycleView
from kivy.uix.modalview import ModalView
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.clock import Clock ,mainthread
from kivy.metrics import dp
from kivy.lang.builder import Builder
from kivy.properties import ObjectProperty, StringProperty, NumericProperty , BooleanProperty
import random , datetime, threading , logging , create_db as cdb
from update.main import schedule_update_m3u
from kivy.uix.screenmanager import ScreenManager, Screen
# from kivy.core.video import video_ffpyplayer  as VideoFFPyplayer
# VideoFFPyplayer.logger_level = 'debug'  # Enable FFmpeg debug logs

INFO = """
FloatLayout:
    MDLabel:
        id: info_chanel_no
        on_parent:
            app.widgets_to_hide["info_channel_no"] = self
        text: str(app.chanel_no)[:5]
        font_size: dp(40)  
        size_hint: 0.2, 0.1
        pos_hint: {'right': 0.3, 'center_y': 0.9}
        color: 0.7, 1, 0, 0.7
        # icon: "plus"
        # opacity: 1 if app.channel_input else 0
    
    MDLabel:
        id: info_time
        on_parent:
            app.widgets_to_hide["info_time"] = self
        text: app.get_time()
        halign: "center"
        font_size: sp(17)  
        bold: True
        theme_text_color: "Custom"
        text_color: 0.7, 0.5, 0, 1
        size_hint: 0.2, 0.1
        pos_hint: {'right': 0.9, 'center_y': 0.9}
        md_bg_color: 0.7, 1, 0, 0.7
        # icon: "plus"
        # opacity: 1 if app.channel_input else 0
    
    MDIcon:
        id: channel_favourite
        on_parent:
            app.widgets_to_hide["info_favourite"] = self
        pos_hint: {'right': 0.9, 'center_y': 0.9}
        icon: "heart" if app.is_channel_no_favourite else "heart-outline"
        color: 0.7, 0.1, 0, 0.7
    
    MDLabel:
        on_parent: setattr(app,"update_label" , self)
        text: f"updates are underaway may take a while - {str(app.update_done)}%" if app.update_done < 100 else "updates done"
        halign: "center"
        font_size: sp(17)
        bold: True
        theme_text_color: "Custom"
        text_color: 0.7, 0.5, 0, 0.7
        size_hint: 0.7, 0.1
        pos_hint: {'center_x': 0.5, 'center_y': 0.2}
        # opacity: 0 if app.update_done==100 else 1

    MDLabel:
        id : poweroff_label
        text: "TV will shut down in 5 seconds" 
        halign: "center"
        font_size: sp(17)
        bold: True
        theme_text_color: "Custom"
        text_color: 0.7, 0.5, 0, 0.7
        size_hint: 0.7, 0.1
        pos_hint: {'center_x': 0.5, 'center_y': 0.6}
        opacity: 1 if app.poweroff else 0


    MDCard:
        on_parent:
            app.menu_mode_widgets.append(self)
        size_hint: None, None
        width: dp(400)
        height: dp(600)
        padding: dp(10)
        pos_hint: {'top': 0.98, 'center_x': 0.3}
        md_bg_color: 0.7, 1, 0, 0.7
        MDBoxLayout:
            orientation: "vertical"
            spacing: dp(10)
            MDBoxLayout:
                orientation: "horizontal"
                size_hint_y: None
                height: dp(40)
                spacing: dp(10)
                radius: [dp(10), dp(10), dp(10), dp(10)]
                md_bg_color: 0.7, 1, 0, 1
                MDIcon:
                    icon: "menu-left"
                    font_size: dp(50)
                    pos_hint: {'center_y': 0.5}
                    disabled: True if app.current_gerne == 0 else False
                MDLabel:
                    id : gernes_label
                    # on_parent:
                    #     app.menu_mode_widgets.append(self)
                    text: "Undefined"
                    halign: "right"
                    # md_bg_color: 0.7, 1, 0, 1
                    size_hint: 0.5 , None
                    height: dp(40)
                MDIcon:
                    id: gernes_label_icon
                    icon: "help-circle"
                    pos_hint: {'center_y': 0.5}
                MDLabel:
                    text: ""
                    size_hint_x: 0.3
                MDIcon:
                    icon: "menu-right"
                    font_size: dp(50)
                    disabled: True if app.current_gerne == app.total_gernes else False
                    pos_hint: {'center_y': 0.5}

            MDCard:
                md_bg_color: 0.7, 1, 0.7, 0.7

                CustomRecycleView:
                    id: channels_rv
                    group_id: 1
                    on_parent: 
                        self.init()
                        setattr(app , 'menu_mode_scroll_to_channel', int(self.data[0]['channel_no']))
                        app.menu_mode_widgets.append(self)
                    effect_cls: "ScrollEffect"      # prevents overscrolling
                    scroll_type: ['bars', 'content']
                    bar_width: 10
                    size_hint: 1 , None
                    height: dp(500)
                    # pos_hint: {'top': 0.9, 'center_x': 0.4}

    NeonVolumeSphere:
        id: neon_sphere
        on_parent:
            app.widgets_to_hide["neon_sphere"] = self
        pos_hint: {'center_x': 0.5, 'center_y': 0.2}

#:include kv/volume.kv
        
<LabelChannel@BoxLayout>:
    id : gernes
    channel_no: ''
    icon: ''
    channel_name: ''
    selected: False
    favourite: False
    gerne : ''
    orientation: 'horizontal'
    spacing: dp(10)
    padding: [dp(10) , dp(0), dp(10), dp(0)]
    canvas.before:
        Color:
            rgba: (1, 0.7, 0.2, 0.4) if self.selected else (0.7, 1, 0.4, 0)
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        id: channel_no
        text: str(root.channel_no)
        font_size: dp(20)
        size_hint: 0.1, None
        height: dp(40)
        color: 0.7, 1, 0, 0.7
    AsyncImage:
        id: channel_icon
        source: root.icon 
        on_error: 
            print("error loading icon")
            setattr(self ,"source", "icon.png")
    Label:
        text: root.channel_name
    MDIcon:
        icon: app.get_gerne_icon(root.gerne)  if root.gerne  else ""
    MDIcon:
        icon: "heart" if root.favourite else "heart-outline"
        color: 0.7, 0, 0, 0.7

<CustomRecycleView>:

    viewclass: 'LabelChannel'
    RecycleBoxLayout:
        default_size: None, None
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'
        spacing: dp(10)
        padding: dp(10)
        
"""

REMOTE_MODAL = '''

MDCard:
    id : qr_card
    ip : app.local_ip
    size_hint: None , None
    width: dp(350)
    height: dp(400)
    padding: dp(10)
    pos_hint: {'top': 0.7, 'center_x': 0.5}
    md_bg_color: 0.7, 1, 0, 0.7
    on_parent: app.ip_image_object = self
    MDBoxLayout:
        orientation: "vertical"
        spacing: dp(10)
        radius: dp(20)
        AsyncImage:
            id: qr_image
            source: "icon.png" 
            allow_stretch: True
            keep_ratio: True
            pos_hint: {'center_y': 0.5}
        MDLabel:
            id : gernes_label
            text: f"{qr_card.ip}\\nuse this IP address to connect your remote"
            font_style: "Caption"
            theme_text_color: "Custom"
            text_color: 0.7, 1, 0, 1
            halign: "center"
            size_hint_y: None
            height: dp(40)
'''


class CustomRecycleView(RecycleView):
    group_id = NumericProperty(1)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def init(self, **kwargs):
        # Get the channel data from the database
        # get fav channels
        # print("initing....")
        def clean_url(url):
            if not url or url == " ":
                return "icon.png"
            try:
                # Replace spaces with %20
                return url.replace(" ", "%20")
            except:
                return "icon.png"
        favs = {}
        [favs.update({channel: id}) for i , (id , channel) in enumerate(cdb.get_favourites()) if channel]        

        self.data = [
            {
                "channel_no": str(no),
                "icon": clean_url(icon) if icon and not icon==" " else "icon.png",
                "channel_name": name,
                "selected": i == 0 , # Only the first is selected initially
                "favourite": True if no in favs.keys() else False,
                "gerne" : "",
            }
            for i, (no, domain, name, icon, url) in enumerate(cdb.get_channel_by_group(self.group_id)) if no
        ] if self.group_id != 0 else [
            {
                "channel_no": str(no),
                "icon": icon if icon and not icon==" " else "icon.png",
                "channel_name": name,
                "selected": i == 0 , # Only the first is selected initially
                "favourite": True if no in favs.keys() else False,
                "gerne" : gerne,
            }
            for i, (no, domain, name, icon, gerne ,url) in enumerate(cdb.get_favourite_channels()) if no
        ] # 0 - favourites

    ## during an update ongoing we if we do CRUD : sqlite3.OperationalError: database is locked

    def jump_to_index(self, index):
        try: self.scroll_y = 1 - (index / (len(self.data) - 1))  # index/number of widgets
        except ZeroDivisionError: ...

class IPTVApp(MDApp):

    gernes = None
    gernes_box = True
    current_rv = None
    total_gernes = NumericProperty(28)
    current_gerne = NumericProperty(1)
    current_index = NumericProperty(0)
    # seamphore for inputs
    seamphore_release = BooleanProperty(True)
    remote_thread_closure_callback = None
    remote_connected_to = StringProperty("")
    local_ip = StringProperty("0.0.0.0")
    ip_image_object = None
    # updates (0 - 100)%
    update_done = NumericProperty(0)
    update_label = None
    # modes
    menu_mode = BooleanProperty(False)
    menu_mode_widgets = []
    menu_mode_scroll_to_channel = NumericProperty(0)
    max_chanel_no = (_:= cdb.get_channel_count() if not cdb.get_channel_count() else 11377)
    chanel_no =10
    is_channel_no_favourite = BooleanProperty(False)
    widgets_to_hide = {         # storing widgets to hide later 

    }
    channel_info_label = None   # for displaying the channel number
    channel_input = [           # storing keyboard input for channel number

    ] # channel numbs
    # known number keys which will be checked against the keycode
    num_keys = {
        48: 0,
        49: 1,
        50: 2,
        51: 3,
        52: 4,
        53: 5,
        54: 6,
        55: 7,
        56: 8,
        57: 9,
    }

    # known gernes
    known_gernes = {
    gerne[0]: gerne[1] for gerne in [
        (1, 'Undefined'), (2, 'Shop '), (3, 'General '), (4, 'Entertainment '), (5, 'Family'),
        (6, 'Music'), (7, 'News'), (8, 'Religious'), (9, 'Animation'), (10, 'Kids'),
        (11, 'Movies '), (12, 'Lifestyle'), (13, 'Series'), (14, 'Relax '), (15, 'Comedy'),
        (16, 'Outdoor'), (17, 'Sports'), (18, 'Business'), (19, 'Documentary'), (20, 'Auto'),
        (21, 'Classic '), (22, 'Education '), (23, 'Culture '), (24, 'Legislative '), (25, 'Weather'),
        (26, 'Cooking'), (27, 'Travel'), (28, 'Science') 
        ]
    }
    # known_gernes
    # known gernes icons
    known_gernes_icons = {
        1: "help-circle",
        2: "src/icons/shop-48.png",
        3: "src/icons/globe-94.png",
        4: "src/icons/popcorn-48.png",
        5: "home-heart",
        6: "music",
        7: "newspaper",
        8: "hands-pray",
        9: "filmstrip",
        10: "puzzle",
        11: "src/icons/movies-48.png",
        12: "spa",
        13: "layers",
        14: "src/icons/spa-flower-48.png",
        15: "src/icons/comedy-48.png",
        16: "tree",
        17: "trophy",
        18: "briefcase",
        19: "book",
        20: "car",
        21: "src/icons/classic-64.png",
        22: "src/icons/student-male-48.png",
        23: "src/icons/aztec-48.png",
        24: "src/icons/scales-48.png",
        25: "weather-partly-cloudy",
        26: "chef-hat",
        27: "airplane",
        28: "flask",
        0: "heart",  # Favourites
    }
    
    # favourites
    known_gernes[0] = "Favourites"

    volume = NumericProperty(0.5)        # default stream volume
    poweroff = BooleanProperty(False)  # poweroff state
    exit_event = None  # exit event

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # bind keyboard
        Window.bind(on_key_down=self.on_key_down)

    def build(self):
        self.m3u8_source = "https://linear-11.frequency.stream/dist/glewedtv/11/hls/master/playlist.m3u8" if not cdb.get_channel_by_id(self.chanel_no)[0] else cdb.get_channel_by_id(self.chanel_no)[0][-1]
        self.video = Video(
            source=self.m3u8_source, 
            state='play',
            allow_stretch=True, 
            keep_ratio=False , 
            # eos=self.on_video_state_change , 
            preview="icon.png",
            volume=self.volume, 
        )
        self.icon = "icon.png"  # Set the Kivy application icon  # Set the application icon
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(self.video)
        
        # btn_layout = BoxLayout(size_hint_y=0.2)
        
        
        # stop_btn = Button(text="Stop")
        # stop_btn.bind(on_press=self.stop_video)
        # box = BoxLayout(orientation='horizontal')
        # box.add_widget(TextInput(text=self.m3u8_source, multiline=False, size_hint_x=0.8))
        # box.add_widget(Button(text="Play", size_hint_x=0.2))
        # box.children[0].bind(on_press=self.jump_to_chanel)
        
        # switch_btn = Button(text="Switch Stream")
        # switch_btn.bind(on_press=self.switch_stream)
        
        # # add to hide dict
        # self.widgets_to_hide["switch_btn"] = switch_btn
        # self.widgets_to_hide["box"] = box

        # btn_layout.add_widget(box)
        # btn_layout.add_widget(switch_btn)
        # fl = FloatLayout()
        # info = Label(
        #     text = int(''.join(map(str, self.channel_input))) if self.channel_input else "0",
        #     size_hint=(0.2, 0.1), 
        #     pos_hint={'x': 0.4, 'y': 0.9},
        #     # opacity = 1 if self.channel_input else 0,
        # )


        # fl.add_widget(info)
        # add to hide dict
        self.info = Builder.load_string(INFO)
        self.channel_info_label = self.info.ids.info_chanel_no
        # Clock.schedule_once(lambda dt : setattr(self,"gernes_box" , False) , 7)
        # self.widgets_to_hide["info"] = info

        # Log display label
        # Log display label with better styling
        self.log_label = Label(
            size_hint_y=None,
            height=200,
            text_size=(None, None),
            halign='left',
            valign='top',
            padding=(10, 10),
            color=(0.7, 1, 0, 0.7),
        )
        scroll = ScrollView(size_hint=(0.9, 0.7), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        scroll.add_widget(self.log_label)

        # add to hide dict
        self.widgets_to_hide["scroll"] = scroll

        # layout.add_widget(scroll)

        # self.redirect_logs_to_label()  # Redirect logs to label
        
        # layout.add_widget(btn_layout)
        # Enable DEBUG logging for ffpyplayer
        # from kivy.core.video import video_ffpyplayer  as VideoFFPyplayer
        # VideoFFPyplayer.logger_level = 'debug'  # Enable FFmpeg debug logs
        os.environ['KIVY_LOG_LEVEL'] = 'debug'

        # Redirect ALL logs (including Kivy's Logger) to your label
        self.setup_logging()

        sm = ScreenManager()
        screen = Screen(name='main')
        screen.add_widget(layout)
        screen.add_widget(scroll)
        screen.add_widget(self.info)
        sm.add_widget(screen)

        # Create a ModalView
        if not hasattr(self , "modal"):
            # setattr(self , "ip" , "192.186.1.7")
            self.modal = ModalView(size_hint=(0.4, 0.4), auto_dismiss=True ,overlay_color=(0.1, 0.1, 0.4, 0.4))
            # Load the content of the modal from a KV file
            self.modal.add_widget(Builder.load_string(REMOTE_MODAL))
        # bind self.remote_connected_to to the modal
        self.bind(remote_connected_to=lambda instance, value: self.dismiss_modal() if value else self.show_modal())

        return sm
    
    def on_start(self):
        # # Start the video when the app starts
        # self.video.play()
        # # Set the initial channel number
        # self.channel_info_label.text = str(self.chanel_no)
        # # Set the initial volume
        # self.video.volume = self.volume
        # # Set the initial time
        # self.info.ids.info_time.text = str(datetime.datetime.now().strftime("%H:%M:%S"))
        # # Set the initial favourite icon
        # self.info.ids.channel_favourite.icon = "heart" if self.is_channel_no_favourite else "heart-outline"
        # Prevent screen timeout/sleep
        Window.allow_screensaver = False
        # hide menu
        [setattr(widget,"opacity", 0) for widget in self.menu_mode_widgets]
        # check update
        Clock.schedule_once(lambda dt: self.check_update() , 10)
        # show the remote-modal
        self.show_modal()
    
    def on_pre_stop(self):
        # Stop the video when the app is closed
        self.video.state = 'stop'
        self.video.unload()
        # Stop the remote server if it's running
        if hasattr(self, 'remote_thread_closure_callback') and self.remote_thread_closure_callback:
            self.remote_thread_closure_callback()
        # Stop the manager server if it's running
        if hasattr(self, 'manager_thread_closure_callback') and self.manager_thread_closure_callback:
            self.manager_thread_closure_callback()
    
    def get_qr(self,content:str):
        qr = qrcode.make(content)

        qr.save(
            _:=os.path.join(app_data,"qr.png")
        )
        return _

    @mainthread
    def dismiss_modal(self): self.modal.dismiss() if hasattr(self , "modal") else None
    @mainthread
    def show_modal(self):
        # Show the modal
        self.modal.open()

    @mainthread
    def set_local_ip(self, ip:str):
        # print("setting local ip: ", ip , self.ip_image_object)
        Clock.schedule_once(lambda dt: setattr(self,"local_ip" , ip) , 0.2)
        Clock.schedule_once(lambda dt: setattr(self.ip_image_object.ids.qr_image,"source" , self.get_qr(ip)) , 0.5)

    def check_update(self):
        @mainthread
        def set_attr(value):
            setattr(self,"update_done" , value)
        @mainthread
        def hide_update_label(): Clock.schedule_once(lambda dt : setattr(self.update_label,"opacity" , 0) ,0.5) if self.update_done == 100 else None

        def update():
            # set update_done=10
            print(self.update_done)
            set_attr(10)
            time.sleep(1)
            _ = schedule_update_m3u()
            # set update_done=100
            set_attr(100)
            # opacity = 0
            hide_update_label()
        #
        threading.Thread(target=update,daemon=True).start()

    # Poweroff/Exit
    def exit_application(self):
        if self.poweroff:
            """Properly exit the application"""
            print("[App] Shutting down...")
            
            # Clean up resources
            self.video.state = 'stop'
            self.video.unload()
            
            # Close remote connections
            if hasattr(self, 'remote_thread_closure_callback') and self.remote_thread_closure_callback:
                self.remote_thread_closure_callback()
            
            # Close manager server
            if hasattr(self, 'manager_thread_closure_callback') and self.manager_thread_closure_callback:
                self.manager_thread_closure_callback()
            
            # Stop the app
            self.stop()

    def on_key_down(self, window, keycode, scancode, codepoint, modifiers):
            """
            keycode is an integer, scancode unused here, codepoint is the actual character.
            """
            # spacebar → play/stop toggle
            # if keycode == 32:  # space
            #     for _ in self.widgets_to_hide.values():
            #         if _.opacity == 0: _.opacity = 1
            #         else: _.opacity = 0
            if keycode == 105: ... # i
            elif keycode == 27:  # esc
                # clear thew channel typed no.
                setattr(self,"channel_input" , []) if self.channel_input else print("channel input is empty" , self.channel_input , self.chanel_no)
                # clear the channel info label 
                self.channel_info_label.text = str(self.chanel_no)  
                # hide all widgets
                for widget in self.widgets_to_hide.values():
                  if widget.opacity:
                    setattr(widget,"opacity", 0)
                  else: 
                    setattr(widget,"opacity", 1) 

            # digits 0-9 → jump to channel 
            elif keycode in self.num_keys.keys():
                print(self.num_keys[keycode])
                self.channel_input.append(self.num_keys[keycode])
                # update the channel_info no. label
                self.channel_info_label.text = "".join(map(str , self.channel_input))
                # opacity
                for widget in self.widgets_to_hide.values():
                  if not widget.opacity:
                    setattr(widget,"opacity", 1)
    
            ### menu mode
            elif keycode == 13:  # enter
                if not self.menu_mode : 
                    # change the channel
                    if self.channel_input:
                        _ = self.jump_to_chanel(int(''.join(map(str, self.channel_input))))
                        # clear thew channel typed no.
                        self.channel_input = []
                        # update channel favourite label
                        # update the channel info_favourite label
                        self.is_channel_no_favourite = True if  self.chanel_no in [chanel for i ,(id , chanel) in enumerate(cdb.get_favourites())] else False
                # menu mode ON
                else: 
                    # switch to channel
                    self.jump_to_chanel(self.menu_mode_scroll_to_channel)
                    print("menu mode channel no: ", self.menu_mode_scroll_to_channel)
                    # update the channel info_favourite label
                    self.is_channel_no_favourite = True if  self.chanel_no in [chanel for i ,(id , chanel) in enumerate(cdb.get_favourites())] else False

            # volume controll up/down arrows ↑ ↓
            elif keycode in (273, 274):  
                if not self.menu_mode:
                    # make volume label visible
                    [setattr(widget,"opacity", 1) for widget in self.widgets_to_hide.values()]  
                    if keycode == 273:  # up arrow ↑ 
                        self.volume = min(self.volume + 0.1, 1.0)
                        setattr(self.video, "volume" , self.volume)
                    else: # down arrow ↓
                        self.volume = max(self.volume - 0.1, 0.0)
                        setattr(self.video, "volume" , self.volume)
                # menu mode ON
                else:
                    if keycode == 273:  # up arrow ↑ 
                        self.move_selection(-1)
                    else: # down arrow ↓
                        self.move_selection(1)

            # change channel  back & forth ← →
            elif keycode in (276, 275):
                if not self.menu_mode:
                    # left/right arrows → switch stream
                    if keycode == 276: # left arrow ←
                        self.chanel_no = max(self.chanel_no - 1, 0)
                        self.jump_to_chanel(self.chanel_no)
                        self.channel_info_label.text = str(self.chanel_no)
                        # update time
                        self.info.ids.info_time.text = str(datetime.datetime.now().strftime("%H:%M"))
                        # check fav
                        if self.chanel_no in [chanel for i ,(id , chanel) in enumerate(cdb.get_favourites())] :
                            self.is_channel_no_favourite = True
                        else: 
                            self.is_channel_no_favourite = False
                    else: # right arrow  →
                        self.chanel_no = min(self.chanel_no + 1, self.max_chanel_no)
                        self.jump_to_chanel(self.chanel_no)
                        self.channel_info_label.text = str(self.chanel_no)
                        # update time
                        self.info.ids.info_time.text = str(datetime.datetime.now().strftime("%H:%M"))
                        # check fav
                        if self.chanel_no in [chanel for i ,(id , chanel) in enumerate(cdb.get_favourites())] :
                            self.is_channel_no_favourite = True
                        else:
                            self.is_channel_no_favourite = False
                # menu mode ON
                else:
                    if keycode == 276: # left arrow ←
                        self.switch_gerne(0)
                    else: # right arrow  →
                        self.switch_gerne(1)
            
            # elif codepoint == "d":  # a
            #     self.switch_gerne(1)
            # elif codepoint == "a":
            #     self.switch_gerne(0)
            # elif codepoint == 'w':
            #     self.move_selection(-1)
            # elif codepoint == 's':
            #     self.move_selection(1)
            # menu mode
            elif codepoint == 'm':
                # toggle menu mode
                self.menu_mode = not self.menu_mode
                # enable/disable menu mode widgets
                [setattr(widget,"opacity", 0 if not self.menu_mode else 1) for widget in self.menu_mode_widgets]
                # hide other widgets
                [setattr(widget,"opacity", 0) for widget in self.widgets_to_hide.values()]
            # mark favourite ❤
            elif codepoint == 'f':  
                if self.seamphore_release:
                    # lock the seamphore
                    Clock.schedule_once(lambda dt: setattr(self,"seamphore_release" , False) , 0)
                    # make remote label visible
                    [setattr(widget,"opacity", 1) for widget in self.widgets_to_hide.values()]
                    # update the channel info_favourite label
                    self.is_channel_no_favourite = True if not self.chanel_no in [chanel for i ,(id , chanel) in enumerate(cdb.get_favourites())] else False
                    # get the channel by id
                    self.mark_channel_favourite()
                    # release the seamphore
                    Clock.schedule_once(lambda dt: setattr(self,"seamphore_release" , True) , 0)


            print( "keycode: ", keycode , type(keycode) , "scancode: ", scancode , "codepoint: ", codepoint , "modifiers: ", modifiers)
            # left/right arrows → switch stream
            # elif keycode == 276:  # left arrow
            #     self.current_stream = (self.current_stream - 1) % len(self.streams)
            #     self.play_stream()
            # elif keycode == 275:  # right arrow
            #     self.current_stream = (self.current_stream + 1) % len(self.streams)
            #     self.play_stream()
            return True
    @mainthread
    def remote_keys(self, keycode):
        # if keycode == 105: ... # i
        print("keycode: ", keycode)
        if keycode == "esc":  # esc
            # clear thew channel typed no.
            setattr(self,"channel_input" , []) if self.channel_input else print("channel input is empty" , self.channel_input , self.chanel_no)
            # clear the channel info label 
            self.channel_info_label.text = str(self.chanel_no)  
            # hide all widgets
            for widget in self.widgets_to_hide.values():
                if widget.opacity:
                    setattr(widget,"opacity", 0)
                else: 
                    setattr(widget,"opacity", 1) 

        # digits 0-9 → jump to channel 
        elif keycode in "".join(map(str,[*range(0,10)])):
            # print(self.num_keys[keycode])
            self.channel_input.append(int(keycode))
            # update the channel_info no. label
            self.channel_info_label.text = "".join(map(str , self.channel_input))
            # opacity
            for widget in self.widgets_to_hide.values():
                if not widget.opacity:
                    setattr(widget,"opacity", 1)

        ### menu mode
        elif keycode == "enter":  # enter
            if not self.menu_mode : 
                # change the channel
                if self.channel_input:
                    _ = self.jump_to_chanel(int(''.join(map(str, self.channel_input))))
                    # clear thew channel typed no.
                    self.channel_input = []
                    # update channel favourite label
                    # update the channel info_favourite label
                    self.is_channel_no_favourite = True if  self.chanel_no in [chanel for i ,(id , chanel) in enumerate(cdb.get_favourites())] else False
            # menu mode ON
            else: 
                # switch to channel
                self.jump_to_chanel(self.menu_mode_scroll_to_channel)
                print("menu mode channel no: ", self.menu_mode_scroll_to_channel)
                # update the channel info_favourite label
                self.is_channel_no_favourite = True if  self.chanel_no in [chanel for i ,(id , chanel) in enumerate(cdb.get_favourites())] else False

        # volume controll up/down arrows ↑ ↓
        elif keycode in ("up", "down"):  
            if not self.menu_mode:
                # make volume label visible
                [setattr(widget,"opacity", 1) for widget in self.widgets_to_hide.values()]
                if keycode == "up":  # up arrow ↑ 
                    self.volume = min(self.volume + 0.1, 1.0)
                    setattr(self.video, "volume" , self.volume)
                else: # down arrow ↓
                    self.volume = max(self.volume - 0.1, 0.0)
                    setattr(self.video, "volume" , self.volume)
            # menu mode ON
            else:
                if keycode == "up":  # up arrow ↑ 
                    self.move_selection(-1)
                else: # down arrow ↓
                    self.move_selection(1)

        # change channel  back & forth ← →
        elif keycode in ("back", "forth"):
            if not self.menu_mode:
                # left/right arrows → switch stream
                if keycode == "back": # left arrow ←
                    self.chanel_no = max(self.chanel_no - 1, 0)
                    self.jump_to_chanel(self.chanel_no)
                    self.channel_info_label.text = str(self.chanel_no)
                    # update time
                    self.info.ids.info_time.text = str(datetime.datetime.now().strftime("%H:%M"))
                    # check fav
                    if self.chanel_no in [chanel for i ,(id , chanel) in enumerate(cdb.get_favourites())] :
                        self.is_channel_no_favourite = True
                    else: 
                        self.is_channel_no_favourite = False
                    # show the channel info label
                    # make volume label visible
                    [setattr(widget,"opacity", 1) for widget in self.widgets_to_hide.values()]
                else: # right arrow  →
                    self.chanel_no = min(self.chanel_no + 1, self.max_chanel_no)
                    self.jump_to_chanel(self.chanel_no)
                    self.channel_info_label.text = str(self.chanel_no)
                    # update time
                    self.info.ids.info_time.text = str(datetime.datetime.now().strftime("%H:%M"))
                    # check fav
                    if self.chanel_no in [chanel for i ,(id , chanel) in enumerate(cdb.get_favourites())] :
                        self.is_channel_no_favourite = True
                    else:
                        self.is_channel_no_favourite = False
                    # show the channel info label
                    # make volume label visible
                    [setattr(widget,"opacity", 1) for widget in self.widgets_to_hide.values()]
            # menu mode ON
            else:
                if keycode == "back": # left arrow ←
                    self.switch_gerne(0)
                else: # right arrow  →
                    self.switch_gerne(1)
        # menu mode
        elif keycode == 'menu':
            # toggle menu mode
            self.menu_mode = not self.menu_mode
            # enable/disable menu mode widgets
            [setattr(widget,"opacity", 0 if not self.menu_mode else 1) for widget in self.menu_mode_widgets]
            # hide other widgets
            [setattr(widget,"opacity", 0) for widget in self.widgets_to_hide.values()]
        # mark favourite ❤
        elif keycode == 'fav':  
            if self.seamphore_release:
                # lock the seamphore
                Clock.schedule_once(lambda dt: setattr(self,"seamphore_release" , False) , 0)
                # make favourite label visible
                [setattr(widget,"opacity", 1) for widget in self.widgets_to_hide.values()]
                # update the channel info_favourite label
                self.is_channel_no_favourite = True if not self.chanel_no in [chanel for i ,(id , chanel) in enumerate(cdb.get_favourites())] else False
                # get the channel by id
                self.mark_channel_favourite()
                # release the seamphore
                Clock.schedule_once(lambda dt: setattr(self,"seamphore_release" , True) , 0)
        # +/ and -/ max/min volume
        elif keycode == 'max_volume':
            if self.volume < 1.0:
                self.volume = 1.0
                Clock.schedule_once(lambda dt : setattr(self.video, "volume" , self.volume), 0)
            else: 
                self.volume = 0.5
                Clock.schedule_once(lambda dt : setattr(self.video, "volume" , self.volume), 0)
        elif keycode == 'min_volume':
            if self.volume > 0.0:
                self.volume = 0.0
                Clock.schedule_once(lambda dt : setattr(self.video, "volume" , self.volume), 0)
            else:
                self.volume = 0.5
                Clock.schedule_once(lambda dt : setattr(self.video, "volume" , self.volume), 0)
        # power off
        elif keycode == 'power': 
            self.poweroff = not self.poweroff
            if self.poweroff:
                # show the power off label
                # [setattr(widget,"opacity", 1) for widget in self.widgets_to_hide.values()]
                # exit the application
                self.exit_event = Clock.schedule_once(lambda dt: self.exit_application() , 5)
            else: self.exit_event.cancel() if self.exit_event else None
            
    
    def get_time(self): return datetime.datetime.now().strftime("%H:%M")
    def get_gerne_icon(self , g: str):
        _ = [
            key for i , (key , gerne) in enumerate(self.known_gernes.items()) if gerne.strip() == g
        ]
        print("gerne: ", g , "key: ", _)
        return self.known_gernes_icons[_[0]] if _ else "help-circle"
    
    def switch_gerne(self , direction:int):
        """
        ``1`` for next gerne
        ``0`` for previous gerne
        """
        # change gernes
        self.current_gerne  =  min(self.current_gerne + 1, self.total_gernes) if direction else max(self.current_gerne - 1, 0) # 0 - favourites ❤
        # change gernes label gerne
        self.info.ids.gernes_label.text = self.known_gernes[self.current_gerne]
        # change gernes label icon
        self.info.ids.gernes_label_icon.icon = self.known_gernes_icons[self.current_gerne]
        # set the next group id
        self.info.ids.channels_rv.group_id = self.current_gerne
        self.info.ids.channels_rv.init()
        # take the selection back to the first channel
        self.current_index = 0
        rv = self.current_rv if self.current_rv else  self.info.ids.channels_rv
        rv.refresh_from_data()
        rv.jump_to_index(self.current_index)
        # Set the first item["channel"] as menu_mode_scroll_to_channel
        try:self.menu_mode_scroll_to_channel = int(self.info.ids.channels_rv.data[0]['channel_no']) if self.info.ids.channels_rv else 0
        except IndexError: print("IndexError: ", self.info.ids.channels_rv.data)

    def mark_channel_favourite(self): 
        if self.menu_mode:
            rv = self.info.ids.channels_rv  # or wherever your RecycleView is
            data = rv.data
            for w in rv.children[0].children:
                    if hasattr(w, 'channel_no') and w.channel_no == data[self.current_index]['channel_no']:
                        rv.data[self.current_index]['favourite'] = not rv.data[self.current_index]['favourite']
                        print("marking as favourite: ", w.channel_no)
                        # add to db
                        cdb.add_favourite(w.channel_no) if rv.data[self.current_index]['favourite'] else cdb.remove_favourite(w.channel_no)
                        rv.refresh_from_data()
                        break
        else: 
            cdb.add_favourite(self.chanel_no) if self.chanel_no not in [chanel for i ,(id , chanel) in enumerate(cdb.get_favourites())] else cdb.remove_favourite(self.chanel_no)

    def move_selection(self, direction):
        rv = self.current_rv if self.current_rv else  self.info.ids.channels_rv  # or wherever your RecycleView is
        data = rv.data
        old_index = self.current_index
        new_index = max(0, min(len(data) - 1, old_index + direction))
        if old_index != new_index:
            data[old_index]['selected'] = False
            data[new_index]['selected'] = True
            self.current_index = new_index
            rv.refresh_from_data()
            # rv.scroll_to(new_index)
         # Scroll to the widget at new_index
        # Wait for the next frame to ensure widgets are updated
        def do_scroll(dt):
            # Find the widget for new_index
            for w in rv.children[0].children:
                if hasattr(w, 'channel_no') and w.channel_no == data[new_index]['channel_no']:
                    # set channel no to menu_mode_scroll_to_channel
                    self.menu_mode_scroll_to_channel = int(w.channel_no)
                    print("scrolling to: ", w.channel_no)
                    # rv.scroll_y(w)
                    rv.jump_to_index(new_index)
                    break
        # from kivy.clock import Clock
        Clock.schedule_once(do_scroll, 0)

    def setup_logging(self):
        """Configure logging to capture FFmpeg output"""
        Logger.handlers = []
        
        class LogHandler(logging.Handler):
            def __init__(self, label):
                super().__init__()
                self.label = label
                
            def emit(self, record):
                msg = self.format(record) + "\n"
                Clock.schedule_once(lambda dt: self.update_label(msg))
                
            def update_label(self, message):
                self.label.text += message
                if len(self.label.text) > 2000:
                    self.label.text = self.label.text[-1800:]
                # with open("iptv.log", "a") as f:
                #     f.write(message)
        
        handler = LogHandler(self.log_label)
        handler.setLevel(logging.DEBUG)
        Logger.addHandler(handler)
        logging.root.addHandler(handler)
        logging.root.setLevel(logging.DEBUG)


    def jump_to_chanel(self, channel_no:int):
        # print(instance.parent.children[1].text)
        if channel_no and type(channel_no) == int:
            self.chanel_no = channel_no  # int(instance.parent.children[1].text) if instance.parent.children[1].text.isdigit() else 0
            # get the channel by id
            _ = cdb.get_channel_by_id(self.chanel_no)[0]  # [(10656, 'KukhnyaTV.ru', 'Кухня ТВ HD', 'https://i.imgur.com/7jxZnuS.png', 'http://stream01.vnet.am/KukhnyaTv/mono.m3u8')]
            # switch to the channel
            if _:
                self.video.state = 'stop'
                self.video.unload()
                def _set():
                    self.video.source = _[-1]
                    self.video.state = 'play'
                    print('chanel no: ' ,_[0])
                    print('chanel name: ' ,_[1])
                    self.title = _[2]

                Clock.schedule_once(lambda dt: _set(), 1)
                print("Jump to channel:", self.chanel_no , _[-1])
            # self.video.state = 'stop'

     
    
        
    
app_ = IPTVApp()

# main.py

from remote_server import RemoteSocketServer

def handle_remote_command(action):
    # print(f"[COMMAND] {action.upper()} {value}")
    app_.remote_keys(action)
    # Plug this into your IPTV logic

def set_local_ip(ip):
    app_.set_local_ip(ip)

def set_connected_client(ip):
    app_.remote_connected_to = ip

# Start remote socket server
remote_thread = RemoteSocketServer(callback_handler=handle_remote_command,set_ip_callback=set_local_ip,set_client_ip_callback=set_connected_client)

def close():
    remote_thread.running = False
    remote_thread.join()

#
remote_thread.daemon = True
remote_thread.start()

from manager import ChannelManager

# start channel manager server

channel_manager = ChannelManager()

channel_manager.start()

# Your Kivy app definition and run logic

app_.run()

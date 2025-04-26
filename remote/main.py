# remote
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.button import MDRectangleFlatButton
from kivy.clock import Clock ,mainthread
from kivy.lang.builder import Builder
from kivy.uix.label import Label
from kivymd.toast import toast
from kivymd.app import MDApp
import socket,os,threading

class RemoteButton(MDRectangleFlatButton):
    pass

class CircularButton(MDRectangleFlatButton):
    text = StringProperty()
    is_primary = BooleanProperty(False)
    is_power = BooleanProperty(False)

class NavButton(MDRectangleFlatButton):
    text = StringProperty()
    is_center = BooleanProperty(False)

MAIN = """
Screen:
    name: "main"
    Image:
        source: "src/space.jpg"
        allow_stretch: True
        keep_ratio: True
        size_hint: None, None
        size: self.texture_size
    FloatLayout:

        MDLabel:
            text: "Enter IP Address\\nthat you see on the TV screen"
            halign: "center"
            font_size: dp(18)
            bold: True
            theme_text_color: "Custom"
            text_color: app.theme_cls.primary_color
            pos_hint: {"center_x": 0.5, "center_y": 0.9}

        MDTextField:
            id: ip_address
            mode: "rectangle"
            hint_text: "e.g. 192.168.1.5"
            # helper_text: "e.g. 192.168.1.5"
            size_hint_x: None
            width: root.width * 0.8
            on_focus: 
                print(self.y)   
            pos_hint:  {"center_x": 0.5, "center_y": 0.6 if self.focus else 0.2}
        
        MDIconButton:
            icon: "check"
            pos_hint: {"center_x": 0.8, "center_y": 0.1}
            on_release: app.connect(ip_address.text)
"""

class RemoteAPP(MDApp):
    ir_glow = BooleanProperty(False)
    # socket backend
    client_socket = None
    is_connected = BooleanProperty(False)
    tv_name = StringProperty("TV : ON")

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"	
        
        sm = ScreenManager()
        # main screen
        sm.add_widget(Builder.load_string(MAIN))
        # remote screen
        sm.add_widget(Builder.load_file("kv/remote.kv"))
        # set current screen
        sm.current = "main"
        return sm

    def on_start(self): 
         # init the socket connection
        ...

    def connect(self , ip:str):
        def socket_connect(client_ , address):
            soc = socket.socket()
            soc.connect(address)
            print(f"Connected to {address}")
            client_ = soc
        # connect to the socket server
        try:
            _=threading.Thread(target=socket_server , args=((ip, 9090),), daemon=True)
            _.start()
            # _.join()
        except socket.error as e:
            print(f"Error connecting to server: {e}")
            Clock.schedule_once(lambda dt: toast("Error connecting to server"), 0.5)
            return
        finally:
            # self.is_connected = True
            # get the tv name
            try:
                self.client_socket.sendall("tv_name".encode())
                tv_name = self.client_socket.recv(1024).decode()
                print(f"TV Name: {tv_name}")
                self.tv_name = f"TV : {tv_name}"
            except Exception as e:
                print(f"Error getting TV name: {e}")
                Clock.schedule_once(lambda dt: toast("Error getting TV name"), 0.5)
                
            self.tv_name = f"TV : {ip}"
            # switch to remote screen
            self.root.current = "remote"

    def switch_to_main(self):
        # switch to main screen
        self.root.current = "main"

    def key_press(self , key:str):
        # send the key press to the socket server
        print(f"Key pressed: {key}")
        # send the key press to the socket server
        if self.is_connected:
            try:
                self.client_socket.sendall(key.encode())
            except Exception as e:
                print(f"Error sending data: {e}")
                Clock.schedule_once(lambda dt: toast("Error sending data\nreconnect your device"), 0.5)
                self.is_connected = False
                self.tv_name = "TV : OFF"
                self.switch_to_main()
        else:
            print("Not connected to server")

app_ = RemoteAPP()

# socket server
def socket_server(address:tuple):
    # start the socket server
    try:
        s = socket.socket()
        s.connect(address)
        # if connection sucessful add to app_ client
        app_.client_socket = s
        app_.is_connected = True

    except socket.error as e:
        print(f"Error connecting to server: {e}")
        return
    
    finally:
        try:
            while app_.is_connected:
                _ = s.recv(1024).decode()
                print(f"Received: {_.strip()}")
        except Exception as e:
            print(f"Error receiving data: {e}")
            app_.is_connected = False
            app_.tv_name = "TV : OFF"
            app_.switch_to_main()

app_.run()

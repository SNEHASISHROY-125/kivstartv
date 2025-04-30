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
import time

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
    
        MDSpinner:
            id: spinner
            size_hint: None, None
            size: dp(30), dp(30)
            pos_hint: {"center_x": 0.5, "center_y": 0.5}
            active: app.is_trying_to_connect
            color: app.theme_cls.primary_color
"""

class RemoteAPP(MDApp):
    ir_glow = BooleanProperty(False)
    # socket backend
    client_socket = None
    is_trying_to_connect = BooleanProperty(False)
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
        # bind is_connected to the sm
        self.bind(is_connected=lambda instance, value: self.switch_screen("remote" if value else "main"))
        return sm

    def switch_screen(self , screen:str):
        # hault the spinner
        self.is_trying_to_connect = False
        # switch screen
        if screen == "main":
            Clock.schedule_once(lambda dt: setattr(self.root, "current" , "main"), 0.5)
        elif screen == "remote":
            Clock.schedule_once(lambda dt: setattr(self.root, "current" , "remote"), 0.5)
        else:
            print("Invalid screen name")
            return
    
    @mainthread
    def show_toast(self , message:str):
        '''
        ``connected`` : connected to the tv
        ``disconnected`` : disconnected from the tv
        ``error`` : error connecting to the tv
        '''
        # show toast message
        if message == "connected":
            Clock.schedule_once(lambda dt: toast("Connected to TV"), 0.5)
        elif message == "disconnected":
            Clock.schedule_once(lambda dt: toast("Disconnected from TV"), 0.5)
        elif message == "wrong_ip":
            Clock.schedule_once(lambda dt: toast("Wrong ip address entered"), 0.5)
        elif message == "tv_down":
            Clock.schedule_once(lambda dt: toast("TV is off"), 0.5)
        

    def on_start(self): 
         # init the socket connection
        ...

    def connect(self , ip:str):
        # connect to the socket server
        try:
            _=threading.Thread(target=socket_server , args=((ip, 9090),), daemon=True)
            _.start()
        except socket.error as e:
            # print(f"Error connecting to server: {e}")
            # Clock.schedule_once(lambda dt: toast("Error connecting to server"), 0.5)
            return
        
        if self.is_connected:
            try:
                self.client_socket.sendall("tv_name".encode())
                tv_name = self.client_socket.recv(1024).decode()
                print(f"TV Name: {tv_name}")
                self.tv_name = f"TV : {tv_name}"
            except Exception as e:
                print(f"Error getting TV name: {e}")
                Clock.schedule_once(lambda dt: toast("Error getting TV name"), 0.5)
                
            self.tv_name = f"TV : {ip}"

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
                # self.switch_to_main()
        else:
            print("Not connected to server")

app_ = RemoteAPP()

# socket server
def socket_server(address:tuple):
    app_.is_trying_to_connect = True
    # start the socket server
    try:
        s = socket.socket()
        s.connect(address)
        # if connection sucessful add to app_ client
        app_.client_socket = s
        app_.is_connected = True
        # give time to recognize the connection
        time.sleep(0.5)
        app_.is_trying_to_connect = False
        # send toast
        app_.show_toast("connected")

    except socket.error as e:
        if e.errno == 113:
            print(f"Error connecting to server: {e}")
            app_.show_toast("wrong_ip")
        elif e.errno == 111:
            print(f"Error connecting to server: {e}")
            app_.show_toast("tv_down")
        # set connection tries to false
        app_.is_trying_to_connect = False

        return
    
    try:
        while app_.is_connected:
            _ = s.recv(1024).decode()
            print(f"Received: {_.strip()}") if _ else setattr(app_,"is_connected" , False)
    except Exception as e:
        print(f"Error receiving data: {e}")
        app_.is_connected = False
        app_.tv_name = "TV : OFF"
        # app_.switch_to_main()
    finally:
        # show toast
        app_.show_toast("disconnected")

app_.run()

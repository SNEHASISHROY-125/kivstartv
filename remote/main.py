# remote
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.button import MDRectangleFlatButton
from kivy.clock import Clock ,mainthread
import socket, os,threading , time, db
from kivy.lang.builder import Builder
from kivy.uix.label import Label
from kivymd.toast import toast
from kivymd.app import MDApp
from kivy.core import window

from lbarcam.LbarCam import LegacyScanner

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
        id: background
        source: ""
        allow_stretch: True
        keep_ratio: True
        size_hint: None, None
        size: self.texture_size
    FloatLayout:

        MDLabel:
            id : instruction
            text: "Scan the QR Code\\nthat you see on the TV screen"
            halign: "center"
            font_size: dp(18)
            bold: True
            theme_text_color: "Custom"
            text_color: app.theme_cls.primary_color
            # md_bg_color: app.theme_cls.bg_darkest
            pos_hint: {"center_x": 0.5, "center_y": 0.95}

        # MDTextField:
        #     id: ip_address
        #     mode: "rectangle"
        #     hint_text: "e.g. 192.168.1.5"
        #     # helper_text: "e.g. 192.168.1.5"
        #     size_hint_x: None
        #     width: root.width * 0.8
        #     on_focus: 
        #         print(self.y)   
        #     pos_hint:  {"center_x": 0.5, "center_y": 0.6 if self.focus else 0.2}
        
        # MDIconButton:
        #     icon: "check"
        #     pos_hint: {"center_x": 0.8, "center_y": 0.1}
        #     on_release: app.connect(ip_address.text)

        MDFillRoundFlatButton:
            text: "Connect Remote"
            pos_hint: {"center_x": 0.5, "center_y": 0.2}
            font_size: dp(20)
            md_bg_color: app.theme_cls.primary_color
            on_release: app.open_scanner()
            

        MDSpinner:
            id: spinner
            size: dp(30), dp(30)
            size_hint: None, None
            active: app.is_trying_to_connect
            color: app.theme_cls.primary_color
            pos_hint: {"center_x": 0.8, "center_y": 0.95}
"""

## TV STATUS
TV_OFF = "TV is off\nPlease turn on the TV and try again"
TV_SYNC = "Scan the QR Code\nthat you see on the TV screen"


class RemoteAPP(MDApp):
    # socket backend
    is_trying_to_connect = BooleanProperty(False)
    is_connected = BooleanProperty(False)
    tv_name = StringProperty("TV : ON")
    check_previous_session_ip = None
    ir_glow = BooleanProperty(False)
    schedule_scan_close = None
    schedule_scan = None
    client_socket = None
    scanner = None

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"	
        
        sm = ScreenManager()
        # main screen
        sm.add_widget(Builder.load_string(MAIN))
        # remote screen
        sm.add_widget(Builder.load_file("kv/remote.kv"))
        # set current screen
        # sm.current = "main"
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
            Clock.schedule_once(lambda dt : setattr(self.root.get_screen("main").ids.instruction , "text" , TV_SYNC) ,1)
        elif message == "disconnected":
            Clock.schedule_once(lambda dt: toast("Disconnected from TV"), 0.5)
        elif message == "wrong_ip":
            Clock.schedule_once(lambda dt: toast("Wrong ip address entered"), 0.5)
        elif message == "tv_down":
            if not self.root.get_screen("main").ids.instruction.text == TV_OFF:
                Clock.schedule_once(lambda dt: toast("TV is off"), 0.5)
                Clock.schedule_once(lambda dt : setattr(self.root.get_screen("main").ids.instruction , "text" , TV_OFF) ,1)


    def on_start(self):
        # init the socket connection
        # init the scanner
        self.scanner = LegacyScanner(self.validate_ip ,recycle_frames=True)
        # check previous session ip
        self.check_previous_session_ip = Clock.schedule_interval(lambda dt: self.check_previous_session(), 1.5)
        #
        # self.root.canvas.ask_update()
        Clock.schedule_once(lambda dt : setattr(self.root.get_screen("main").ids.background , "source" , "src/space.jpg") ,1) #os.path.join(os.getcwd(), "assets", "background.jpg")

    def on_resume(self):
        return True
    
    def check_previous_session(self): 
        # print("Previous session remotes: ", _)
        if not self.is_connected:
            _ = db.get_remotes()
            self.connect(_[0][0]) if _ else None

    def open_scanner(self):
        if not self.schedule_scan:
            self.scanner.start_preview()
            self.schedule_scan = Clock.schedule_interval(lambda dt: self.scanner.scan(), 0.7)
            self.schedule_scan_close = Clock.schedule_interval(lambda dt: self.close_scanner(), 0.7)
        else:
            self.scanner.start_preview()
            Clock.unschedule(self.schedule_scan)
            self.schedule_scan = Clock.schedule_interval(lambda dt: self.scanner.scan(), 0.7)

    def close_scanner(self):
        if self.is_connected and self.schedule_scan_close:
            # if self.schedule_scan:
            Clock.unschedule(self.schedule_scan) if self.schedule_scan else None
            self.schedule_scan = None
            Clock.unschedule(self.schedule_scan_close) if self.schedule_scan_close else None
            self.schedule_scan_close = None

            self.scanner.stop_preview()

    def validate_ip(self, frame ,ip:str):
        print(f"Validating IP: {ip}")
        if ip:
            # validate the ip address
            parts = ip[0].split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not part.isdigit() or not (0 <= int(part) <= 255):
                    return False
            # try to connect to the socket server
            try:
                _ = self.connect(ip[0])
                if _ and self.schedule_scan:
                    # if self.schedule_scan:
                    Clock.unschedule(self.schedule_scan)
                    self.schedule_scan = None

                    self.scanner.stop_preview()
                    print("Connection successful")
                else:
                    print("Connection failed" , _)
            except Exception as e: print(f"Error connecting to server: {e}")


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
            return True
        # else:
        #     print("is_connected is " , self.is_connected)

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
    
    # add it to the database
    db.add_remote(address[0], str(time.strftime("%Y-%m-%d %H:%M:%S")))
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

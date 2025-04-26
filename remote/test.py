from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.behaviors import CircularRippleBehavior, BackgroundColorBehavior
from kivymd.theming import ThemableBehavior
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.widget import Widget

KV = '''
<RemoteButton>:
    size_hint: None, None
    size: dp(60), dp(60)
    md_bg_color: app.theme_cls.primary_color if self.is_primary else root.theme_cls.bg_dark
    radius: dp(12)
    
    MDLabel:
        text: root.text
        font_size: dp(24)
        theme_text_color: "Custom"
        text_color: "white" if not root.disabled else "gray"
        halign: "center"
        valign: "center"

<CircularButton>:
    size_hint: None, None
    size: dp(50), dp(50)
    radius: [self.height/2]
    md_bg_color: app.theme_cls.primary_color if self.is_primary else (1, 0.2, 0.2, 1) if self.is_power else root.theme_cls.bg_dark
    
    MDLabel:
        text: root.text
        font_size: dp(24)
        theme_text_color: "Custom"
        text_color: "white" if not root.disabled else "gray"
        halign: "center"
        valign: "center"

<NavButton>:
    size_hint: None, None
    size: dp(50), dp(50)
    md_bg_color: app.theme_cls.primary_color if self.is_center else root.theme_cls.bg_dark
    radius: dp(12)
    
    MDLabel:
        text: root.text
        font_size: dp(24)
        theme_text_color: "Custom"
        text_color: "white" if not root.disabled else "gray"
        halign: "center"
        valign: "center"

MDScreen:
    md_bg_color: 0.07, 0.07, 0.07, 1
    
    MDCard:
        id: remote
        orientation: "vertical"
        size_hint: None, None
        size: dp(320), dp(650)
        pos_hint: {"center_x": 0.5, "center_y": 0.5}
        padding: dp(20)
        spacing: dp(10)
        radius: dp(24)
        elevation: 10
        md_bg_color: 0.1, 0.1, 0.1, 1
        
        MDBoxLayout:
            size_hint_y: None
            height: dp(30)
            spacing: dp(10)
            
            MDLabel:
                text: "SMART REMOTE"
                font_size: dp(18)
                bold: True
                theme_text_color: "Custom"
                text_color: app.theme_cls.primary_color
                
            MDBoxLayout:
                size_hint_x: None
                width: dp(80)
                spacing: dp(5)
                
                MDIcon:
                    icon: "battery"
                    theme_text_color: "Custom"
                    text_color: 0.7, 0.7, 0.7, 1
                    font_size: dp(16)
                    
                MDLabel:
                    text: "85%"
                    font_size: dp(14)
                    theme_text_color: "Custom"
                    text_color: 0.7, 0.7, 0.7, 1
        
        CircularButton:
            id: power_btn
            size: dp(50), dp(50)
            pos_hint: {"center_x": 0.5}
            is_power: True
            text: "power"
            on_release: app.power_toggle()
        
        MDGridLayout:
            id: nav_pad
            cols: 3
            rows: 3
            spacing: dp(8)
            size_hint_y: None
            height: dp(166)
            pos_hint: {"center_x": 0.5}
            
            Widget:
            NavButton:
                id: nav_up
                text: "arrow-up"
                on_release: app.nav_press("up")
            Widget:
            
            NavButton:
                id: nav_left
                text: "arrow-left"
                on_release: app.nav_press("left")
            NavButton:
                id: nav_center
                text: "OK"
                is_center: True
                on_release: app.nav_press("ok")
            NavButton:
                id: nav_right
                text: "arrow-right"
                on_release: app.nav_press("right")
            
            Widget:
            NavButton:
                id: nav_down
                text: "arrow-down"
                on_release: app.nav_press("down")
            Widget:
        
        MDBoxLayout:
            id: volume_controls
            size_hint_y: None
            height: dp(60)
            spacing: dp(8)
            pos_hint: {"center_x": 0.5}
            
            RemoteButton:
                id: vol_down
                text: "volume-minus"
                on_release: app.volume_change(-5)
            
            RemoteButton:
                id: mute_btn
                text: "volume-high"
                on_release: app.toggle_mute()
            
            RemoteButton:
                id: vol_up
                text: "volume-plus"
                on_release: app.volume_change(5)
        
        MDBoxLayout:
            id: channel_controls
            size_hint_y: None
            height: dp(60)
            spacing: dp(8)
            pos_hint: {"center_x": 0.5}
            
            RemoteButton:
                id: ch_down
                text: "chevron-left"
                on_release: app.channel_change(-1)
            
            RemoteButton:
                id: ch_up
                text: "chevron-right"
                on_release: app.channel_change(1)
        
        MDGridLayout:
            id: num_pad
            cols: 3
            spacing: dp(8)
            size_hint_y: None
            height: dp(240)
            
            RemoteButton:
                id: num_1
                text: "1"
                on_release: app.num_press(1)
            
            RemoteButton:
                id: num_2
                text: "2"
                on_release: app.num_press(2)
            
            RemoteButton:
                id: num_3
                text: "3"
                on_release: app.num_press(3)
            
            RemoteButton:
                id: num_4
                text: "4"
                on_release: app.num_press(4)
            
            RemoteButton:
                id: num_5
                text: "5"
                on_release: app.num_press(5)
            
            RemoteButton:
                id: num_6
                text: "6"
                on_release: app.num_press(6)
            
            RemoteButton:
                id: num_7
                text: "7"
                on_release: app.num_press(7)
            
            RemoteButton:
                id: num_8
                text: "8"
                on_release: app.num_press(8)
            
            RemoteButton:
                id: num_9
                text: "9"
                on_release: app.num_press(9)
            
            RemoteButton:
                id: num_asterisk
                text: "*"
                on_release: app.special_press("*")
            
            RemoteButton:
                id: num_0
                text: "0"
                on_release: app.num_press(0)
            
            RemoteButton:
                id: num_hash
                text: "#"
                on_release: app.special_press("#")
        
        MDBoxLayout:
            id: function_buttons
            size_hint_y: None
            height: dp(60)
            spacing: dp(8)
            pos_hint: {"center_x": 0.5}
            
            RemoteButton:
                id: back_btn
                text: "arrow-left"
                on_release: app.function_press("back")
            
            RemoteButton:
                id: home_btn
                text: "home"
                on_release: app.function_press("home")
            
            RemoteButton:
                id: menu_btn
                text: "menu"
                on_release: app.function_press("menu")
        
        MDBoxLayout:
            id: status_bar
            size_hint_y: None
            height: dp(40)
            spacing: dp(20)
            padding: dp(10), 0
            radius: dp(20)
            md_bg_color: 0, 0, 0, 0.3
            pos_hint: {"center_x": 0.5}
            
            MDBoxLayout:
                spacing: dp(5)
                
                MDIcon:
                    id: tv_icon
                    icon: "television"
                    theme_text_color: "Custom"
                    text_color: app.theme_cls.primary_color
                    font_size: dp(16)
                
                MDLabel:
                    id: tv_status
                    text: "TV: On"
                    font_size: dp(14)
                    theme_text_color: "Custom"
                    text_color: 0.9, 0.9, 0.9, 1
            
            MDBoxLayout:
                spacing: dp(5)
                
                MDIcon:
                    id: wifi_icon
                    icon: "wifi"
                    theme_text_color: "Custom"
                    text_color: app.theme_cls.primary_color
                    font_size: dp(16)
                
                MDLabel:
                    id: wifi_status
                    text: "Connected"
                    font_size: dp(14)
                    theme_text_color: "Custom"
                    text_color: 0.9, 0.9, 0.9, 1
'''

class RemoteButton(ThemableBehavior):
    text = StringProperty()
    is_primary = BooleanProperty(False)

class CircularButton(ThemableBehavior, BackgroundColorBehavior, ButtonBehavior):
    text = StringProperty()
    is_primary = BooleanProperty(False)
    is_power = BooleanProperty(False)

class NavButton(ThemableBehavior, BackgroundColorBehavior, ButtonBehavior):
    text = StringProperty()
    is_center = BooleanProperty(False)

class SmartRemoteApp(MDApp):
    is_tv_on = BooleanProperty(True)
    current_channel = NumericProperty(1)
    current_volume = NumericProperty(50)
    is_muted = BooleanProperty(False)
    
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        return Builder.load_string(KV)
    
    def power_toggle(self):
        self.is_tv_on = not self.is_tv_on
        self.root.ids.tv_status.text = f"TV: {'On' if self.is_tv_on else 'Off'}"
        self.toggle_buttons_state()
        print(f"TV turned {'on' if self.is_tv_on else 'off'}")
    
    def toggle_buttons_state(self):
        state = not self.is_tv_on
        for id in ['vol_down', 'vol_up', 'mute_btn', 'ch_down', 'ch_up', 
                  'nav_up', 'nav_down', 'nav_left', 'nav_right', 'nav_center',
                  'num_1', 'num_2', 'num_3', 'num_4', 'num_5', 'num_6', 
                  'num_7', 'num_8', 'num_9', 'num_0', 'num_asterisk', 'num_hash',
                  'back_btn', 'home_btn', 'menu_btn']:
            self.root.ids[id].disabled = state
    
    def volume_change(self, delta):
        if not self.is_tv_on:
            return
        self.current_volume = max(0, min(100, self.current_volume + delta))
        if self.is_muted:
            self.toggle_mute()
        print(f"Volume changed to {self.current_volume}")
    
    def toggle_mute(self):
        if not self.is_tv_on:
            return
        self.is_muted = not self.is_muted
        self.root.ids.mute_btn.text = "volume-off" if self.is_muted else "volume-high"
        print(f"Volume {'muted' if self.is_muted else 'unmuted'}")
    
    def channel_change(self, delta):
        if not self.is_tv_on:
            return
        self.current_channel = max(1, min(999, self.current_channel + delta))
        print(f"Channel changed to {self.current_channel}")
    
    def num_press(self, num):
        if not self.is_tv_on:
            return
        print(f"Number {num} pressed")
    
    def special_press(self, char):
        if not self.is_tv_on:
            return
        print(f"{char} button pressed")
    
    def nav_press(self, direction):
        if not self.is_tv_on:
            return
        print(f"{direction.capitalize()} navigation pressed")
    
    def function_press(self, function):
        if not self.is_tv_on:
            return
        print(f"{function.capitalize()} button pressed")

if __name__ == "__main__":
    SmartRemoteApp().run()
from kivymd.tools.hotreload.app import MDApp
import os
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.uix.screenmanager import ScreenManager, Screen

KV_DIR = os.path.join(os.path.dirname(__file__), "kv")

# remote
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivymd.uix.button import MDRectangleFlatButton

class RemoteButton(MDRectangleFlatButton):
    pass

class CircularButton(MDRectangleFlatButton):
    text = StringProperty()
    is_primary = BooleanProperty(False)
    is_power = BooleanProperty(False)

class NavButton(MDRectangleFlatButton):
    text = StringProperty()
    is_center = BooleanProperty(False)


class MyApp(MDApp):
	ir_glow = BooleanProperty(False)
	is_tv_on = BooleanProperty(False)
	current_channel = NumericProperty(1)
	current_volume = NumericProperty(50)
	is_muted = BooleanProperty(False)
    # ... your app code ...
	KV_FILES = [os.path.join(KV_DIR, "remote.kv"),]
	DEBUG = True
	def build_app(self):
		self.title = "My App"
		# self.theme_cls.primary_palette = "Blue"
		# self.theme_cls.accent_palette = "Pink"
		# self.theme_cls.theme_style = "Light"
		##
		self.theme_cls.theme_style = "Dark"
		self.theme_cls.primary_palette = "Blue"	
		# sm = ScreenManager()
		# sm.add_widget(sc:=Screen(name="main"))
		# sc.add_widget(Builder.load_file("menu.kv"))

		return Factory.Main()
	

MyApp().run()
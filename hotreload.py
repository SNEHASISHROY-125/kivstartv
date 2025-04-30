from kivymd.tools.hotreload.app import MDApp
import os
from kivy.lang import Builder
from kivy.clock import mainthread
import random
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
	volume = NumericProperty(50)
    # ... your app code ...
	KV_FILES = [os.path.join(KV_DIR, "volume.kv"),]
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
	
	previous_volume = 50  # Store previous volume for mute toggle

	@mainthread
	def toggle_mute(self):
		neon = self.root.children[0].ids.neon_sphere
		if getattr(self, 'is_muted', False) or neon.volume == 0:
			# Unmute: restore previous volume
			neon.volume = getattr(self, 'previous_volume', 50)
			self.is_muted = False
		else:
			# Mute: store current volume and set to 0
			self.previous_volume = neon.volume
			neon.volume = 0
			self.is_muted = True

	@mainthread
	def random_volume(self):
		try:
			# print(self.root.children[0].ids)
			neon = self.root.children[0].ids.neon_sphere
			value = random.randint(0, 100)
			# neon.volume = value
			self.volume = value
			print(f"Volume: {value}")
			self.is_muted = False if value > 0 else True
		except Exception as e:
			print(f"Error in random_volume: {e}")

MyApp().run()
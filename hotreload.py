from kivymd.tools.hotreload.app import MDApp
import os
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.uix.screenmanager import ScreenManager, Screen

KV_DIR = os.path.join(os.path.dirname(__file__), "kv")

class MyApp(MDApp):
    # ... your app code ...
	KV_FILES = [os.path.join(KV_DIR, "info.kv"),]
	DEBUG = True
	def build_app(self):
		self.title = "My App"
		self.theme_cls.primary_palette = "Blue"
		self.theme_cls.accent_palette = "Pink"
		self.theme_cls.theme_style = "Light"
		sm = ScreenManager()
		sm.add_widget(sc:=Screen(name="main"))
		# sc.add_widget(Builder.load_file("menu.kv"))

		return Factory.Info()
	

MyApp().run()
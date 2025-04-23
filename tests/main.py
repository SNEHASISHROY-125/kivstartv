import subprocess
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics.texture import Texture
from kivy.graphics import Rectangle
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.logger import Logger
import logging
import os , random

class IPTVPlayer(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'

        # bind keyboard
        Window.bind(on_key_down=self.on_key_down)
        
        # Video display area
        self.video_texture = None
        with self.canvas:
            self.video_rect = Rectangle()
        
        # Log display
        self.log_label = Label(
            size_hint_y=None,
            height=200,
            text_size=(None, None),
            halign='left',
            valign='top',
            padding=(10, 10)
        )
        scroll = ScrollView(size_hint=(1, 0.3))
        scroll.add_widget(self.log_label)
        self.add_widget(scroll)
        
        # Controls
        controls = BoxLayout(size_hint_y=0.1)
        self.play_btn = Button(text='Play')
        self.stop_btn = Button(text='Stop')
        self.switch_btn = Button(text='Switch Stream')
        
        self.play_btn.bind(on_press=self.play_stream)
        self.stop_btn.bind(on_press=self.stop_stream)
        self.switch_btn.bind(on_press=self.switch_stream)
        
        controls.add_widget(self.play_btn)
        controls.add_widget(self.stop_btn)
        controls.add_widget(self.switch_btn)
        self.add_widget(controls)
        
        # FFmpeg process
        self.ffmpeg_process = None
        self.streams = []
        
        self.current_stream = 0
        
        # Setup logging
        self.setup_logging()

        # …existing code…
    def on_key_down(self, window, keycode, scancode, codepoint, modifiers):
            """
            keycode is an integer, scancode unused here, codepoint is the actual character.
            """
            # spacebar → play/stop toggle
            if keycode == 32:  # space
                if self.ffmpeg_process:
                    self.stop_stream()
                else:
                    self.play_stream()
            # left/right arrows → switch stream
            elif keycode == 276:  # left arrow
                self.current_stream = (self.current_stream - 1) % len(self.streams)
                self.play_stream()
            elif keycode == 275:  # right arrow
                self.current_stream = (self.current_stream + 1) % len(self.streams)
                self.play_stream()
            return True

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
                if len(self.label.text) > 10000:
                    self.label.text = self.label.text[-5000:]
                with open("iptv.log", "a") as f:
                    f.write(message)
        
        handler = LogHandler(self.log_label)
        handler.setLevel(logging.DEBUG)
        Logger.addHandler(handler)
        logging.root.addHandler(handler)
        logging.root.setLevel(logging.DEBUG)

    def play_stream(self, instance=None):
        """Start playing the current stream"""
        self.stop_stream()
        
        stream_url = random.choice(self.streams)
        self.log_message(f"\nStarting stream: {stream_url}")
        
        # FFmpeg command to output raw RGB frames
        cmd = [
            "ffmpeg",
            "-i", stream_url,
            "-f", "image2pipe",
            "-pix_fmt", "rgb24",
            "-vcodec", "rawvideo",
            "-an", "-sn",
            "-loglevel", "debug",
            "-"
        ]
        
        try:
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                bufsize=10**8
            )
            
            # Start log reader thread
            threading.Thread(
                target=self.read_logs,
                args=(self.ffmpeg_process.stderr,),
                daemon=True
            ).start()
            
            # Start frame updater
            Clock.schedule_interval(self.update_frame, 1/60.0)
            
        except Exception as e:
            self.log_message(f"Error starting FFmpeg: {str(e)}")

    def stop_stream(self ):
        """Stop the current stream"""
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            self.ffmpeg_process = None
        Clock.unschedule(self.update_frame)
        self.log_message("Stream stopped")

    def switch_stream(self, instance):
        """Switch to next stream"""
        self.current_stream = (self.current_stream + 1) % len(self.streams)
        self.play_stream()
        self.log_message(f"Switched to stream {self.current_stream}")

    def read_logs(self, stderr):
        """Read FFmpeg logs from stderr"""
        while True:
            line = stderr.readline().decode("utf-8", errors="ignore")
            if not line:
                break
            self.log_message(line.strip())

    def update_frame(self, dt):
        """Update video texture with new frame"""
        if not self.ffmpeg_process:
            return
            
        width, height = 640, 360  # Default resolution
        
        try:
            # Read raw frame
            frame_size = width * height * 3
            raw_frame = self.ffmpeg_process.stdout.read(frame_size)
            
            if not raw_frame:
                self.log_message("No frame received - stream ended?")
                self.stop_stream()
                return
                
            # Create/update texture
            if not self.video_texture:
                self.video_texture = Texture.create(
                    size=(width, height),
                    colorfmt='rgb'
                )
                self.video_texture.flip_vertical()
                self.video_rect.texture = self.video_texture
                self.video_rect.size = (width, height)
                
            self.video_texture.blit_buffer(raw_frame, colorfmt='rgb')
            
        except Exception as e:
            self.log_message(f"Frame error: {str(e)}")
            self.stop_stream()

    def log_message(self, message):
        """Thread-safe log update"""
        Clock.schedule_once(lambda dt: self._update_log(message))

    def _update_log(self, message):
        """Actually update the log display"""
        self.log_label.text += message + "\n"
        with open("iptv.log", "a") as f:
            f.write(message + "\n")

class IPTVApp(App):
    def build(self):
        # Enable debug logging
        os.environ['KIVY_LOG_LEVEL'] = 'debug'
        return IPTVPlayer()

    def on_stop(self):
        # Clean up when app closes
        self.root.stop_stream()

if __name__ == '__main__':
    IPTVApp().run()
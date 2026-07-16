# from kivy.app import App
# from kivy.uix.widget import Widget
# from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Rectangle
from kivy.graphics import Callback
# from kivy.graphics.context_instructions import ResetContext
from kivy.graphics.texture import Texture
from kivy.clock import Clock , mainthread
from kivy.core.window import Window
from kivy.uix.image import Image

# from dev.tcpComm import start_tcp_server
# from dev.tcpClient import send_msg
from core.linux.mpv.helpers._events import (
    BaseEvents,
    on_ready,
    on_start,
    on_end,
    on_play,
    on_pause,
    on_pos,
    on_duration,
    on_volume,
    on_speed,
    on_buffering,
    on_error,
    on_log
)

import ctypes

bin_abs_path = "core/linux/mpv/libs/x86_64/libmpv_bridge.so"

mpv = ctypes.CDLL(
    bin_abs_path
)



mpv.create_player.restype = ctypes.c_int
mpv.create_render.restype = ctypes.c_int


mpv.set_texture.argtypes=[
    ctypes.c_uint
]


mpv.render.argtypes=[
    ctypes.c_int,
    ctypes.c_int
]

mpv.init_gl.restype = ctypes.c_int

class MPVEvent(ctypes.Structure):

    _fields_ = [

        ("event", ctypes.c_int),

        ("name", ctypes.c_char * 64),

        ("number", ctypes.c_double),

        ("flag", ctypes.c_int)

    ]

CALLBACK = ctypes.CFUNCTYPE(
    None,
    ctypes.POINTER(MPVEvent)
)

RENDER_CALLBACK = ctypes.CFUNCTYPE(None)

mpv.mpv_set_render_callback.argtypes = [
    RENDER_CALLBACK
]

mpv.mpv_set_render_callback.restype = ctypes.c_void_p

mpv.mpv_set_callback.argtypes = [
    CALLBACK
]

mpv.mpv_set_options.argtypes = [
    ctypes.c_char_p,
    ctypes.c_char_p
]

mpv.mpv_set_options.restype = ctypes.c_int

mpv.load.argtypes = [ctypes.c_char_p]
mpv.load.restype = ctypes.c_int

# ---------- seek ----------
mpv.seek.argtypes = [ctypes.c_double]
mpv.seek.restype = ctypes.c_int

# ---------- skip ----------
mpv.skip.argtypes = [ctypes.c_double]
mpv.skip.restype = ctypes.c_int

# ---------- current position ----------
mpv.pos.argtypes = []
mpv.pos.restype = ctypes.c_double

# ---------- duration ----------
mpv.duration.argtypes = []
mpv.duration.restype = ctypes.c_double

# ---------- volume ----------
mpv.volume.argtypes = [ctypes.c_double]
mpv.volume.restype = ctypes.c_int

mpv.volume_get.argtypes = []
mpv.volume_get.restype = ctypes.c_double

# ---------- speed ----------
mpv.speed.argtypes = [ctypes.c_double]
mpv.speed.restype = ctypes.c_int

mpv.speed_get.argtypes = []
mpv.speed_get.restype = ctypes.c_double

# ---------- mute ----------
mpv.mute.argtypes = [ctypes.c_int]
mpv.mute.restype = ctypes.c_int

mpv.mute_get.argtypes = []
mpv.mute_get.restype = ctypes.c_int

class MPVWidget(BoxLayout):
    '''
    MPV GPU Accelerated Media Player Port for Kivy
    '''

    texture=None
    # internals
    _render_cb=None
    _update = None
    _listener = None
    # ui
    _playing = False
    _muted = False
    _duration = None
    _pos = None
    _volume = None
    _speed = None
    _buffering = False
    _err = None
    # events
    ev_pos = None

    def __init__(self,**kwargs):

        super().__init__(**kwargs)

        # ### didnt work
        # self.texture.min_filter = "linear"
        # self.texture.mag_filter = "linear"

        # self.texture.wrap = "clamp_to_edge"

        # register events
        on_ready.bind(self)
        on_start.bind(self)
        on_end.bind(self)
        on_play.bind(self)
        on_pause.bind(self)
        on_pos.bind(self)
        on_duration.bind(self)
        on_volume.bind(self)
        on_speed.bind(self)
        on_buffering.bind(self)
        on_error.bind(self)
        on_log.bind(self)
        # 

    def mpv_listener(self, event):

        e = event.contents

        # print("EVENT :", e.event)

        # print("NAME  :", e.name.decode())

        # print("NUM   :", e.number)

        # print("FLAG  :", e.flag)
    
        match e.event:

            case 1:   # EVENT_READY
                ev = e.event
                on_ready(ev)

            case 2:   # EVENT_START
                ev = e.event
                on_start(ev)

            case 3:   # EVENT_END
                ev = e.event
                on_end(ev)

            case 4:   # EVENT_PLAY
                ev = e.event
                on_play(ev)

            case 5:   # EVENT_PAUSE
                ev = e.event
                on_pause(ev)

            case 6:   # EVENT_POSITION
                ev = e.number
                on_pos(ev)

            case 7:   # EVENT_DURATION
                ev = e.event
                on_duration(ev)

            case 8:   # EVENT_VOLUME
                ev = e.event
                on_volume(ev)

            case 9:   # EVENT_SPEED
                ev = e.event
                on_speed(ev)

            case 10:  # EVENT_BUFFERING
                ev = bool(e.flag)
                on_buffering(ev)

            case 11:  # EVENT_ERROR
                ev = e.name.decode()
                on_error(ev)

            case 12:  # EVENT_LOG
                ev = e.name.decode()
                on_log(ev)



    def _mpvinit(self,*args):
        self.texture = Texture.create(
            size=(
                int(self.width),
                int(self.height)
            ),
            colorfmt="rgba"
        )
        print('check tex: ',self.texture.target)
        print(self.texture.colorfmt)
        print(self.texture.size)

        # self.texture.bind()

        # XXX Experiment
        # self.canvas.clear()
        # with self.canvas:
        #     # Callback(self.render_frame)             
        #     self.rect = Rectangle(
        #         texture=self.texture,
        #     )

        self.rect = Image(
            texture=self.texture
        ) ; self.add_widget(self.rect)

        self.rect.size = self.size
        self.rect.pos = self.x , self.y

        # debug
        print("init complete","texture id ", self.texture.id)

        @RENDER_CALLBACK
        def _render_ready():

            Clock.schedule_once(
                lambda dt: self.update(),
                0
            )
        # recreating texture according to window size   
        def _start_mpv():

            mpv.init_gl()
            mpv.set_texture(self.texture.id)

            print("player",mpv.create_player())

            print("render",mpv.create_render())

            self._render_cb = RENDER_CALLBACK(_render_ready)

            mpv.mpv_set_render_callback(
                self._render_cb
            )

            print("texture id",self.texture.id)

            mpv.set_texture(self.texture.id)

            # listeners
            if not self._listener:
                
                self._listener = CALLBACK(self.mpv_listener)

                mpv.mpv_set_callback(
                    self._listener
                )


            # update   XXX may move to mpv schedules 
            # if self._update: self._update.cancel()
            # self._update = Clock.schedule_interval(
            #     self.update,
            #     1/60    # 60 HZ
            # )
            print("MPV configured for screen size: ", self.parent.width , self.parent.height)

        Clock.schedule_once(lambda dt: _start_mpv() , 0.3)


    def update(self,*dt):

        mpv.process_events()

        mpv.render(
            int(self.width),
            int(self.height)
        )
        self.rect.pos=self.x , self.y,

        self.rect.size=self.width , self.height
        self.canvas.ask_update()

        # experiment
        # self._parent.canvas.after.clear()

        # with self._parent.canvas.after:
        #     ResetContext()

    def _mpvdestroy(self): mpv.destroy()

    # controlls
    def _set_mpvoptions(
        self, 
        options_key="user-agent" , 
        options_val="Mozilla/5.0"
        ) -> int:
        # set before player initialization
        return mpv.mpv_set_options(
            options_key.encode(),
            options_val.encode()
        )
    def init(self): Clock.schedule_once(lambda dt: self._mpvinit() , 0.1)   # segment falt without kivy thread
    def destroy(self): Clock.schedule_once(lambda dt: self._mpvdestroy() , 0.1)

    def load(self,url) -> int: return mpv.load(url.encode())
    def play(self) -> int: return mpv.play()
    def pause(self) -> int: return mpv.pause()
    def stop(self) -> int: return mpv.stop()
    def isplaying(self) -> int: return mpv.isplaying()
    def paused(self) -> int: return mpv.paused()
    def seek(self, sec:float) -> int: return mpv.seek(sec)
    def skip(sself, sec:float) -> int: return mpv.skip(sec)
    def pos(self) -> float: return mpv.pos()
    def duration(self) -> float: return mpv.duration()
    def volume(self) -> float: return mpv.volume_get()
    def volume_set(self, v:float) -> int: return mpv.volume(v)
    def speed(self) -> float: return mpv.speed_get()
    def speed_set(self, s:float) -> int: return mpv.speed(s)
    def mute(self) -> int: return mpv.mute_get()
    def mute_set(self, m:int) -> int: return mpv.mute(m)

    # events
    @on_ready
    def __ready(self, *args): print(args)
    @on_start
    def __start(self , *a):  print("stream starts!!" , a)
    @on_end
    def __end(self, *a): 
        self._playing = False
        print("stream ended!!!" , a)
    @on_play
    def __play(self,*a):
        self._playing = True
        print("playing" , a)
    @on_pause
    def __pause(self,*a):
        self._playing = False
        print("paused" , a)
    @on_pos
    def __pos(self, *a):
        if a: self._pos = a[0]
        print("pos...", a)
    @on_duration
    def __duration(self , *a):
        if a: self._duration = a[0]
        print("duration...", a)
    @on_volume
    def __vol(self, *a):
        if a: self._volume = a[0]
        print("vol..." , a)
    @on_speed
    def __speed(self, *a):
        if a: self._speed = a[0]
        print("speed ..." , a)
    @on_buffering
    def __buff(self, *a):
        if a: self._buffering = a[0]
        print("buff..." , a)
    @on_error
    def __err(self, *a):
        if a: self._err = a[0]
        self._playing=False
        print("err..." , a)
    @on_log
    def __logs(self, *a): 
        print('LOGS : ', a[0] if a else None)



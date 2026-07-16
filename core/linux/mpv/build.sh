#!/bin/bash


gcc -shared -fPIC \
src/mpv_bridge.c \
src/mpv_controller.c \
src/mpv_events.c \
-o libs/x86_64/libmpv_bridge.so \
-lmpv \
-lGL \
-lGLEW
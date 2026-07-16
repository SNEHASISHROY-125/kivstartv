#ifndef MPV_CONTROLLER_H
#define MPV_CONTROLLER_H
#include <stdio.h>

#ifdef __cplusplus
extern "C" {
#endif

int mpv_load(const char *url);

int mpv_play(void);

int mpv_pause(void);

int mpv_stop(void);

int mpv_seek(double seconds);

int mpv_seek_relative(double seconds);

int mpv_set_volume(double volume);

double mpv_get_volume(void);

int mpv_set_speed(double speed);

double mpv_get_speed(void);

int mpv_set_mute(int mute);

int mpv_get_mute(void);

double mpv_get_position(void);

double mpv_get_duration(void);

int mpv_is_paused(void);

int mpv_is_playing(void);

#ifdef __cplusplus
}
#endif

#endif
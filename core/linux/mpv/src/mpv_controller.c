#include <string.h>

#include <mpv/client.h>

#include "mpv_core.h"
#include "mpv_controller.h"

int mpv_load(const char *url)
{
    const char *cmd[] =
    {
        "loadfile",
        url,
        NULL
    };

    return mpv_command(g_mpv, cmd);
}

int mpv_play(void)
{
    int pause = 0;

    return mpv_set_property(
        g_mpv,
        "pause",
        MPV_FORMAT_FLAG,
        &pause
    );
}

int mpv_pause(void)
{
    int pause = 1;

    return mpv_set_property(
        g_mpv,
        "pause",
        MPV_FORMAT_FLAG,
        &pause
    );
}

int mpv_stop(void)
{
    const char *cmd[] =
    {
        "stop",
        NULL
    };

    return mpv_command(g_mpv, cmd);
}

int mpv_seek(double seconds)
{
    return mpv_set_property(
        g_mpv,
        "time-pos",
        MPV_FORMAT_DOUBLE,
        &seconds
    );
}

int mpv_seek_relative(double seconds)
{
    char offset[64];

    snprintf(offset,sizeof(offset),"%.3f",seconds);

    const char *cmd[] =
    {
        "seek",
        offset,
        "relative",
        NULL
    };

    return mpv_command(g_mpv,cmd);
}

int mpv_set_volume(double volume)
{
    return mpv_set_property(
        g_mpv,
        "volume",
        MPV_FORMAT_DOUBLE,
        &volume
    );
}

double mpv_get_volume(void)
{
    double value=0;

    mpv_get_property(
        g_mpv,
        "volume",
        MPV_FORMAT_DOUBLE,
        &value
    );

    return value;
}

int mpv_set_speed(double speed)
{
    return mpv_set_property(
        g_mpv,
        "speed",
        MPV_FORMAT_DOUBLE,
        &speed
    );
}

double mpv_get_speed(void)
{
    double value=1.0;

    mpv_get_property(
        g_mpv,
        "speed",
        MPV_FORMAT_DOUBLE,
        &value
    );

    return value;
}

int mpv_set_mute(int mute)
{
    return mpv_set_property(
        g_mpv,
        "mute",
        MPV_FORMAT_FLAG,
        &mute
    );
}

int mpv_get_mute(void)
{
    int mute=0;

    mpv_get_property(
        g_mpv,
        "mute",
        MPV_FORMAT_FLAG,
        &mute
    );

    return mute;
}

double mpv_get_position(void)
{
    double value=0;

    mpv_get_property(
        g_mpv,
        "time-pos",
        MPV_FORMAT_DOUBLE,
        &value
    );

    return value;
}

double mpv_get_duration(void)
{
    double value=0;

    mpv_get_property(
        g_mpv,
        "duration",
        MPV_FORMAT_DOUBLE,
        &value
    );

    return value;
}

int mpv_is_paused(void)
{
    int pause=0;

    mpv_get_property(
        g_mpv,
        "pause",
        MPV_FORMAT_FLAG,
        &pause
    );

    return pause;
}

int mpv_is_playing(void)
{
    if (!g_mpv)
        return 0;

    int idle = 1;
    int pause = 1;

    mpv_get_property(
        g_mpv,
        "core-idle",
        MPV_FORMAT_FLAG,
        &idle
    );

    mpv_get_property(
        g_mpv,
        "pause",
        MPV_FORMAT_FLAG,
        &pause
    );

    return (!idle && !pause);
}
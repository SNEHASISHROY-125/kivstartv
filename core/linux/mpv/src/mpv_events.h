#ifndef MPV_EVENTS_H
#define MPV_EVENTS_H

#ifdef __cplusplus
extern "C" {
#endif

/* ---------- Generic Events ---------- */

typedef enum
{
    EVENT_NONE = 0,

    EVENT_READY,
    EVENT_START,
    EVENT_END,

    EVENT_PLAY,
    EVENT_PAUSE,

    EVENT_POSITION,
    EVENT_DURATION,

    EVENT_VOLUME,
    EVENT_SPEED,

    EVENT_BUFFERING,

    EVENT_ERROR,

    EVENT_LOG

} MPV_EVENT;


/* ---------- Event Packet ---------- */

typedef struct
{
    int event;

    char name[64];

    double number;

    int flag;

} MPVEvent;


/* ---------- Callback ---------- */

typedef void (*mpv_callback)(
    MPVEvent *event
);


/* ---------- API ---------- */

void mpv_set_callback(
    mpv_callback cb
);

void mpv_events_init(void);

void mpv_events_process(void);

#ifdef __cplusplus
}
#endif

#endif
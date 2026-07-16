#include <stdio.h>
#include <string.h>

#include <mpv/client.h>

#include "mpv_core.h"
#include "mpv_events.h"

static mpv_callback g_callback = NULL;

void mpv_set_callback(
    mpv_callback cb
)
{
    g_callback = cb;
}


static void dispatch(
    MPVEvent *e
)
{
    if(g_callback)
        g_callback(e);
}


void mpv_events_init()
{

    mpv_observe_property(
        g_mpv,
        1,
        "time-pos",
        MPV_FORMAT_DOUBLE
    );

    mpv_observe_property(
        g_mpv,
        2,
        "duration",
        MPV_FORMAT_DOUBLE
    );

    mpv_observe_property(
        g_mpv,
        3,
        "pause",
        MPV_FORMAT_FLAG
    );

    mpv_observe_property(
        g_mpv,
        4,
        "volume",
        MPV_FORMAT_DOUBLE
    );

    mpv_observe_property(
        g_mpv,
        5,
        "speed",
        MPV_FORMAT_DOUBLE
    );

    mpv_observe_property(
        g_mpv,
        6,
        "paused-for-cache",
        MPV_FORMAT_FLAG
    );

}

void mpv_events_process()
{

    MPVEvent evt;

    while(1)
    {

        mpv_event *event =
            mpv_wait_event(
                g_mpv,
                0
            );

        if(event->event_id == MPV_EVENT_NONE)
            break;


        memset(
            &evt,
            0,
            sizeof(evt)
        );

        // debug
        // mpv_event *event = mpv_wait_event(g_mpv, 0);

        // printf("EVENT = %d\n", event->event_id);
        // fflush(stdout);

        switch(event->event_id)
        {

        case MPV_EVENT_START_FILE:

            evt.event = EVENT_START;

            dispatch(&evt);

            break;



        case MPV_EVENT_FILE_LOADED:

            evt.event = EVENT_READY;

            dispatch(&evt);

            break;



        case MPV_EVENT_END_FILE:

            mpv_event_end_file *end = event->data;

            // printf("reason = %d\n", end->reason);
            // printf("error  = %d\n", end->error);

            // evt.event = EVENT_END;
            if (end->reason == MPV_END_FILE_REASON_ERROR)
            {
                evt.event = EVENT_ERROR;
                evt.number = end->error;          // -13
                evt.flag   = end->reason;    // MPV_END_FILE_REASON_ERROR (4)
                strncpy(evt.name,
                        mpv_error_string(end->error),
                        sizeof(evt.name)-1);
            }
            else
            {
                evt.event = EVENT_END;
                evt.flag = end->reason;
            }


            dispatch(&evt);

            break;



        case MPV_EVENT_LOG_MESSAGE:
        {

            mpv_event_log_message *msg =
                event->data;

            evt.event = EVENT_LOG;

            strncpy(
                evt.name,
                msg->text,
                63
            );

            dispatch(&evt);

            break;
        }



        case MPV_EVENT_PROPERTY_CHANGE:
        {

            mpv_event_property *prop =
                event->data;

            if(!prop->data)
                break;


            strcpy(
                evt.name,
                prop->name
            );


            if(
                strcmp(
                    prop->name,
                    "time-pos"
                ) == 0
            )
            {

                evt.event = EVENT_POSITION;

                evt.number =
                    *(double *)prop->data;

            }


            else if(
                strcmp(
                    prop->name,
                    "duration"
                ) == 0
            )
            {

                evt.event = EVENT_DURATION;

                evt.number =
                    *(double *)prop->data;

            }


            else if(
                strcmp(
                    prop->name,
                    "volume"
                ) == 0
            )
            {

                evt.event = EVENT_VOLUME;

                evt.number =
                    *(double *)prop->data;

            }


            else if(
                strcmp(
                    prop->name,
                    "speed"
                ) == 0
            )
            {

                evt.event = EVENT_SPEED;

                evt.number =
                    *(double *)prop->data;

            }


            else if(
                strcmp(
                    prop->name,
                    "pause"
                ) == 0
            )
            {

                evt.event =
                    *(int *)prop->data ?
                    EVENT_PAUSE :
                    EVENT_PLAY;

                evt.flag =
                    *(int *)prop->data;

            }


            else if(
                strcmp(
                    prop->name,
                    "paused-for-cache"
                ) == 0
            )
            {

                evt.event =
                    EVENT_BUFFERING;

                evt.flag =
                    *(int *)prop->data;

            }


            dispatch(
                &evt
            );

            break;
        }


        default:

            break;

        }

    }

}
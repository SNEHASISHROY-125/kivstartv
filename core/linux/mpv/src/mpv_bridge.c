#include <stdio.h>

#include <mpv/client.h>
#include <mpv/render_gl.h>

#include <GL/glew.h>
#include <GL/glx.h>

#include "mpv_controller.h"

#include "mpv_core.h"
#include "mpv_events.h"

#include <time.h>

mpv_handle *g_mpv = NULL;
mpv_render_context *g_mpv_gl = NULL;


static mpv_handle *mpv = NULL;
static mpv_render_context *mpv_gl = NULL;


static GLuint video_texture = 0;
static GLuint video_fbo = 0;

static void (*python_render_cb)(void)=NULL;


static void *get_proc(
    void *ctx,
    const char *name
)
{
    return glXGetProcAddress(
        (const GLubyte *)name
    );
}

int init_gl()
{
    GLenum err = glewInit();

    if(err != GLEW_OK)
    {
        printf(
            "GLEW failed: %s\n",
            glewGetErrorString(err)
        );
        return -1;
    }


    printf(
        "GLEW initialized\n"
    );

    printf("from gl_init: %s\n",glGetString(GL_VERSION));

    return 0;
}


int create_player()
{
    g_mpv = mpv_create();

    if(!g_mpv)
        return -1;


    mpv_set_option_string(
        g_mpv,
        "vo",
        "libmpv"
    );


    mpv_set_option_string(
        g_mpv,
        "hwdec",
        "auto"
    );


    mpv_set_option_string(
        g_mpv,
        "gpu-api",
        "opengl"
    );


    mpv_initialize(g_mpv);

    mpv_events_init();

    return 0;
}

void mpv_set_render_callback(
    void (*cb)(void)
)
{
    python_render_cb = cb;
}

static void render_update(
    void *ctx
)
{
    if (python_render_cb)
        python_render_cb();
}

int create_render()
{

    mpv_opengl_init_params gl_init =
    {
        .get_proc_address = get_proc,
        .get_proc_address_ctx = NULL
    };


    mpv_render_param params[] =
    {

        {
            MPV_RENDER_PARAM_API_TYPE,
            MPV_RENDER_API_TYPE_OPENGL
        },

        {
            MPV_RENDER_PARAM_OPENGL_INIT_PARAMS,
            &gl_init
        },

        {
            0
        }
    };


    int res = mpv_render_context_create(
        &g_mpv_gl,
        g_mpv,
        params
    );

    mpv_render_context_set_update_callback(
        g_mpv_gl,
        render_update,
        NULL
    );

    return res;

}





void set_texture(
    unsigned int tex
)
{
    //  deleting old fbo
    if (video_fbo) {
        glDeleteFramebuffers(1, &video_fbo);
        video_fbo = 0;
    }

    video_texture = tex;


    glGenFramebuffers(
        1,
        &video_fbo
    );


    glBindFramebuffer(
        GL_FRAMEBUFFER,
        video_fbo
    );


    glFramebufferTexture2D(
        GL_FRAMEBUFFER,
        GL_COLOR_ATTACHMENT0,
        GL_TEXTURE_2D,
        video_texture,
        0
    );


    GLenum status =
        glCheckFramebufferStatus(
            GL_FRAMEBUFFER
        );


    printf(
        "FBO status %x\n",
        status
    );


    glBindFramebuffer(
        GL_FRAMEBUFFER,
        0
    );
}




/* ------player controlls------- */

int mpv_set_options(const char *name, const char *value)
{
    if (!g_mpv)
        return -1;

    return mpv_set_option_string(
        g_mpv,
        name,
        value
    );
}
// load & play
int load(char *url) {
    int res = mpv_load(url);
    printf("load returned\n");
    fflush(stdout);

    for (int i = 0; i < 100; i++) {
        mpv_events_process();
        // usleep(10000);
        struct timespec ts;
        ts.tv_sec = 0;
        ts.tv_nsec = 10000000; // 10 milliseconds (10,000 microseconds)
        nanosleep(&ts, NULL);
    }
    return res;
}
int play(void) {
    return mpv_play();
}
int pause(void) {
    return mpv_pause();
}
int stop(void) {
    return mpv_stop();
}
int paused(void) {
    return mpv_is_paused();
}
int isplaying(void) {
    return mpv_is_playing();
}
// Absolute seek
int seek(double s) {
    return mpv_seek(s);
}
// ± offset from current position
int skip(double s) {
    return mpv_seek_relative(s);
}
double pos(void) {
    return mpv_get_position();
}
double duration(void) {
    return mpv_get_duration();
}
int volume(double v) {
    return mpv_set_volume(v);
}
double volume_get(void) {
    return mpv_get_volume();
}
int speed(double s) {
    return mpv_set_speed(s);
}
double speed_get(void) {
    return mpv_get_speed();
}
int mute(int m) {
    return mpv_set_mute(m);
}
int mute_get(void) {
    return mpv_get_mute();
}


void render(
    int width,
    int height
)
{

    if(!g_mpv_gl)
        return;


    uint64_t flags =
        mpv_render_context_update(
            g_mpv_gl
        );


    if(!(flags & MPV_RENDER_UPDATE_FRAME))
        return;



    mpv_opengl_fbo target =
    {
        .fbo = video_fbo,
        .w = width,
        .h = height,
        .internal_format = GL_RGBA8
    };


    int flip = 1;


    mpv_render_param params[] =
    {

        {
            MPV_RENDER_PARAM_OPENGL_FBO,
            &target
        },

        {
            MPV_RENDER_PARAM_FLIP_Y,
            &flip
        },

        {
            0
        }

    };

    mpv_render_context_render(
        g_mpv_gl,
        params
    );

    // kivy black box fix
    glEnable(GL_BLEND);

    glBlendFunc(
        GL_SRC_ALPHA,
        GL_ONE_MINUS_SRC_ALPHA
    );

    glBlendEquation(GL_FUNC_ADD);

}



void process_events()
{
    mpv_events_process();
}



void destroy()
{

    if(g_mpv_gl)
        mpv_render_context_free(
            g_mpv_gl
        );


    if(video_fbo)
        glDeleteFramebuffers(
            1,
            &video_fbo
        );


    if(g_mpv)
        mpv_terminate_destroy(
            g_mpv
        );
}
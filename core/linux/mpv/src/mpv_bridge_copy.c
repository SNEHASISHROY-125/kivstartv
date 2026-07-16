#include <stdio.h>

#include <mpv/client.h>
#include <mpv/render_gl.h>

#include <GL/glew.h>
#include <GL/glx.h>

#include "mpv_core.h"

mpv_handle *g_mpv = NULL;
mpv_render_context *g_mpv_gl = NULL;


static mpv_handle *mpv = NULL;
static mpv_render_context *mpv_gl = NULL;


static GLuint video_texture = 0;
static GLuint video_fbo = 0;



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
    mpv = mpv_create();

    if(!mpv)
        return -1;


    mpv_set_option_string(
        mpv,
        "vo",
        "libmpv"
    );


    mpv_set_option_string(
        mpv,
        "hwdec",
        "auto"
    );


    mpv_set_option_string(
        mpv,
        "gpu-api",
        "opengl"
    );


    return mpv_initialize(mpv);
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


    return mpv_render_context_create(
        &mpv_gl,
        mpv,
        params
    );
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




int load(
    char *url
)
{

    const char *cmd[] =
    {
        "loadfile",
        url,
        NULL
    };


    return mpv_command(
        mpv,
        cmd
    );
}



void render(
    int width,
    int height
)
{

    if(!mpv_gl)
        return;


    uint64_t flags =
        mpv_render_context_update(
            mpv_gl
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

    // debug
    GLint vp[4];

    glGetIntegerv(GL_VIEWPORT,vp);

    // printf("from render: %d %d %d %d\n",
    // vp[0],vp[1],vp[2],vp[3]);

    // debug
    glBindTexture(GL_TEXTURE_2D, video_texture);

    GLint w,h;

    glGetTexLevelParameteriv(
        GL_TEXTURE_2D,
        0,
        GL_TEXTURE_WIDTH,
        &w
    );

    glGetTexLevelParameteriv(
        GL_TEXTURE_2D,
        0,
        GL_TEXTURE_HEIGHT,
        &h
    );

    // printf("actual texture = %d x %d\n",w,h);

    // debug
    GLint current_program;

    glGetIntegerv(
        GL_CURRENT_PROGRAM,
        &current_program
    );

    // printf(
    //     "shader=%d\n",
    //     current_program
    // );

    // original

    mpv_render_context_render(
        mpv_gl,
        params
    );

    // glFlush();

}



void process_events()
{
    while(1)
    {

        mpv_event *event =
            mpv_wait_event(
                mpv,
                0
            );


        if(event->event_id ==
           MPV_EVENT_NONE)
            break;
    }
}



void destroy()
{

    if(mpv_gl)
        mpv_render_context_free(
            mpv_gl
        );


    if(video_fbo)
        glDeleteFramebuffers(
            1,
            &video_fbo
        );


    if(mpv)
        mpv_terminate_destroy(
            mpv
        );
}
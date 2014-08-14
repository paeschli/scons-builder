import os
from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.btools import runCommand
from builder.bconfig import getAutoconfPrefix

def CheckSDL(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for SDL... ')
    confprefix = getAutoconfPrefix(ctx.env)
    platform = ctx.env['PLATFORM']
    
    if platform == 'win32':
        savedVars = ctx.env.SaveVars('LIBS')

        if ctx.env.IsMSVC_Debug() :
            sdllibs = ['SDLd', 'SDLmaind']
        else:
            sdllibs = ['SDL', 'SDLmain']

        ctx.env.Append(LIBS = sdllibs)
        ret = ctx.TryLink("""
            #include <SDL.h>
            int main(int argc, char **argv)
            {
                SDL_Init(SDL_INIT_VIDEO);
                SDL_Quit();
                return 0;
            }
            """, extension='.c')

        ctx.env.RestoreVars(savedVars)

        if ret:
            ctx.env.DeclarePackage('sdl',
                                   trigger_libs=['SDL', 'SDLmain'],
                                   trigger_frameworks=['SDL'],
                                   LIBS = sdllibs)
            ctx.env.Replace(LIBSDL = sdllibs)
    else:
        ret, output = ctx.TryAction('sdl-config --version')
        if ret:
            
            vars = ctx.env.ParseFlags('!sdl-config --cflags --libs')

            ctx.env.DeclarePackage('sdl', vars=vars,
                                   trigger_libs=['SDL', 'SDLmain'],
                                   trigger_frameworks=['SDL'])

            if add_to_compiler_env:
                ctx.env.Append(CPPPATH = vars.get('CPPPATH'))
                ctx.env.Append(LIBPATH = vars.get('LIBPATH'))
            ctx.env.Replace(LIBSDL = vars.get('LIBS'))
        
    key = confprefix+'HAVE_LIBSDL'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckSDL', CheckSDL)

def CheckSDLTTF(ctx, write_config_h=False, add_to_compiler_env=False):
    # We assume here that SDL is available
    ctx.Message('Checking for SDL_ttf... ')
    confprefix = getAutoconfPrefix(ctx.env)

    platform = ctx.env['PLATFORM']

    savedLIBS = ctx.env.SaveVars('LIBS')

    sdllibs = ctx.env.get('LIBSDL', [])
    sdlttflibs = ['SDL_ttf']

    savedVars = None
    if ctx.env.GetPackage('sdl'):
        savedVars = ctx.env.RequirePackage('sdl')
    
    ctx.env.Append(LIBS = sdlttflibs + sdllibs)
    ret = ctx.TryLink("""
        #include <SDL_ttf.h>
        int main(int argc, char **argv) {
            TTF_Init();
            TTF_Quit();
            return 0;
        }
        """, extension='.c')

    ctx.env.RestoreVars(savedLIBS)

    if savedVars:
        ctx.env.RestoreVars(savedVars)

    if ret:
        ctx.env.DeclarePackage('sdlttf', vars={'LIBS' : sdlttflibs},
                               dependencies='sdl',
                               trigger_libs=['SDL_ttf'])
        ctx.env.Replace(LIBSDLTTF=sdlttflibs)

    key = confprefix+'HAVE_LIBSDL_TTF'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckSDLTTF', CheckSDLTTF)

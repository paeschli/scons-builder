import os
from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix

def CheckRTSG(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for RTSG library... ')
    confprefix = getAutoconfPrefix(ctx.env)

    platform = ctx.env['PLATFORM']

    RTSG_DIST_DIR = ctx.env.GetEnvVar('RTSG_DIST_DIR')
    
    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS LIBPATH CPPPATH')

    libDir = ''
    incDir = ''

    if RTSG_DIST_DIR:
        if platform == 'win32':
            rtsgLibFile = 'rtsg.dll'
        else:
            rtsgLibFile = 'librtsg.so'

        libDir = os.path.join(RTSG_DIST_DIR, 'lib')
        rtsgLib = os.path.join(libDir, rtsgLibFile)
        if not os.path.exists(rtsgLib):
            libDir = os.path.join(RTSG_DIST_DIR, 'build', 'lib')
            rtsgLib = os.path.join(libDir, rtsgLibFile)
            if not os.path.exists(rtsgLib):
                ctx.Message('Warning: could not find RTSG library %s. '\
                            % (rtsgLib,))
                ctx.Result(0)
                return 0
        
        incDir = os.path.join(RTSG_DIST_DIR, 'include')
        if not os.path.exists(incDir):
            incDir = os.path.join(RTSG_DIST_DIR, '..', 'include')
            if not os.path.exists(incDir):
                ctx.Message('Warning: could not find RTSG include dir %s. '\
                            % (incDir,))
                ctx.Result(0)
                return 0

        ctx.env.Append(LIBPATH=os.path.abspath(libDir))
        ctx.env.Append(CPPPATH=os.path.abspath(incDir))
    
    ctx.env.Append(LIBS = ['rtsg'])
    
    ret = ctx.TryLink("""
    #include "rtsg/base/Config.hpp"
    #include "rtsg/base/Vec3.hpp"
    using namespace rtsg;

    int main(int argc, char **argv)
    {
      Vec3f v(1,2,3);
      return 0;
    }
""", extension='.cpp')

    if ret:
        ctx.env.DeclarePackage('rtsg',
                               LIBS=['rtsg'],
                               LIBPATH=[os.path.abspath(libDir)],
                               CPPPATH=[os.path.abspath(incDir)],
                               dependencies=[],
                               trigger_libs=['RTSG', 'rtsg'],
                               trigger_frameworks=['RTSG'])

    ctx.env.RestoreVars(savedVars)

    if add_to_compiler_env:
        ctx.env.Append(LIBPATH=os.path.abspath(libDir))
        ctx.env.Append(CPPPATH=os.path.abspath(incDir))

    key = confprefix+'HAVE_RTSG'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckRTSG', CheckRTSG)

def CheckRTSG_OpenRT(ctx, write_config_h=False, add_to_compiler_env=False):
    # We assume here that RTSG is available
    ctx.Message('Checking for RTSG/OpenRT library... ')
    confprefix = getAutoconfPrefix(ctx.env)
    
    platform = ctx.env['PLATFORM']

    OPENRT_INCLUDE_DIR = ctx.env.get('OPENRT_INCLUDE_DIR', '')

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS LIBPATH CPPPATH')

    if ctx.env.GetPackage('rtsg'):
        ctx.env.RequirePackage('rtsg')

    rtsgopenrtlibs = ['rtsgortext']

    ctx.env.Append(LIBS = rtsgopenrtlibs)
    ctx.env.Append(CPPPATH = OPENRT_INCLUDE_DIR)
    ret = ctx.TryLink("""
        #include <openrt/rt.h>
        #include <openrt/types.h>
        #include <rtsg/ortext/OpenRTRenderer.hpp>
        int main(int argc, char **argv) {
            ortext::OpenRTRenderer *r = 0;
            return 0;
        }
""", extension='.cpp')

    ctx.env.RestoreVars(savedVars)

    if ret:
        ctx.env.DeclarePackage('rtsg_openrt',
                               LIBS=[rtsgopenrtlibs],
                               CPPPATH=[OPENRT_INCLUDE_DIR],
                               dependencies=['rtsg'],
                               trigger_libs=['RTSG_OpenRT', 'rtsg_openrt',
                                             'rtsgort', 'rtsgortext'],
                               trigger_frameworks=['RTSG_OpenRT'])
        ctx.env.Replace(LIBRTSGOPENRT=rtsgopenrtlibs)
        
    key = confprefix+'HAVE_LIBRTSG_OPENRT'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])
        
    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckRTSG_OpenRT', CheckRTSG_OpenRT)

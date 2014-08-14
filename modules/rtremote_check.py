from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
import os.path

def CheckRTfactRemote(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for RTfactRemote header files... ')
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_RTFACT_REMOTE'

    compiler = ctx.env['compiler']
    platform = ctx.env['PLATFORM']
    isWin32 = (platform == 'win32')

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS CCFLAGS')

    rtremoteLIBS = ['RTfactRemote']
    if compiler == 'GCC' or (compiler == 'INTEL' and not isWin32):
        rtremoteCCFLAGS = ['-mmmx', '-msse', '-msse2']
    elif compiler == 'MSVC':
        rtremoteCCFLAGS = ['/arch:SSE2']
    else:
        rtremoteCCFLAGS = []

    ctx.env.Append(LIBS = rtremoteLIBS)
    ctx.env.Append(CCFLAGS = rtremoteCCFLAGS)

    ret = ctx.TryLink("""
#include "RTremote/Renderer.hpp"

using namespace RTfact::Remote;
    
int main(int argc, char **argv) {
  Renderer r;
  return 0;
}
""", extension='.cpp')

    if ret:
        ctx.env.DeclarePackage('rtremote', LIBS=rtremoteLIBS,
                               dependencies=[],
                               vars={'CPPDEFINES' : [key],
                                     'CCFLAGS' : rtremoteCCFLAGS},
                               trigger_libs=['RTfactRemote'],
                               trigger_frameworks=['RTfactRemote'])

    ctx.env.RestoreVars(savedVars)

    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])
    
    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckRTfactRemote', CheckRTfactRemote)

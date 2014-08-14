from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
import os.path

def CheckRTfactRTpie(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for delicious RTfact Pie header files... ')
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_RTFACT_REMOTE'

    compiler = ctx.env['compiler']
    platform = ctx.env['PLATFORM']
    isWin32 = (platform == 'win32')

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS CCFLAGS')

    rtpieLIBS = ['RTfactRTpie']
    if compiler == 'GCC' or (compiler == 'INTEL' and not isWin32):
        rtpieCCFLAGS = ['-mmmx', '-msse', '-msse2']
    elif compiler == 'MSVC':
        rtpieCCFLAGS = ['/arch:SSE2']
    else:
        rtpieCCFLAGS = []

    ctx.env.Append(LIBS = rtpieLIBS)
    ctx.env.Append(CCFLAGS = rtpieCCFLAGS)

    ret = ctx.TryLink("""
#include "RTpie/IRayTracer.hpp"

using namespace RTfact::RTpie;
    
int main(int argc, char **argv) {
  IRayTracer *r;
  HRESULT rv = CreateRayTracer(&r);
  if(SUCCEEDED(rv)){
  	r->Release();
  }
  return 0;
}
""", extension='.cpp')

    if ret:
        ctx.env.DeclarePackage('rtpie', LIBS=rtpieLIBS,
                               dependencies=[],
                               vars={'CPPDEFINES' : [key],
                                     'CCFLAGS' : rtpieCCFLAGS},
                               trigger_libs=['RTfactRTpie'],
                               trigger_frameworks=['RTfactRTpie'])

    ctx.env.RestoreVars(savedVars)

    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])
    
    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckRTfactRTpie', CheckRTfactRTpie)

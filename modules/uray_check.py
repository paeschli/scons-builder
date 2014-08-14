from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
import os.path

def CheckURayUtils(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for URayUtils header files... ')
    confprefix = getAutoconfPrefix(ctx.env)
    
    platform = ctx.env['PLATFORM']

    ret = ctx.TryLink("""
    #include "URayUtils/Config/URayConfig.hpp"

    using namespace URay;
    
    int main(int argc, char **argv) {
      uint32 i = 0;
      return 0;
    }
""", extension='.cpp')

    key = confprefix+'HAVE_URAY_UTILS'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])
    
    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckURayUtils', CheckURayUtils)

def CheckRTfact(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for RTfact library... ')
    confprefix = getAutoconfPrefix(ctx.env)
    
    platform = ctx.env['PLATFORM']
    compiler = ctx.env['compiler']
    isGCC = (compiler == 'GCC')

    lastCCFLAGS = list(ctx.env.get('CCFLAGS', []))

    if isGCC:
        ctx.env.AppendUnique(CCFLAGS = ['-fpermissive'])

    ret = ctx.TryLink("""
    #include "URayUtils/Config/URayConfig.hpp"
    #include "RTfact/Config/Config.hpp"
    #include "RTfact/Concept/Scene.hpp"

    using namespace URay::RTfact;
    using namespace URay;
    
    int main(int argc, char **argv) {
      uint32 i = 0;
      return 0;
    }
""", extension='.cpp')

    key = confprefix+'HAVE_RTFACT'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.env.Replace(CCFLAGS = lastCCFLAGS)
    
    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckRTfact', CheckRTfact)

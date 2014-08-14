from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
import os.path

def CheckJitRT(ctx, write_config_h=False, add_to_cppdefines=False):
    ctx.Message('Checking for jitRT library... ')
    confprefix = getAutoconfPrefix(ctx.env)

    platform = ctx.env['PLATFORM']

    haveLLVM = ctx.env.GetPackage('llvm')

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS')

    jitrtlibs = ['jitRT']

    ctx.env.Append(LIBS = jitrtlibs)

    ret = ctx.TryLink("""
#include <jitRT/llvmWrapper.h>

int main(int argc, char **argv)
{
    llvm::Module* mod = jitRT::createModuleFromFile("file");
    return 0;
}
""", extension='.cpp')

    ctx.env.RestoreVars(savedVars)

    if ret:
        ctx.env.DeclarePackage('jitrt',
                               vars={'LIBS' : jitrtlibs,
                                     'CPPDEFINES' : confprefix+'HAVE_ANYSL'},
                               trigger_libs=['jitrt', 'jitRT'],
                               trigger_frameworks=['jitRT'])

    key = confprefix+'HAVE_ANYSL'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_cppdefines:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckJitRT', CheckJitRT)

from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
import os.path

def CheckAnySL2(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for AnySL2 library... ')
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_ANYSL2'

    compiler = ctx.env['compiler']
    platform = ctx.env['PLATFORM']
    isWin32 = (platform == 'win32')

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS CCFLAGS')

    anysl2LIBS = ['AnySL']
    anysl2CCFLAGS = []

    ctx.env.Append(LIBS = anysl2LIBS)
    ctx.env.Append(CCFLAGS = anysl2CCFLAGS)

    ret = ctx.TryLink("""
#include <AnySL/AnySL.hpp>
#include <AnySL/ParameterInfo.hpp>
#include <AnySL/Module.hpp>

using namespace AnySL;
    
int main(int argc, char **argv) {
  AnySL::Module::Ptr module;
  return 0;
}
""", extension='.cpp')

    if ret:
        ctx.env.DeclarePackage('anysl2', LIBS=anysl2LIBS,
                               dependencies=[],
                               vars={'CPPDEFINES' : [key],
                                     'CCFLAGS' : anysl2CCFLAGS},
                               trigger_libs=['AnySL'],
                               trigger_frameworks=['AnySL'])

    ctx.env.RestoreVars(savedVars)

    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])
    
    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckAnySL2', CheckAnySL2)

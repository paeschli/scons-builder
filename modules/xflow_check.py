from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
import os.path

def CheckXflow(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for Xflow library... ')
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_XFLOW'

    compiler = ctx.env['compiler']
    platform = ctx.env['PLATFORM']
    isWin32 = (platform == 'win32')

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS CCFLAGS')

    xflowLIBS = ['DFC','Xflow']
    xflowCCFLAGS = []

    ctx.env.Append(LIBS = xflowLIBS)
    ctx.env.Append(CCFLAGS = xflowCCFLAGS)

    ret = ctx.TryLink("""
#include <Xflow/Graph/Graph.hpp>

int main(int argc, char **argv) {
  Xflow::Graph::Ptr graph = new Xflow::Graph();
  return 0;
}
""", extension='.cpp')

    if ret:
        ctx.env.DeclarePackage('xflow', LIBS=xflowLIBS,
                               dependencies=['dfccdd'],
                               vars={'CPPDEFINES' : [key],
                                     'CCFLAGS' : xflowCCFLAGS},
                               trigger_libs=['Xflow'],
                               trigger_frameworks=['Xflow'])

    ctx.env.RestoreVars(savedVars)

    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckXflow', CheckXflow)

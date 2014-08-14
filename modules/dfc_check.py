from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
import os.path

def CheckDFC(ctx, write_config_h=False, add_to_compiler_env=False, enable_package_cppdefines=False):
    ctx.Message('Checking for DFC library... ')
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_DFC'

    compiler = ctx.env['compiler']
    platform = ctx.env['PLATFORM']
    isWin32 = (platform == 'win32')

    haveBoostThread = ctx.env.GetPackage('boost_thread')
    if not haveBoostThread:
        ctx.Message('Warning ! Please check for boost_thread first !')
        savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS CCFLAGS')
    else:
        savedVars = ctx.env.RequirePackage('boost_thread')

    dfcLIBS = ['DFC']
    dfcCCFLAGS = []

    ctx.env.Append(LIBS = dfcLIBS)
    ctx.env.Append(CCFLAGS = dfcCCFLAGS)

    ret = ctx.TryLink("""
#include <DFC/Base/Core/LibraryInit.hpp>

int main(int argc, char **argv) {
  DFC::LibraryInit init;
  return 0;
}
""", extension='.cpp')

    if ret:

        deps = ''
        if haveBoostThread:
            deps += 'boost_thread'

        vars = {'CCFLAGS' : dfcCCFLAGS}
        if enable_package_cppdefines:
            vars.update({'CPPDEFINES' : [key]})

        ctx.env.DeclarePackage('dfc', LIBS=dfcLIBS,
                               dependencies=deps,
                               vars=vars,
                               trigger_libs=['DFC'],
                               trigger_frameworks=['DFC'])
        ctx.env.DeclarePackage('dfccdd', LIBS=['DFCCDD'],
                               dependencies=['dfc'],
                               vars=vars,
                               trigger_libs=['DFCCDD'],
                               trigger_frameworks=['DFCCDD'])

    ctx.env.RestoreVars(savedVars)

    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckDFC', CheckDFC)

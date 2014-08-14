from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
import os.path

def CheckLibFI(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for libFI library ... ')
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_LIBFI'

    platform = ctx.env['PLATFORM']

    savedVars = ctx.env.SaveVars('LIBS')

    if platform == 'win32' and ctx.env.IsMSVC_Debug():
        libFILibs = ['fid']
    else:
        libFILibs = ['fi']

    ctx.env.Append(LIBS = libFILibs)

    ret = ctx.TryLink("""
#include <fi/Encoder.h>

int main(int argc, char **argv) {
  FI::Encoder enc;

  return 0;
}
""", extension='.cpp')

    if ret:
        ctx.env.DeclarePackage('libfi', LIBS=libFILibs,
                               trigger_libs=['fi'])

    ctx.env.RestoreVars(savedVars)

    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckLibFI', CheckLibFI)

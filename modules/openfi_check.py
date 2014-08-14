from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
import os.path

def CheckOpenFI(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for openFI library ... ')
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_OPENFI'

    platform = ctx.env['PLATFORM']

    savedVars = ctx.env.SaveVars('LIBS')

    if platform == 'win32' and ctx.env.IsMSVC_Debug():
        openFILibs = ['openFId']
    else:
        openFILibs = ['openFI']

    ctx.env.Append(LIBS = openFILibs)

    ret = ctx.TryLink("""
#include <xiot/FIEncoder.h>

int main(int argc, char **argv) {
  FI::FIEncoder enc;
  enc.reset();

  return 0;
}
""", extension='.cpp')

    if ret:
        ctx.env.DeclarePackage('openfi', LIBS=openFILibs,
                               trigger_libs=['openFI'])

    ctx.env.RestoreVars(savedVars)

    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckOpenFI', CheckOpenFI)

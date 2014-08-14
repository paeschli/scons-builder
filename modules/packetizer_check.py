from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix

def CheckPacketizer(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for Packetizer... ')
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_PACKETIZER'

    platform = ctx.env['PLATFORM']

    # If LLVM is not available Packetizer cannot be used as it linked statically
    # and do not contain any LLVM symbols
    if not ctx.env.GetPackage('llvm'):
        ctx.Message('No LLVM detected')
        if write_config_h:
            AddConfigKey(ctx, key, 0)
        ctx.Result(0)
        return 0

    packetizerlibs = ['Packetizer']

    # RequirePackage('llvm') will add all libraries needed for linking with
    # LLVM and return dictionary of all modified variables with original
    # values.
    savedVars = ctx.env.RequirePackage('llvm')

    # Note: order of adding to LIBS variable is important for static
    # libraries, Packetizer library need to be added before LLVM so
    # LLVM symbols not found in Packetizer library will be found in the
    # LLVM library after it.
    ctx.env.Prepend(LIBS = packetizerlibs)

    ret = ctx.TryLink("""
#define PACKETIZER_STATIC_LIBS
#include <Packetizer/api.h>

int main(int argc, char **argv)
{
    Packetizer::Packetizer* packetizer = Packetizer::getPacketizer(false, false);
    Packetizer::addFunctionToPacketizer(packetizer, "test", "test_simd", 4);
    return 0;
}
""", extension='.cpp')

    ctx.env.RestoreVars(savedVars)

    if ret:
        ctx.env.DeclarePackage('packetizer',
                               vars={'LIBS' : packetizerlibs,
                                     'CPPDEFINES' : confprefix+'HAVE_PACKETIZER'},
                               dependencies='llvm',
                               trigger_libs=['packetizer', 'Packetizer'],
                               trigger_frameworks=['Packetizer'])

        if ctx.env.GetPackage('llvm_shared'):
            ctx.env.DeclarePackage('packetizer_shared',
                                   vars={'LIBS' : packetizerlibs,
                                         'CPPDEFINES' : confprefix+'HAVE_PACKETIZER'},
                                   dependencies='llvm_shared',
                                   trigger_libs=['packetizer_shared', 'Packetizer_shared'],
                                   trigger_frameworks=['Packetizer_shared'])


    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckPacketizer', CheckPacketizer)

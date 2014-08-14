import os
from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.btools import runCommand
from builder.bconfig import getAutoconfPrefix

def CheckOpenSSL(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for OpenSSL... ')
    confprefix = getAutoconfPrefix(ctx.env)
    platform = ctx.env['PLATFORM']

    savedVars = ctx.env.SaveVars('LIBS')

    if platform == 'win32':
        if ctx.env.IsMSVC_Debug() :
            libs = ['libeay32', 'ssleay32']
        else:
            libs = ['libeay32', 'ssleay32']
    else:
        libs = ['ssl', 'crypto']

    ctx.env.Append(LIBS = libs)
    ret = ctx.TryLink("""
        #include <openssl/ssl.h>
        int main(int argc, char **argv)
        {
            SSL_load_error_strings();
            SSL_library_init ();
            return 0;
        }
        """, extension='.c')

    ctx.env.RestoreVars(savedVars)

    if ret:
        ctx.env.DeclarePackage('openssl',
                               trigger_libs=['ssl', 'openssl', 'OpenSSL'],
                               trigger_frameworks=['OpenSSL'],
                               LIBS = libs)

    key = confprefix+'HAVE_OPENSSL'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckOpenSSL', CheckOpenSSL)

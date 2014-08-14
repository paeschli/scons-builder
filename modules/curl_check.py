import os
from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.btools import runCommand
from builder.bconfig import getAutoconfPrefix

def CheckCurl(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for libcurl... ')
    confprefix = getAutoconfPrefix(ctx.env)
    platform = ctx.env['PLATFORM']

    savedVars = ctx.env.SaveVars('LIBS')

    if platform == 'win32':
        if ctx.env.IsMSVC_Debug() :
            libs = ['libcurl_imp']
        else:
            libs = ['libcurl_imp']
    else:
        libs = ['curl']

    ctx.env.Append(LIBS = libs)
    ret = ctx.TryLink("""
        #include <curl/curl.h>
        int main(int argc, char **argv)
        {
            CURL * curlHandle = curl_easy_init();
            curl_easy_cleanup(curlHandle);
            return 0;
        }
        """, extension='.c')

    ctx.env.RestoreVars(savedVars)

    if ret:
        ctx.env.DeclarePackage('curl',
                               trigger_libs=['curl', 'Curl'],
                               trigger_frameworks=['Curl'],
                               LIBS = libs)

    key = confprefix+'HAVE_CURL'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckCurl', CheckCurl)

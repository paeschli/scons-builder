from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import filterOut

def CheckXercesC(ctx, write_config_h=False, add_to_compiler_env=False,
                 link_static_lib=False):
    ctx.Message('Checking for xerces-c Library... ')
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_XERCESC'

    compiler = ctx.env['compiler']
    platform = ctx.env['PLATFORM']
    isWin32 = (platform == 'win32')

    libsToCheck = ('xerces-c', 'xerces-c_2', 'xerces-c_3')

    if isWin32:
        if link_static_lib:
            libsToCheck = ('xerces-c_static',
                           'xerces-c_static_2',
                           'xerces-c_static_3')

        if ctx.env.IsMSVC_Debug():
            # add 'D' suffix
            libsToCheck = [s+'D' for s in libsToCheck]

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS')

    ret = 0

    xercesc_libs = []

    for lib in libsToCheck:
        ctx.env.AppendUnique(LIBS = [lib])
        ret = ctx.TryLink("""
        #include <xercesc/util/XercesVersion.hpp>
        #include <stdio.h>
        int main(int argc, char **argv) {
          printf("%s\\n", XERCES_FULLVERSIONSTR);
        }
""", extension='.cpp')
        ctx.env.RestoreVars(savedVars)
        if ret:
            xercesc_libs = [lib]
            ctx.env.Replace(LIBXERCESC=[lib])
            break

    if ret:
        vars = {'CPPDEFINES' : [key]}
        if isWin32 and link_static_lib:
            vars['CPPDEFINES'].append('XERCES_STATIC_LIBRARY')
        #vars['LINKFLAGS'] = ['/NODEFAULTLIB:MSVCRT.LIB']

        ctx.env.DeclarePackage('xercesc', LIBS=xercesc_libs,
                               dependencies=[],
                               vars=vars,
                               trigger_libs=['xercesc', 'xerces-c'],
                               trigger_frameworks=['xercesc'])

    ctx.env.RestoreVars(savedVars)

    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckXercesC', CheckXercesC)

from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import filterOut

def CheckBoostRegex(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for Boost Regex Library... ')
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_BOOST_REGEX'
    
    compiler = ctx.env['compiler']
    platform = ctx.env['PLATFORM']
    isWin32 = (platform == 'win32')

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS')

    ret = 0

    code = """
        #include <boost/regex.hpp>
        int main(int argc, char** argv) {
            const boost::regex e("\\\\d{2}");
            return boost::regex_match("12", e);
        }
"""

    # On Windows MSVC and Intel compiler automatically find out the correct
    # library name.
    if isWin32 and compiler in ('MSVC', 'INTEL', 'INTEL_NOGCC'):
        boost_regex_libs = []
        ret = ctx.TryLink(code, extension='.cpp')
    else:
        for lib in ('boost_regex-mt', 'boost_regex'):
            boost_regex_libs = [lib]

            ctx.env.AppendUnique(LIBS = boost_regex_libs)

            ret = ctx.TryLink(code, extension='.cpp')

            ctx.env.RestoreVars(savedVars)

            if ret:
                break

    if ret:
        ctx.env.DeclarePackage('boost_regex', LIBS=boost_regex_libs,
                               dependencies=[],
                               vars={'CPPDEFINES' : [key]},
                               trigger_libs=['boost_regex'],
                               trigger_frameworks=['boost_regex'])

    ctx.env.RestoreVars(savedVars)

    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])
    
    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckBoostRegex', CheckBoostRegex)

from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import filterOut

def CheckBoostProgramOptions(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for Boost Program Options Library... ')
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_BOOST_PROGRAM_OPTIONS'

    compiler = ctx.env['compiler']
    platform = ctx.env['PLATFORM']
    isWin32 = (platform == 'win32')

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS')

    ret = 0

    code = """
        #include <boost/program_options.hpp>
        void func() { }

        int main(int argc, char** argv) {
            boost::program_options::options_description desc("Test");
            desc.add_options()
                 ("help", "produce this help message");
            return 0;
        }
"""

    # On Windows MSVC and Intel compiler automatically find out the correct
    # library name.
    if isWin32 and compiler in ('MSVC', 'INTEL', 'INTEL_NOGCC'):
        boost_program_options_libs = []
        ret = ctx.TryLink(code, extension='.cpp')
    else:
        for lib in ('boost_program_options-mt', 'boost_program_options'):
            boost_program_options_libs = [lib]

            ctx.env.AppendUnique(LIBS = boost_program_options_libs)

            ret = ctx.TryLink(code, extension='.cpp')

            ctx.env.RestoreVars(savedVars)

            if ret:
                break

    if ret:
        ctx.env.DeclarePackage('boost_program_options', LIBS=boost_program_options_libs,
                               dependencies=[],
                               vars={'CPPDEFINES' : [key]},
                               trigger_libs=['boost_program_options'],
                               trigger_frameworks=['boost_program_options'])

    ctx.env.RestoreVars(savedVars)

    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckBoostProgramOptions', CheckBoostProgramOptions)

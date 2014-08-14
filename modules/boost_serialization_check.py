from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import filterOut

def CheckBoostSerialization(ctx, write_config_h=False, add_to_compiler_env=False, enable_package_cppdefines=False):
    ctx.Message('Checking for Boost Serialization Library... ')
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_BOOST_SERIALIZATION'

    compiler = ctx.env['compiler']
    platform = ctx.env['PLATFORM']
    isWin32 = (platform == 'win32')

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS')

    ret = 0

    code = """
        #include <fstream>
        #include <boost/archive/text_oarchive.hpp>
        #include <boost/archive/text_iarchive.hpp>
        int main(int argc, char** argv)
        {
          std::ofstream ofs("filename");
          {
            boost::archive::text_oarchive oa(ofs);
            double d = 2.0;
            oa << d;
          }
          return 0;
        }
"""

    # On Windows MSVC and Intel compiler automatically find out the correct
    # library name.
    if isWin32 and compiler in ('MSVC','INTEL','INTEL_NOGCC'):
        boost_serialization_libs = []
        ret = ctx.TryLink(code, extension='.cpp')
    else:
        for lib in ('boost_serialization-mt', 'boost_serialization'):
            boost_serialization_libs = ctx.env.Split(lib)

            ctx.env.AppendUnique(LIBS = boost_serialization_libs)

            ret = ctx.TryLink(code, extension='.cpp')

            ctx.env.RestoreVars(savedVars)

            if ret:
                break

    if ret:
        vars = {}
        if enable_package_cppdefines:
            vars.update({'CPPDEFINES' : [key]})
        ctx.env.DeclarePackage('boost_serialization', LIBS=boost_serialization_libs,
                               dependencies=[],
                               vars=vars,
                               trigger_libs=['boost_serialization'],
                               trigger_frameworks=['boost_serialization'])

    ctx.env.RestoreVars(savedVars)

    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckBoostSerialization', CheckBoostSerialization)

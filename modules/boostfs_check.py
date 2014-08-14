from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import filterOut

def CheckBoostFileSystem(ctx, write_config_h=False, add_to_compiler_env=False, enable_package_cppdefines=False):
    ctx.Message('Checking for Boost Filesystem Library... ')
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_BOOST_FILESYSTEM'
    
    compiler = ctx.env['compiler']
    platform = ctx.env['PLATFORM']
    isWin32 = (platform == 'win32')

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS')
    
    ret = 0

    code = """
        #include <boost/filesystem/operations.hpp>
        int main(int argc, char** argv) {
            namespace bfs = boost::filesystem;
            bool b = bfs::exists(argv[0]);
            return b?1:0;
        }
"""

    # On Windows MSVC and Intel compiler automatically find out the correct
    # library name.
    if isWin32 and compiler in ('MSVC','INTEL','INTEL_NOGCC'):
        boost_filesystem_libs = []
        ret = ctx.TryLink(code, extension='.cpp')
    else:
        for lib in ('boost_filesystem-mt', 'boost_filesystem',
                    'boost_system-mt boost_filesystem-mt',
                    'boost_system boost_filesystem',):
            boost_filesystem_libs = ctx.env.Split(lib)

            ctx.env.AppendUnique(LIBS = boost_filesystem_libs)

            ret = ctx.TryLink(code, extension='.cpp')

            ctx.env.RestoreVars(savedVars)

            if ret:
                break

    if ret:
        vars = {}
        if enable_package_cppdefines:
            vars.update({'CPPDEFINES' : [key]})
        ctx.env.DeclarePackage('boost_filesystem', LIBS=boost_filesystem_libs,
                               dependencies=[],
                               vars=vars,
                               trigger_libs=['boost_filesystem'],
                               trigger_frameworks=['boost_filesystem'])

    ctx.env.RestoreVars(savedVars)

    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])
    
    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckBoostFileSystem', CheckBoostFileSystem)

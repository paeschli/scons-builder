from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import filterOut

def CheckBoostPython(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for Boost Python Library... ')

    try:
        import distutils.sysconfig
        python_includes = [distutils.sysconfig.get_python_inc()]
        python_libs = ['python'+distutils.sysconfig.get_python_version()]
    except ImportError:
        ctx.Message('No distutils package, use default paths')
        python_includes = []
        python_libs = None
    
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_BOOST_PYTHON'
    
    compiler = ctx.env['compiler']
    platform = ctx.env['PLATFORM']

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS CPPPATH')

    ret = 0

    code = """
    #include <boost/python.hpp>
    using namespace boost::python;

    char const* greet()
    {
      return "hello, world";
    }

    BOOST_PYTHON_MODULE(hello)
    {
      def("greet", greet);
    }

    // dummy main func
    int main(int argc, char **argv) { }
    """

    def doCheck(python_includes, python_libs, boost_python_libs):
        if boost_python_libs:
            ctx.env.AppendUnique(LIBS = boost_python_libs)

        ctx.env.AppendUnique(CPPPATH = python_includes)
        if python_libs:
            ctx.env.AppendUnique(LIBS=python_libs+boost_python_libs)
            return ctx.TryLink(code, extension='.cpp')
        else:
            return ctx.TryCompile(code, extension='.cpp')


    # MSVC and Intel compiler automatically find out the correct library name
    if compiler not in ('MSVC', 'INTEL', 'INTEL_NOGCC'):
        boost_python_libs_alt = [['boost_python-mt'], ['boost_python']]
    else:
        boost_python_libs_alt = [[]]

    for libs in boost_python_libs_alt:
        boost_python_libs = libs
        ret = doCheck(python_includes, python_libs, boost_python_libs)
        ctx.env.RestoreVars(savedVars)
        if ret:
            break

    if ret:

        vars = {'CPPDEFINES' : [key], 'SHLIBPREFIX' : '',
                'CPPPATH' : python_includes}

        if platform == 'win32':
            vars['SHLIBSUFFIX'] = '.pyd'
        
        ctx.env.DeclarePackage('boost_python', LIBS=boost_python_libs,
                               dependencies=[],
                               vars=vars,
                               trigger_libs=['boost_python'],
                               trigger_frameworks=['boost_python'])

        if python_libs:
            ctx.env.Replace(LIBBOOST_PYTHON=['boost_python'])
            ctx.env.Replace(LIBPYTHON=python_libs)

    ctx.env.RestoreVars(savedVars)

    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])
    
    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckBoostPython', CheckBoostPython)

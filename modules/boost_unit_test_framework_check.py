from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import filterOut

def CheckBoostUnitTestFramework(ctx, write_config_h=False,
                                add_to_compiler_env=False):

    ctx.Message('Checking for Boost Unit Test Framework Library... ')
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_BOOST_UNIT_TEST_FRAMEWORK'

    compiler = ctx.env['compiler']
    platform = ctx.env['PLATFORM']
    isWin32 = (platform == 'win32')

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS CPPDEFINES')

    ret = 0

    code = """
        #define BOOST_TEST_MODULE example
        #include <boost/test/unit_test.hpp>

        BOOST_AUTO_TEST_CASE( test )
        {
            int i = 2;
            int j = 1;
            BOOST_REQUIRE_EQUAL( i, j );
        }
"""

    # On Windows MSVC and Intel compiler automatically find out the correct
    # library name.
    if isWin32 and compiler in ('MSVC', 'INTEL', 'INTEL_NOGCC'):
        boost_utf_libs = []
        boost_utf_cppdefs = []
        ret = ctx.TryLink(code, extension='.cpp')
    else:
        for lib in ('boost_unit_test_framework-mt', 'boost_unit_test_framework'):
            boost_utf_libs = [lib]
            boost_utf_cppdefs = ['BOOST_TEST_DYN_LINK']
            ctx.env.AppendUnique(LIBS = boost_utf_libs)
            ctx.env.AppendUnique(CPPDEFINES = boost_utf_cppdefs)

            ret = ctx.TryLink(code, extension='.cpp')

            ctx.env.RestoreVars(savedVars)

            if ret:
                break

    if ret:
        cppdefines = [key]+boost_utf_cppdefs
        ctx.env.DeclarePackage('boost_unit_test_framework', LIBS=boost_utf_libs,
                               dependencies=[],
                               vars={'CPPDEFINES' : cppdefines},
                               trigger_libs=['boost_unit_test_framework'],
                               trigger_frameworks=['boost_unit_test_framework'])

    ctx.env.RestoreVars(savedVars)

    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=cppdefines)

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckBoostUnitTestFramework', CheckBoostUnitTestFramework)

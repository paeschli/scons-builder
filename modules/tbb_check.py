from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import filterOut
from builder.bconfig import Version

def CheckTBB(ctx, write_config_h=False, add_to_compiler_env=False,
             min_version=None, max_version=None):
    ctx.Message('Checking for TBB Library... ')
    confprefix = getAutoconfPrefix(ctx.env)

    platform = ctx.env['PLATFORM']

    if min_version is not None:
        min_version = Version(min_version)
    if max_version is not None:
        max_version = Version(max_version)

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS CPPPATH')

    ret = 0

    if platform == 'win32':
        # on windows, TBB include path should be in $PATH
        if ctx.env.IsMSVC_Debug():
            # debug version of library ends with '_debug'
            tbbLibName = 'tbb_debug'
        else:
            tbbLibName = 'tbb'
        ctx.env.Append(LIBS = [tbbLibName])
        ret, outputStr = ctx.TryRun("""
            #include <tbb/tbb_stddef.h>
            #include <tbb/task_scheduler_init.h>
            #include <iostream>

            void test() { tbb::task_scheduler_init init; }

            int main(int argc, char** argv)
            {
            #if defined(TBB_VERSION_MAJOR) && defined(TBB_VERSION_MINOR) && defined(TBB_INTERFACE_VERSION)
                std::cout<<TBB_VERSION_MAJOR<<"."
                         <<TBB_VERSION_MINOR<<"."
                         <<TBB_INTERFACE_VERSION
                         <<std::endl;
            #else
                // Version is not defined, we assume 2.0
                std::cout<<"2.0"<<std::endl;
            #endif
                return 0;
            }
            """, extension='.cpp')

        if ret:
            tbbVersion = Version(outputStr)
            ctx.Message('version %s ' % tbbVersion)

            if tbbVersion.compatible(min_version, max_version):
                tbbPackage = ctx.env.DeclarePackage(
                    'tbb',
                    LIBS=[tbbLibName],
                    TBB_VERSION=tbbVersion,
                    trigger_libs=['tbb', 'TBB'])
            else:
                ctx.Message('is not within required [%s, %s] version range ' % \
                            (min_version, max_version))
                ret = 0

        ctx.env.RestoreVars(savedVars)

    else:

        # on linux, search in some common locations
        for includeDir in ('',):
            ctx.env.Append(LIBS = ['tbb'])
            ctx.env.Append(CPPPATH = [includeDir])
            ret, outputStr = ctx.TryRun("""
                #include <tbb/tbb_stddef.h>
                #include <tbb/task_scheduler_init.h>
                #include <iostream>

                void test() { tbb::task_scheduler_init init; }

                int main(int argc, char** argv)
                {
                #if defined(TBB_VERSION_MAJOR) && defined(TBB_VERSION_MINOR) && defined(TBB_INTERFACE_VERSION)
                    std::cout<<TBB_VERSION_MAJOR<<"."
                             <<TBB_VERSION_MINOR<<"."
                             <<TBB_INTERFACE_VERSION
                             <<std::endl;
                #else
                    // Version is not defined, we assume 2.0
                    std::cout<<"2.0"<<std::endl;
                #endif
                    return 0;
                }
            """, extension='.cpp')

            ctx.env.RestoreVars(savedVars)

            if ret:
                tbbVersion = Version(outputStr)
                ctx.Message('version %s ' % tbbVersion)
                if tbbVersion.compatible(min_version, max_version):
                    tbbPackage = ctx.env.DeclarePackage(
                        'tbb',
                        CPPPATH=[includeDir],
                        LIBS=['tbb'],
                        TBB_VERSION=tbbVersion,
                        trigger_libs=['tbb', 'TBB'])
                else:
                    ctx.Message(
                        'is not within required [%s, %s] version range ' % \
                        (min_version, max_version))
                    ret = 0
                break

    key = confprefix+'HAVE_TBB'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckTBB', CheckTBB)

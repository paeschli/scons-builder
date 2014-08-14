from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import getArchInfo, ARCH_X86_64
from builder.bconfig import Version
import os.path

def CheckCUDA(ctx, write_config_h=False, add_to_compiler_env=False,
              min_version=None, max_version=None):
    ctx.Message('Checking for CUDA Library... ')
    confprefix = getAutoconfPrefix(ctx.env)

    platform = ctx.env['PLATFORM']
    archInfo = getArchInfo(ctx.env)

    isWin32 = platform == 'win32'
    isX64 = archInfo.getArchID() == ARCH_X86_64

    if min_version is not None:
        min_version = Version(min_version)
    if max_version is not None:
        max_version = Version(max_version)

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS CPPPATH')

    # detect common locations
    commonLocations = [None] # default location
    paths = []

    if not isWin32:
        # default search path on *ix
        paths.append(ctx.env.Dir('/usr/local/cuda'))

    for p in paths:
        if os.path.exists(p.Dir('include').File('cuda.h').abspath):
            commonLocations.append(p)

    ret = 0

    for location in commonLocations:

        ctx.env.RestoreVars(savedVars)

        ctx.env.Append(LIBS = ['cuda'])
        vars = {'LIBS' : ['cuda']}

        if location is not None:
            includeDir = str(location.Dir('include'))
            ctx.env.Append(CPPPATH = [includeDir])
            vars['CPPPATH']= [includeDir]

            if isX64:
                lib64Dir = str(location.Dir('lib64'))
                ctx.env.Append(LIBPATH = [lib64Dir])
                vars['LIBPATH'] = [lib64Dir]
            else:
                libDir = str(location.Dir('lib'))
                ctx.env.Append(LIBPATH = [libDir])
                vars['LIBPATH'] = [libDir]

        ret, outputStr = ctx.TryRun("""
        #include <stdio.h>
        #include <cuda.h>

        int main(int argc, char** argv)
        {
          printf("%i\\n", CUDA_VERSION);
          return 0;
        }
        """, extension='.c')

        if ret:
            v = int(outputStr)
            vmajor = int(v / 1000)
            vminor = (v % 1000) / 10

            libVersion = Version(vmajor, vminor)

            if not libVersion.compatible(min_version, max_version):
                ctx.Message(
                    'version %s is not within required [%s, %s] version range '\
                    % (libVersion, min_version, max_version))
                ret = 0
                continue

            # check for CUDA SDK
            ret = ctx.TryLink("""
            #include <vector_functions.h>

            int main(int argc, char** argv)
            {
              return 0;
            }
            """, extension='.cpp')

            if not ret:
                ret = 0
                continue

            ctx.env.RestoreVars(savedVars)

            ctx.Message('version %s ' % libVersion)

            vars['CUDA_VERSION'] = libVersion
            libPackage = ctx.env.DeclarePackage(
                'cuda',
                vars=vars,
                trigger_libs=['cuda', 'CUDA'])
            break

    ctx.env.RestoreVars(savedVars)

    key = confprefix+'HAVE_CUDA'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckCUDA', CheckCUDA)

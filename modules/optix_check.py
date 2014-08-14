from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import getArchInfo, ARCH_X86_64
from builder.bconfig import Version
import os.path

def CheckOptix(ctx, write_config_h=False, add_to_compiler_env=False,
               min_version=None, max_version=None):
    ctx.Message('Checking for Optix Library... ')
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_OPTIX'

    platform = ctx.env['PLATFORM']
    archInfo = getArchInfo(ctx.env)

    # If CUDA is not available Optix cannot be used
    if not ctx.env.GetPackage('cuda'):
        ctx.Message('No CUDA detected, call CheckCUDA first')
        if write_config_h:
            AddConfigKey(ctx, key, 0)
        ctx.Result(0)
        return 0

    isWin32 = platform == 'win32'
    isX64 = archInfo.getArchID() == ARCH_X86_64

    if min_version is not None:
        min_version = Version(min_version)
    if max_version is not None:
        max_version = Version(max_version)

    # RequirePackage('cuda') will add all libraries needed for linking with
    # CUDA and return dictionary of all modified variables with original
    # values.
    savedVars = ctx.env.RequirePackage('cuda')

    # detect common locations
    commonLocations = [None] # default location
    paths = ctx.env.Glob(os.path.join(os.path.expanduser('~'),
                                      'NVIDIA-OptiX-SDK*'))
    for p in paths:
        if os.path.exists(p.Dir('include').File('optix.h').abspath):
            commonLocations.append(p)

    ret = 0

    for location in commonLocations:

        ctx.env.RestoreVars(savedVars)

        ctx.env.RequirePackage('cuda')

        ctx.env.Append(LIBS = ['optix'])
        vars = {'LIBS' : ['optix']}

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
        #include <optix.h>

        int main(int argc, char** argv)
        {
          printf("%i\\n", OPTIX_VERSION);
          return 0;
        }
        """, extension='.c')

        if ret:
            v = int(outputStr)
            vmajor = int(v / 1000)
            vminor = (v % 1000) / 10
            vmicro = v % 10

            libVersion = Version(vmajor, vminor, vmicro)

            if not libVersion.compatible(min_version, max_version):
                ctx.Message('version %s is not within required [%s, %s] version range ' % \
                            (libVersion, min_version, max_version))
                ret = 0
                continue

            ctx.Message('version %s ' % libVersion)

            # check for optixu/optixpp
            ret = ctx.TryLink("""
            #include <optixu/optixu_matrix.h>

            int main(int argc, char** argv)
            {
              optix::Matrix3x3 matrix;
              return 0;
            }
            """, extension='.cpp')

            if not ret:
                ctx.Message('could not link with optixu library')
                ret = 0
                continue

            ctx.env.RestoreVars(savedVars)

            vars['OPTIX_VERSION'] = libVersion
            libPackage = ctx.env.DeclarePackage(
                'optix',
                vars=vars,
                dependencies=['cuda'],
                trigger_libs=['optix', 'Optix'])
            break

    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckOptix', CheckOptix)

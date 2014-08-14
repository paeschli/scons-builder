from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import Version
import os.path

def CheckAssimp(ctx, write_config_h=False, add_to_compiler_env=False,
                min_version=None, max_version=None):
    ctx.Message('Checking for Assimp library... ')
    confprefix = getAutoconfPrefix(ctx.env)

    compiler = ctx.env['compiler']
    platform = ctx.env['PLATFORM']
    isWin32 = (platform == 'win32')

    if min_version is not None:
        min_version = Version(min_version)
    if max_version is not None:
        max_version = Version(max_version)

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS CCFLAGS')

    assimpLIBS = ['assimp']
    assimpCCFLAGS = []

    ctx.env.Append(LIBS = assimpLIBS)
    ctx.env.Append(CCFLAGS = assimpCCFLAGS)

    ret, outputStr = ctx.TryRun("""
#include "assimp.h"
#include "aiVersion.h"
#include <stdio.h>  
int main(int argc, char **argv) {
  printf("%i.%i.%i\\n", aiGetVersionMajor(), aiGetVersionMinor(), aiGetVersionRevision());
  return 0;
}
""", extension='.c')

    if ret:
        assimpVersion = Version(outputStr.strip())
        ctx.Message('version %s ' % assimpVersion)

        if assimpVersion.compatible(min_version, max_version):
            ctx.env.DeclarePackage('assimp',
                                   LIBS=assimpLIBS,
                                   ASSIMP_VERSION=assimpVersion,
                                   CCFLAGS=assimpCCFLAGS,
                                   trigger_libs=['assimp'],
                                   trigger_frameworks=['assimp'])
        else:
            ctx.Message('is not within required [%s, %s] version range ' % \
                        (min_version, max_version))

            ret = 0

    ctx.env.RestoreVars(savedVars)

    key = confprefix+'HAVE_ASSIMP'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])
    
    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckAssimp', CheckAssimp)

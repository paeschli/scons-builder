from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import filterOut
from builder.bconfig import Version

def CheckAxtor(ctx, write_config_h=False, add_to_compiler_env=False,
               min_version=None, max_version=None):
    ctx.Message('Checking for Axtor Backends (OpenCL, GLSL) ... ')
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix +'HAVE_AXTOR'

#   if min_version is not None:
#      min_version = Version(min_version)
#   if max_version is not None:
#      max_version = Version(max_version)

    # LLVM is required for axtor
    if not ctx.env.GetPackage('llvm'):
        ctx.Message('LLVM not detected')
        if write_config_h:
            AddConfigKey(ctx, key, 0)
        ctx.Result(0)
        return 0

    savedVars = ctx.env.RequirePackage('llvm')
    axtorCoreLibs = ctx.env.Split("""
        axtorMetainfo
        axtorWriter
        axtorIntrinsics
        axtorGenericC
        axtorInterface
        axtorConsole
        axtorPass
        axtorParsers
        axtorSolvers
        axtorCNS
        axtorAST
        axtorUtil
        """)

    axtorBackendLibs = ['Axtor_OCL','Axtor_GLSL']

    axtorLibs = axtorBackendLibs + axtorCoreLibs

    ctx.env.Prepend(LIBS = axtorLibs)
    ret, outputStr = ctx.TryRun("""
   #include <axtor_ocl/OCLBackend.h>
   #include <axtor_glsl/GLSLBackend.h>

   int main(int argc, char** argv)
   {
      axtor::OCLBackend oclBackend;
      axtor::GLSLBackend glslBackend;
      printf("%d",1);
      return 0;
   }
   """, extension='.cpp')

    ctx.env.RestoreVars(savedVars)

    if ret:
        ctx.env.DeclarePackage('axtor',
                               vars={'LIBS' : axtorLibs},
                               dependencies='llvm',
                               trigger_libs=['Axtor', 'Axtor'],
                               trigger_frameworks=['Axtor', 'Axtor'])

#        if ctx.env.GetPackage('llvm_shared'):
#            ctx.env.DeclarePackage('axtor_shared',
#                                   vars={'LIBS' : axtorSharedLibs},
#                                   trigger_libs=['Axtor_shared'],
#                                   trigger_frameworks=['Axtor_shared'])

   # define
#   if ret:
#       ctx.env.DeclarePackage('axtor',
#                               vars={'LIBS' : axtorLibs,
#                                     'CPPDEFINES' : key},
#                               dependencies='llvm',
#                               trigger_libs=['axtor', 'Axtor'],
#                               trigger_frameworks=['Axtor'])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckAxtor', CheckAxtor)

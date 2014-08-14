from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import filterOut
from builder.bconfig import Version

def CheckOpenCL(ctx, write_config_h=False, add_to_compiler_env=False,
              min_version=None, max_version=None):
   ctx.Message('Checking for OpenCL Library... ')
   confprefix = getAutoconfPrefix(ctx.env)

   platform = ctx.env['PLATFORM']

   if min_version is not None:
      min_version = Version(min_version)
   if max_version is not None:
      max_version = Version(max_version)

   savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS CPPPATH')

   ret = 0
   ctx.env.Append(LIBS = ['OpenCL'])
   ret, outputStr = ctx.TryRun("""
   #include <CL/cl.h>

   int main(int argc, char** argv)
   {
   cl_uint numEntries=2;
   cl_platform_id platforms[2];
   cl_uint numPlatforms;

   clGetPlatformIDs(numEntries,
              (cl_platform_id*) platforms,
              &numPlatforms);

   printf("%d", CL_VERSION_1_0);
   return 0;
   }
   """, extension='.c')

   ctx.env.RestoreVars(savedVars)

   # define 
   # if ret:
   #   key = confprefix + 'HAVE_OPENCL'

   ctx.Result(ret)
   return ret

RegisterCustomTest('CheckOpenCL', CheckOpenCL)

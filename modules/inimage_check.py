import os
from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix

def CheckInImage(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for InImage library... ')
    confprefix = getAutoconfPrefix(ctx.env)

    platform = ctx.env['PLATFORM']
    ROOT_DIR = ctx.env.GetRootDir()
    INIMAGE_DIST_DIR = ctx.env.GetEnvVar('INIMAGE_DIST_DIR')
    
    ret = 0

    if not INIMAGE_DIST_DIR:
        # try to link inImage library

        savedVars = ctx.env.SaveVars('LIBS')

        ctx.env.Append(LIBS = ['InImage'])
	
        ret = ctx.TryLink("""
#include "inimage/Image.hpp"
#include "inimage/ImageIO.hpp"
        
using namespace inimage;
    
int main(int argc, char **argv) {
  Image *img = ImageIO::read("test.ppm");
  delete img;
  return 0;
}
""", extension='.cpp')
        
        if ret:
            ctx.env.DeclarePackage('inimage', LIBS=['InImage'],
                                   trigger_libs=['InImage', 'inimage'])
            
        ctx.env.RestoreVars(savedVars)
        
    if not INIMAGE_DIST_DIR and not ret:
        # is inImage a sub module ?
        p = os.path.join(ROOT_DIR, 'inImage')
        if not os.path.exists(p):
            # is inImage one dir higher ?
            p = os.path.join(ROOT_DIR, '..', 'inImage')

        if os.path.exists(p):
            INIMAGE_DIST_DIR = p
        else:
            INIMAGE_DIST_DIR = None
            ctx.Message('Warning: could not find inImage, you need to define INIMAGE_DIST_DIR environment variable. ')


    if INIMAGE_DIST_DIR and not ret:
        
        if platform == 'win32':
            imgLibFile = 'InImage.dll'
        elif platform == 'darwin':
            imgLibFile = 'libInImage.dylib'
        else:
            imgLibFile = 'libInImage.so'

        libDir = os.path.join(INIMAGE_DIST_DIR, 'lib')
        imgLib = os.path.join(libDir, imgLibFile)
        if not os.path.exists(imgLib):
            libDir = os.path.join(INIMAGE_DIST_DIR, 'build', 'lib')
            imgLib = os.path.join(libDir, imgLibFile)
            if not os.path.exists(imgLib):
                ctx.Message('Warning: could not find inImage library %s. ' % (imgLib,))
                if write_config_h:
                    AddConfigKey(ctx, confprefix+'HAVE_LIBINIMAGE', 0)
                ctx.Result(0)
                return 0
                
        incDir = os.path.join(INIMAGE_DIST_DIR, 'include')
        if not os.path.exists(incDir):
            incDir = os.path.join(INIMAGE_DIST_DIR, '..', 'include')
            if not os.path.exists(incDir):
                ctx.Message('Warning: could not find inImage include dir %s. ' % (incDir,))
                if write_config_h:
                    AddConfigKey(ctx, confprefix+'HAVE_LIBINIMAGE', 0)
                ctx.Result(0)
                return 0

        ctx.env.Replace(INIMAGE_LIB_DIR=os.path.abspath(libDir))
        ctx.env.Replace(INIMAGE_INCLUDE_DIR=os.path.abspath(incDir))

        ctx.env.DeclarePackage('inimage',
                               CPPPATH=[os.path.abspath(incDir)],
                               LIBPATH=[os.path.abspath(libDir)],
                               LIBS=['InImage'],
                               trigger_libs=['InImage', 'inimage'])
        
        ret = 1

    key = confprefix+'HAVE_LIBINIMAGE'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckInImage', CheckInImage)

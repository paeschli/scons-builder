from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import filterOut

def CheckPNG(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for libpng... ')
    confprefix = getAutoconfPrefix(ctx.env)

    platform = ctx.env['PLATFORM']
    lastLIBS = list(ctx.env.get('LIBS', []))

    if platform == 'win32':
        if ctx.env.IsMSVC_Debug() :
            ZLIB=['zlibd']
            pngLibNames=['pngd']
        else:
            ZLIB=['zlib']
            pngLibNames=['png', 'libpng', '"libpng"']
    else:
        ZLIB=['z']
        pngLibNames=['png', 'libpng', '"libpng"']

    ret = 0
    # "libpng" variant is required here because scons seems to remove
    # remove sometimes lib prefix (at least in mingw mode)
    #for pnglib in ('png', 'libpng', '"libpng"'):
    for pnglib in pngLibNames:
        for includeDir in ('', 'libpng/'):
            ctx.env.Append(LIBS = [pnglib] + ZLIB)
            ret = ctx.TryLink("""
                #include <%spng.h>
                int main(int argc, char **argv) {
                  png_create_read_struct(PNG_LIBPNG_VER_STRING, 0, 0, 0);
                  return 0;
                }
""" % includeDir, extension='.c')
            ctx.env.Replace(LIBS = lastLIBS)
            if ret:
                ctx.env.Replace(LIBPNG=[pnglib] + ZLIB)
                break
        if ret:
            break

    key = confprefix+'HAVE_LIBPNG'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckPNG', CheckPNG)

def CheckJPEG(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for libjpeg... ')
    confprefix = getAutoconfPrefix(ctx.env)

    platform = ctx.env['PLATFORM']
    lastLIBS = list(ctx.env.get('LIBS', []))

    if platform == 'win32':
        if ctx.env.IsMSVC_Debug() :
            jpegLibNames=['jpegd']
        else:
            jpegLibNames=['jpeg']
    else:
        # "libjpeg" variant is required here because scons seems to remove
        # remove sometimes lib prefix (at least in mingw mode)
        jpegLibNames=['jpeg', 'libjpeg', '"libjpeg"']

    for jpeglib in jpegLibNames:
        ctx.env.Append(LIBS = [jpeglib])
        ret = ctx.TryLink("""
    #include <stdio.h>
    #include <jpeglib.h>
    int main(int argc, char **argv) {
      struct jpeg_decompress_struct cinfo;
      jpeg_destroy_decompress(&cinfo);
      return 0;
    }
""", extension='.c')
        ctx.env.Replace(LIBS = lastLIBS)
        if ret:
            ctx.env.Replace(LIBJPEG=[jpeglib])
            break

    key = confprefix+'HAVE_LIBJPEG'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckJPEG', CheckJPEG)

def CheckTIFF(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for libtiff... ')
    confprefix = getAutoconfPrefix(ctx.env)

    platform = ctx.env['PLATFORM']
    lastLIBS = list(ctx.env.get('LIBS', []))

    if platform == 'win32':
        if ctx.env.IsMSVC_Debug() :
            tiffLibNames=['tiffd']
        else:
            tiffLibNames=['tiff']
    else:
        tiffLibNames=['tiff', 'libtiff']

    for tifflib in tiffLibNames:
        ctx.env.Append(LIBS = [tifflib])
        ret = ctx.TryLink("""
    #include <stdio.h>
    #include <tiffio.h>
    int main(int argc, char **argv) {
      TIFF *tif;
      tif = TIFFOpen("test","r");
      TIFFClose(tif);
      return 0;
    }
""", extension='.c')
        ctx.env.Replace(LIBS = lastLIBS)
        if ret:
            ctx.env.Replace(LIBTIFF=[tifflib])
            break

    key = confprefix+'HAVE_LIBTIFF'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckTIFF', CheckTIFF)

def CheckImageMagick(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for ImageMagick... ')
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_LIBMAGICK'

    compiler = ctx.env['compiler']
    platform = ctx.env['PLATFORM']
    isWin32 = (platform == 'win32')

    varNames = 'LIBS FRAMEWORKS CPPPATH CCFLAGS CXXFLAGS LINKFLAGS'
    varNamesList = ctx.env.Split(varNames)

    savedVars = ctx.env.SaveVars(varNames)

    ret, output = ctx.TryAction('Magick-config --version')
    if ret:
        # removed --cflags due to the problems with some options:
        #                  conflicts between icc and g++ options

        # Reset all flags so we can find everything what is changed
        for var in varNamesList:
            ctx.env[var] = []

        ctx.env.ParseConfig('Magick-config --cppflags --ldflags --libs')
        if ctx.env.get('CCFLAGS'):
            ctx.env['CCFLAGS'] = filterOut('-no-undefined', ctx.env['CCFLAGS'])

        vars = {}
        for var in varNamesList:
            vars[var] = ctx.env[var]

        package = ctx.env.DeclarePackage(
            'magick',
            vars=vars,
            trigger_libs=['magick', 'Magick', 'MagickCore', 'ImageMagick'])

    ctx.env.RestoreVars(savedVars)

    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckImageMagick', CheckImageMagick)

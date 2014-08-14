from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import Version

def CheckOpenImageIO(ctx, write_config_h=False, add_to_compiler_env=False,
                     min_version=None, max_version=None):
    ctx.Message('Checking for OpenImageIO... ')
    confprefix = getAutoconfPrefix(ctx.env)

    platform = ctx.env['PLATFORM']
    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS')

    lib = 'OpenImageIO'

    ctx.env.Append(LIBS = [lib])
    ctx.env.RequirePackage('dl')

    ret, outputStr = ctx.TryRun("""
    #include <OpenImageIO/imageio.h>
    #include <cstdio>

    int main(int argc, char** argv)
    {
      printf("%i\\n", OPENIMAGEIO_VERSION);
      return 0;
    }
    """, extension='.cpp')

    if ret:
        v = int(outputStr)
        vmajor = int(v / 10000)
        tmp = (v % 10000)
        vminor = int(tmp / 100)
        vpatch = tmp % 100

        libVersion = Version(vmajor, vminor, vpatch)

        if not libVersion.compatible(min_version, max_version):
            ctx.Message(
                'version %s is not within required [%s, %s] version range '\
                % (libVersion, min_version, max_version))
            ret = 0
        else:
            ret = ctx.TryLink("""
            #include <OpenImageIO/imageio.h>
            using namespace OpenImageIO;
            int main(int argc, char **argv) {
              const char *filename = "test.png";
              const float pixels[] = {0,1,0,1,0,0};
              ImageOutput *out = ImageOutput::create (filename);
              ImageSpec spec(sizeof(pixels)/sizeof(float), 1, 1, TypeDesc::FLOAT);
              out->open(filename, spec);
              out->write_image(TypeDesc::FLOAT, pixels);
              out->close();
              delete out;
              return 0;
            }
            """, extension='.cpp')

    ctx.env.RestoreVars(savedVars)

    if ret:
        ctx.Message('version %s ' % libVersion)
        ctx.env.Replace(LIBOPENIMAGEIO=[lib])
        vars = {'LIBS' : [lib],
                'LIBOPENIMAGEIO_VERSION' : libVersion}
        ctx.env.DeclarePackage('openimageio',
                               LIBS=[lib],
                               vars=vars,
                               dependencies=['dl'],
                               trigger_libs=['OpenImageIO', 'openimageio'])


    key = confprefix+'HAVE_LIBOPENIMAGEIO'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckOpenImageIO', CheckOpenImageIO)

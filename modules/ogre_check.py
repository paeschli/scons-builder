from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import filterOut
from builder.bconfig import Version

def CheckOgre(ctx, write_config_h=False, add_to_compiler_env=False,
              min_version=None, max_version=None):
    ctx.Message('Checking for Ogre Library... ')
    confprefix = getAutoconfPrefix(ctx.env)

    platform = ctx.env['PLATFORM']

    if min_version is not None:
        min_version = Version(min_version)
    if max_version is not None:
        max_version = Version(max_version)

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS CPPPATH')

    ctx.env.Replace(OGRE_INCLUDES=[])

    ret = 0

    if platform == 'win32':
        # on windows, Ogre include path should be in $PATH
        if ctx.env.IsMSVC_Debug():
            # debug version of library ends with '_d'
            ogreLibName = 'OgreMain_d'
        else:
            ogreLibName = 'OgreMain'
        ctx.env.Append(LIBS = [ogreLibName])
        ret, outputStr = ctx.TryRun("""
            #include <Ogre.h>
            #include <iostream>

            Ogre::Root* makeRoot() { return new Ogre::Root(""); }

            int main(int argc, char** argv)
            {
                std::cout<<OGRE_VERSION_MAJOR<<"."
                         <<OGRE_VERSION_MINOR<<"."
                         <<OGRE_VERSION_PATCH
                         <<std::endl;
                return 0;
            }
            """, extension='.cpp')

        if ret:
            ogreVersion = Version(outputStr)
            ctx.Message('version %s ' % ogreVersion)

            if ogreVersion.compatible(min_version, max_version):
                ogrePackage = ctx.env.DeclarePackage(
                    'ogre',
                    LIBS=[ogreLibName],
                    OGRE_VERSION=ogreVersion,
                    trigger_libs=['Ogre',
                                  'OgreMain',
                                  'ogre'])
            else:
                ctx.Message('is not within required [%s, %s] version range ' % \
                            (min_version, max_version))
                ret = 0

        ctx.env.RestoreVars(savedVars)

    else:

        # on linux, search in some common locations
        for includeDir in ('', '/usr/include/OGRE', '/usr/local/include/OGRE'):
            ctx.env.Append(LIBS = ['OgreMain'])
            ctx.env.Append(CPPPATH = [includeDir])
            ret, outputStr = ctx.TryRun("""
                #include <Ogre.h>

                Ogre::Root* makeRoot() { return new Ogre::Root(""); }

                int main(int argc, char** argv)
                {
                    std::cout<<OGRE_VERSION_MAJOR<<"."
                             <<OGRE_VERSION_MINOR<<"."
                             <<OGRE_VERSION_PATCH
                             <<std::endl;
                    return 0;
                }
                """, extension='.cpp')

            ctx.env.RestoreVars(savedVars)

            if ret:
                ogreVersion = Version(outputStr)
                ctx.Message('version %s ' % ogreVersion)
                if ogreVersion.compatible(min_version, max_version):
                    ogrePackage = ctx.env.DeclarePackage(
                        'ogre',
                        CPPPATH=[includeDir],
                        LIBS=['OgreMain'],
                        OGRE_VERSION=ogreVersion,
                        trigger_libs=['Ogre',
                                      'OgreMain',
                                      'ogre'])
                    ctx.env.Replace(OGRE_INCLUDES=[includeDir])
                else:
                    ctx.Message(
                        'is not within required [%s, %s] version range ' % \
                        (min_version, max_version))
                    ret = 0
                break

    key = confprefix+'HAVE_OGRE'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])
    
    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckOgre', CheckOgre)

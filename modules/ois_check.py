from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import filterOut

# returns 1 if installed ois version is 1.2 or higher and 0 else
def CheckOISVersion_1_2(ctx, write_config_h = True):

    ctx.Message('Checking for OIS Library Version 1.2 or higher... ')

    confprefix = getAutoconfPrefix(ctx.env)

    platform = ctx.env['PLATFORM']
    lastLIBS = ctx.env.get('LIBS', [])
    lastCppPath = ctx.env.get('CPPPATH', [])

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS CPPPATH')

    ret = 0

    if platform == 'win32':
        # on windows, OIS include paths should be in $PATH
        if ctx.env.IsMSVC_Debug():
            # debug version of library ends with '_d'
            oisLibName = 'OIS_d'
        else:
            oisLibName = 'OIS'
        ctx.env.Append(LIBS = [oisLibName])
        ret = ctx.TryLink("""
            #include <OIS.h>
            int main(int argc, char** argv) {
                OIS::ParamList paramList;
                OIS::InputManager* input = OIS::InputManager::createInputSystem( paramList );
                input->getNumberOfDevices(OIS::OISKeyboard);
                return 0;
            }
            """, extension='.cpp')

    else:

        # on linux, search in some common locations
        for includeDir in ('', '/usr/include/OIS', '/usr/local/include/OIS'):
            ctx.env.Append(LIBS = ['OIS'])
            ctx.env.Append(CPPPATH = [includeDir])
            ret = ctx.TryLink("""
            #include <OIS.h>
            int main(int argc, char** argv) {
                OIS::ParamList paramList;
                OIS::InputManager* input = OIS::InputManager::createInputSystem( paramList );
                input->getNumberOfDevices(OIS::OISKeyboard);
                return 0;
            }
            """, extension='.cpp')

    ctx.env.RestoreVars(savedVars)

    if(ret):
        key = confprefix+'HAVE_OIS_VERSION_12_HIGHER'
        if not (write_config_h and AddConfigKey(ctx, key, ret)):
            # no config file is specified or it is disabled, use compiler options
            if ret and add_to_compiler_env:
                ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

def CheckOIS(ctx, write_config_h=True, add_to_compiler_env=False):
    ctx.Message('Checking for OIS Library... ')
    confprefix = getAutoconfPrefix(ctx.env)

    platform = ctx.env['PLATFORM']
    lastLIBS = ctx.env.get('LIBS', [])
    lastCppPath = ctx.env.get('CPPPATH', [])

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS CPPPATH')

    ctx.env.Replace(OIS_INCLUDES=[])

    ret = 0

    if platform == 'win32':
        # on windows, OIS include paths should be in $PATH
        if ctx.env.IsMSVC_Debug():
            # debug version of library ends with '_d'
            oisLibName = 'OIS_d'
        else:
            oisLibName = 'OIS'
        ctx.env.Append(LIBS = [oisLibName])
        ret = ctx.TryLink("""
            #include <OIS.h>
            int main(int argc, char** argv) {
                OIS::ParamList paramList;
                OIS::InputManager* input = OIS::InputManager::createInputSystem( paramList );
                return 0;
            }
            """, extension='.cpp')
        if ret:
            oisPackage = ctx.env.DeclarePackage(
                'ois',
                LIBS=[oisLibName],
                trigger_libs=['OIS', 'ois'])

        ctx.env.RestoreVars(savedVars)

    else:

        # on linux, search in some common locations
        for includeDir in ('', '/usr/include/OIS', '/usr/local/include/OIS'):
            ctx.env.Append(LIBS = ['OIS'])
            ctx.env.Append(CPPPATH = [includeDir])
            ret = ctx.TryLink("""
            #include <OIS.h>
            int main(int argc, char** argv) {
                OIS::ParamList paramList; 
                OIS::InputManager* input = OIS::InputManager::createInputSystem( paramList );
                return 0;
            }
            """, extension='.cpp')

            ctx.env.RestoreVars(savedVars)
            if ret:
                oisPackage = ctx.env.DeclarePackage(
                    'ois',
                    CPPPATH=[includeDir],
                    LIBS=['OIS'],
                    trigger_libs=['OIS', 'ois'])
                ctx.env.Replace(OIS_INCLUDES=[includeDir])
                break

    key = confprefix+'HAVE_OIS'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckOIS', CheckOIS)
RegisterCustomTest('CheckOISVersion_1_2', CheckOISVersion_1_2)

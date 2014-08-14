from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix

def CheckSpiderMonkey(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for Mozilla SpiderMonkey...')
    confprefix = getAutoconfPrefix(ctx.env)

    compiler = ctx.env['compiler']
    platform = ctx.env['PLATFORM']
    isWin32 = (platform == 'win32')

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS CCFLAGS')

    # FIXME: Detection should work independently of DevEnv
    # find SpiderMonkey relative to DevEnv
    SPIDERMONKEY_PATH = '../../js-1.8.0-rc1/src'
    SPIDERMONKEY_OBJ_PATH = SPIDERMONKEY_PATH + '/Linux_All_DBG.OBJ'

    smCCFLAGS = ['-DXP_UNIX']
    smLIBS =  ['js', 'm']
    #smCPPPATH = [SPIDERMONKEY_PATH, SPIDERMONKEY_OBJ_PATH]
    #smLIBPATH = [SPIDERMONKEY_OBJ_PATH]

    # add paths
    # TODO I think this should be a package
    ctx.env.Append(LIBS     = smLIBS)
    ctx.env.Append(CCFLAGS = smCCFLAGS)

    ret = ctx.TryLink("""
    #include <jsatom.h>

int main(int argc, char **argv) {
  JSString *jsString;
  JSAtom *jsAtom;
  return 0;
}
""", extension='.c')
    if ret:
        ctx.env.DeclarePackage('spidermonkey',
                               LIBS=smLIBS,
                               dependencies=[],
                               vars={'CCFLAGS' : smCCFLAGS},
                               trigger_libs=['spidermonkey', 'js'],
                               trigger_frameworks=['spidermonkey', 'js'])

    ctx.env.RestoreVars(savedVars)

    key = confprefix+'HAVE_SPIDERMONKEY'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckSpiderMonkey', CheckSpiderMonkey)

# Portions from midl.py tool from SCons distribution

from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix

import string
import os.path

import SCons.Action
import SCons.Builder
import SCons.Defaults
import SCons.Scanner.IDL
import SCons.Util
import SCons.Errors

def nmmidlEmitter(target, source, env):
    """Produces a list of outputs from the NMMIDL compiler"""

    headerSuffix = env['NMMHXXFILESUFFIX']
    sourceSuffix = env['NMMCXXFILESUFFIX']

    if len(source) > 1 and len(target) > 1:
        raise SCons.Errors.UserError, "multiple sources and targets are not supported"

    base, ext = SCons.Util.splitext(str(target[0]))

    hpp = target[0]
    cpp = base + sourceSuffix

    hpp_impl = base + 'Impl' + headerSuffix
    cpp_impl = base + 'Impl' + sourceSuffix

    t = [hpp, cpp, hpp_impl, cpp_impl]

    # Additional dependencies (*.in)

    src_hpp_in      = env.GetRealPath(str(hpp)) + '.in'
    src_cpp_in      = env.GetRealPath(str(cpp)) + '.in'
    src_hpp_impl_in = env.GetRealPath(str(hpp_impl)) + '.in'
    src_cpp_impl_in = env.GetRealPath(str(cpp_impl)) + '.in'

    hpp_in      = env.GetBuildPath(hpp) + '.in'
    cpp_in      = env.GetBuildPath(cpp) + '.in'
    hpp_impl_in = env.GetBuildPath(hpp_impl) + '.in'
    cpp_impl_in = env.GetBuildPath(cpp_impl) + '.in'

    s = []

    if os.path.exists(src_hpp_in):
        env.Depends(hpp, hpp_in)
        s.append(hpp_in)
        
    if os.path.exists(src_cpp_in):
        env.Depends(cpp, cpp_in)
        s.append(cpp_in)
        
    if os.path.exists(src_hpp_impl_in):
        env.Depends(hpp_impl, hpp_impl_in)
        s.append(hpp_impl_in)

    if os.path.exists(src_cpp_impl_in):
        env.Depends(cpp_impl, cpp_impl_in)
        s.append(cpp_impl_in)

    source.extend(s)

    return (t,source)

idlScanner = SCons.Scanner.IDL.IDLScan()

nmmihppAction = SCons.Action.Action('$NMMIHPPCOM', '$NMMIHPPCOMSTR')
nmmicppAction = SCons.Action.Action('$NMMICPPCOM', '$NMMICPPCOMSTR')
nmmihppimplAction = SCons.Action.Action('$NMMIHPPIMPLCOM',
                                         '$NMMIHPPIMPLCOMSTR')
nmmicppimplAction = SCons.Action.Action('$NMMICPPIMPLCOM',
                                         '$NMMICPPIMPLCOMSTR')

nmmidlAction = SCons.Action.Action([nmmihppAction,
                                    nmmicppAction,
                                    nmmihppimplAction,
                                    nmmicppimplAction])

nmmidlBuilder = SCons.Builder.Builder(action = nmmidlAction,
                                      src_suffix = '.idl',
                                      suffix='.hpp',
                                      emitter = nmmidlEmitter,
                                      source_scanner = idlScanner)

ihppBuilder = SCons.Builder.Builder(action = '$NMMIHPP $SOURCE > $TARGET',
                             suffix = '.hpp',
                             src_suffix = '.idl')

icppBuilder = SCons.Builder.Builder(action = '$NMMICPP $SOURCE > $TARGET',
                             suffix = '.cpp',
                             src_suffix = '.idl',
                             source_scanner = idlScanner)

ihppimplBuilder = SCons.Builder.Builder(action = '$NMMIHPPIMPL $SOURCE > $TARGET',
                                        suffix = '.hpp',
                                        src_suffix = '.idl',
                                        source_scanner = idlScanner)

icppimplBuilder = SCons.Builder.Builder(action = '$NMMICPPIMPL $SOURCE > $TARGET',
                                        suffix = '.cpp',
                                        src_suffix = '.idl',
                                        source_scanner = idlScanner)

def NMMIDL(env, *args, **kw):
    """Trigger idl builder, but only return cpp source files"""

    source = []
    
    if kw.has_key('source'):
        source = kw['source']
    elif args:
        if len(args) > 1:
            source = args[1]

    result = []
    for s in source:
        kw['source'] = [s]
        out = env.NMMIDLBuilder(**kw)

        # NOTE: instead of implicitly filter out anything but sources
        #       we explicitly will use FilterFiles function 
        #for i in out:
        #    if str(i)[-4:] in ('.cpp', '.cxx', '.C', '.cc'):
        #        result.append(i)

        result.extend(out)
        
    return result

def NMMPlugin(env, *args, **kw):
    platform = env['PLATFORM']
    if platform == 'darwin':
        # On Mac OS X NMM uses Linux suffixes and prefixes for bundles.
        # By default suffixes and prefixes are empty on Mac OS X.
        if not kw.has_key('LDMODULEPREFIX'):
            kw['LDMODULEPREFIX'] = 'lib'
        if not kw.has_key('LDMODULESUFFIX'):
            kw['LDMODULESUFFIX'] = '.so'
    return env.LoadableModule(*args, **kw)

def NMMInstallPlugin(env, target, source):
    """Installs one or more NMM plugins in a specified target, which
       must be a directory. Sources should be a NMM plugin libraries
       created previously"""

    suffixes = [ '.dll', '.so', env['SHLIBSUFFIX'], env['LDMODULESUFFIX'] ]
    def checkSuffixes(fn, *args, **kw):
        for s in suffixes:
            if fn.endswith(s):
                return True
        return False

    pluginLibs = env.FilterFiles(source, match_function=checkSuffixes)
    
    installedLibs = env.Install(target, pluginLibs)
    
    for lib in installedLibs:

        f = os.path.basename(lib.abspath)

        env.Command('$NMMDEVLIB/%s' % f,
                    lib,
                    ["ln -sf $SOURCE $TARGET"])

def generate(env):
    """Add Builders and construction variables for nmmidl to an Environment."""

    env['NMMHXXFILESUFFIX'] = '.hpp'
    env['NMMCXXFILESUFFIX'] = '.cpp'

    env['NMMIHPP']          = 'ihpp'
    env['NMMIHPPCOM']       = '$NMMIHPP $SOURCE > ${TARGETS[0]}'

    env['NMMICPP']          = 'icpp'
    env['NMMICPPCOM']       = '$NMMICPP $SOURCE > ${TARGETS[1]}'

    env['NMMIHPPIMPL']      = 'ihppimpl'
    env['NMMIHPPIMPLCOM']   = '$NMMIHPPIMPL $SOURCE > ${TARGETS[2]}'

    env['NMMICPPIMPL']      = 'icppimpl'
    env['NMMICPPIMPLCOM']   = '$NMMICPPIMPL $SOURCE > ${TARGETS[3]}'

    # NMMDEVLIB is a path to a dev-lib and is used by NMM to scan for plugins
    env['NMMDEVLIB'] = '$prefix/nmm/dev-lib'
    
    #env['NMMIDLFLAGS']      = SCons.Util.CLVar('')

    env['BUILDERS']['NMMIDLBuilder'] = nmmidlBuilder
    env['BUILDERS']['NMMIDL'] = NMMIDL

    env.AddMethod(NMMPlugin, 'NMMPlugin')
    env.AddMethod(NMMInstallPlugin, 'NMMInstallPlugin')
    
    # Create simple builders to build hpp and cpp files from idl files
    
    env['BUILDERS']['Ihpp'] = ihppBuilder
    env['BUILDERS']['Icpp'] = icppBuilder
    env['BUILDERS']['IhppImpl'] = ihppimplBuilder
    env['BUILDERS']['IcppImpl'] = icppimplBuilder


def exists(env):
    return env.Detect('ihpp') and \
           env.Detect('icpp') and \
           env.Detect('ihppimpl') and \
           env.Detect('icppimpl')

def CheckNMM(ctx, write_config_h=False, add_to_compiler_env=False,
             idl_compiler_required=True):
    ctx.Message('Checking for NMM... ')
    confprefix = getAutoconfPrefix(ctx.env)
    
    platform = ctx.env['PLATFORM']
    lastLIBS = list(ctx.env.get('LIBS', []))

    ret = False

    for nmmlib in ('nmmthread nmmutils',):
        ctx.env.Append(LIBS = ctx.env.Split(nmmlib))
        ret = ctx.TryLink("""
    #include <nmm/utils/thread/Thread.hpp>
    int main(int argc, char **argv) {
      NMM::Thread thread;
      return 0;
    }
""", extension='.cpp')
        ctx.env.Replace(LIBS = lastLIBS)
        if ret:
            break

    nmm_defines = []

    if ret:
        # modify configuration environment
        ctx.env.Replace(LIBNMM_THREAD=['nmmthread'])
        ctx.env.Replace(LIBNMM_UTILS=['nmmutils'])
        ctx.env.Replace(LIBNMM_COMM=['nmmcomm'])
        ctx.env.Replace(LIBNMM_FORK=['nmmfork'])
        ctx.env.Replace(LIBNMM_FORMAT=['nmmformat'])
        ctx.env.Replace(LIBNMM_MULTIMEDIA=['nmmmultimedia'])
        ctx.env.Replace(LIBNMM_XML=['nmmxml'])

        # simulate config.h
        if ctx.env['PLATFORM'] == 'posix':
            nmm_defines = ['BUILD_LINUX']
        elif ctx.env['PLATFORM'] == 'win32':
            nmm_defines = ['BUILD_WIN32']
        elif ctx.env['PLATFORM'] == 'darwin':
            nmm_defines = ['BUILD_MACOSX', 'BUILD_LINUX']
        else:
            print "Warning: Unknown Platform"

        #ctx.env.Append(CPPDEFINES='HAVE_CONFIG_H')

        # setup NMM IDL compiler
        if exists(ctx.env):
            generate(ctx.env)
            ctx.env.Replace(HAVE_NMMIDL=1)
        else:
            ctx.Message('NMM IDL compiler not found')
            if idl_compiler_required:
                ret = False
            ctx.env.Replace(HAVE_NMMIDL=0)

    nmm_defines = nmm_defines + [confprefix+'HAVE_LIBNMM']

    nmm_libs = ctx.env.Split("""
        nmmfileinterfaces
        nmmaudiointerfaces
        nmmpluginsinterfaces
        nmmxml
        xml2
        nmmmultimedia
        nmmregistry
        nmmutils
        nmmthread
        nmmformat
        nmmsyncinterfaces
        nmmcomm
        nmmserialize
        nmmmessaging
        nmmdisplayinterfaces
        nmmsync
        nmmaudiointerfaces
        nmmtime
        nmmnet
        nmmpluginsinterfaces
        nmmproc
        nmmmultimediainterfaces
        nmmifilter
        nmmproc
        nmmnetstrategy
        nmmgdparse
        """)

    ctx.env.DeclarePackage( 'nmm', LIBS=nmm_libs, CPPDEFINES=nmm_defines,
                            trigger_libs=['NMM'] )
    
    if not (write_config_h and AddConfigKey(ctx, nmm_defines, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=nmm_defines)

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckNMM', CheckNMM)

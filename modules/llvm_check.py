import os
from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.btools import runCommand
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import Version
import re

import SCons.Scanner
import SCons.Action

def LLVM_CScanner():
    cs = SCons.Scanner.ClassicCPP(
        "LLVMCScanner",
        "$CPPSUFFIXES",
        "LLVM_CPPPATH",
        '^[ \t]*#[ \t]*(?:include|import)[ \t]*(<|")([^>"]+)(>|")')
    return cs

llvmCScanner = LLVM_CScanner()

def createLLVMBitCodeBuilder(env):
    try:
        llvmBitCode = env['BUILDERS']['LLVMBitCode']
    except KeyError:
        llvmBitCode = SCons.Builder.Builder(action = {},
                                            emitter = {},
                                            prefix = '',
                                            suffix = '.bc',
                                            src_builder = ['CFile', 'CXXFile'],
                                            source_scanner = llvmCScanner,
                                            single_source = 1)
        env['BUILDERS']['LLVMBitCode'] = llvmBitCode
        return llvmBitCode

def createLLVMLinkBuilder(env):
    try:
        llvmLink = env['BUILDERS']['LLVMLink']
    except KeyError:
        llvmLinkAction = SCons.Action.Action(
            "$LLVM_LINKCOM", "$LLVM_LINKCOMSTR")
        llvmLink = SCons.Builder.Builder(
            action = {'.bc' : llvmLinkAction},
            emitter = {},
            prefix = '',
            suffix = '.bc',
            src_builder = ['LLVMBitCode'],
            single_source = 0)
        env['BUILDERS']['LLVMLink'] = llvmLink
        return llvmLink

def createLLVMOptBuilder(env):
    try:
        llvmOpt = env['BUILDERS']['LLVMOpt']
    except KeyError:
        llvmOptAction = SCons.Action.Action("$LLVM_OPTCOM", "$LLVM_OPTCOMSTR")
        llvmOpt = SCons.Builder.Builder(action = {'.bc' : llvmOptAction},
                                        emitter = {},
                                        prefix = '',
                                        suffix = '.bc',
                                        src_builder = ['LLVMBitCode', 'LLVMAssembler'],
                                        single_source = 1)
        env['BUILDERS']['LLVMOpt'] = llvmOpt
        return llvmOpt

def createLLVMAssemblerBuilder(env):
    try:
        llvmAssembler = env['BUILDERS']['LLVMAssembler']
    except KeyError:
        llvmAssemblerAction = SCons.Action.Action("$LLVM_ASCOM", "$LLVM_ASCOMSTR")
        llvmAssembler = SCons.Builder.Builder(action = {'.ll' : llvmAssemblerAction},
                                        emitter = {},
                                        prefix = '',
                                        suffix = '.bc',
                                        #src_builder = [],
                                        single_source = 1)
        env['BUILDERS']['LLVMAssembler'] = llvmAssembler
        return llvmAssembler

llvmCXXAction = SCons.Action.Action("$LLVM_CXXCOM", "$LLVM_CXXCOMSTR")
llvmCAction = SCons.Action.Action("$LLVM_CCCOM", "$LLVM_CCCOMSTR")

def generate(env, use_clang=False):
    """Add Builders and construction variables for LLVM tools to an Environment."""
    # LLVM_CXX for LLVMBitCode tool

    if use_clang:
        env['LLVM_CXX'] = 'clang++'
        env['LLVM_CC'] = 'clang'
    else:
        env['LLVM_CXX'] = 'llvm-g++'
        env['LLVM_CC'] = 'llvm-gcc'

    env['LLVM_INCPREFIX'] = '-I'
    env['LLVM_INCSUFFIX'] = ''
    env['LLVM_CPPDEFPREFIX'] = '-D'
    env['LLVM_CPPDEFSUFFIX'] = ''
    env['_LLVM_CPPDEFFLAGS'] = '${_defines(LLVM_CPPDEFPREFIX, LLVM_CPPDEFINES, LLVM_CPPDEFSUFFIX, __env__)}'
    env['_LLVM_CPPINCFLAGS'] = '$( ${_concat(LLVM_INCPREFIX, LLVM_CPPPATH, LLVM_INCSUFFIX, __env__, RDirs, TARGET, SOURCE)} $)'
    env['_LLVM_CCCOMCOM'] = '$LLVM_CPPFLAGS $_LLVM_CPPDEFFLAGS $_LLVM_CPPINCFLAGS'
    env['LLVM_CXXCOM'] = '$LLVM_CXX -o $TARGET -c $LLVM_CXXFLAGS $LLVM_CCFLAGS $_LLVM_CCCOMCOM $SOURCES'
    env['LLVM_CCCOM']  = '$LLVM_CC -o $TARGET -c $LLVM_CFLAGS $LLVM_CCFLAGS $_LLVM_CCCOMCOM $SOURCES'
    env['LLVM_CCFLAGS'] = ['-emit-llvm']
    env['LLVM_CXXFLAGS'] = []
    env['LLVM_CPPDEFINES'] = []
    env['LLVM_CPPPATH'] = []

    # LLVM_LINK for LLVMLink tool

    env['LLVM_LINK'] = 'llvm-link'
    env['LLVM_LINKCOM'] = '$LLVM_LINK -f -o $TARGET $SOURCES $LLVM_LINKFLAGS'
    env['LLVM_LINKFLAGS'] = []

    # setup LLVM_OPT for LLVMOpt tool

    env['LLVM_OPT'] = 'opt'
    env['LLVM_OPTCOM'] = '$LLVM_OPT -f -o $TARGET $SOURCES $LLVM_OPTFLAGS'
    env['LLVM_OPTFLAGS'] = []

    # LLVM_AS for LLVMAssembler tool
    env['LLVM_AS'] = 'llvm-as'
    env['LLVM_ASCOM'] = '$LLVM_AS -f -o $TARGET $SOURCES $LLVM_ASFLAGS'
    env['LLVM_ASFLAGS'] = []

    CSuffixes = ['.c', '.m']
    CXXSuffixes = ['.cpp', '.cc', '.cxx', '.c++', '.C++', '.mm']

    llvmBitCodeBuilder = createLLVMBitCodeBuilder(env)

    for suffix in CSuffixes:
        llvmBitCodeBuilder.add_action(suffix, llvmCAction)

    for suffix in CXXSuffixes:
        llvmBitCodeBuilder.add_action(suffix, llvmCXXAction)

    createLLVMLinkBuilder(env)
    createLLVMOptBuilder(env)
    createLLVMAssemblerBuilder(env)

def exists(env):
    return ((env.Detect('llvm-gcc') and env.Detect('llvm-g++')) or \
            (env.Detect('clang') and env.Detect('clang++'))) and \
             env.Detect('llvm-link') and \
             env.Detect('opt') and \
             env.Detect('llvm-as')

def CheckLLVM(ctx, write_config_h=True, add_to_cppdefines=False,
              llvm_tools_required=True, use_clang_if_available=False,
              min_version=None, max_version=None):
    ctx.Message('Checking for LLVM library... ')
    confprefix = getAutoconfPrefix(ctx.env)
    platform = ctx.env['PLATFORM']

    if platform == 'win32':
        savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS')

        llvmlibs = ['LLVMJIT.lib',
                    'LLVMCodeGen.lib',
                    'LLVMCore.lib',
                    'LLVMSupport.lib',
                    'LLVMTarget.lib',
                    'LLVMInterpreter.lib',
                    'LLVMExecutionEngine.lib',
                    'LLVMX86CodeGen.lib',
                    'LLVMSelectionDAG.lib',
                    'LLVMAnalysis.lib',
                    'LLVMScalarOpts.lib',
                    'LLVMTransformUtils.lib',
                    'LLVMipa.lib',
                    'LLVMAsmPrinter.lib',
                    'LLVMBitReader.lib',
                    'LLVMBitWriter.lib',
                    'LLVMInstrumentation.lib',
                    'LLVMipo.lib',
                    'LLVMLinker.lib',
                    'LLVMX86AsmPrinter.lib',
                    'LLVMAsmParser.lib',
                    'LLVMArchive.lib',
                    'LLVMX86Info.lib',
                    'LLVMInstCombine.lib',
                    'Shell32.lib',
                    'Advapi32.lib',
                    'LLVMX86Utils.lib',
                    'LLVMMC.lib']
        #llvmlibs = ['LLVMSystem']

        ctx.env.Append(LIBS = llvmlibs)
        ret = ctx.TryLink("""
            #include <llvm/Config/llvm-config.h>
            #if (LLVM_VERSION_MAJOR >= 3 && LLVM_VERSION_MINOR >= 3)
            #include <llvm/IR/Module.h>
            #include <llvm/IR/LLVMContext.h>
            #else
            #include <llvm/Module.h>
            #include <llvm/LLVMContext.h>
            #endif

            int main(int argc, char **argv)
            {
                llvm::Module *module = new llvm::Module("test", llvm::getGlobalContext());
                return 0;
            }
            """, extension='.cpp')

        ctx.env.RestoreVars(savedVars)

        if ret:
            ctx.env.DeclarePackage('llvm',
                                   trigger_libs=['LLVM'],
                                   trigger_frameworks=['LLVM'],
                                   LLVM_VERSION=None,
                                   LLVM_VERSION_SUFFIX=None,
                                   LIBS = llvmlibs)
            ctx.env.Replace(LIBLLVM = llvmlibs)

    else:
        ret, output = ctx.TryAction('llvm-config --version')
        if ret:

            vars = ctx.env.ParseFlags('!llvm-config --cflags --libs && llvm-config --ldflags')

            # filter out -fomit-frame-pointer and -O3
            vars['CCFLAGS'] = [k for k in vars['CCFLAGS']              \
                               if k not in ('-fomit-frame-pointer',    \
                                            '-O', '-O1', '-O2', '-O3')]

            # Save cxxflags configuration
            vars['LLVM_CONFIG_CXXFLAGS'] = ctx.env.ParseFlags('!llvm-config --cxxflags')

            ctx.env.DeclarePackage('llvm', vars=vars,
                                   trigger_libs=['LLVM'],
                                   trigger_frameworks=['LLVM'],
                                   LLVM_VERSION=None,
                                   LLVM_VERSION_SUFFIX=None)

            ctx.env.Append(CPPPATH = vars.get('CPPPATH'))
            ctx.env.Append(LIBPATH = vars.get('LIBPATH'))
            ctx.env.Replace(LIBLLVM = vars.get('LIBS'))

    # check availability of the internal debug flag
    if ret:
        savedVars = ctx.env.RequirePackage('llvm')

        hasDebugFlag = ctx.TryLink("""
            #undef NDEBUG
            #include <llvm/Support/Debug.h>

            int main(int argc, char **argv)
            {
                llvm::DebugFlag = true;
                return 0;
            }
            """, extension='.cpp')

        ctx.env.RestoreVars(savedVars)
        ctx.env.Replace(LLVM_HAS_DEBUGFLAG=hasDebugFlag)
    else:
        ctx.env.Replace(LLVM_HAS_DEBUGFLAG=0)

    # try to get version
    if ret:
        savedVars = ctx.env.RequirePackage('llvm')

        ret1, outputStr = ctx.TryRun("""
            #include <llvm/Config/config.h>
            #include <cstdio>

            int main(int argc, char **argv)
            {
                printf("%s\\n", PACKAGE_VERSION);
                return 0;
            }
            """, extension='.cpp')

        ctx.env.RestoreVars(savedVars)

        LLVM_PACKAGE_VERSION = outputStr.strip()
    else:
        LLVM_PACKAGE_VERSION = None

    ctx.env.Replace(LLVM_PACKAGE_VERSION=LLVM_PACKAGE_VERSION)

    # Split llvm package version into numeric part and suffix
    LLVM_VERSION = None
    LLVM_VERSION_SUFFIX = None
    if LLVM_PACKAGE_VERSION is not None:
        ctx.Message('version %s ' % LLVM_PACKAGE_VERSION)
        m = re.search(r'([0-9]+(?:\.(?:[0-9]+))*)(.*)', LLVM_PACKAGE_VERSION)
        if m:
            LLVM_VERSION = Version(m.group(1))
            LLVM_VERSION_SUFFIX = m.group(2)

    if ret and (min_version is not None or max_version is not None):
        if LLVM_VERSION:
            if not LLVM_VERSION.compatible(min_version, max_version):
                ctx.Message(
                    'version %s is not within required [%s, %s] version range '\
                        % (LLVM_VERSION, min_version, max_version))
                ret = False
        else:
            ctx.Message(
                'could not detect LLVM version, required version is [%s, %s]'\
                    % (min_version, max_version))
            ctx.env.RemovePackage('llvm')
            ret = False

    if ret and LLVM_PACKAGE_VERSION:
        llvmpkg = ctx.env.GetPackage('llvm')

        # try shared library variant
        savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS CCFLAGS CFLAGS CPPDEFINES')

        llvmlibs = ['LLVM-'+LLVM_PACKAGE_VERSION]
        vars = {}
        for k in ('CCFLAGS', 'CFLAGS', 'CPPDEFINES'):
            if( k in llvmpkg.vars ):
                value = llvmpkg.vars[k]
                vars[k] = value
        llvmpkg.vars['LLVM_VERSION'] = LLVM_VERSION
        llvmpkg.vars['LLVM_VERSION_SUFFIX'] = LLVM_VERSION_SUFFIX
        ctx.env.Append(LIBS = llvmlibs)
        ctx.env.Append(**vars)
        dyn_ret = ctx.TryLink("""
            #include <llvm/Config/llvm-config.h>
            #if (LLVM_VERSION_MAJOR >= 3 && LLVM_VERSION_MINOR >= 3)
            #include <llvm/IR/Module.h>
            #include <llvm/IR/LLVMContext.h>
            #else
            #include <llvm/Module.h>
            #include <llvm/LLVMContext.h>
            #endif

            int main(int argc, char **argv)
            {
                llvm::Module *module = new llvm::Module("test", llvm::getGlobalContext());
                return 0;
            }
            """, extension='.cpp')

        ctx.env.RestoreVars(savedVars)

        if platform == 'win32':
            if LLVM_VERSION >= Version(3, 0):
                libs = ['LLVMMCDisassembler.lib',
                        'LLVMX86Desc.lib',
                        'LLVMX86AsmParser.lib',
                        'LLVMMCParser.lib']
                llvmpkg.vars['LIBS'].extend(libs)
            if LLVM_VERSION >= Version(3, 1):
                libs = ['LLVMMCJIT.lib',
                        'LLVMRuntimeDyld.lib',
                        'LLVMObject.lib',
                        'LLVMVectorize.lib']
                llvmpkg.vars['LIBS'].extend(libs)
            if LLVM_VERSION >= Version(3, 3):
                libs = ['LLVMIRReader.lib',
                        'LLVMObjCARCOpts.lib',
                        'LLVMXCoreAsmPrinter.lib',
                        'LLVMXCoreCodeGen.lib',
                        'LLVMXCoreDesc.lib',
                        'LLVMXCoreDisassembler.lib',
                        'LLVMXCoreInfo.lib',
                        'LLVMSystemZAsmParser.lib',
                        'LLVMSystemZAsmPrinter.lib',
                        'LLVMSystemZCodeGen.lib',
                        'LLVMSystemZDesc.lib',
                        'LLVMSystemZInfo.lib',
                        'LLVMSparcCodeGen.lib',
                        'LLVMSparcDesc.lib',
                        'LLVMSparcInfo.lib',
                        'LLVMPowerPCAsmParser.lib',
                        'LLVMPowerPCAsmPrinter.lib',
                        'LLVMPowerPCCodeGen.lib',
                        'LLVMPowerPCDesc.lib',
                        'LLVMPowerPCInfo.lib',
                        'LLVMNVPTXAsmPrinter.lib',
                        'LLVMNVPTXCodeGen.lib',
                        'LLVMNVPTXDesc.lib',
                        'LLVMNVPTXInfo.lib',
                        'LLVMMSP430AsmPrinter.lib',
                        'LLVMMSP430CodeGen.lib',
                        'LLVMMSP430Desc.lib',
                        'LLVMMSP430Info.lib',
                        'LLVMMBlazeAsmParser.lib',
                        'LLVMMBlazeAsmPrinter.lib',
                        'LLVMMBlazeCodeGen.lib',
                        'LLVMMBlazeDesc.lib',
                        'LLVMMBlazeDisassembler.lib',
                        'LLVMMBlazeInfo.lib',
                        'LLVMMipsAsmParser.lib',
                        'LLVMMipsAsmPrinter.lib',
                        'LLVMMipsCodeGen.lib',
                        'LLVMMipsDesc.lib',
                        'LLVMMipsDisassembler.lib',
                        'LLVMMipsInfo.lib',
                        'LLVMHexagonAsmPrinter.lib',
                        'LLVMHexagonCodeGen.lib',
                        'LLVMHexagonDesc.lib',
                        'LLVMHexagonInfo.lib',
                        'LLVMCppBackendCodeGen.lib',
                        'LLVMCppBackendInfo.lib',
                        'LLVMARMAsmParser.lib',
                        'LLVMARMAsmPrinter.lib',
                        'LLVMARMCodeGen.lib',
                        'LLVMARMDesc.lib',
                        'LLVMARMDisassembler.lib',
                        'LLVMARMInfo.lib',
                        'LLVMAArch64AsmParser.lib',
                        'LLVMAArch64AsmPrinter.lib',
                        'LLVMAArch64CodeGen.lib',
                        'LLVMAArch64Desc.lib',
                        'LLVMAArch64Disassembler.lib',
                        'LLVMAArch64Info.lib',
                        'LLVMAArch64Utils.lib']
                llvmpkg.vars['LIBS'].extend(libs)

        if dyn_ret:
            ctx.env.DeclarePackage('llvm_shared', vars=vars,
                                   trigger_libs=['LLVM_shared'],
                                   trigger_frameworks=['LLVM_shared'],
                                   LIBS = llvmlibs)
            ctx.env.Replace(LIBLLVM_SHARED = llvmlibs)

    # Try to setup LLVM tools
    if ret:
        if exists(ctx.env):
            have_clang = ctx.env.Detect('clang') and ctx.env.Detect('clang++')
            have_llvm_gcc = ctx.env.Detect('llvm-gcc') and ctx.env.Detect('llvm-g++')

            generate(ctx.env, use_clang=have_clang and use_clang_if_available)

            ctx.env.Replace(HAVE_LLVMTOOLS=1)
            if have_clang:
                ctx.env.Replace(HAVE_CLANG_COMPILER=1)
            else:
                ctx.env.Replace(HAVE_CLANG_COMPILER=0)
            if have_llvm_gcc:
                ctx.env.Replace(HAVE_LLVM_GCC_COMPILER=1)
            else:
                ctx.env.Replace(HAVE_LLVM_GCC_COMPILER=0)
        else:
            ctx.Message('LLVM tools (llvm-gcc, llvm-g++, clang, clang++, llvm-link, opt) not found')
            if llvm_tools_required:
                ret = False
            ctx.env.Replace(HAVE_LLVMTOOLS=0)

    key = confprefix+'HAVE_LIBLLVM'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_cppdefines:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckLLVM', CheckLLVM)

from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.butils import Version

def CheckClang(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for Clang... ')
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_CLANG'

    platform = ctx.env['PLATFORM']

    # If LLVM is not available Clang cannot be used as it linked statically
    # and do not contain any LLVM symbols
    llvmpkg = ctx.env.GetPackage('llvm')
    if not llvmpkg:
        ctx.Message('No LLVM detected')
        if write_config_h:
            AddConfigKey(ctx, key, 0)
        ctx.Result(0)
        return 0

    LLVM_VERSION = llvmpkg.vars['LLVM_VERSION']
    LLVM_VERSION_SUFFIX = llvmpkg.vars['LLVM_VERSION_SUFFIX']

    if LLVM_VERSION is not None and LLVM_VERSION >= Version(3, 3):
        clanglibs = ctx.env.Split("""
        clangFrontendTool
        clangFrontend
        clangDriver
        clangSerialization
        clangCodeGen
        clangParse
        clangSema
        clangStaticAnalyzerFrontend
        clangStaticAnalyzerCheckers
        clangStaticAnalyzerCore
        clangAnalysis
        clangARCMigrate
        clangRewriteCore
        clangRewriteFrontend
        clangAST
        clangASTMatchers
        clangBasic
        clangEdit
        clangLex
        clangTooling
        clangFormat
        """)
    elif LLVM_VERSION is not None and LLVM_VERSION >= Version(3, 1):
        clanglibs = ctx.env.Split("""
        clangFrontendTool
        clangFrontend
        clangDriver
        clangSerialization
        clangCodeGen
        clangParse
        clangSema
        clangStaticAnalyzerFrontend
        clangStaticAnalyzerCheckers
        clangStaticAnalyzerCore
        clangAnalysis
        clangARCMigrate
        clangRewrite
        clangAST
        clangLex
        clangBasic
        clangEdit
        clangTooling
        """)
    elif LLVM_VERSION is not None and LLVM_VERSION >= Version(3, 0):
        clanglibs = ctx.env.Split("""
        clangFrontendTool
        clangFrontend
        clangDriver
        clangSerialization
        clangCodeGen
        clangParse
        clangSema
        clangStaticAnalyzerFrontend
        clangStaticAnalyzerCheckers
        clangStaticAnalyzerCore
        clangAnalysis
        clangIndex
        clangARCMigrate
        clangRewrite
        clangAST
        clangLex
        clangBasic
        """)
    elif LLVM_VERSION is not None and LLVM_VERSION >= Version(2, 9):
        clanglibs = ctx.env.Split("""
        clangFrontend
        clangDriver
        clangCodeGen
        clangSema
        clangAnalysis
        clangRewrite
        clangAST
        clangParse
        clangLex
        clangBasic
        clangFrontendTool
        clangIndex
        clangSerialization
        clangStaticAnalyzerCheckers
        clangStaticAnalyzerCore
        clangStaticAnalyzerFrontend
        """)
    else:
        clanglibs = ctx.env.Split("""
        clangFrontend
        clangDriver
        clangCodeGen
        clangSema
        clangChecker
        clangAnalysis
        clangRewrite
        clangAST
        clangParse
        clangLex
        clangBasic
        """)

    # Note: order of adding to LIBS variable is important for static
    # libraries, Clang library need to be added before LLVM so
    # LLVM symbols not found in Clang library will be found in the
    # LLVM library after it.
    ctx.env.Append(LIBS = clanglibs)
    # RequirePackage('llvm') will add all libraries needed for linking with
    # LLVM and return dictionary of all modified variables with original
    # values.
    savedVars = ctx.env.RequirePackage('llvm')

    ret = ctx.TryLink("""
#include <clang/Driver/Driver.h>
#include <clang/Frontend/CompilerInstance.h>
int main(int argc, char **argv)
{
    clang::CompilerInstance Clang;
    return 0;
}
""", extension='.cpp')

    ctx.env.RestoreVars(savedVars)

    if ret:
        # Detect location of clang library, required for proper
        # initialization of the compiler.
        # When detected it is stored in COMPILER_LIB_DIR package variable.
        # Then path to clang include files is :
        # COMPILER_LIB_DIR/CLANG_VERSION_STRING/include where
        # CLANG_VERSION_STRING is a macro defined in
        # clang/Basic/Version.h header file.

        # perform substitution on LIBPATH, and return
        # as a list of strings
        clangDir = None
        for p in ctx.env.subst("$LIBPATH", conv=lambda x: x):
            # try to get "clang" subdirectory
            d = ctx.env.Glob(p+"/clang")
            if d:
                clangDir = d[0]

        ctx.env.DeclarePackage('clang',
                               vars={'LIBS' : clanglibs,
                                     'CPPDEFINES' : confprefix+'HAVE_CLANG',
                                     'COMPILER_LIB_DIR' : clangDir},
                               dependencies='llvm',
                               trigger_libs=['clang', 'Clang'],
                               trigger_frameworks=['Clang'])

    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckClang', CheckClang)

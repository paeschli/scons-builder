import os
from builder.btools import RegisterCustomTest

def CheckOpenRT(ctx):
    ctx.Message('Checking for OpenRT library... ')
    platform = ctx.env['PLATFORM']
    compiler = ctx.env['compiler']
    ROOT_DIR = ctx.env.GetRootDir()
    OPENRT_DIST_DIR = ctx.env.GetEnvVar('OPENRT_DIST_DIR')

    if OPENRT_DIST_DIR:
        openrtIncPath = os.path.join(OPENRT_DIST_DIR, 'include')
        openrtLibPath = os.path.join(OPENRT_DIST_DIR, 'lib')
        rtutLibPath = os.path.join(OPENRT_DIST_DIR, 'RTUT')
        if platform == 'win32':
            if compiler == 'GCC':
                openrtLib = ['OpenRT']
                rtutLib = ['rtut']
            else:
                openrtLib = ['libOpenRT']
                rtutLib = ['librtut']

            haveOpenRT = os.path.exists(os.path.join(openrtLibPath, 'libOpenRT.lib')) and os.path.exists(os.path.join(openrtLibPath, 'libOpenRT.dll'))
            haveRTUT = os.path.exists(os.path.join(rtutLibPath, 'librtut.lib')) and os.path.exists(os.path.join(openrtLibPath, 'librtut.dll'))
        else:
            openrtLib = ['OpenRT']
            rtutLib = ['rtut']

            haveOpenRT = os.path.exists(os.path.join(openrtLibPath, 'libOpenRT.so'))
            haveRTUT = os.path.exists(os.path.join(openrtLibPath, 'librtut.so'))
        if not haveOpenRT:
            ret = 0
        else:
            ret = 1
            ctx.env.Replace(OPENRT_LIB_DIR=os.path.abspath(openrtLibPath))
            ctx.env.Replace(OPENRT_INCLUDE_DIR=os.path.abspath(openrtIncPath))
            ctx.env.Replace(LIBOPENRT=openrtLib)

            ctx.env.DeclarePackage('openrt',
                                   CPPPATH=[os.path.abspath(openrtIncPath)],
                                   LIBPATH=[os.path.abspath(openrtLibPath)],
                                   LIBS=openrtLib,
                                   trigger_libs=['OpenRT']+openrtLib)
            
            if not haveRTUT:
                ctx.Message('Warning: could not find RTUT library. ')
                ctx.env.Replace(HAVE_RTUT=0)
            else:
                ctx.env.Replace(HAVE_RTUT=1)
                ctx.env.Replace(RTUT_LIB_DIR=os.path.abspath(rtutLibPath))
                ctx.env.Replace(LIBRTUT=rtutLib)

                ctx.env.DeclarePackage('rtut',
                                       dependencies='openrt',
                                       LIBPATH=[os.path.abspath(rtutLibPath)],
                                       LIBS=rtutLib,
                                       trigger_libs=['RTUT', 'rtut']+rtutLib)
    else:
        ctx.Message('Warning: could not find OpenRT library, you need to define OPENRT_DIST_DIR environment variable. ')
        ret = 0

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckOpenRT', CheckOpenRT)

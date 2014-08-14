# SCons Builder Engine Configuration V2.20

# Configuration
from btools import *
from butils import *
import sys
import os
import os.path
import getpass
import re
from string import split
import struct
import SCons.Util

# Utilities

def loadModules(modulesPath):
    modules = []
    if os.path.exists(modulesPath):
        # list all "modules/*.py" files
        modules = [ p[:-3] for p in os.listdir(modulesPath) \
                    if len(p) > 0 and p[0].isalpha() and p.endswith('.py') ]
    oldSysPath = sys.path
    sys.path = [modulesPath] + sys.path
    print '* Loading configuration modules:',
    for m in modules:
        try:
            mod = __import__(m)
            print m,
        except Exception, e:
            print '\n'
            print 'Error: Loading of module %s failed !' % m
            import traceback
            print '-'*60
            traceback.print_exc(file=sys.stdout)
            print '-'*60
            raise e
    sys.path = oldSysPath
    print '.'

def getProjectPrefix(env):
    return env.get('PROJECT_PREFIX', '_')

def getProjectSystemPrefix(env):
    return getProjectPrefix(env)+env.get('SYSTEM_PREFIX','')
    
def getProjectCompilerPrefix(env):
    return getProjectPrefix(env)+env.get('COMPILER_PREFIX','')

def getAutoconfPrefix(env):
    return env.get('AUTOCONF_PREFIX','')

# Architecture Info

# Architecture ID
ARCH_UNKNOWN  = 0
ARCH_X86      = 1
ARCH_X86_64   = 2
ARCH_IA64     = 3
ARCH_ARM      = 4

# CPU ID
CPU_GENERIC   = 0 # generic CPU of a given architecture
CPU_NATIVE    = 1 # optimize for CPU of the compiling machine
CPU_PENTIUM_3 = 2 # PentiumIII
CPU_PENTIUM_4 = 3 # PentiumIV
CPU_PENTIUM_M = 4 # PentiumM
CPU_OPTERON   = 5 # AMD Opteron
CPU_CORE      = 6 # Intel Core
CPU_CORE_2    = 7 # Intel Core 2
CPU_ITANIUM   = 8 # Intel Itanium   (ia64 architecture)
CPU_ITANIUM_2 = 9 # Intel Itanium 2 (ia64 architecture)

# Architecture database

# Architecture tuples :
# (arch_id, cpu_id_list)
ARCH_X86_DATA    = (ARCH_X86,
                    [CPU_GENERIC, CPU_NATIVE, CPU_PENTIUM_3, CPU_PENTIUM_4,
                     CPU_PENTIUM_M, CPU_OPTERON, CPU_CORE, CPU_CORE_2
                     ])

ARCH_X86_64_DATA = (ARCH_X86_64,
                    [CPU_GENERIC, CPU_NATIVE, CPU_OPTERON, CPU_CORE, CPU_CORE_2
                     ])

ARCH_IA64_DATA   = (ARCH_IA64,
                    [CPU_GENERIC, CPU_NATIVE, CPU_ITANIUM, CPU_ITANIUM_2
                     ])

ARCH_ARM_DATA = (ARCH_ARM,
                 [CPU_GENERIC, CPU_NATIVE
                  ])

ARCH_NAME_LIST = ['x86', 'x86_64', 'ia64', 'arm']

ARCH_NAME_TO_ID = {'x86' : ARCH_X86,
                   'x86_64' : ARCH_X86_64,
                   'ia64' : ARCH_IA64,
                   'arm'  : ARCH_ARM
                   }

# ARCH_ALIASES maps arch name to all aliases
ARCH_ALIASES = {'x86' : ['i386', 'i586', 'i686'],
                'x86_64' : ['amd64', 'emt64'],
                'ia64' : ['Itanium'],
                'arm'  : ['arm', 'armv1l', 'armv2l', 'armv3l', 'armv4l', 'armv5l', 'armv6l', 'armv7l']
                }

# add aliases to ARCH_NAME_TO_ID
for archName, aliases in ARCH_ALIASES.items():
    archID = ARCH_NAME_TO_ID[archName]
    for aliasName in aliases:
        ARCH_NAME_TO_ID[aliasName] = archID

ARCH_ID_TO_DATA = {ARCH_X86 : ARCH_X86_DATA,
                   ARCH_X86_64 : ARCH_X86_64_DATA,
                   ARCH_IA64 : ARCH_IA64_DATA,
                   ARCH_ARM : ARCH_ARM_DATA}

# CPU database

CPU_NAME_LIST = ['generic', 'native', 'PentiumIII', 'PentiumIV', 'PentiumM',
                 'Opteron', 'Core', 'Core2', 'Itanium', 'Itanium2']

CPU_NAME_TO_ID = {'generic' : CPU_GENERIC,
                  'native' : CPU_NATIVE,
                  'PentiumIII' : CPU_PENTIUM_3,
                  'PentiumIV' : CPU_PENTIUM_4,
                  'PentiumM' : CPU_PENTIUM_M,
                  'Opteron' : CPU_OPTERON,
                  'Core' : CPU_CORE,
                  'Core2' : CPU_CORE_2,
                  'Itanium' : CPU_ITANIUM,
                  'Itanium2' : CPU_ITANIUM_2
                  }

class ArchInfo:

    def __init__(self, env):
        arch = env['arch']
        cpu = env['cpu']

        try:
            self.arch = ARCH_NAME_TO_ID[arch]
        except KeyError:
            raise RuntimeError('Unknown architecture name: %s' % arch)
        try:
            self.cpu = CPU_NAME_TO_ID[cpu]
        except KeyError:
            raise RuntimeError('Unknown CPU name: %s' % cpu)

        # validate architecture/CPU combination
        archData = ARCH_ID_TO_DATA[self.arch]

        assert archData[0] == self.arch

        if self.cpu not in archData[1]:
            raise RuntimeErrror('%s/%s architecture/CPU combination is not supported' % (arch, cpu))

    def getArchID(self):
        return self.arch

    def getCpuID(self):
        return self.cpu

def getArchInfo(env):
    archInfo = env.get('SB_ARCH_INFO', None)
    if not archInfo:
        archInfo = ArchInfo(env)
        env.Replace(SB_ARCH_INFO=archInfo)
    return archInfo

# MSVC specific info

class MSVCInfo:

    def __init__(self, env):
        self.update(env)

    def update(self, env):
        self.debugRTL = False
        self.dynamicRTL = False
        self.multithreadRTL = False

        self.optMD = False
        self.optMDd = False
        self.optMT = False
        self.optMTd = False
        self.optLD = False
        self.optLDd = False

        flags = SCons.Util.Split(env.subst("$CCFLAGS $CXXFLAGS"))
        for flag in flags:
            if flag == '/MD':
                self.optMD = True
            elif flag == '/MDd':
                self.optMDd = True
            elif flag == '/MT':
                self.optMT = True
            elif flag == '/MTd':
                self.optMTd = True
            elif flag == '/LD':
                self.optLD = True
            elif flag == '/LDd':
                self.optLDd = True

        if self.optMDd or self.optMTd or self.optLDd:
            self.debugRTL = True
        if self.optMD or self.optMDd:
            self.dynamicRTL = True
        if self.optMD or self.optMDd or self.optMT or self.optMTd:
            self.multithreadRTL = True
        return False

    def isDebugRTL(self):
        return self.debugRTL

    def isDynamicRTL(self):
        return self.dynamicRTL

    def isMultithreadRTL(self):
        return self.multithreadRTL

def GetMSVCInfo(env):
    msvcInfo = env.get('SB_MSVC_INFO', None)
    if not msvcInfo:
        msvcInfo = MSVCInfo(env)
        env.Replace(SB_MSVC_INFO=msvcInfo)
    return msvcInfo

def UpdateMSVCInfo(env):
    msvcInfo = GetMSVCInfo(env)
    msvcInfo.update(env)
    return msvcInfo

def IsMSVC_Debug(env):
    """Check if debug-specific version of a MSVC runtime library is used"""
    return GetMSVCInfo(env).isDebugRTL()

def IsMSVC_DLL(env):
    """Check if DLL-specific version of a MSVC runtime library is used"""
    return GetMSVCInfo(env).isDynamicRTL()

def IsMSVC_Multithread(env):
    """Check if multithread-specific version of a MSVC runtime library is used
    """
    return GetMSVCInfo(env).isMultithreadRTL()

# Custom Variables

AddCustomVariables(
    ('IA32ROOT', "Path to the Intel's icc compiler. Specific to Intel compiler."),
    EnumVariable('intel_link_libintel', 'Mode for linking of the Intel provided libraries. Specific to Intel compiler.', 'shared', ['shared', 'static']),
    EnumVariable('intel_link_libgcc', 'Mode for linking of the libgcc C++ library. Specific to Intel compiler.', 'shared', ['shared', 'static']),
    ('MSVC_VERSION', 'Version of MSVC to use'),
    PackageVariable('msvc_compiler_dir',
                    'path to MSVC compiler directory', 'no')
    )

# Custom Configuration

def CheckCCompiler(ctx):
    ctx.Message('Checking C compiler... ')
    ret, outputStr = ctx.TryRun("""
    #include <stdio.h>
    int main(int argc, char **argv) {
      printf("Hello world");
      return 0;
    }
    """, extension='.c')
    
    if ret and outputStr:
        if outputStr.strip() != 'Hello world':
            ctx.Message('Compilation failed')
            ctx.Result(0)
            return 0
    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckCCompiler', CheckCCompiler)

def CheckTypeSizes(ctx, write_config_h=True):
    ctx.Message('Checking type sizes... ')
    ret, outputStr = ctx.TryRun("""
    #include <stdio.h>
    int main(int argc, char **argv) {
      printf("%i %i %i %i\\n", sizeof(char), sizeof(short), sizeof(int), sizeof(long));
      return 0;
    }
    """, extension='.c')
    
    ret1, outputStr1 = ctx.TryRun("""
    #include <stdio.h>
    int main(int argc, char **argv) {
      printf("%i\\n", sizeof(long long));
      return 0;
    }
    """, extension='.c')

    symprefix = getAutoconfPrefix(ctx.env)
    
    if ret and outputStr:
        sizes = map(int, outputStr.split())
        if not (sizes[0] == 1 and \
                sizes[0] <= sizes[1] and \
                sizes[1] <= sizes[2] and \
                sizes[2] <= sizes[3]):
            ctx.Message('Wrong type sizes : char : %i, short : %i, int : %i, long : %i. ' % tuple(sizes))
            ctx.Result(0)
            return 0

        if ret1:
            sizes += map(int, outputStr1.split())

        names = ['char', 'short', 'int', 'long', 'long long']
        defs = []
        
        # define sizeof int
        k, v = symprefix+'SIZE_OF_INT', sizes[2]

        if not (write_config_h and AddConfigKey(ctx, k, v)):
            defs.append((k, v))
        
        
        # int8 is always char !
        # int16
        try:
            k, v = symprefix+'INT16_TYPE', names[sizes.index(2)]
            if not (write_config_h and AddConfigKey(ctx, k, v)):
                defs.append((k, v))
        except ValueError:
            ctx.Message('No 16-bit integer ')
            ctx.Result(0)
            return 0

        # int32
        try:
            k, v = symprefix+'INT32_TYPE', names[sizes.index(4)]
            if not (write_config_h and AddConfigKey(ctx, k, v)):
                defs.append((k, v))
            
        except ValueError:
            ctx.Message('No 32-bit integer ')
            ctx.Result(0)
            return 0

        # int64
        try:
            k, v = symprefix+'INT64_TYPE', names[sizes.index(8)]
            if not (write_config_h and AddConfigKey(ctx, k, v)):
                defs.append((k, v))
        except ValueError:
            ctx.Message('No 64-bit integer ')
        
        ctx.env.Append(CPPDEFINES=defs)
    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckTypeSizes', CheckTypeSizes)

def CheckEndianness(ctx, write_config_h=True):
    ctx.Message('Checking platform endianness... ')
    ret, outputStr = ctx.TryRun("""
    #include <stdio.h>
    int main(int argc, char **argv) {
      // From Harbison&Steele, adopted from cmake
      union
      {
        long l;
        char c[sizeof (long)];
      } u;
      u.l = 1;
      if (u.c[sizeof (long) - 1] == 1)
        printf("big\\n");
      else
        printf("little\\n");
      return 0;
    }
    """, extension='.c')
    
    symprefix = getAutoconfPrefix(ctx.env)
    
    if ret:
        be_key = symprefix+'BIG_ENDIAN'
        le_key = symprefix+'LITTLE_ENDIAN'
        
        if outputStr.find('big') != -1:
            if write_config_h and AddConfigKey(ctx, be_key, 1):
                AddConfigKey(ctx, le_key, 0)
            else:
                ctx.env.Append(CPPDEFINES=[be_key])
        elif outputStr.find('little') != -1:
            if write_config_h and AddConfigKey(ctx, le_key, 1):
                AddConfigKey(ctx, be_key, 0)
            else:
                ctx.env.Append(CPPDEFINES=[le_key])
        else:
            if write_config_h:
                AddConfigKey(ctx, le_key, 0)
                AddConfigKey(ctx, be_key, 0)
            ctx.Message('Could not determine platform endianess')
            ctx.Result(0)
            return 0
    
    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckEndianness', CheckEndianness)

def CheckPthreads(ctx, write_config_h=False, add_to_cppdefines=False):
    ctx.Message('Checking for pthreads... ')
    platform = ctx.env['PLATFORM']
    lastLIBS = list(ctx.env.get('LIBS', []))

    for pthreadlib in ('pthread',):
        ctx.env.Append(LIBS = [pthreadlib])
        ret = ctx.TryLink("""
    #include <pthread.h>
    void *thread_main(void *dummy) { }
       
    int main(int argc, char **argv) {
      pthread_t handle;
      pthread_create(&handle, 0, &thread_main, NULL);
      return 0;
    }
    """, extension='.c')
        ctx.env.Replace(LIBS = lastLIBS)
        if ret:
            ctx.env.Replace(LIBPTHREAD=[pthreadlib])
            break
    key = getAutoconfPrefix(ctx.env)+'HAVE_LIBPTHREAD'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_cppdefines:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckPthreads', CheckPthreads)

def CheckCPUInfo(ctx, write_config_h=False, add_to_cppdefines=False):
    ctx.Message('Trying to get CPU information ... ')

    confprefix = getAutoconfPrefix(ctx.env)

    ret, outputStr = ctx.TryRun("""
#include <stdio.h>

#if defined(_MSC_VER) || (defined(__INTEL_COMPILER) && defined(_WIN32))
#
#   include <intrin.h>
#
#   define GET_CPUID(aInfo, aInfoType) __cpuid(aInfo, aInfoType)
#
#else // POSIX & Mac OS X
#
#   define GET_CPUID(aInfo, aInfoType)                             \
        __asm__ __volatile__ ("cpuid":                             \
            "=a" (aInfo[0]), "=b" (aInfo[1]), "=c" (aInfo[2]),     \
            "=d" (aInfo[3]) : "a" (aInfoType));
#
#endif

#define INFO_TYPE_IDENTIFICATION    0
#define INFO_TYPE_CAPABILITIES      1
#define INFO_TYPE_EXT               0x80000000
#define INFO_TYPE_EXT1              0x80000001
#define INFO_TYPE_EXT6              0x80000006

int main(int argc, char **argv)
{
  int info[4];
  int maxExtInfo;
  
  // Get CPU brand
  GET_CPUID(info, INFO_TYPE_IDENTIFICATION);

  printf("%i %i %i %i\\n", info[0], info[1], info[2], info[3]);

  GET_CPUID(info, INFO_TYPE_CAPABILITIES);

  printf("%i %i %i %i\\n", info[0], info[1], info[2], info[3]);

  GET_CPUID(info, INFO_TYPE_EXT);

  printf("%i %i %i %i\\n", info[0], info[1], info[2], info[3]);

  maxExtInfo = info[0];

  // Get extended capabilities 1
  if (maxExtInfo >= INFO_TYPE_EXT1)
  {
      GET_CPUID(info, INFO_TYPE_EXT1);
      printf("%i %i %i %i\\n", info[0], info[1], info[2], info[3]);
  }

  if (maxExtInfo >= INFO_TYPE_EXT6)
  {
      GET_CPUID(info, INFO_TYPE_EXT6);
      printf("%i %i %i %i\\n", info[0], info[1], info[2], info[3]);
  }
  
  return 0;
}
""", extension='.c')
    
    if ret and outputStr:
        values = map(int, outputStr.split())

        if len(values) % 4 != 0:
            ctx.Message('Wrong number of values : %i, should be multiple of 4 ' % len(values))
            ctx.Result(0)
            return 0

        infoList = []

        for i in xrange(0, len(values), 4):
            infoList.append(values[i:i+4])

        def extract(data, mask):
            return data & mask

        def checkBit(data, bit):
            return int((data & (1 << bit)) != 0)

        def unsigned_int(i):
            return struct.unpack('I', struct.pack('i', i))[0]

        info = infoList[0]

        brand = struct.pack('3i', info[1], info[3], info[2])

        capabilities = {'intel' : 0, 'amd' : 0}

        if brand == 'GenuineIntel':
            capabilities['intel'] = 1

        if brand == 'AuthenticAMD':
            capabilities['amd'] = 1

        # Get basic capabilities
        typeCaps = infoList[1]

        capabilities["mmx"]    = checkBit(typeCaps[3], 23)
        capabilities["sse"]    = checkBit(typeCaps[3], 25)
        capabilities["sse2"]   = checkBit(typeCaps[3], 26)
        capabilities["sse3"]   = checkBit(typeCaps[2],  0)
        capabilities["ssse3"]  = checkBit(typeCaps[2],  9)
        capabilities["sse4_1"] = checkBit(typeCaps[2], 19)
        capabilities["sse4_2"] = checkBit(typeCaps[2], 20)
        capabilities["popcnt"] = checkBit(typeCaps[2], 23)
        capabilities["x87"]    = checkBit(typeCaps[3],  0)
        capabilities["cores"]  = extract(typeCaps[1] >> 16, 0xF)

        # Get extended capabilities
        INFO_TYPE_EXT  = 0x80000000
        INFO_TYPE_EXT1 = 0x80000001
        INFO_TYPE_EXT6 = 0x80000006

        maxExtInfo = unsigned_int(infoList[2][0])

        if maxExtInfo >= INFO_TYPE_EXT1:

            info = infoList[3]

            capabilities["3dnow"]      = 0
            capabilities["3dnowext"]   = 0
            capabilities["mmxext"]     = 0
            capabilities["sse4a"]      = 0
            capabilities["amd_rdtscp"] = 0

            if capabilities["amd"]:
                capabilities["3dnow"]      = checkBit(info[3], 31)
                capabilities["3dnowext"]   = checkBit(info[3], 30)
                capabilities["mmxext"]     = checkBit(info[3], 22)
                capabilities["sse4a"]      = checkBit(info[2],  6)
                capabilities["amd_rdtscp"] = checkBit(info[3], 27)

            capabilities["x64"] = checkBit(info[3], 29)

        if maxExtInfo >= INFO_TYPE_EXT6:

            info = infoList[4]

            capabilities["cache_line"] = extract(info[2], 0xFF)
            capabilities["cache"]      = extract(info[2] >> 16, 0xFFFF)
            capabilities["cache_associativity"] = extract(info[2] >> 12, 0xF)

        ctx.env.Replace(CPUINFO=capabilities)
        
    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckCPUInfo', CheckCPUInfo)

def getCPUInfo(env):
    CPUINFO = env.get('CPUINFO')
    if CPUINFO:
        return CPUINFO
    else:
        # Try to detect current CPU
        conf = Configure(env, custom_tests = { 'CheckCPUInfo' : CheckCPUInfo },
                         conf_dir=env.GetConfigureDir(),
                         log_file=env.GetConfigureLogFile())

        success = conf.CheckCPUInfo()
        
        confEnv = conf.Finish()
        
        if success:
            return confEnv['CPUINFO']
        
    return None

# Custom Environment

def customizeEnvironment(env):
    # setup all basic libraries

    platform = env['PLATFORM']
    
    env.Replace(LIBPTHREADS=['pthread'])
    if platform == 'win32':
        env.Replace(LIBDL=[])
        # compatibility dl package
        env.DeclarePackage('dl', vars={}, trigger_libs=['dl'])
    else:
        env.Replace(LIBDL=['dl'])
        env.DeclarePackage('dl', trigger_libs=['dl'], LIBS=['dl'])
        
    # TODO: this setup is only correct for Linux
    env.Replace(LIBX11DIR=['/usr/X11R6/lib', '/usr/X11R6/lib64'])
    env.Replace(LIBXMU=['Xmu'])
    env.Replace(LIBXRENDER=['Xrender'])
    env.Replace(LIBGL=['GL']) 
    env.Replace(LIBX11=['Xext', 'X11'])
    env.Replace(LIBMATH=['m'])
    env.Replace(INCLUDEX11='/usr/X11R6/include')

    #env.Append(LIBS=['$LIBDL', '$LIBMATH'])
    #env.Append(CPPDEFINES=['__%s__' % getpass.getuser()])

    env.AddMethod(GetMSVCInfo, 'GetMSVCInfo')
    env.AddMethod(UpdateMSVCInfo, 'UpdateMSVCInfo')
    env.AddMethod(IsMSVC_Debug, 'IsMSVC_Debug')
    env.AddMethod(IsMSVC_DLL, 'IsMSVC_DLL')
    env.AddMethod(IsMSVC_Multithread, 'IsMSVC_Multithread')

    env.AddMethod(getProjectPrefix, 'GetProjectPrefix')
    env.AddMethod(getProjectSystemPrefix, 'GetProjectSystemPrefix')
    env.AddMethod(getProjectCompilerPrefix, 'GetProjectCompilerPrefix')
    env.AddMethod(getAutoconfPrefix, 'GetAutoconfPrefix')

RegisterEnvironmentCustomizer(customizeEnvironment)

# Compilers

# ARGUMENTS variable can be used to find out which environment variables
# were set by the command line arguments

def parseCompilerVersion(s):
    m = re.search(r'([0-9]+)\.([0-9]+)(?:\.([0-9]+))?', s)
    if m:
        major, minor, patch = map(lambda x: x and int(x), m.groups())
        if patch is None:
            patch = 0
        versionid = major*10000 + minor*100 + patch
        return (major, minor, patch, versionid)
    else:
        return (0, 0, 0, 0)

def parseIntelCompilerVersion(s):
    """this function can parse version information printed
    by -v and -V options.
    Returns tuple (minor, major, patch, buildid, versionid)
    where minor, major, patch and versionid are ints and buildid is string
    """
    m = re.search(r'Version\s+([0-9]+)\.([0-9]+)(?:\s+Build\s+([^\s]+)\s+Package\sID:\s[^\s0-9]+([0-9]+)\.([0-9]+)\.([0-9]+))?', s)
    if m:
        major = int(m.group(1))
        minor = int(m.group(2))
        buildid = m.group(3)
        if m.group(4) and int(m.group(4)) == major and \
               m.group(5) and int(m.group(5)) == minor:
            patch = int(m.group(6))
        else:
            patch = 0
        versionid = major*10000 + minor*100 + patch
        return (major, minor, patch, buildid, versionid)
    else:
        return (0, 0, 0, '', 0)

# misc MSVC utilities

def setupMsvcTool(env, msvcCompilerDir, toolName='msvc'):
    """returns modified msvcCompilerDir"""
    if msvcCompilerDir:
        compilerFound = False
        for d in [msvcCompilerDir,
                  os.path.join(msvcCompilerDir, 'bin'),
                  os.path.join(msvcCompilerDir, 'VC', 'bin')]:
            if env.WhereIs('cl', d):
                env.PrependENVPath('PATH', d)
                msvcCompilerDir = d
                compilerFound = True
                break
        if not compilerFound:
            print >>sys.stderr, 'Error: No compiler found in %s directory' % \
                  msvcCompilerDir
            msvcCompilerDir = None
            env.Exit(1)
        else:
            print '** Use MSVC compiler from directory %s' % msvcCompilerDir

    env.Tool(toolName)

    if msvcCompilerDir:
        # loading msvc tool may change env['ENV']['PATH'], thus repeat update
        env.PrependENVPath('PATH', msvcCompilerDir)
        
        # check for include and lib directories
        includeDir = os.path.normpath(os.path.join(msvcCompilerDir,
                                                   '..', 'include'))
        if os.path.exists(includeDir):
            env.PrependENVPath('INCLUDE', includeDir)
            
        libDir = os.path.normpath(os.path.join(msvcCompilerDir,
                                               '..', 'lib'))
        if os.path.exists(libDir):
            env.PrependENVPath('LIB', libDir)

    # Check MSVS version number
    
    MSVS = env.get('MSVS')
    if not MSVS:
        print >>sys.stderr, 'Error: Could not find MSVC/MSVS C/C++ compiler'
        env.Exit(1)

    MSVC_VERSION = env.get('MSVC_VERSION', env.get('MSVS_VERSION'))

    (vmaj, vmin, vpatch, versionid) = parseCompilerVersion(MSVC_VERSION)

    print '** Determined MSVC/MSVS Compiler Version %s' % MSVC_VERSION
    print '** All Available: %s' % (' '.join(MSVS.get('VERSIONS', [MSVC_VERSION])))

    # Workaround for SCons versions which does not know about MSVS 9.0
    if versionid >= 90000 and MSVS.has_key('VCINSTALLDIR') and \
            (not env['ENV'].has_key('INCLUDE') or \
                 MSVS['VCINSTALLDIR'] not in env['ENV']['INCLUDE']):

        print '** Applying workaround for MSVS 9.x'
        # -- INCLUDE --
        env.PrependENVPath('INCLUDE', os.path.join(MSVS['VCINSTALLDIR'], 
                                                   'INCLUDE'))
        env.PrependENVPath('INCLUDE', os.path.join(MSVS['VCINSTALLDIR'], 
                                                   'ATLMFC', 'INCLUDE'))

        # -- LIB --
        env.PrependENVPath('LIB', os.path.join(MSVS['VCINSTALLDIR'], 'LIB'))
        env.PrependENVPath('LIB', os.path.join(MSVS['VCINSTALLDIR'],
                                               'ATLMFC', 'LIB'))
        # -- LIBPATH --
        env.PrependENVPath('LIBPATH', os.path.join(MSVS['VCINSTALLDIR'], 'LIB'))
        env.PrependENVPath('LIBPATH', os.path.join(MSVS['VCINSTALLDIR'], 
                                                   'ATLMFC', 'LIB'))
        env.PrependENVPath('LIBPATH', os.path.join(MSVS['FRAMEWORKDIR'], 
                                                   MSVS['FRAMEWORKVERSION']))

        # -- PATH --
        env.PrependENVPath('PATH', os.path.join(MSVS['VCINSTALLDIR'],
                                                'VCPackages'))
        env.PrependENVPath('PATH', os.path.join(MSVS['FRAMEWORKDIR'], 
                                                MSVS['FRAMEWORKVERSION']))
        env.PrependENVPath('PATH', os.path.join(MSVS['VSINSTALLDIR'],
                                                'Common7', 'Tools'))
        env.PrependENVPath('PATH', os.path.join(MSVS['VCINSTALLDIR'], 'BIN'))
        env.PrependENVPath('PATH', os.path.join(MSVS['VSINSTALLDIR'], 
                                                'Common7', 'IDE'))

    if versionid >= 80000: # MSVS 8.0
        # add support for manifests
        print '** Using mt.exe for adding manifests to the binaries'
        env.Replace(SHLINKCOM=[ env['SHLINKCOM'], 'mt.exe -nologo -manifest ${TARGET}.manifest -outputresource:$TARGET;2' ])

    if versionid >= 100000: # MSVS 10.0
        # With MSVS 10.0 link.exe does not create manifests when /MD option
        # is used. We need to force manifests with /MANIFEST option
        env['MSLINKFLAGS'] = SCons.Util.CLVar('/MANIFEST')
    else:
        env['MSLINKFLAGS'] = SCons.Util.CLVar('')

    # Check for Platform SDK

    PLATFORMSDKDIR = MSVS.get('PLATFORMSDKDIR')
    if not PLATFORMSDKDIR and SCons.Util.can_read_reg:
        # Try alternative check for PSDK (portions from msvs.py SCons tool)
        winMajorVer = sys.getwindowsversion()[0]
        
        # list of tuples (main_registry_key, installation_path_subkey)
        regKeysToCheck = [
            (r'Software\Microsoft\Microsoft SDKs\Windows', 
             'installationfolder'), # MS SDK v6.0a (later versions too?)
            (r'Software\Microsoft\MicrosoftSDK\InstalledSDKs',
             'install dir')
            ]

        ## Windows Vista
        #if winMajorVer >= 6:
        #    location = r'Software\Microsoft\Microsoft SDKs\Windows'
        #    keyValue = 'installationfolder'

        ## Windows XP and older
        #else:
        #    location = r'Software\Microsoft\MicrosoftSDK\InstalledSDKs'
        #    keyValue = 'install dir'
        
        rootKeys = [SCons.Util.HKEY_LOCAL_MACHINE, SCons.Util.HKEY_CURRENT_USER]
        
        installDirs = []

        for location, keyValue in regKeysToCheck:
            try:
                for rootKey in rootKeys:
                    k = SCons.Util.RegOpenKeyEx(rootKey, location)
                    i = 0
                    while 1:
                        try:
                            key = SCons.Util.RegEnumKey(k,i)
                            sdk = SCons.Util.RegOpenKeyEx(k,key)
                            j = 0
                            installDir = ''
                            while 1:
                                try:
                                    (vk,vv,t) = SCons.Util.RegEnumValue(sdk,j)

                                    if vk.lower() == keyValue:
                                        installDir = vv
                                        break
                                    j = j + 1
                                except SCons.Util.RegError:
                                    break
                            if installDir:
                                installDirs.append(installDir)
                            i = i + 1
                        except SCons.Util.RegError:
                            break
            except SCons.Util.RegError:
                pass

        for dir in installDirs:
            if os.path.isdir(os.path.join(dir, 'Include')) and \
                   os.path.isdir(os.path.join(dir, 'Lib')):
                PLATFORMSDKDIR = dir
                break
    
    if PLATFORMSDKDIR:
        print '** Determined Platform SDK Path: %s' % PLATFORMSDKDIR
        env.AppendENVPath('INCLUDE', os.path.join(PLATFORMSDKDIR, 'Include'))
        env.AppendENVPath('LIB', os.path.join(PLATFORMSDKDIR, 'Lib'))
        env.AppendENVPath('PATH', os.path.join(PLATFORMSDKDIR, 'bin'))
        # Following does not work correctly :
        #env.Append(CPPPATH=[os.path.join(PLATFORMSDKDIR, 'Include')])
        #env.Append(LIBPATH=[os.path.join(PLATFORMSDKDIR, 'Lib')])
    else:
        print '** Warning: Platform SDK not found, please specify the paths manually'

    class _setup_result:
        pass

    r = _setup_result()
    r.msvcVersionMajor = vmaj
    r.msvcVersionMinor = vmin
    r.msvcVersionPatch = vpatch
    r.msvcVersionId = versionid
    r.msvcCompilerDir = msvcCompilerDir
    r.PLATFORMSDKDIR = PLATFORMSDKDIR
    return r

def getIntelCompilerVersion(env):
    # check version number (on Windows icl prints version by default)
    isWin32 = (env['PLATFORM'] == 'win32')
    cmd = env['CXX']

    if not isWin32:
        # on posix you need -V to get full version
        cmd += ' -V'
    
    ret, out, err = runCommand(cmd, env=env['ENV'])

    if ret == 0 or out or err:
        (vmaj, vmin, vpatch, buildid, versionid) = \
               parseIntelCompilerVersion(out+' '+err)
        version = '%s.%s.%s' % (vmaj, vmin, str(vpatch).rjust(3, '0'))
    else:
        version = None

    if version:
        print '** Determined Intel C/C++ Compiler Version %s' % (version,)
    else:
        version = '9.x'
        versionid = 90000
        print '** Could not determine Intel C/C++ Compiler Version, '\
              'assume %s' % (version,)

    class _version_result:
        pass

    r = _version_result()
    r.iccVersionMajor = vmaj
    r.iccVersionMinor = vmin
    r.iccVersionPatch = vpatch
    r.iccBuildId      = buildid
    r.iccVersionId    = versionid
    r.iccVersion      = version
    return r


def SetupIntelCompiler(env):
    compiler = env['compiler']
    assert compiler in ('INTEL', 'INTEL_NOGCC')
    
    print '* Setup %s compiler' % compiler

    CC = ARGUMENTS.get('CC')
    CXX = ARGUMENTS.get('CXX')

    archInfo = getArchInfo(env)
    optMode = env['optimization']
    warningsMode = env['warnings'] # False/True
    debugMode = env['debug']       # 'no' / 'symbols' / 'macro' / 'full'
    platform = env['PLATFORM']
    isWin32 = (platform == 'win32')
    isMacOSX = (platform == 'darwin')

    msvcCompilerDir = env['msvc_compiler_dir']

    intelLinkLibIntel = env['intel_link_libintel']
    intelLinkLibGCC = env['intel_link_libgcc']

    # analyize optimization modes

    optimizeCode = (optMode not in ('none', 'debug'))

    # analyize debug modes
    debugSymbols = False
    debugMacro = False
    
    if optMode == 'debug':
        debugSymbols = True
        debugMacro = True
    elif optMode == 'none':
        debugMacro = True
        debugSymbols = False

    if debugMode == 'symbols':
        debugSymbols = True
    elif debugMode == 'macro':
        debugMacro = True
    elif debugMode == 'full':
        debugSymbols = True
        debugMacro = True

    customLinker = True
    
    if env.PropagateEnvVar('IA32ROOT'):
        env.Replace(ICCPATH = os.path.join('$IA32ROOT', 'bin'))
        ICCPATH = os.path.join(env['IA32ROOT'], 'bin')
    else:
        ICCPATH = ''

    if isWin32:
        # Win32
        #         for v in ['DevEnvDir', 'INCLUDE', 'LIB', 'LIBPATH', 'MSSdk',
        #                   'Bkoffice', 'Basemake', 'INETSDK', 'Ms']:
        #             env['ENV'] = os.environ[v]
        env['ENV'] = os.environ

        msvcInfo = setupMsvcTool(env, msvcCompilerDir, toolName='icl')

        ICLBIN = os.path.join(ICCPATH, 'icl.exe')

        if CC is None:
            CC = ICLBIN
        if CXX is None:
            CXX = ICLBIN

        if env.WhereIs(CC):
            env.Replace(CC=CC)
        else:
            print >>sys.stderr, 'Error: Could not find Intel C compiler',CC
            env.Exit(1)

        if env.WhereIs(CXX):
            env.Replace(CXX=CXX)
        else:
            print >>sys.stderr, 'Error: Could not find Intel C++ compiler',CXX
            env.Exit(1)

        iccInfo = getIntelCompilerVersion(env)

        # Deactivate Intel compiler warnings
        env.Append(CCFLAGS = split('/Qwd 1538 /Qwd 1429 /Qwd 1420 /Qwd 589 /Qwd 1572'))

        # Misc flags
        WARNING_FLAGS = ['/W1']
        DEBUG_FLAGS = ['/Zi']

        # MSVC compatibility flag
        if msvcInfo.msvcVersionId >= 90000:   # MSVC >=9.0
            env.Append(CCFLAGS = ['/Qvc9'])
        elif msvcInfo.msvcVersionId >= 80000:   # MSVC >=8.0
            env.Append(CCFLAGS = ['/Qvc8'])
        elif msvcInfo.msvcVersionId == 70000: # MSVC 7.0
            env.Append(CCFLAGS = ['/Qvc7'])
        elif msvcInfo.msvcVersionId == 70100: # MSVC 7.1
            env.Append(CCFLAGS = ['/Qvc7.1'])
        elif msvcInfo.msvcVersionId == 60000: # MSVC 6.0
            env.Append(CCFLAGS = ['/Qvc6'])

        # --------------------------------------------
        # architecture dependent flags for various processor platforms

        genericArchFlags = {
            ARCH_X86 : ['/QxK'],
            ARCH_X86_64 : ['/QxP'],
            ARCH_IA64 : ['/G2']
            }
        genericArchFlag = genericArchFlags.get(archInfo.arch, [])

        targetFlags = {
            CPU_GENERIC : genericArchFlag,
            CPU_NATIVE : genericArchFlag,
            CPU_PENTIUM_3 : ['/QxK'],
            CPU_PENTIUM_4 : ['/QxW'],
            CPU_PENTIUM_M : ['/QxB'],
            CPU_CORE      : ['/QxP'],
            CPU_CORE_2    : ['/QxT'],
            CPU_OPTERON   : ['/QxP'],
            CPU_ITANIUM   : ['/G2']
            }

        if optimizeCode and targetFlags.has_key(archInfo.cpu):
            env.Append(CCFLAGS = targetFlags[archInfo.cpu])
        
        # /GR : Enables C++ Run Time Type Information (RTTI).
        # /Gr : Makes __fastcall the default calling convention.
        # /O2 : Enables optimizations for speed.
        # /Ob2 : Enables inlining of any function at the compiler's discretion.
        # /Od : Disables all optimizations.
        # /TP : Tells the compiler to process all source or unrecognized file types as C++ source files.
        # /Ot : Enables all speed optimizations.
        # /Oy : Determines whether EBP is used as a general-purpose register in optimizations.
        # /G7 : Optimizes for Intel(R) Core  Duo processors, Intel(R) Core  Solo processors, Intel(R) Pentium(R) 4 processors, Intel(R) Xeon(R) processors, Intel(R) Pentium(R) M processors, and Intel(R) Pentium(R) 4 processors with Streaming SIMD Extensions 3 (SSE3) instruction support. 
        # /Zi : Tells the compiler to generate full debugging information in the object file.
        # /Og : Enables global optimizations.
        # /EHsc : enable synchronous C++ exception handling model,
        #         assume extern "C" functions do not throw exceptions
        # /MD   : Tells the linker to search for unresolved references in 
        #         a multithreaded, debug, dynamic-link run-time library. 
        # /Zp16 : Specifies alignment for structures on byte boundaries.
        # /Zc:forScope : Enforce standard behavior for initializers
        #                of for loops.
        # /Qc99 : Enables/disables C99 support for C programs. (DEPRECATED!)
        # /Gm   : enable minimal rebuild
        # /Qscalar_rep : Enables scalar replacement performed during
        #                loop transformation.
        # /Qrestrict   : Enables pointer disambiguation with the restrict
        #                qualifier. 
        # /Gd : Makes __cdecl the default calling convention.
        # /FD : Generates file dependencies related to the Microsoft* C/C++ compiler. 

        # general optimization options
        
        OPTFLAGS_NONE = split('/Od /FD /EHsc /MD /GR /Zi /Gd /Qrestrict /Qmultibyte-chars')
        OPTFLAGS_DEBUG = split('/Od /FD /EHsc /RTC1 /MDd /GR /Zi /Gd /Qrestrict /Qmultibyte-chars')
        OPTFLAGS_MEDIUM = split('/GR /O2 /Ob2 /TP /Ot /Oy /G7 /Zi /Og /EHsc /MD /Zp16 /Zc:forScope /Qscalar_rep /Qrestrict /Gd')
        OPTFLAGS_HIGH = OPTFLAGS_MEDIUM
        OPTFLAGS_EXTREME = OPTFLAGS_HIGH

        opts = {
            'none' : OPTFLAGS_NONE,
            'debug' : OPTFLAGS_DEBUG,
            'medium' : OPTFLAGS_MEDIUM,
            'high' : OPTFLAGS_HIGH,
            'extreme' : OPTFLAGS_EXTREME
            }

        if opts.has_key(optMode):
            env.Append(CCFLAGS = opts[optMode])
        else:
            # medium optimization per default
            env.Append(CCFLAGS = opts['medium'])

        # linking with/without debug

        if optMode == 'debug':
            env.Replace(LINKFLAGS = split('/nologo /DEBUG /SUBSYSTEM:CONSOLE $MSLINKFLAGS'))
        else:
            env.Replace(LINKFLAGS = split('/nologo /SUBSYSTEM:CONSOLE $MSLINKFLAGS'))

        env.Append(CPPPATH=[os.path.join('${IA32ROOT}','include')])

        if env.WhereIs(env['LINK']):
            customLinker = False
        else:
            customLinker = True            
            
        # end Win32
    else:
        # POSIX
        for tool in ('gcc', 'g++'):
            env.Tool(tool)

        if isMacOSX:
            for tool in ('applelink', 'ar', 'as'):
                env.Tool(tool)

        # locate compiler
        for k in env.Split('INTEL_LICENSE_FILE LIB INCLUDE LD_LIBRARY_PATH DYLD_LIBRARY_PATH MKLROOT IPPROOT CPATH LIBRARY_PATH'):
            if os.environ.has_key(k):
                env['ENV'][k] = os.environ.get(k)

        ICCBIN = env.Detect([os.path.join(ICCPATH, 'iccbin'),
                             os.path.join(ICCPATH, 'icc')])

        if CC is None:
            CC = ICCBIN
        if CXX is None:
            CXX = ICCBIN

        if CC:
            env.Replace(CC = CC)
        else:
            print 'Error: Could not find Intel C compiler'
            env.Exit(1)

        if CXX:
            env.Replace(CXX = CXX)
        else:
            print 'Error: Could not find Intel C++ compiler'
            env.Exit(1)

        iccInfo = getIntelCompilerVersion(env)

        # Deactivate some Intel compiler warnings
        env.Append(CCFLAGS = ['-Wno-unknown-pragmas',
                              '-wd1188,1476,1505,1572,858'])

        # Setup general options
        if iccInfo.iccVersionId > 100000: # > 10.0
            OPT_CXXLIB_ICC = None
            OPT_CXXLIB_GCC = '-cxxlib'
            OPT_INLINE_LEVEL = lambda x: '-inline-level='+str(x)
            OPT_TUNE_x86 = ''
            OPT_TUNE_Pentium3 = ''
            OPT_TUNE_Pentium4 = '-mtune=pentium4'
            OPT_TUNE_Itanium2 = '-mtune=itanium2'
            OPT_STATIC_INTEL = '-static-intel'
            OPT_SHARED_INTEL = '-shared-intel'
        else:
            OPT_CXXLIB_ICC = '-cxxlib-icc'
            OPT_CXXLIB_GCC = '-cxxlib-gcc'
            OPT_INLINE_LEVEL = lambda x: '-Ob'+str(x)
            OPT_TUNE_x86 = ''
            OPT_TUNE_Pentium3 = '-tpp6'
            OPT_TUNE_Pentium4 = '-tpp7'
            OPT_TUNE_Itanium2 = '-tpp2'
            OPT_STATIC_INTEL = '-i-static'
            OPT_SHARED_INTEL = '-i-dynamic'

        if compiler == 'INTEL_NOGCC':
            if iccInfo.iccVersionId > 100000:
                print >>sys.stderr, 'Error: INTEL_NOGCC mode is not supported'\
                      ' by Intel C/C++ Compiler since 10.x'
                env.Exit(1)
            CXXLIB = OPT_CXXLIB_ICC
            NOGCC = '-no-gcc'
        else:
            CXXLIB = OPT_CXXLIB_GCC
            NOGCC = ''

        env.Append(CCFLAGS = [NOGCC, CXXLIB])
        
        # Misc flags
        WARNING_FLAGS = ['-w1']
        DEBUG_FLAGS = ['-g']

        # --------------------------------------------
        # architecture dependent flags for various processor platforms
        #
        # -xK == Pentium III
        # -xW or -xN == Pentium IV
        # -xB == Pentium M
        # -xP == Prescott
        # -xT == Core 2

        genericArchFlags = {
            ARCH_X86 : ['', OPT_TUNE_x86, ''],
            ARCH_X86_64 : ['-xW', '-fPIC'],
            ARCH_IA64 : ['-IPF_fltacc', '-mcpu=itanium2', OPT_TUNE_Itanium2,
                         '-fPIC']
            }
        genericArchFlag = genericArchFlags.get(archInfo.arch, [])

        targetFlags = {
            CPU_GENERIC   : genericArchFlag,
            CPU_NATIVE    : genericArchFlag,
            CPU_PENTIUM_3 : ['-xK', OPT_TUNE_Pentium3, '-fPIC'],
            CPU_PENTIUM_4 : ['-xW', OPT_TUNE_Pentium4, '-fPIC'],
            CPU_PENTIUM_M : ['-xB', OPT_TUNE_Pentium4, '-fPIC'],
            CPU_CORE      : ['-xP', '-fPIC' ],
            CPU_CORE_2    : ['-xT', '-march=core2', '-mtune=core2', '-fPIC'],
            CPU_OPTERON   : ['-xW', '-fPIC'],
            CPU_ITANIUM   : ['-IPF_fltacc', '-mcpu=itanium2', OPT_TUNE_Itanium2, '-fPIC']
            }
        
        if optimizeCode and targetFlags.has_key(archInfo.cpu):
            env.Append(CCFLAGS = targetFlags[archInfo.cpu])

        OPTFLAGS_NONE = ['-O0', OPT_INLINE_LEVEL(0)]
        OPTFLAGS_DEBUG = ['-g'] + OPTFLAGS_NONE
        OPTFLAGS_MEDIUM = ['-O2', OPT_INLINE_LEVEL(1),'-restrict']
        OPTFLAGS_HIGH = ['-O3', OPT_INLINE_LEVEL(1), '-restrict']
        OPTFLAGS_EXTREME = ['-O3', OPT_INLINE_LEVEL(1), '-restrict', '-inline-forceinline']

        # unused:
        OPTFLAGS_ITANIUM = ['-DNDEBUG', '-restrict',
                            '-DALLOW_RESTRICT', '-O3', '-IPF_fma',
                            OPT_INLINE_LEVEL(1), '-IPF_fltacc',
                            '-IPF_flt_eval_method0',
                            '-IPF_fp_relaxed',
                            '-IPF_fp_speculationfast',
                            '-scalar_rep',
                            '-alias_args-', '-fno-alias']
        INLINE_FLAGS = ['-fno-alias', '-Qoption,c,-ip_ninl_max_stats=6000',
                        '-Qoption,c,-ip_ninl_max_total_stats=10000',
                        OPT_INLINE_LEVEL(2)]

        opts = {
            'none' : OPTFLAGS_NONE,
            'debug' : OPTFLAGS_DEBUG,
            'medium' : OPTFLAGS_MEDIUM,
            'high' : OPTFLAGS_HIGH,
            'extreme' : OPTFLAGS_EXTREME
            }

        if opts.has_key(optMode):
            env.Append(CCFLAGS = opts[optMode])
        else:
            # medium optimization per default
            env.Append(CCFLAGS = opts['medium'])

        if optimizeCode:
            # TODO: ALLOW_RESTRICT is unused, maybe remove
            #env.Append(CPPDEFINES = split('ALLOW_RESTRICT'))
            pass

        if not isMacOSX:
            # -Bsymbolic was removed from LINKFLAGS because 
            # of problems with dynamic_cast in shared libraries
            env.AppendUnique(LINKFLAGS = split('-rdynamic '+CXXLIB))

        if intelLinkLibIntel == 'static':
            env.AppendUnique(LINKFLAGS = [OPT_STATIC_INTEL])
        else:
            env.AppendUnique(LINKFLAGS = [OPT_SHARED_INTEL])

        if intelLinkLibGCC == 'static':
            env.AppendUnique(LINKFLAGS = ['-static-libgcc'])
        else:
            env.AppendUnique(LINKFLAGS = ['-shared-libgcc'])

        ICPCBIN = env.Detect([os.path.join(ICCPATH, 'icpcbin'),
                              os.path.join(ICCPATH, 'icpc')])

        if ICPCBIN:
            env.Replace(ICCLINK = ICPCBIN)
        else:
            print 'Error: Could not find Intel C++ compiler (icpc)'
            env.Exit(1)

        # end POSIX

    if warningsMode:
        env.Append(CCFLAGS = WARNING_FLAGS)

    if debugSymbols:
        # produce debug symbols
        env.AppendUnique(CCFLAGS = DEBUG_FLAGS)

    if not debugMacro:
        # disable debugging macros
        env.AppendUnique(CPPDEFINES = ['NDEBUG'])

    if customLinker:
        env.Replace(LINK = '${ICCLINK}')
        
def SetupGccCompiler(env):
    print '* Setup GCC compiler'

    archInfo = getArchInfo(env)
    optMode = env['optimization']
    warningsMode = env['warnings']  # False/True
    debugMode = env['debug']        # 'no' / 'symbols' / 'output' / 'full'
    profileMode = env['profile']    # False/True
    platform = env['PLATFORM']
    isWin32 = (platform == 'win32')
    isMacOSX = (platform == 'darwin')

    isBuild32on64bit = (archInfo.arch == ARCH_X86 and \
                        GetArchitectureId() == 'x86')

    if isWin32:
        # Workaround for the case msvc module was initialized
        # before mingw module: remove /nologo option.
        CCFLAGS = env.get('CCFLAGS')
        if CCFLAGS:
            filterOut = ['/nologo']
            CCFLAGS = filter(lambda i: i not in filterOut,
                             SCons.Util.Split(CCFLAGS))
            env.Replace(CCFLAGS=CCFLAGS)
        # Load mingw tool only if it is not already loaded
        TOOLS = env.get('TOOLS')
        if not TOOLS or 'mingw' not in TOOLS:
            env.Tool('mingw')
    elif isMacOSX:
        for tool in ('gcc', 'g++', 'applelink', 'ar', 'as'):
            env.Tool(tool)
    else:
        for tool in ('gcc', 'g++', 'gnulink', 'ar', 'as'):
            env.Tool(tool)

    # Determine CC/CXX vars (look in arguments, cache, config file(s),
    #                        environment variables)
    CACHED_VARIABLES = env['CACHED_VARIABLES']
    CONFIG_FILE_VARIABLES = env['CONFIG_FILE_VARIABLES']
        
    CACHED_VARIABLES_COMPILER = CACHED_VARIABLES.get('compiler',
                                                     GetDefaultCompilerName())
    
    if CACHED_VARIABLES_COMPILER == 'GCC':
        # cached options are for this compiler
        VAR_SEARCH_LIST = [ARGUMENTS, CONFIG_FILE_VARIABLES, CACHED_VARIABLES,
                           env['ENV'], os.environ]
    else:
        # cached options are for another compiler, ignore them
        VAR_SEARCH_LIST = [ARGUMENTS, CONFIG_FILE_VARIABLES,
                           env['ENV'], os.environ]
        print '** Cached options are for %s compiler, ignoring them.' % \
              CACHED_VARIABLES_COMPILER

    CC = findVarInDicts('CC', VAR_SEARCH_LIST, 'gcc')[0]
    CXX = findVarInDicts('CXX', VAR_SEARCH_LIST, 'g++')[0]

    # analyize optimization modes

    optimizeCode = (optMode not in ('none', 'debug'))

    # analyize debug modes
    debugSymbols = False
    debugMacro = False
    
    if optMode == 'debug':
        debugSymbols = True
        debugMacro = True
    elif optMode == 'none':
        debugMacro = True
        debugSymbols = False

    if debugMode == 'symbols':
        debugSymbols = True
    elif debugMode == 'macro':
        debugMacro = True
    elif debugMode == 'full':
        debugSymbols = True
        debugMacro = True

    # for safety update env
    env.Replace(CC = CC)
    env.Replace(CXX = CXX)
    
    # check version number
    ret, out, err = runCommand(CXX + ' --version', env=env['ENV'])

    if ret == 0 or out or err:
        (vmaj, vmin, vpatch, versionid) = parseCompilerVersion(out+' '+err)
        version = '%s.%s.%s' % (vmaj, vmin, vpatch)
        # try to detect compiler name
        for tok in [x.lower() for x in out.split()]:
            if tok in ('gcc', 'g++'):
                compilerName = 'GNU C/C++'
                break
            elif tok in ('clang', 'clang++'):
                compilerName = 'Clang'
                break
        else:
            compilerName = '<Unknown>'
    else:
        version = None
        compilerName = ''

    if version:
        print '** Determined %s Compiler Version %s' % (compilerName, version)
    else:
        version = '4.x'
        versionid = 40000
        print '** Could not determine GNU C/C++ Compiler Version, '\
              'assume %s' % (version,)

    # --------------------------------------------
    # architecture dependent flags for various processor platforms

    # setup 32/64-bit architecture
    # specificArchFlags contains tuples (CCFLAGS, LINKSFLAGS)
    specificArchFlags = {
        ARCH_X86 : (split('-m32'), split('-m32')),
        ARCH_X86_64 : (split('-m64'), split('-m64'))
        }
    if specificArchFlags.has_key(archInfo.arch):
        ccflags, linkflags = specificArchFlags[archInfo.arch]
        env.AppendUnique(CCFLAGS = ccflags)
        env.AppendUnique(LINKFLAGS = linkflags)

    genericArchFlags = {
        ARCH_X86 : split('-mfpmath=sse -msse -mmmx'),
        ARCH_X86_64 : split('-march=opteron -mmmx -msse -msse2'),
        ARCH_IA64 : split('-mtune=itanium2'),
        }
    genericArchFlag = genericArchFlags.get(archInfo.arch, [])

    targetFlags = {
        CPU_GENERIC   : genericArchFlag,
        CPU_NATIVE    : split('-march=native'),
        CPU_PENTIUM_3 : split('-march=pentium3 -mfpmath=sse -msse -mmmx'),
        CPU_PENTIUM_4 : split('-march=pentium4 -mfpmath=sse -msse -mmmx -msse2'),
        CPU_PENTIUM_M : split('-march=pentium-m -mfpmath=sse -msse -mmmx -msse2'),
        CPU_CORE      : split('-march=prescott -mfpmath=sse -msse -mmmx -msse2'),
        CPU_CORE_2    : split('-march=core2 -mtune=core2 -mfpmath=sse -msse -mmmx -msse2'),
        CPU_OPTERON   : split('-march=opteron -mmmx -msse -msse2'),
        CPU_ITANIUM   : split('-mtune=itanium2'),
        }

    if optimizeCode and targetFlags.has_key(archInfo.cpu):
        env.Append(CCFLAGS = targetFlags[archInfo.cpu])

    # -fPIC option
    if platform not in ('cygwin', 'win32'):
        env.Append(CCFLAGS=['-fPIC'])

    OPTFLAGS_NONE = split('-O0')
    OPTFLAGS_DEBUG = split('-g')+OPTFLAGS_NONE
    OPTFLAGS_MEDIUM = split('-O2 -finline-functions') # -fkeep-inline-functions
    OPTFLAGS_HIGH = split('-O3 -finline-functions')
    OPTFLAGS_EXTREME = OPTFLAGS_HIGH

    opts = {
        'none' : OPTFLAGS_NONE,
        'debug' : OPTFLAGS_DEBUG,
        'medium' : OPTFLAGS_MEDIUM,
        'high' : OPTFLAGS_HIGH,
        'extreme' : OPTFLAGS_EXTREME
        }

    if opts.has_key(optMode):
        env.Append(CCFLAGS = opts[optMode])
    else:
        # medium optimization per default
        env.Append(CCFLAGS = opts['medium'])

    if optimizeCode:
        # TODO: ALLOW_RESTRICT is unused, maybe remove
        #env.Append(CPPDEFINES = split('ALLOW_RESTRICT'))
        pass

    if warningsMode:
        env.Append(CCFLAGS = ['-Wall', ])

    if debugSymbols:
        # produce debug symbols
        env.AppendUnique(CCFLAGS = ['-g'])

    if not debugMacro:
        # disable debugging macros
        env.AppendUnique(CPPDEFINES = ['NDEBUG'])

    if profileMode:
        env.AppendUnique(CCFLAGS = ['-g'])
        env.AppendUnique(CCFLAGS = ['-pg'])
        env.AppendUnique(LINKFLAGS = ['-pg'])

    # Deactivate GCC compiler warnings (need to do this always after -Wall)
    env.Append(CCFLAGS = '-Wno-unknown-pragmas')


def SetupMsvcCompiler(env):
    compiler = env['compiler']
    assert compiler == 'MSVC'
    
    print '* Setup %s compiler' % compiler

    CC = ARGUMENTS.get('CC')
    CXX = ARGUMENTS.get('CXX')

    archInfo = getArchInfo(env)
    optMode = env['optimization']
    warningsMode = env['warnings'] # False/True
    debugMode = env['debug']       # 'no' / 'symbols' / 'output' / 'full'
    profileMode = env['profile']   # False/True
    platform = env['PLATFORM']
    isWin32 = (platform == 'win32')
    msvcCompilerDir = env['msvc_compiler_dir']
    
    # analyize optimization modes
        
    optimizeCode = (optMode not in ('none', 'debug'))

    # analyize debug modes
    debugSymbols = False
    debugMacro = False
    
    if optMode == 'debug':
        debugSymbols = True
        debugMacro = True
    elif optMode == 'none':
        debugMacro = True
        debugSymbols = False

    if debugMode == 'symbols':
        debugSymbols = True
    elif debugMode == 'macro':
        debugMacro = True
    elif debugMode == 'full':
        debugSymbols = True
        debugMacro = True

    customLinker = True

    assert isWin32 # ??? may be later test on win64 ???
    
    env['ENV'] = os.environ

    # setup MSVC tool chain
    for tool in ('mslink', 'msvs', 'masm', 'mslib'):
        env.Tool(tool)

    setupMsvcTool(env, msvcCompilerDir, toolName='msvc')

    # Deactivate MSVC compiler warnings
    #env.Append(CCFLAGS=split('')) # /wd<n>

    # --------------------------------------------
    # architecture dependent flags for various processor platforms

    genericArchFlags = {
        ARCH_X86 : [],
        ARCH_X86_64 : [], # '/arch:SSE2' seems to be obsolete
        ARCH_IA64 : []
        }
    genericArchFlag = genericArchFlags.get(archInfo.arch, [])

    targetFlags = {
        CPU_GENERIC   : genericArchFlag,
        CPU_NATIVE    : genericArchFlag,
        CPU_PENTIUM_3 : [],
        CPU_PENTIUM_4 : ['/arch:SSE2'],
        CPU_PENTIUM_M : ['/arch:SSE2'],
        CPU_CORE      : ['/arch:SSE2'],
        CPU_CORE_2    : ['/arch:SSE2'],
        CPU_OPTERON   : ['/arch:SSE2'],
        CPU_ITANIUM   : []
        }

    if optimizeCode and targetFlags.has_key(archInfo.cpu):
        env.Append(CCFLAGS = targetFlags[archInfo.cpu])
    
    # /fp:fast

    OPTFLAGS_NONE = split('/Od /FD /EHsc /MD /GR /Gd')
    OPTFLAGS_DEBUG = split('/Od /FD /EHsc /RTC1 /MDd /GR /Zi /Gd /vmv /vmg')
    OPTFLAGS_MEDIUM = split('/GR /O2 /Ob2 /Ot /Oy /EHsc /MD /Zp16 /Zc:forScope /Gd')
    OPTFLAGS_HIGH = OPTFLAGS_MEDIUM
    OPTFLAGS_EXTREME = OPTFLAGS_HIGH

    opts = {
        'none' : OPTFLAGS_NONE,
        'debug' : OPTFLAGS_DEBUG,
        'medium' : OPTFLAGS_MEDIUM,
        'high' : OPTFLAGS_HIGH,
        'extreme' : OPTFLAGS_EXTREME
        }

    if opts.has_key(optMode):
        env.Append(CCFLAGS = opts[optMode])
    else:
        # medium optimization per default
        env.Append(CCFLAGS = opts['medium'])

    if optimizeCode:
        env.AppendUnique(CPPDEFINES = ['NDEBUG'])

    # linking flags
    env.Replace(LINKFLAGS = split('/nologo /SUBSYSTEM:CONSOLE $MSLINKFLAGS'))

    if warningsMode:
        env.AppendUnique(CCFLAGS = ['/W1'])

    if debugSymbols:
        # produce debug symbols
        env.AppendUnique(CCFLAGS = ['/Zi'])
        env.AppendUnique(LINKFLAGS = ['/DEBUG'])


RegisterCompiler('INTEL', SetupIntelCompiler)
RegisterCompiler('INTEL_NOGCC', SetupIntelCompiler)
RegisterCompiler('GCC', SetupGccCompiler)
RegisterCompiler('MSVC', SetupMsvcCompiler)
SetDefaultCompilerName('GCC')

# Architectures

# archSuffixDict dictionary map between scons's platform and 
# architecture suffix def. If scons's platform is not in the dict, 
# 'default' mapping will be used instead.

ARCH_SUFFIX_DICT = {
    'default' : 'POSIX',
    'win32' : 'WINDOWS',
    'os2' : 'OS2',
    'darwin' : 'MACOSX'
    }

def SetupArch(env):
    global ARCH_SUFFIX_DICT

    arch = env['arch']
    platform = env['PLATFORM']
    staticlibs = env['staticlibs']
    projPrefix = getProjectPrefix(env)
    archPrefix = getProjectSystemPrefix(env)
    
    print '* Setup %s architecture on platform %s' % (arch, platform)

    platformDef = archPrefix + ARCH_SUFFIX_DICT.get(platform, 
                                                    ARCH_SUFFIX_DICT['default'])
    if not env.AddConfigKey(platformDef, 1):
        env.Append(CPPDEFINES=[platformDef])

    if staticlibs:
        if not env.AddConfigKey(key, 1):
            env.Append(CPPDEFINES=[key])

    archInfo = getArchInfo(env)

    if archInfo.arch == ARCH_X86:
        env.Replace(TARGET_ARCH_SUFFIX = 'IA32') #??? change it to X86
        env.Append(CPPDEFINES = ['ARCH_X86'])          # remove ?
    elif archInfo.arch == ARCH_X86_64:
        env.Replace(TARGET_ARCH_SUFFIX = 'X64')  #??? change it to X86_64
        env.Append(CPPDEFINES = ['ARCH_X86_64'])
        
        # Check for INTEL Compiler as combination of INTEL/Opteron
        # causes problems when including C++'s <cmath> header file
        if env['compiler'] in ('INTEL', 'INTEL_NOGCC'):
            key = projPrefix+'USE_MATH_H'
            if not env.AddConfigKey(key, 1):
                env.Append(CPPDEFINES=[key])

        # Check for SuSE system, as it causes problems
        # on Opterons
        if os.path.exists('/etc/SuSE-release'):
            fd = open('/etc/SuSE-release', 'r')
            content = fd.read()
            fd.close()
            if 'X86-64' in content:
                print '*** Warning: SuSE X86-64 system found, -i-static disabled'
                env.Replace(LINKFLAGS = filterOut('-i-static', env['LINKFLAGS']))
            del fd
            del content
    elif archInfo.arch == ARCH_IA64:
        env.Replace(TARGET_ARCH_SUFFIX = 'IA64')
        env.Append(CPPDEFINES = ['ARCH_IA64'])  # remove ?
        if env['compiler'] == 'INTEL_NOGCC':
            env.Append(LINKFLAGS = split('-static-libcxa -rdynamic -i-static'))

# Register architectures

for archName in ARCH_NAME_LIST:
    RegisterArchitecture(archName, SetupArch)
    # register aliases of a given archName
    for archAlias in ARCH_ALIASES[archName]:
        RegisterArchitectureAlias(archAlias, archName)

SetDefaultArchitectureName('x86')

# Register supported CPU names
for cpuName in CPU_NAME_LIST:
    RegisterCPU(cpuName)

SetDefaultCPUName('generic')

# Load all additional configuration modules

loadModules(os.path.join(os.path.dirname(__file__), 'modules'))

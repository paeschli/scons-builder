#-*- Python -*-
# SCons Builder Engine V2.23

# NOTE: This file is executed by the bootstrap loader in the context of
#       the project root directory.

EnsureSConsVersion(1, 2, 0)

import os
import os.path
import sys

from builder.btools import *
import builder.bconfig
import builder.bversion

print '* SB Engine version: %s' % builder.bversion.SB_ENGINE_VERSION
print '* Using SCons version:', GetSConsVersion()

# Get host architecture and use it as default

arch = GetArchitectureId()

if not arch:
    arch = 'x86'

print '* Detected architecture:', arch

if IsArchitectureSupported(arch):
    SetDefaultArchitectureName(arch)
else:
    print '* Detected architecture %s is not supported, x86 will be used when no specified' % arch
    SetDefaultArchitectureName('x86')

# Print platform information

defaultPlatform = Platform()
allowedPlatforms = ('posix', 'cygwin', 'win32', 'irix', 'sunos',
                    'hpux', 'aix', 'darwin', 'os2')

print '* Detected platform:',defaultPlatform

# Determine platform to use for build

platform = ARGUMENTS.get('PLATFORM', defaultPlatform)

# Determine target architecture to use for build

# target_arch argument is an alias for arch command line variable
# arch takes precedence over target_arch

arch = ARGUMENTS.get('arch', ARGUMENTS.get('target_arch', arch))

if re.match('[aA]md64|AMD64|x64|x86_64', arch):
    arch = 'x86_64'
elif re.match('ia32|IA32|[xX]86|[iI]386', arch):
    arch = 'x86'
elif re.match('armv[1-7]l', arch):
    arch = 'arm'

if not IsArchitectureSupported(arch):
    print 'Selected unsupported target architecture:', arch
    Exit(1)

print '* Selected target architecture:', arch

# Determine build directory

buildDir = ARGUMENTS.get('build', 'build')

while os.path.islink(buildDir):
    # resolve symbolic links
    buildDir = os.path.join(os.path.dirname(buildDir), os.readlink(buildDir))

# Create build directory, inclusive all intermediate-level directories if
# it does not exists
if not os.path.isdir(buildDir):
    if os.path.exists(buildDir):
        print '%s is not a directory' % buildDir
        Exit(1)
    else:
        os.makedirs(buildDir)

# Setup initial environment

if os.path.isabs(buildDir):
    BUILD_DIR = buildDir
else:
    BUILD_DIR = '#' + buildDir

OBJ_DIR = BUILD_DIR + os.sep + 'obj'

env = Environment(platform=platform,
                  TARGET_ARCH=arch,
                  tools=['gnulink', 'ar', 'subst'],
                  toolpath=['builder/scons_tools'],
                  BUILD_DIR=BUILD_DIR,
                  OBJ_DIR=OBJ_DIR)

# setup variables coming from multiple sources
#
# arch can be set from arch and target_arch arguments.
env.Replace(arch=arch)
ARGUMENTS['arch'] = arch

# Update external environment
for varName in ('PATH', 'LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH'):
    if os.environ.has_key(varName):
        value = os.environ[varName]
        argName = varName.lower()
        newValue = ARGUMENTS.get(argName)
        if newValue is not None:
            print '* Overriding environment variable %s with %s' % (varName, newValue)
            value = newValue
        env.AppendENVPath(varName, value)

# put all .sconsign files into a big one
env.SConsignFile(Dir(BUILD_DIR).abspath + os.sep + '.sconsignatures')

print '* Selected build platform:', env['PLATFORM']
print '* Selected build directory:', buildDir

# Load project file

loaded = False
for f in ('SConsProject', 'Sconsproject', 'sconsproject'):
    if os.path.exists(f):
        print '* Loading project file:', f
        SConscript(f, exports={'init_env' : env})
        loaded = True
        break
if not loaded:
    print >>sys.stderr, 'Error: Could not find SConsProject file'
    Exit(1)

# Load configuration variables

# In <buildDir>/build.conf are cached variables of the last run
variablesCacheFile = os.path.join(buildDir, 'build.conf')

# Get list of additional configuration files
configFiles = ARGUMENTS.get('config', None)
if configFiles:
    configFiles = configFiles.split(os.pathsep)
else:
    configFiles = []

VARIABLES_FILES = [variablesCacheFile] + configFiles

ALL_VARIABLES = [
    ('CC', 'The C compiler.'),
    ('CXX', 'The C++ compiler.'),
    EnumVariable('compiler', 'select compiler configuration',
                 GetDefaultCompilerName(),
                 allowed_values=GetCompilerNames()),
    EnumVariable('arch', 'select target architecture configuration',
                 GetDefaultArchitectureName(),
                 allowed_values=GetArchitectureNames()),
    EnumVariable('cpu', 'select CPU for CPU-specific optimization',
                 GetDefaultCPUName(),
                 allowed_values=GetCPUNames()),
    EnumVariable('PLATFORM', 'select target platform',
                 str(defaultPlatform),
                 allowed_values=allowedPlatforms),
    EnumVariable('optimization', 'optimization mode', 'medium',
                 allowed_values=('debug', 'none', 'medium', 'high', 'extreme')),
    BoolVariable('warnings', 'compilation with -Wall and similar', 1),
    EnumVariable('debug', 'debug symbols and macros (macro option disables NDEBUG)', 'no',
                 allowed_values=('no', 'symbols', 'macro', 'full'),
                 map={}, ignorecase=0), # case sensitive
    ('prefix', 'Installation prefix directory', '/usr/local'),
    ('libpath',
     'Additional library paths to use (separated by \''+os.pathsep+'\')'),
    ('cpppath',
     'Additional include paths to use (separated by \''+os.pathsep+'\')'),
    ('path',
     'Override system search paths (separated by \''+os.pathsep+'\')'),
    ('ccflags', 'Additional C/C++ flags to use (separated by spaces)'),
    ('cxxflags', 'Additional C++ flags to use (separated by spaces)'),
    ('linkflags', 'Additional linker flags to use (separated by spaces)'),
    BoolVariable('profile', 'compile and link with -pg option (gprof)', 0),
    BoolVariable('staticlibs', 'create static instead of dynamic libraries', 0),
    PackageVariable('gnuwin32', 'path to gnuwin32 package', 'no'),
    PackageVariable('mingw', 'path to MinGW package', 'no'),
	('project_name', 'Set Visual Studio project name', 'msvs')
    ]

# Append all user defined variables (see builder/bconfig.py)

ALL_VARIABLES.extend(GetCustomVariables())

def GetVariableNames(optlist, exclude_variables=[]):
    return [o[0] for o in optlist if o[0] not in exclude_variables]

# Load cached variables

print '* Loading configuration files:',' '.join(VARIABLES_FILES)

VARIABLES_TO_CACHE = GetVariableNames(ALL_VARIABLES)

# In CACHED_VARIABLES are all variables saved last time in the cache
CACHED_VARIABLES = LoadConfigVariables([variablesCacheFile], VARIABLES_TO_CACHE)
env.Replace(CACHED_VARIABLES=CACHED_VARIABLES)

# In CONFIG_FILE_VARIABLES are all variables loaded from external config file
CONFIG_FILE_VARIABLES = LoadConfigVariables(configFiles, VARIABLES_TO_CACHE)
env.Replace(CONFIG_FILE_VARIABLES=CONFIG_FILE_VARIABLES)

# In SPECIFIED_VARIABLES are put all variables specified over different sources:
# cache, command-line arguments, and finally user config file.
# Order of the updating is important: cached variables are overwritten by
# variables from config file, which again are overwritten by command-line
# arguments.

SPECIFIED_VARIABLES = {}
SPECIFIED_VARIABLES.update(CACHED_VARIABLES)
SPECIFIED_VARIABLES.update(CONFIG_FILE_VARIABLES)
SPECIFIED_VARIABLES.update(ARGUMENTS)
env.Replace(SPECIFIED_VARIABLES=SPECIFIED_VARIABLES)

# Print cached variables if showconf is specified
if 'showconf' in COMMAND_LINE_TARGETS:
    def printVariables(optdict):
        for k, v in optdict.items():
            print '%s = %s' % (k,repr(v))
        
    print '==== Cached variables ===='
    printVariables(CACHED_VARIABLES)
    print '==== Config file variables ===='
    printVariables(CONFIG_FILE_VARIABLES)
    print '==== Specified variables ===='
    printVariables(SPECIFIED_VARIABLES)
    Exit(0)

# Setup variables
opts = Variables(None, SPECIFIED_VARIABLES)
apply(opts.AddVariables, ALL_VARIABLES)
opts.Update(env)

# Generate help
Help("""
---- Command-line variable=value variables ----

config: Additional configuration files (separated by '%(pathsep)s').
        Variables from the configuration files will be stored in the cache.

build: Build directory.
""" % {'pathsep' : os.pathsep})

Help(opts.GenerateHelpText(env))

Help("""
Use cpppath+="PATH" and libpath+="PATH" for adding additional paths to the cache.
Use cpppath-="PATH" and libpath-="PATH" for removing paths from the cache.

Similarily for ccflags, cxxflags and linkflags.

---- Command-line targets ----

showconf:       Print cached variables.
showsources:    Print paths of all source and header files used for building to stderr.
                Paths are relative to the directory where SConstruct file is located.
msvsproject:    Creates MSVS project file with the name specified in variable 'project_name'.
                Command line options for Debug and Release variants of a project are specified in this form:
                project_<Variant>_<OptionName>=<OptionValue>
                e.g.
                project_Release_cpppath="C:\Include"
""")

print '* Selected optimization mode:', env['optimization']

# Misc environment setup

if env['staticlibs']:
    print '* Building and linking statically'
else:
    print '* Building and linking dynamically'

if env['gnuwin32']:
    env.Append(CPPPATH=env['gnuwin32']+os.sep+'include')
    env.Append(LIBPATH=env['gnuwin32']+os.sep+'lib')
    env.AppendENVPath('PATH', env['gnuwin32']+os.sep+'bin')

if env['mingw']:
    env.AppendENVPath('PATH', env['mingw']+os.sep+'bin')

# paths to the libraries instaled by macports
if env['PLATFORM'] == 'darwin':
    env.Append(CPPPATH = ['/opt/local/include'])
    env.Append(LIBPATH = ['/opt/local/lib'])

# check for 'XXX+=YYY' arguments for every pathvar,
# and append path YYY to environment variable XXX
# the same for 'XXX-=YYY' but remove YYY from XXX instead

for pathVar in ('libpath', 'cpppath'):
    pathToAppend = ARGUMENTS.get(pathVar+'+')
    pathToRemove = ARGUMENTS.get(pathVar+'-')

    varValue = env.get(pathVar, '')
    
    if pathToAppend:
        varValue = AppendPath(varValue, pathToAppend)
    if pathToRemove:
        varValue = RemovePath(varValue, pathToRemove)

    env[pathVar] = varValue


for flagsVar in ('ccflags', 'cxxflags', 'linkflags'):
    flagsToAppend = ARGUMENTS.get(flagsVar+'+')
    flagsToRemove = ARGUMENTS.get(flagsVar+'-')

    varValue = env.get(flagsVar, '')
    
    if flagsToAppend:
        varValue = ' '.join(varValue.split() + flagsToAppend.split())
    if flagsToRemove:
        flagsToRemove = flagsToRemove.split()
        flags = varValue.split()
        newFlags = [f for f in flags if f not in flagsToRemove]
        varValue = ' '.join(newFlags)

    env[flagsVar] = varValue

try:
    env = env.SetupEnvironment()
finally:
    # Save current configuration
    opts.Save(variablesCacheFile, env)

# Print all source files if showsources target is specified
if 'showsources' in COMMAND_LINE_TARGETS:

    # We need to build all dependencies and output
    # all collected source files so we alias showsources to
    # default targets.
    env.Alias('showsources', DEFAULT_TARGETS)
    # In order to avoid real building we activate dry-run/no_exec mode.
    env.SetOption('no_exec', True)

    def printSources():
        src = env.FindSourceFiles()

        # filter out all auto-generated files
        src = [f for f in src if os.path.exists(f.srcnode().abspath)]
        for f in src:
            print >>sys.stderr, str(f)

    # printSources will be executed when SCons exits
    import atexit
    atexit.register(printSources)
elif 'msvsproject' in COMMAND_LINE_TARGETS:
    import builder.msvs_proj_gen
    env.Alias('msvsproject', DEFAULT_TARGETS)
    # In order to avoid real building we activate dry-run/no_exec mode.
    env.SetOption('no_exec', True)

    def makeProject(env):
        all_sources = env.FindSourceFiles()
        env = env.Clone()
        sources = []
        includes = []
        misc = []
        for f in all_sources:
            if not os.path.exists(f.srcnode().abspath):
                continue
            path = f.srcnode().path
            added = False
            for ext in ('.cpp', '.c', '.C', '.cxx'):
                if path.endswith(ext):
                    sources.append(path)
                    added = True
                    break
            if added:
                continue
            for ext in ('.h', '.hpp', '.H', '.hxx'):
                if path.endswith(ext):
                    includes.append(path)
                    added = True
                    break
            if added:
                continue
            misc.append(path)
        path = os.environ['PATH']
        #tmp = []
        #for p in path.split(os.pathsep):
        #    if ' ' in p:
        #        tmp.append('"'+p+'"')
        #    else:
        #        tmp.append(p)
        #path = os.pathsep.join(tmp)
        #del tmp

        if env['TARGET_ARCH'] in ('x86', 'i386'):
            variant_platform = 'Win32'
        elif env['TARGET_ARCH'] in ('amd64', 'emt64', 'x86_64'):
            variant_platform = 'x64'
        elif env['TARGET_ARCH'] in ('ia64'):
            variant_platform = 'Itanium'
        else:
            variant_platform = env['TARGET_ARCH']
        variant = ['Debug', 'Release']
        buildtarget = []
        runfile = []
        for v in variant:
            argkey = 'project_'+v+'_'
            opts = {}
            opts['compiler'] = ARGUMENTS.get(argkey+'compiler', env['compiler'])
            opts['MSVC_VERSION'] = ARGUMENTS.get(argkey+'MSVC_VERSION', env['MSVC_VERSION'])
            if v == 'Debug':
                opts['optimization'] = ARGUMENTS.get(argkey+'optimization', 'debug')
            else:
                opts['optimization'] = ARGUMENTS.get(argkey+'optimization', 'high')
            for k, v in ARGUMENTS.items():
                if k.startswith(argkey):
                    param = k[len(argkey):]
                    opts[param] = v
            tmp = []
            for key, value in opts.items():
                tmp.append('%s="%s"' % (key, value))
            buildtarget.append(' '.join(tmp))
            runfile.append('')

        if 'MSVS_VERSION' in env:
            version_num, suite = builder.msvs_proj_gen.msvs_parse_version(env['MSVS_VERSION'])
        else:
            (version_num, suite) = (7.0, None) # guess at a default
        if 'MSVS' not in env:
            env['MSVS'] = {}
        if (version_num < 7.0):
            env['MSVS']['PROJECTSUFFIX']  = '.dsp'
            env['MSVS']['SOLUTIONSUFFIX'] = '.dsw'
        elif (version_num < 10.0):
            env['MSVS']['PROJECTSUFFIX']  = '.vcproj'
            env['MSVS']['SOLUTIONSUFFIX'] = '.sln'
        else:
            env['MSVS']['PROJECTSUFFIX']  = '.vcxproj'
            env['MSVS']['SOLUTIONSUFFIX'] = '.sln'

        if (version_num >= 10.0):
            env['MSVSENCODING'] = 'utf-8'
        else:
            env['MSVSENCODING'] = 'Windows-1252'

        env['GET_MSVSPROJECTSUFFIX']  = builder.msvs_proj_gen.GetMSVSProjectSuffix
        env['GET_MSVSSOLUTIONSUFFIX']  = builder.msvs_proj_gen.GetMSVSSolutionSuffix
        env['MSVSPROJECTSUFFIX']  = '${GET_MSVSPROJECTSUFFIX}'
        env['MSVSSOLUTIONSUFFIX']  = '${GET_MSVSSOLUTIONSUFFIX}'
        env['SCONS_HOME'] = os.environ.get('SCONS_HOME')

        msvsProject = str(env.File('#/'+env['project_name']+env['MSVSPROJECTSUFFIX']))
        msvsSolution = str(env.File('#/'+env['project_name']+env['MSVSSOLUTIONSUFFIX']))

        env2 = env.Clone(
                    MSVSSCONS='PATH=%s && "%s" "%s"' % (path, sys.executable, sys.argv[0]),
                    MSVSSCONSCOM='$MSVSSCONS $MSVSSCONSFLAGS',
                    MSVSBUILDCOM='$MSVSSCONSCOM $MSVSBUILDTARGET',
                    MSVSREBUILDCOM='$MSVSSCONSCOM -r $MSVSBUILDTARGET',
                    MSVSCLEANCOM='$MSVSSCONSCOM -c $MSVSBUILDTARGET',
                    projects=[msvsProject],
                    srcs=sources,
                    incs=includes,
                    misc=misc,
                    runfile=runfile,
                    variant=[v+'|'+variant_platform for v in variant],
                    buildtarget=buildtarget)
        builder.msvs_proj_gen.GenerateProject(
            target=[env2.File(msvsProject),
                    env2.File(msvsSolution)],
            source=None,
            env=env2)
    # makeProject will be executed when SCons exits
    import atexit
    atexit.register(lambda: makeProject(env))

# Activate logging

#logfile = open('log.txt', 'w')

#def log_cmd_line(s, target, source, env):
#  sys.stdout.write(s + "\n")
#  logfile.write(s+"\n")

#env['PRINT_CMD_LINE_FUNC'] = log_cmd_line

# Dump configuration

if ARGUMENTS.has_key('dump'):
    envName = ARGUMENTS['dump']
    dumpKey = ARGUMENTS.get('dump_key')

    dumpEnv = globals()[envName]
    
    if not dumpKey:
        prefix = envName + '.Dictionary()'
        dumpKey = None
    else:
        prefix = envName + '.Dictionary( ' + dumpKey + ' )'
        
    dumpEnv.DumpEnv(key = dumpKey,
                    header = prefix + ' - start',
                    footer = prefix + ' - end')

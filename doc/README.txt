* SCons-Based Build System (SB Engine) *

You will need a SCons and Python installed. SB Engine require SCons v1.2.0
and higher.

This build system was tested with SCons version v1.2.0
and Python 2.5.x and 2.6.x. Older version of the engine were tested with
Python 2.3.4, 2.3.5, 2.4.1.

You can download SCons from http://www.scons.org/ and Python from
http://www.python.org/ .

SCons-based build system creates object files and binaries in the build
directories and not in the source code tree. This allow to create builds
with different compilers and options side by side without copying
the source code tree. The default build directory is "build", but you can
specify it on the command line e.g.:

scons build=build-gcc

Please note that SBEngine is built on top of the unmodified SCons build system,
you need to read SCons documentation first.

1. Main Options

You can get all supported options by running "scons -h" in the
source code directory where SConstruct file resides.
The main options are "compiler" and "arch",
which selects compiler and architecture for the build.

compiler : GCC | INTEL  | MSVC
arch     : x86 | x86_64 | ia64

Following command compiles source code with Intel's compiler for
64-bit Intel architecture :

> scons compiler=INTEL arch=x86_64

You can additionally override default names of the compiler tools,
which are selected by compiler=XXX option. e.g. :

> scons compiler=INTEL arch=x86_64 CXX=/my/path/to/icc CC=/my/path/to/icc

This can be helpful when your compiler is not at the standard location.

Debug mode can be activated by setting "optimization" option to "debug" value:

> scons compiler=GCC optimization=debug

All options are cached in the <build directory>/build.conf so when
you started first time:

> scons build=build-icc compiler=INTEL arch=x86_64 \
                        CXX=/my/path/to/icc CC=/my/path/to/icc

Next time you only need to run:

> scons build=build-icc

Because all other options will be automatically restored.

In order to cleanup your build you can run:

> scons -c

2. Compiler and linker options

You can adjust compiler and linker flags with options:

cpppath  : Additional include paths to use (separated by ':' on *nix, ';' on Windows)
libpath  : Additional library paths to use (separated by ':' on *nix, ';' on Windows)
ccflags  : Additional C/C++ flags to use (separated by spaces)
cxxflags : Additional C++ flags to use (separated by spaces)
linkflags: Additional linker flags to use (separated by spaces)

These options will modify following SCons environment variables:

Option       SCons variable
---------------------------
cpppath      CPPPATH
libpath      LIBPATH
ccflags      CCFLAGS
cxxflags     CXXFLAGS
linkflags    LINKFLAGS

All options will be cached, so you need only to type them once
for a specified build environment (build=build-dir).
Next time they will be restored from build-dir/build.conf cache.

As an extension specified options can be added to or removed from
already cached options:

Use option+="value" for adding additional values to the option in a cache.
Use option-="value" for removing values from the option in a cache.

e.g. cpppath+="PATH", cpppath-="PATH"

3. Compilation under Windows

You will need Visual Studio 2008 or 2010 or alternatively latest version
of MinGW/MSYS. Older versions of the engine were tested with
MS Visual C++ 2005 Express Edition (MSVC 8.0).

When executed from MSYS environment SCons will be able
to compile with GCC and MSVC specified as a compiler.

4. Troubleshooting

* When configuration tests fail you can get detailed information on what
happened looking in build-dir/config.log file.

* When you need to know contents of the environment that SCons uses for
building run:

scons dump=env

* When you need to know which configuration options SCons uses for building run:

scons showconf

* For creating project files for IDEs (e.g. Visual Studio, Eclipse) it might
be useful to get a list of all source files used in a build:

scons showsources

* SCons caches results of the configuration in order to avoid configuring
each time when you run it. Sometimes configuration changes in a way that
SCons cannot detect the change, e.g. you installed missing software package.
In this case you need to force reconfiguring by running scons with
option --config=force:

scons --config=force

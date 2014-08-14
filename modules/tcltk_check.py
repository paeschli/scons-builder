from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix

tclver_source = """
puts [info tclversion]
"""

def CheckTclTk(ctx, write_config_h=False, add_to_compiler_env=False):
    # TODO: make better identification, add library paths
    ctx.Message('Checking for Tcl/Tk... ')

    confprefix = getAutoconfPrefix(ctx.env)
    
    ctx.env.Replace(HAVE_TK=0)
    
    ret, tclVersion = ctx.TryAction('tclsh < $SOURCES > $TARGET',
                                    text = tclver_source,
                                    extension = '.tcl')
    tclVersion = tclVersion.strip()
    if ret:
        ret, tclLibPath = ctx.TryAction('tclsh < $SOURCES > $TARGET',
                                        text = 'puts $tcl_libPath',
                                        extension = '.tcl')
        if ret:
            if ctx.env['PLATFORM'] in ('cygwin', 'win32'):
                s = tclVersion.replace('.','')
                libTcl = 'tcl'+s
                libTk = 'tk'+s
                includeTcl = '' #???
                includeTk = '' #???
            else:
                libTcl = 'tcl'+tclVersion
                libTk = 'tk'+tclVersion
                includeTcl = '/usr/include/tcl'+tclVersion
                includeTk = '/usr/include/tk'+tclVersion

            savedVars = ctx.env.SaveVars('LIBS CPPPATH')

            # check Tcl
            ctx.env.Append(LIBS = [libTcl])
            ctx.env.Append(CPPPATH = [includeTcl])
            ret = ctx.TryLink("""
            #include <tcl.h>
            int main(int argc, char **argv) {
              Tcl_Interp *interp;
              interp = Tcl_CreateInterp();
              if (Tcl_Init(interp) == TCL_ERROR)
                return 1;
              return 0;
            }
            """, extension='.c')

            cppPath = []

            if ret:
                ctx.env.Replace(TCLVER = tclVersion)
                ctx.env.Replace(LIBTCL = libTcl)
                cppPath.append(includeTcl)

                ctx.env.DeclarePackage('tcl',
                                       trigger_libs=['tcl', libTcl],
                                       trigger_frameworks=['Tcl'],
                                       LIBS=[libTcl],
                                       CPPPATH=[includeTcl])

                key = confprefix+'HAVE_LIBTCL'
                if not (write_config_h and AddConfigKey(ctx, key, ret)):
                    # no config file is specified or it is disabled,
                    # use compiler options
                    if ret and add_to_compiler_env:
                        ctx.env.Append(CPPDEFINES=[key])

                # check Tk
                ctx.env.Append(LIBS = [libTk])
                ctx.env.Append(CPPPATH = [includeTk])
                ret = ctx.TryLink("""
                #include <tk.h>
                int main(int argc, char **argv) {
                  Tcl_Interp *interp;
                  interp = Tcl_CreateInterp();
                  if (Tcl_Init(interp) == TCL_ERROR)
                    return 1;
                  if (Tk_Init(interp) == TCL_ERROR)
                    return 1;
                  return 0;
                }
                """, extension='.c')
                
                if ret:
                    ctx.env.Replace(HAVE_TK=1)
                    ctx.env.Replace(TKVER = tclVersion)
                    ctx.env.Replace(LIBTK = libTk)
                    ctx.env.Replace(LIBTCLTK = ['$LIBTCL', '$LIBTK'])
                    cppPath.append(includeTk)

                    ctx.env.DeclarePackage('tk',
                                           dependencies='tcl',
                                           trigger_libs=['tk', libTk],
                                           trigger_frameworks=['Tk'],
                                           LIBS=[libTk],
                                           CPPPATH=[includeTk])

                    key = confprefix+'HAVE_LIBTK'
                    if not (write_config_h and AddConfigKey(ctx, key, ret)):
                        # no config file is specified or it is disabled,
                        # use compiler options
                        if ret and add_to_compiler_env:
                            ctx.env.Append(CPPDEFINES=[key])

                else:
                    ctx.Message('Warning: could not find Tk library. ')
                    if write_config_h:
                        AddConfigKey(ctx, confprefix+'HAVE_LIBTK', 0)
                ret = 1

            # restore saved environment vars
            ctx.env.RestoreVars(savedVars)

            # update CPPPATH
            if cppPath and add_to_compiler_env:
                ctx.env.Append(CPPPATH=cppPath)

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckTclTk', CheckTclTk)

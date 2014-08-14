import sys
import os.path
from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import filterOut

def CheckPython(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for Python Library... ')

    platform = ctx.env['PLATFORM']
    isWin32 = (platform == 'win32')

    try:
        import distutils.sysconfig
        python_cpppath = [distutils.sysconfig.get_python_inc()]
        libver = distutils.sysconfig.get_config_var('VERSION')
        if not libver:
            libver = distutils.sysconfig.get_python_version()
        if isWin32:
            if ctx.env.IsMSVC_Debug():
                python_libs = ['python'+libver+'_d']
            else:
                python_libs = ['python'+libver]
            python_libpath = [os.path.join(sys.exec_prefix, 'libs')]
        else:
            python_libs = ['python'+libver]
            python_libpath = [distutils.sysconfig.get_config_var('LIBDIR')]

    except ImportError:
        ctx.Message('No distutils package, use default paths')

        if isWin32:
            libver = sys.version[0]+sys.version[2]
            python_cpppath = [os.path.join(sys.exec_prefix, 'include')]
            python_libpath = [os.path.join(sys.exec_prefix, 'libs')]
            if ctx.env.IsMSVC_Debug():
                python_libs = ['python'+libver+'_d']
            else:
                python_libs = ['python'+libver]
        else:
            libver = sys.version[:3]
            python_cpppath = [os.path.join(sys.prefix, 'include', 'python'+libver)]
            if sys.prefix != sys.exec_prefix:
                python_cpppath.append(os.path.join(sys.prefix, 'include', 'python'+libver))
            python_libpath = []
            python_libs = ['python'+libver]

    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_PYTHON'
    
    compiler = ctx.env['compiler']
    platform = ctx.env['PLATFORM']

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS CPPPATH LIBPATH')

    ret = 0

    ctx.env.AppendUnique(CPPPATH = python_cpppath)
    ctx.env.AppendUnique(LIBPATH = python_libpath)

    code = """
    #include <Python.h>

    static PyObject *
    hello(PyObject *self, PyObject *args)
    {
      return NULL;
    }

    static PyMethodDef HelloMethods[] = {
      {"hello",  hello, METH_VARARGS, "hello function."},
      {NULL, NULL, 0, NULL}        /* Sentinel */
    };

    PyMODINIT_FUNC
    inithello(void)
    {
      PyObject *m;

      m = Py_InitModule("hello", HelloMethods);
      if (m == NULL)
        return;
    }

    // dummy main func
    int main(int argc, char **argv) { return 0; }
    """
    
    if python_libs:
        ctx.env.AppendUnique(LIBS=python_libs)
        ret = ctx.TryLink(code, extension='.c')
    else:
        ret = ctx.TryCompile(code, extension='.c')

    if ret:

        vars = {'CPPDEFINES' : [key],
                'LIBPATH' : python_libpath,
                'CPPPATH' : python_cpppath}

        ctx.env.Replace(PYTHON_INCLUDES=python_cpppath)
        ctx.env.Replace(PYTHON_LIBPATH=python_libpath)

        ctx.env.DeclarePackage('python',
                               LIBS=python_libs,
                               dependencies=[],
                               vars=vars,
                               trigger_libs=['python', 'Python'],
                               trigger_frameworks=['python', 'Python'])

        vars = vars.copy()
        vars['SHLIBPREFIX'] = ''
        
        if platform == 'win32':
            vars['SHLIBSUFFIX'] = '.pyd'

        ctx.env.DeclarePackage('python_module',
                               LIBS=python_libs,
                               dependencies=[],
                               vars=vars,
                               trigger_libs=['python_module',
                                             'PythonModule'],
                               trigger_frameworks=['python_module',
                                                   'PythonModule'])

        if python_libs:
            ctx.env.Replace(LIBPYTHON=python_libs)

    ctx.env.RestoreVars(savedVars)

    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])
    
    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckPython', CheckPython)

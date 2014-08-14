from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix

def CheckOpenGL(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for OpenGL... ')
    confprefix = getAutoconfPrefix(ctx.env)
    
    platform = ctx.env['PLATFORM']

    haveGL = ctx.env.GetPackage('gl')
    
    ret = 0

    code = """
    #include %s
    int main(int argc, char **argv) { 
      glVertex3f(0.0f, 0.0f, 0.0f);
      return 0;
    }
"""

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS')

    if platform == 'darwin':
        ctx.env.AppendUnique(FRAMEWORKS=['OpenGL'])
        glHeader = '<OpenGL/gl.h>'

        ret = ctx.TryLink(code % glHeader, extension='.c')
        
        if ret and not haveGL:
            ctx.env.DeclarePackage('gl', FRAMEWORKS=['OpenGL'],
                                   trigger_libs=['GL', 'gl', 'GLU', 'glu', 'OpenGL'],
                                   trigger_frameworks=['OpenGL'])
                
    elif platform == 'win32':
        glHeader = '<GL/gl.h>'

        code = """
    #ifndef NOMINMAX
    #   define NOMINMAX 1
    #endif
    #include <windows.h>

    #include %s
    int main(int argc, char **argv) { 
      glVertex3f(0.0f, 0.0f, 0.0f);
      return 0;
    }
"""
        
        ctx.env.AppendUnique(LIBS = ['opengl32', 'glu32', 'glut32'])

        ret = ctx.TryLink(code % glHeader, extension='.c')

        if ret and not haveGL:
            ctx.env.DeclarePackage('gl', LIBS=['opengl32', 'glu32'],
                                   trigger_libs=['GL', 'gl', 'GLU', 'glu', 'OpenGL'],
                                   trigger_frameworks=['OpenGL'])
    else:
        glHeader = '<GL/gl.h>'
        ctx.env.AppendUnique(LIBS = ['GL'])

        ret = ctx.TryLink(code % glHeader, extension='.c')

        if ret and not haveGL:
            ctx.env.DeclarePackage('gl',  LIBS=['GL'],
                                   trigger_libs=['GL', 'gl', 'OpenGL'],
                                   trigger_frameworks=['OpenGL'])

    ctx.env.RestoreVars(savedVars)

    if ret:
        ctx.env.Replace(GL_HEADER=glHeader)
        ctx.env.Replace(LIBGL=['GL'])

    key = confprefix+'HAVE_LIBGL'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckOpenGL', CheckOpenGL)

def CheckGLUT(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for GLUT... ')
    confprefix = getAutoconfPrefix(ctx.env)
    
    platform = ctx.env['PLATFORM']

    haveGL = ctx.env.GetPackage('gl')
    
    ret = 0

    code = """
    #include %s
    int main(int argc, char **argv) { 
      glutInit(&argc, argv);
      return 0;
    }
"""

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS')

    if platform == 'darwin':
        ctx.env.AppendUnique(FRAMEWORKS=['OpenGL', 'GLUT'])
        glutHeader = '<GLUT/glut.h>'
        ret = ctx.TryLink(code % glutHeader, extension='.c')
        if ret:
            if not haveGL:
                ctx.env.DeclarePackage('gl', FRAMEWORKS=['OpenGL'],
                                       trigger_libs=['GL', 'gl', 'OpenGL'],
                                       trigger_frameworks=['OpenGL'])
                
            ctx.env.DeclarePackage('glut', FRAMEWORKS=['GLUT'], 
                                   dependencies=['gl'],
                                   trigger_libs=['glut', 'GLUT'],
                                   trigger_frameworks=['GLUT'])
            
            ctx.env.Replace(GLUT_HEADER=glutHeader)
            ctx.env.Replace(LIBGLUT=['glut'])
        ctx.env.RestoreVars(savedVars)

    elif platform == 'win32':
        glutHeader = '<GL/glut.h>'
        ctx.env.AppendUnique(LIBS = ['opengl32', 'glu32', 'glut32'])
        ret = ctx.TryLink(code % glutHeader, extension='.c')
        if ret:
            if not haveGL:
                ctx.env.DeclarePackage('gl', LIBS=['opengl32', 'glu32'],
                                       trigger_libs=['GL', 'gl', 'OpenGL'],
                                       trigger_frameworks=['OpenGL'])
                
            ctx.env.DeclarePackage('glut', LIBS=['glut32'],
                                   dependencies=['gl'],
                                   trigger_libs=['glut', 'GLUT'],
                                   trigger_frameworks=['GLUT'])
            ctx.env.Replace(GLUT_HEADER=glutHeader)
            ctx.env.Replace(LIBGLUT=['glut'])
        ctx.env.RestoreVars(savedVars)
    else:
        glutHeader = '<GL/glut.h>'

        for glutlib in ('glut',):
            ctx.env.Append(LIBS = [glutlib, 'GL'])

            ret = ctx.TryLink(code % glutHeader, extension='.c')

            ctx.env.RestoreVars(savedVars)

            if ret:
                if not haveGL:
                    ctx.env.DeclarePackage('gl',  LIBS=['GL'],
                                           trigger_libs=['GL', 'gl', 'OpenGL'],
                                           trigger_frameworks=['OpenGL'])
                    
                ctx.env.DeclarePackage('glut', LIBS=[glutlib],
                                       dependencies=['gl'],
                                       trigger_libs=['glut', 'GLUT', glutlib],
                                       trigger_frameworks=['GLUT'])
                ctx.env.Replace(GLUT_HEADER=glutHeader)
                ctx.env.Replace(LIBGLUT=[glutlib, 'GL'])
                break

    key = confprefix+'HAVE_LIBGLUT'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckGLUT', CheckGLUT)

def CheckGLEW(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for GLEW... ')
    confprefix = getAutoconfPrefix(ctx.env)
    
    platform = ctx.env['PLATFORM']

    haveGL = ctx.env.GetPackage('gl')
    
    ret = 0

    code = """
    #include %s
    int main(int argc, char **argv) { 
      GLenum err = glewInit();
      return 0;
    }
"""

    savedVars = ctx.env.SaveVars('LIBS FRAMEWORKS')

    if platform == 'darwin':
        ctx.env.AppendUnique(FRAMEWORKS=['OpenGL', 'GLEW'])
        glewHeader = '<GL/glew.h>'
        ret = ctx.TryLink(code % glewHeader, extension='.c')
        
        if ret:
            if not haveGL:
                ctx.env.DeclarePackage('gl', FRAMEWORKS=['OpenGL'],
                                       trigger_libs=['GL', 'gl', 'OpenGL'],
                                       trigger_frameworks=['OpenGL'])
                
            ctx.env.DeclarePackage('glew', FRAMEWORKS=['GLEW'],
                                   dependencies=['gl'],
                                   trigger_libs=['glew', 'GLEW'],
                                   trigger_frameworks=['GLEW'])
    elif platform == 'win32':
        glewHeader = '<GL/glew.h>'
        glewLib = 'glew32'
        if(ctx.env['TARGET_ARCH'] == 'x86_64'):
            glewLib = 'glew64'

        ctx.env.AppendUnique(LIBS = ['opengl32', 'glu32', glewLib])
        
        ret = ctx.TryLink(code % glewHeader, extension='.c')
        if ret:
            if not haveGL:
                ctx.env.DeclarePackage('gl', LIBS=['opengl32', 'glu32'],
                                       trigger_libs=['GL', 'gl', 'OpenGL'],
                                       trigger_frameworks=['OpenGL'])
            ctx.env.DeclarePackage('glew', LIBS=[glewLib],
                                   dependencies=['gl'],
                                   trigger_libs=['glew', 'GLEW'],
                                   trigger_frameworks=['GLEW'])
    else:
        glewHeader = '<GL/glew.h>'
        ctx.env.AppendUnique(LIBS = ['GL', 'GLEW'])
        
        ret = ctx.TryLink(code % glewHeader, extension='.c')
        if ret:
            if not haveGL:
                ctx.env.DeclarePackage('gl',  LIBS=['GL'],
                                       trigger_libs=['GL', 'gl', 'OpenGL'],
                                       trigger_frameworks=['OpenGL'])
                
            ctx.env.DeclarePackage('glew', LIBS=['GLEW'],
                                   dependencies=['gl'],
                                   trigger_libs=['glew', 'GLEW'],
                                   trigger_frameworks=['GLEW'])
            
    ctx.env.RestoreVars(savedVars)

    if ret:
        ctx.env.Replace(GLEW_HEADER=glewHeader)
        ctx.env.Replace(LIBGLEW=['GLEW'])

    key = confprefix+'HAVE_LIBGLEW'
    if not (write_config_h and AddConfigKey(ctx, key, ret)):
        # no config file is specified or it is disabled, use compiler options
        if ret and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckGLEW', CheckGLEW)

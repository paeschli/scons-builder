import re
from SCons.Script import *

"""Adds SubstInFile builder, which substitutes the keys->values of SUBST_DICT
    from the source to the target.
    The values of subst_dict first have any construction variables expanded
    (its keys are not expanded).
    If a value of subst_dict is a python callable function, it is called and
    the result is expanded as the value.
    If there's more than one source and more than one target, each target gets
    substituted from the corresponding source.
"""

def do_subst_in_file(targetfile, sourcefile, dict):
    """Replace all instances of the keys of dict with their values.
    For example, if dict is {'%VERSION%': '1.2345', '%BASE%': 'MyProg'},
    then all instances of %VERSION% in the file will be replaced with 1.2345 etc.
    """
    try:
        f = open(sourcefile, 'rb')
        contents = f.read()
        f.close()
    except:
        raise SCons.Errors.UserError, "Can't read source file %s"%sourcefile
    for (k,v) in dict.items():
        contents = re.sub(k, v, contents)
    try:
        f = open(targetfile, 'wb')
        f.write(contents)
        f.close()
    except:
        raise SCons.Errors.UserError, "Can't write target file %s"%targetfile
    return 0 # success

def subst_in_file(target, source, env):
    if not env.has_key('subst_dict'):
        raise SCons.Errors.UserError, "SubstInFile requires subst_dict to be set."
    d = dict(env['subst_dict']) # copy it
    for (k,v) in d.items():
        if callable(v):
            d[k] = env.subst(v())
        elif SCons.Util.is_String(v):
            d[k]=env.subst(v)
        else:
            raise SCons.Errors.UserError, "SubstInFile: key %s: %s must be a string or callable"%(k, repr(v))
    for (t,s) in zip(target, source):
        return do_subst_in_file(str(t), str(s), d)

def subst_in_file_string(target, source, env):
    """This is what gets printed on the console."""
    return '\n'.join(['Substituting vars from %s into %s'%(str(s), str(t))
                      for (t,s) in zip(target, source)])

def subst_emitter(target, source, env):
    """Add dependency from substituted subst_dict to target.
    Returns original target, source tuple unchanged.
    """
    d = env['subst_dict'].copy() # copy it
    for (k,v) in d.items():
        if callable(v):
            d[k] = env.subst(v())
        elif SCons.Util.is_String(v):
            d[k]=env.subst(v)
    env.Depends(target, SCons.Node.Python.Value(d))
    return target, source

def generate(env):
    subst_action=SCons.Action.Action(subst_in_file, subst_in_file_string)
    env['BUILDERS']['SubstInFile'] = env.Builder(action=subst_action,
                                                 emitter=subst_emitter)

def exists(env):
    return True

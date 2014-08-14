from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.cpuinfo import *
import os.path

def CheckSSE3(ctx, write_config_h=False, add_to_compiler_env=False):
    ctx.Message('Checking for SSE3 availability... ')
    confprefix = getAutoconfPrefix(ctx.env)
    
    has_sse3 = cpu.has_sse3() is not None
    
    key = confprefix + 'HAVE_SSE3'
    if not (write_config_h and AddConfigKey(ctx, key, has_sse3)):
        # no config file is specified or it is disabled, use compiler options
        if has_sse3 and add_to_compiler_env:
            ctx.env.Append(CPPDEFINES=[key])
    
    ctx.Result(has_sse3)
        
    return has_sse3

RegisterCustomTest('CheckSSE3', CheckSSE3)

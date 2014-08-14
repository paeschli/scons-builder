from builder.btools import RegisterCustomTest

def CheckSwig(ctx):
    ctx.Message('Checking for SWIG... ')
    if ctx.env.WhereIs('swig'):
        res = 1
        ctx.env.Tool('swig')
    else:
        res = 0
    ctx.Result(res)
    return res

RegisterCustomTest('CheckSwig', CheckSwig)

from builder.btools import RegisterCustomTest

def CheckCoin(ctx):
    ctx.Message('Checking for Coin... ')
    ret, output = ctx.TryAction('coin-config --version')
    if ret:
        ctx.env.ParseConfig('coin-config --cflags --cxxflags --cppflags --ldflags')
    ctx.Result(ret)
    return ret

RegisterCustomTest('CheckCoin', CheckCoin)

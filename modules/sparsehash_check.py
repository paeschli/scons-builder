from builder.btools import RegisterCustomTest
from builder.btools import AddConfigKey
from builder.bconfig import getAutoconfPrefix
from builder.bconfig import filterOut

def CheckGoogleSparseHash(ctx, write_config_h=True, add_to_cppdefines=False):
    ctx.Message('Checking for Google\'s Sparse Hash... ')
    confprefix = getAutoconfPrefix(ctx.env)
    key = confprefix+'HAVE_GOOGLE_SPARSEHASH'

    haveHeaders = ctx.TryLink("""
            #include <google/dense_hash_map>
            #include <google/sparse_hash_map>
            int main(int argc, char** argv) {
                google::dense_hash_map<int, int> map1;
                google::sparse_hash_map<int, int> map2;

                return 0;
            }
            """, extension='.cpp')

    if not (write_config_h and AddConfigKey(ctx, key, haveHeaders)):
    # no config file is specified or it is disabled, use compiler options
        if haveHeaders and add_to_cppdefines:
            ctx.env.Append(CPPDEFINES=[key])

    ctx.Result(haveHeaders)
    return haveHeaders

RegisterCustomTest('CheckGoogleSparseHash', CheckGoogleSparseHash)

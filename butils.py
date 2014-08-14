import SCons.Util

class Version:

    def __init__(self, *args):
        """Either first argument is a string of digits separated by '.',
           list of ints, or there are multiple integer arguments.
        """
        self.value = ()
        if len(args):
            if isinstance(args[0], Version):
                self.value = list(args[0].value)
            if SCons.Util.is_Sequence(args[0]):
                self.value = map(int, args[0])
            elif SCons.Util.is_String(args[0]):
                self.value = map(int, args[0].strip().split('.'))
            else:
                self.value = map(int, args)

    def compatible(self, minVersion=None, maxVersion=None):
        """Checks if this version is compatible with specified
        min and max versions : minVersion <= self <= maxVersion"""

        if minVersion is not None and (self < minVersion):
            return False
        if maxVersion is not None and (self > maxVersion):
            return False
        return True

    def __cmp__(self, other):
        # -1 if self < other
        #  0 if self == other
        # +1 if self > other
        if not isinstance(other, Version):
            raise TypeError('not a Version type')
        a = self.value
        b = other.value
        # check that both a and b have the same length
        # when not fill it at the end with zeros
        # (1,2) vs (1,2,3) is the same as (1,2,0) vs (1,2,3)
        if len(a) < len(b):
            a = a + [0,] * (len(b)-len(a))
        elif len(a) > len(b):
            b = b + [0,] * (len(a)-len(b))
        assert len(a) == len(b)
        for i in xrange(len(a)):
            if a[i] < b[i]:
                return -1
            elif a[i] > b[i]:
                return 1
        return 0

    def __repr__(self):
        return 'Version(%s)' % repr(self.value)

    def __str__(self):
        return '.'.join(map(str, self.value))

def filterOut(patterns, textList):
    if isinstance(patterns, str):
        patterns = patterns.split()
    if isinstance(textList, str):
        textList = textList.split()
        rejoin = True
    else:
        rejoin = False

    res = filter(lambda i: i not in patterns, textList)
    if rejoin:
        res = ' '.join(res)
    return res

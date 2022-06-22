import sys
from functools import partial


class Console:
    stdout = partial(print, file=sys.stdout)
    stderr = partial(print, file=sys.stderr)


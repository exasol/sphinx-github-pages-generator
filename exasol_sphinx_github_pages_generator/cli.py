import sys
from functools import partial


class Console:
    stdout = click.echo
    stderr = partial(click.echo, err=True)


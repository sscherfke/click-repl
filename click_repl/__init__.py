import sys

import click

from .exceptions import InternalCommandException, ExitReplException
from .blocking import repl
if sys.version_info[:2] >= (3, 5):
    from .async import async_repl, repl_task
else:
    async_repl, repl_task = None, None


__all__ = [
    'register_repl',
    'repl',
    'InternalCommandException', 'ExitReplException',
]
if async_repl is not None:
    __all__ += ['async_repl', 'repl_task']


def register_repl(group, name='repl', async=False):
    """Register :func:`repl()` as sub-command *name* of *group*.

    If *async* is ``True`` it will use *asyncio* to create an asyncronous repl.
    This allows you to shedule background tasks from your commands (e.g.,
    timeouts).  This feature requires Python 3.5 or later.

    """
    if async and async_repl is None:
        raise RuntimeError('You need Python >= 3.5 for this feature to work.')

    func = async_repl if async else repl
    group.command(name=name)(click.pass_context(func))

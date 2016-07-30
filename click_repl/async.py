import asyncio
import sys

from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import prompt_async
import click
import click._bashcomplete
import click.parser

from .exceptions import ExitReplException
from .core import (
        ClickCompleter,
        dispatch_repl_commands,
        handle_internal_commands,
        invoke_command,
)


async def repl_task(old_ctx):
    """
    Start an interactive shell. All subcommands are available in it.

    You can also pipe to this command to execute subcommands.

    """
    # parent should be available, but we're not going to bother if not
    group_ctx = old_ctx.parent or old_ctx
    group = group_ctx.command
    isatty = sys.stdin.isatty()
    if isatty:
        history = InMemoryHistory()
        completer = ClickCompleter(group)

        async def get_command():
            command = await prompt_async(
                u'> ', completer=completer, history=history, patch_stdout=True)
            return command
    else:
        async def get_command():
            # See
            # https://stackoverflow.com/questions/29475007/python-asyncio-reader-callback-and-coroutine-communication
            # to make it not-blocking
            return sys.stdin.readline()

    while True:
        try:
            command = await get_command()
        except KeyboardInterrupt:
            continue
        except EOFError:
            break

        if not command:
            if isatty:
                continue
            else:
                break

        if dispatch_repl_commands(command):
            continue

        try:
            result = handle_internal_commands(command)
            if isinstance(result, str):
                click.echo(result)
                continue
        except ExitReplException:
            break

        invoke_command(command, group, group_ctx)


def async_repl(context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(repl_task(context))

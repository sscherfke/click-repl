import sys

from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import prompt
import click
import click._bashcomplete
import click.parser
import six

from .exceptions import ExitReplException
from .core import (
        ClickCompleter,
        dispatch_repl_commands,
        handle_internal_commands,
        invoke_command,
)


def repl(old_ctx):
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

        def get_command():
            return prompt(u'> ', completer=completer, history=history)
    else:
        get_command = sys.stdin.readline

    while True:
        try:
            command = get_command()
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
            if isinstance(result, six.string_types):
                click.echo(result)
                continue
        except ExitReplException:
            break

        invoke_command(command, group, group_ctx)

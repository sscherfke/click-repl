from collections import defaultdict
import os
import shlex

from prompt_toolkit.completion import Completer, Completion
import click
import click._bashcomplete
import click.parser
import six

from .exceptions import ExitReplException


_internal_commands = dict()


def _register_internal_command(names, target, description=None):
    if not hasattr(target, '__call__'):
        raise ValueError('Internal command must be a callable')

    if isinstance(names, six.string_types):
        names = [names]
    elif not isinstance(names, (list, tuple)):
        raise ValueError('"names" must be a string or a list / tuple')

    for name in names:
        _internal_commands[name] = (target, description)


def _get_registered_target(name, default=None):
    target_info = _internal_commands.get(name)
    if target_info:
        return target_info[0]
    return default


def _exit_internal():
    raise ExitReplException()


def _help_internal():
    formatter = click.HelpFormatter()
    formatter.write_heading('REPL help')
    formatter.indent()
    with formatter.section('External Commands'):
        formatter.write_text('prefix external commands with "!"')
    with formatter.section('Internal Commands'):
        formatter.write_text('prefix internal commands with ":"')
        info_table = defaultdict(list)
        for mnemonic, target_info in six.iteritems(_internal_commands):
            info_table[target_info[1]].append(mnemonic)
        formatter.write_dl(
            (', '.join((':{0}'.format(mnemonic)
                        for mnemonic in sorted(mnemonics))), description)
            for description, mnemonics in six.iteritems(info_table)
        )
    return formatter.getvalue()


_register_internal_command(['q', 'quit', 'exit'], _exit_internal,
                           'exits the repl')
_register_internal_command(['?', 'h', 'help'], _help_internal,
                           'displays general help information')


class ClickCompleter(Completer):
    def __init__(self, cli):
        self.cli = cli

    def get_completions(self, document, complete_event):
        # If ends in space, no completions are wished
        if document.text_before_cursor.rstrip() != document.text_before_cursor:
            return

        # Code analogous to click._bashcomplete.do_complete

        try:
            args = shlex.split(document.text_before_cursor)
        except ValueError:
            # Invalid command, perhaps caused by missing closing quotation.
            return

        incomplete = args.pop() if args else ''

        ctx = click._bashcomplete.resolve_ctx(self.cli, '', args)
        if ctx is None:
            return

        choices = []
        for param in ctx.command.params:
            if not isinstance(param, click.Option):
                continue
            for options in (param.opts, param.secondary_opts):
                for o in options:
                    choices.append(Completion(o, -len(incomplete),
                                              display_meta=param.help))

        if isinstance(ctx.command, click.MultiCommand):
            for name in ctx.command.list_commands(ctx):
                command = ctx.command.get_command(ctx, name)
                choices.append(Completion(
                    name,
                    -len(incomplete),
                    display_meta=getattr(command, 'short_help')
                ))

        for item in choices:
            if item.text.startswith(incomplete):
                yield item


def invoke_command(command, group, group_ctx):
    args = shlex.split(command)

    try:
        with group.make_context(None, args, parent=group_ctx) as ctx:
            group.invoke(ctx)
            ctx.exit()
    except click.ClickException as e:
        e.show()
    except SystemExit:
        pass


def dispatch_repl_commands(command):
    """Execute system commands entered in the repl.

    System commands are all commands starting with "!".

    """
    if command.startswith('!'):
        os.system(command[1:])
        return True

    return False


def handle_internal_commands(command):
    """Run repl-internal commands.

    Repl-internal commands are all commands starting with ":".

    """
    if command.startswith(':'):
        target = _get_registered_target(command[1:], default=None)
        if target:
            return target()

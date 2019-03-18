import asyncio
import logging

CR, LF, NUL = '\r\n\x00'


@asyncio.coroutine
def readline(reader, writer, show_ack=True, eol=CR+LF,
             hidden_ack=False, replace_ack_symbols_with='*'):
    """A very crude readline coroutine interface.
    This function is a :func:`~asyncio.coroutine`.

    It is a bit modified version of telnetlib3.server_shell.readline() function
    that can repeat user input when it gets the whole line, so it's some kind
    of ack. Ack content may be filled by any symbol if you want to hide it for
    some reason.

    For example, given the function call
        readline(reader, writer, hidden_ack=True, replace_ack_symbols_with='-')
    and user input 'test', user terminal will output something like this:
        > test
        ----
        >
    """
    command, inp, last_inp = '', '', ''
    inp = yield None
    while True:
        if inp in (CR, LF, NUL) and not command:
            # Skip special symbols at the left of input
            last_inp = inp
            inp = yield None

        elif inp in (LF, NUL) and last_inp == CR:
            last_inp = inp
            inp = yield None

        elif inp in (CR, LF):
            # first CR or LF yields command
            last_inp = inp

            if show_ack:
                if hidden_ack:
                    ack = replace_ack_symbols_with * len(command)
                else:
                    ack = command.upper()

                echo_data = eol + ack
                writer.echo(echo_data)
                log_echo(echo_data)

            inp = yield command
            command = ''

        elif inp in ('\b', '\x7f'):
            # backspace over input
            if command:
                command = command[:-1]

                echo_data = '\b \b'
                writer.echo(echo_data)
                log_echo(echo_data)
            last_inp = inp
            inp = yield None

        else:
            # buffer and echo input
            command += inp

            writer.echo(inp)
            log_echo(inp)

            last_inp = inp
            inp = yield None


def log_echo(data):
    logger = logging.getLogger('smdr_server.logger')

    logger.info('Echo: {}'.format(data.encode('ascii')))

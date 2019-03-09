import asyncio

CR, LF, NUL = '\r\n\x00'


@asyncio.coroutine
def readline(reader, writer, hide_input=False, hide_symbol='*'):
    """
    A very crude readline coroutine interface.
    This function is a :func:`~asyncio.coroutine`.

    It is a bit modified version of telnetlib3.server_shell.readline() function
    that support hidden user input, e.g. for getting password
    """
    command, inp, last_inp = '', '', ''
    inp = yield None
    while True:
        if inp in (LF, NUL) and last_inp == CR:
            last_inp = inp
            inp = yield None

        elif inp in (CR, LF):
            # first CR or LF yields command
            last_inp = inp

            inp = yield command
            command = ''

        elif inp in ('\b', '\x7f'):
            # backspace over input
            if command:
                command = command[:-1]
                writer.echo('\b \b')
            last_inp = inp
            inp = yield None

        else:
            # buffer and echo input
            command += inp

            echo_symbol = inp if not hide_input else hide_symbol
            writer.echo(echo_symbol)
            last_inp = inp
            inp = yield None

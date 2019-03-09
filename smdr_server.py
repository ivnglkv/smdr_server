import asyncio
import random
import telnetlib3

from telnetlib3.server_shell import readline

CR, LF, NUL = '\r\n\x00'


class SmdrSingleton(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        return cls.instance

    def getline(self):
        while True:
            with open('/tmp/lorem', 'r') as log_file:
                for line in log_file:
                    yield line


@asyncio.coroutine
def shell(reader, writer):
    command = None
    password = None

    writer.transport.set_write_buffer_limits(low=0, high=0)

    linereader = readline(reader, writer)
    linereader.send(None)

    s = SmdrSingleton()

    while True:
        if command:
            writer.write(CR + LF)
        writer.write('> ')
        command = None
        while command is None:
            # TODO: use reader.readline()
            inp = yield from reader.read(1)
            if not inp:
                return
            command = linereader.send(inp)
        writer.write(CR + LF)

        if command == 'q':
            writer.write('Goodbye.' + CR + LF)
            break
        elif command == 'help':
            writer.write('q, smdr')
        elif command == 'smdr':
            writer.write('Enter password: ')
            password = None
            while password is None:
                # TODO: hide password input
                inp = yield from reader.read(1)
                if not inp:
                    return
                password = linereader.send(inp)
            writer.write(CR + LF)

            if password.lower() == 'pccsmdr':
                for line in s.getline():
                    sleep_time = random.random() * 2
                    yield from asyncio.sleep(sleep_time)
                    writer.write(line + CR)
                    yield from writer.drain()
        elif command:
            writer.write('no such command.')
        else:
            writer.write('Goodbye' + CR + LF)
            break
    writer.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    coro = telnetlib3.create_server(port=6023, shell=shell)
    server = loop.run_until_complete(coro)
    loop.run_until_complete(server.wait_closed())

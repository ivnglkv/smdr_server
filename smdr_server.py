import asyncio
import getpass
import random
import re
import telnetlib3

from argparse import ArgumentParser

from utils import readline

CR, LF = '\r\n'


class SmdrSingleton(object):
    initialized = False

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, smdr_logfile=None, smdr_password=None, eol=CR+LF,
                 records_on_page=60, loglevel='warning'):
        if not self.initialized:
            self.logfile = smdr_logfile
            self.password = smdr_password
            self.eol = eol
            self.records_on_page = records_on_page
            self.header = ('  Date     Time    Ext CO        Dial Number      '
                           '  Ring Duration  Acc code  CD ' + self.eol +
                           '--------------------------------------------------'
                           '------------------------------')

            """Using logger creation function provided with telnetlib3
            because it's default log format meets our requirements"""
            self.logger = telnetlib3.accessories.make_logger(
                'smdr_server.logger', loglevel=loglevel)

            self.initialized = True

    def getline(self):
        i = self.records_on_page

        while True:
            with open(self.logfile, 'r') as log_file:
                for line in log_file:
                    # Print header after every self.records_on_page + 1 lines
                    if i % self.records_on_page == 0:
                        # Add empty line before every header except first one
                        if i != self.records_on_page:
                            yield ''
                        yield self.header
                    yield line
                    i += 1

    def log_input(self, input):
        self.logger.info('Got input {}'.format(input.encode('ascii')))

    def log_output(self, output):
        self.logger.info('Sent {}'.format(output.encode('ascii')))

    def write(self, writer, data):
        writer.write(data)
        self.log_output(data)


@asyncio.coroutine
def shell(reader, writer):
    command = None
    password = None

    writer.transport.set_write_buffer_limits(low=0, high=0)

    cmdreader = readline(reader, writer)
    cmdreader.send(None)

    s = SmdrSingleton()

    while True:
        if command:
            s.write(writer, s.eol)
        s.write(writer, '-')
        command = None
        while command is None:
            # TODO: use reader.readline()
            inp = yield from reader.read(1)
            if not inp:
                return
            command = cmdreader.send(inp)

        s.log_input(command)

        # Writing CR instead of EOL after command, because Panasonic
        # telnet interface is doing the same. It looks weird, but so life is
        s.write(writer, CR)

        if command == 'q':
            reply = 'Goodbye.' + s.eol
            s.write(writer, reply)
            break
        elif command == 'help':
            reply = 'q, smdr'
            s.write(writer, reply)
        elif command == 'smdr':
            reply = 'Enter Password:'

            s.write(writer, reply)

            password = None

            password_reader = readline(reader, writer, hidden_ack=True)
            password_reader.send(None)

            while password is None:
                inp = yield from reader.read(1)
                if not inp:
                    return
                password = password_reader.send(inp)

            s.log_input(password)
            s.write(writer, s.eol)

            if password.lower() == s.password:
                for line in s.getline():
                    sleep_time = random.random() * 2
                    yield from asyncio.sleep(sleep_time)
                    s.write(writer, re.sub('(\n|\r)*$', '', line) + s.eol)
                    yield from writer.drain()
        elif command:
            s.write(writer, 'No such command.')
        else:
            s.write(writer, 'Goodbye' + s.eol)
            break
    writer.close()


if __name__ == '__main__':
    parser = ArgumentParser(
        description='Fake SMDR server, purposed for testing SMDR analyzing '
                    'software. It feeds data to clients from sample file '
                    '(not included with program)')
    parser.add_argument('-f', '--file', required=True)
    parser.add_argument('-H', '--host', default='localhost')
    parser.add_argument('-P', '--port', type=int, default=2300)
    parser.add_argument('-p', '--password', action='store_true',
                        help='Read password from user input')
    parser.add_argument('-e', '--eol', choices=['CR', 'LF', 'CR+LF'],
                        default='CR+LF')
    parser.add_argument('-n', '--records_on_page', type=int, default=60)
    parser.add_argument('-v', '--loglevel', default='WARNING',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set logging level. Default is WARNING')

    args = parser.parse_args()

    if args.password:
        password = getpass.getpass()
    else:
        password = 'pccsmdr'

    eol_aliases = {
        'CR': '\r',
        'LF': '\n',
        'CR+LF': '\r\n',
    }

    if args.records_on_page <= 0:
        parser.error('number of records on page should be positive integer')

    s = SmdrSingleton(args.file, password,
                      eol_aliases[args.eol], args.records_on_page,
                      args.loglevel)

    """We need very big timeout because clients will be running
    for quite long period of time.
    This value will give us about 25 days of passing SMDR data to client.

    # TODO: This is not complete solution for this problem. Why telnetlib3
    counts timeout only on read operations? Successful write should
    reset timer too.
    Maybe there is a way to do it without patching telnetlib3"""
    timeout = 2147483
    loop = asyncio.get_event_loop()
    coro = telnetlib3.create_server(host=args.host, port=args.port,
                                    shell=shell, timeout=timeout)
    server = loop.run_until_complete(coro)

    s.logger.info('Created server on {}:{}, feeding SMDR file {}'.format(
              args.host, args.port, args.file))

    loop.run_until_complete(server.wait_closed())

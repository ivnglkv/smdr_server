# SMDR server

This is fake SMDR server, emulating Panasonic PBX SMDR server behavior. It
provides access to SMDR data over telnet. It can be used to test SMDR
analyzing software.

Calls data is taken from sample file. You can find examples with randomly generated data in `samples` folder.

## How to run

Minimum required Python version is 3.3

1. Install dependencies:  
`pip3 install -r requirements.txt`
2. Run server:  
`python3 smdr_server.py -f samples/sample1.log`

### Command-line options

`-f, --file` — path to sample log file. Required argument.  
`-H, --host` — server IP address. Default `localhost`  
`-P, --port` — default `2300`  
`-p, --password` — prompt for a password to change it
from default `pccsmdr`. Clients are prompted for this password
to access SMDR data.  
`-e, --eol` — EOL sequence. Choices are `CR`, `LF`, `CR+LF`.
Default is `CR+LF`.  
`-n, --records_on_page` — number of records per page. Pages are separated
by special headers.

## Usage

Telnet commands:

- `smdr` — get smdr data
- `q` — close connection
- `help` — show available commands

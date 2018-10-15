# mmquery

A command line utility for querying the MatterMost API for various auditing or reporting purposes.

## Quick setup

```bash
apt install python3-pip
pip3 install git+https://github.com/haam3r/mmquery.git
```

## Install with virtualenv

```bash
git clone https://github.com/haam3r/mmquery.git
cd mmquery
virtualenv -p python3 venv
. venv/bin/activate
pip install --editable .
```

## Usage examples

Generate a personal access token to use from: Account Settings -> Security

```bash
# Search for user by string
mmquery --host mattermost.example.com --token 123abcdfeg user --term example

# Export posts from channel
mmquery --host mattermost.example.com --token 123abcdfeg posts --channel example --team team-name

# Export posts from channel, but also dump files from channel to current working directory
mmquery --host mattermost.example.com --token 123abcdfeg posts --channel example --team team-name --filedump

# Get members of a team
mmquery --host mattermost.example.com --token 123abcdfeg members --team example

# Send user audit reports per email domain(s)
mmquery --host mattermost.example.com --token 123abcdfeg report --managers managers.json --template message.txt --smtp-host mail.example.com
```

## Example config file

You can also use a config file to store the common config parameters. An example:

```bash
[Default]
host = mm.example.com
port = 443
token = 23abcdfeg
```
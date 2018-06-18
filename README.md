# mmquery

A command line utility for querying the MatterMost API for various auditing or reporting purposes.

## Quick setup

```bash
apt install python3-pip
git clone https://github.com/haam3r/mmquery.git
cd mmquery
pip install .
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
```
# mmquery

A command line utility for querying the MatterMost API for various auditing or reporting purposes.

## Quick setup

```bash
apt install python3-pip
pip3 install git+https://github.com/otmarlendl/mmquery.git
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
mmquery --host mattermost.example.com --token 123abcdfeg report --managers managers.json --template message.txt --smtp-host mail.example.com --source mm@example.com --admin mm+noadmin@example.com [--print]
```

## Example config file

You can also use a config file to store the common config parameters. An example:

```bash
[Default]
host = mm.example.com
port = 443
token = 23abcdfeg
```

## Example managers file

The managers file defines admins and their associated domains. Example:

```bash
{
  "admin@example.com": {
    "name": "Admin Example",
    "domain": [
                "example.com",
                "example.top",
                "example.info"
              ]
  },
  "manager@exampleorg.com": {
    "name": "Org Manager",
    "domain": [
                  "exampleorg.com"
                ]
  }
}
```

## Example massage file

```bash
Hi ${MANAGER_NAME},

I'm writing you on behalf of EXAMPLE ORG regarding MatterMost chat instance.
(Team ${TEAM_DISPLAY_NAME}, Description (${TEAM_DESCRIPTION})

I have you listed as the team rep for domain(s) "${DOMAIN}".
Please spare a minute or two and validate the users that belong to your domain.

Currently, these are your ${MEM_COUNT} users:

${USERS}

If any of these users should no longer have access to the EXAMPLE ORG chat team, please notify me via mm@example.com.
Additionally, for those who do not have a nickname set, please remind them to set one in their profile in format country_organization_name (cc_example_joe)
.

If you have any additional questions or comments, you can contact me directly via mm@example.com.

Regards
EXAMPLE ORG
```

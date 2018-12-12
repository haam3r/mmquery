import datetime
from string import Template


def convert_time(time):
    '''
    Convert from milliseconds since Unix epoch
    '''
    fmt = "%Y-%m-%d %H:%M:%S"
    if time == 0 or time == 1:
        return time
    else:
        # local time
        t = datetime.datetime.fromtimestamp(float(time)/1000.)
        return t.strftime(fmt)


def get_team(self, name):
    '''
    Get team by name
    '''
    team = self.teams.get_team_by_name(name)
    return team


def get_channel(self, name, team):
    '''
    Get channel by team id and name
    '''
    team_id = get_team(self, team)
    channel = self.channels.get_channel_by_name(team_id['id'], name)
    return channel


def get_nickname(self, id, full=False):
    '''
    Get user nickname from ID
    '''
    user = self.users.get_user(id)

    if full:
        return user

    if not user['nickname']:
        return user['username']

    return user['nickname']


def read_template(filename):
    '''
    Get email template file
    '''
    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)

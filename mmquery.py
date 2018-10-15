#!/usr/bin/python3

'''
Query posts and users over the MatterMost API.
Allows for searching a user by the username.
Exporting posts from a channel, optionally also export files from channel
Setup with virtualenv:
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
virtualenv -p python3 venv
. venv/bin/activate
pip install --editable .
'''

import sys
import logging
import math
import click
import abstract
from mattermostdriver import Driver

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='/tmp/mmquery.log', filemode='a')


# Set up an object to pass around click options
class Config(object):

    def __init__(self, connect):
        self.connect = connect
        self.config = {}

    def set_config(self, key, value):
        self.config[key] = value

    def __repr__(self):
        return '<Config %r>' % self.connect


pass_conf = click.make_pass_decorator(Config)

@click.group()
@click.option('--host', help='Hostname of MatterMost server')
@click.option('--token', help='Your personal access token')
@click.option('--port', default=443 ,help='Which port to use. Default is 443')
@click.version_option('1.0')
@click.pass_context
def cli(ctx, host, token, port):
    '''
    Main entry point for command line
    '''
    connect = Driver({'url': host, 'token': token, 'port': port})
    connect.login()
    ctx.obj = Config(connect)
    ctx.obj.set_config('host', host)
    ctx.obj.set_config('token', token)
    ctx.obj.set_config('port', port)


@cli.command()
@click.option('--channel', help='Name of channel')
@click.option('--team', help='Name of channel as it appears in the URL')
@click.option('--filedump',  is_flag=True, help='Also download posted files to current working directory')
@pass_conf
def posts(ctx, channel, team, filedump):
    '''
    Get posts from channel by channel name
    '''
    
    full = {}
    file_ids = []
    chan = abstract.get_channel(self=ctx.connect, name=channel, team=team)
    # Paginate over results pages if needed
    if chan['total_msg_count'] > 200:
        pages = math.ceil(chan['total_msg_count']/200)
        for page in range(pages):
            posts = ctx.connect.posts.get_posts_for_channel(chan['id'], params={'per_page': 200, 'page': page})
            try:
                full['order'].extend(posts['order'])
                full['posts'].update(posts['posts'])
            except KeyError:
                full['order'] = posts['order']
                full['posts'] = posts['posts']
    else:
        full = ctx.connect.posts.get_posts_for_channel(chan['id'], params={'per_page': chan['total_msg_count']})
    
    # Print messages in correct order and resolve user id-s to nickname or username
    for message in reversed(full['order']):
        time = abstract.convert_time(full['posts'][message]['create_at'])

        if full['posts'][message]['user_id'] in ctx.config:
            nick = ctx.config[full['posts'][message]['user_id']]
        else:
            nick = abstract.get_nickname(self=ctx.connect, id=full['posts'][message]['user_id'])
            # Let's store id and nickname pairs locally to reduce API calls
            ctx.config[full['posts'][message]['user_id']] = nick
        
        click.echo('{nick} at {time} said: {msg}'
                    .format(nick=nick,
                            time=time,
                            msg=full['posts'][message]['message']))
        
        if 'file_ids' in full['posts'][message]:
            file_ids.extend(full['posts'][message]['file_ids'])
    
    # If --filedump specified then download files
    if filedump:
        for id in file_ids:
            metadata = ctx.connect.files.get_file_metadata(id)
            file = ctx.connect.files.get_file(id)
            file_name = '{}_{}'.format(chan['name'], metadata['name'])
            click.echo('Downloading {}'.format(file_name))
            with open(metadata['name'], 'wb') as f:
                f.write(file.content)
    
    click.echo('Total number of messages: {}'.format(chan['total_msg_count']) )


@cli.command()
@click.option('--term', help='Find user based on some string')
@pass_conf
def user(ctx, term):
    '''
    Search for a user by name
    '''

    result = ctx.connect.users.search_users(options={'term': term})
    for user in result:
        for key, value in user.items():
            try:
                time = abstract.convert_time(value)
                click.echo('{key}: {value}'.format(key=key, value=time))
            except (ValueError, TypeError):
                click.echo('{key}: {value}'.format(key=key, value=value))

@cli.command()
@click.option('--team', help='Name of team')
@pass_conf
def members(ctx, team):
    '''
    Get members of a team.
    '''

    full = []
    team_id = abstract.get_team(ctx.connect, team)
    click.echo(team_id)
    team_stats = ctx.connect.teams.get_team_stats(team_id['id'])
    click.echo(team_stats)
    
    # Paginate over results pages if needed
    if team_stats['total_member_count'] > 200:
        pages = math.ceil(team_stats['total_member_count']/100)
        for page in range(pages):
            results = ctx.connect.teams.get_team_members(team_id['id'], params={'per_page': 200, 'page': page})
            try:
                full.extend(results)
            except KeyError:
                full = results
    else:
        full = results = ctx.connect.teams.get_team_members(team_id['id'], params={'per_page': 200})

    count = 0
    for member in full:
        userdata = abstract.get_nickname(ctx.connect, member['user_id'], full=True)
        click.echo(userdata['email'])
        count += 1
    
    click.echo('Found {} users'.format(count))

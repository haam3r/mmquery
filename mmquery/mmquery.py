#!/usr/bin/python3

'''
Query posts and users over the MatterMost API.
Allows for searching a user by the username.
Exporting posts from a channel, optionally also export files from channel
'''

import configparser
import json
import logging
import math
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from pprint import pprint

import requests

import click
import tabulate
from mattermostdriver import Driver, exceptions
from mmquery import abstract

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='mmquery.log', filemode='a')


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
@click.option('--host', '-h', type=str, help='Hostname of MatterMost server')
@click.option('--token', '-t', type=str, help='Your personal access token')
@click.option('--port', '-p', type=int, default=443, help='Which port to use. Default 443')
@click.option('--config', '-c', type=click.Path(), help='Path to config file for host, port and token')
@click.version_option()
@click.pass_context
def cli(ctx, host, token, port, config):

    if config:
        settings = configparser.ConfigParser()
        settings.read(config)
        if not host and 'host' in settings['Default']:
            host = settings['Default']['host']
        if not token and 'token' in settings['Default']:
            token = settings['Default']['token']
        if not port and 'port' in settings['Default']:
            port = int(settings['Default']['port'])

    if not host:
        click.echo('Missing parameter `--host/-h`.', err=True)
        click.echo(cli.get_help(ctx))
        sys.exit(1)
    if not port:
        click.echo('Missing parameter `--port/-p`.', err=True)
        click.echo(cli.get_help(ctx))
        sys.exit(1)
    if not token:
        click.echo('Missing parameter `--token/-t`.', err=True)
        click.echo(cli.get_help(ctx))
        sys.exit(1)

    connect = Driver({'url': host, 'token': token, 'port': port})
    try:
        connect.login()
    except exceptions.NoAccessTokenProvided:
        sys.exit('No or invalid Access Token.')
    ctx.obj = Config(connect)
    ctx.obj.set_config('host', host)
    ctx.obj.set_config('token', token)
    ctx.obj.set_config('port', port)
    if config:
        ctx.obj.set_config('settings', settings._sections)


@cli.command()
@click.option('--channel', required=True, help='Name of channel')
@click.option('--team', required=True, help='Name of channel')
@click.option('--filedump', is_flag=True, help='Also download posted files to current working directory')
@pass_conf
def posts(ctx, channel, team, filedump):
    '''
    Get posts from channel by channel name
    '''

    full = {}
    file_ids = []
    try:
        chan = abstract.get_channel(self=ctx.connect, name=channel, team=team)
    except requests.exceptions.HTTPError as exc:
        if exc.response.status_code == 404:
            click.echo('Channel %r not found.' % chan, file=sys.stderr)
        else:
            click.echo('Error getting channel, got status code %d.' % exc.response.status_code, file=sys.stderr)
        return
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
            try:
                nick = abstract.get_nickname(self=ctx.connect, id=full['posts'][message]['user_id'])
            except requests.exceptions.HTTPError as exc:
                if exc.response.status_code == 404:
                    click.echo('Nickname %r not found.' % nick, file=sys.stderr)
                else:
                    click.echo('Error getting nickname, got status code %d.' % exc.response.status_code, file=sys.stderr)
                return
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

    click.echo('Total number of messages: {}'.format(chan['total_msg_count']))


@cli.command()
@click.option('--term', help='Search string to find user')
@pass_conf
def user(ctx, term):
    '''
    Search for a user by name
    '''

    result = ctx.connect.users.search_users(options={'term': term})
    click.echo('Found %d users matching the query.' % len(result))
    for user in result:
        click.echo()
        for key, value in user.items():
            try:
                time = abstract.convert_time(value)
                click.echo('{key}: {value}'.format(key=key, value=time))
            except (ValueError, TypeError):
                click.echo('{key}: {value}'.format(key=key, value=value))


@cli.command()
@click.option('--team', required=True, help='Name of team')
@pass_conf
def members(ctx, team):
    '''
    Get members of a team. NB! Will return only active users
    '''
    members, team_info = get_members(ctx, team)
    for member in members.values():
        click.echo('{0}: {1}'.format(member['email'], member['nickname']))


def get_members(ctx, team):
    '''
    Base function for members wrapper function.
    Done like this, so that the report command could call this function
    '''

    full = []
    try:
        team_id = abstract.get_team(ctx.connect, team)
    except requests.exceptions.HTTPError as exc:
        if exc.response.status_code == 404:
            click.echo('Team %r not found.' % team, file=sys.stderr)
        else:
            click.echo('Error getting team, got status code %d.' % exc.response.status_code, file=sys.stderr)
        return
    click.echo('Team info: %r' % team_id)
    team_stats = ctx.connect.teams.get_team_stats(team_id['id'])
    logging.info('{0} active members from {1} total members'.format(team_stats['active_member_count'], team_stats['total_member_count']))
    members = {}

    # Paginate over results pages if needed
    if team_stats['total_member_count'] > 200:
        pages = math.ceil(team_stats['total_member_count']/100)
        logging.debug('Nr of pages: %s' % pages)
        for page in range(pages):
            results = ctx.connect.teams.get_team_members(team_id['id'], params={'per_page': 100, 'page': page})
            try:
                full.extend(results)
            except KeyError:
                full = results
    else:
        full = results = ctx.connect.teams.get_team_members(team_id['id'], params={'per_page': 200})

    count = 0
    table = []
    keys_to_use = ['username', 'nickname', 'first_name', 'last_name', 'email', 'mfa_active']
    with click.progressbar(full, label='Resolving nicknames') as full:
        for member in full:
            userdata = abstract.get_nickname(ctx.connect, member['user_id'], full=True)

            # if mfa ist not active, the key is not in the dictionary. Fix this
            if 'mfa_active' not in userdata:
                userdata['mfa_active'] = False

            if userdata['delete_at'] == 0:
                count += 1
                table.append({k: userdata[k] for k in keys_to_use})
                members[userdata['email']] = {k: userdata[k] for k in keys_to_use}
            else:
                logging.info('Found inactive user: {0}'.format(userdata['email']))

    logging.debug('Got nickname for: {}'.format(count))

    click.echo(tabulate.tabulate(table, headers='keys', tablefmt='psql'))

    return members, team_id


@cli.command()
@click.option('--print', is_flag=True, help='Print emails instead of sending. For debugging.')
@click.option('--managers', default='managers.json', required=True, type=click.Path(), help='Path to managers.json file')
@click.option('--team', type=str, required=True, help='Team for which to generate reports')
@click.option('--smtp-host', '-s', type=str, default='localhost', help='SMTP server address. Default is localhost')
@click.option('--smtp-port', default=25, type=str, help='SMTP server port. Default is 25')
@click.option('--template', default='message.txt', required=True, type=click.Path(), help='Message template file')
@click.option('--subject', type=str, required=True, help='Message subject')
@click.option('--admin', type=str, required=True, help='Admin email i.e. who gets report for user without a manager')
@click.option('--source', type=str, required=True, help='From address field')
@pass_conf
def report(ctx, print, managers, team, smtp_host, smtp_port, template, subject, admin, source):
    '''
    Send user audit reports to team managers
    '''

    reportkeys = ['nickname', 'email', 'mfa_active', 'username']
    reporting = {}
    managers = json.load(open(managers))
    if not print:
        click.echo('Loading SMTP for emails')
        smtp = smtplib.SMTP(host=smtp_host, port=smtp_port)
        smtp.connect()
    message_template = abstract.read_template(template)
    teammembers, teaminfo = get_members(ctx, team)

    # Add a parsed tracking key to every user
    # This way, if a user does not get a manager we can alert the admin about it.
    for user, params in teammembers.items():
        params['parsed'] = False

    count = 0
    for manager, data in managers.items():
        reporting[manager] = {'name': data['name'],
                              'domains': data['domain'],
                              'table' : [],
                              'count' : 0}

        for user, params in teammembers.items():
            dom = params['email'].split('@')[1]
            if dom in data['domain']:
                filtered = { rk: params[rk] for rk in reportkeys }
                reporting[manager]['table'].append(filtered)
                teammembers[user].update({'parsed': True})
                reporting[manager]['count'] += 1
                count += 1

    logging.info('Total members: {0} and parsed count: {1}'.format(len(teammembers), count))

    # Maybe the specified admin is not a manager for any domains
    if admin not in reporting:
        reporting[admin] = {'name': admin.split('@')[0],
                            'domains': '',
                            'table' : [],
                            'count' : 0}

    # Alert admin about users who will not be included in any report
    for user, params in teammembers.items():
        if not params['parsed']:
            click.echo('No manager defined for "{0}"'.format(params['email']))
            filtered = { rk: params[rk] for rk in reportkeys }
            reporting[admin]['table'].append(filtered)
            reporting[admin]['count'] += 1

    for manager, values in reporting.items():
        msg = MIMEMultipart()
        usertable = values['table']

        if values['count'] == 0:
            logging.info('No user for {0}'.format(manager))
            continue

        users = tabulate.tabulate(values['table'], headers='keys', tablefmt='psql')

        message = message_template.substitute(MANAGER_NAME=values['name'],
                                              USERS=users,
                                              MEM_COUNT=values['count'],
                                              DOMAIN=', '.join(values['domains']),
                                              TEAM_DISPLAY_NAME=teaminfo['display_name'],
                                              TEAM_DESCRIPTION=teaminfo['description'])
        msg['From'] = source
        msg['To'] = manager
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        if print:
            click.echo(msg)
        else:
            click.echo('Sending message to: {0}'.format(manager))
            smtp.send_message(msg)

        del msg

    if not print:
        click.echo('Quitting SMTP connection. All done.')
        smtp.quit()

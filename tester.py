#!/usr/bin/env python
# -*- coding=utf-8 -*-


import sys

from time import time, sleep


try:
    # noinspection PyUnresolvedReferences,PyShadowingBuiltins
    input = raw_input
except NameError:
    # noinspection PyUnboundLocalVariable,PyShadowingBuiltins
    input = input


def install_dependency(dependency):
    print('Missing {0} library, trying installing it...'.format(dependency))
    try:
        # noinspection PyUnresolvedReferences
        import pip
        ret = pip.main(['install', dependency])
        if ret:
            raise Exception(
                'Unable to install {0} library, '
                'please install it manually (see https://pypi.python.org/pypi/{0}) and retry...'
                .format(dependency))
    except ImportError:
        raise Exception(
            'Unable to install pip library, '
            'pip is missing (https://pip.pypa.io/en/stable/installing/).')

    return __import__(dependency)

try:
    import requests
except ImportError:
    requests = install_dependency('requests')
try:
    import ovh
except ImportError:
    ovh = install_dependency('ovh')
try:
    import pyspeedtest
except ImportError:
    pyspeedtest = install_dependency('pyspeedtest')


ovh_creds = {
    'endpoint': 'ovh-eu',
    'application_key': 'foUF4VKJJQju7u7S',
    'application_secret': 'WpnR1xhavQ7i40ekYVZn5ThFjvUj23k3',
    'consumer_key': 'fake_ass_key'
}

if len(sys.argv) > 1:
    ovh_creds['consumer_key'] = sys.argv[1]


client = ovh.Client(**ovh_creds)

did_auth = False
for _ in range(3):
    try:
        client.get('/me')
        break
    except ovh.exceptions.NotCredential:
        did_auth = True
        # Request API access
        ck = client.new_consumer_key_request()
        ck.add_rules(ovh.API_READ_ONLY, "/me")
        ck.add_recursive_rules(ovh.API_READ_WRITE, '/xdsl')

        # Request token
        validation = ck.request()
        print('Authentication needed, please go to: {}'
              .format(validation['validationUrl']))
        input('login and then press enter to continue...')
        ovh_creds['consumer_key'] = validation['consumerKey']
        client = ovh.Client(**ovh_creds)
else:
    raise Exception('Authentication failed')

if did_auth:
    print('Avoid this process by giving "{0}" to this script next time.'
          .format(ovh_creds['consumer_key']))


def pick(what, choices):
    nbr_choices = len(choices)
    if nbr_choices is 1:
        return choices[0]

    print('Please choose your {} from the list:'.format(what))
    for i, choice in enumerate(choices):
        print('  {0} - {1}'.format(i + 1, choice))

    while True:
        c = input('Your choice [1-{0}]: '.format(nbr_choices))
        try:
            i = int(c) - 1
            assert i in range(1, nbr_choices)
            return choices[i]
        except (AssertionError, ValueError):
            continue


services = client.get('/xdsl')
service = pick('xdsl service', services)

lines = client.get('/xdsl/{0}/lines'.format(service))
line = pick('xdsl line', lines)

print('This will test out every configuration for {0} - {1}\n'
      'It will take a long time and your connection will be unstable during the test'.format(service, line))
input('Press enter when ready ...')


print('\nStarting ...')
profiles_json = client.get('/xdsl/{0}/lines/{1}/dslamPort/availableProfiles'.format(service, line))

# example of filtering
#profiles_json = list(p for p in profiles_json
#                     if '17a' in p['name'] and ('SNR1 ' in p['name'] or 'SNR3 ' in p['name']))

profiles_json = sorted(profiles_json)
profiles_names = set(p['name'] for p in profiles_json)
nbr_profiles = len(profiles_names)
print('Found {0} profiles, testing will take nearly {1} minutes'.format(nbr_profiles, nbr_profiles * 2))

tester = pyspeedtest.SpeedTest(runs=1)
tester.chooseserver()
print('Tests will be done against server: {}'.format(tester.host))

profiles_longuest_name = len(max(profiles_names, key=len))
print('\rDURATION {0}    PING      DOWNLOAD        UPLOAD'.format('PROFIL'.rjust(profiles_longuest_name + 1)))

results = {}
for n, profile in enumerate(profiles_json):
    test_time = time()
    profile_name = profile['name']
    msg = '({0} / {1} profiles tested) Testing "{2}" -'.format(n, nbr_profiles, profile_name)

    sys.stdout.write('{0} Applying profiles'.format(msg))
    client.post(
        '/xdsl/{0}/lines/{1}/dslamPort/changeProfile'.format(service, line),
        dslamProfileId=profile['id'])


    connection_status = 'down'
    while True:
        try:
            sleep(.5)
            sys.stdout.write('\r{0} Waiting connection to go {1} ({2:.0f}s)'
                             .format(msg, connection_status, time() - test_time))
            requests.get('https://www.ovh.com', timeout=2)
            if connection_status == 'up':
                break
        except requests.exceptions.RequestException:
            connection_status = 'up'

    while True:
        # noinspection PyBroadException
        try:
            sleep(.5)
            dslam = client.get('/xdsl/{0}/lines/{1}/dslamPort'.format(service, line))
            assert dslam['profile']['name'] == profile_name
            break
        except Exception:
            sys.stdout.write('\r{0} Waiting profile to be applied'.format(msg))


    sys.stdout.write('\r{0} Testing ping'.format(msg))
    ping = tester.ping()

    sys.stdout.write('\r{0} Testing download'.format(msg))
    download = tester.download()

    sys.stdout.write('\r{0} Testing upload'.format(msg))
    upload = tester.upload()


    results[profile_name] = {
        'id': profile['id'],
        'name': profile_name,
        'ping': ping,
        'upload': upload,
        'download': download,
        'score': (upload * download) / ping
    }

    sys.stdout.write('\r{0:7.0f}s {1} {2:5.0f}ms {3:>13s} {4:>13s}\n'.format(
        time() - test_time,
        profile_name.rjust(profiles_longuest_name + 1), ping,
        pyspeedtest.pretty_speed(download), pyspeedtest.pretty_speed(upload)))

best_profile = max(results.values(), key=lambda p: p['score'])
print('\nApplying best found profile "{0}"'.format(best_profile['name']))

client.post(
    '/xdsl/{0}/lines/{1}/dslamPort/changeProfile'.format(service, line),
    dslamProfileId=best_profile['id'])

connection_status = 'down'
while True:
    try:
        sleep(.5)
        requests.get('https://www.ovh.com', timeout=2)
        if connection_status == 'up':
            break
    except requests.exceptions.RequestException:
        connection_status = 'up'

print('All done !')
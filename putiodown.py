from collections import defaultdict
import configparser
import os
import requests
import webbrowser
import urllib.parse


CLIENT_ID = '2473'
BASE_URL = 'https://api.put.io/v2/'


def Tree():
    return defaultdict(Tree)


def create_url(endpoint, token=None):
    url = urllib.parse.urljoin(BASE_URL, endpoint)

    if token:
        url = '{}?{}'.format(
            url,
            urllib.parse.urlencode({'oauth_token': token}))

    return url


def read_token():
    home = os.path.expanduser('~')
    config_file = os.path.join(home, '.putiodown')
    config = configparser.ConfigParser()

    if os.path.exists(config_file):
        config.read(config_file)

        token = config.get('putiodown', 'token')

    else:
        token = get_token()
        config['putiodown'] = {}
        config['putiodown']['token'] = token

        with open(config_file, 'w') as f:
            config.write(f)

    return token


def get_token():
    apptoken_url = "http://put.io/v2/oauth2/apptoken/{}".format(CLIENT_ID)
    webbrowser.open(apptoken_url)
    token = input("Enter token: ").strip()

    return token


def get_putio_filelist(token, parent_id=0):
    url = create_url('files/list', token)
    r = requests.get(url, params={'parent_id': parent_id})

    return r.json()


def _finditem(obj, key):
    if key in obj:
        return obj[key]
    for k, v in obj.items():
        if isinstance(v, dict):
            item = _finditem(v, key)
            if item is not None:
                return item


def file_tree(token):
    tree = {0: {}}
    dir_list = [0]

    for dir_id in dir_list:

        # getting data from the putio api
        response = get_putio_filelist(token, parent_id=dir_id)

        # if the folder doesnt have a parent_id it needs to be id 0
        if response['parent']['parent_id'] is None:
            leaf = tree[0]

        else:
            # looking for the parent in the tree
            parent = _finditem(tree, response['parent']['parent_id'])

            # create a new dict for the leaf
            parent[response['parent']['id']] = {}

            # define leaf in tree object
            leaf = parent[response['parent']['id']]

        # store dir name
        leaf['name'] = response['parent']['name']

        # create filelist
        leaf['files'] = []

        for item in response['files']:

            # if "file" is a directory store it in the dir_list
            if item['content_type'] == 'application/x-directory':
                if item['id'] not in dir_list:
                    dir_list.append(item['id'])

            # if its a file it will get append to the file list
            else:
                leaf['files'].append(item)

    return tree


import json
token = read_token()
print(json.dumps(file_tree(token)))

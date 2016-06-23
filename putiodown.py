import configparser
import os
import requests
import webbrowser
import urllib.parse


CLIENT_ID = '2473'
BASE_URL = 'https://api.put.io/v2/'


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
    """Opens a webbrowser and shows a token after accepting it.

    You have to paste the token that is shown.

    :returns token:
    :rtype: str
    """
    apptoken_url = "http://put.io/v2/oauth2/apptoken/{}".format(CLIENT_ID)
    webbrowser.open(apptoken_url)
    token = input("Enter token: ").strip()

    return token


def get_putio_filelist(token, parent_id=0):
    """Gets a filelist for a specific id.

    It gets a filelist from the putio api and decodes the json to a dict.

    :param token: a putio auth token
    :param parent_id: the id of a folder to fetch
    :type token: str
    :type parent_id: int
    :returns: dict with filelist data
    :rtype: dict
    """
    url = create_url('files/list', token)
    r = requests.get(url, params={'parent_id': parent_id})

    return r.json()


def get_full_path(parent_index, parent_id):
    """Returns a full path.

    It needs a dictionary with all parents and its references.

    Example::

        parents = {
            0: {
                'name': 'root',
                'parent': None
            },
            2: {
                'name': 'Musik',
                'parent': 0
            },
            3: {
                'name': 'morrissey',
                'parent': 2
            },
            4: {
                'name': 'Filme',
                'parent': 0
            },
        }

    :param parent_index: A dictionary with all parent items
    :param parent_id: parent id to search for
    :type parent_index: dict
    :type parent_id: int
    :returns: a full path string
    :rtype: str
    """
    path = []

    def get_parents(id):
        if parent_index[id]['parent'] is None:
            path.append('root')

            return list(reversed(path))

        path.append(parent_index[id]['name'])
        id = parent_index[id]['parent']

        return get_parents(id)

    parent_list = get_parents(parent_id)

    return os.path.join(*parent_list)


def download_list(token):
    """Yields a download data dictionary.

    This functions walks through all directories, looks for file parents,
    generates full file paths and yields the data dictionary.

    Example::

        {
            'name': 'foobar.mp3',
            'path': 'Good_Music/AlbumFoo',
            'id': 777
        }

    :param token: A putio api token
    :type token: str
    :returns: A dictionary with all data it needs to download the file
    :rtype: dict
    """
    # this is a list it iterates over with all directory ids. it gets filled
    # on the fly if it finds another directory. it pre-filled with a 0
    # because its the id of the root directory
    dir_list = [0]

    # a dictionary to store every parent directory it finds with its
    # name and parent id stored
    parents = {}

    for dir_id in dir_list:

        # getting data from putio api
        response = get_putio_filelist(token, parent_id=dir_id)

        # add parent data to the parents dictionary
        parents[response['parent']['id']] = {
            'name': response['parent']['name'],
            'parent': response['parent']['parent_id']
        }

        # iterate of files
        for item in response['files']:

            # if its a directory it will add the id to the dir_list and
            # iterate over the next directory in list
            if item['content_type'] == 'application/x-directory':
                if item['id'] not in dir_list:
                    dir_list.append(item['id'])

            else:

                # yield the item data
                yield {
                    'name': item['name'],
                    'path': get_full_path(parents, item['parent_id']),
                    'id': item['id']
                }


token = read_token()
for i in download_list(token):
    print(i)

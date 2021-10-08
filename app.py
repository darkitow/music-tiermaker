import os ; import sys ; import shlex ; import math
parent_dir = os.path.abspath(os.path.dirname(__file__))
vendor_dir = os.path.join(parent_dir, 'vendor')
sys.path.append(vendor_dir)
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import unicodedata ; import re ; import requests
from PIL import Image, ImageFont, ImageDraw
from string import ascii_letters ; import textwrap
from tqdm import tqdm ; bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} ETA: {remaining}, '

client_id = '6e6f47d5221b462fa8030e359ea314a9'
client_secret = '2eb1b154acaa4fb485d110a90fa57cee'
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id,client_secret))

class colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    RED = '\033[31m'
    YELLOW = '\033[33m'
    BOLD = '\033[1m'
    END = '\033[0m'

config = {
    'remove_tags':True,
    'artist_singles':False,
    'only_cover':False,
    'choose_albums':True,
    'artist_subfolders':False}

help_text = '''
    COMMANDS

    search              search on spotify based on query
                        search <type> 'query'
                        types: album, artist

    album               get album from spotify link
                        album 'link'

    artist              get artist from spotify link
                        artist 'link'

    playlist            get playlist from spotify link
                        playlist 'link'

    config              config settings
                        config <option> - to toggle option
                        config - to see all configs

    help                displays help
    '''

def removeTags(value):
    str_copy = value.lower()
    ban1 = ['feat','with','prod'] ; ban2 = ['(','[','.']
    banned_str = [b+a for a in ban1 for b in ban2]
    for ban_str in banned_str:
        if ban_str in str_copy: value = value[:str_copy.find(ban_str)]
    return value

def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')

def saveImg(link,name):
    r = session.get(link, stream=True)
    if r.status_code == 200:
        with open('./'+name,'wb') as f:
            f.write(r.content)

def drawImg(img,text):
    index = ''
    if not config['artist_subfolders']:
        if song_index[0] > 0:
            for i in range(0,2):
                index += f'{str(song_index[i]).zfill(math.floor(math.log10(lead_zero[i]))+1)}-'
    if config['remove_tags'] == True: text = removeTags(text)
    
    fileName = slugify(text)
    # text fitting settings
    fontSize = 100
    while True:
        fontSize -= 4
        font = ImageFont.truetype(f'{parent_dir}/vendor/SourceCodePro-Bold.ttf',fontSize)
        avg_char_width = sum(font.getsize(char)[0] for char in ascii_letters) / len(ascii_letters)
        max_char_count = int((img.size[0] * .95)/avg_char_width)
        if max_char_count >= 10: break
    # draw image and save
    text = textwrap.fill(text=text, width=max_char_count)
    draw = ImageDraw.Draw(img)
    draw.multiline_text(xy=(img.size[0]/2, img.size[1]/2), text=text, font=font, fill='white', anchor='mm', align='center',stroke_width=int(fontSize/10), stroke_fill='black')
    img.save(f'./{index}{fileName}.png')

def getalbum(album_id,create_dir=True):
    global song_index, lead_zero
    result = sp.album(album_id) ; os.remove('.cache')
    album_name = result['name']
    album_cover = result['images'][0]['url']
    
    if config['only_cover'] == True: saveImg(album_cover,f'{slugify(album_name)}.png') ; return

    if create_dir == True:
        album_dir = f'./{slugify(album_name)}'
        if not os.path.exists(album_dir):
            os.makedirs(album_dir)
        os.chdir(album_dir)
    
    saveImg(album_cover, 'temp.png')
    img = Image.open('temp.png')
    lead_zero[1] = len(result['tracks']['items'])
    for track in tqdm(result['tracks']['items'], bar_format=bar_format, leave=False):
        song_index[1] += 1
        drawImg(img.copy(), track['name'])
    os.remove('temp.png')
    if create_dir == True: os.chdir('../') 

def getartist(artist_id):
    global song_index, lead_zero
    result = sp.artist(artist_id) ; os.remove('.cache')
    artist_name = result['name']
    artist_pfp = result['images'][0]['url']
    
    artist_dir = f'./{slugify(artist_name)}'
    if not os.path.exists(artist_dir):
        os.makedirs(artist_dir)
    os.chdir(artist_dir)
    saveImg(artist_pfp,'artist_pfp.png')

    result = sp.artist_albums(artist_id, limit=50, album_type='album') ; os.remove('.cache')

    ignore_album = list()
    if config['choose_albums'] == True:
        for i,album in enumerate(result['items']):
            if album['name'] in list(i['name'] for i in result['items'][:i]):
                ignore_album.append(album['uri'])
        while True:
            for i,album in enumerate(result['items']):
                if album['uri'] in ignore_album: color = colors.RED
                else: color = colors.GREEN
                print(f'{i+1}. {color}{album["name"]} ({album["release_date"]}){colors.END}')
            print('0. Confirm')
            try:
                opt = int(input())
                album_opt = result['items'][opt-1]['uri']
                if opt == 0: break
                elif album_opt in ignore_album: ignore_album.remove(album_opt)
                else: ignore_album.append(album_opt)
            except: pass

    selected_albums = list(i['uri'] for i in result['items'] if i['uri'] not in ignore_album)
    lead_zero[0] = len(selected_albums)
    if config['artist_singles']: lead_zero[0] += 1
    for album in tqdm(selected_albums, bar_format=bar_format):
        song_index = [song_index[0]+1,0]
        if config['artist_subfolders']: getalbum(album)
        else: getalbum(album,False)
    
    if config['artist_singles'] == True:
        song_index = [song_index[0]+1,0]

        if config['artist_subfolders'] == True:
            singles_dir = './.singles'
            if not os.path.exists(singles_dir):
                os.makedirs(singles_dir)
            os.chdir(singles_dir)
        
        # spotify api has a 50 song limit, dont know what i can do
        result = sp.artist_albums(artist_id, limit=50, album_type='single') ; os.remove('.cache')
        for single in tqdm(result['items'], bar_format=bar_format):
            getalbum(single['uri'],False)
        if config['artist_subfolders'] == True: os.chdir('../')
    os.chdir('../')

def getplaylist(playlist_id):
    result = sp.playlist(playlist_id) ; os.remove('.cache')
    playlist_name = result['name']
    playlist_cover = result['images'][0]['url']

    playlist_dir = f'./{slugify(playlist_name)}'
    if not os.path.exists(playlist_dir):
        os.makedirs(playlist_dir)
    os.chdir(playlist_dir)
    saveImg(playlist_cover,'playlist_cover.png')

    for track in tqdm(result['tracks']['items'], bar_format=bar_format):
        album_cover = track['track']['album']['images'][0]['url']
        saveImg(album_cover, 'temp.png')
        img = Image.open('temp.png')
        drawImg(img.copy(), track['track']['name'])
        os.remove('temp.png')
    os.chdir('../')

def search(nature,q):
    valid_types = ['album','artist']
    if nature not in valid_types: print('invalid type') ; return
    result = sp.search(q=q, type=nature, limit=10) ; os.remove('.cache')
    options = dict()
    for i, option in enumerate(result[nature+'s']['items']):
        if nature == 'album':
            opt_name = option['name']
            opt_artist = ', '.join(list(i['name'] for i in option['artists']))
            print(f'{i+1}. {colors.YELLOW}{opt_name}{colors.END} - {opt_artist}')
        elif nature == 'artist':
            opt_name = option['name']
            opt_followers = option['followers']['total']
            print(f'{i+1}. {colors.YELLOW}{opt_name}{colors.END} - {opt_followers} Followers')
        options[i+1] = option['uri']
    print('0. Cancel')
    while True:
        try:
            opt = int(input())
            if opt in options:
                if nature == 'album': getalbum(options[opt])
                elif nature == 'artist': getartist(options[opt])
                return
            elif opt == 0: return
        except Exception as e: print(e) ; print('invalid option') ; pass

def configs(opt=None):
    if opt in config:
        if config[opt] == True: config[opt] = False
        elif config[opt] == False: config[opt] = True
        #else: config[opt] == arg
        if config[opt] == True: color = colors.GREEN
        elif config[opt] == False: color = colors.RED
        else: color = colors.YELLOW
        print(f'{opt}: {color}{config[opt]}{colors.END}')
    else: 
        for opt in config:
            if config[opt] == True: color = colors.GREEN
            elif config[opt] == False: color = colors.RED
            else: color = colors.YELLOW
            print(f'{opt}: {color}{config[opt]}{colors.END}')
    return

def helper(arg=None):
    if arg == None: print(help_text)
        
def main():
    global session
    global song_index, lead_zero
    session = requests.Session()
    commands = {
        'album':getalbum,
        'artist':getartist,
        'playlist':getplaylist,
        'search':search,
        'config':configs,
        'help':helper
    }
    while True:
        song_index = [0,0] ; lead_zero = [0,0]
        user_input = shlex.split(input('> '))
        if user_input[0] in commands:
            try: commands[user_input[0]](*user_input[1:])
            except TypeError: print('invalid argument, type "help" for help') ; pass
        else:
            print('invalid command, type "help" for help')

if __name__ == '__main__':
    main()
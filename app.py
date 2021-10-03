# C:\Python27 python
import os ; import sys ; import shlex
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
    'artist_singles':True
}
help_text = '''
    COMMANDS

    search              search on spotify based on query
                        search <type> "query"
                        types: album, artist

    album               get album from spotify link
                        album "link"

    artist              get artist from spotify link
                        artist "link"

    playlist            get playlist from spotify link
                        playlist "link"

    config              change <option>, if option not provided see current configs
                        config <option>

    help                displays help
    '''

def saveImg(link,name='temp',ext='.png'):
    r = requests.get(link, stream=True)
    if r.status_code == 200:
        with open('./'+name+ext,'wb') as f:
            f.write(r.content)

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

def drawImg(text,img_link):
        saveImg(img_link)
        if config['remove_tags'] == True: text = removeTags(text)
        img = Image.open('./temp.png')
        fileName = slugify(text)
        # text fitting settings
        fontSize = 100
        while True:
            fontSize -= 4
            font = ImageFont.truetype(f'{parent_dir}/vendor/SourceCodePro-Bold.ttf',fontSize)
            avg_char_width = sum(font.getsize(char)[0] for char in ascii_letters) / len(ascii_letters)
            max_char_count = int((img.size[0] * .95)/avg_char_width)
            if max_char_count >= 10: break

        # draw image, save, and remove cache
        text = textwrap.fill(text=text, width=max_char_count)
        draw = ImageDraw.Draw(img)
        draw.multiline_text(xy=(img.size[0]/2, img.size[1]/2), text=text, font=font, fill='white', anchor='mm', align='center',stroke_width=int(fontSize/10), stroke_fill='black')
        img.save(f'./{fileName}.png')
        os.remove('temp.png')

def getalbum(album_id,create_dir=True):
    result = sp.album(album_id) ; os.remove('.cache')
    album_name = result['name']
    album_cover = result['images'][0]['url']

    if create_dir == True:
        album_dir = f'./{slugify(album_name)}'
        if not os.path.exists(album_dir):
            os.makedirs(album_dir)
        os.chdir(album_dir)
    
    for track in tqdm(result['tracks']['items'], bar_format=bar_format, leave=False):
        drawImg(track['name'], album_cover)
    if create_dir == True: os.chdir('../') 

def getartist(artist_id):
    result = sp.artist(artist_id) ; os.remove('.cache')
    artist_name = result['name']
    artist_pfp = result['images'][0]['url']
    
    artist_dir = f'./{slugify(artist_name)}'
    if not os.path.exists(artist_dir):
        os.makedirs(artist_dir)
    os.chdir(artist_dir)
    saveImg(artist_pfp,'artist_pfp')

    result = sp.artist_albums(artist_id, album_type='album') ; os.remove('.cache')
    for album in tqdm(result['items'], bar_format=bar_format):
        getalbum(album['uri'])
    
    if config['artist_singles'] == True:
        # why the fuck i doesn't get all the singles is beyond me
        singles_dir = './.singles'
        if not os.path.exists(singles_dir):
            os.makedirs(singles_dir)
        os.chdir(singles_dir)
        
        result = sp.artist_albums(artist_id, album_type='single') ; os.remove('.cache')
        for single in tqdm(result['items'], bar_format=bar_format):
            getalbum(single['uri'],False)
        os.chdir('../')
    os.chdir('../')

def getplaylist(playlist_id):
    result = sp.playlist(playlist_id) ; os.remove('.cache')
    playlist_name = result['name']
    playlist_cover = result['images'][0]['url']

    playlist_dir = f'./{slugify(playlist_name)}'
    if not os.path.exists(playlist_dir):
        os.makedirs(playlist_dir)
    os.chdir(playlist_dir)
    saveImg(playlist_cover,'playlist_cover')

    for track in tqdm(result['tracks']['items'], bar_format=bar_format):
        drawImg(track['track']['name'], track['track']['album']['images'][0]['url'])
    os.chdir('../')

def search(nature,q):
    valid_types = ['album','artist']
    if nature not in valid_types: print('invalid type') ; return
    result = sp.search(q=q, type=nature, limit=10)
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
        except: print('invalid option') ; pass

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
    commands = {
        'album':getalbum,
        'artist':getartist,
        'playlist':getplaylist,
        'search':search,
        'config':configs,
        'help':helper
    }
    while True:
        user_input = shlex.split(input('> '))
        if user_input[0] in commands:
            try: commands[user_input[0]](*user_input[1:])
            except TypeError: print('invalid argument, type "help" for help') ; pass
        else:
            print('invalid command, type "help" for help')

if __name__ == '__main__':
    main()
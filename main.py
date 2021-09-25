from typing import Tuple
import requests
from bs4 import BeautifulSoup
import re
from pytube import Playlist
import os


tor_proxies = {
    'http': 'socks5h://127.0.0.1:9150',
    'https': 'socks5h://127.0.0.1:9150',
}


def get_session(headers={}, proxies={}, cookies={}) -> requests.Session:
    session = requests.Session()
    if headers:
        session.headers = headers
    if proxies:
        session.proxies = proxies
    if cookies:
        session.cookies = cookies
    return session


def download_mp3(yt_url: str, session=get_session(), timeout=120.0) -> Tuple[bytes, str]:
    payload = {
        'typ': 'mp3',
        'search_txt': yt_url
    }
    res = session.post('https://www.bestmp3converter.com/models/convertProcess.php', data=payload, timeout=timeout)
    res.raise_for_status()

    # parse for download url and video title
    soup = BeautifulSoup(res.text, 'html.parser')
    data_link = soup.find('option', text=re.compile('320kbps'), attrs={'class': 'data_option'}).get('data-link')
    title = soup.find('h5', attrs={'class': 'media-heading'}).text

    if (not data_link) or (not title):
        raise Exception('Could not parse the video data!')

    res = session.get(data_link, timeout=60.0)
    res.raise_for_status
    return res.content, title


def get_valid_file_name_for_windows(name: str) -> str:
    return name.replace('/', ' ').replace('\\', ' ').replace('|', ' ').replace('>', ' ').replace('<', ' ')\
        .replace('"', ' ').replace('?', ' ').replace('*', ' ').replace(':', ' ')



if __name__ == '__main__':
    url = 'https://youtube.com/playlist?list=PLtjOj4GHYr57dvVDGg0Y22F8eg6bKaxkn'
    playlist = Playlist(url)
    session = get_session()

    # get title of playlist and replace all forbidden characters
    pl_title = get_valid_file_name_for_windows(playlist.title) + ' - Download'


    if not os.path.exists(os.path.normpath(pl_title)):
        print('Creating download directory ...')
        os.mkdir(os.path.normpath(pl_title))


    print('Start Download...')
    for idx, vid in enumerate(playlist.video_urls, 1):
        print(f'{idx}/{playlist.length} {vid} ...', end='\r')

        download_complete = False
        retries = 0
        while not download_complete and retries < 10:
            try:
                mp3, title = download_mp3(vid, session=session)
            except:
                retries += 1
                print(f'{idx}/{playlist.length} {vid} ... [retry: {retries}]', end='\r')
            else:
                download_complete = True
        
        if download_complete:
            with open(os.path.normpath(os.path.join(pl_title, get_valid_file_name_for_windows(title) + '.mp3')), 'wb') as f:
                f.write(mp3)
            print(f'{idx}/{playlist.length} {title}' + ' '*(len(vid) + 14 + len(str(retries)) - len(title)))
        else:
            print(f'ERROR :: download failed!{" "*(len(vid) + len(str(retries)) - 11)}\n\t{idx}/{playlist.length} {vid}')
            with open(os.path.normpath(os.path.join(pl_title, 'failed.txt')), mode='a') as f:
                f.write(vid + '\n')
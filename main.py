from typing import Tuple
import requests
from bs4 import BeautifulSoup
import re
from pytube import Playlist
import os


tor_proxies = {
    'http': 'socks5://127.0.0.1:9150',
    'https': 'socks5://127.0.0.1:9150',
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

    res = session.get(data_link, timeout=60.0)
    res.raise_for_status
    return res.content, title



url = 'https://www.youtube.com/playlist?list=PLmv_bvU0txj_s55Z_2ax5AzAIYY0pN25-'
playlist = Playlist(url)
session = get_session()

pl_title = playlist.title.replace('/', ' ').replace('\\', ' ')

if not os.path.exists(os.path.normpath(pl_title)):
    os.mkdir(os.path.normpath(pl_title))

print('Start Download...')
for idx, vid in enumerate(playlist.video_urls, 1):
    print(f'{idx}/{playlist.length} {vid} ...', end='\r')
    mp3, title = download_mp3(vid, session=session)
    with open(os.path.normpath(os.path.join(pl_title, title.replace('/', ' ').replace('\\', ' ') + '.mp3')), 'wb') as f:
        f.write(mp3)
    print(f'{idx}/{playlist.length} {title}' + ' '*(len(vid) + 4 - len(title)))
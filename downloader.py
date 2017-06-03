import requests
import urllib
import json
import os
import sys

BASE_URL = 'http://dragonsdogma.wikia.com'

CATEGORIES = {'Weapons', 'Armor', 'Clothing', 'Dark Arisen: Weapons', 'Dark Arisen: Armor'}


def get_category(category):
    url = '{base}/api/v1/Articles/List?category={category}&limit=2500'.format(base=BASE_URL, category=category)
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    for item in data['items']:
        yield item['id'], item['title']


def get_page_text(page_id):
    url = '{base}/api.php?action=query&format=json&pageids={page_id}&export'.format(base=BASE_URL, page_id=page_id)
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    return data['query']['export']['*']


if __name__ == '__main__':
    only_download = None
    if len(sys.argv) > 1:
        only_download = ' '.join(sys.argv[1:])
        
    try:
        os.mkdir('cache')
    except FileExistsError:
        pass
    
    for category in CATEGORIES:
        for page_id, title in get_category(category):
            if only_download is not None and title != only_download:
                continue
            print(title)
            page = get_page_text(page_id)
            filename = 'id' + str(page_id) + '.wiki'
            with open(os.path.join('cache', filename), 'w') as f:
                f.write(page)

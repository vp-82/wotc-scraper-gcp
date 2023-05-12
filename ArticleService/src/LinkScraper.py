import os
import json
import time
import datetime
from typing import List, Tuple
import requests
from bs4 import BeautifulSoup
from firebase_admin import auth, credentials, firestore
import firebase_admin

from GCPHandler import FirestoreArticleLinkAdapter
from ArticleHandler import ArticleLink


class Scraper:
    def __init__(self, adapter: FirestoreArticleLinkAdapter):
        self.adapter = adapter

    def load_known_link_ids(self) -> List[str]:
        known_link_ids = []
        link_list = self.adapter.get_links()
        for link_info in link_list:
            known_link_ids.append(link_info.url_hash)
        return known_link_ids

    def scrape_links(self, from_page: int, to_page: int) -> None:
        known_link_ids = self.load_known_link_ids()

        has_results = True
        i = from_page
        while has_results and i <= to_page:
            time.sleep(2)
            search_response = requests.get(f'https://magic.wizards.com/en/news/archive?search&page={i}&category=all&author=all&order=newest')
            page_result = search_response.text
            soup = BeautifulSoup(page_result, 'html.parser')

            entry = soup.find(class_="css-36asz")
            if entry:
                print(f'Response from page {i} :'+entry.text.strip())
                has_results = False
                break

            entry_list = soup.find_all(class_="css-9f4rq")
            for entry in entry_list:
                parent = entry.findParent()
                link_id = parent.get('href')
                link_url = 'https://magic.wizards.com' + link_id
                if link_id not in known_link_ids:
                    link_info = ArticleLink(
                        link_url='https://magic.wizards.com' + link_id,
                        link_added_at=datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S"),
                    )
                    print(f'Adding {link_id}')
                    self.adapter.save_link(link_info)

                    known_link_ids.append(link_id)
                else:
                    print(f'Link with Id {link_id} already exists')

            if i % 10 == 0:
                print(f'Page: {i}')
                print(search_response.status_code)
            i += 1


if __name__ == "__main__":
    # Initialize Firestore client
    if firebase_admin._apps.get('[DEFAULT]'):
        print('Firestore Default App already initialized')
    else:
        print('Init Firestore Default App')
        cred = credentials.Certificate('mtg-scraper-385015-aad053a61746.json')
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    adapter = FirestoreArticleLinkAdapter(db)
    scraper = Scraper(adapter)
    from_page = 1
    to_page = 4
    scraper.scrape_links(from_page, to_page)

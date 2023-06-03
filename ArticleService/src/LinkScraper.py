import os
import json
import time
import datetime
from typing import List, Tuple
import requests
from bs4 import BeautifulSoup
from firebase_admin import auth, credentials, firestore
import firebase_admin
import logging

from GCPHandler import FirestoreArticleLinkAdapter
from ArticleHandler import ArticleLink


class Scraper:
    def __init__(self, adapter: FirestoreArticleLinkAdapter):
        self.adapter = adapter
        self.logger = logging.getLogger(__name__)

    def _fetch_and_parse_page_content(self, page_number: int) -> BeautifulSoup:
        time.sleep(2)
        search_response = requests.get(f'https://magic.wizards.com/en/news/archive?search&page={page_number}&category=all&author=all&order=newest')
        return BeautifulSoup(search_response.text, 'html.parser')

    def _extract_links_from_soup(self, soup: BeautifulSoup) -> List[str]:
        links = []
        entry_list = soup.find_all("article", class_="css-415ug css-o3Y69")
        for entry in entry_list:
            link_tag = entry.find("a", href=True)
            if link_tag:
                link_path = link_tag.get('href')  # renamed link_id to link_path
                if link_path.startswith("/"):  # if the link is a relative URL
                    links.append('https://magic.wizards.com' + link_path)
        return links


    def _create_link_info(self, link: str) -> ArticleLink:
        return ArticleLink(
            link_url=link,
            link_added_at=datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S"),
        )

    def _load_known_link_ids(self) -> List[str]:
        known_link_ids = []
        link_list = self.adapter.get_links()
        for link_info in link_list:
            known_link_ids.append(link_info.url_hash)
        return known_link_ids

    def _save_new_links(self, links: List[str], known_link_ids: List[str]) -> None:
        for link in links:
            link_info = self._create_link_info(link)
            if link_info.url_hash not in known_link_ids:
                self.logger.info(f'Adding {link}')
                self.adapter.save_link(link_info)
                known_link_ids.append(link_info.url_hash)
            else:
                self.logger.info(f'Link with Id {link_info.url_hash} already exists')

    def scrape_links(self, from_page: int, to_page: int) -> None:
        known_link_ids = self._load_known_link_ids()

        for i in range(from_page, to_page + 1):
            soup = self._fetch_and_parse_page_content(i)
            links = self._extract_links_from_soup(soup)
            self._save_new_links(links, known_link_ids)

            if i % 10 == 0:
                self.logger.info(f'Page: {i}')

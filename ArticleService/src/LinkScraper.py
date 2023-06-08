import datetime
import logging
import time
from typing import List, Optional

import requests
from bs4 import BeautifulSoup
from firebase_admin import auth, credentials, firestore

from src.ArticleHandler import ArticleLink
from src.GCPHandler import FirestoreArticleLinkAdapter


class Scraper:
    def __init__(self, adapter: FirestoreArticleLinkAdapter):
        self.adapter = adapter
        self.logger = logging.getLogger(__name__)

    def _fetch_and_parse_page_content(self, page_number: int) -> Optional[BeautifulSoup]:
        time.sleep(2)
        response = None
        try:
            response = requests.get(f'https://magic.wizards.com/en/news/archive?search&page={page_number}&category=all&author=all&order=newest')
            response.raise_for_status()
            self.logger.info(f'Successfully fetched and parsed content from page number {page_number}')
        except requests.HTTPError as http_err:
            self.logger.error(f'HTTP error occurred: {http_err}') 
        except Exception as err:
            self.logger.error(f'Error occurred: {err}') 

        if response is not None:
            return BeautifulSoup(response.text, 'html.parser')
        else:
            return None


    def _extract_links_from_soup(self, soup: BeautifulSoup) -> List[str]:
        links = []
        entry_list = soup.find_all("article", class_="css-415ug css-o3Y69")
        for entry in entry_list:
            link_tag = entry.find("a", href=True)
            if link_tag:
                link_path = link_tag.get('href')  
                if link_path.startswith("/"):
                    links.append('https://magic.wizards.com' + link_path)
        self.logger.info(f'Extracted {len(links)} links from the soup')
        return links
    

    def _create_link_info(self, link: str) -> ArticleLink:
        return ArticleLink(
            link_url=link,
            link_added_at=datetime.datetime.now()
            # link_added_at=datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S"),
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
        self.logger.info(f'Starting to scrape links from page {from_page} to page {to_page}')
        known_link_ids = self._load_known_link_ids()
        for i in range(from_page, to_page):
            soup = self._fetch_and_parse_page_content(i)
            if soup is None:
                self.logger.warning(f'Failed to fetch and parse content from page {i}')
                continue
            links = self._extract_links_from_soup(soup)
            self._save_new_links(links, known_link_ids)
            if i % 10 == 0:
                self.logger.info(f'Page: {i}')
        self.logger.info(f'Finished scraping links from page {from_page} to page {to_page}')



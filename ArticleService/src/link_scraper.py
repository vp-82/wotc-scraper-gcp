"""
Module for Scraper class
"""

import datetime
import logging
import time
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from src.article_handler import ArticleLink
from src.firestore_article_link_adapter import FirestoreArticleLinkAdapter


class Scraper:
    """
    Class for Scraping web pages
    """
    def __init__(self, adapter: FirestoreArticleLinkAdapter):
        self.adapter = adapter
        self.logger = logging.getLogger(__name__)

    def _fetch_and_parse_page_content(self, page_number: int) -> Optional[BeautifulSoup]:
        """
        Fetch and parse page content
        """
        time.sleep(2)
        response = None
        try:
            response = requests.get(
                (
                    f'https://magic.wizards.com/en/news/archive?search&page={page_number}'
                    f'&category=all&author=all&order=newest'
                ),
                timeout=60
            )
            response.raise_for_status()
            self.logger.info('Successfully fetched and parsed content from page number %s', page_number)
        except requests.HTTPError as http_err:
            self.logger.error('HTTP error occurred: %s', http_err)
        except requests.RequestException as err:
            self.logger.error('Error occurred: %s', err)

        if response is not None:
            return BeautifulSoup(response.text, 'html.parser')
        else:
            return None

    def _extract_links_from_soup(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract links from BeautifulSoup object
        """
        links = []
        entry_list = soup.find_all("article", class_="css-415ug css-o3Y69")
        for entry in entry_list:
            link_tag = entry.find("a", href=True)
            if link_tag:
                link_path = link_tag.get('href')
                if link_path.startswith("/"):
                    links.append('https://magic.wizards.com' + link_path)
        self.logger.info('Extracted %s links from the soup', len(links))
        return links

    def _create_link_info(self, link: str) -> ArticleLink:
        """
        Create link info
        """
        return ArticleLink(
            link_url=link,
            link_added_at=datetime.datetime.now()
        )

    def _load_known_link_ids(self) -> List[str]:
        """
        Load known link ids
        """
        known_link_ids = []
        link_list = self.adapter.get_links()
        for link_info in link_list:
            known_link_ids.append(link_info.url_hash)
        return known_link_ids

    def _save_new_links(self, links: List[str], known_link_ids: List[str]) -> bool:
        """
        Save new links
        """
        found_only_new_links = True
        for link in links:
            link_info = self._create_link_info(link)
            if link_info.url_hash not in known_link_ids:
                self.logger.info('Adding %s', link)
                self.adapter.save_link(link_info)
                known_link_ids.append(link_info.url_hash)
            else:
                self.logger.info('Link with Id %s already exists', link_info.url_hash)
                found_only_new_links = False
        return found_only_new_links

    def scrape_links(self, from_page: int, to_page: int, stop_on_existing: bool = False) -> bool:
        """
        Scrape links
        """
        stopped_on_existing = False
        self.logger.info('Starting to scrape links from page %s to page %s', from_page, to_page)
        known_link_ids = self._load_known_link_ids()
        for i in range(from_page, to_page):
            soup = self._fetch_and_parse_page_content(i)
            if soup is None:
                self.logger.warning('Failed to fetch and parse content from page %s', i)
                continue
            links = self._extract_links_from_soup(soup)
            only_new_link_found = self._save_new_links(links, known_link_ids)
            if stop_on_existing and not only_new_link_found:
                self.logger.info('Stopped scraping due to encountering an existing link at page %s', i)
                stopped_on_existing = True
                return stopped_on_existing
            if i % 10 == 0:
                self.logger.info('Page: %s', i)
        self.logger.info('Finished scraping links from page %s to page %s', from_page, to_page)
        return stopped_on_existing

import re
from re import Pattern

import requests
from bs4 import BeautifulSoup
from requests import Response

from custom_exceptions import DoiNotFound, CrossrefUnavailable, ScihubUnavailable


# TODO: Exception handling
#       Unit tests

class SciHubScraper:
    def __init__(self, download_dir: str = None):
        """
        SciHubScraper is an unofficial API for SciHub.
        :param download_dir: Default None. Path to directory where documents will be saved.
        """
        # Regex pattern to macht DOI https://ihateregex.io/expr/doi/.
        self.doi_pattern: Pattern[str] = re.compile(r'^(10\.\d{4,5}/[\S]+[^;,.\s])$')
        # Regex pattern to match download link on Sci-Hub.
        self.url_pattern: Pattern[str] = re.compile(r"https://.*.pdf\?download=true")
        # TODO: get valid urls from ilovescihub.wordpress.com during initialisation
        self.scihub_urls: list[str] = ["http://sci-hub.ee", "https://sci-hub.ee", "https://sci-hub.ru",
                                       "https://sci-hub.se", "https://sci-hub.st", "http://sci-hub.ai",
                                       "https://sci-hub.ai", "https://sci-hub.cat"]
        self.crossref_url: str = 'https://api.crossref.org/works'
        self.url: str = self.get_valid_url()
        self.download_dir = download_dir

    def download_document(self, param: str) -> bool:
        """
        Downloads document
        :param param: Name or DOI of document
        :return: True if download finished successfully
        """
        doi: str = self.get_doi(param)

        document_url: str = "{}/{}".format(self.url, doi)
        request: Response = requests.get(document_url, stream=True)

        # TODO: Include url_pattern regex in soup.find
        soup: BeautifulSoup = BeautifulSoup(request.content, 'html.parser')
        download_url: str = self.url_pattern.findall(str(soup.find("button")))[0]

        if self.download_dir:
            save_path: str = "{}/{}.pdf".format(self.download_dir, doi.replace("/", "-"))
        else:
            save_path: str = "{}.pdf".format(doi.replace("/", "-"))

        self.save_document(download_url, save_path)

        return True

    def get_doi(self, param: str) -> str:
        """
        Checks if param is a valid DOI, if not it looks it up.
        :param param: Either name of document or a DOI. Any valid DOI format is supported.
        :return: DOI as str.
        """
        match = self.doi_pattern.match(param.strip())
        if match is None:
            return self.search_doi_on_crossref(param)
        else:
            return match.group()

    def search_doi_on_crossref(self, publication_name: str) -> str:
        """
        Searches for publication on crossref.org to find the DOI.
        If the DOI can't be found, it throws a DoiNotFound exception.
        If Crossref is unavailable it throws a CrossrefUnavailable exception.
        :param publication_name: Name of the publication.
        :return: DOI as str.
        """
        publication_name: str = publication_name.strip()
        request: dict = requests.get(self.crossref_url,
                                     params={'query.title': publication_name}).json()

        if request['status'] == 'ok':
            if 'message' in request:
                for item in request['message']['items']:
                    if item['title'][0].lower() == publication_name.lower():
                        return item['DOI']
            raise DoiNotFound
        else:
            raise CrossrefUnavailable

    def get_valid_url(self, enforce_https: bool = True) -> str:
        """
        Tests if an url from scihub_urls is available.
        If none are available, throws ScihubUnavailable exception.
        :param enforce_https: Default True. If True, filters non https Sci-Hub urls.
        :return: available Sci-Hub url.
        """
        if enforce_https:
            url_list: list[str] = list(filter(lambda x: x.startswith('https://'), self.scihub_urls))
        else:
            url_list: list[str] = self.scihub_urls
        for url in url_list:
            if requests.get(url).status_code == 200:
                return url
        raise ScihubUnavailable

    @staticmethod
    def save_document(url: str, dst: str):
        """
        Saves document.
        If permissions are insufficient to write, throws PermissionError.
        :param url: Sci-Hub download URL of document.
        :param dst: Path where to save document.
        :return:
        """
        request = requests.get(url, stream=True)
        try:
            with open(dst, 'wb') as fh:
                for chunk in request.iter_content(chunk_size=1024):
                    fh.write(chunk)
        except PermissionError:
            raise PermissionError
        except Exception:
            raise Exception("Something went wrong while downloading document from {}".format(url))

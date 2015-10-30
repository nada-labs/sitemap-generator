#!/usr/bin/env python3
#
# Generates a sitemap of the provided URL
#
# It's an excuse to play with BeautifulSoup

import urllib
import re
from io import BytesIO
from bs4 import BeautifulSoup
from pycurl import Curl

class PageFetcher():
    """Fetches a page and parses it for links"""

    def __init__(self):
        self.curl = Curl()
        self.url = None
        self.headers = {}
        self.status = ''
        self.code = 0
        self.charset_re = re.compile('charset=(\S+)')

    def handle_headers(self, header):
        """Parses the headers from a HTTP response"""
        header = header.decode('iso-8859-1') #headers always in iso-8859-1

        if ':' in header:
            #split out the headers name and value
            n, v = header.split(':', 1)
            self.headers[n] = v
        elif 'HTTP' in header:
            h, self.code, self.status = header.split(' ', 2)
            self.code = int(self.code)

    def encoding(self):
        """Gets the encoding from the headers, otherwise assumes iso-8859-1"""
        if 'Content-Type' in self.headers:
            match = self.charset_re.search(self.headers['Content-Type'].lower())
            if match:
                return match.group(1)
        return 'iso-8859-1'

    def getlinks(self, url):
        """Gets the specified webpage and returns any links found in it"""
        #reset the gathered data
        self.headers = {}
        self.code = 0
        self.status = None

        links = []

        #get the page
        buff = BytesIO()
        self.curl.setopt(self.curl.URL, url)
        self.curl.setopt(self.curl.WRITEDATA, buff)
        self.curl.setopt(self.curl.HEADERFUNCTION, self.handle_headers)
        self.curl.perform()

        #parse for anchor tags
        body = buff.getvalue().decode(self.encoding())
        bs = BeautifulSoup(body)

        for anchor in bs.find_all('a'):
            links.append(anchor['href'])

        return links

if __name__ == "__main__":
    from pprint import pprint
    fetch = PageFetcher()
    links = fetch.getlinks('http://nada-labs.net')

    pprint(links)

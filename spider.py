#
# Walks every page that it can find in a website
#
# It's an excuse to play with BeautifulSoup

import re
from io import BytesIO
from bs4 import BeautifulSoup
from pycurl import Curl
from queue import Queue, Empty as QueueEmpty
from urllib.parse import urlsplit, urlunsplit, urljoin
from sys import stdout

class PageFetcher():
    """Fetches a page"""

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
            n, v = header.split(': ', 1)
            self.headers[n] = v.rstrip('\r\n')
        elif 'HTTP' in header:
            h, code, status = header.split(' ', 2)
            self.code = int(code)
            self.status = status.rstrip('\r\n')

    def encoding(self):
        """Gets the encoding from the headers, otherwise assumes iso-8859-1"""
        if 'Content-Type' in self.headers:
            match = self.charset_re.search(self.headers['Content-Type'].lower())
            if match:
                return match.group(1)
        return 'iso-8859-1'

    def fetch(self, url, headers_only=False):
        """Gets the specified webpage"""
        #reset the gathered data
        self.headers = {}
        self.code = 0
        self.status = None

        links = []

        #get the page
        buff = BytesIO()
        self.curl.setopt(self.curl.URL, url)
        if headers_only:
            self.curl.setopt(self.curl.NOBODY, 1)
        else:
            self.curl.setopt(self.curl.NOBODY, 0)
        self.curl.setopt(self.curl.WRITEDATA, buff)
        self.curl.setopt(self.curl.HEADERFUNCTION, self.handle_headers)
        self.curl.perform()

        #decode the returned data to the correct type
        body = buff.getvalue().decode(self.encoding())
        return self.code, self.headers, body

class Spider:
    """Fetches every page within a website"""
    def __init__(self):
        self.htmlpage = re.compile('text/(html|xml)|application/(xhtml\+xml|xml)')

    def walk(self, url, pagefilter = None):
        """Walks all pages in the given website"""
        if not url.startswith('http'):
            url = 'http://' + url

        fetch = PageFetcher()
        queued = Queue()
        queued.put(url)
        processed = set()

        while not queued.empty():
            url = queued.get()
            if url not in processed:
                have_body = False
                processed.add(url)
                code, headers, body = fetch.fetch(url, True) #only get headers

                if code >= 300 and code <= 399 and 'Location' in headers:
                    locpart = urlsplit(headers['Location'])
                    urlpart = urlsplit(url)
                    if locpart.scheme == urlpart.scheme and locpart.netloc == urlpart.netloc:
                        queued.put(headers['Location'])

                #parse out the links if it's a html page
                if self.ishtml(headers):
                    code, headers, body = fetch.fetch(url) #get the whole page
                    have_body = True
                    links = self.sitelinks(body, url)

                    for l in links:
                        queued.put(l)

                #pass the page onto the processor, if it passes the defined filter
                if not pagefilter or (pagefilter and pagefilter(code, headers)):
                    if not have_body:
                        code, headers, body = fetch.fetch(url) #get the whole page
                    self.process_page(url, code, headers, body)

    def ishtml(self, headers):
        '''Determines if the retrieved page is a (x)html page'''
        if 'Content-Type' in headers and self.htmlpage.search(headers['Content-Type']):
            return True
        return False

    def sitelinks(self, html_page, url):
        """Finds all links in the provided html page"""
        bs = BeautifulSoup(html_page)
        links = set()
        urlpart = urlsplit(url)

        try:
            for anchor in bs.find_all('a'):
                linkpart = list(urlsplit(anchor['href']))
                linkpart[4] = '' #remove the fragment

                if linkpart[0] == '':
                    linkpart[0] = urlpart.scheme

                if linkpart[1] == '':
                    linkpart[1] = urlpart.netloc

                if linkpart[0] == urlpart.scheme and linkpart[1] == urlpart.netloc:
                    if linkpart[2].startswith('/'):
                        links.add(urlunsplit(linkpart))
                    elif linkpart[2] != '':
                        #relative URL.
                        links.add(urljoin(url, linkpart[2]))
        except KeyError:
            pass

        return links

    def process_page(self, url, code, headers, body):
        '''Does things with the retrieved page'''
        pass

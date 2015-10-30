# Sitemap Generator #

Generates a sitemap.xml for the provided website. It's an excuse for me
to play with BeautifulSoup, curl and ElementTree.

## Requirements ##
 * BeautifulSoup4
 * pycurl
 * python3

## Usage ##
  ./sitemap.py http://nada-labs.net sitemap.xml
Will dump all pages it can find at http://nada-labs.net into sitemap.xml


#!/usr/bin/env python3
#
# Generates a sitemap of all files and feeds available from a given URL
#

from spider import Spider
from time import strftime, gmtime, strptime
from urllib.parse import urlsplit
from re import search
import xml.etree.ElementTree as ET
from sys import stdout

spinny = ['-', '\\', '|', '/']

class Sitemap(Spider):
    def __init__(self):
        self.pageinfo = {}
        self.errors = []

    def process_page(self, url, code, headers, body):
        if code == 200:
            lastmod = ''
            pri = 1.0
            change = 'monthly'

            urlpath = urlsplit(url).path

            if 'Last-Modified' in headers:
                t = strptime(headers['Last-Modified'], '%a, %d %b %Y %H:%M:%S GMT')
            else:
                t = gmtime()
            lastmod = strftime('%Y-%m-%d', t)

            #set priority and change status based on urlpath. Tags and categorys
            #have a lower priority as we want linking to the post.
            #The main page has a higher change frequency, all others assumed
            #to be posts or static files.
            if search('^/(tags|category)', urlpath):
                pri = 0.7
                change = 'weekly'
            if urlpath == '' or urlpath == '/':
                change = 'weekly'

            stdout.write('\r[%s] Processing...' % (spinny[len(self.pageinfo) % 4]))
            stdout.flush()

            self.pageinfo[url] = {'lastmod':lastmod, 'pri':pri, 'change':change}

        if code >= 400:
            self.errors.append((url, code))

    def walk(self, url, outfile):
        self.pageinfo = {}
        self.errors = []

        Spider.walk(self, url)

        print("\r[ ] Processed %i urls" % (len(self.pageinfo)))

        urlset = ET.Element('urlset', {'xmlns':"http://www.sitemaps.org/schemas/sitemap/0.9"})
        for page in self.pageinfo:
            url = ET.SubElement(urlset, 'url')
            loc = ET.SubElement(url, 'loc')
            lastmod = ET.SubElement(url, 'lastmod')
            changefreq = ET.SubElement(url, 'changefreq')
            priority = ET.SubElement(url, 'priority')

            loc.text = page
            lastmod.text = self.pageinfo[page]['lastmod']
            changefreq.text = self.pageinfo[page]['change']
            priority.text = '%0.1f' % self.pageinfo[page]['pri']

        tree = ET.ElementTree(urlset)
        tree.write(outfile, encoding='utf-8', xml_declaration=True)

        if len(self.errors) > 0:
            print("[!] The following pages produced errors:")
            for e in self.errors:
                print("    %i %s" % (e[1], e[0]))

if __name__ == '__main__':
    from sys import argv
    if len(argv) != 3:
        print('usage: %s url sitemap.xml' % (argv[0]))
    else:
        sitemap = Sitemap()
        sitemap.walk(argv[1], argv[2])

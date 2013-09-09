from BeautifulSoup import BeautifulSoup
import datetime
import httplib2
import os
import re
import urllib2

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "../../../downloads")

class BuildRetriever(object):
    """
    This class helps with retrieving builds of various types

    This class is rather gratuitously copied from mozregression. It would be
    good if we could consolidate all this code from mozregression/mozdownload
    into one thing that we could use for fennec, desktop builds, etc.
    """
    _monthlinks = {}
    _baseurl = "http://ftp.mozilla.org/pub/mozilla.org/mobile/nightly/"

    @staticmethod
    def _url_links(url):
        res = [] # do not return a generator but an array, so we can store it for later use

        h = httplib2.Http();
        resp, content = h.request(url, "GET")
        if resp.status != 200:
            return res

        soup = BeautifulSoup(content)
        for link in soup.findAll('a'):
            res.append(link)
        return res

    @staticmethod
    def get_date(datestr):
        p = re.compile('(\d{4})\-(\d{1,2})\-(\d{1,2})')
        m = p.match(datestr)
        if not m:
            raise Exception("Incorrect date format")
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    @staticmethod
    def _format_date_part(part):
        if part < 10:
            part = "0" + str(part)
        return str(part)

    def _get_build_url(self, product, date):
        url = self._baseurl
        year = str(date.year)
        month = self._format_date_part(date.month)
        day = self._format_date_part(date.day)
        url += year + "/" + month + "/"

        linkregex = '^' + year + '-' + month + '-' + day + '-' + '[\d-]+' + product['reponame'] + '/$'
        cachekey = year + '-' + month
        if cachekey in self._monthlinks:
            monthlinks = self._monthlinks[cachekey]
        else:
            monthlinks = self._url_links(url)
            self._monthlinks[cachekey] = monthlinks

        # first parse monthly list to get correct directory
        for dirlink in monthlinks:
            dirhref = dirlink.get("href")
            if re.match(linkregex, dirhref):
                # now parse the page for the correct build url
                for url in [ url+dirhref, url + dirhref + "en-US/" ]:
                    for link in self._url_links(url):
                        href = link.get("href")
                        if re.match(product['buildregex'], href):
                            return url + href

        return None

    def _get_latest_build_url(self, product):
        baseurl =  product['latest']
        matches = []
        for link in self._url_links(baseurl):
            href = link.get("href")
            # sometimes there will be multiple matching products between
            # merges. in that case, we grab the greater of them (as the
            # latest has a higher version number)
            if re.match(product['buildregex'], href):
                matches.append(href)
        if not matches:
            raise Exception("Could not find matching build!")

        return baseurl + sorted(matches)[-1]

    def get_build(self, product, date=None):
        if not date:
            url = self._get_latest_build_url(product)
            datestr = "latest"
        else:
            url = self._get_build_url(product, date)
            datestr = date.strftime("%Y-%m-%d")

        fname = os.path.join(DOWNLOAD_DIR,
                             "%s-%s.apk" % (product['name'], datestr))
        if date and os.path.exists(fname):
            print "Build already exists for %s. Skipping download." % datestr
            return fname

        print "Downloading '%s' to '%s'" % (url, fname)
        dl = urllib2.urlopen(url)
        with open(fname, 'w') as f:
            f.write(dl.read())

        return fname

products = [
    {
        "name": "nightly",
        "platform": "android",
        "buildregex": ".*android-arm.apk",
        "reponame": "mozilla-central-android",
        "latest": "http://ftp.mozilla.org/pub/mozilla.org/mobile/nightly/latest-mozilla-central-android/en-US/",
        "appname": "org.mozilla.fennec"
    },
    {
        "name": "nightly-armv6",
        "platform": "android",
        "buildregex": ".*android-arm-armv6.apk",
        "reponame": "mozilla-central-android-armv6",
        "latest": "http://ftp.mozilla.org/pub/mozilla.org/mobile/nightly/latest-mozilla-central-android-armv6/en-US/",
        "appname": "org.mozilla.fennec"
    },
    {
        "name": "stock",
        "platform": "android",
        "url": None,
        "appname": "com.android.browser"
    },
    {
        "name": "stock-ics",
        "platform": "android",
        "url": None,
        "appname": "com.google.android.browser"
    },
    {
        "name": "chrome",
        "platform": "android",
        "url": None,
        "appname": "com.android.chrome"
    },
    {
        "name": "b2g-nightly",
        "platform": "b2g",
        "url": None,
        "appname": None
    }
]

def get_product(productname):
    matching_products = [product for product in products if \
                             product['name'] == productname]
    if not matching_products:
        raise Exception("No products matching '%s'" % productname)
    if len(matching_products) > 1:
        raise Exception("More than one product matching '%s'" % productname)

    return matching_products[0]

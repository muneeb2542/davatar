# davatar.py: domain avatars as fallback for gravatar
#
# davatar checks several different sources to find a suitable image for a
# domain avatar by downloading http://<domain>/ and looking for the following
# tags (in this order):
#
# - apple-touch-icon (http://bit.ly/18X1vXA)
# - og:image (http://ogp.me/)
# - twitter:image (https://dev.twitter.com/docs/cards/markup-reference)
# - shortcut icon link (http://www.w3.org/wiki/More_about_the_document_head)
# - And of course it will fall back to the venerable favicon.ico
#
# Usage:
#
# To request a domain avatar:
#
# http://<davatar server>/avatar/<domain>/
#
# If not domain avatar can be found, davatar will fall back to gravatar. To
# customize the fallback, you can specify size and possibly default for
# gravatar:
#
# http://<davatar server>/avatar/<domain>/<size>/
# http://<davatar server>/avatar/<domain>/<size>/<default>
#
# Examples:
#
# http://<davatar server>/avatar/kaarsemaker.net/
# http://<davatar server>/avatar/kaarsemaker.net/60/
# http://<davatar server>/avatar/kaarsemaker.net/60/wavatar/
#
# To use it as fallback for gravatar, append davatar.jpg to the url. This
# example uses all these features and falls back to a 40x40 wavatar
#
# http://www.gravatar.com/avatar/d676657d7fc100f6feb43d71f7b69630/?d=http%3A%2F%2Fdavatar.seveas.net%2Favatar%2Fkaarsemaker.net%2F40%2Fwavatar%2Fdavatar.jpg
#
# (C)2014 Dennis Kaarsemaker <dennis@kaarsemaker.net>

from flask import Flask, redirect, send_file, current_app
from flask.views import View
from hashlib import md5
import HTMLParser
import os
import requests
import time

class Defaults:
    CACHE_ROOT = '/tmp/davatar/'
    DEBUG = os.environ.get('DAVATAR_DEBUG', 'false').lower() in ('1', 'true', 'yes')

class ImageView(View):
    def dispatch_request(self, domain, size=21, default='mm'):
        # Image url's are cached for 2 days. First clean the cache and add the image
        cache_dir = current_app.config['CACHE_ROOT']
        msum = md5(domain).hexdigest()
        cache = os.path.join(cache_dir, msum[:2], msum[2:4], domain)
        if not os.path.exists(cache):
            self.cache_image(domain, cache)
        if (time.time() - os.path.getmtime(cache)) > 172800:
            os.unlink(cache)
            self.cache_image(domain, cache)

        # And now serve it, falling back to what the user may have specified
        with open(cache) as fd:
            data = fd.read()
        if not data:
            return redirect('http://gravatar.com/avatar/?s=%d&f=d&d=%s' % (size, default))
        return redirect(data)

    def cache_image(self, domain, cache):
        try:
            resp = requests.get('http://%s' % domain, timeout=5)
            parser = FaviconParser(domain)
            parser.feed(resp.text)
            url = parser.url
        except requests.ConnectionError:
            url = ''

        if not os.path.exists(os.path.dirname(cache)):
            os.makedirs(os.path.dirname(cache))
        with open(cache, 'w') as fd:
            fd.write(url)

class FaviconParser(HTMLParser.HTMLParser):
    possible_images = {
        'apple':     {'tag': 'link', 'attr': 'rel',      'value': 'apple-touch-icon', 'url': 'href'},
        'opengraph': {'tag': 'meta', 'attr': 'property', 'value': 'og:image',         'url': 'content'},
        'twitter':   {'tag': 'meta', 'attr': 'property', 'value': 'twitter:image',    'url': 'content'},
        'twitter2':  {'tag': 'meta', 'attr': 'property', 'value': 'twitter:image:src','url': 'content'},
        'favicon':   {'tag': 'link', 'attr': 'rel',      'value': 'shortcut icon',    'url': 'content'},
    }
    preference = ('apple', 'opengraph', 'twitter', 'twitter2', 'favicon')

    def __init__(self, domain):
        HTMLParser.HTMLParser.__init__(self)
        self.domain = domain
        self.urls = {}
        self.url = ''

    def feed(self, data):
        try:
            HTMLParser.HTMLParser.feed(self, data)
        except StopIteration:
            pass

    def handle_starttag(self, tag, attrs):
        attrs = dict([(x[0].lower(), x[1]) for x in  attrs])
        tag = tag.lower()
        for imgt, img in self.possible_images.items():
            if tag == img['tag'] and attrs.get(img['attr'], '').lower() == img['value']:
                self.urls[imgt] = attrs.get(img['url'])

    def handle_endtag(self, tag):
        if tag != 'head':
            return

        for x in self.preference:
            if self.urls.get(x, None):
                self.url = self.urls[x]
                break

        if not self.url:
            self.url = 'favicon.ico'

        if self.url and not self.url.startswith(('http://', 'https://')):
            if self.url.startswith('/'):
                self.url = self.url[1:]
            self.url ='http://%s/%s' % (self.domain, self.url)

        # Make sure image exists, gravatar doesn't like being served 404's
        try:
            resp = requests.get(self.url)
            if resp.status_code != 200:
                self.url =''
        except requests.ConnectionError:
            self.url =''

        # Once we've parsed <head>, we can discard the rest
        raise StopIteration()

app = Flask(__name__)
app.config.from_object(Defaults)
app.add_url_rule('/', view_func=lambda: redirect('http://github.com/seveas/davatar/'))
app.add_url_rule('/avatar/<domain>/', view_func=ImageView.as_view('image'))
app.add_url_rule('/avatar/<domain>/<int:size>/', view_func=ImageView.as_view('image_with_size'))
app.add_url_rule('/avatar/<domain>/<int:size>/<default>/', view_func=ImageView.as_view('image_with_size_and_default'))
app.add_url_rule('/avatar/<domain>/davatar.jpg', view_func=ImageView.as_view('image-2'))
app.add_url_rule('/avatar/<domain>/<int:size>/davatar.jpg', view_func=ImageView.as_view('image_with_size-2'))
app.add_url_rule('/avatar/<domain>/<int:size>/<default>/davatar.jpg', view_func=ImageView.as_view('image_with_size_and_default-2'))

if __name__ == '__main__':
    os.chdir('/')
    app.run()

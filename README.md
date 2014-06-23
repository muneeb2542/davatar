davatar.py: domain avatars as fallback for gravatar
===================================================

davatar checks several different sources to find a suitable image for a
domain avatar by downloading http://\<domain\>/ and looking for the following
tags (in this order):

- [apple-touch-icon] (http://bit.ly/18X1vXA) 
- [og:image] (http://ogp.me/) 
- [twitter:image] (https://dev.twitter.com/docs/cards/markup-reference) 
- [shortcut icon link] (http://www.w3.org/wiki/More_about_the_document_head) 
- And of course it will fall back to the venerable favicon.ico

Requesting a domain avatar
--------------------------

- http://\<davatar server\>/avatar/\<domain\>/

If not domain avatar can be found, davatar will fall back to gravatar. To
customize the fallback, you can specify size and possibly default for
gravatar:

- http://\<davatar server\>/avatar/\<domain\>/\<size\>/ 
- http://\<davatar server\>/avatar/\<domain\>/\<size\>/\<default\>

Examples:

- http://\<davatar server\>/avatar/kaarsemaker.net/
- http://\<davatar server\>/avatar/kaarsemaker.net/60/ 
- http://\<davatar server\>/avatar/kaarsemaker.net/60/wavatar/

To use it as fallback for gravatar, append davatar.jpg to the url. This
example uses all these features and falls back to a 40x40 wavatar

http://www.gravatar.com/avatar/d676657d7fc100f6feb43d71f7b69630/?d=http%3A%2F%2Fdavatar.seveas.net%2Favatar%2Fkaarsemaker.net%2F40%2Fwavatar%2Fdavatar.jpg

Setting up a davatar server
---------------------------

davatar is a [flask](http://flask.pocoo.org) application, so you'll need to
install that. I recommend using nginx and uwsgi to serve it, but any wsgi
container will do. In fact, simply running `python -mdavatar` in a screen will
do in a pinch :smile:.

I use this uwsgi config on Ubuntu:

```
[uwsgi]
plugins       = python
module        = davatar:app
env           = PYTHONPATH=/home/dennis
env           = HOME=/nonexistent

# Basic management setup
shared-socket = 1
chown_socket  = www-data
log-reopen    = 1

# Process handling: don't overload the server
processes     = 10
harakiri      = 60
max-requests  = 20
reload-on-as  = 1024
auto-procname = 1
procname-prefix-spaced = davatar
```

And here's the ngnix config:

```
server {
    listen 80;
    listen  [::]:80;

    root /usr/share/nginx/www;
    index index.html index.htm;

    server_name davatar.seveas.net;

    try_files $uri @uwsgi;
    location @uwsgi {
        include uwsgi_params;
        uwsgi_pass unix:/run/uwsgi/app/davatar/socket;
    }
}
```

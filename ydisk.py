#!/usr/bin/env python

import sys
import os
import tempfile
import gzip
import urlparse
import xml.etree.ElementTree as et
import BaseHTTPServer

import requests

try:
    from dateutil.parser import parse as dateparse
except:
    dateparse = None

OAYR = "https://oauth.yandex.ru/"
D = '{DAV:}'


class YploadRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse.parse_qs(urlparse.urlparse(self.path).query)
        if "code" in parsed:
            YploadRequestHandler._code = parsed["code"][0]
        self.wfile.write("HTTP/1.0 200 OK")
        self.send_header("Date", self.date_time_string())
        self.send_header("Server", self.version_string())
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write("<html><body>\n")
        self.wfile.write("<script>" +
                         "var win = window.open('', '_self');win.close();" +
                         "</script>\n")
        self.wfile.write("Your code is %s" % YploadRequestHandler._code)
        self.wfile.write("</body></html>\n")
        self.finish()


class FileInfo(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def fromXML(self, j):
        [href, propstat] = j.getchildren()
        self.href = href.text
        [status, prop] = propstat.getchildren()
        for x in prop:
            tag = x.tag.replace(D, '')
            if   tag == 'displayname':
                self.name = x.text
            elif tag == 'getcontentlength':
                self.length = int(x.text)
            elif tag == 'getlastmodified':
                self.modified = dateparse(x.text)
            elif tag == 'creationdate':
                self.created = dateparse(x.text)
        return self

    def json(self):
        return dict(
            name=self.name,
            length=self.length,
            modified=self.modified.strftime('%s')
        )

    def __str__(self):
        return '%(name)s (%(href)s) - %(length)s bytes' % self

    __repr__ = __str__


def getKey(YD_APP_ID, YD_APP_SECRET, keyfile):
    if os.path.isfile(keyfile):
        return open(keyfile, 'r').read()
    import webbrowser
    webbrowser.open_new(
        OAYR + 'authorize?response_type=code&client_id=' + YD_APP_ID)

    YploadRequestHandler._code = None
    httpd = BaseHTTPServer.HTTPServer(('', 8714), YploadRequestHandler)
    httpd.handle_request()

    if YploadRequestHandler._code:
        code = YploadRequestHandler._code
    else:
        code = raw_input('Input your code: ').strip()

    res = requests.post(OAYR + 'token', data=dict(
        grant_type='authorization_code',
        code=code,
        client_id=YD_APP_ID, client_secret=YD_APP_SECRET
    ))
    if res.status_code != 200:
        raise Exception('Wrong code')
    key = res.json['access_token']
    with open(keyfile, 'w') as fl:
        fl.write(key)
    return key


class LoginAPI:
    MP = "https://login.yandex.ru/info?format=json"

    def __init__(self, key):
        self.key = "OAuth " + key

    def getInfo(self):
        rq = requests.get(self.MP, headers={
            'Authorization': self.key,
        })
        return rq.json


class DiskAPI:
    MP = 'https://webdav.yandex.ru'

    def __init__(self, key):
        self.key = "OAuth " + key

    def url(self, d):
        return self.MP + d

    def request(self, method, url=None, data=None, headers=None):
        if not headers:
            headers = {}
        if 'Accept' not in headers:
            headers['Accept'] = '*/*'
        headers['Authorization'] = self.key

        return requests.request(
            method, url=self.url(url), headers=headers, data=data
        )

    def ls(self, directory='/'):
        if not dateparse:
            raise Exception('You need to install dateutil module')
        rq = self.request('PROPFIND', directory, headers={
            'Depth': '1'
        })
        res = []
        xml = et.fromstring(rq.text)
        for line in xml.findall('{DAV:}response'):
            res.append(FileInfo().fromXML(line))
        return res

    def mkdir(self, path):
        rq = self.request('MKCOL', path)
        return rq.status_code == 201

    def put(self, path, data, tp='application/binary'):
        headers = {
            'Expect': '100-continue',
            'Content-Type': tp,
        }
        if requests.__version__.split('.') >= [1, 1, 0]:
            # This is a dummy solutino for gzizpped and chunked upload
            headers['Content-Encoding'] = 'gzip'
            headers['Transfer-Encoding'] = 'chunked'

            def gzipped_data_generator(dt):
                with tempfile.TemporaryFile(mode="w+b") as gfl:
                    zip = gzip.GzipFile(mode='wb', fileobj=gfl)
                    zip.write(dt)
                    zip.close()
                    gfl.seek(0)
                    while True:
                        st = gfl.read(1024)
                        if st:
                            yield st
                        else:
                            break

            data = gzipped_data_generator(data)

        rq = self.request(
            'PUT', path, data=data, headers=headers
        )
        return rq.status_code == 201

    def publish(self, path):
        rq = requests.post(
            self.url(path) + '?publish', allow_redirects=False,
            headers={
                'Authorization': self.key,
                'Accept': '*/*'
            })
        if rq.status_code != 302:
            raise Exception('Wtf?')
        return rq.headers['location']

if __name__ == '__main__':
    key = getKey()
    api = DiskAPI(key)
    api.mkdir('/JustShared')
    fname = sys.argv[1]
    newname = '/JustShared/' + os.path.basename(fname)
    api.put(newname, open(sys.argv[1], 'r').read())
    print api.publish(newname)

#!/usr/bin/env python
import sys
import os
import requests
import urlparse
try:
    from pyxml2obj import XMLin
    from dateutil.parser import parse as dateparse
except:
    XMLin = None
import json
import BaseHTTPServer


class YploadRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse.parse_qs(urlparse.urlparse(self.path).query)
        if "code" in parsed:
            YploadRequestHandler._code = parsed["code"][0]
        self.wfile.write("HTTP/1.0 200 OK")
        self.send_header("Date", self.date_time_string())
        self.send_header("Server", self.version_string())
        self.end_headers()
        self.wfile.write("<html><body>\n")
        self.wfile.write("<script>var win = window.open('', '_self');win.close();</script>\n")
        self.wfile.write("Your code is %s" % YploadRequestHandler._code)
        self.wfile.write("</body></html>\n")
        self.finish()


class FileInfo(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def fromJSON(self, j):
        self.href = j['d:href']
        prop = j['d:propstat']['d:prop']
        self.name = prop['d:displayname']
        self.length = prop['d:getcontentlength']
        self.modified = dateparse(prop['d:getlastmodified'])
        self.created = dateparse(prop['d:creationdate'])
        return self

    def json(self):
        return dict(
                name = self.name,
                length = self.length,
                modified = self.modified.strftime('%s')
            )

    def __str__(self):
        return '%(name)s (%(href)s) - %(length)s bytes' % self

    __repr__ = __str__


def getKey(YD_APP_ID, YD_APP_SECRET, keyfile):
    if os.path.isfile(keyfile):
        return open(keyfile, 'r').read()
    import webbrowser
    webbrowser.open_new('https://oauth.yandex.ru/authorize?response_type=code&client_id=' + YD_APP_ID)

    YploadRequestHandler._code = None
    httpd = BaseHTTPServer.HTTPServer(('', 8714), YploadRequestHandler)
    httpd.handle_request()

    if YploadRequestHandler._code:
        code = YploadRequestHandler._code
    else:
        code = raw_input('Input your code: ').strip()

    res = requests.post('https://oauth.yandex.ru/token',
        data = dict(
            grant_type='authorization_code',
            code=code,
            client_id=YD_APP_ID, client_secret=YD_APP_SECRET
        )
    )
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
        rq = requests.get(self.MP,
                headers = {
                    'Authorization' : self.key,
                })
        return rq.json


class DiskAPI:
    MP = 'https://webdav.yandex.ru'
    def __init__(self, key):
        self.key = "OAuth " + key

    def url(self, d):
        return self.MP + d

    def ls(self, directory='/'):
        if not XMLin:
            raise Exception('You need to install pyxml2obj and dateutil')
        rq = requests.request('PROPFIND', self.url(directory),
                headers = {
                    'Authorization' : self.key,
                    'Accept'        : '*/*',
                    'Depth'         : '1'
                })
        res = []
        for line in XMLin(rq.text)['d:response']:
            res.append(FileInfo().fromJSON(line))
        return res

    def mkdir(self, path):
        rq = requests.request('MKCOL',
                self.url(path),
                headers = {
                    'Authorization' : self.key,
                    'Accept'           : '*/*',
                }
            )
        return rq.status_code == 201

    def put(self, path, data, tp = 'application/binary'):
        dt = data
        rq = requests.request('PUT',
                self.url(path),
                data = data,
                headers = {
                    'Authorization' : self.key,
                    'Accept'           : '*/*',
                    'Expect'           : '100-continue',
                    'Content-Type'     : tp,
                }
            )
        return rq.status_code == 201

    def publish(self, path):
        rq = requests.post(self.url(path) + '?publish', headers = {
                    'Authorization' : self.key,
                    'Accept'           : '*/*',} ,
                allow_redirects=False)
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
    # for x in api.ls('/JustShared'):
    #    print x


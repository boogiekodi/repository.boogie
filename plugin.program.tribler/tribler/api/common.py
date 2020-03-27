'''
Created on 26 Mar 2020

@author: boogie
'''
from tinyxbmc import net
from tinyxbmc import gui
from requests.exceptions import StreamConsumedError, ConnectionError, ConnectTimeout

import os
import ConfigParser

import json


def getconfig():
    try:
        base_dir = os.path.expanduser("~/.Tribler")
        for d in os.listdir(base_dir):
            subdir = os.path.join(base_dir, d)
            if os.path.isdir(subdir):
                for subfile in os.listdir(subdir):
                    if subfile == "triblerd.conf":
                        config = ConfigParser.ConfigParser()
                        config.read(os.path.join(subdir, subfile))
                        break
                if config:
                    break
    except Exception:
        config = None
    return config


config = getconfig()


def call(method, endpoint, **data):
    url = "http://localhost:%s/%s" % (config.get("http_api", "port"), endpoint)
    headers = {"X-Api-Key": config.get("http_api", "key")}
    print url
    print data
    if method in ["GET"] or method == "PUT" and endpoint == "remote_query":
        params = data
        js = True
    else:
        params = None
        js = data

    resp = net.http(url, timeout=60, params=params, headers=headers, json=js, method=method)
    print json.dumps(resp)
    if "error" in resp:
        if isinstance(resp["error"], dict):
            title = resp["error"].get("code", "ERROR")
            msg = resp["error"].get("message", "Unknown Error")
        else:
            title = "ERROR"
            msg = str(resp["error"])
        gui.ok(title, msg)
    else:
        return resp


def makemagnet(infohash):
    return "magnet:?xt=urn:btih:%s" % infohash


class event(object):
    def __init__(self, timeout):
        self.url = "http://localhost:%s/events" % config.get("http_api", "port")
        self.headers = {"X-Api-Key": config.get("http_api", "key")}
        self.timeout = timeout
        self.prepare()

    def prepare(self):
        self.response = net.http(self.url, timeout=self.timeout, headers=self.headers, stream=True, text=False)

    def iter(self):
        try:
            for content in self.response.iter_lines(delimiter="\n\ndata: "):
                try:
                    js = json.loads(content)
                except ValueError:
                    print "." + content.encode("ascii", "replace") + "."
                    continue
                print js["event"]
                yield js["event"]
            self.response.close()
        except GeneratorExit:
            self.response.close()
        except (StreamConsumedError, AttributeError, ConnectionError, ConnectTimeout):
            raise StopIteration

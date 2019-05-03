# -*- coding: utf-8 -*-

from xbmc import executebuiltin, Monitor
from resources.lib.server import create_server
from resources.lib.wsgi_app import *
from resources.lib.utils import *

xbmc.executebuiltin('RunScript(plugin.program.freebgtvs, False)')
monitor = Monitor()

httpd = create_server(BIND_IP, app, port=port)
httpd.timeout = 0.1
starting = True

while not monitor.abortRequested():
  httpd.handle_request()
  if starting:
    notify_success('PVR backend стартира на порт %s' % port)
    starting = False

httpd.socket.close()
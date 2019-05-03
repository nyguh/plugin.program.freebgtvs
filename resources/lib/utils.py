# -*- coding: utf-8 -*-
import json
from kodibgcommon.utils import *
from assets import Assets

id             = get_addon_id()
name           = get_addon_name()
profile_dir    = get_profile_dir()
icon           = get_addon_icon()
c_debug        = settings.debug
local_db       = xbmc.translatePath(os.path.join( get_addon_dir(), 'resources', 'tvs.sqlite3' ))
url            = 'https://raw.githubusercontent.com/hristo-genev/uWsgiApps/master/freetvandradio/tvs.sqlite3'
a              = Assets(profile_dir, url, local_db, log)
db             = a.file

try:
  db = os.environ['BGTVS_DB_']
except Exception:
  pass  

## Initialize the addon
pl_name       = 'playlist.m3u'
pl_path       = os.path.join( get_profile_dir() + pl_name)
pl_json_path  = os.path.join( get_profile_dir() + 'channels.json')
__version__   = xbmc.getInfoLabel('System.BuildVersion')
VERSION       = int(__version__[0:2])
user_agent    = 'Kodi %s' % __version__
scheduled_run = len(sys.argv) > 1 and sys.argv[1] == str(True)
progress_bar  = None

### Literals
RUNSCRIPT     = 'RunScript(%s, True)' % id
GET           = 'GET'
HEAD          = 'HEAD'
NEWLINE       = '\n'
BIND_IP       = '0.0.0.0' if settings.bind_all else '127.0.0.1'
STREAM_URL    = 'http://' + settings.stream_ip + ':' + str(settings.port) + '/freebgtvs.backend/stream/%s'


def get_stream_url(name):
  log("Loading " + pl_json_path + " and searching for channel " + name, 2)
  channels = json.load(open(pl_json_path))
  log("channels loaded from json", 2)
  log (channels.get(name.decode('utf-8')))
  return channels.get(name.decode('utf-8'))
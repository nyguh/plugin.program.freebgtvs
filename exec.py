# -*- coding: utf-8 -*-
import os, sys, xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs, re, urllib, sqlite3
import simplejson as json
#from ga import ga
from resources.lib.helper import *
from resources.lib.assets import *

DEBUG = True

def show_progress(a):
  if c_debug:
    _str = name
    if a.has_key('idx') and a.has_key('max'):
      _str += ' %s of %d' % (a['idx'], a['max'])
    dp.update(a['pr'], _str  , a['str'])

def debug_log(msg):
  if c_debug:
    xbmc.log('%s | %s' % (id, str(msg)))
    
addon = xbmcaddon.Addon()
id = addon.getAddonInfo('id')
name = addon.getAddonInfo('name').decode('utf-8')
cwd = xbmc.translatePath( addon.getAddonInfo('path') ).decode('utf-8')
profile_dir = xbmc.translatePath( addon.getAddonInfo('profile') ).decode('utf-8')
icon = addon.getAddonInfo('icon').decode('utf-8')
c_debug = True if addon.getSetting('debug') == 'true' else False
#db = xbmc.translatePath(os.path.join( cwd, 'resources', 'tv.db' ))
remote_db = 'https://github.com/harrygg/plugin.video.free.bgtvs/blob/master/resources/storage/tv.db.gz?raw=true'
db = Assets(profile_dir, remote_db)
try:
  if DEBUG == True: db = os.environ['BGTVS_DB']
except Exception:
  pass  
  
if c_debug:
  dp = xbmcgui.DialogProgressBG()
  dp.create(heading = name)

debug_log('Зареждане на канали от базата данни %s ' % db)
show_progress({'pr': 10, 'str': 'Зареждане на канали от базата данни'})

conn = sqlite3.connect(db)
cursor = conn.execute('''SELECT c.id, c.disabled, c.name, cat.name AS category, c.logo, COUNT(s.id) AS streams, s.stream_url, s.page_url, s.player_url, c.epg_id, u.string 
  FROM channels AS c 
  JOIN streams AS s ON c.id = s.channel_id 
  JOIN categories as cat ON c.category_id = cat.id
  JOIN user_agents as u ON u.id = s.user_agent_id
  WHERE c.disabled <> 1
  GROUP BY c.name, c.id
  ORDER BY c.id''')
  
show_progress({'pr': 20, 'str': 'Старт на генерирането на плейлиста'})
pl = Playlist()
show_progress({'pr': 25, 'str': 'Търсене на потоци'})
n = 25

for row in cursor:
  c = Channel(row)
  n += 1
  show_progress({'pr': n, 'str': 'Търсене на поток за канал %s' % c.name})
  debug_log('Търсене на поток за канал %s с id %s' % (c.name, c.id))
  if c.streams == 1 and c.playpath != '':
    pl.channels.append(c)
  else: #If we have more than one stream get all streams and select the default one
    cursor = conn.execute('''SELECT * FROM streams WHERE disabled <> 1 AND channel_id = %s AND ordering = 1''' % c.id)
    s = Stream(cursor.fetchone())
    c.playpath = s.url
    pl.channels.append(c)
  debug_log('Намерен поток за канал: %s' % c.playpath)
  
show_progress({'pr': 90, 'str': 'Записване на плейлиста'})
debug_log('Записване на плейлиста в %s ' % profile_dir)
pl.save(profile_dir)

### Apend/Prepend another playlist if specified
apf = addon.getSetting('additional_playlist_file')
if addon.getSetting('concat_playlist') == 'true' and os.path.isfile(apf):
  debug_log('Appending playlist %s' % apf)
  pl.concat(apf, addon.getSetting('append') == '1')
  pl.save(profile_dir)

### Copy playlist to additional folder if specified
ctf = addon.getSetting('copy_to_folder')
if addon.getSetting('copy_playlist') == 'true' and ctf and os.path.isdir(ctf):
  show_progress({'pr': 95, 'str': 'Копиране на плейлиста'})
  pl.save(ctf)
  
show_progress({'pr': 100, 'str': 'Генерирането на плейлистата завърши!'})
debug_log('Генерирането на плейлистата завърши!')

### Set next run
roi = int(addon.getSetting('run_on_interval')) * 60
debug_log('Настройване на AlarmClock. Следващото изпълнение на скрипта ще бъде след %s часа' % (roi / 60))
xbmc.executebuiltin('AlarmClock(%s, RunScript(%s, False), %s, silent)' % (id, id, roi))
 
###Restart PVR Sertice to reload channels' streams
xbmc.executebuiltin('XBMC.StopPVRManager')
xbmc.executebuiltin('XBMC.StartPVRManager')

if c_debug:
  dp.close()

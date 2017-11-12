# -*- coding: utf-8 -*-
import os
import json
import time
import xbmc
import xbmcgui
import sqlite3
import xbmcaddon
from ga import ga
from resources.lib.playlist import *
from resources.lib.assets import Assets

__DEBUG__ = True
if __DEBUG__:
  sys.path.append(os.environ['PYSRC'])
  import pydevd
  pydevd.settrace('localhost', stdoutToServer=False, stderrToServer=False)

def log(msg, level = xbmc.LOGNOTICE):
  if c_debug or level == 4:
    xbmc.log('%s | %s' % (id, msg), level)

def show_progress(percent, msg):
  if c_debug or is_manual_run:
    heading = name.encode('utf-8') + ' ' + str(percent) + '%'
    dp.update(percent, heading, msg)
    log(msg)

def update(action, location, crash=None):
  lu = addon.getSetting('last_update')
  day = time.strftime("%d")
  if lu == "" or lu != day:
    addon.setSetting('last_update', day)
    p = {}
    p['an'] = addon.getAddonInfo('name')
    p['av'] = addon.getAddonInfo('version')
    p['ec'] = 'Addon actions'
    p['ea'] = action
    p['ev'] = '1'
    p['ul'] = xbmc.getLanguage()
    p['cd'] = location
    ga('UA-79422131-8').update(p, crash)

def is_player_active():
  try:
    res = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Player.GetActivePlayers", "id":1}')
    player_id = json.loads(res)["result"][0]["playerid"]
    res = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Player.GetItem","params":{"properties":["channeltype","channelnumber"],"playerid":%s},"id":"id1"}' % player_id)
    item_type = json.loads(res)["result"]["item"]["type"]
    if item_type == "channel":
      xbmc.log("PVR is playing!")
      return True
  except Exception, er:
    xbmc.log(str(er))
  xbmc.log("PVR is not playing!")
  return False   
  
###################################################
### Settings
###################################################
is_manual_run = False if len(sys.argv) > 1 and sys.argv[1] == 'False' else True
if not is_manual_run:
  xbmc.log('%s | Автоматично генериране на плейлиста' % id)
addon = xbmcaddon.Addon()
id = addon.getAddonInfo('id')
name = addon.getAddonInfo('name').decode('utf-8')
cwd = xbmc.translatePath( addon.getAddonInfo('path') ).decode('utf-8')
profile_dir = xbmc.translatePath( addon.getAddonInfo('profile') ).decode('utf-8')
icon = addon.getAddonInfo('icon').decode('utf-8')
c_debug = True if addon.getSetting('debug') == 'true' else False
include_radios = False if addon.getSetting('include_radios') == 'false' else True
local_db = xbmc.translatePath(os.path.join( cwd, 'resources', 'tv.db' ))
url = 'https://github.com/harrygg/plugin.video.free.bgtvs/raw/master/resources/tv.db'
a = Assets(profile_dir, url, local_db, log)
db = a.file
try:
  db = os.environ['BGTVS_DB']
except Exception:
  pass  

###################################################
### Addon logic
###################################################
if is_player_active():
  xbmc.log("PVR is in use. Delaying playlist regeneration with 5 minutes")
  xbmc.executebuiltin('AlarmClock(%s, RunScript(%s, False), %s, silent)' % (id, id, 5))
else:
  if c_debug or is_manual_run:
    dp = xbmcgui.DialogProgressBG()
    dp.create(heading = name)

  show_progress(10, 'Зареждане на канали от базата данни %s ' % db)

  conn = sqlite3.connect(db)
  cursor = conn.execute(
    '''SELECT c.id, c.disabled, c.name, cat.name AS category, c.logo, 
      COUNT(s.id) AS streams, s.stream_url, s.page_url, s.player_url, c.epg_id, u.string, c.ordering 
    FROM channels AS c 
    JOIN streams AS s ON c.id = s.channel_id 
    JOIN categories as cat ON c.category_id = cat.id
    JOIN user_agents as u ON u.id = s.user_agent_id
    WHERE c.disabled <> 1
    GROUP BY c.name, c.id
    ORDER BY c.ordering''')
    
  show_progress(20,'Генериране на плейлиста')
  update('generation', 'PlaylistGenerator')

  pl = Playlist(include_radios)
  show_progress(25,'Търсене на потоци')
  n = 26

  for row in cursor:
    try:
      c = Channel(row)
      n += 1
      show_progress(n,'Търсене на поток за канал %s' % c.name)
      cursor = conn.execute(
        '''SELECT s.*, u.string AS user_agent 
        FROM streams AS s 
        JOIN user_agents as u ON s.user_agent_id == u.id 
        WHERE disabled <> 1 AND channel_id = %s AND preferred = 1''' % c.id)
      s = Stream(cursor.fetchone())
      c.playpath = s.url
      if c.playpath is None:
        xbmc.log('Не е намерен валиден поток за канал %s ' % c.name)
      else:
        pl.channels.append(c)
    except Exception, er:
      xbmc.log('Грешка при търсене на поток за канал %s ' % c.name)
      xbmc.log(str(er), xbmc.LOGERROR)
        
  show_progress(90,'Записване на плейлиста')
  pl.save(profile_dir)

  ###################################################
  ### Apend/Prepend another playlist if specified
  ###################################################
  apf = addon.getSetting('additional_playlist_file')
  if addon.getSetting('concat_playlist') == 'true' and os.path.isfile(apf):
    show_progress(92,'Обединяване с плейлиста %s' % apf)
    pl.concat(apf, addon.getSetting('append') == '1')
    pl.save(profile_dir)
    
  ###################################################
  ### Copy playlist to additional folder if specified
  ###################################################
  ctf = addon.getSetting('copy_to_folder')
  if addon.getSetting('copy_playlist') == 'true' and os.path.isdir(ctf):
    show_progress(95,'Копиране на плейлиста')
    pl.save(ctf)

  ####################################################
  ### Set next run
  ####################################################
  show_progress(98,'Генерирането на плейлистата завърши!')
  roi = int(addon.getSetting('run_on_interval')) * 60
  show_progress(99,'Настройване на AlarmClock. Следващото изпълнение на скрипта ще бъде след %s часа' % (roi / 60))
  xbmc.executebuiltin('AlarmClock(%s, RunScript(%s, False), %s, silent)' % (id, id, roi))
   
  ####################################################
  ###Restart PVR Sertice to reload channels' streams
  ####################################################
  xbmc.executebuiltin('XBMC.StopPVRManager')
  xbmc.sleep(1000)
  xbmc.executebuiltin('XBMC.StartPVRManager')

  if c_debug or is_manual_run:
    dp.close()

# -*- coding: utf-8 -*-
import os
import json
import time
import xbmc
import xbmcgui
import sqlite3
import xbmcaddon
from ga import ga
from urllib import quote
from resources.lib.playlist import *
from resources.lib.utils import *

      
def show_progress(percent, msg):
  if c_debug or is_manual_run:
    heading = name.encode('utf-8') + ' ' + str(percent) + '%'
    dp.update(percent, heading, msg)
    log(msg)

def update(action, location, crash=None):
  lu = settings.last_update
  day = time.strftime("%d")
  if lu == "" or lu != day:
    settings.last_update
    p = {}
    p['an'] = get_addon_name()
    p['av'] = get_addon_version()
    p['ec'] = 'Addon actions'
    p['ea'] = action
    p['ev'] = '1'
    p['ul'] = get_kodi_language()
    p['cd'] = location
    ga('UA-79422131-8').update(p, crash)   
  
###################################################
### Settings
###################################################
is_manual_run = False if len(sys.argv) > 1 and sys.argv[1] == 'False' else True
if not is_manual_run:
  log('%s | Автоматично генериране на плейлиста' % get_addon_id())


###################################################
### Addon logic
###################################################
if c_debug or is_manual_run:
  dp = xbmcgui.DialogProgressBG()
  dp.create(heading = name)

show_progress(5, 'Зареждане на канали от базата данни %s ' % db)

conn = sqlite3.connect(db)
cursor = conn.execute(
  '''SELECT c.id, c.name, c.logo, c.ordering, c.enabled, cat.name AS category, c.epg_id
  FROM freetvandradio_channel AS c 
  JOIN freetvandradio_channel_category AS cc
  JOIN freetvandradio_category AS cat
  ON c.id = cc.channel_id AND cc.category_id = cat.id
  WHERE c.enabled = 1
  GROUP BY c.id
  ORDER BY c.ordering''')
  
show_progress(8,'Генериране на плейлиста')
update('generation', 'PlaylistGenerator')

pl = Playlist()
pl_json = {}
pl.include_radios = settings.include_radios
show_progress(10,'Търсене на потоци')
n = 11

for row in cursor:
  name = None
  try:
    c = Channel(row)
    name = c.name
    n += 1
    show_progress(n,'Търсене на поток за канал %s' % name)
    cursor = conn.execute(
      '''SELECT s.*, u.string AS user_agent 
      FROM freetvandradio_stream AS s 
      JOIN freetvandradio_user_agent as u 
      ON s.user_agent_id = u.id 
      WHERE s.enabled = 1 
      AND s.channel_id = %s 
      AND preferred = 1''' % c.id)
    attr = cursor.fetchone()
    s = Stream( id=attr[0],
                stream_url=attr[1],
                page_url=attr[2],
                comment=attr[3],
                preferred=attr[4],
                channel_id=attr[7],
                enabled=attr[9],
                player_url=attr[10],
                user_agent=attr[11]
              )
                
    if s.url is None:
      log('Не е намерен валиден поток за канал %s ' % name)
    else:
      c.static_playpath = STREAM_URL % quote(name.encode("utf-8"))
      c.static_playpath += '|User-agent=%s' % s.user_agent
      c.static_playpath += '&Referer=%s' % s.player_url
      c.playpath = s.url
      pl.channels.append(c)
      pl_json[name.encode("utf-8")] = s.url
  except Exception, er:
    log('Грешка при търсене на поток за канал %s ' % name)
    log_last_exception()
      
show_progress(90,'Записване на плейлиста')
log('Записване на плейлиста в директория %s' % profile_dir, 2)
# save static playlist
pl.save(profile_dir)
# save dynamic playlist
pl.save(profile_dir, False)

# Save JSON playlist
try:
  log('Записване на JSON плейлиста в %s' % pl_json_path, 4)
  with open(pl_json_path, 'w') as w:
    w.write(json.dumps(pl_json, ensure_ascii=False).encode('utf8'))
except:
  log('Грешка при записване на плейлиста в JSON формат %s' % pl_json_path, 2)
  log_last_exception()

###################################################
### Apend/Prepend another playlist if specified
###################################################
# apf = settings.additional_playlist_file
# if settings.concat_playlist and os.path.isfile(apf):
  # show_progress(92,'Обединяване с плейлиста %s' % apf)
  # pl.concat(apf, settings.append == 1)
  # pl.save(profile_dir)
  
###################################################
### Copy playlist to additional folder if specified
###################################################
ctf = settings.copy_to_folder
if settings.copy_playlist and os.path.isdir(ctf):
  show_progress(95,'Копиране на плейлиста')
  pl.save(ctf)

####################################################
### Set next run
####################################################
show_progress(98,'Генерирането на плейлистата завърши!')
roi = int(settings.run_on_interval) * 60
show_progress(99,'Настройване на AlarmClock. Следващото изпълнение на скрипта ще бъде след %s часа' % (roi / 60))
xbmc.executebuiltin('AlarmClock(%s, RunScript(%s, False), %s, silent)' % (id, id, roi))
 
####################################################
###Restart PVR Sertice to reload channels' streams
####################################################
#xbmc.executebuiltin('XBMC.StopPVRManager')
xbmc.sleep(1000)
#xbmc.executebuiltin('XBMC.StartPVRManager')

if c_debug or is_manual_run:
  dp.close()

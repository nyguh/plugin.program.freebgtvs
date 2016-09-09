# -*- coding: utf-8 -*-
import os, xbmc, xbmcaddon, xbmcgui, sqlite3
from ga import ga
from resources.lib import *
from resources.lib.assets import Assets

def show_progress(percent, msg, level = xbmc.LOGDEBUG):
  if c_debug:
    heading = name.encode('utf-8') + ' ' + str(percent) + '%'
    dp.update(percent, heading, msg)
    xbmc.log('%s | %s' % (id, percent), level)

def update(action, location, crash=None):
	p = {}
	p['an'] = addon.getAddonInfo('name')
	p['av'] = addon.getAddonInfo('version')
	p['ec'] = 'Addon actions'
	p['ea'] = action
	p['ev'] = '1'
	p['ul'] = xbmc.getLanguage()
	p['cd'] = location
	ga('UA-79422131-7').update(p, crash)
  
###################################################
### Settings
###################################################
__DEBUG__ = False
addon = xbmcaddon.Addon()
id = addon.getAddonInfo('id')
name = addon.getAddonInfo('name').decode('utf-8')
cwd = xbmc.translatePath( addon.getAddonInfo('path') ).decode('utf-8')
profile_dir = xbmc.translatePath( addon.getAddonInfo('profile') ).decode('utf-8')
icon = addon.getAddonInfo('icon').decode('utf-8')
c_debug = True if addon.getSetting('debug') == 'true' else False
local_db = xbmc.translatePath(os.path.join( cwd, 'resources', 'tv.db' ))
url = 'http://offshoregit.com/harrygg/assets/tv.db.gz'
a = Assets(profile_dir, url, local_db, xbmc.log)
db = a.file
try:
  if __DEBUG__ == True: db = os.environ['BGTVS_DB']
except Exception:
  pass  

###################################################
### Addon logic
###################################################
if c_debug:
  dp = xbmcgui.DialogProgressBG()
  dp.create(heading = name)

show_progress(10, 'Зареждане на канали от базата данни %s ' % db)

conn = sqlite3.connect(db)
cursor = conn.execute('''SELECT c.id, c.disabled, c.name, cat.name AS category, c.logo, COUNT(s.id) AS streams, s.stream_url, s.page_url, s.player_url, c.epg_id, u.string 
  FROM channels AS c 
  JOIN streams AS s ON c.id = s.channel_id 
  JOIN categories as cat ON c.category_id = cat.id
  JOIN user_agents as u ON u.id = s.user_agent_id
  WHERE c.disabled <> 1
  GROUP BY c.name, c.id
  ORDER BY c.id''')
  
show_progress(20,'Генериране на плейлиста')
update('generation', 'PlaylistGenerator')
pl = Playlist(xbmc.log)
show_progress(25,'Търсене на потоци')
n = 26

for row in cursor:
  c = Channel(row)
  n += 1
  show_progress(n,'Търсене на поток за канал %s' % c.name)
  if c.streams == 1 and c.playpath != '':
    pl.channels.append(c)
  else: #If we have more than one stream get all streams and select the default one
    cursor = conn.execute('''SELECT * FROM streams WHERE disabled <> 1 AND channel_id = %s AND ordering = 1''' % c.id)
    s = Stream(cursor.fetchone(), xbmc.log)
    c.playpath = s.url
    pl.channels.append(c)
  
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
  update('concatenation', 'PlaylistGenerator')
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
xbmc.executebuiltin('XBMC.StartPVRManager')

if c_debug:
  dp.close()

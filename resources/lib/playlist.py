# -*- coding: utf8 -*-
import os
import re
import sys
import xbmc
import xbmcaddon
import json
import time
import requests
from kodibgcommon.utils import *

reload(sys)  
sys.setdefaultencoding('utf8')

class Playlist:
  name = 'playlist.m3u'
  channels = []
  raw_m3u = None
  append = True
  
  def __init__(self, name = ''):
    if name != '':
      self.name = name
  
  def save(self, path):
    file_path = os.path.join(path, self.name)
    xbmc.log("Запазване на плейлистата: %s " % file_path, xbmc.LOGNOTICE)
    if os.path.exists(path):
      with open(file_path, 'w') as f:
        f.write(self.to_string().encode('utf-8', 'replace'))
  
  def concat(self, new_m3u, append = True, raw = True):
    if raw: #TODO implement parsing playlists
      self.append = append
      with open(new_m3u, 'r') as f:
        self.raw_m3u = f.read().replace('#EXTM3U', '')
  
  def to_string(self):
    output = ''
    for c in self.channels:
      output += c.to_string()
      
    if self.raw_m3u != None:
      if self.append:
        output += self.raw_m3u
      else:
        output = self.raw_m3u + output
    
    return '#EXTM3U\n' + output

class Category:
	def __init__(self, id, title):
		self.id = id
		self.title = title
    
class Channel:

  def __init__(self, attr):
    self.id = attr[0]
    self.disabled = attr[1] == 1
    self.name = attr[2]
    self.category = attr[3]
    self.logo = attr[4]
    self.streams = attr[5]
    self.playpath = '' if attr[6] == None else attr[6]
    self.page_url = '' if attr[7] == None else attr[7]
    self.player_url = '' if attr[8] == None else attr[8]
    self.epg_id = '' if attr[9] == None else attr[9]
    self.user_agent = False if attr[10] == None else attr[10]

  def to_string(self):
    output = '#EXTINF:-1 radio="False" tvg-shift=0 group-title="%s" tvg-logo="%s" tvg-id="%s",%s\n' % (self.category, self.logo, self.epg_id, self.name)
    output += '%s\n' % self.playpath
    return output 
 
class Stream:
  def __init__(self, attr):
    self.id = attr[0] 
    xbmc.log("id=%s" % attr[0])
    self.channel_id = attr[1]
    xbmc.log("channel_id=%s" % attr[1])
    self.url = attr[2]
    self.page_url = attr[3]
    self.player_url = attr[4]
    self.disabled = attr[5] == 1
    self.comment = attr[6]
    self.user_agent = False if attr[9] == None else attr[9]
    if self.url == None:
      xbmc.log("Resolving playpath url from %s" % self.player_url, 4)
      self.url = self.resolve()
    if self.url is not None and self.user_agent: 
      self.url += '|User-Agent=%s' % self.user_agent
    if self.url is not None and self.page_url:
      self.url += '&Referer=%s' % self.page_url
    xbmc.log("Stream final playpath: %s" % self.url, xbmc.LOGERROR)
    
  def resolve(self):
    stream = None
    s = requests.session()
    headers = {'User-agent': self.user_agent, 'Referer':self.page_url}
    
    # If btv - custom dirty fix to force login
    if self.channel_id == 2:
      body = { "username": settings.btv_username, "password": settings.btv_password }
      headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
      r = s.post("https://btvplus.bg/lbin/social/login.php", headers=headers, data=body)
      xbmc.log(r.text, xbmc.LOGNOTICE)
      if r.json()["resp"] != "success":
        xbmc.log("Unable to login to btv.bg", xbmc.LOGERROR)
        return None

    self.player_url = self.player_url.replace("{timestamp}", str(time.time() * 100))
    xbmc.log(self.player_url, xbmc.LOGNOTICE)
    r = s.get(self.player_url, headers=headers)
    xbmc.log(r.text, 4)
    m = re.compile('(http.*\.m3u.*?)[\s\'"\\\\]+').findall(r.text)
    if len(m) > 0:
      stream = m[0].replace('\/', '/')
    else:
      xbmc.log("No match for playlist url found", xbmc.LOGNOTICE)
      
    xbmc.log('Намерени %s съвпадения в %s' % (len(m), self.player_url), xbmc.LOGNOTICE)
    xbmc.log('Извлечен видео поток %s' % stream, xbmc.LOGNOTICE)
    return stream

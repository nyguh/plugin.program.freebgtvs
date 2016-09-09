# -*- coding: utf8 -*-
import os, sys, requests, re

reload(sys)  
sys.setdefaultencoding('utf8')

class Playlist:
  name = 'playlist.m3u'
  channels = []
  raw_m3u = None
  append = True
  
  def __init__(self, log, name = ''):
    self.log = log
    if name != '':
      self.name = name
  
  def save(self, path):
    file_path = os.path.join(path, self.name)
    self.log("Запазване на плейлистата: %s " % file_path)
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
  
class Channel:
  #user_agent = 'stagefright/2.0'
  user_agent = 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
  
  def __init__(self, attr):
    self.id = attr[0]
    self.disabled = attr[1] == 1
    self.name = attr[2]
    self.category = attr[3]
    self.logo = attr[4]
    self.streams = attr[5]
    self.playpath = '' if attr[6] == None else attr[6]
    self.epg_id = '' if attr[9] == None else attr[9]
    self.user_agent = False if attr[10] == None else attr[10]

  def to_string(self):
    output = '#EXTINF:-1 radio="False" tvg-shift=0 group-title="%s" tvg-logo="%s" tvg-id="%s",%s\n' % (self.category, self.logo, self.epg_id, self.name)
    output += '%s' % self.playpath
    if self.user_agent: 
      output += '|User-Agent=%s' % self.user_agent
    return output + '\n'
 
class Stream:
  def __init__(self, attr, log):
    self.log = log
    self.id = attr[0] 
    self.channel_id = attr[1] 
    self.url = attr[2]
    self.page_url = attr[3]
    self.player_url = attr[4]
    self.disabled = attr[5] == 1
    self.comment = attr[6]
    self.user_agent = 'Mozilla/5.0 (Linux; Android 6.0; LG-H960; Build/WRA58K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.36'
    if self.url == None:
      self.url = self.resolve()
    
  def resolve(self):
    #if '3583019' in self.player_url: #BiT
    #	return self._livestream()
    headers = {'User-agent': self.user_agent, 'Referer':self.page_url}
    res = requests.get(self.player_url, headers=headers)
    m = re.compile('(http.*m3u.*?)[\s\'"]+').findall(res.text)
    self.log('Намерени %s съвпадения в %s' % (len(m), self.player_url))
    stream = '' if len(m) == 0 else m[0]
    self.log('Извлечен видео поток %s' % stream)
    #travelhd wrong stream name hack
    if 'playerCommunity' in self.player_url:
      stream.replace('/community/community', '/travel/community')
    return stream
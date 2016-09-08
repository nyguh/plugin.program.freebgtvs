# -*- coding: utf8 -*-
import os, gzip, urllib2, xbmc

class Assets:
  db_name = 'tv.db'
  
  def __init__(self, profile_path, remote_db):
    self.db_path = os.path.join(profile_path, self.db_name)
    self.remote_db = remote_db
    if self.is_update_assets():
      self.get_assets()

  def is_update_assets(self):
    try:
      from datetime import datetime, timedelta
      if os.path.exists(self.db_path):
        treshold = datetime.now() - timedelta(hours=24)
        fileModified = datetime.fromtimestamp(os.path.getmtime(self.db_path))
        if fileModified < treshold: #file is more than a day old
          return True
        return False
      else: #file does not exist, perhaps first run
        return True
    except Exception, er:
      xbmc.log(str(er))
      return False

  def get_assets(self):
    try:
      xbmc.log('Downloading assets from url: %s' % self.remote_db)
      save_to_file = self.db_path if '.gz' not in self.remote_db else self.db_path + ".gz"
      f = urllib2.urlopen(self.remote_db)
      if not os.path.exists(os.path.dirname(save_to_file)):
        create_dir(save_to_file)
      with open(save_to_file, "wb") as code:
        code.write(f.read())
      self.extract(save_to_file)
    except Exception, er:
      xbmc.log(str(er))
      xbmc.executebuiltin('Notification(%s,%s,10000,%s)' % ('Assets', 'Неуспешно сваляне на най-новата база данни!',''))
      assets = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../%s.gz' % self.db_name)
      self.extract(assets)
      
  def create_dir(path):
    try: os.makedirs(os.path.dirname(path))
    except OSError as exc: # Guard against race condition
      if exc.errno != errno.EEXIST:
        raise
      
  def extract(self, path):
    try:
      gz = gzip.GzipFile(path, 'rb')
      s = gz.read()
      gz.close()
      if not os.path.exists(os.path.dirname(self.db_path)):
        create_dir(self.db_path)      
      out = file(self.db_path, 'wb')
      out.write(s)
      out.close()
    except:
      raise
import sys
import os
import json

def map_controller(controllerName):
  folder = 'controller/keymap'
  for f in os.listdir(folder):
    fpath = os.path.join(folder, f)
    if os.path.isfile(fpath) and fpath.endswith('.json'):
      json_file = open(fpath)
      json_parsed = json.load(json_file)
      json_file.close()
      if controllerName in json_parsed['name']:
        return json_parsed
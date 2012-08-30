#!/usr/bin/env python
""" hostlists plugin to get hosts from a file """
import hostlists

def name():
  return ['type','type_vip','type_vip_up','type_vip_down']

def expand(value,name=None):
  """ Try all plugins of a specific type for a result, if none
  are able to expand the value further then return just the value """
  tmplist=[]
  mod_type='vip'
  if not name:
    return [value]
  if name.lower() in ['type_vip']:
    mod_type='vip'
    filter_append=''
  if name.lower() in ['type_vip_down']:
    mod_type='vip_down'
    filter_append='_down'
  if name.lower() in ['type_vip_up']:
    mod_type='vip_up'
    filter_append='_up'
  plugins=hostlists.hostlists._get_plugins()
  for plugin_name in plugins.keys():
    if ( 
      (filter_append != '' and plugin_name.endswith(filter_append)) or
      (filter_append == '' and plugin_name.find('_') == -1) 
    ):
      try:
        if mod_type in plugins[plugin_name].type():
          name=plugin_name+filter_append
          result=plugins[plugin_name].expand(value,name=name)
          if len(result):
            return result
      except AttributeError:
        pass
  return [value]
  

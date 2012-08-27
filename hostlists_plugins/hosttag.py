#!/usr/bin/env python
""" hosttag host plugin """

"""
 Copyright (c) 2012 Yahoo! Inc. All rights reserved.
 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,   
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License. See accompanying LICENSE file.
"""

"""
This hostlist plugin obtains host lists from the hosttag rest based web
service.

http://github.com/dwighthubbar/django-hosttags
"""
import os
import urllib2
import base64
import json
import hostlists

def name():
  """ Name of plugins this plugin responds to """
  return ['hosttag']

def type():
  return ['db']
  
def expand(value,name='hosttag',method=None):
  state='ALL'
  group='False'
  tags=''
  templist=[]

  # Parse the parameters passed
  temp=value.split(':')
  if len(temp):
    tags=temp[0]
    for index in range(0,len(temp)):
      temp2=temp[index].split('=')
      if len(temp2) == 2:
        if temp2[0].lower() == 'tags':
          tags=temp2[1]
        if temp2[0].lower() == 'group':
          group=temp2[1]
  else:
   return []
  # Get a list of servers from our settings and try each in turn
  settings=hostlists.get_setting('hosttag_plugin')
  for server in settings['servers']:
    url='http://%s/api/host?tags=%s&group=%s' % (server,tags,group)
    try:
      result=json.load(urllib2.urlopen(url))
    except urllib2.HTTPError:
      # Get an error from the server rest api
      result=[]
    if len(result):
      for host in result:
        templist.append(host['name'])
  return templist


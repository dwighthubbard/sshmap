#!/usr/bin/env python
""" 
A plugin extendable hostlist infrastructure 

This module provides functions for getting a list of hosts
from various systems as well as compressing the list into
a simplified list.

This module uses the hostlists_plugins python scripts
to actually obtain the listings.  
"""

"""
 Copyright (c) 2010 Yahoo! Inc. All rights reserved.
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

# Built in module imports
import os
import sys
import optparse
import site
import imp

# Global plugin cache so we don't constantly reload the plugin modules
global_plugins={}

def _get_plugins():
    """ Find all the hostlists plugins """
    plugins=global_plugins
    pluginlist=[]
    plugin_path=['/lib/hostlists']+sys.path
    for directory in plugin_path:
        if os.path.isdir(os.path.join(directory,'plugins')):
            templist=os.listdir(os.path.join(directory,'plugins'))
            for item in templist:
                pluginlist.append(os.path.join(os.path.join(directory,'plugins'),item))
    pluginlist.sort()
    # Create a dict mapping the plugin name to the plugin method
    for item in pluginlist:
        if item.endswith('.py'):
            #mod=__import__(item[:-3])
            mod=imp.load_module('hostlists_plugins_%s'% os.path.basename(item[:-3]),open(item),item,('.py','r',imp.PY_SOURCE))
            if mod.name() not in plugins.keys():
                plugins[mod.name().lower()]=mod
    return plugins

def expand(range_list):
    """ Expand a list of plugin:parameters into a list of hosts """
    if type(range_list) is str:
      range_list=[range_list]
      
    # Find all the host list plugins
    plugins=_get_plugins()
    
    # Iterate through our list
    newlist=[]
    found_plugin=False
    for item in range_list:
        # Is the item a plugin
        temp=item.split(':')
        if len(temp) > 1:
            plugin=temp[0].lower()
            # Do we have a plugin that matches the passed plugin
            if plugin in plugins.keys():
                # Call the plugin
                item=None
                newlist+=plugins[plugin].expand(':'.join(temp[1:]).strip(':'))
                found_plugin=True
        else:
            # Default to running through the range plugin
            item=None
            newlist+=plugins['range'].expand(temp[0])
        if item:
            newlist.append(item)
    # Recurse back through ourselves incase a plugin returns a value that needs to be parsed
    # by another plugin.  For example a dns resource that has an address that points to a
    # load balancer vip that may container a number of hosts that need to be looked up via
    # the load_balancer plugin.
    if found_plugin:
        newlist=expand(newlist)
    return newlist
        
def compress(range_list):
    """ Compress a list of hosts into a more compact range representation """
    # This is currently a simple stubbed out implementation that doesn't 
    # really compress at all.
    return ','.join(range_list).strip(',')

def range_split(range):
    """ Split up a range string, this needs to seperate comma seperated
    items unless they are within square brackets """
    in_brackets=False
    current=""
    result_list=[]
    for c in range:
        if c in ['[']:
            in_brackets=True
        if c in [']']:
            in_brackets=False
        if not in_brackets and c==',':
            result_list.append(current)
            current=""
        else:
            current+=c
    if len(current):
        result_list.append(current)
    return result_list
    
if __name__ == "__main__":
    parser = optparse.OptionParser(usage="usage: %prog [options] plugin:parameters")
    parser.add_option("-s","--sep",dest="sep",default=',',help="Seperator character, default=\",\"")
    parser.add_option("--onepass",dest="onepass",default=False,action="store_true")
    parser.add_option("--expand","-e",dest="expand",default=False,action="store_true",help="Expand the host list and dislay one host per line")
    (options, args) = parser.parse_args()
    range=range_split(','.join(args))
    
    if options.expand:
        print '\n'.join(expand(range))
    else:
        print compress(expand(range))
    
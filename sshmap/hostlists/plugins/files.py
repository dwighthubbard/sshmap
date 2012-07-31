#!/usr/bin/env python
""" hostlists plugin to get hosts from a file """

def name():
  return 'file'

def expand(value):
  tmplist=[]
  for host in [i.strip() for i in open(value,'r').readlines()]:
    if not host.startswith('#'):
      tmplist.append(host)
  return tmplist
  
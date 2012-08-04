#!/usr/bin/env python
""" hostlists plugin to get hosts from dns """
import dns.resolver

def name():
  return 'dns'

def expand(value):
  tmplist=[]
  adresses=[]
  try:
    answers = dns.resolver.query(value, 'A')
  except dns.resolver.NoAnswer:
    answers=[]
  try:
    answers = answers+dns.resolver.query(value,'CNAME')
  except dns.resolver.NoAnswer:
    pass
  for rdata in answers:
    print dir(rdata)
    tmplist.append(rdata.address)
  return tmplist
  
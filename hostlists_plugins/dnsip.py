#!/usr/bin/env python
""" hostlists plugin to get hosts from dns """
import dns.resolver

def name():
  return 'dnsip'

def expand(value):
  tmplist=[]
  adresses=[]
  try:
    answers = list(dns.resolver.query(value))
  except dns.resolver.NoAnswer:
    answers=[]
  for rdata in answers:
    tmplist.append(rdata.address)
  return tmplist
  
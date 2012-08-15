#!/usr/bin/env python
""" hostlists plugin to get hosts from dns """
import dns.resolver
import dns.reversename
def name():
  return 'dns'

def expand(value):
  tmplist=[]
  addresses=[]
  try:
    answers = list(dns.resolver.query(value))
  except dns.resolver.NoAnswer:
    answers=[]
  for rdata in answers:
    addresses.append(rdata.address)
  for address in addresses:
    result=dns.reversename.from_address(address)
    try:
      # See if we can reverse resolv the IP address and insert
      # it only if it's a unique hostname.
      revaddress=str(dns.resolver.query(result,'PTR')[0]).strip('.')
      if revaddress not in tmplist:
        tmplist.append(revaddress)
    except dns.resolver.NXDOMAIN:
      tmplist.append(address)
  # if the tmplist with the reverse resolved hostnames
  # is not the same length as the list of addresses then
  # the site has the same hostname assigned to more than 
  # one IP address dns reverse resolving
  # If this happens we return the IP addresses because
  # they are unique, otherwise we return the hostnames.
  if len(tmplist) < len(addresses):
    return addresses
  return tmplist
  
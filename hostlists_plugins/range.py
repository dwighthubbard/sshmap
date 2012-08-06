#!/usr/bin/env python
""" hostlists plugin to get hosts from a file """

def name():
  return 'range'

def expand(value):
  return expand_item(value)
    
def block_to_list(block):
  """ Convert a range block into a numeric list 
      input "1-3,17,19-20"
      output=[1,2,3,17,19,20]
  """
  block+=','
  result=[]
  val=''
  in_range=False
  for letter in block:
    if letter in [',','-']:
      if in_range:
        val2=int(val)
        result+=range(val1,val2+1)
        val=''
        val1=None
        in_range=False
      else:
        val1=int(val)
        val=''
      if letter == ',':
        if val1 != None:
          result.append(val1)
      else:
        in_range=True
    else:
      val+=letter
  return result
    
def expand_item(item):
  result=[]
  in_block=False
  pre_block=''
  for count in range(0,len(item)):
    letter=item[count]
    if letter == '[': 
      in_block=True
      block=''
    elif letter == ']' and in_block:
      in_block=False
      for value in block_to_list(block):
        result.append('%s%d%s'% (pre_block,value,item[count+1:]))
    elif in_block:
      block+=letter
    elif not in_block:
      pre_block += letter
  return result

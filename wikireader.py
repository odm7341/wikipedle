# -*- coding: utf-8 -*-
"""
Created on Thu May 12 10:25:48 2022

@author: omccl
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import random
# Making a GET request
r = requests.get('https://en.wikipedia.org/wiki/Wikipedia:Popular_pages')
 
# check status code for response received
# success code - 200
#print(r)
 
# print content of request
#print(r.content)

# Parsing the HTML
soup = BeautifulSoup(r.content, 'html.parser')

def is_valid_wiki_page(tag):
    td_rank = re.compile(r'\<td\>[0-9]+')
    if (tag.name == 'tr'):
        #print(str(tag.contents[1]))
        if (td_rank.match(str(tag.contents[1]))):
            return True
    return False

articles = soup.find_all(is_valid_wiki_page)



rand_idx = random.randint(0, len(articles))

print(articles[rand_idx])
    
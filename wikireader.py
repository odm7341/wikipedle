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
import json
import math

class wikiReader:
    def __init__(self):
        self.main_url = 'https://en.wikipedia.org/wiki/Wikipedia:Popular_pages'
        self.url_prefix = 'https://en.wikipedia.org'
        
    def is_valid_wiki_row(self, tag):
        td_rank = re.compile(r'\<td\>[0-9]+') # match td followed by valid rank
        if (tag.name == 'tr'):
            #print(str(tag.contents[1]))
            # only good if the rank is valid and it has a link
            if (td_rank.match(str(tag.contents[1])) and tag.find('a')):
                return True
        return False
    
    def get_articles(self):
        r = requests.get(self.main_url)
        if not r.ok:
            print('error')
            
        soup = BeautifulSoup(r.content, 'html.parser')
        articles = soup.find_all(self.is_valid_wiki_row)
        # put the articles into a dictionary
        article_lst = []
        for article in articles:
            # get the first occurance of a link
            article = article.find('a')
            article = [str(article['title']), self.url_prefix + str(article['href'])]
            
            article_lst.append(article)
        return article_lst
    
    def get_clues(self, pg_name, pg_url):
        r = requests.get(pg_url)
        if not r.ok:
            print('error')
        soup = BeautifulSoup(r.content, 'html.parser')
        
        short_des = soup.find('div', class_='shortdescription')
        print(short_des.text, '\n')
        
        '''
        paragraphs = soup.find_all('p')
        for par in paragraphs[1:]:
            par = par.text
            par = self.clean_clue(par, pg_name)
            par = par.split('. ')
            print(par)
        '''    
        paragraph = soup.find_all('p')[1]
        paragraph = paragraph.text
        paragraph = self.scrub_prop_noun(paragraph)
        #paragraph = paragraph.split('. ')
        print(paragraph)
        
        
    def clean_clue(self, clue, pg_name):
        keywords = pg_name.split(' ')
        for word in keywords:
            clue = re.sub(word, '***', clue, flags=re.M|re.I)
        return clue
    
    def scrub_prop_noun(self, clue):
        return re.sub(r'\b([A-Z][a-z]+)\b', '***', clue, flags=re.M)
        
        
        
        





if __name__ == '__main__':
    print('TESTS...')

    testReader = wikiReader()
    art = testReader.get_articles()
    i = random.randint(0, len(art))
    #i = 77
    print(i)
    ans = art[i][0]
    testReader.get_clues(art[i][0], art[i][1])
    
    

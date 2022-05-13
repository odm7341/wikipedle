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
import spacy

class wikiClues:
    def __init__(self):
        self.url_prefix = 'https://en.wikipedia.org'
        
    def is_valid_wiki_row(self, tag):
        td_rank = re.compile(r'\<td\>[0-9]+') # match td followed by valid rank
        if (tag.name == 'tr'):
            #print(str(tag.contents[1]))
            # only good if the rank is valid and it has a link
            if (td_rank.match(str(tag.contents[1])) and tag.find('a')):
                return True
        return False
    
    def get_pop_articles(self):
        r = requests.get('https://en.wikipedia.org/wiki/Wikipedia:Popular_pages')
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
        self.noun_set = set() # used for later when we censor nouns
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # clue 0
        short_des = soup.find('div', class_='shortdescription')
        clue_list = [short_des.text]
        
        # setup for paragraph based clues
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
        og_paragraph = paragraph
        print(og_paragraph)
        paragraph = re.sub(r'\(([^\)]+)\)', '', paragraph, flags=re.M) # remove ()
        paragraph = self.clean_clue(paragraph, pg_name) # no keywords
        # clue 1 (no proper nouns or keywords)
        clue1 = self.scrub_prop_noun(paragraph)
        clue_list.append(clue1)
        # clue 2 (first and last letters of prop nouns, no keywords)
        clue2 = self.censor_prop_noun(paragraph)
        clue_list.append(clue2)
        # clue 3 (show prop nouns, no keywords)
        
        
        return clue_list

        
    def get_clues_api(self, article):        
        text = self.parse(article[0])
        #print(text)
        header_re = re.compile(u'\ufffd.*$', flags=re.M|re.UNICODE)
        headers = []
        for match in header_re.findall(text):
            text = text.replace(match, '')
            match = match.replace('\ufffd', '')
            match = (' ' * int(int(match[0]) - 2)) + match[1:]
            headers.append(match)        
        
        nlp = spacy.load('en_core_web_sm')
        doc = nlp(text)
        sentences = [sent for sent in doc.sents]
        print(len(sentences))
        #for p in sentences:
        #   print(p, end='\n==\n')



    def clean_clue(self, clue, pg_name):
        keywords = pg_name.split(' ')
        for word in keywords:
            clue = re.sub(word, '***', clue, flags=re.M|re.I)
        return clue
    
    def scrub_prop_noun(self, clue):
        proper_noun = re.compile(r'\b([A-Z][a-z]+)\b', flags=re.M)
        for match in proper_noun.findall(clue):
            clue = clue.replace(match, '***')
            self.noun_set.add(match)
        
        return clue
    
    def censor_prop_noun(self, clue):
        for noun in self.noun_set:
            for match in re.finditer(noun, clue):
                strt = match.start()
                end = match.end()
                clue_char = list(clue)
                length = (end-1) - (strt + 1)
                clue_char[strt+1:end] = '*' * (length+1)
                clue = ''.join(clue_char)
        return clue
    
    def parse(self, title):
        API_URL = "https://en.wikipedia.org/w/api.php"
        params = {
        	"action": "query",
        	"format": "json",
        	"prop": "extracts",
        	"titles": title,
        	"explaintext": 1,
        	"exsectionformat": "raw"
        }
        headers = {"User-Agent": "Wikipedle/1.0"}
        req = requests.get(API_URL, headers=headers, params=params)
        res = req.json()
        res = res["query"]["pages"]
        text = res[next(iter(res))]['extract']
        return text
                  
        
        
def test_non_api(testReader, art):
    i = random.randint(0, len(art))
    i = 152
    print(i)
    ans = art[i][0]
    clue_list = testReader.get_clues(art[i][0], art[i][1])
    for c in clue_list:
        print(c)


def test_api(testReader, articles):
    i = 152
    h = testReader.get_clues_api(art[152])
    print(h)
    #for hs in h:
    #    print(hs)


if __name__ == '__main__':
    print('TESTS...')

    testReader = wikiClues()
    art = testReader.get_pop_articles()
    #test_non_api(testReader, art)
    test_api(testReader, art)
    
    

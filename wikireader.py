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
        paragraph = self.scrub_keywords(paragraph, pg_name) # no keywords
        # clue 1 (no proper nouns or keywords)
        clue1 = self.scrub_prop_noun(paragraph)
        clue_list.append(clue1)
        # clue 2 (first and last letters of prop nouns, no keywords)
        clue2 = self.censor_prop_noun(paragraph)
        clue_list.append(clue2)
        # clue 3 (show prop nouns, no keywords)
        
        
        return clue_list

        
    def get_clues_api(self, search_term):
        useless_headers = ['See also', 'Notes', 'References', 'Further reading', 'External links']
        text = self.parse_by_title(search_term)
        #print(title)
        headers, content  = self.format_sections(text)
        
        content = ''.join(content)
        
        
        nlp = spacy.load('en_core_web_sm')
        doc = nlp(content)        
        sentences = [sent for sent in doc.sents]
        
        if (len(sentences) < 20):
            print('article too small')
            return
        sen_clues = []
        sen_clues.append(''.join(sentences[:5]))
        sen_clues.append(''.join(sentences[5:10]))
        sen_clues.append(''.join(sentences[10:15]))
        sen_clues.append(''.join(sentences[15:20]))
        
        for clue in sen_clues:
            clue = self.scrub_keywords(clue, self.title)
            clue = self.scrub_prop_noun(clue)
            
        return sen_clues


    def format_sections(self, text):
        match_pat = re.compile(u'(\ufffd.*$)', flags=re.M|re.UNICODE)
        junk_headers = ['See also', 'Notes', 'References', 'Further reading', 'External links']
        headers = []
        content = []
        sep_text = match_pat.split(text)
        content.append(sep_text[0])
        for i in range(1, len(sep_text), 2):
            heading = sep_text[i].replace('\ufffd', '')
            if (heading[1:] in junk_headers):
                pass
            elif (int(heading[0]) <= 2):
                headers.append(self.scrub_keywords(heading[1:], self.title))
                content.append(self.scrub_parens(sep_text[i+1]))
            else:
                content.append(self.scrub_parens(sep_text[i+1]))
                
        return headers, content


    def scrub_keywords(self, text, keyword):
        keywords = keyword.split(' ')
        for word in keywords:
            text = text.replace(word, '***')
        return text
    
    def scrub_parens(self, text):
        text = re.sub(r'\(([^\)]+)\)', '', text, flags=re.M) # remove ()
        text = re.sub(r'\[(.*?)\]', '', text, flags=re.M) # remove []
        return text
    
    def scrub_prop_noun(self, clue):
        proper_noun = re.compile(r'\b([A-Z][a-z]+)\b', flags=re.M)
        for match in proper_noun.findall(clue):
            clue = clue.replace(match, '***')
            self.noun_set.add(match)
        
        return clue
    
    def censor_prop_noun(self, clue):
        # must call scrub_proper_noun first
        for noun in self.noun_set:
            for match in re.finditer(noun, clue):
                strt = match.start()
                end = match.end()
                clue_char = list(clue)
                length = (end-1) - (strt + 1)
                clue_char[strt+1:end] = '*' * (length+1)
                clue = ''.join(clue_char)
        return clue
    
    def parse_by_title(self, title):
        API_URL = "https://en.wikipedia.org/w/api.php"
        headers = {"User-Agent": "Wikipedle/1.0"}
        params_query = {
        	"action": "query",
        	"format": "json",
        	"list": "search",
        	"srsearch": title,
            "srenablerewrites": 1
        }
        req = requests.get(API_URL, headers=headers, params=params_query)
        res = req.json()
        page_id = res["query"]["search"][0]['pageid']
        
        params_extract = {
        	"action": "query",
        	"format": "json",
        	"prop": "extracts",
        	"pageids": page_id,
        	"explaintext": 1,
        	"exsectionformat": "raw"
        }        
        req = requests.get(API_URL, headers=headers, params=params_extract)
        res = req.json()
        text = res["query"]["pages"][str(page_id)]['extract']
        self.title = res["query"]["pages"][str(page_id)]['title']
        return text
                  
        
        
def test_non_api(testReader, art):
    i = random.randint(0, len(art))
    #i = 152
    print(i)
    ans = art[i][0]
    clue_list = testReader.get_clues(art[i][0], art[i][1])
    for c in clue_list:
        print(c)


def test_api(testReader, articles):
    i = random.randint(0, len(art))
    i = 152
    print(i)
    #h = testReader.get_clues_api(art[i][0])
    h = testReader.get_clues_api('Expanse novel')
    #for hs in h:
    #    print(hs)
    return h, art[i][0]


if __name__ == '__main__':
    print('TESTS...')

    testReader = wikiClues()
    art = testReader.get_pop_articles()
    #test_non_api(testReader, art)
    clue, ans = test_api(testReader, art)
    
    

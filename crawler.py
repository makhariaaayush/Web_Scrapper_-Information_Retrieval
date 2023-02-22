import nltk
import os
import re
import string
import math
import queue
import threading
import ssl
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from nltk import PorterStemmer
from pathlib import Path
from bs4 import BeautifulSoup

stopword_path = Path( 'stopwords.txt' )
stopword_list = []
list_of_stop = set()


def Stopwords_Function():
    file = open( Path( 'stopwords.txt' ), 'r' )
    for stop in file:
        stop = re.split( "\n", stop.lower() )
        list_of_stop.add( stop[0] )
    file.close()

Stopwords_Function()

stemmer = PorterStemmer()

in_index = {}
prankScores = {}

def Preprocessor_Function(b):
    if b not in list_of_stop:
        b_1 = set( string.punctuation )
        b_2 = ''.join( x for x in b if x not in b_1 )
        b_3 = ''.join( [i for i in b_2 if not i.isdigit()] )
        stem_word = stemmer.stem( b_3 )
        if stem_word not in list_of_stop:
            return stem_word
        return 'b'
    return 'b'

class Node_Function():
    def __init__(self, source_url):
        self.url = source_url
        self.edges = set()
        self.score = 0
        self.times = 0

    def Add_Edge_Function(self, destination_url):
        if destination_url not in self.edges:
            self.edges.add( destination_url )
            self.times += 1

def Page_Rank_Function(a):
    dF = 0.85
    n = 10
    v = len(a)

    for url, urlNode in a.items():
        urlNode.score = 1 / float(v)

    for i in range( n ):
        d = 0
        us = {}
        for url, urlNode in a.items():
            if (len( urlNode.edges ) == 0):
                d += urlNode.score / v
                continue
            temp = urlNode.score / urlNode.times
            for destination_url in urlNode.edges:
                if destination_url not in us:
                    us[destination_url] = temp
                else:
                    us[destination_url] += temp
        for url in a:
            val = 0
            if url in us:
                val = us[url]
            a[url].score = (1 - dF) * (1 / float( v )) + dF * (val + d)

    for url, urlNode in a.items():
        prankScores[url] = urlNode.score

def Web_Parser_Function(currUrl, q, unique, vocabulary, urlGraph):
    req = Request( currUrl )
    try:
        response = urlopen( currUrl )
    except HTTPError:
        return
    except URLError:
        return
    except ssl.CertificateError:
        return

    soup = BeautifulSoup( response, from_encoding=response.info().get_param( 'charset' ) )

    urls = []
    for abc in soup.find_all( 'a', href=True ):
        abc = abc['href']
        if abc.find( '#' ):
            abc = abc.split( '#' )
            abc = abc[0]
        if len( abc ) >= 1 and abc[-1] != '/':
            abc += '/'
        abcParts = abc.split('://')
        if len( abcParts ) > 1 and abcParts[0][:4] == 'http':
            if len( abcParts[0] ) > 4 and abcParts[0][4] == 's':
                abcParts[0] = 'http'
            if abcParts[1][:4] == "www.":
                abcParts[1] = abcParts[1][4:]
            parts = abcParts[1].split( '/' )
            if 'uic.edu' in parts[0]:
                urls.append( abcParts[0] + '://' + abcParts[1] )
        if len( abcParts ) == 1:
            if len( abcParts[0] ) > 1 and abcParts[0][0] == '/':
                urls.append( currUrl + abcParts[0][1:] )

    if currUrl not in urlGraph:
        urlGraph[currUrl] = Node_Function( currUrl )
    for aUrl in urls:
        if aUrl not in unique:
            unique.add( aUrl )
            q.put( aUrl )
            if aUrl not in urlGraph:
                urlGraph[aUrl] = Node_Function( aUrl )
            urlGraph[currUrl].Add_Edge_Function( aUrl )

    c = soup.find_all( ('p', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6') )
    for object in c:
        text = object.text.strip()
        c = text.lower()
        generator = c.split()

        for t in generator:
            t = Preprocessor_Function( t )
            if not (len( t ) < 3):
                if t not in in_index:
                    in_index[t] = {}
                    in_index[t][currUrl] = 1
                    vocabulary[t] = 1
                else:
                    if currUrl in in_index[t]:
                        in_index[t][currUrl] += 1
                    else:
                        in_index[t][currUrl] = 1
                    vocabulary[t] += 1

def Save_Function():
    with open('InvertedIndex.json', 'w') as fp:
        json.dump( in_index, fp )
    with open('PageRankScores.json', 'w') as fp:
        json.dump( prankScores, fp )

def Web_Crawl_Function(startUrl):
    q = queue.Queue()
    unique = set()
    q.put(startUrl)
    unique.add(startUrl)
    count = 1
    vocab = {}
    urlGraph = {}

    while count < 3000 and not q.empty():
        if q.qsize() > 100:
            urlCrawlers = [threading.Thread( target=Web_Parser_Function, args=([q.get(), q, unique, vocab, urlGraph]),
                                             kwargs={} ) for x in range( 75 )]
            for subCrawler in urlCrawlers:
                subCrawler.start()
            for subCrawler in urlCrawlers:
                subCrawler.join()
            count += 100
        else:
            Web_Parser_Function( q.get(), q, unique, vocab, urlGraph )
            count += 1
        print( count )
    Page_Rank_Function( urlGraph )

    Save_Function()


Web_Crawl_Function( 'http://www.cs.uic.edu/' )
import json, nltk, os, re, math, string
from nltk import PorterStemmer
from pathlib import Path
from flask import Flask, render_template, request

in_index_path = Path( 'InvertedIndex.json' )
prank_path = Path( 'PageRankScores.json' )

list_of_stop = set()
in_index = {}
prankScores = {}


def Stopwords_Function():
    file = open( Path( 'stopwords.txt' ), 'r' )
    for stop in file:
        # stop = stop.lower()
        stop = re.split( "\n", stop.lower() )
        list_of_stop.add( stop[0] )
    file.close()


Stopwords_Function()

stemmer = PorterStemmer()


# def Tokenizer_Function(a):
#     a_1 = a.lower()
#     generatedTokens = a_1.split()
#     return generatedTokens


def Preprocessor_Function(b):
    if b not in list_of_stop:
        b_1 = set( string.punctuation )
        b_2 = ''.join( ch for ch in b if ch not in b_1)
        b_3 = ''.join( [i for i in b_2 if not i.isdigit()] )
        stem_word = stemmer.stem( b_3 )
        if stem_word not in list_of_stop:
            return stem_word
        return 'b'
    return 'b'


with open( in_index_path ) as f:
    in_index = json.load( f )
with open( prank_path ) as f:
    prankScores = json.load( f )


def IDF_Function(c):
    for w in in_index:
        idf_dic[w] = math.log( (float( c ) / u_freq[w]), 2 )
        for c_1 in in_index[w]:
            in_index[w][c_1] *= idf_dic[w]
            if c_1 in u_dens:
                u_dens[c_1] += in_index[w][c_1] ** 2
            else:
                u_dens[c_1] = in_index[w][c_1] ** 2


# Compute the rank of pages based on the page ranking scores
def Rank_Page_Function():
    rankList = []
    for u, s in prankScores.items():
        rankList.append( (s, u) )
    rankList.sort( reverse=True )
    for i, v in enumerate( rankList ):
        rankDict[v[1]] = i + 1


# Method for parsing the query and finding its tf-idf and cosine similarity scores to find top 200 pages
def Query_Processing_Function(user_query, similar_list, idf_dic, u_dens, rankDict):
    queryIndex = {}
    a_1 = user_query.lower()
    generatedTokens = a_1.split()
    for aToken in generatedTokens:
        text = Preprocessor_Function( aToken )
        if (text == "b"):
            continue
        if text not in queryIndex:
            queryIndex[text] = 1
        else:
            queryIndex[text] += 1

    queryUrlFreq = {}
    queryDen = 0

    # Compute query scores
    for w in queryIndex:
        if w in in_index:
            for url in in_index[w]:
                if url in queryUrlFreq:
                    queryUrlFreq[url] += in_index[w][url] * idf_dic[w] * queryIndex[w]
                else:
                    queryUrlFreq[url] = in_index[w][url] * idf_dic[w] * queryIndex[w]
            queryDen += (queryIndex[w] * idf_dic[w]) ** 2

    similar_score = []
    for url in u_dens:
        if url in queryUrlFreq:
            score = queryUrlFreq[url] / math.sqrt( u_dens[url] * queryDen )
        else:
            score = 0
        similar_score.append( (score, url) )
    similar_score.sort( reverse=True )
    similar_list.append( similar_score[0:30] )


# Find the top 20 pages out of the 200 pages using Page Rank Scores
def Ranks_Function(similar_list, rankDict):
    finalRank = []
    for page in similar_list:
        tempArr = []
        for val in page:
            if val[1] in rankDict:
                tempArr.append( (rankDict[val[1]], val[1]) )
        tempArr.sort()
        finalRank.append( tempArr[0:20] )
    finalRank = finalRank[0]
    for i in range( len( finalRank ) ):
        finalRank[i] = finalRank[i][1]
    return finalRank


u_freq = {}
for w, urlDict in in_index.items():
    u_freq[w] = len( urlDict )
idf_dic = {}
u_dens = {}
rankDict = {}
IDF_Function(3000)
Rank_Page_Function()

# Flask application
app = Flask( __name__ )


@app.route( '/' )
def Search_Function():
    return render_template( 'search.html' )


final_Rank = []


@app.route( '/', methods=['POST'] )
def get_user_input():
    if request.form['submit_button'] == 'Search':
        user_query = request.form['inputQuery']
        # global finalRankings
        similar_list = []
        Query_Processing_Function( user_query, similar_list, idf_dic, u_dens, rankDict )
        final_Rank = Ranks_Function( similar_list, rankDict )
        print( final_Rank )
        return render_template( 'search.html', your_list=enumerate( final_Rank[:10] ) )


if __name__ == '__main__':
    app.run()
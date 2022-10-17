from typing import AnyStr, List, Dict

from urllib.request import urlopen
from bs4 import BeautifulSoup as bs

import nltk
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.SearchEngine
link_list: List = []


def word_separator(words: AnyStr):
    content = nltk.word_tokenize(str(words))
    return content


def read_html(web_site: AnyStr):
    """
    Open and read page content.
    """
    try:
        html = urlopen(web_site)
        page_content = bs(html.read().decode(encoding='UTF-8'), 'html.parser')
        return page_content
    except ConnectionError:
        return


def get_all_link(page_content):
    """
    Finds all links and save in a list.
    """
    try:
        for tag in page_content.find_all('a'):
            link_list.append(tag.get('href'))
        return link_list
    except ConnectionError:
        return ''


def add_to_index(index: Dict[Dict[AnyStr, Dict]], word: AnyStr, url: AnyStr):
    """
    Create an index
    :index: {word: {'url', rank}, }
    :word: Search item
    :url: Pages that are searched
    """
    index[word] = {url: 'rank'}


def add_page_to_index(index: Dict[Dict[AnyStr, Dict]], url: AnyStr, content):
    """
    :index: {word:{'url', rank}, }
    :url: Pages
    :content: A sentence containing words.
    """
    words = word_separator(content)
    for word in words:
        add_to_index(index, word, url)


def crawl_web(seed: AnyStr):
    """
    Crawling into web and create graph
    :seed: Start page URL
    :return: ({word:{'url', rank},... }, graph)
    """
    to_crawl = [seed]
    crawled = []
    index = {}
    graph = {}  # web graph
    while to_crawl:
        url = to_crawl.pop(0)
        if url not in crawled:
            content = read_html(url)
            add_page_to_index(index, url, content)
            out_links = get_all_link(content)
            # Update the graph
            graph[url] = out_links
            # Union
            for link in out_links:
                if link not in to_crawl:
                    to_crawl.append(link)
            crawled.append(url)
    return index, graph


def compute_rank(graph: Dict):
    """
    Page rank algorithm
    :graph: {url: [links, ]}
    :return: {Url: 'probability'}
    """
    d = 0.9  # Damping factors
    num_loops = 10
    num_pages = len(graph)

    ranks = {}
    for page in graph:
        ranks[page] = 1.0 / num_pages

    for i in range(num_loops):
        new_rank = {}
        for page in graph:
            new_rank_var = (1 - d) / num_pages
            if page is not None:
                for node in graph:
                    if page in graph[node] and len(graph[node]) != 0:  # 'Page' may contain 'None Type' data !
                        new_rank_var = new_rank_var + d * (ranks[node] / len(graph[node]))
                new_rank[page] = new_rank_var
        ranks = new_rank
    return ranks


def insert_to_database(seed: AnyStr):
    """
    insert data to database and give rank for each page
    :seed: Seed page URL
    """
    index, graph = crawl_web(seed)  # index and graph are dictionaries
    ranks = compute_rank(graph)  # ranks is dictionary
    for symbol, url_dic in index.items():
        for key in url_dic.keys():  # keys are urls
            url_dic[key] = ranks[key]
        db.reviews.insert({'word': symbol, 'url': url_dic}, check_keys=False)


def main():
    seed_page = 'https://sokanacademy.com/'  # Can be change :)
    insert_to_database(seed_page)


main()

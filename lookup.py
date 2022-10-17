from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.SearchEngine


def lookup(search_item: str):
    """
    Search for keywords in database
    """
    find_result = db.reviews.find({'word': search_item}, {'_id': 0}).sort('url')
    for query in find_result:
        for i in query['url']:
            print(i)


def main():
    search_here = input('Search here... ')
    lookup(search_here)


main()

"""
This module handles the incoming requests to the Bookmark tagging service.
"""

from flask import Flask, request, render_template
from flask_restful import Resource, Api

from web_scraper import Scraper
from nlp import NLP
import db

app = Flask(__name__)
api = Api(app)


@app.route('/', methods=['GET'])
def connect():
    return render_template("index.html")


class BookmarkTagger(Resource):
    """
    Handles get and post requests to the /tags endpoint.
    """

    def __init__(self):
        db.init_db()

    def get(self):
        '''
        Search bookmarks using tags.
        '''

        request_data = request.get_json()
        tags = request_data['tags']

        url_lists = []

        for tag in tags:
            data_for_tag = db.get_urls("user_1", tag.lower())
            urls_for_tag = []
            if data_for_tag is not None:
                for datum in data_for_tag:
                    urls_for_tag.append(datum[1])
                url_lists.append(urls_for_tag)
        common_urls = []
        if len(url_lists) > 0:
            common_urls = list(set(url_lists[0]).intersection(*url_lists))

        return {'urls': common_urls}, 200  # return data with 200 OK

    def post(self):
        '''
        Handles tagging and adding a new bookmark to the database.
        '''

        request_data = request.get_json()
        urls = request_data['urls']
        urls = [url for url in urls if url.startswith('http')]
        if len(urls) == 0:
            return {'message': 'No valid urls found'}, 400
        scrapper = Scraper(urls)
        parsing_results = scrapper.parsing
        for result in parsing_results:
            if "heading" not in result:
                result["heading"] = ""
            if "description" not in result:
                result["description"] = ""
            if "subheading" not in result:
                result["subheading"] = ""
        # print(parsingResults)
        keywords = NLP(parsing_results).get_keywords()

        keywords = [list(i) for i in keywords]

        for i, url in enumerate(urls):
            for tag in keywords[i]:
                db.add_row(("user_1", url, tag))

        print("Keywords extracted: ", keywords)

        return {'tags': keywords}, 200  # return data with 200 OK


api.add_resource(BookmarkTagger, '/tags')  # add endpoint

if __name__ == '__main__':
    app.run()

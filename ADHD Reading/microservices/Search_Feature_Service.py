import json
from flask import Flask, jsonify, request
import string
import os




app = Flask(__name__)

@app.route("/search", methods=["POST"])
def search():

    search_request = request.get_json()

    print("search request received")
    for key, value in search_request.items():
        print(key, value)

    # Exit the program if a kill command is received.
    if "kill" in search_request and search_request["kill"]:
        os._exit(0)

    is_string = isinstance(search_request["data_source"], str)
    is_list = isinstance(search_request["data_source"], list)
    # TO BE POTENTIALLY IMPLEMENTED:
    # is_integer = isinstance(search_request["data_source"], int)
    # is_dict = isinstance(search_request["data_source"], dict)

    # If data_source type is a string, perform string search.
    if is_string:
        # If search request calls for a file lookup, look for json file:
        if search_request["file_lookup"]:
            data = search_file_json(search_request)
        # Otherwise, do a string search:
        else:
            results = search_string(search_request)
            data = {"search_term": results[0], "count": results[1]}

    elif is_list:
        results = search_string(search_request)

        # If 'results' contains only the query itself, the word was not found.
        if len(results) == 1:
            print("Word not found")
            data = {"search_term": results[0]}
        else:
            data = {"search_term": results[0], "count": results[1], "first_index": results[2]}

    else:
        data = "No search performed."



    return jsonify(data)

def search_string(search_request: dict):
    data_source = search_request["data_source"]
    query = search_request["query"]



    # Strict search will find only exact matches, not including substrings.
    # (i.e. "bee" is not "bees" count = 0)
    if search_request["strict"]:
        text = search_request["data_source"]
        words = [
            w.strip(string.punctuation).lower()
            for w in text.split()
        ]
        try:
            count = words.count(str(query))
        except Exception as e:
            print(f"{e} error 1")
            return (query,)
    else:
        # Loose search, will return count of substrings in other strings
        # (i.e. "bee" is in "bees" count = 1)
        try:
            count = data_source.count(str(query))
            first_instance = data_source.index(str(query))
            return query, count, first_instance
        except Exception as e:
            print(f"{e} error 2")
            return (query,)

    return query, count

def search_file_json(search_request: dict):
    data = {}

    filepath = search_request["data_source"]
    query = search_request["query"]

    with open(filepath, "r") as file:
        data_source = json.load(file)

    # If multiple queries, (AKA 'query' param is a list) search for all queries.  
    if isinstance(query, list):
        for q in query:
            try:
                data[q] = data_source[q]
            except KeyError:
                print(f"Queries not found in filepath: {filepath}")
                data[q] = None
    # If singular query, just search for the one query.
    else:
        data[query] = data_source[query]

    return data

def contains():

    pass

if __name__ == "__main__":
    app.run(port=8001)

















































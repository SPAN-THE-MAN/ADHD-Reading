import json
from flask import Flask, jsonify, request
import os
import re


app = Flask(__name__)

@app.route("/chunk", methods=["POST"])
def chunk_text():

    chunk_request = request.get_json()
    print("Chunk request received")
    for key, value in chunk_request.items():
        print(key, value)

    if "kill" in chunk_request and chunk_request["kill"]:
        print("Terminating...")
        os._exit(0)


    chunked_text = [w for w in chunk_request["contents"].split() if w]
    print(chunked_text)

    return jsonify(chunked_text)


if __name__ == "__main__":
    app.run(port=8003)









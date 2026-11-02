import json
from flask import Flask, jsonify, request
import os


app = Flask(__name__)

# Creates 'Notes' folder if there isn't one.
os.makedirs(fr"Notes", exist_ok=True)



@app.route("/upload", methods=["POST"])
def upload_file():

    upload_request = request.get_json()

    print("Upload request received")
    for key, value in upload_request.items():
        print(key, value)

    if "kill" in upload_request and upload_request["kill"]:
        os._exit(0)


    filepath = upload_request["filepath"]
    file_contents = upload_request["file_contents"]

    try:
        if filepath[-4:] == ".txt":
            with open(fr"{filepath}", "w") as f:
                f.write(file_contents)  # writes exactly what you have
        else:
            with open(fr"{filepath}", "w") as f:
                json.dump(file_contents, f, indent=4)
        status_code = 201
        return {"success": True, "status_code": status_code, "status_message": status_code_handling(status_code)}
    except Exception as e:
        print(e)
        status_code = 500
        return {"success": False, "status_code": status_code, "status_message": status_code_handling(status_code)}



def status_code_handling(status_code):

    # Server side status codes
    status_code_dict = {
        200: "Ok - Request succeeded",
        201: "Created - Resource successfully created",
        202: "Accepted - Request accepted, processing later",
        204: "No Content - Success, no response body",
        500: "Internal Server Error – Generic server failure",
        501: "Not Implemented – Server does not support request",
        502: "Bad Gateway - Invalid response from upstream server",
        503: "Service Unavailable - Server overloaded or down",
        504: "Gateway Timeout - Upstream server did not respond"
    }

    return status_code_dict[status_code]



if __name__ == "__main__":
    app.run(port=8002)
























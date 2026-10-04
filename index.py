"""Minimal health endpoint. Importing this module does not start a server."""

import os

from bottle import Bottle, run


app = Bottle()


@app.route("/")
def hello_world():
    return "hello world"


if __name__ == "__main__":
    run(app=app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

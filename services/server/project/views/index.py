from flask import render_template

from project.manage import app


@app.route('/', methods=["GET"])
@app.route('/<path:text>', methods=["GET"])
def index(text=None):
    return render_template("index.html")


print("Finished loading index.py routes.")

from flask import render_template

from project.manage import app


@app.route('/', methods=["GET"])
def index():
    return render_template("index.html")


print("Finished loading index.py routes.")

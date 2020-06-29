

if __name__ == "__main__":
    from project.manage import app
    app.run(threaded=True, host=app.host, port=app.port, debug=True)
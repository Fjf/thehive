from gevent import monkey
monkey.patch_all()

from geventwebsocket import WebSocketServer

if __name__ == "__main__":
    from project.manage import app

    http_server = WebSocketServer(('0.0.0.0', 5001), app)
    http_server.serve_forever()
    # app.run(threaded=True, host=app.host, port=app.port, debug=True)

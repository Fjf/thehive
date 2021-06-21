import asyncio
import json
import queue
import threading
import time



class Bot:
    def __init__(self, app, interval=0.1):
        self.app = app
        self.queue = queue.Queue()

        self.thread = threading.Thread(target=self.queue_handler)
        self.thread.daemon = True

        self.interval = interval
        self.running = True

    def start(self):
        self.thread.start()

    def stop(self):
        self.running = False

    def queue_handler(self):
        from project.manage import sio
        from project.socket.game import system_chat

        print("Started bot queue handler thread.")
        while self.running:
            time.sleep(self.interval)
            try:
                room = self.queue.get(block=False)

                self.app.games[room].ai_move("minimax")

                with self.app.test_request_context('/'):
                    board_state = json.dumps(self.app.games[room].export())

                    sio.emit("boardState", board_state, json=True, include_self=True)

                if self.app.games[room].n_children() == 0:
                    self.app.games[room].node.contents.board.contents.turn += 1
                    system_chat("No moves available, skipping turn.")
                    self.queue.put(room)
            except queue.Empty as e:
                pass
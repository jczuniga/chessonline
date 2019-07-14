from _thread import start_new_thread
from board import Board
import logging

import random
import os
import pickle
import time
import socket
import sys

'''
Basic logging config
    For server file
        To be used for debugging purposes

'''

logFile = os.path.join('log', 'server.log')  # log file for server

stdout_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler(logFile)
handlers = [stdout_handler, file_handler]

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s:%(name)s: %(levelname)s : %(message)s',
                    handlers=handlers
                    )

log = logging.getLogger(__name__)


'''
Socket instance
'''
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP Connection
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # TCP socket conn config
# server, port numbers
server = "192.168.254.103"
port = 50056

server_ip = socket.gethostbyname(server)

try:
    s.bind((server, port))
except socket.error as e:
    log.error("Error binding IP and port address: %s" % str(e))

s.listen()
log.info("Waiting for a connection...")

connections = 0

games = {0: Board(8, 8)}

spectator_ids = []
specs = 0


def read_specs():
    global spectator_ids

    spectator_ids = []
    try:
        with open("specs.txt", "r") as f:
            for line in f:
                spectator_ids.append(line.strip())
    except Exception:
        log.error("No specs.txt file found, creating one...")
        open("specs.txt", "w")


def threaded_client(conn, game, spec=False):
    global pos, games, currentId, connections, specs

    if not spec:
        name = None
        bo = games[game]

        if connections % 2 == 0:
            currentId = "w"
        else:
            currentId = "b"

        bo.start_user = currentId

        # Pickle the object and send it to the server
        data_string = pickle.dumps(bo)

        if currentId == "b":
            bo.ready = True
            bo.startTime = time.time()

        conn.send(data_string)
        connections += 1

        while True:
            if game not in games:
                break

            try:
                d = conn.recv(8192 * 3)
                data = d.decode("utf-8")
                if not d:
                    break
                else:
                    if data.count("select") > 0:
                        all = data.split(" ")
                        col = int(all[1])
                        row = int(all[2])
                        color = all[3]
                        bo.select(col, row, color)

                    if data == "winner b":
                        bo.winner = "b"
                        log.info("[RESULT] Player b won in game {}".format(game))
                    if data == "winner w":
                        bo.winner = "w"
                        log.info("[RESULT] Player w won in game {}".format(game))

                    if data == "update moves":
                        bo.update_moves()

                    if data.count("name") == 1:
                        name = data.split(" ")[1]
                        if currentId == "b":
                            bo.p2Name = name
                        elif currentId == "w":
                            bo.p1Name = name

                    '''

                    Commented out: Stack trace looping error (TypeError)
                        FOR DEBUGGING

                        # debug 1: Changed str concat to .format() func
                            # Persisting error: logging loop

                    '''
                    # log.info("Received board from {0} in game {1}".format(currentId, game))

                    if bo.ready:
                        if bo.turn == "w":
                            bo.time1 = 900 - (time.time() - bo.startTime) - bo.storedTime1
                        else:
                            bo.time2 = 900 - (time.time() - bo.startTime) - bo.storedTime2

                    sendData = pickle.dumps(bo)

                    '''

                    Commented out: Stack trace looping error (TypeError)
                        FOR DEBUGGING

                        # debug 1 : Changed str concat to .format() func
                         # Persisting error: logging loop

                    '''
                    # log.info("Sending board to player {0} in game {1}".format(currentId, game))

                conn.sendall(sendData)

            except Exception as e:
                log.error(e)

        connections -= 1
        try:
            del games[game]
            log.info("Game {0} ended".format(game))
        except Exception:
            pass
        log.info("[DISCONNECT] Player {0} left game {1}".format(name, game))
        conn.close()

    else:
        available_games = list(games.keys())
        game_ind = 0
        bo = games[available_games[game_ind]]
        bo.start_user = "s"
        data_string = pickle.dumps(bo)
        conn.send(data_string)

        while True:
            available_games = list(games.keys())
            bo = games[available_games[game_ind]]
            try:
                d = conn.recv(128)
                data = d.decode("utf-8")
                if not d:
                    break
                else:
                    try:
                        if data == "forward":
                            log.info("[SPECTATOR] Moved Games forward")
                            game_ind += 1
                            if game_ind >= len(available_games):
                                game_ind = 0
                        elif data == "back":
                            log.info("[SPECTATOR] Moved Games back")
                            game_ind -= 1
                            if game_ind < 0:
                                game_ind = len(available_games) -1

                        bo = games[available_games[game_ind]]
                    except Exception:
                        log.error("[ERROR] Invalid Game Received from Spectator")

                    sendData = pickle.dumps(bo)
                    conn.sendall(sendData)

            except Exception as e:
                log.error(e)

        log.info("[DISCONNECT] Spectator left game {}".format(game))
        specs -= 1
        conn.close()


while True:
    read_specs()
    time.sleep(random.randint(3, 5))
    if connections < 6:
        conn, addr = s.accept()
        spec = False
        g = -1
        log.info("[CONNECT] New connection")
        log.info("[CONNECT] Received connection from {0}:{1}".format(addr[0], addr[1]))

        for game in games.keys():
            if games[game].ready is False:
                g = game

        if g == -1:
            try:
                g = list(games.keys())[-1]+1
                games[g] = Board(8, 8)
            except Exception:
                g = 0
                games[g] = Board(8, 8)

        if addr[0] in spectator_ids and specs == 0:
            spec = True
            log.info("[SPECTATOR DATA] Games to view: ")
            log.info("[SPECTATOR DATA]".format(games.keys()))
            g = 0
            specs += 1

        log.info("[GAME_INFO] Number of Connections: {}".format(connections+1))
        log.info("[GAME_INFO] Number of Games: {}".format(len(games)))

        start_new_thread(threaded_client, (conn, g, spec))


# Chess Online

Description: An online multiplayer chess game. Supports infinite players playing against random opponents on different machines on different networks. This project was created using python 3.7, pygame and the sockets module from python3. It allows the creation of a game server to establish connection between hosts using the two basic types of connection in the network layer (TCP | UDP).


# Requirements:
- Python 3.x
- pygame
- pip module (or easy_install)


# TO RUN
You will need to change the server address from within the following two files:
- client.py
- server.py

You will also need to run server.py on some kind of server. After that you can launch two instances of game from anywhere to play online chess.


# Known Bugs:
- Checkmate does not work, if you loose or win you will need to end the game by hitting "q"
- Very rare bug where a certain move will crash the game
- No Castling and Pawn Promotion rule yet (to be added on next update)



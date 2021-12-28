# Blackjack-game
Blackjack project splitted into multiple modules.

Base module - blackjack_base.py:
The core logic of the game with all the base classes, written in an OOD. This module is can be run both synchronously and asynchronously with AsyncIO.

Offline module - offline.py:
Runs the game from the terminal synchronously.

Online modules includes server.py & client.py:
The server is an event-driven sanic server working with Socket.IO protocol.
To start the server - `python server.py`.
To connect a client, run `python client.py`. 

Upon connecting, each player is assigned to a room which is automatically opened.

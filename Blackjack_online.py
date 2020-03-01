import logging
from abc import ABC
from Blackjack_base import Player, BlackJackGameBase
from flask import Flask, request
from flask_socketio import SocketIO, join_room, rooms
import time

logging.basicConfig(level=logging.DEBUG)
# TODO: https://realpython.com/async-io-python/ USE ASYNC while waiting for usr input
# =========================================================================================================
# ************************************************* Server ************************************************
# =========================================================================================================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
socketio = SocketIO(app)

sid_name_money_room_dictionary = {}  # {sid: {'name': players_name, 'money': players_money, 'room': room_number}}
game_room = {}  # room_num: {'game_instance': BlackJackGame(), 'sid_list': [sid_1, sid_2..]}}
# game_room is a dictionary containing an instance of BlackJackGame class and a list of players SID in that room.

MAX_NUMBER_OF_PLAYERS_IN_ROOM = 6


def open_game_room(room_num):
    time.sleep(1)
    game_room[room_num] = {}
    game_room[room_num]['game_instance'] = BlackJackGameOnline(room_num, socketio)
    game_room[room_num]['sid_list'] = []


def close_game_room(room_num):
    del game_room[room_num]


@socketio.on('connect')
def handle_connect():
    client_sid = request.sid  # request.sid is populated through the context of the call
    print("client SID = %s has connected, Requesting name" % client_sid)

    socketio.emit("send_me_name", room=client_sid)


@socketio.on('get_name')
def get_name(name):
    logging.info("got Name: %s ", name)
    client_sid = request.sid
    sid_name_money_room_dictionary[client_sid] = {'name': name, 'money': None, 'room': None}
    socketio.emit("send_me_money", room=client_sid)


@socketio.on('get_money')
def get_money(money):
    sid = request.sid
    name = sid_name_money_room_dictionary[sid]['name']
    logging.info("Received money from %s: %s", name, money)

    try:
        money = int(money)
        if money <= 0:
            logging.info("Got a negative number from %s", name)
            socketio.emit("send_me_money", room=sid)
        else:
            sid_name_money_room_dictionary[sid]['money'] = money
            socketio.emit("join_a_room", room=sid)
    except TypeError:
        logging.exception("Could not convert money from %s to Integer. \nsid=%s\nRequesting money again", name, sid)
        socketio.emit("send_me_money", room=sid)


@socketio.on('join')
def add_user_to_room():
    # TODO: CLIENT STOPS RECEIVING when entering this function.
    # when I kill the server the client suddenly gets the TEST MSG, and then disconnects

    socketio.send("TEST MSG!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", room=request.sid)

    name = sid_name_money_room_dictionary[request.sid]['name']
    if len(game_room) == 0:
        logging.info("All rooms are empty. Adding %s to room 1", name)
        socketio.send("TEST 2222222222222!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", room=request.sid)

        open_game_room(1)
        join_room(room=1, sid=request.sid)
        socketio.send("You joined room 1", room=request.sid)
        sid_name_money_room_dictionary[request.sid]['room'] = 1
        game_room[1]['sid_list'].append(request.sid)
        game_room[1]['game_instance'].add_player(sid_name_money_room_dictionary[request.sid]['name'],
                                                 sid_name_money_room_dictionary[request.sid]['money'],
                                                 request.sid)
        game_room[1]['game_instance'].play_round()

    else:
        logging.debug("Searching for room...")
        room_to_join = find_most_populated_room()
        join_room(room_to_join)

        logging.info("Adding %s to room %d", sid_name_money_room_dictionary[request.sid]['name'], room_to_join)
        socketio.send("%s has joined the room" % name, room=room_to_join)
        sid_name_money_room_dictionary[request.sid]['room'] = room_to_join
        game_room[room_to_join]['sid_list'].append(request.sid)  # add player to server list
        game_room[room_to_join]['game_instance'].add_player(sid_name_money_room_dictionary[request.sid]['name'],
                                                            sid_name_money_room_dictionary[request.sid]['money'],
                                                            request.sid)


def send_text_to_user(text, sid):
    socketio.send(text, room=sid)


def send_text_to_all_clients_in_the_room(text, room):
    socketio.send(text, room=room)


@socketio.on('disconnect')
def handle_disconnected_user():
    pass
    # name_of_client = sid_name_money_dictionary[request.sid]
    # logging.info("Client %s has disconnected", name_of_client)
    # for room in [x for x in rooms(sid=request.sid) if not x == request.sid]:
    #     socketio.send("%s has left" % name_of_client, room=room)
    # del sid_name_money_dictionary[request.sid]


@socketio.on('get_input')
def handle_input_from_user(player_input):
    player_sid = request.sid
    room_of_player = sid_name_money_room_dictionary[player_sid]['room']
    logging.info("Received: %s from: %s", player_input, sid_name_money_room_dictionary[player_sid]['name'])
    game_room[room_of_player]['game_instance'].update_user_input(player_input)


def find_most_populated_room():
    room_with_max_players = 0
    for room in game_room:
        num_of_players_in_room = len(game_room[room][1])
        if num_of_players_in_room == MAX_NUMBER_OF_PLAYERS_IN_ROOM - 1:
            return room

        if room_with_max_players < num_of_players_in_room:
            room_with_max_players = room
    return room_with_max_players


def get_input_from_user(msg, sid):
    logging.debug("SEND 'send_input' TO USER WITH SID = %s", sid)
    socketio.emit("send_input", data=msg, room=sid)


# =========================================================================================================
# ******************************************** BlackJack Online *******************************************
# =========================================================================================================

class OnlinePlayer(Player, ABC):
    def __init__(self, name, socketio, sid, amount_of_money=0):
        super().__init__(name, amount_of_money)
        self._sid = sid
        self._input = None
        self._socketio = socketio

    def _get_input_from_user(self,
                             msg):  # method to request strings (i.e names, how many players, etc) through websocket
        self._input = None
        logging.debug("asking user input with the following message: %s", msg)
        # get_input_from_user(msg, self._sid)
        socketio.send("TEST MSG!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", room=self._sid)
        socketio.emit("send_input", data=msg, room=self._sid)
        while self._input is None:
            # logging.debug("WAITING FOR INPUT........")
            continue
        logging.debug("Got input. Name: %s. Input: %s", self.get_players_name, self._input)
        return self._input  # updated externally through the game instance on the server

    def update_user_input(self, user_input):
        self._input = user_input

    @staticmethod
    def output_msg_to_user(text, sid):
        send_text_to_user(text, sid)


class BlackJackGameOnline(BlackJackGameBase):

    def __init__(self, room, socketio):
        super().__init__()

        self._players_sid = []
        self._num_of_players = 0
        self._room = room
        self._socketio = socketio
        print("BLACKJACK GAME INSTANCE CREATED. ROOM = %d", room)

    def _add_player(self, name, money, sid):
        pass

    def add_player(self, name, money, sid):
        logging.info("Adding player. \nName: %s\nMoney: %d\nSID: %s", name, money, sid)
        player = OnlinePlayer(name, self._socketio, sid, money)
        self._players_sid.append(sid)
        self._players[sid] = player

    def remove_player_from_game(self, player_sid):
        del self._players[player_sid]
        self._players_sid.remove(player_sid)

    def _end_connection_with_player(self, sid):
        raise NotImplementedError

    def output_msg_to_game(self, text):
        send_text_to_all_clients_in_the_room(text, self._room)

    @staticmethod
    def _round_finished(players_in_round):
        for player in players_in_round:
            player.cards.empty_all_cards()


if __name__ == '__main__':
    socketio.run(app, debug=False, log_output=False)


import logging
from blackjack_base import Player, BlackJackGameBase
import socketio
import sanic
import asyncio
import time

'''
1)
'''

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(module)s | %(lineno)d | %(process)d | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

# =========================================================================================================
# ************************************************* Server ************************************************
# =========================================================================================================

sio = socketio.AsyncServer(async_mode='sanic', logger=False)
app = sanic.app.Sanic(name='TestServer')
sio.attach(app)

event_loop = asyncio.get_event_loop()

sid_to_room = {}
games_list = []  # room numbers and game numbers are always equal.
MAX_NUMBER_OF_PLAYERS_IN_ROOM = 6


# =========================================================================================================
# ******************************************* Server Methods **********************************************
# =========================================================================================================

@sio.event
async def connect(sid: str, evniron):
    logging.info("Client %s connected", sid)
    room_number = find_most_populated_room()
    sid_to_room[sid] = room_number
    sio.enter_room(sid=sid, room=room_number)
    logging.info("Finished creating room")
    await sio.emit(to=sid, event='send login data to server')


@sio.on('get login data from client')
async def put_client_in_room(sid: str, name: str, money: str):
    try:
        assert int(money) > 0
        money = int(money)
        await add_player_to_room(sid, name, money)
    except (ValueError, AssertionError):
        logging.exception("Bad money argumnet from client %s with SID %s", name, sid)
        await sio.emit(event='message', to=sid, data="Server received bad input, disconnecting")
        await sio.disconnect(sid=sid)
        # TODO: check if room needs to be deleted


@sio.on('get input from user')
async def put_user_input_into_player_instance_queue(sid, data):
    client_room_num = sid_to_room[sid]
    player = [x for x in games_list[client_room_num].players if x.id == sid][0]  # get player instance from room
    await player.put_user_input_in_queue(data)


def find_most_populated_room() -> int:
    logging.debug("Searching for room")
    if len(games_list) == 0:
        open_room(1)
        return 1
    try:
        return sorted([x for x in games_list if x.num_of_players_in_room < MAX_NUMBER_OF_PLAYERS_IN_ROOM],
                      key=lambda game: game.num_of_players_in_room)[-1].room_number
    except IndexError:
        logging.info("All rooms are full")
        open_room()
        return games_list[-1].room_number


def open_room(room_num: int = None) -> None:
    if room_num is None:
        room_num = games_list[-1].room_number + 1
    logging.info("Opening room # %d", room_num)
    game_instance = BlackJackGameOnline(room_num=room_num)
    games_list.append(game_instance)
    asyncio.create_task(game_instance.play_round())


async def add_player_to_room(sid: str, name: str, money: int) -> None:
    player = OnlinePlayer(name=name, sid=sid, amount_of_money=int(money))
    client_room_num = sid_to_room[sid]
    games_list[client_room_num].add_player(player=player)
    msg = "Welcome %s to room %d" % (name, client_room_num)
    await send_msg_to_room(msg, client_room_num)


async def send_msg_to_user(msg, sid):
    await sio.send(data=msg, room=sid)


async def send_msg_to_room(msg, room):
    await sio.send(data=msg, room=room)


# =========================================================================================================
# ******************************************** BlackJack Online *******************************************
# =========================================================================================================

class OnlinePlayer(Player):

    def __init__(self, name: str, sid: str, amount_of_money: int = 0):
        Player.__init__(self, name=name, id=sid, amount_of_money=amount_of_money)
        self.q = asyncio.Queue()

    async def _request_input_from_user(self, msg) -> None:
        await sio.emit("send input to server", data=msg, to=self.id)

    async def put_user_input_in_queue(self, usr_input) -> None:
        await self.q.put(usr_input)

    async def _get_input_from_user(self) -> str:
        return await self.q.get()

    async def msg_to_user(self, text):
        await sio.send(data=text, to=self._id)

    def get_bet(self):
        raise NotImplementedError

    async def get_cmd(self, msg, list_of_valid_actions):
        while True:
            await self._request_input_from_user(msg)
            user_input = await self._get_input_from_user()
            logging.info("Got input from user: %s", user_input)
            user_action = self._convert_command_to_Action(user_input)
            if user_action not in list_of_valid_actions:
                logging.info(
                    "Got invalid Action %s from %s",
                    user_action,
                    self.get_players_name,
                )
                continue
            return user_action


class BlackJackGameOnline(BlackJackGameBase):
    def __init__(self, room_num: str):
        super().__init__()
        self._num_of_players = 0
        self._room_num = room_num
        logging.info("BlackJackGameOnline instance created. ROOM # = %d", room_num)

    @property
    def room_number(self) -> int:
        return int(self._room_num)

    @property
    def num_of_players_in_room(self):
        return self._num_of_players

    def add_player(self, player):
        self.players.append(player)
        self._num_of_players = len(self.players)

    def remove_player_from_game(self, player_sid):
        # TODO: rewrite this method
        del self.players[player_sid]
        self._num_of_players = len(self.players)

    def _end_connection_with_player(self, sid):
        # TODO: rewrite this method
        raise NotImplementedError

    async def output_msg_to_game(self, text):
        await send_msg_to_room(text, self.room_number)


if __name__ == '__main__':
    logging.info("******************************Starting server******************************")
    app.run(host='localhost', port=5000, auto_reload=True)

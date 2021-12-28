import socketio
import logging
import asyncio


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(module)s | %(lineno)d | %(process)d | %(message)s"
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

SERVER_ADDRESS = 'http://127.0.0.1:8000'
BJ_NAMESPACE = "/blackjack"
sio = socketio.AsyncClient(logger=True)


@sio.event(namespace=BJ_NAMESPACE)
async def connect():
    logging.info('Connected to server')


async def send_user_details():
    logging.info("Requesting name")
    money = None
    name = input("Welcome to my BlackJack game. What's your name?\n")
    while len(name) == 0:
        input("Name can't be an empty string. Type your name again, then press enter.\n")

    print(f"Welcome {name}. How much money would you like to bet?\nPlease enter a positive integer.")
    while money is None or money < 0:
        try:
            money = int(input())
        except ValueError:
            print("Value not permitted. Enter a positive integer.\n")
            continue

    await sio.emit('get_new_player_data', data=(name, str(money)), namespace=BJ_NAMESPACE)


@sio.on('message', namespace=BJ_NAMESPACE)
def handle_msg(data):
    print(data)


@sio.on("send_input", namespace=BJ_NAMESPACE)
async def send_input(msg):
    logging.debug("Requesting user input")
    res = input(msg)
    await sio.emit(event='get input from user', data=res, namespace=BJ_NAMESPACE)


async def main():
    logging.info("Attempting connection")
    await sio.connect(SERVER_ADDRESS, namespaces=BJ_NAMESPACE)
    await send_user_details()
    await sio.wait()

if __name__ == '__main__':
    asyncio.run(main())

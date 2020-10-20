import socketio
import logging
import asyncio

logging.basicConfig(level=logging.DEBUG)
SERVER_ADDRESS = 'http://127.0.0.1:5000'
sio = socketio.AsyncClient()

namespace = None


@sio.on("send login data to server")
async def get_name_and_money():
    logging.info("Requesting name")
    money = None
    name = input("Welcome to my BlackJack game. What's your name?\n")
    while len(name) == 0:
        input("Name can't be an empty string. Type your name again, then press enter.\n")

    print("Welcome %s. How much money would you like to bet?\nPlease enter a positive integer.\n" % name)
    while money is None or money < 0:
        try:
            money = int(input())
        except ValueError:
            print("Value not permitted. Enter a positive integer.\n")
            continue

    await sio.emit(event='get login data from client', data=(name, str(money)))


@sio.on('message')
def handle_msg(data):
    print(data)


@sio.on("send input to server")
async def send_input(msg):
    logging.debug("Requesting user input")
    res = input(msg)
    await sio.emit(event='get input from user', data=res)


async def main():
    logging.info("Attempting connection")
    await sio.connect(SERVER_ADDRESS)
    await sio.wait()

if __name__ == '__main__':
    asyncio.run(main())

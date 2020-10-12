import socketio
import logging

logging.basicConfig(level=logging.DEBUG)
sio = socketio.Client()


@sio.on('message')
def handle_msg(data):
    print(data)


@sio.event
def send_me_name(data):
    sio.emit('get_name', data=input("What's your name? "))


@sio.event
def send_me_money(data):
    sio.emit('get_money', data=input("How much money do you have? (enter a positive integer)"))


@sio.event
def join_a_room(data):
    print("Joining a room...")
    sio.emit('join')


@sio.event
def send_input(msg):
    logging.debug("Got command from server 'send_input' with msg %s")
    print(msg)


if __name__ == "__main__":
    sio.connect('http://localhost:5000')
    sio.wait()  # wait for connection to end

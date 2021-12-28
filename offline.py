import logging
import asyncio
from blackjack_base import (
    Player,
    BlackJackGameBase,
)
import uuid

logging.basicConfig(level=logging.DEBUG)


class OffLinePlayer(Player):
    def __init__(self, name: str, id: str, amount_of_money: int = 0):
        super().__init__(name, id, amount_of_money)

    def _get_input_from_user(self, msg):
        return input(msg)

    def get_cmd(self, msg, list_of_valid_actions):
        while True:
            user_input = self._get_input_from_user(msg)
            logging.info("Got input from user: %s", user_input)
            user_action = self._convert_command_to_Action(user_input)
            if user_action not in list_of_valid_actions:
                logging.info(
                    "Got un-allowed Action %s from %s",
                    user_action,
                    self.get_player_name,
                )
                continue
            return user_action

    @staticmethod
    def msg_to_user(msg):
        print(msg)


class BlackJackGameOffLine(BlackJackGameBase):
    def __init__(self):
        super().__init__()
        self._num_of_players = 0
        self._take_num_of_players()
        self._create_players()

    def _take_num_of_players(self):
        logging.debug("BlackJack game taking number of players from user")

        while self._num_of_players <= 0:
            try:
                self._num_of_players = int(
                    self.get_input_from_user("Enter number of players: ")
                )
                logging.info(
                    "BlackJack game created with %d players", self._num_of_players
                )

                if self._num_of_players < 0:
                    self.output_msg_to_game("Enter a positive integer!")
                else:
                    break

            except ValueError:
                self.output_msg_to_game("Enter a positive integer!")
                self._num_of_players = 0

    def _create_players(self):
        for i in range(self._num_of_players):
            money_of_player = -1
            msg = "Enter players name: "
            logging.debug("Taking players name")

            name = self.get_input_from_user(msg)

            while (money_of_player < 0) or (not type(money_of_player) is int):
                try:
                    logging.debug("Taking %s amount of money", name)
                    money_of_player = int(
                        self.get_input_from_user(
                            "%s - How much money do you have?\n" % name
                        )
                    )

                    if money_of_player < 0:
                        self.output_msg_to_game("Enter a positive number!!")
                        continue

                except ValueError:
                    logging.exception("User entered an illegal value")
                    continue

            player = OffLinePlayer(
                name=name, amount_of_money=money_of_player, id=uuid.uuid4().hex[:8]
            )
            self.add_player(player)

    def remove_player_from_game(self, player):
        self.players.remove(player)

    def _end_connection_with_player(self, player_id):
        player = self.players[player_id]
        logging.info("Ending connection with player")
        player.msg_to_user("You don't have any money left. Reconnect to play again.")

    def output_msg_to_game(self, msg):
        print(msg)

    @staticmethod
    def get_input_from_user(msg):
        return input(msg)


async def main():
    bj_game = BlackJackGameOffLine()
    await bj_game.play_round()


if __name__ == "__main__":
    asyncio.run(main())

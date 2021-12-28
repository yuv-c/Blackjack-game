from enum import Enum
import random
import logging
import abc
import asyncio

class NoMoreCardsInDeckError(Exception):
    pass


class CardAlreadyInDeckError(Exception):
    pass


class PlayerHasNoMoneyError(Exception):
    pass


SAME_AS_THE_BET = 1
ONE_AND_A_HALF_TIMES_THE_BET = 1.5
TWICE_AS_THE_BET = 2
ACE_VALUE = 11


class Suites(Enum):
    HEARTS = 1
    DIAMONDS = 2
    SPADES = 3
    CLUBS = 4


class Actions(Enum):
    HIT = 1
    STAND = 2
    BET = 3
    SKIP = 4
    DOUBLE = 5
    SURRENDER = 6


SUITES_TO_ICON = {
    Suites.HEARTS: "♥",
    Suites.CLUBS: "♣",
    Suites.DIAMONDS: "♦",
    Suites.SPADES: "♠",
}

ALL_CARD_RANKS = list(range(2, 11)) + list("JQKA")


class Card(object):
    def __init__(self, suit, rank):
        self._suit = suit
        self._rank = rank

    @property
    def suit(self):
        return self._suit

    @property
    def rank(self):
        return self._rank

    @property
    def text_image(self):
        return "[%s of %s ]" % (self.rank, SUITES_TO_ICON[self.suit])

    def __eq__(self, other):
        return self.suit == other.suit and self.rank == other.rank

    def __str__(self):
        return "<Card %s of %s>" % (self.rank, self.suit.name)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(str(self.rank) + str(self.suit.name))


class Deck(object):
    def __init__(self):
        self._deck = []

    def __eq__(self, other):  # implemented only for sorted decks

        if len(self._deck) != len(other._deck):
            return False

        for i in range(len(self._deck)):
            if self._deck[i] != other._deck[i]:
                return False
        return True

    def __len__(self):
        return len(self._deck)

    def shuffle(self):
        random.shuffle(self._deck)

    @property
    def cards(self):
        return self._deck

    @property
    def return_deck_as_icons(self):
        cards_image_list = []

        for card in self.cards:
            cards_image_list.append(card.text_image)

        str_of_deck_as_icons = ", ".join(cards_image_list)
        return str_of_deck_as_icons

    def draw_card(self):
        try:
            return self._deck.pop()
        except IndexError:
            raise NoMoreCardsInDeckError()

    def take_card(self, card, top_of_deck=True):
        if card in self._deck:
            raise CardAlreadyInDeckError("Card %s already in deck" % card)

        if top_of_deck:
            self._deck.append(card)
        else:
            self._deck.insert(0, card)

    def empty_all_cards(self):
        for _ in self.cards:
            self._deck.pop()

    def fill_deck_with_52_cards(self):
        self._deck = []
        for card_rank in ALL_CARD_RANKS:
            for suit in Suites:
                self._deck.append(Card(suit, card_rank))

    def reset_deck_and_shuffle(self):
        self._deck = []
        self.fill_deck_with_52_cards()
        self.shuffle()


class Player(abc.ABC):
    def __init__(self, name: str, id: str, amount_of_money: int = 0) -> None:
        self.cards = Deck()
        self._name = name
        self._amount_of_money = amount_of_money
        self._id = id
        logging.info("Player Created with name: %s. money: %d", name, amount_of_money)

    def __str__(self):
        return self._name

    @property
    def id(self):
        return self._id

    @abc.abstractmethod
    def _get_input_from_user(
            self, msg
    ):  # method to request strings (i.e names, how many players, etc)
        pass

    @abc.abstractmethod
    async def get_cmd(self, msg, list_of_valid_actions):
        pass

    async def _bet_is_valid(self, bet):
        logging.debug("Validating Bet")
        try:
            bet = int(bet)
        except ValueError:
            logging.info(f"Got a non valid bet from %s", self.get_player_name)
            await self.msg_to_user("Enter a positive number")
            return False

        if self.remaining_money == 0:
            raise PlayerHasNoMoneyError(
                "Player %s has no money but tried to bet", self.get_player_name
            )

        if bet > self.remaining_money:
            logging.info("%s tried to bet more than he has", self.get_player_name)
            await self.msg_to_user(
                "You don't have %s$! you can place a bet up to %d"
                % (bet, self.remaining_money)
            )
            return False

        elif bet < 0:
            logging.info("%s tried to bet a negative number", self.get_player_name)
            await self.msg_to_user("Enter a positive number")
            return False
        logging.debug("Bet is valid")
        return True

    async def _convert_command_to_Action(self, user_input):
        logging.debug("Converting user input %s to command", user_input)
        try:
            user_input = user_input.strip().lower()

            if user_input == "h" or user_input == "hit":
                logging.info("accepted decision from %s, HIT", self.get_player_name)
                return Actions.HIT

            if user_input == "s" or user_input == "stand":
                logging.info("accepted decision from %s, STAND", self.get_player_name)
                return Actions.STAND

            if user_input == "b" or user_input == "bet":
                logging.info("accepted decision from %s, BET", self.get_player_name)
                return Actions.BET

            if user_input == "skip":
                logging.info("accepted decision from %s, SKIP", self.get_player_name)
                return Actions.SKIP

            if user_input == "d":
                logging.info(
                    "accepted decision from %s, Double Down", self.get_player_name
                )
                return Actions.DOUBLE

            if user_input == "surrender":
                logging.info(
                    "accepted decision from %s, Surrender", self.get_player_name
                )
                return Actions.SURRENDER

            else:
                await self.msg_to_user("Not a valid command!")
                logging.info(
                    "%s typed the following invalid command: %s.",
                    self.get_player_name,
                    user_input,
                )
                return None

        except AttributeError:
            logging.exception(
                f"{self.get_player_name} typed {user_input}, not a string"
            )
            await self.msg_to_user("Enter a valid command according to the instructions")

    @property
    def get_player_name(self):
        return self._name

    @abc.abstractmethod
    async def msg_to_user(self, *args, **kwargs):
        pass

    def take_card(self, card):
        self.cards.take_card(card, True)

    def draw_card(self):
        return self.cards.draw_card()

    def get_money(self, amount_to_get):
        self._amount_of_money += amount_to_get
        logging.debug(
            f"{self.get_player_name} got {amount_to_get} and now has {self.remaining_money}"
        )

    def give_money(self, amount_to_give):
        self._amount_of_money -= amount_to_give
        logging.debug(
            f"{self.get_player_name} paid {amount_to_give} and has {self._amount_of_money} left",
            self.get_player_name,
            self._amount_of_money,
        )
        return amount_to_give

    @property
    def num_of_remaining_cards(self):
        return len(self.cards)

    @property
    def remaining_money(self):
        return self._amount_of_money


class BlackJackGameBase(abc.ABC):
    def __init__(self):
        self._players_bet = {}
        self.players = []
        self._players_in_round = []
        self._dealers_cards = Deck()
        self._game_deck = Deck()

    def add_player(self, player):
        logging.info("Player added")
        self.players.append(player)

    @abc.abstractmethod
    def remove_player_from_game(self, player_id):
        pass

    def get_players_in_round_decks_as_icons_in_a_dictionary(self):

        cards_as_icons_dict = {}

        for player in self._players_in_round:
            cards_as_icons_dict[player] = player.cards.return_deck_as_icons

        return cards_as_icons_dict

    @staticmethod
    def get_card_value(card):
        if type(card.rank) is int:
            return card.rank
        elif card.rank == "A":  # Ace
            return ACE_VALUE
        else:
            return 10  # A face card

    @abc.abstractmethod
    async def output_msg_to_game(self, msg):
        pass

    def _get_deck_game_value(self, deck):

        logging.debug("getting deck_game_value of a deck " + deck.return_deck_as_icons)

        total_aces = 0

        card_values = []
        for card in deck.cards:

            if card.rank == "A":
                total_aces += 1

            card_values.append(self.get_card_value(card))

        if sum(card_values) <= 21:
            logging.debug("deck_game_value is %d", sum(card_values))
            return sum(card_values)
        elif sum(card_values) > 21 and total_aces == 0:
            logging.debug("deck_game_value is %d", sum(card_values))
            return sum(card_values)
        else:  # Reduce values of aces

            # Remove aces
            card_values_without_aces = sum([a for a in card_values if a != ACE_VALUE])

            # Try each option with ace equals 1 or ace equals 11
            options = []

            for n in range(total_aces + 1):
                option = card_values_without_aces + 11 * n + 1 * (total_aces - n)
                # If we are bust, no need for this option
                if option > 21:
                    logging.debug("[-] Skipping option %s", option)
                    continue

                options.append(option)

            # if all options are over 21
            if len(options) == 0:
                return sum(card_values)

            best_option = min(options, key=lambda x: 21 - x)

            logging.debug("deck_game_value is %d", best_option)

            return best_option

    @staticmethod
    def _round_finished(players_in_round):
        for player in players_in_round:
            player.cards.empty_all_cards()

    def _player_has_blackjack(self, player):
        return self._get_deck_game_value(player.cards) == 21

    def _dealer_has_blackjack(self):
        return self._get_deck_game_value(self._dealers_cards) == 21

    async def _return_money_to_players_with_blackjack(self):
        for player in self._players_in_round:
            if self._player_has_blackjack(player):
                player.get_money(self._players_bet[player])
                await self.output_msg_to_game("%s is in a tie with the dealer." % player)
                self._players_bet[player] = 0
                self._players_in_round.remove(player)

    async def _players_without_blackjack_lose_their_bet(self):
        for player in self._players_in_round:
            if not self._player_has_blackjack(player):
                await self.output_msg_to_game("%s lost" % player)
                self._players_bet[player] = 0

    async def _handle_naturals_before_players_can_decide(self):
        await self.output_msg_to_game(
            "Dealer's hand: %s" % self._dealers_cards.return_deck_as_icons
        )
        if self._dealer_has_blackjack():
            await self.output_msg_to_game(
                "Dealer has Blackjack - %s" % self._dealers_cards.return_deck_as_icons
            )
            await self._return_money_to_players_with_blackjack()
            return

        # If dealer doesn't have blackjack
        for player in self._players_in_round.copy():
            if self._player_has_blackjack(player):
                logging.info("%s has BJ and is getting payed", player.get_player_name)
                await self._pay_player(player, ONE_AND_A_HALF_TIMES_THE_BET)
                self._players_bet[player] = 0
                self._players_in_round.remove(player)
                await self.output_msg_to_game(
                    "%s won 1.5 times his bet" % player.get_player_name
                )

    async def _wait_for_players(self):
        while len(self.players) == 0:
            await asyncio.sleep(1)
            continue
        logging.info("First player has joined the room")
        return

    async def _pay_player(self, player, multiplier):
        bet = self._players_bet[player]
        amount_to_pay = bet * multiplier
        logging.info("%s is getting payed %d$", player, amount_to_pay)
        await player.msg_to_user("%s, you won %d$" % (player.get_player_name, amount_to_pay))
        player.get_money(amount_to_pay)

    async def _take_bets_from_players(self):
        logging.info("Checking if room has players")
        await self._wait_for_players()
        logging.info("BlackJackGame is starting to take bets from players.")
        for player in self.players:

            logging.debug(
                "take_bets_from_players: trying to take a command from %s", player
            )

            allowed_actions = [Actions.BET, Actions.SKIP]
            command = await player.get_cmd(
                "To bet, type 'B'. To skip this round, type 'Skip'", allowed_actions
            )

            logging.debug(
                "take_bets_from_players: Got command %s from %s",
                command,
                player.get_player_name,
            )

            if command == Actions.SKIP:
                pass  # Player will not play the round

            elif command == Actions.BET:
                bet = await player.get_bet()
                logging.info("%s is betting %d$", player.get_player_name, bet)
                self._players_bet[player] = player.give_money(bet)

    async def _handle_winners_and_losers(self):

        dealers_hand_total = self._get_deck_game_value(self._dealers_cards)

        for player in self._players_in_round:

            # The state of the game checks that player is not bust before paying him, so no need to recheck it
            if self._get_deck_game_value(player.cards) > dealers_hand_total:
                logging.info(
                    "%s beat the dealer, he had %d in his pot",
                    player,
                    self._players_bet[player],
                )
                await player.msg_to_user(
                    "%s, You beat the dealer! you get twice your bet"
                    % player.get_player_name
                )
                await self.output_msg_to_game(
                    "%s, has beat the dealer!" % player.get_player_name
                )
                await self._pay_player(player, TWICE_AS_THE_BET)

            elif self._get_deck_game_value(player.cards) == dealers_hand_total:
                logging.info(
                    "%s and the dealer are in a tie, he had %d in his pot",
                    player,
                    self._players_bet[player],
                )
                await player.msg_to_user(
                    "%s, You are tied with the dealer! you get 1.5 times your bet"
                    % player.get_player_name
                )
                await self._pay_player(
                    player, SAME_AS_THE_BET
                )  # This is a tie, just give his money back

            else:  # Player lost, take his money. NOTE: The game doesn't do anything with the money, just takes it from users and deletes it.
                logging.info(
                    "%s lost, he had %d in his pot", player, self._players_bet[player]
                )
                await player.msg_to_user("%s, You lost" % player.get_player_name)
                await self.output_msg_to_game("%s lost" % player.get_player_name)
                self._players_bet[player] = 0

    def _return_lists_of_players_with_and_without_money(self):
        players_with_money = []
        players_without_money = []
        for player in self.players:
            player_id = player.id
            if player.remaining_money == 0:
                players_without_money.append(player_id)
            players_with_money.append(player_id)

        return players_with_money, players_without_money

    @abc.abstractmethod
    def _end_connection_with_player(self, player_id):
        pass

    async def play_round(self):
        # while there are players with money, open new rounds
        # kick players without money
        self._dealers_cards.empty_all_cards()

        self._players_bet = {}

        self._game_deck.reset_deck_and_shuffle()

        await self._take_bets_from_players()

        for player in self._players_bet:  # Only players who bet play the round
            self._players_in_round.append(player)

        if len(self._players_in_round) == 0:
            await self.output_msg_to_game("No Players in this round")
            return

        # =======================================================
        # Deal cards
        # =======================================================
        for _ in range(2):
            for player in self._players_in_round:
                player.take_card(self._game_deck.draw_card())
            self._dealers_cards.take_card(self._game_deck.draw_card())

        logging.info("play_round: cards were dealt to players")

        cards_as_icons_dictionary = (
            self.get_players_in_round_decks_as_icons_in_a_dictionary()
        )

        await self.output_msg_to_game(
            "Dealers Cards: %s, 🂠" % self._dealers_cards.cards[0].text_image
        )

        for player in self._players_in_round:
            await self.output_msg_to_game(
                "%s Cards: %s"
                % (player.get_player_name, cards_as_icons_dictionary[player])
            )

        # =======================================================
        # Check for blackjacks
        # =======================================================
        if any(self._player_has_blackjack(player) for player in self._players_in_round):
            await self._handle_naturals_before_players_can_decide()
            # Some players won, the round continues without them

        for player in self._players_in_round.copy():
            player_action = None
            allowed_commands = [
                Actions.HIT,
                Actions.DOUBLE,
                Actions.STAND,
                Actions.SURRENDER,
            ]
            logging.debug("play_round: trying to get command from %s", player)
            while (
                    not player_action == Actions.STAND
                    and not player_action == Actions.SURRENDER
                    and not player_action == Actions.DOUBLE
            ):  # player can hit until he's bust
                msg = (
                    f"{player.get_player_name} - To Hit type 'H'\nTo stand type 'S'\n"
                    "To Double down type 'D'\n"
                    "To Surrender and get half your money back, type 'Surrender'\n"
                )

                player_action = await player.get_cmd(msg, allowed_commands)

                if player_action == Actions.HIT:
                    try:
                        allowed_commands.remove(
                            Actions.DOUBLE
                        )  # players can't double down after hitting
                    except ValueError:
                        pass  # already removed this option when player previously hit
                    player.take_card(self._game_deck.draw_card())
                    logging.info("%s said HIT", player)
                    await self.output_msg_to_game(
                        "%s's deck: %s"
                        % (player.get_player_name, player.cards.return_deck_as_icons)
                    )

                if player_action == Actions.DOUBLE:
                    logging.info("%s said DOUBLE DOWN", player)
                    players_bet = self._players_bet[player]

                    if (
                            players_bet <= player.remaining_money
                    ):  # check if can double down
                        player.take_card(self._game_deck.draw_card())
                        await self.output_msg_to_game(
                            "%s's deck: %s"
                            % (
                                player.get_player_name,
                                player.cards.return_deck_as_icons,
                            )
                        )
                        self._players_bet[player] += player.give_money(players_bet)

                    else:
                        await player.msg_to_user(
                            "%s - You don't have enough to double down"
                            % player.get_player_name
                        )
                        logging.info(
                            "%s tried to double down, but doesnt have enough money",
                            player.get_player_name,
                        )

                if player_action == Actions.STAND:
                    logging.info("%s said STAND", player)

                if player_action == Actions.SURRENDER:
                    logging.info(
                        "%s said SURRENDER, giving him half the bet back", player
                    )
                    players_bet = self._players_bet[player]
                    player.get_money(players_bet * 0.5)
                    self._players_bet[player] = 0
                    self._players_in_round.remove(player)
                    await self.output_msg_to_game("%s said SURRENDER" % player)

                if self._get_deck_game_value(player.cards) > 21:
                    logging.info(
                        "%s is bust after hitting too much "
                        + player.cards.return_deck_as_icons,
                        player,
                    )
                    await self.output_msg_to_game(
                        "Player %s is bust: %s"
                        % (player, player.cards.return_deck_as_icons)
                    )
                    self._players_bet[player.get_player_name] = 0
                    self._players_in_round.remove(player)
                    break

            logging.debug("%s has stand or was removed if he was bust", player)

        if len(self._players_in_round) == 0:
            logging.info("No players left, returning.")
            await self.output_msg_to_game("No more players, game over")
            return

        # =======================================================
        # Dealer takes cards until he has 17 or higher, then check who won
        # =======================================================
        while self._get_deck_game_value(self._dealers_cards) < 17:
            self._dealers_cards.take_card(self._game_deck.draw_card())
            logging.info("Dealer took another card")
            await self.output_msg_to_game(
                "Dealer's deck: %s" % self._dealers_cards.return_deck_as_icons
            )

        if self._get_deck_game_value(self._dealers_cards) > 21:
            logging.debug("Dealer is bust, paying remaining players twice their bet")
            await self.output_msg_to_game(
                "Dealer is bust! \n%s - you get twice your bet"
                % str(self._players_in_round).strip("[]")
            )

            for player in self._players_in_round:
                await self._pay_player(player, TWICE_AS_THE_BET)
            return

        else:
            return await self._handle_winners_and_losers()

        # =======================================================
        # Round over
        # =======================================================

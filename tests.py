from unittest import mock
from blackjack_base import (
    Card,
    Deck,
    Suites,
    Actions,
    NoMoreCardsInDeckError,
    CardAlreadyInDeckError,
    TWICE_AS_THE_BET,
)
from offline import BlackJackGameOffLine, Player, OffLinePlayer


def test_cards():
    card = Card(suit=Suites.SPADES, rank="A")
    assert card.rank == "A"
    assert card.suit == Suites.SPADES


def test_card_to_icon():
    card = Card(suit=Suites.HEARTS, rank="8")
    assert card.text_image == "[8 of ♥ ]"


@mock.patch.object(BlackJackGameOffLine, "get_input_from_user")
def test_get_deck_game_value_reduces_value_of_ace_if_bust(get_input_from_user_mock):
    get_input_from_user_mock.side_effect = [
        "4",
        "Player A",
        0,
        "Player B",
        0,
        "Player C",
        0,
        "Player D",
        0,
    ]  # create a BJ game instance with 4 players

    game = BlackJackGameOffLine()
    game.players[0].take_card(Card(suit=Suites.HEARTS, rank=5))
    game.players[0].take_card(Card(suit=Suites.HEARTS, rank=2))

    game.players[1].take_card(Card(suit=Suites.HEARTS, rank="A"))
    game.players[1].take_card(Card(suit=Suites.HEARTS, rank="K"))

    game.players[2].take_card(Card(suit=Suites.HEARTS, rank=5))
    game.players[2].take_card(Card(suit=Suites.HEARTS, rank=2))
    game.players[2].take_card(Card(suit=Suites.HEARTS, rank="A"))
    game.players[2].take_card(Card(suit=Suites.HEARTS, rank="K"))

    game.players[3].take_card(Card(suit=Suites.HEARTS, rank="J"))
    game.players[3].take_card(Card(suit=Suites.HEARTS, rank=5))
    game.players[3].take_card(Card(suit=Suites.HEARTS, rank="Q"))

    assert game._get_deck_game_value(game.players[0].cards) == 7
    assert game._get_deck_game_value(game.players[1].cards) == 21
    assert game._get_deck_game_value(game.players[2].cards) == 18
    assert game._get_deck_game_value(game.players[3].cards) == 25


@mock.patch.object(Deck, "draw_card")
@mock.patch.object(OffLinePlayer, "_get_input_from_user")
@mock.patch.object(BlackJackGameOffLine, "get_input_from_user")
def test_handle_naturals_before_players_can_decide_on_first_round(
    get_input_from_user_mock, get_input_from_offline_player_mock, draw_card_mock
):
    get_input_from_user_mock.side_effect = [
        "1",
        "Test Player",
        500,
    ]  # mock 1 player that has 500$
    get_input_from_offline_player_mock.side_effect = ["b", 500]

    draw_card_mock.side_effect = [
        Card(suit=Suites.CLUBS, rank="A"),  # deal player a BlackJack (21)
        Card(suit=Suites.SPADES, rank="Q"),
        Card(suit=Suites.DIAMONDS, rank="K"),
        Card(suit=Suites.HEARTS, rank=5),
    ]
    game = BlackJackGameOffLine()
    game.play_round()
    assert game.players[0].remaining_money == 750


@mock.patch.object(OffLinePlayer, "_get_input_from_user")
@mock.patch.object(Deck, "draw_card")
@mock.patch.object(BlackJackGameOffLine, "get_input_from_user")
def test_players_have_to_bet_or_skip(
    get_input_from_user_blackjack_mock, draw_card_mock, _get_input_from_user_mock
):
    get_input_from_user_blackjack_mock.side_effect = [
        "1",
        "Test Player A",
        500,
    ]  # mock a player that has 500$

    # try to hit when you need to bet, then make proceed as normal
    _get_input_from_user_mock.side_effect = ["h", "b", 500]

    draw_card_mock.side_effect = [
        Card(suit=Suites.CLUBS, rank="A"),  # deal player a BlackJack (21)
        Card(suit=Suites.SPADES, rank="Q"),
        Card(suit=Suites.DIAMONDS, rank="K"),
        Card(suit=Suites.HEARTS, rank=5),
    ]
    game = BlackJackGameOffLine()
    game.play_round()
    assert game.players[0].remaining_money == 750


@mock.patch.object(OffLinePlayer, "_get_input_from_user")
@mock.patch.object(Deck, "draw_card")
@mock.patch.object(BlackJackGameOffLine, "get_input_from_user")
def test_game_full_round(
    get_input_from_blackjack_user, draw_card_mock, _get_input_from_user_mock
):
    # 3 players with 100$ each
    get_input_from_blackjack_user.side_effect = [
        "3",
        "Bust Player A",
        100,
        "Tie Player B",
        100,
        "Winning Player C",
        100,
    ]

    # deal bust player, then, tie player, then, winning player, then dealer...
    draw_card_mock.side_effect = [
        Card(suit=Suites.SPADES, rank=2),
        Card(suit=Suites.HEARTS, rank="J"),
        Card(suit=Suites.HEARTS, rank="K"),
        Card(suit=Suites.CLUBS, rank="J"),
        Card(suit=Suites.SPADES, rank=10),
        Card(suit=Suites.SPADES, rank=6),
        Card(suit=Suites.HEARTS, rank=3),
        Card(suit=Suites.DIAMONDS, rank=6),
        Card(suit=Suites.CLUBS, rank="K"),
        Card(suit=Suites.HEARTS, rank=2),
        Card(suit=Suites.HEARTS, rank=7),
        Card(suit=Suites.CLUBS, rank=2),
    ]

    _get_input_from_user_mock.side_effect = [
        "b",
        100,
        "b",
        100,
        "b",
        100,
        "h",
        "h",
        "s",
        "h",
        "s",
    ]
    # Hit one card for each player, then stand
    game = BlackJackGameOffLine()
    game.play_round()

    assert game.players[0].remaining_money == 0
    assert game.players[1].remaining_money == 100
    assert game.players[2].remaining_money == 200


def test_hash_of_identical_cards_gives_the_same_result():
    card_a = Card(suit=Suites.SPADES, rank="A")
    card_b = Card(suit=Suites.SPADES, rank="A")
    assert hash(card_a) == hash(card_b)


def test_cards_equal():
    card_a = Card(suit=Suites.SPADES, rank="A")
    card_b = Card(suit=Suites.SPADES, rank="A")
    assert card_a == card_b


def test_cards_not_equal():
    card_a = Card(suit=Suites.SPADES, rank="A")
    card_b = Card(suit=Suites.SPADES, rank="K")
    assert card_a != card_b


def test_deck_shuffle_does_not_give_same_card():
    deck = Deck()
    deck.reset_deck_and_shuffle()
    card_a = deck.draw_card()

    deck.reset_deck_and_shuffle()
    card_b = deck.draw_card()

    assert card_a != card_b


def test_deck_equals():
    deck_a = Deck()
    deck_b = Deck()
    assert deck_a == deck_b


def test_deck_shuffle():  # This will fail with a probability of 1/52
    deck = Deck()
    deck.reset_deck_and_shuffle()
    card_a = deck.draw_card()

    deck.reset_deck_and_shuffle()
    card_b = deck.draw_card()

    assert card_a != card_b


def test_deck_draw_card_all_cards_are_different():
    deck = Deck()
    deck.fill_deck_with_52_cards()
    drawn_cards = set()

    for _ in range(52):
        card = deck.draw_card()
        assert card not in drawn_cards
        drawn_cards.add(card)

    assert len(drawn_cards) == 52


def test_deck_draw_more_than_52_raises_NoMoreCardsInDeckError():
    deck = Deck()
    deck.fill_deck_with_52_cards()

    # Draw all cards from deck
    for _ in range(52):
        deck.draw_card()

    try:  # draw one too many
        deck.draw_card()
    except NoMoreCardsInDeckError:
        return  # Test complete

    raise Exception("FUCK YOU! THIS SHOULD'NT HAVE HAPPENED")


def test_card_player_take_card_and_draw():
    player = OffLinePlayer("player 1", id="foo")
    player.take_card(Card(suit=Suites.SPADES, rank="A"))
    assert player.draw_card() == Card(suit=Suites.SPADES, rank="A")


def test_cannot_take_same_card_twice():
    deck = Deck()
    assert len(deck) == 0

    deck.take_card(Card(Suites.HEARTS, 9))
    assert len(deck) == 1

    try:
        deck.take_card(Card(Suites.HEARTS, 9))
        raise Exception("Should not reach here")
    except CardAlreadyInDeckError:
        pass

    assert len(deck) == 1


def test_take_card_puts_on_top_of_the_deck():
    deck = Deck()
    assert len(deck) == 0

    card_a = Card(Suites.HEARTS, 9)
    card_b = Card(Suites.SPADES, 7)

    deck.take_card(card_a)
    deck.take_card(card_b)

    assert deck.draw_card() == card_b
    assert len(deck) == 1

    assert deck.draw_card() == card_a
    assert len(deck) == 0


def test_take_card_puts_on_bottom_of_the_deck_when_lifo_false():
    deck = Deck()
    assert len(deck) == 0

    card_a = Card(Suites.HEARTS, 9)
    card_b = Card(Suites.SPADES, 7)

    deck.take_card(card_a, top_of_deck=False)
    deck.take_card(card_b, top_of_deck=False)

    assert deck.draw_card() == card_a
    assert len(deck) == 1

    assert deck.draw_card() == card_b
    assert len(deck) == 0


def test_player_has_no_money_by_default():
    player = OffLinePlayer("test player", id="foo")
    assert player.remaining_money == 0


def test_player_gets_and_gives_money():
    player = OffLinePlayer("test player", id="foo")
    player.get_money(200)
    assert player.remaining_money == 200
    player.give_money(90)
    assert player.remaining_money == 110


@mock.patch.object(BlackJackGameOffLine, "get_input_from_user")
def test_pay_player(user_input_mock):
    user_input_mock.side_effect = ["1", "Test Player", 0]
    game = BlackJackGameOffLine()
    test_player = game.players[0]
    game._players_bet[test_player] = 100

    game._pay_player(test_player, TWICE_AS_THE_BET)
    assert test_player.remaining_money == 200


@mock.patch.object(BlackJackGameOffLine, "get_input_from_user")
def test_handle_winners_and_losers(user_input_mock):
    user_input_mock.side_effect = [
        "3",
        "Test player A",
        "0",
        "Test player B",
        "0",
        "Test Player C",
        "0",
    ]
    game = BlackJackGameOffLine()
    player_a = game.players[0]
    player_b = game.players[1]
    player_c = game.players[2]

    player_a.take_card(Card(suit=Suites.SPADES, rank=8))
    player_a.take_card(Card(suit=Suites.DIAMONDS, rank=10))

    player_b.take_card(Card(suit=Suites.HEARTS, rank=3))
    player_b.take_card(Card(suit=Suites.DIAMONDS, rank=7))

    player_c.take_card(Card(suit=Suites.SPADES, rank=2))
    player_c.take_card(Card(suit=Suites.DIAMONDS, rank=4))

    game._dealers_cards.take_card(Card(suit=Suites.SPADES, rank=7))
    game._dealers_cards.take_card(Card(suit=Suites.SPADES, rank=3))
    game._players_bet[player_a] = 100
    game._players_bet[player_b] = 400
    game._players_bet[player_c] = 500

    for player in game._players_bet:
        game._players_in_round.append(player)

    game._handle_winners_and_losers()
    assert player_a.remaining_money == 200
    assert player_b.remaining_money == 400
    assert player_c.remaining_money == 0


@mock.patch.object(BlackJackGameOffLine, "get_input_from_user")
def test_player_deck_print(get_input_from_user_mock):
    get_input_from_user_mock.side_effect = [1, "Test Player", 500]

    game = BlackJackGameOffLine()

    player = game.players[0]

    game._players_in_round.append(player)

    game.players[0].take_card(Card(suit=Suites.DIAMONDS, rank=7))
    game.players[0].take_card(Card(suit=Suites.DIAMONDS, rank=8))
    game.players[0].take_card(Card(suit=Suites.DIAMONDS, rank=9))

    dict_of_icons = game.get_players_in_round_decks_as_icons_in_a_dictionary()

    assert dict_of_icons[player] == "[7 of ♦ ], [8 of ♦ ], [9 of ♦ ]"


@mock.patch.object(OffLinePlayer, "get_bet")
@mock.patch.object(OffLinePlayer, "_get_input_from_user")
@mock.patch.object(Deck, "draw_card")
@mock.patch.object(BlackJackGameOffLine, "get_input_from_user")
def test_one_player_wins_and_the_rest_continue_to_play(
    get_input_from_user_blackjack_mock,
    draw_card_mock,
    get_input_from_offline_user_mock,
    get_bet_mock,
):
    get_input_from_user_blackjack_mock.side_effect = [
        "2",
        "P1",
        100,
        "P2",
        100,
    ]  # generate two players with 100$ each

    get_input_from_offline_user_mock.side_effect = ["b", "b", "s"]
    #    player 1 wins automatically, P2 stands and should beat the dealer
    get_bet_mock.side_effect = [100, 100]  # both players will bet 100

    draw_card_mock.side_effect = [
        Card(suit=Suites.CLUBS, rank="A"),  # deal player a BlackJack (21)
        Card(suit=Suites.SPADES, rank="Q"),  # other player gets Q and K
        Card(suit=Suites.DIAMONDS, rank=10),  # Dealer gets total of 17
        Card(suit=Suites.DIAMONDS, rank="K"),
        Card(suit=Suites.CLUBS, rank="K"),
        Card(suit=Suites.HEARTS, rank=7),
    ]
    game = BlackJackGameOffLine()
    game.play_round()
    assert game.players[0].remaining_money == 150
    assert game.players[1].remaining_money == 200


@mock.patch.object(OffLinePlayer, "get_bet")
@mock.patch.object(OffLinePlayer, "get_cmd")
@mock.patch.object(BlackJackGameOffLine, "get_input_from_user")
def test_surrender_gives_back_half_the_money(
    get_input_from_user_mock, get_cmd_mock, get_bet_mock
):
    get_input_from_user_mock.side_effect = ["1", "P1", 100]
    get_cmd_mock.side_effect = [Actions.BET, Actions.SURRENDER]
    get_bet_mock.side_effect = [100]
    game = BlackJackGameOffLine()
    game.play_round()
    assert game.players[0].remaining_money == 50


@mock.patch.object(Deck, "draw_card")
@mock.patch.object(OffLinePlayer, "_get_input_from_user")
@mock.patch.object(BlackJackGameOffLine, "get_input_from_user")
def test_bust_player_is_kicked_from_round(
    get_input_from_user_mock, _get_input_from_offline_player_mock, draw_card_mock
):
    get_input_from_user_mock.side_effect = ["1", "P1", 100]
    _get_input_from_offline_player_mock.side_effect = ["b", 100, "h", "h"]

    draw_card_mock.side_effect = [
        Card(suit=Suites.DIAMONDS, rank=2),
        Card(suit=Suites.SPADES, rank=3),
        Card(suit=Suites.DIAMONDS, rank="A"),
        Card(suit=Suites.DIAMONDS, rank="K"),
        Card(suit=Suites.CLUBS, rank="J"),
        Card(suit=Suites.CLUBS, rank="K"),
    ]

    game = BlackJackGameOffLine()
    game.play_round()
    assert game.players[0].remaining_money == 0


@mock.patch.object(Deck, "draw_card")
@mock.patch.object(OffLinePlayer, "_get_input_from_user")
@mock.patch.object(BlackJackGameOffLine, "get_input_from_user")
def test_player_cant_double_down_after_hitting(
    get_input_from_user_mock, _get_input_from_offline_player_mock, draw_card_mock
):
    #   ****** test fails when player has 4 cards ******

    get_input_from_user_mock.side_effect = ["1", "P1", 100]
    _get_input_from_offline_player_mock.side_effect = ["b", 100, "h", "d", "s"]

    draw_card_mock.side_effect = [
        Card(suit=Suites.DIAMONDS, rank=2),
        Card(suit=Suites.SPADES, rank="Q"),
        Card(suit=Suites.DIAMONDS, rank=4),
        Card(suit=Suites.DIAMONDS, rank="K"),
        Card(suit=Suites.CLUBS, rank=8),
    ]

    game = BlackJackGameOffLine()
    game.play_round()

    assert game.players[0].num_of_remaining_cards == 3

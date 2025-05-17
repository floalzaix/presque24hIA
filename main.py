from server.server import Server
from server.game_api import GameApi
from bot.bot import Bot

if __name__ == "__main__":
    with Server("Alaix") as server:
        api = GameApi(server)
        bot = Bot(api)

        while True:
            bot.play_turns()

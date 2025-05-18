from server.server import Server
from server.game_api import GameApi
from iut.bot.bot import Bot

server = Server("Test")
api = GameApi(server)
bot = Bot(api)

bot.get_current_hp()
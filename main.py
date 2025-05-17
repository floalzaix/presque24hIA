from server.game_api import GameApi
from server.server import Server


if __name__ == "__main__":
    with Server("Alzaix") as server : 
        api = GameApi(server)
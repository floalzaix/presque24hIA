from server.game_api import GameApi
from server.server import Server
from ai.actor_critic import ActorCritic
from utils.action import ACTIONS


if __name__ == "__main__":
    model = ActorCritic(state_size=35, action_size=len(ACTIONS))
    with Server("Alzaix") as server : 
        api = GameApi(server, model)
        
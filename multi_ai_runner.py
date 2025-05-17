from server.server import Server
from server.game_api import GameApi
from ai.actor_critic import ActorCritic
from ai.train import run_episode
from utils.action import ACTIONS
from ai.actor_critic import state_from_game
import tensorflow as tf
import time

def ai_worker(team_name: str, episode_num: int):
    print(f"🤖 Lancement de l'IA {team_name} pour l'épisode {episode_num}")
    
    try:
        model = ActorCritic(state_size=35, action_size=len(ACTIONS))
        optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)

        with Server(team_name) as server:
            api = GameApi(server, model)

            print(f"🎮 {team_name} en attente de début de tour...")

            # Boucle principale pour attendre un tour
            while True:
                message = server.receive()
                if message[0] == "DEBUT_TOUR":
                    api.numero_tour = message[1]
                    api.numero_phase = message[2]

                    run_episode(api, model, optimizer, episode_num)
                    break
    except Exception as e:
        print(f"⚠️ Erreur dans l'IA {team_name} : {e}")

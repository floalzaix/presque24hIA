from server.server import Server
from server.game_api import GameApi
from ai.actor_critic import ActorCritic
from ai.train import run_episode
from utils.action import ACTIONS
from ai.actor_critic import state_from_game
import tensorflow as tf
import time
from multiprocessing import Queue
import os
from ai.model_utils import save_model

def ai_worker(team_name: str, episode_num: int, result_queue=None, best_model_path=None):
    print(f"🤖 Lancement de l'IA {team_name} pour l'épisode {episode_num}")
    
    try:
        model = ActorCritic(state_size=35, action_size=len(ACTIONS))
        optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)

        # Charger le meilleur modèle précédent si disponible
        if best_model_path and os.path.exists(best_model_path):
            print(f"📥 {team_name} charge le modèle {best_model_path}")
            model.load_weights(best_model_path)

        with Server(team_name) as server:
            api = GameApi(server, model)

            print(f"🎮 {team_name} en attente de début de tour...")

            # Boucle principale pour attendre un tour
            while True:
                message = server.receive()
                if message[0] == "DEBUT_TOUR":
                    api.numero_tour = message[1]
                    api.numero_phase = message[2]

                    # run_episode doit retourner le score cumulé
                    total_reward = run_episode(api, model, optimizer, episode_num, team_name)
                    # Sauvegarde du modèle pour ce bot
                    model_path = f"models/model_{team_name}_episode_{episode_num}.h5"
                    save_model(model, model_path)
                    if result_queue:
                        result_queue.put((team_name, total_reward, model_path))
                    break
    except Exception as e:
        print(f"⚠️ Erreur dans l'IA {team_name} : {e}")
        if result_queue:
            result_queue.put((team_name, float('-inf'), None))

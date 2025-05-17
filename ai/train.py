from utils.action import ACTIONS
from ai.model_utils import save_model
from ai.actor_critic import state_from_game
import tensorflow as tf 
import numpy as np

def run_episode(api, model, optimizer, gamma=0.99):
    state_buffer = []
    action_buffer = []
    reward_buffer = []

    done = False

    while not done:
        # 1. Obtenir l'état du jeu
        state = state_from_game(api)
        state_buffer.append(state)

        # 2. Prédire la distribution des actions
        EPSILON = 0.1  # Exploration : 10%

        logits, _ = model(tf.convert_to_tensor([state], dtype=tf.float32))
        logits = tf.squeeze(logits)

        # Softmax sécurisé
        action_probs = tf.nn.softmax(logits).numpy()

        # Correction potentielle de somme ≠ 1
        action_probs = np.nan_to_num(action_probs)  # remplace NaN/inf par 0
        action_probs /= np.sum(action_probs) + 1e-8  # sécurité pour éviter la division par 0

        if np.random.rand() < EPSILON:
            action = np.random.choice(len(ACTIONS))  # Choix aléatoire
        else:
            try:
                action = np.random.choice(len(ACTIONS), p=action_probs)
            except ValueError as e:
                print("⚠️ Problème avec action_probs :", action_probs)
                action = np.random.choice(len(ACTIONS))  # fallback

        action_buffer.append(action)


        # 3. Jouer l'action
        command = ACTIONS[action]
        reward = play_action(command, api)
        reward_buffer.append(reward)

        if is_episode_done(api):
            done = True
        api.jouer_tour()
        
    # 5. Calculer les retours
    returns = compute_returns(reward_buffer, gamma)

    # 6. Optimisation
    train_step(model, optimizer, state_buffer, action_buffer, returns)
    
    save_model(model, f"models/model_episode_{episode_num}.h5")


def play_action(command, api):
    parts = command.split("|")
    if parts[0] == "PIOCHER":
        api.piocher(int(parts[1]), int(parts[2]))
    elif parts[0] == "UTILISER":
        api.utiliser(parts[1])
    elif parts[0] == "ATTAQUER":
        api.attaquer(int(parts[1]))
    
    # TODO: définir une vraie fonction de récompense
    return compute_reward(api)

def compute_reward(api):
    me = api.moi()
    enemies = api.monstres()

    try:
        health = int(me[0])
        energy = int(me[1])
        shield = int(me[2])
        score = int(me[3])
    except Exception as e:
        print(f"❌ Erreur lors de la lecture des stats du joueur : {e}")
        return -100  # pénalité en cas d'erreur

    alive_bonus = 10 if health > 0 else -100
    health_reward = (health - 500) / 10
    shield_reward = shield * 0.2
    energy_reward = energy * 0.1
    score_reward = score * 1.0

    try:
        enemy_health = sum([int(e[0]) for e in enemies])
        enemy_penalty = -enemy_health * 0.05
        enemy_dead_bonus = 20 if all(int(e[0]) <= 0 for e in enemies) else 0
    except Exception as e:
        print(f"❌ Erreur lors de la lecture des ennemis : {e}")
        enemy_penalty = 0
        enemy_dead_bonus = 0

    total_reward = (
        alive_bonus
        + health_reward
        + shield_reward
        + energy_reward
        + score_reward
        + enemy_penalty
        + enemy_dead_bonus
    )

    return total_reward




def is_episode_done(api):
    me = api.moi()
    try:
        vie = int(me[0])
    except ValueError:
        print(f"⚠️ Valeur de vie invalide : {me[0]}")
        return True  # On arrête l'épisode par sécurité
    return vie <= 0


def train_step(model, optimizer, states, actions, returns):
    with tf.GradientTape() as tape:
        total_loss = 0
        for state, action, G in zip(states, actions, returns):
            logits, value = model(tf.convert_to_tensor([state]))
            value = tf.squeeze(value)
            advantage = G - value

            critic_loss = advantage ** 2

            action_probs = tf.nn.softmax(logits)
            log_prob = tf.math.log(action_probs[0, action] + 1e-8)
            actor_loss = -log_prob * advantage

            total_loss += actor_loss + critic_loss

    grads = tape.gradient(total_loss, model.trainable_variables)
    optimizer.apply_gradients(zip(grads, model.trainable_variables))

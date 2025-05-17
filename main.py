import numpy as np
import tensorflow as tf
from ai.actor_Critic import ActorCritic, compute_returns
from server.server import Server

# Exemple de mapping simplifié des actions
ACTIONS = [
    "PIOCHER|0",  # Défense safe
    "PIOCHER|1",  # Attaque safe
    "PIOCHER|2",  # Savoir safe
    "UTILISER|DEFENSE",
    "UTILISER|ATTAQUE",
    "UTILISER|SAVOIR",
    "ATTAQUER|0",  # Monstre 0
    "ATTAQUER|1",
    "ATTAQUER|2"
]

def state_from_game(data_dict):
    """Encode un état simple"""
    me = data_dict["MOI"]
    return np.array([me["vie"], me["defense"], me["attaque"], me["savoir"]], dtype=np.float32)

def run_episode(model, optimizer):
    with Server("Alzaix") as client: 
        state_buffer, action_buffer, reward_buffer = [], [], []

        while True:
            client.send("MOI")
            msg = client.receive()
            if "FIN" in msg:
                break

            # Récupérer l'état
            data = {
                "MOI": parse_moi(msg)
            }
            state = state_from_game(data)
            state = tf.convert_to_tensor([state], dtype=tf.float32)

            # Prédire action et valeur
            probs, value = model(state)
            action = np.random.choice(len(ACTIONS), p=np.squeeze(probs))

            # Envoyer action
            client.send(ACTIONS[action])
            response = client.receive()
            reward = parse_reward_from_response(response)

            # Mémoriser
            state_buffer.append(state)
            action_buffer.append(action)
            reward_buffer.append(reward)

        # Calcul des cibles
        returns = compute_returns(reward_buffer)
        returns = tf.convert_to_tensor(returns[:, None], dtype=tf.float32)

        # Backprop
        with tf.GradientTape() as tape:
            total_loss = 0
            for i in range(len(state_buffer)):
                probs, value = model(state_buffer[i])
                critic_loss = tf.square(returns[i] - value)
                action_prob = probs[0, action_buffer[i]]
                actor_loss = -tf.math.log(action_prob + 1e-8) * (returns[i] - value)
                total_loss += actor_loss + critic_loss

        grads = tape.gradient(total_loss, model.trainable_variables)
        optimizer.apply_gradients(zip(grads, model.trainable_variables))

# Fonctions de parsing à implémenter :
def parse_moi(msg):
    # Exemple brut à parser : "25|10|20|50"
    parts = list(map(int, msg.strip().split("|")))
    return {"vie": parts[0], "defense": parts[1], "attaque": parts[2], "savoir": parts[3]}

def parse_reward_from_response(response):
    # Tu peux définir une stratégie, par exemple +10 si savoir augmente ou 0 par défaut
    return 1.0 if "OK" in response else -1.0

if __name__ == "__main__":
    model = ActorCritic(state_size=4, action_size=len(ACTIONS))
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)
    for episode in range(100):
        run_episode(model, optimizer)
        print(f"Episode {episode + 1} terminé.")


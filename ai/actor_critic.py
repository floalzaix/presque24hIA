import tensorflow as tf
from tensorflow.keras import layers
import numpy as np

CARD_TYPES = {
    "DEFENSE": 0,
    "ATTAQUE": 1,
    "SAVOIR": 2,
    "VIE": 3,
    "MONSTRE": 4,
    "OBJET": 5,
    "INCONNU": 6  # Par sécurité
}

class ActorCritic(tf.keras.Model):
    def __init__(self, state_size, action_size):
        super(ActorCritic, self).__init__()
        self.common = layers.Dense(64, activation='relu')
        self.actor = layers.Dense(action_size, activation='softmax')
        self.critic = layers.Dense(1)

    def call(self, inputs):
        x = self.common(inputs)
        return self.actor(x), self.critic(x)

def compute_returns(rewards, gamma=0.99):
    G = 0
    returns = []
    for r in reversed(rewards):
        G = r + gamma * G
        returns.insert(0, G)
    return np.array(returns)

def state_from_game(api):
    me = api.moi()
    monstres = api.monstres()
    pioches = api.pioches()
    degats = api.degats()

    pioches_encoded = []
    for type_str, value in pioches:
        type_num = CARD_TYPES.get(type_str.upper(), CARD_TYPES["INCONNU"])
        pioches_encoded.extend([type_num, value])

    if isinstance(degats, str):
        degats = [int(degats)]
    elif isinstance(degats, int):
        degats = [degats]

    state = me \
        + [val for monstre in monstres for val in monstre] \
        + pioches_encoded \
        + degats

    return np.array(state, dtype=np.float32)

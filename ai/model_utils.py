from ai.actor_critic import ActorCritic
from tensorflow.keras.models import load_model
import os

def save_model(model, path="models/model.h5"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    model.save_weights(path)
    print(f"💾 Modèle sauvegardé à : {path}")
    

def load_actor_critic_model(state_size, action_size, path="models/actor_critic_model.keras"):
    if os.path.exists(path):
        print("Model loaded from", path)
        return load_model(path, custom_objects={"ActorCritic": ActorCritic}, compile=False)
    else:
        print("No saved model found. Creating a new one.")
        return ActorCritic(state_size, action_size)

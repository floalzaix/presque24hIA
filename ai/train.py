from utils.actions import ACTIONS

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
        logits, _ = model(tf.convert_to_tensor([state]))
        action_probs = tf.squeeze(logits)
        action = np.random.choice(len(ACTIONS), p=action_probs.numpy())

        action_buffer.append(action)

        # 3. Jouer l'action
        command = ACTIONS[action]
        reward = play_action(command, api)
        reward_buffer.append(reward)

        if is_episode_done(api):
            done = True

    # 5. Calculer les retours
    returns = compute_returns(reward_buffer, gamma)

    # 6. Optimisation
    train_step(model, optimizer, state_buffer, action_buffer, returns)

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
    return me[3] 

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

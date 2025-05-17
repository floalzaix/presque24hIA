"""
    Lib which allows the communication between the ai and the game on the server
    
    Simply allows to send and receive reponce adapted to the game from the server
    
    Attibuts of the GameApi : (To egt with the AI)
    
    self.server
    
    self.team_name 
    self.team_num
    
    self.numero_tour
    self.numero_phase
"""

from server.server import Server
from ai.actor_critic import ActorCritic, compute_returns, state_from_game
from ai.train import run_episode
import tensorflow as tf
from tensorflow.keras.models import load_model
import numpy as np
from ai.model_utils import load_actor_critic_model
from utils.action import ACTIONS
import os


class GameApi:
    def __init__(self, server : Server, model):
        self.server = server
        if os.path.isdir("models/actor_critic_model.keras"):
            self.model = load_actor_critic_model(state_size, action_size)
        else :
            self.model = model
        self.team_name = self.server.team_name
        self.team_num = self.server.team_num
                
    #
    #   Handle mannager
    #
    
    def end_tour(self):
        data = self.server.receive()
        
        if data[0] == "DEBUT_TOUR":
            self.numero_tour = data[1]
            self.numero_phase = data[2]
            
            # REND LA MAIN A L'IA <= Par exemple : self.piocher(0) ou self.piocher(4,1)
            state = state_from_game(self)
            logits, _ = self.model(tf.convert_to_tensor([state]))
            probs = tf.squeeze(logits)
            action_index = np.random.choice(len(probs), p=probs.numpy())
            command = ACTIONS[action_index]
            
            self.play_command(command)
    #
    #   Action commands
    #
        
    def piocher(self, expedition_index : int, player_index : int = -1):
        if player_index == -1:
            player_index = self.team_num
        self.server.send(f"PIOCHER|{expedition_index}|{player_index}")
        self.server.receive()
        self.end_tour()
    
    def utiliser(self, type_carte : str):
        self.server.send(f"UTILISER|{type_carte}")
        try:
            self.server.receive()
        except ValueError:
            self.piocher(0)
            return

        # Après avoir utilisé, décider quoi faire
        me = self.moi()
        attaque = int(me[2])  # Supposons que l'indice 2 = attaque, à adapter selon ton jeu
        monstres = self.monstres()
        cible = next((i for i, m in enumerate(monstres) if int(m[0]) > 0), None)

        if attaque > 0 and cible is not None:
            self.attaquer(cible)
        else:
            self.piocher(0)
    
    def attaquer(self, monster_index : int):
        self.server.send(f"ATTAQUER|{monster_index}")
        try:
            self.server.receive()
        except ValueError :
            self.piocher(0)
        self.end_tour()
    
    def jouer_tour(self):
        # On suppose que la phase nuit s'appelle "NUIT" ou "BLOOD_MOON"
        if self.numero_phase in ["NUIT", "BLOOD_MOON"]:
            # Utilise toutes les cartes disponibles (adapte selon ton jeu)
            # On suppose que moi() retourne [vie, def, att, savoir]
            me = self.moi()
            if int(me[1]) > 0:  # Si score défense > 0
                print("🛡️ Utilisation de la défense pendant la nuit")
                self.utiliser("DEFENSE")
                return
            elif int(me[2]) > 0:  # Si score attaque > 0
                print("⚔️ Utilisation de l'attaque pendant la nuit")
                monstres = self.monstres()
                cible = next((i for i, m in enumerate(monstres) if int(m[0]) > 0), None)
                if cible is not None:
                    self.attaquer(cible)
                    return
            # Ajoute d'autres types de cartes ici si besoin

            # Si aucune carte utilisable, pioche
            print("🃏 Pioche pendant la nuit")
            self.piocher(0)
        else:
            # Hors nuit, pioche par défaut
            print("🃏 Pioche hors nuit")
            self.piocher(0)
    
    #
    #   Info commands
    #
    
    def joueurs(self) -> list[list[int]]:
        """ Returns the info on the players
            out : [[Vie|ScoreDefense|ScoreAttaque|ScoreSavoir], [...], [], []]
        """
        self.server.send("JOUEURS")
        data = self.server.receive()
        
        res = []
        for i in range(0, 4):
            res.append([])
            for j in range(0, 4):
                res[i].append(data[4 * i + j])
        
        return res
    
    def moi(self) -> list[int]:
        self.server.send("MOI")
        data = self.server.receive()
        
        return [data[0], data[1], data[2], data[3]]
    
    def monstres(self) -> list[list[int]]:
        """ Returns the info on the monsters
            out : [[Vie|GainSavoir], [...], []]
        """
        self.server.send("MONSTRES")
        data = self.server.receive()
        
        res = []
        for i in range(0, 3):
            res.append([])
            for j in range(0, 2):
                res[i].append(data[2 * i + j])
        
        return res
    
    def pioches(self) -> list[list[int]]:
        """ Returns the info on the pioche
            out : [[Type|Valeur], [...], [], [], [], []]
        """
        self.server.send("PIOCHES")
        data = self.server.receive()
        
        res = []
        for i in range(0, 6):
            res.append([])
            for j in range(0, 2):
                res[i].append(data[2 * i + j])
        
        return res
    
    def degats(self):
        self.server.send("DEGATS")
        data = self.server.receive()
        
        return data[0]
    
    def play_command(self, command: str):
        parts_commande = command.split("|")
        if parts_commande[0] == "PIOCHER":
            self.piocher(int(parts_commande[1]), int(parts_commande[2]))
        elif parts_commande[0] == "UTILISER":
            self.utiliser(parts_commande[1])
        elif parts_commande[0] == "ATTAQUER":
            self.attaquer(int(parts_commande[1]))




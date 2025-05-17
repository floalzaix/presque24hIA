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

from server import Server

class GameApi:
    def __init__(self, server : Server):
        self.server = server
        self.team_name = self.server.team_name
        self.team_num = self.server.team_num
        
        self.end_tour()
        
    #
    #   Handle mannager
    #
    
    def end_tour(self):
        data = self.server.receive()
        
        if data[0] == "DEBUT_TOUR":
            self.numero_tour = data[1]
            self.numero_phase = data[2]
            
            # REND LA MAIN A L'IA <= Par exemple : self.piocher(0, 0)
    
    #
    #   Action commands
    #
        
    def piocher(self, expedition_index : int, player_index : int):
        self.server.send(f"PIOCHER|{expedition_index}|{player_index}")
        self.server.receive()
        self.end_tour()
    
    def utiliser(self, type_carte : str):
        self.server.send(f"UTILISER|{type_carte}")
        self.server.receive()
    
    def attaquer(self, monster_index : int):
        self.server.send(f"ATTAQUER|{monster_index}")
        self.server.receive()
        self.end_tour()
    
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
        

with Server("Test") as server:
    api = GameApi(server)
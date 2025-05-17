"""
    Lib which allows the communication between the ai and the game on the server
    
    Usage :
    
"""

from server import Server

class GameApi:
    def __init__(self, server : Server):
        self.server = server
        
    def piocher(expedition_index : int, player)

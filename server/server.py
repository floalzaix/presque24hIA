"""
    Local game lib accesser
    
    Usage : 
    
    with Server("teamName") as serveur:
        server.send("bla")
        server.receive() # Blocking
"""

import socket

HOST = "127.0.0.1"
PORT = 1234
    
class Server:
    def __init__(self, name):
        self.name = name
        
    def __enter__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, PORT))
        print("Connexion serveur ouverte !")
        
        # Connection to the server and sending the name
        name_request = self.sock.recv(1024)
        
        if name_request.decode().strip() == "NOM_EQUIPE":
            self.sock.sendall(self.name.encode())
        else:
            raise ValueError("Mauvaise réponce serveur à la connexion")
        
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.sock:
            self.sock.close()
            print("Connexion serveur fermée !")
            
    def send(self, msg: str):
        """ Sends a str to the server """
        print(f"Envoie du message {msg} au serveur !")
        self.sock.sendall(msg.encode())
        
    def receive(self) -> str:
        """ Returns the responce of the server as a str"""
        print("En attente d'une reponse serveur !")
        data = self.sock.recv(1024)
        return data.decode().strip()
    
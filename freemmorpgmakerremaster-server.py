import pygame
import socket
import json

class MarioMMOClient:
    def __init__(self):
        self.server_address = ('localhost', 8000)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.game_data = {}
        self.player_data = {}
        self.other_players = {}
        
    def connect_to_server(self):
        try:
            self.socket.connect(self.server_address)
            
            # Send player join request
            join_request = {
                'type': 'join',
                'player_name': 'Mario'
            }
            self.socket.sendall(json.dumps(join_request).encode())
            
            # Receive player ID and initial game data
            data = self.socket.recv(2048).decode()
            response = json.loads(data)
            
            self.player_id = response['player_id'] 
            self.game_data = response['game_data']
            print(f"Connected to {self.game_data['title']} server as player {self.player_id}")
            
        except ConnectionRefusedError:
            print("Could not connect to the game server")
            return False
        
        return True
            
    def load_assets(self):
        # Load sprite sheets, fonts, audio, etc.
        pass
        
    def update_player(self, player_data):
        self.player_data = player_data
        
    def update_other_players(self, players_data):
        for player_id, player_data in players_data.items():
            if player_id != self.player_id:
                self.other_players[player_id] = player_data
        
    def render_map(self, map_data):
        # Render the current map using pygame
        pass
        
    def render_characters(self):
        # Render player character
        pass
        
        # Render other players
        for player_id, player_data in self.other_players.items():
            pass
        
    def render_ui(self):
        # Render player stats, inventory, etc.
        pass

    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_LEFT]:
            self.player_data['x'] -= 1
        if keys[pygame.K_RIGHT]:  
            self.player_data['x'] += 1
        if keys[pygame.K_UP]:
            self.player_data['y'] -= 1  
        if keys[pygame.K_DOWN]:
            self.player_data['y'] += 1
            
        # Send player update to server
        player_update = {
            'type': 'update',
            'player_id': self.player_id,
            'player_data': self.player_data  
        }
        self.socket.sendall(json.dumps(player_update).encode())
        
    def game_loop(self):
        pygame.init()
        
        self.load_assets()
        clock = pygame.time.Clock()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Send player leave notification
                    leave_notification = {
                        'type': 'leave',
                        'player_id': self.player_id
                    }
                    self.socket.sendall(json.dumps(leave_notification).encode())
                    pygame.quit() 
                    return
                
            # Receive game state update from server
            data = self.socket.recv(2048).decode()
            game_state = json.loads(data)
            
            self.update_player(game_state['players'][self.player_id])
            self.update_other_players(game_state['players'])
            
            pygame.display.get_surface().fill((0, 0, 0))
            
            self.render_map(self.game_data['maps'][game_state['map']])  
            self.render_characters()
            self.render_ui()
            
            self.handle_input()
            
            pygame.display.flip()
            clock.tick(60)
                
if __name__ == "__main__":
    client = MarioMMOClient()
    
    if client.connect_to_server():
        client.game_loop()

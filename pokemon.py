import pygame
import socket
import threading
import pickle

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Club Pokémon MMORPG")

# Define colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (150, 150, 150)
LIGHT_GREEN = (0, 255, 0)

# Tile size
TILE_SIZE = 64

# Sample tile map (2D grid)
tile_map = [
    [0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
    [0, 0, 0, 0, 2, 2, 2, 0, 0, 0],
    [0, 3, 3, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 2, 2, 2, 0, 0],
    [0, 0, 0, 4, 0, 0, 0, 0, 0, 0],
]

# Player class
class Player:
    def __init__(self, x, y, name):
        self.x = x
        self.y = y
        self.name = name

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def serialize(self):
        return (self.x, self.y, self.name)

    @staticmethod
    def deserialize(data):
        x, y, name = data
        return Player(x, y, name)

# Networking setup
players = {}

def server_thread():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 12345))
    server_socket.listen(5)

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        players[addr] = Player(1 * TILE_SIZE, 1 * TILE_SIZE, "Player")  # Placeholder for player name
        threading.Thread(target=client_handler, args=(client_socket, addr)).start()

def client_handler(client_socket, addr):
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            
            # Update player position based on received data
            players[addr] = Player.deserialize(pickle.loads(data))

            # Broadcast player positions to all clients
            positions = {addr: player.serialize() for addr, player in players.items()}
            for player_addr in players.keys():
                if player_addr != addr:  # Avoid sending to self
                    player_socket = players[player_addr].client_socket
                    player_socket.send(pickle.dumps(positions))

        except Exception as e:
            print(f"Connection error: {e}")
            break
    client_socket.close()
    del players[addr]

def draw_overworld():
    for row_index, row in enumerate(tile_map):
        for col_index, tile in enumerate(row):
            color = WHITE if tile == 0 else GRAY
            pygame.draw.rect(screen, color, (col_index * TILE_SIZE, row_index * TILE_SIZE, TILE_SIZE, TILE_SIZE))

def draw_players():
    for addr, player in players.items():
        pygame.draw.rect(screen, LIGHT_GREEN, (player.x, player.y, TILE_SIZE, TILE_SIZE))
        # Render player names
        font = pygame.font.Font(None, 24)
        text = font.render(player.name, True, BLACK)
        screen.blit(text, (player.x, player.y - 20))  # Draw above player

def main():
    running = True
    player_name = "Player"  # Placeholder for player name input logic
    player = Player(1 * TILE_SIZE, 1 * TILE_SIZE, player_name)

    while running:
        screen.fill(BLACK)
        draw_overworld()  # Draw the overworld
        draw_players()    # Draw all players

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    player.move(0, -TILE_SIZE)  # Move up
                if event.key == pygame.K_DOWN:
                    player.move(0, TILE_SIZE)  # Move down
                if event.key == pygame.K_LEFT:
                    player.move(-TILE_SIZE, 0)  # Move left
                if event.key == pygame.K_RIGHT:
                    player.move(TILE_SIZE, 0)  # Move right

                # Serialize and send player data to server
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                        client_socket.connect(('server_ip', 12345))  # Replace 'server_ip' with actual server IP
                        client_socket.send(pickle.dumps(player.serialize()))
                except Exception as e:
                    print(f"Failed to send data: {e}")

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()

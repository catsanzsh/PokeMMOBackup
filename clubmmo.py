import pygame
import random
import socket
import threading
import pickle
import miniupnpc

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Club Pokémon")

# Define colors
BLACK = (0, 0, 0)
LIGHT_GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
GRAY = (150, 150, 150)

# Tile size
TILE_SIZE = 64

# Sample tile map
tile_map = [
    [0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
    [0, 0, 0, 0, 2, 2, 2, 0, 0, 0],
    [0, 3, 3, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 2, 2, 2, 0, 0],
    [0, 0, 0, 4, 0, 0, 0, 0, 0, 0],
]

# Player class
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def serialize(self):
        return (self.x, self.y)

    @staticmethod
    def deserialize(data):
        x, y = data
        return Player(x, y)

# Networking setup
players = {}

def server_thread():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))
    server_socket.listen(5)

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        players[addr] = Player(1 * TILE_SIZE, 1 * TILE_SIZE)
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
                # Send position updates to all players
                if player_addr != addr:
                    client_socket.send(pickle.dumps(positions))

        except Exception as e:
            print(f"Connection error: {e}")
            break
    client_socket.close()
    del players[addr]

def draw_overworld():
    # Draw the overworld
    for row_index, row in enumerate(tile_map):
        for col_index, tile in enumerate(row):
            color = WHITE if tile == 0 else GRAY
            pygame.draw.rect(screen, color, (col_index * TILE_SIZE, row_index * TILE_SIZE, TILE_SIZE, TILE_SIZE))

def draw_menu():
    screen.fill(BLACK)
    font = pygame.font.Font(None, 48)
    title = font.render("Club Pokémon", True, WHITE)
    subtitle = font.render("Press H to Host or J to Join a Server", True, WHITE)
    
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 50))
    screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, HEIGHT // 2 + 10))

    # Host button
    host_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 60, 200, 50)
    pygame.draw.rect(screen, LIGHT_GREEN, host_button)
    button_text = font.render("Host Server", True, BLACK)
    screen.blit(button_text, (host_button.x + (host_button.width - button_text.get_width()) // 2,
                               host_button.y + (host_button.height - button_text.get_height()) // 2))

    return host_button

def automatic_port_forward():
    try:
        # UPnP setup
        upnp = miniupnpc.UPnP()
        upnp.discoverdelay = 200  # milliseconds
        upnp.discover()
        upnp.selectigd()
        external_ip = upnp.externalipaddress()
        print(f"External IP: {external_ip}")
        
        # Forward the port
        port = 12345
        upnp.addportmapping(port, 'TCP', upnp.lanaddr, port, 'Club Pokémon', '', 0)
        print(f"Port {port} forwarded")
    except Exception as e:
        print(f"Port forwarding failed: {e}")

def main():
    running = True
    server_running = False
    player = Player(1 * TILE_SIZE, 1 * TILE_SIZE)

    while running:
        host_button = draw_menu()  # Draw the main menu

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    if host_button.collidepoint(event.pos) and not server_running:
                        server_running = True
                        threading.Thread(target=server_thread, daemon=True).start()
                        print("Hosting server...")
                        automatic_port_forward()  # Attempt port forwarding

        if server_running:
            draw_overworld()  # Draw the overworld
            pygame.draw.rect(screen, LIGHT_GREEN, (player.x, player.y, TILE_SIZE, TILE_SIZE))

            # Draw other players
            for addr, p in players.items():
                if addr != 'localhost':
                    pygame.draw.rect(screen, WHITE, (p.x, p.y, TILE_SIZE, TILE_SIZE))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()

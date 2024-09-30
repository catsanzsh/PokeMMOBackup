import socket
import threading
import pickle
import gradio as gr

# Networking setup
players = {}
connections = {}
server_running = True
lock = threading.Lock()

# Sample tile map (modifiable)
tile_map = [
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 2, 0, 0, 3, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1],
]

def broadcast_positions():
    positions = {addr: player for addr, player in players.items()}
    data = pickle.dumps(positions)
    with lock:
        for conn in connections.values():
            try:
                conn.send(data)
            except:
                pass

def client_handler(client_socket, addr):
    with lock:
        connections[addr] = client_socket
        players[addr] = {'x': 2, 'y': 2}
    print(f"Player {addr} connected.")
    
    while server_running:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            position = pickle.loads(data)
            with lock:
                players[addr] = position
            broadcast_positions()
        except:
            break

    client_socket.close()
    with lock:
        if addr in players:
            del players[addr]
        if addr in connections:
            del connections[addr]
    print(f"Player {addr} disconnected.")

def server_thread():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 12345))  # Bind to all interfaces
    server_socket.listen(5)
    print("Server started and listening on port 12345.")
    
    while server_running:
        try:
            client_socket, addr = server_socket.accept()
            threading.Thread(target=client_handler, args=(client_socket, addr), daemon=True).start()
        except:
            break

    server_socket.close()

def get_player_list():
    with lock:
        return list(players.keys())

def get_connected_players_count():
    with lock:
        return len(players)

def kick_player(addr):
    addr_tuple = eval(addr)
    with lock:
        if addr_tuple in connections:
            connections[addr_tuple].close()
            del connections[addr_tuple]
        if addr_tuple in players:
            del players[addr_tuple]
    print(f"Kicked player {addr_tuple}")
    return get_player_list()

def update_tile_map(new_tile_map):
    global tile_map
    try:
        tile_map = eval(new_tile_map)
        print("Tile map updated.")
        return "Tile map updated."
    except Exception as e:
        print("Failed to update tile map:", e)
        return "Failed to update tile map."

def send_message_to_players(message):
    data = pickle.dumps({'message': message})
    with lock:
        for conn in connections.values():
            try:
                conn.send(data)
            except:
                pass
    print(f"Sent message: {message}")
    return f"Sent message: {message}"

# Run Gradio interface
def run_gradio():
    with gr.Blocks() as app:
        gr.Markdown("# Server Admin Panel with HUD")

        # HUD Section
        with gr.Row():
            player_count_box = gr.Number(label="Connected Players", value=lambda: get_connected_players_count(), interactive=False)
            refresh_player_count_button = gr.Button("Refresh Player Count")
            refresh_player_count_button.click(fn=lambda: get_connected_players_count(), inputs=None, outputs=player_count_box)

        # Player list
        with gr.Column():
            player_list_box = gr.Textbox(label="Connected Players", value=lambda: "\n".join(map(str, get_player_list())), interactive=False, lines=10)
            refresh_button = gr.Button("Refresh Player List")
            refresh_button.click(fn=lambda: "\n".join(map(str, get_player_list())), inputs=None, outputs=player_list_box)

        # Kick player
        with gr.Column():
            kick_player_textbox = gr.Textbox(label="Enter Player Address to Kick", placeholder="e.g. ('127.0.0.1', 12345)")
            kick_button = gr.Button("Kick Player")
            kick_button.click(fn=kick_player, inputs=kick_player_textbox, outputs=player_list_box)

        # Edit tile map
        with gr.Column():
            tile_map_box = gr.Textbox(label="Edit Tile Map", value=str(tile_map), lines=10)
            update_tile_button = gr.Button("Update Tile Map")
            tile_map_output = gr.Textbox(label="Tile Map Update Status", interactive=False)
            update_tile_button.click(fn=update_tile_map, inputs=tile_map_box, outputs=tile_map_output)

        # Send message to players
        with gr.Column():
            message_box = gr.Textbox(label="Broadcast Message", placeholder="Enter message here")
            send_message_button = gr.Button("Send Message")
            message_output = gr.Textbox(label="Message Status", interactive=False)
            send_message_button.click(fn=send_message_to_players, inputs=message_box, outputs=message_output)

    app.launch(server_name="0.0.0.0", server_port=5000)

if __name__ == "__main__":
    # Start the server thread
    threading.Thread(target=server_thread, daemon=True).start()
    # Start the Gradio app in a separate thread
    threading.Thread(target=run_gradio, daemon=True).start()

    try:
        while True:
            pass  # Keep the main thread alive
    except KeyboardInterrupt:
        server_running = False
        print("Server shutting down.")

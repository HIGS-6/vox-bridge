import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from websocket_server import WebsocketServer

import state

# Protocolo
ORDER_SET_USERNAME = 1
ORDER_BROADCAST_TEXT = 3

# clients: client_id -> {"username": str}
clients = {}


def run_webclient_server(host="0.0.0.0", port=5173, directory="webclient"):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"[WebClient] Serving '{directory}' at http://{host}:{port}")
    httpd.serve_forever()


def new_client(client, server):
    clients[client["id"]] = {"username": "anon"}
    print(f"[Broadcast] Conectado: {client['id']}")


def client_left(client, server):
    info = clients.get(client["id"], {"username": "anon"})
    print(f"[Broadcast] Desconectado: {info['username']}")
    clients.pop(client["id"], None)


def message_received(client, server, message):
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        return

    if data.get("order") == ORDER_SET_USERNAME:
        username = data.get("username", "anon")
        clients[client["id"]]["username"] = username
        print(f"[Broadcast] Usuario set: {username}")


def broadcast_text(server: WebsocketServer, text: str):
    payload = json.dumps({"order": ORDER_BROADCAST_TEXT, "text": text})
    # Esta lib ya manda a todos con una sola llamada
    server.send_message_to_all(payload)


def run_broadcast(host="0.0.0.0", port=8765):
    """
    state.translated_text_queue debe ser queue.Queue[str]
    """
    server = WebsocketServer(host=host, port=port)
    server.set_fn_new_client(new_client)
    server.set_fn_client_left(client_left)
    server.set_fn_message_received(message_received)

    print(f"[Broadcast] Server en ws://{host}:{port}")

    # Arranca el server en su propio hilo interno
    # (run_forever bloquea, así que lo lanzamos en background)
    import threading

    webclient_t = threading.Thread(target=run_webclient_server, daemon=True)
    webclient_t.start()

    t = threading.Thread(target=server.run_forever, daemon=True)
    t.start()

    print("[Broadcast] Loop principal consumiendo la queue...")

    # Loop SYNC normal y corriente
    while True:
        text = state.translated_text.get()  # bloquea hasta que haya algo
        if not text:
            continue
        print(f"[Broadcast] Enviando: {text}")
        broadcast_text(server, text)

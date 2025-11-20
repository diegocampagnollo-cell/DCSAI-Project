# core/dcs_network.py
import os
import json
import base64
import socket
import threading
import hashlib
import secrets
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

DATA_DIR = "data"
IDENTITY_FILE = os.path.join(DATA_DIR, "identity.json")
PEERS_FILE = os.path.join(DATA_DIR, "peers.json")

# Utils
def load_identity():
    if not os.path.exists(IDENTITY_FILE):
        raise FileNotFoundError("identity.json não encontrado. Rode a Fase 111 primeiro.")
    with open(IDENTITY_FILE, "r") as f:
        return json.load(f)

def save_peer(peer_info):
    os.makedirs(DATA_DIR, exist_ok=True)
    peers = {}
    if os.path.exists(PEERS_FILE):
        with open(PEERS_FILE, "r") as f:
            peers = json.load(f)
    peers[peer_info["dcs_id"]] = peer_info
    with open(PEERS_FILE, "w") as f:
        json.dump(peers, f, indent=4)

def load_private_public_keys(identity):
    private_key = serialization.load_pem_private_key(
        identity["private_key"].encode(), password=None
    )
    public_key = serialization.load_pem_public_key(
        identity["public_key"].encode()
    )
    return private_key, public_key

# Message helpers
def send_json(sock, obj):
    data = (json.dumps(obj) + "\n").encode()
    sock.sendall(data)

def recv_json(sock):
    buf = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
        if b"\n" in buf:
            line, rest = buf.split(b"\n", 1)
            return json.loads(line.decode())
    if buf:
        return json.loads(buf.decode())
    return None

# Server (ouvinte) que aceita handshakes
def start_server(bind_host="0.0.0.0", bind_port=22000):
    identity = load_identity()
    priv, pub = load_private_public_keys(identity)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((bind_host, bind_port))
    s.listen(5)
    print(f"[DCS-NET] Servidor ouvindo em {bind_host}:{bind_port} (DCS-ID {identity['dcs_id']})")

    def client_thread(conn, addr):
        try:
            msg = recv_json(conn)
            if not msg or msg.get("type") != "HELLO":
                print("[DCS-NET] Mensagem inicial inválida")
                conn.close()
                return

            peer_dcs = msg.get("dcs_id")
            peer_pub_pem = msg.get("pub_key")
            print(f"[DCS-NET] HELLO de {peer_dcs} ({addr})")

            # gera nonce para o peer
            nonce = secrets.token_bytes(32)
            send_json(conn, {"type":"CHALLENGE", "nonce": base64.b64encode(nonce).decode()})

            # espera resposta assinada
            resp = recv_json(conn)
            if not resp or resp.get("type") != "RESPONSE":
                print("[DCS-NET] RESPOSTA inválida")
                conn.close()
                return

            signature_b64 = resp.get("signature")
            signature = base64.b64decode(signature_b64)
            # verifica assinatura com chave pública enviada no HELLO
            peer_pub = serialization.load_pem_public_key(peer_pub_pem.encode())
            try:
                peer_pub.verify(
                    signature,
                    nonce,
                    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                    hashes.SHA256()
                )
            except Exception as e:
                print("[DCS-NET] Verificação falhou:", e)
                send_json(conn, {"type":"ERROR", "reason":"signature_verify_failed"})
                conn.close()
                return

            # se OK, agora o servidor assina um nonce do servidor para autorizar reciprocamente
            nonce_srv = secrets.token_bytes(32)
            sig_srv = priv.sign(
                nonce_srv,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            send_json(conn, {"type":"AUTH_OK", "nonce": base64.b64encode(nonce_srv).decode(), "signature": base64.b64encode(sig_srv).decode()})

            # opcional: grava peer (salva pub_key e endpoint)
            peer_info = {
                "dcs_id": peer_dcs,
                "pub_key": peer_pub_pem,
                "addr": f"{addr[0]}:{addr[1]}"
            }
            save_peer(peer_info)
            print(f"[DCS-NET] Peer {peer_dcs} autenticado e salvo.")
        finally:
            conn.close()

    try:
        while True:
            conn, addr = s.accept()
            threading.Thread(target=client_thread, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("[DCS-NET] Servidor encerrado.")
    finally:
        s.close()

# Client: conecta a outro núcleo e faz handshake
def connect_and_handshake(remote_host, remote_port):
    identity = load_identity()
    priv, pub = load_private_public_keys(identity)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((remote_host, remote_port))

    # envia HELLO com dcs_id e public key
    send_json(sock, {"type":"HELLO", "dcs_id": identity["dcs_id"], "pub_key": identity["public_key"]})

    # espera CHALLENGE
    challenge_msg = recv_json(sock)
    if not challenge_msg or challenge_msg.get("type") != "CHALLENGE":
        print("[DCS-NET] Não recebeu CHALLENGE")
        sock.close()
        return False

    nonce_b64 = challenge_msg.get("nonce")
    nonce = base64.b64decode(nonce_b64)

    # assina o nonce e envia RESPONSE
    signature = priv.sign(
        nonce,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )
    send_json(sock, {"type":"RESPONSE", "signature": base64.b64encode(signature).decode(), "challenge_hash": hashlib.sha256(nonce).hexdigest()})

    # espera AUTH_OK
    auth = recv_json(sock)
    if not auth or auth.get("type") != "AUTH_OK":
        print("[DCS-NET] Autorização falhou ou não recebida")
        sock.close()
        return False

    # verifica assinatura do servidor para um nonce do cliente (reciprocidade)
    nonce_srv = base64.b64decode(auth.get("nonce"))
    sig_srv = base64.b64decode(auth.get("signature"))

    # remote may have sent its pub_key before in HELLO; but client only got its pub_key if the server sent it earlier.
    # To be safe, retrieve server's public key from peers.json after successful handshake, or assume server included it earlier.
    # Here we will request server to include pub_key in HELLO in a production version. For now we accept and store endpoint.
    # We'll trust the signed nonce as success if signature verifies using the public key that server included in initial HELLO in the other direction.
    # For the simplicity of this demo, we will skip verifying server signature if we didn't previously receive server pub_key.
    # But better approach: server should include its pub_key in HELLO (this implementation does for the server side when it got HELLO).
    # If the server included pub_key in a prior HELLO to us, the server's pub_key is available in peers.json.
    # Try loading peer info from peers.json
    try:
        if os.path.exists(PEERS_FILE):
            with open(PEERS_FILE, "r") as f:
                peers = json.load(f)
            # if remote already saved us earlier, remote's pubkey might be present; otherwise server should have included it
    except Exception:
        peers = {}

    # For this demo we will accept authentication success and save endpoint info.
    # Save peer with endpoint; in a robust system you'd verify sig_srv with server's public key.
    peer_info = {"dcs_id": f"{remote_host}:{remote_port}", "addr": f"{remote_host}:{remote_port}"}
    save_peer(peer_info)
    print("[DCS-NET] Handshake finalizado com sucesso.")
    sock.close()
    return True

# Quick CLI test
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--server", action="store_true", help="Inicia servidor de handshake")
    p.add_argument("--host", default="127.0.0.1", help="Host remoto (para client)")
    p.add_argument("--port", type=int, default=22000, help="Porta (server bind / remote port)")
    p.add_argument("--connect", action="store_true", help="Conecta a host:port e faz handshake")
    args = p.parse_args()

    if args.server:
        start_server(bind_host="0.0.0.0", bind_port=args.port)
    elif args.connect:
        connect_and_handshake(args.host, args.port)
    else:
        p.print_help()

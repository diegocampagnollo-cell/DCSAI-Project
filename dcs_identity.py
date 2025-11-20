import os
import json
import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa # type: ignore
from cryptography.hazmat.primitives import serialization # type: ignore

# Diretório onde a identidade será salva
DATA_DIR = "data"
IDENTITY_FILE = os.path.join(DATA_DIR, "identity.json")

def generate_identity():
    # Garante que o diretório exista
    os.makedirs(DATA_DIR, exist_ok=True)

    # Se já existir uma identidade, apenas retorna
    if os.path.exists(IDENTITY_FILE):
        with open(IDENTITY_FILE, "r") as f:
            identity = json.load(f)
        print(f"[DCs.AI] Identity já existente.\nDCS-ID: {identity['dcs_id']}")
        return identity

    print("[DCs.AI] Gerando nova identidade digital...")

    # Gera um par de chaves RSA 2048 bits
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    # Serializa as chaves
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Gera o hash da chave pública (identificador único)
    dcs_id = "0x" + hashlib.sha256(public_pem).hexdigest()[:16].upper()

    # Salva as chaves e o ID em arquivo JSON
    identity = {
        "public_key": public_pem.decode(),
        "private_key": private_pem.decode(),
        "dcs_id": dcs_id
    }

    with open(IDENTITY_FILE, "w") as f:
        json.dump(identity, f, indent=4)

    print(f"[DCs.AI] Identidade criada com sucesso.")
    print(f"[DCs.AI] DCS-ID: {dcs_id}")

    return identity


if __name__ == "__main__":
    identity = generate_identity()

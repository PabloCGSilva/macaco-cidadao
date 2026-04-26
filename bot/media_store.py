import os
import hashlib
from datetime import datetime

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")

EXTENSOES = {
    "photo": ".jpg",
    "video": ".mp4",
    "audio": ".ogg",
}


def salvar_midia(dados: bytes, tipo: str, protocolo: str) -> str:
    """Persiste o arquivo em uploads/ e retorna o path relativo."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    ext = EXTENSOES.get(tipo, ".bin")
    nome = f"{protocolo}{ext}"
    caminho = os.path.join(UPLOAD_DIR, nome)

    with open(caminho, "wb") as f:
        f.write(dados)

    return caminho


def hash_midia(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()

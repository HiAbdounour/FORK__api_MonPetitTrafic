"""
Pour plus de facilité, on met toutes les fonctions annexes ici.

Le fourre-tout
"""
# IMPORTS =====
from typing import Any
from base64 import b64decode as decoder
import os,json

# UTILS =====

def format_rss_url(slug:str)-> str:
    """
    Transforme un slug (de feeds.json) en une URL de flux RSS Nitter
    directement exploitable
    """
    return f"https://nitter.net/{slug}/rss"

def safe_import_sk()-> str:
    """
    Importer la clé privée du projet Firebase
    de manière sécurisée (par .env et contrôlé par un try ... except)
    """
    try:
        k_retrieve = os.getenv('ENCODED_FIREBASE_SERVICE_KEY')
        k_retrieve  = json.dumps(k_retrieve)
        k = decoder(k_retrieve).decode('utf-8')
        return json.dumps(k)
    except Exception as e:
        raise RuntimeError("Not found or unreadable Firebase service key")

# FICHIERS ===

def import_feeds()-> Any|None:
    """
    Renvoie le contenu du fichier feeds.json
    """
    try:
        with open("feeds.json","r") as file:
            data = json.load(file)
        return data
    except Exception as e:
        raise e
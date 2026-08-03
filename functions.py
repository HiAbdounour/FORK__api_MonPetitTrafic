"""
Pour plus de facilité, on met toutes les fonctions annexes ici.

Le fourre-tout
"""
# IMPORTS =====
from typing import Any, TypeAlias
from base64 import b64decode as decoder
import feedparser, requests
import firebase_admin
import os,json
from dotenv import load_dotenv
import re
from datetime import datetime

# UTILS =====

FormattableDate: TypeAlias = str# format attendu : "YYYY-MM-DDTHH:MM:SS.mmmZ"
ExpectedFormat = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")

def format_rss_url(slug:str)-> str:
    """
    Transforme un slug (de feeds.json) en une URL de flux RSS Nitter
    directement exploitable
    """
    return f"https://nitter.net/{slug}/rss"

def safe_import_sk()-> Any:
    """
    Importer la clé privée du projet Firebase
    de manière sécurisée (par .env et contrôlé par un try ... except)
    """
    try:
        load_dotenv()
        k_retrieve = os.getenv('ENCODED_FIREBASE_SERVICE_KEY')
        if k_retrieve is None:
            raise Exception
        k = decoder(k_retrieve.encode('utf-8')).decode('utf-8')
        return json.loads(k)
    except Exception as e:
        raise RuntimeError("Not found or unreadable Firebase service key")
    
def formatAsDate(d:str)-> FormattableDate|None:
    """
    Vérifie qu'une chaîne de caractères d respecte bien le format attendu
    pour les dates
    Si ce n'est pas le cas, renvoie None
    """
    try:
        dt = datetime.strptime(d,"%Y-%m-%dT%H:%M:%S.%fZ")
        return d # est de type FormattableDate
    except Exception:
        return None

# FICHIERS =====

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
    

# FIREBASE =====

def init_firebase(k:Any)-> firebase_admin.App:
    """
    Initialise une session Firebase avec la clé privée
    """
    try:
        return firebase_admin.initialize_app(firebase_admin.credentials.Certificate(k))
    except Exception as e:
        raise firebase_admin.DefaultCredentialsError("Cannot initialize a Firebase session with this private key")

# FETCH (Requests to Nitter) =====

def fetch_nitter(url:str,etag:str,modified:FormattableDate|str,timeout:int=20):
    """
    Fetche les instances de Nitter pour un compte X et renvoie le contenu obtenu après la requête

    Le fetch utilise la méthode If-None-Match/If-Modified-Since afin d'éviter de spammer
    les instances de Nitter
    """
    headers = {}

    headers["If-None-Match"] = etag  # If-None-Match a la priorité 

    modified_corrected:FormattableDate|None = formatAsDate(modified)
    if modified_corrected is not None:
        headers["If-Modified-Since"] = modified_corrected

    try:
        req = requests.get(url,headers=headers,timeout=timeout)
    except Exception as e:
        raise e
    else:
        if req.status_code==304:
            return {"status": 304, "headers": req.headers, "rawcontent": None}
        if req.status_code>=400:
            return {"status": req.status_code, "text": req.text, "headers": req.headers, "rawcontent":None}
        return {"status": req.status_code, "rawcontent": req.content, "headers": req.headers}

def parsing():
    """
    === Sera utilisé pour filtrer les posts et ne conserver que les infos trafic
    """
    pass
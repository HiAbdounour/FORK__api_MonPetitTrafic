"""
Pour plus de facilité, on met toutes les fonctions annexes ici.

Le fourre-tout
"""
# IMPORTS =====
from typing import Any
from custom_types import *
from base64 import b64decode as decoder
import feedparser, requests
import firebase_admin
import os,json
from dotenv import load_dotenv
from datetime import datetime

# UTILS =====


print("DEBUG::WARNING ! ExpectedFormat n'a pas été testé !")#<<<DEBUG was not tested

def format_rss_url(slug:str)-> str:
    """
    Transforme un slug (de feeds.json) en une URL de flux RSS Nitter
    directement exploitable
    """
    # RMQ : Nitter est uniquement exploitable par Python
    # les autres instances sont exploitables avec JavaScript
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
        dt = datetime.strptime(d,"%a, %d %b %Y %H:%M:%S GMT") #DAY, DD MON YYYY hh:mm:ss GMT
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

def fetch_nitter(url:str,etag:str|None=None,modified:FormattableDate|str|None=None,timeout:int=20):
    """
    Fetche les instances de Nitter pour un compte X et renvoie le contenu obtenu après la requête

    Le fetch utilise la méthode If-None-Match/If-Modified-Since afin d'éviter de spammer
    les instances de Nitter
    """
    headers = {}

    headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MonPetitTrafic/1.0(+https://github.com/MonPetitTrafic)"
    headers["Accept"] = "application/rss+xml, application/xml, text/xml"
    # headers["From"] ## nécessaire pour l'automatisation par GitHub Actions

    if etag: # If-None-Match a la priorité 
        headers["If-None-Match"] = etag

    if modified is not None:
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
        return {"status": req.status_code, "text":req.text,"rawcontent": req.content, "headers": req.headers}

def parsing(ctxt:Any)-> list[postsReady]:
    """
    Filtre les posts X en ne conservant que les posts intéressants

    Fonctionne à partir d'un dico du type {"status": req.status_code, "text":req.text,"rawcontent": req.content, "headers": req.headers}
    Ce qui nous intéresse, c'est "text"
    Et renvoie une liste des posts prêts à être envoyés sur FCM (formattés en un dico)

    Perso, je trouve la méthode de parsing actuellement utilisée pourrie mais on l'améliorera plus tard...
    """
    KEPT:list[postsReady] = []
    try:
        if ctxt.status_code!=200:
            raise ValueError
        feed = feedparser.parse(ctxt.text)
    except Exception as e:
        raise ValueError(f"Invalid value for ctxt. Found {ctxt}.\nRemember that parsing works only for successful fetching !")

    
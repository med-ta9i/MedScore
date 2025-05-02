import requests
import pandas as pd # Toujours présent, mais non utilisé. À enlever si non nécessaire.
import json
import os
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from io import BytesIO
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class FootballDataAPI:


    def __init__(self, api_key, cache_dir='cache', image_cache_dir='image_cache'):
        """Initialisation de la classe avec la clé API"""
        self.api_key = api_key
        self.base_url = "https://api.football-data.org/v4"
        self.headers = {"X-Auth-Token": self.api_key}
        self.cache_dir = cache_dir
        self.image_cache_dir = image_cache_dir
        self.logo_cache = {}

        # Création des dossiers cache s'ils n'existent pas
        for directory in [cache_dir, image_cache_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)

    

    def get_competitions(self):
        endpoint = "/competitions"
        data = self._make_request(endpoint)

        excluded_codes = ['WC', 'CL', 'EC']

        # Filtrer les compétitions
        if isinstance(data, dict) and 'competitions' in data:
            filtered_competitions = [
                comp for comp in data.get('competitions', [])
                if comp.get('code') not in excluded_codes
            ]
            return filtered_competitions
        elif isinstance(data, dict) and 'error' in data:
             print(f"Erreur API lors de la récupération des compétitions: {data['error']}")
             return {"error": data['error']} # Retourner l'erreur pour la gestion UI
        else:
            print("Réponse inattendue de l'API pour les compétitions.")
            return {"error": "Réponse inattendue de l'API"}


    def get_competition_standings(self, competition_id):
        """Récupère le classement d'une compétition"""
        endpoint = f"/competitions/{competition_id}/standings"
        return self._make_request(endpoint)

    def get_competition_matches(self, competition_id, matchday=None):
        """Récupère les matchs d'une compétition, éventuellement filtrés par journée"""
        endpoint = f"/competitions/{competition_id}/matches"
        params = {}
        if matchday:
            params['matchday'] = matchday
        return self._make_request(endpoint, params)

    def get_competition_scorers(self, competition_id, limit=10):
        """Récupère les meilleurs buteurs d'une compétition"""
        endpoint = f"/competitions/{competition_id}/scorers"
        params = {'limit': limit}
        return self._make_request(endpoint, params)

    # --- NOUVELLE MÉTHODE ---
    def get_team_matches(self, team_id, status=None):
        """Récupère les matchs d'une équipe spécifique"""
        endpoint = f"/teams/{team_id}/matches"
        params = {}
        if status:
            params['status'] = status
        return self._make_request(endpoint, params)
    # -----------------------

    def get_team_logo(self, team_id, crest_url):

        if not crest_url:
             return None

        
        image_path = os.path.join(self.image_cache_dir, f"team_{team_id}.png")


        if os.path.exists(image_path):
            try:

                 file_age = time.time() - os.path.getmtime(image_path)
                 if file_age < 604800: # 7 jours
                    return Image.open(image_path)
                 else:
                     print(f"Logo en cache fichier obsolète pour {team_id}, re-téléchargement.")
            except Exception as e:
                print(f"Erreur lors de l'ouverture de l'image en cache fichier: {e}")
                # Tenter de re-télécharger si l'ouverture échoue

        # Si pas en cache ou erreur, télécharger
        try:
            print(f"Téléchargement du logo pour {team_id} depuis {crest_url}")
            response = requests.get(crest_url, headers={"X-Auth-Token": self.api_key} if 'football-data.org' in crest_url else {}) # Adapter headers si besoin
            response.raise_for_status()

            # Sauvegarder l'image
            image = Image.open(BytesIO(response.content))
            # Essayer de convertir en RGBA pour gérer la transparence potentielle des PNG/SVG
            try:
                image = image.convert("RGBA")
            except Exception as conv_e:
                print(f"Note : Impossible de convertir l'image {team_id} en RGBA : {conv_e}. Utilisation du format original.")

            image.save(image_path)
            print(f"Logo sauvegardé pour {team_id} dans {image_path}")
            return image
        except requests.exceptions.RequestException as e:
            print(f"Erreur réseau lors du téléchargement du logo {team_id}: {e}")
        except Exception as e:
            print(f"Erreur générale lors du traitement/téléchargement du logo {team_id}: {e}")

            return None # Retourner None si le logo ne peut être obtenu

    def _make_request(self, endpoint, params=None):
        """Effectue une requête à l'API avec gestion du cache"""
        cache_file = self._get_cache_filename(endpoint, params)


        if os.path.exists(cache_file):
            try:
                file_age = time.time() - os.path.getmtime(cache_file)
                if file_age < 3600:  # 1 heure
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                else:
                    print(f"Cache API obsolète pour {endpoint}, requête API.")
            except (IOError, json.JSONDecodeError) as e:
                print(f"Erreur lecture/décodage cache API {cache_file}: {e}. Requête API.")



        url = f"{self.base_url}{endpoint}"
        print(f"Requête API: {url} avec params {params}")
        try:
            # Ajouter un timeout aux requêtes
            response = requests.get(url, headers=self.headers, params=params, timeout=10) # Timeout de 10s
            response.raise_for_status() #  une exception pour les codes 4xx/5xx
            data = response.json()

            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4) # Indent pour lisibilité
            except IOError as e:
                 print(f"Erreur écriture cache API {cache_file}: {e}")


            return data
        except requests.exceptions.Timeout:
            print(f"Erreur lors de la requête API: Timeout")
            return self._fallback_to_cache_or_error(cache_file, "Timeout lors de la connexion à l'API.")
        except requests.exceptions.HTTPError as e:
             print(f"Erreur HTTP lors de la requête API: {e.response.status_code} - {e}")

             if e.response.status_code == 429:
                  wait_time = int(e.response.headers.get('Retry-After', 60)) # Respecter l'en-tête si possible
                  print(f"Limite API atteinte. Attente de {wait_time} secondes.")
                  # On pourrait implémenter une attente ici, mais pour l'UI, il vaut mieux retourner une erreur.
                  return self._fallback_to_cache_or_error(cache_file, f"Limite API atteinte. Réessayez dans {wait_time}s.")
             else:
                  return self._fallback_to_cache_or_error(cache_file, f"Erreur HTTP {e.response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la requête API: {e}")
            return self._fallback_to_cache_or_error(cache_file, str(e))
        except json.JSONDecodeError as e:
            print(f"Erreur décodage JSON réponse API: {e}")
            return self._fallback_to_cache_or_error(cache_file, "Réponse invalide de l'API.")

    def _fallback_to_cache_or_error(self, cache_file, error_message):
        """Tente de retourner le cache si la requête API échoue, sinon retourne une erreur."""
        if os.path.exists(cache_file):
            print(f"Utilisation des données en cache (potentiellement obsolètes) suite à l'erreur: {error_message}")
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                 print(f"Erreur lecture/décodage cache API lors du fallback {cache_file}: {e}")
                 return {"error": f"{error_message} (et cache indisponible/invalide)"}
        else:
            return {"error": error_message}

    def _get_cache_filename(self, endpoint, params=None):

        clean_endpoint = endpoint.replace('/', '_').replace('?', '_').replace('&', '_')

        param_str = ""
        if params:
            sorted_params = sorted(params.items())
            param_str = "_" + "_".join(f"{k}-{v}" for k, v in sorted_params)

        # Limiter la longueur du nom de fichier si nécessaire
        max_len = 100
        full_name = f"{clean_endpoint}{param_str}.json"
        if len(full_name) > max_len:
            import hashlib
            param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
            full_name = f"{clean_endpoint[:max_len - 10]}_{param_hash}.json"

        return os.path.join(self.cache_dir, full_name)

    def get_match_details(self, match_id):

        endpoint = f"/matches/{match_id}"
        return self._make_request(endpoint)
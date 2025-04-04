import requests
import pandas as pd
import json
import os
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox


class FootballDataAPI:
    """Classe pour gérer les appels à l'API football-data.org"""

    def __init__(self, api_key, cache_dir='cache'):
        """Initialisation de la classe avec la clé API"""
        self.api_key = api_key
        self.base_url = "https://api.football-data.org/v4"
        self.headers = {"X-Auth-Token": self.api_key}
        self.cache_dir = cache_dir

        # Création du dossier cache s'il n'existe pas
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def get_competitions(self):
        """Récupère la liste des compétitions disponibles"""
        endpoint = "/competitions"
        data = self._make_request(endpoint)
        return data.get('competitions', [])

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

    def _make_request(self, endpoint, params=None):
        """Effectue une requête à l'API avec gestion du cache"""
        cache_file = self._get_cache_filename(endpoint, params)

        # Vérifier si les données sont en cache et récentes (moins d'une heure)
        if os.path.exists(cache_file):
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age < 3600:  # 1 heure
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)

        # Si pas de cache valide, faire la requête
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            # Sauvegarder dans le cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)

            return data
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la requête API: {e}")
            if os.path.exists(cache_file):
                print("Utilisation des données en cache (potentiellement obsolètes)")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {"error": str(e)}

    def _get_cache_filename(self, endpoint, params=None):
        """Génère un nom de fichier pour le cache basé sur l'endpoint et les paramètres"""
        # Nettoyer l'endpoint pour l'utiliser dans un nom de fichier
        clean_endpoint = endpoint.replace('/', '_')

        # Ajouter les paramètres au nom du fichier s'ils existent
        param_str = ""
        if params:
            param_str = "_" + "_".join(f"{k}-{v}" for k, v in params.items())

        return os.path.join(self.cache_dir, f"{clean_endpoint}{param_str}.json")


class FootballDataApp:
    """Application pour visualiser les données de football"""

    def __init__(self, api_key):
        self.api = FootballDataAPI(api_key)
        self.competitions = []
        self.selected_competition = None

        # Créer l'interface utilisateur
        self.root = tk.Tk()
        self.root.title("Analyse des Événements Sportifs")
        self.root.geometry("800x600")

        self.create_widgets()
        self.load_competitions()

    def create_widgets(self):
        """Crée les widgets de l'interface utilisateur"""
        # Frame pour le menu principal
        menu_frame = ttk.Frame(self.root, padding=10)
        menu_frame.pack(fill=tk.X)

        # Sélection de compétition
        ttk.Label(menu_frame, text="Compétition:").pack(side=tk.LEFT)
        self.competition_var = tk.StringVar()
        self.competition_combo = ttk.Combobox(menu_frame, textvariable=self.competition_var, width=30)
        self.competition_combo.pack(side=tk.LEFT, padx=5)
        self.competition_combo.bind("<<ComboboxSelected>>", self.on_competition_selected)

        # Boutons pour les différentes fonctionnalités
        ttk.Button(menu_frame, text="Classement", command=self.show_standings).pack(side=tk.LEFT, padx=5)
        ttk.Button(menu_frame, text="Matchs", command=self.show_matches).pack(side=tk.LEFT, padx=5)
        ttk.Button(menu_frame, text="Buteurs", command=self.show_scorers).pack(side=tk.LEFT, padx=5)

        # Frame pour le contenu
        self.content_frame = ttk.Frame(self.root, padding=10)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Message initial
        ttk.Label(self.content_frame, text="Sélectionnez une compétition pour commencer").pack(pady=50)

    def load_competitions(self):
        """Charge la liste des compétitions disponibles"""
        try:
            self.competitions = self.api.get_competitions()
            competition_names = [f"{c['name']} ({c['code']})" for c in self.competitions]
            self.competition_combo['values'] = competition_names
            if competition_names:
                self.competition_combo.current(0)
                self.on_competition_selected(None)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les compétitions: {e}")

    def on_competition_selected(self, event):
        """Gère la sélection d'une compétition"""
        selected_index = self.competition_combo.current()
        if selected_index >= 0:
            self.selected_competition = self.competitions[selected_index]
            print(f"Compétition sélectionnée: {self.selected_competition['name']}")

    def clear_content(self):
        """Efface le contenu de la frame principale"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_standings(self):
        """Affiche le classement de la compétition sélectionnée"""
        if not self.selected_competition:
            messagebox.showinfo("Information", "Veuillez d'abord sélectionner une compétition")
            return

        self.clear_content()
        ttk.Label(self.content_frame, text=f"Classement - {self.selected_competition['name']}",
                  font=("Arial", 14, "bold")).pack(pady=10)

        try:
            standings_data = self.api.get_competition_standings(self.selected_competition['code'])
            if 'standings' in standings_data:
                for standing_type in standings_data['standings']:
                    ttk.Label(self.content_frame, text=standing_type.get('group', 'Classement général'),
                              font=("Arial", 12)).pack(pady=5)

                    # Créer le tableau
                    columns = ('position', 'team', 'played', 'won', 'draw', 'lost', 'points', 'gd')
                    tree = ttk.Treeview(self.content_frame, columns=columns, show='headings')

                    # Définir les en-têtes
                    tree.heading('position', text='Pos')
                    tree.heading('team', text='Équipe')
                    tree.heading('played', text='J')
                    tree.heading('won', text='G')
                    tree.heading('draw', text='N')
                    tree.heading('lost', text='P')
                    tree.heading('points', text='Pts')
                    tree.heading('gd', text='+/-')

                    # Ajuster les largeurs de colonnes
                    tree.column('position', width=40)
                    tree.column('team', width=200)
                    tree.column('played', width=40)
                    tree.column('won', width=40)
                    tree.column('draw', width=40)
                    tree.column('lost', width=40)
                    tree.column('points', width=40)
                    tree.column('gd', width=40)

                    # Ajouter les données
                    for team in standing_type['table']:
                        tree.insert('', tk.END, values=(
                            team['position'],
                            team['team']['name'],
                            team['playedGames'],
                            team['won'],
                            team['draw'],
                            team['lost'],
                            team['points'],
                            team['goalDifference']
                        ))

                    tree.pack(pady=5, fill=tk.X)
            else:
                ttk.Label(self.content_frame, text="Aucun classement disponible").pack()
        except Exception as e:
            ttk.Label(self.content_frame, text=f"Erreur: {e}").pack()

    def show_matches(self):
        """Affiche les matchs de la compétition sélectionnée"""
        if not self.selected_competition:
            messagebox.showinfo("Information", "Veuillez d'abord sélectionner une compétition")
            return

        self.clear_content()
        ttk.Label(self.content_frame, text=f"Matchs - {self.selected_competition['name']}",
                  font=("Arial", 14, "bold")).pack(pady=10)

        # Frame pour la sélection de journée
        filter_frame = ttk.Frame(self.content_frame)
        filter_frame.pack(fill=tk.X, pady=5)

        ttk.Label(filter_frame, text="Journée:").pack(side=tk.LEFT)
        matchday_var = tk.StringVar()
        matchday_combo = ttk.Combobox(filter_frame, textvariable=matchday_var, width=10)
        matchday_combo['values'] = list(range(1, 39))  # La plupart des ligues ont entre 1 et 38 journées
        matchday_combo.current(0)
        matchday_combo.pack(side=tk.LEFT, padx=5)

        # Tableau des matchs
        columns = ('date', 'status', 'home', 'score', 'away')
        matches_tree = ttk.Treeview(self.content_frame, columns=columns, show='headings')

        matches_tree.heading('date', text='Date')
        matches_tree.heading('status', text='Statut')
        matches_tree.heading('home', text='Domicile')
        matches_tree.heading('score', text='Score')
        matches_tree.heading('away', text='Extérieur')

        matches_tree.column('date', width=100)
        matches_tree.column('status', width=80)
        matches_tree.column('home', width=200)
        matches_tree.column('score', width=80)
        matches_tree.column('away', width=200)

        matches_tree.pack(pady=5, fill=tk.BOTH, expand=True)

        # Fonction pour charger les matchs
        def load_matches():
            # Effacer le tableau
            for item in matches_tree.get_children():
                matches_tree.delete(item)

            try:
                matchday = int(matchday_var.get())
                matches_data = self.api.get_competition_matches(self.selected_competition['code'], matchday)

                if 'matches' in matches_data:
                    for match in matches_data['matches']:
                        # Formater la date
                        match_date = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
                        date_str = match_date.strftime('%d/%m/%Y %H:%M')

                        # Formater le score
                        if match['status'] == 'FINISHED':
                            score = f"{match['score']['fullTime']['home']} - {match['score']['fullTime']['away']}"
                        else:
                            score = "vs"

                        matches_tree.insert('', tk.END, values=(
                            date_str,
                            match['status'],
                            match['homeTeam']['name'],
                            score,
                            match['awayTeam']['name']
                        ))
                else:
                    messagebox.showinfo("Information", "Aucun match disponible pour cette journée")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de charger les matchs: {e}")

        # Bouton pour charger les matchs
        ttk.Button(filter_frame, text="Charger", command=load_matches).pack(side=tk.LEFT, padx=5)

        # Charger la première journée par défaut
        load_matches()

    def show_scorers(self):
        """Affiche les meilleurs buteurs de la compétition sélectionnée"""
        if not self.selected_competition:
            messagebox.showinfo("Information", "Veuillez d'abord sélectionner une compétition")
            return

        self.clear_content()
        ttk.Label(self.content_frame, text=f"Meilleurs buteurs - {self.selected_competition['name']}",
                  font=("Arial", 14, "bold")).pack(pady=10)

        try:
            scorers_data = self.api.get_competition_scorers(self.selected_competition['code'])

            if 'scorers' in scorers_data and scorers_data['scorers']:
                # Créer le tableau
                columns = ('rank', 'player', 'team', 'goals', 'assists')
                tree = ttk.Treeview(self.content_frame, columns=columns, show='headings')

                tree.heading('rank', text='#')
                tree.heading('player', text='Joueur')
                tree.heading('team', text='Équipe')
                tree.heading('goals', text='Buts')
                tree.heading('assists', text='Passes D.')

                tree.column('rank', width=40)
                tree.column('player', width=200)
                tree.column('team', width=200)
                tree.column('goals', width=60)
                tree.column('assists', width=80)

                # Ajouter les données
                for i, scorer in enumerate(scorers_data['scorers'], 1):
                    tree.insert('', tk.END, values=(
                        i,
                        scorer['player']['name'],
                        scorer['team']['name'],
                        scorer['goals'],
                        scorer.get('assists', 'N/A')
                    ))

                tree.pack(pady=5, fill=tk.BOTH, expand=True)
            else:
                ttk.Label(self.content_frame, text="Aucune donnée de buteurs disponible").pack()
        except Exception as e:
            ttk.Label(self.content_frame, text=f"Erreur: {e}").pack()

    def run(self):
        """Lance l'application"""
        self.root.mainloop()


if __name__ == "__main__":
    # Votre clé API
    API_KEY = "7057bc93ed864b648356d2d588443800"

    # Lancer l'application
    app = FootballDataApp(API_KEY)
    app.run()
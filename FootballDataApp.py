from FootballDataAPi import *

class FootballDataApp:


    def __init__(self, api_key):
        self.api = FootballDataAPI(api_key)
        self.competitions = []
        self.selected_competition = None
        self._logo_photo_cache = {}
        self._tree_logo_refs = {}


        self.root = tk.Tk()
        self.root.title("Analyse des Événements Sportifs")
        self.root.geometry("1000x700")


        style = ttk.Style()
        style.theme_use('clam')

        self.current_standings_tree = None # Référence au Treeview du classement actuel
        self.current_scorers_tree = None # Référence au Treeview des buteurs actuel

        self.create_widgets()
        self.load_competitions()

    def create_widgets(self):
        """Crée les widgets de l'interface utilisateur"""
        # Frame pour le menu principal
        menu_frame = ttk.Frame(self.root, padding=10)
        menu_frame.pack(fill=tk.X)

        # Frame pour les boutons principaux
        main_buttons_frame = ttk.Frame(menu_frame)
        main_buttons_frame.pack(fill=tk.X)

        # Sélection de compétition
        ttk.Label(main_buttons_frame, text="Compétition:").pack(side=tk.LEFT)
        self.competition_var = tk.StringVar()
        self.competition_combo = ttk.Combobox(main_buttons_frame, textvariable=self.competition_var, width=40, state='readonly')
        self.competition_combo.pack(side=tk.LEFT, padx=5)
        self.competition_combo.bind("<<ComboboxSelected>>", self.on_competition_selected)

        # Boutons pour les différentes fonctionnalités
        self.standings_button = ttk.Button(main_buttons_frame, text="Classement", command=self.show_standings, state=tk.DISABLED)
        self.standings_button.pack(side=tk.LEFT, padx=5)
        self.matches_button = ttk.Button(main_buttons_frame, text="Matchs", command=self.show_matches, state=tk.DISABLED)
        self.matches_button.pack(side=tk.LEFT, padx=5)
        self.scorers_button = ttk.Button(main_buttons_frame, text="Buteurs", command=self.show_scorers, state=tk.DISABLED)
        self.scorers_button.pack(side=tk.LEFT, padx=5)
        self.today_matches_button = ttk.Button(main_buttons_frame, text="Matchs de la semaine", command=self.show_today_matches)
        self.today_matches_button.pack(side=tk.LEFT, padx=5)

        # Frame pour les boutons de statistiques
        stats_buttons_frame = ttk.Frame(menu_frame)
        stats_buttons_frame.pack(fill=tk.X, pady=(5, 0))

        # Label pour la section statistiques
        ttk.Label(stats_buttons_frame, text="Statistiques:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 10))

        # Boutons pour les statistiques
        self.comp_stats_button = ttk.Button(stats_buttons_frame, text="Stats Compétition", 
                                          command=self.show_competition_statistics, state=tk.DISABLED)
        self.comp_stats_button.pack(side=tk.LEFT, padx=5)
        
        self.player_stats_button = ttk.Button(stats_buttons_frame, text="Stats Joueurs", 
                                            command=self.show_player_statistics, state=tk.DISABLED)
        self.player_stats_button.pack(side=tk.LEFT, padx=5)

        # Bouton pour la Golden Boot
        self.golden_boot_button = ttk.Button(stats_buttons_frame, text="Golden Boot", 
                                           command=self.show_golden_boot)
        self.golden_boot_button.pack(side=tk.LEFT, padx=5)

        # Frame pour le contenu
        self.content_frame = ttk.Frame(self.root, padding=10)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Message initial
        self.initial_message_label = ttk.Label(self.content_frame, text="Chargement des compétitions...", font=("Arial", 12))
        self.initial_message_label.pack(pady=50)

    def load_competitions(self):
        """Charge la liste des compétitions disponibles"""
        def _load():
            competitions_data = self.api.get_competitions()

            # Planifier la mise à jour de l'UI dans le thread principal
            self.root.after(0, self._update_competitions_ui, competitions_data)

        # Lancer dans un thread pour ne pas bloquer l'UI au démarrage
        threading.Thread(target=_load, daemon=True).start()

    def _update_competitions_ui(self, competitions_data):
        """Met à jour l'UI avec les compétitions chargées (appelé via root after)"""
        self.initial_message_label.destroy() # Enlever le message de chargement

        if isinstance(competitions_data, dict) and 'error' in competitions_data:
            messagebox.showerror("Erreur", f"Impossible de charger les compétitions: {competitions_data['error']}")
            ttk.Label(self.content_frame, text=f"Erreur chargement compétitions: {competitions_data['error']}").pack(pady=50)
            return

        self.competitions = competitions_data
        competition_names = [f"{c['name']} ({c['code']})" for c in self.competitions if c.get('name') and c.get('code')]
        self.competition_combo['values'] = competition_names

        if competition_names:
            self.competition_combo.current(0)
            self.competition_combo.config(state='readonly')
            self.on_competition_selected(None) # Charger la première compétition
            # Activer les boutons
            self.standings_button.config(state=tk.NORMAL)
            self.matches_button.config(state=tk.NORMAL)
            self.scorers_button.config(state=tk.NORMAL)
            self.comp_stats_button.config(state=tk.NORMAL)
            self.player_stats_button.config(state=tk.NORMAL)
            # Afficher les matchs du jour par défaut
            self.show_today_matches()
        else:
             self.competition_combo.config(state=tk.DISABLED)
             ttk.Label(self.content_frame, text="Aucune compétition disponible ou erreur de chargement.").pack(pady=50)


    def on_competition_selected(self, event):
        """Gère la sélection d'une compétition"""
        selected_index = self.competition_combo.current()
        if selected_index >= 0 and self.competitions:
            self.selected_competition = self.competitions[selected_index]
            print(f"Compétition sélectionnée: {self.selected_competition.get('name', 'N/A')}")

        else:
             self.selected_competition = None
             # Désactiver les boutons si aucune compétition n'est valide/sélectionnée
             self.standings_button.config(state=tk.DISABLED)
             self.matches_button.config(state=tk.DISABLED)
             self.scorers_button.config(state=tk.DISABLED)
             self.comp_stats_button.config(state=tk.DISABLED)
             self.player_stats_button.config(state=tk.DISABLED)


    def clear_content(self):
        """Efface le contenu de la frame principale"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.current_standings_tree = None
        self.current_scorers_tree = None
        self._tree_logo_refs.clear() # Nettoyer les références de logo

    def load_team_logo(self, team_id, logo_url, size=(30, 30)):
        """Charge le logo d'une équipe et renvoie un objet PhotoImage redimensionné"""
        cache_key = (team_id, size) # Clé de cache incluant la taille
        if cache_key in self._logo_photo_cache:
            return self._logo_photo_cache[cache_key]

        try:

            image_pil = self.api.get_team_logo(team_id, logo_url)
            if image_pil:
                # Redimensionner l'image
                image_pil_resized = image_pil.resize(size, Image.Resampling.LANCZOS)
                # Convertir en PhotoImage pour Tkinter
                photo = ImageTk.PhotoImage(image_pil_resized)
                # Mettre en cache l'objet PhotoImage
                self._logo_photo_cache[cache_key] = photo
                return photo
        except Exception as e:
            print(f"Erreur de chargement/redimensionnement du logo pour l'équipe {team_id}: {e}")

        return None # Retourner None en cas d'échec


    def show_standings(self):
        """Affiche le classement de la compétition sélectionnée avec les logos et permet de voir les matchs d'une équipe"""
        if not self.selected_competition:
            messagebox.showinfo("Information", "Veuillez d'abord sélectionner une compétition")
            return

        self.clear_content()
        comp_name = self.selected_competition.get('name', 'N/A')
        ttk.Label(self.content_frame, text=f"Classement - {comp_name}",
                  font=("Arial", 14, "bold")).pack(pady=10)

        # Indicateur de chargement
        loading_label = ttk.Label(self.content_frame, text="Chargement des données...")
        loading_label.pack(pady=20)
        self.root.update() # Afficher le label de chargement

        # Fonction pour charger les données en arrière-plan
        def _load_data():
            standings_data = self.api.get_competition_standings(self.selected_competition['code'])
            # Planifier la mise à jour de l'UI dans le thread principal
            self.root.after(0, self._display_standings, standings_data, loading_label)

        # Lancer le chargement dans un thread
        threading.Thread(target=_load_data, daemon=True).start()

    def _display_standings(self, standings_data, loading_label):
        """Met à jour l'UI avec les données du classement (appelé via root after)."""
        if loading_label.winfo_exists():
            loading_label.destroy()

        # Vérification de l'erreur API
        if isinstance(standings_data, dict) and 'error' in standings_data:
            messagebox.showerror("Erreur API", f"Impossible de charger le classement : {standings_data['error']}")
            ttk.Label(self.content_frame, text=f"Erreur chargement classement: {standings_data['error']}").pack()
            return

        if 'standings' in standings_data and standings_data['standings']:
            for standing_type in standings_data['standings']:
                group_name = standing_type.get('group', 'Classement général')
                if group_name: # Ne pas afficher si le groupe est None ou vide
                    ttk.Label(self.content_frame, text=group_name, font=("Arial", 12)).pack(pady=5)

                # Frame pour contenir le tableau et la scrollbar
                table_frame = ttk.Frame(self.content_frame)
                table_frame.pack(fill=tk.BOTH, expand=True, pady=5)

                # Créer le tableau avec scrollbar
                columns = ('logo', 'position', 'team', 'played', 'won', 'draw', 'lost', 'points', 'gd')
                tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15) # Hauteur ajustée
                self.current_standings_tree = tree # Garder la référence

                # Ajouter scrollbar
                vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
                vsb.pack(side='right', fill='y')
                tree.configure(yscrollcommand=vsb.set)

                # Définir les en-têtes et largeurs
                tree.heading('logo', text='')
                tree.column('logo', width=40, anchor='center', stretch=False)
                tree.heading('position', text='Pos')
                tree.column('position', width=40, anchor='center', stretch=False)
                tree.heading('team', text='Équipe')
                tree.column('team', width=250) # Un peu plus large
                tree.heading('played', text='J')
                tree.column('played', width=40, anchor='center', stretch=False)
                tree.heading('won', text='G')
                tree.column('won', width=40, anchor='center', stretch=False)
                tree.heading('draw', text='N')
                tree.column('draw', width=40, anchor='center', stretch=False)
                tree.heading('lost', text='P')
                tree.column('lost', width=40, anchor='center', stretch=False)
                tree.heading('points', text='Pts')
                tree.column('points', width=50, anchor='center', stretch=False)
                tree.heading('gd', text='+/-')
                tree.column('gd', width=50, anchor='center', stretch=False)

                tree.pack(side='left', fill='both', expand=True)

                # Ajouter les données (sans logo initialement) et lancer le chargement des logos
                if 'table' in standing_type:
                    for team_data in standing_type['table']:
                        team_id = team_data.get('team', {}).get('id')
                        team_name = team_data.get('team', {}).get('name', 'N/A')
                        logo_url = team_data.get('team', {}).get('crest')

                        if team_id is None: continue # Ignorer si l'ID de l'équipe manque

                        # Insérer la ligne sans logo
                        item_id = tree.insert('', tk.END, values=(
                            '',  # Placeholder logo
                            team_data.get('position', ''),
                            team_name,
                            team_data.get('playedGames', ''),
                            team_data.get('won', ''),
                            team_data.get('draw', ''),
                            team_data.get('lost', ''),
                            team_data.get('points', ''),
                            team_data.get('goalDifference', '')
                        ), tags=(str(team_id),)) # Utiliser l'ID comme tag

                        # Lancer le chargement du logo en arrière-plan
                        if logo_url:
                            threading.Thread(
                                target=self._fetch_and_schedule_logo_update,
                                args=(tree, item_id, team_id, logo_url),
                                daemon=True
                            ).start()

                    # Ajouter l'événement de double-clic APRÈS avoir ajouté les éléments
                    # Le lambda capture la variable 'tree' de cette itération de la boucle externe
                    tree.bind("<Double-1>", lambda event, current_tree=tree: self.on_team_double_click(current_tree))
                else:
                     ttk.Label(table_frame, text="Données de classement non disponibles pour ce groupe.").pack()

        else:
            ttk.Label(self.content_frame, text="Aucun classement disponible pour cette compétition.").pack()


    def _fetch_and_schedule_logo_update(self, tree, item_id, team_id, logo_url):
        """Charge le logo dans un thread et planifie la mise à jour de l'UI."""
        try:
            # Cette partie (réseau/disque/redimensionnement) est OK dans un thread
            logo_photo = self.load_team_logo(team_id, logo_url, size=(30, 30))

            if logo_photo:

                self.root.after(0, self._update_treeview_item_logo, tree, item_id, logo_photo)
        except Exception as e:
            print(f"Erreur chargement/planification logo pour {team_id} (item {item_id}): {e}")

    def _update_treeview_item_logo(self, tree, item_id, logo_photo):
        """Met à jour l'image d'un item dans le Treeview (appelé via root after)."""
        try:
            # Vérifier si le treeview et l'item existent toujours
            if tree.winfo_exists() and tree.exists(item_id):
                # Stocker la référence pour éviter le garbage collector
                # Utiliser une clé unique combinant l'id du widget et l'item_id
                ref_key = (id(tree), item_id)
                self._tree_logo_refs[ref_key] = logo_photo # Stocke la référence

                tree.item(item_id, image=logo_photo)
        except tk.TclError as e:

             pass # Ignorer silencieusement est souvent acceptable ici
        except Exception as e:
            print(f"Erreur mise à jour logo pour item {item_id} dans Treeview: {e}")
        finally:

             pass

    # --- NOUVELLE MÉTHODE POUR GÉRER LE CLIC ---
    def on_team_double_click(self, tree):
         """Appelé lors d'un double-clic sur une ligne du classement."""
         self.show_team_matches(tree) # Appelle la fonction d'affichage des matchs

    # --- NOUVELLE MÉTHODE ---
    def show_team_matches(self, tree):
        """Affiche les matchs d'une équipe sélectionnée dans le classement"""
        # Récupérer l'équipe sélectionnée
        selected_item = tree.selection()
        if not selected_item:
            return  # Rien n'est sélectionné

        item_id = selected_item[0] # Un seul item est sélectionné sur double-clic

        # Vérifier si l'item existe toujours (par précaution)
        if not tree.exists(item_id):
             print("L'item sélectionné n'existe plus.")
             return

        # Récupérer l'ID de l'équipe depuis les tags et le nom depuis les valeurs
        try:
            tags = tree.item(item_id, "tags")
            values = tree.item(item_id, "values")
            if not tags:
                 print("Aucun tag trouvé pour l'item sélectionné.")
                 return

            team_id = tags[0] # Le premier tag est l'ID
            team_name = values[2] if len(values) > 2 else "Équipe Inconnue" # Le nom est à l'index2

        except (IndexError, TypeError) as e:
            print(f"Erreur lors de la récupération des infos de l'équipe : {e}")
            messagebox.showerror("Erreur", "Impossible de récupérer les informations de l'équipe sélectionnée.")
            return

        print(f"Affichage des matchs pour l'équipe ID: {team_id}, Nom: {team_name}")

        # Créer une nouvelle fenêtre Toplevel
        team_window = tk.Toplevel(self.root)
        team_window.title(f"Matchs de {team_name}")
        team_window.geometry("900x600")
        # Rendre la fenêtre modale (optionnel, bloque l'interaction avec la fenêtre principale)
        # team_window.grab_set()
        team_window.transient(self.root) # Liée à la fenêtre principale

        # Indicateur de chargement
        loading_frame = ttk.Frame(team_window)
        loading_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(loading_frame, text="Chargement des matchs...").pack(pady=50)
        team_window.update()

        # Fonction pour charger les données en arrière-plan
        def _load_data():
            matches_data = self.api.get_team_matches(team_id)
            # Planifier la mise à jour de l'UI dans le thread principal
            self.root.after(0, self._display_team_matches, team_window, loading_frame, matches_data, team_id, team_name)

        # Lancer le chargement dans un thread
        threading.Thread(target=_load_data, daemon=True).start()

    def _display_team_matches(self, team_window, loading_frame, matches_data, team_id, team_name):
        """Met à jour l'UI de la fenêtre Toplevel avec les matchs (appelé via root after)"""
        if not team_window.winfo_exists(): # Vérifier si la fenêtre existe toujours
            return
        if loading_frame.winfo_exists():
            loading_frame.destroy()

        # Vérification de l'erreur API
        if isinstance(matches_data, dict) and 'error' in matches_data:
            messagebox.showerror("Erreur API", f"Impossible de charger les matchs pour {team_name}: {matches_data['error']}", parent=team_window)
            ttk.Label(team_window, text=f"Erreur chargement matchs: {matches_data['error']}").pack(pady=20)
            return
        elif 'matches' not in matches_data:
             messagebox.showerror("Erreur Données", f"Format de réponse inattendu pour les matchs de {team_name}.", parent=team_window)
             ttk.Label(team_window, text="Format de réponse inattendu.").pack(pady=20)
             return

        all_matches = matches_data.get('matches', [])
        # Trier les matchs par date (le plus récent en premier pour 'Passés', le plus proche en premier pour 'À venir')
        all_matches.sort(key=lambda m: m.get('utcDate', ''), reverse=True)

        finished_matches = [m for m in all_matches if m.get('status') == 'FINISHED']
        scheduled_matches = [m for m in all_matches if m.get('status') in ['SCHEDULED', 'TIMED', 'IN_PLAY', 'PAUSED']] # Inclure en cours/pause
        scheduled_matches.sort(key=lambda m: m.get('utcDate', '')) # Trier les futurs par date croissante


        # Création des onglets
        notebook = ttk.Notebook(team_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Créer les onglets
        tabs = {
            "Tous": self.create_matches_tab(notebook, all_matches, str(team_id)), # S'assurer que team_id est une chaîne pour la comparaison
            "Passés": self.create_matches_tab(notebook, finished_matches, str(team_id)),
            "À venir / En cours": self.create_matches_tab(notebook, scheduled_matches, str(team_id))
        }

        # Ajouter les onglets au notebook
        for tab_name, tab_frame in tabs.items():
             if tab_frame: # S'assurer que le frame a été créé
                 notebook.add(tab_frame, text=f"{tab_name} ({len(tab_frame.winfo_children())})") # Afficher le nombre de matchs dans le titre de l'onglet


    def create_matches_tab(self, parent, matches, team_id):
        """Crée un onglet avec une liste de matchs pour une équipe avec une meilleure structure d'affichage"""
        tab = ttk.Frame(parent)

        if not matches:
            ttk.Label(tab, text="Aucun match disponible").pack(pady=20)
            return tab

        # Créer un canvas avec scrollbar pour les matchs
        canvas_frame = ttk.Frame(tab)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Dictionnaire des couleurs pour les compétitions
        competition_colors = {
            'Premier League': '#37003c',  # Violet foncé
            'La Liga': '#ff0000',         # Rouge
            'Bundesliga': '#d71e28',      # Rouge foncé
            'Serie A': '#0c1b33',         # Bleu marine
            'Ligue 1': '#0d0d0d',         # Noir
            'Eredivisie': '#ff6b00',      # Orange
            'Primeira Liga': '#006437',   # Vert foncé
            'Championship': '#1d428a',    # Bleu
            'Europa League': '#ffd700',    # Or
            'Champions League': '#1a1a1a'  # Noir
        }

        # Parcourir les matchs
        for match in matches:
            # Créer un cadre pour chaque match avec un style moderne
            match_frame = ttk.Frame(scrollable_frame, style='Match.TFrame')
            match_frame.pack(fill=tk.X, pady=5, padx=10)

            # Configurer le style pour le cadre du match
            style = ttk.Style()
            style.configure('Match.TFrame', background='#f0f0f0', relief='solid', borderwidth=1)

            # Associer un événement de clic au cadre du match
            match_frame.bind("<Button-1>", lambda event, match_id=match['id']: self.show_match_statistics(match_id))
            match_frame.bind("<Enter>", lambda e, frame=match_frame: frame.configure(style='MatchHover.TFrame'))
            match_frame.bind("<Leave>", lambda e, frame=match_frame: frame.configure(style='Match.TFrame'))

            # Date et compétition
            match_date = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
            date_str = match_date.strftime('%d/%m/%Y %H:%M')
            competition_name = match['competition']['name']

            header_frame = ttk.Frame(match_frame)
            header_frame.pack(fill=tk.X, pady=5)

            # Style pour la date et la compétition
            date_label = ttk.Label(header_frame, text=date_str, font=("Arial", 9))
            date_label.pack(side=tk.LEFT, padx=10)

            # Appliquer la couleur de la compétition
            comp_color = competition_colors.get(competition_name, '#000000')
            comp_label = ttk.Label(header_frame, text=competition_name, 
                                 font=("Arial", 9, "bold"),
                                 foreground=comp_color)
            comp_label.pack(side=tk.RIGHT, padx=10)

            # Statut du match avec couleur appropriée
            status_colors = {
                'FINISHED': '#28a745',    # Vert
                'SCHEDULED': '#007bff',   # Bleu
                'IN_PLAY': '#ffc107',     # Jaune
                'PAUSED': '#ffc107',      # Jaune
                'POSTPONED': '#dc3545',   # Rouge
                'CANCELLED': '#dc3545'    # Rouge
            }
            status = match['status']
            status_color = status_colors.get(status, '#6c757d')  # Gris par défaut
            status_label = ttk.Label(header_frame, text=status,
                                   foreground=status_color,
                                   font=("Arial", 9, "bold"))
            status_label.pack(side=tk.RIGHT, padx=5)

            # Structure principale pour les équipes et le score
            teams_score_frame = ttk.Frame(match_frame)
            teams_score_frame.pack(fill=tk.X, pady=10, padx=5)

            # Configurer les colonnes pour avoir un alignement centré
            teams_score_frame.columnconfigure(0, weight=1)  # Équipe domicile
            teams_score_frame.columnconfigure(1, weight=1)  # Logo domicile
            teams_score_frame.columnconfigure(2, weight=1)  # Score
            teams_score_frame.columnconfigure(3, weight=1)  # Logo extérieur
            teams_score_frame.columnconfigure(4, weight=1)  # Équipe extérieure

            # Récupérer les données des équipes
            home_id = match['homeTeam']['id']
            home_name = match['homeTeam']['name']
            home_logo_url = match['homeTeam'].get('crest')

            away_id = match['awayTeam']['id']
            away_name = match['awayTeam']['name']
            away_logo_url = match['awayTeam'].get('crest')

            # Charger les logos avec une taille uniforme
            logo_size = (40, 40)
            home_logo = self.load_team_logo(home_id, home_logo_url, size=logo_size)
            away_logo = self.load_team_logo(away_id, away_logo_url, size=logo_size)

            # Créer des frames pour chaque colonne
            home_team_frame = ttk.Frame(teams_score_frame)
            home_team_frame.grid(row=0, column=0, sticky="e", padx=5)
            
            home_logo_frame = ttk.Frame(teams_score_frame)
            home_logo_frame.grid(row=0, column=1, sticky="e", padx=5)
            
            score_frame = ttk.Frame(teams_score_frame)
            score_frame.grid(row=0, column=2, sticky="nsew", padx=10)
            
            away_logo_frame = ttk.Frame(teams_score_frame)
            away_logo_frame.grid(row=0, column=3, sticky="w", padx=5)
            
            away_team_frame = ttk.Frame(teams_score_frame)
            away_team_frame.grid(row=0, column=4, sticky="w", padx=5)

            # Nom de l'équipe domicile
            home_style = "bold" if str(home_id) == str(team_id) else "normal"
            home_color = "blue" if str(home_id) == str(team_id) else "black"
            home_label = ttk.Label(home_team_frame, text=home_name,
                                 font=("Arial", 10, home_style),
                                 foreground=home_color)
            home_label.pack(side=tk.RIGHT)

            # Logo équipe domicile
            if home_logo:
                home_logo_label = ttk.Label(home_logo_frame, image=home_logo)
                home_logo_label.image = home_logo
                home_logo_label.pack(side=tk.RIGHT)

            # Score au centre
            if match['status'] == 'FINISHED':
                score_text = f"{match['score']['fullTime']['home']} - {match['score']['fullTime']['away']}"
                score_color = '#28a745'  # Vert pour les matchs terminés
            else:
                score_text = "vs"
                score_color = '#6c757d'  # Gris pour les matchs à venir

            score_label = ttk.Label(score_frame, text=score_text,
                                  font=("Arial", 12, "bold"),
                                  foreground=score_color)
            score_label.pack(expand=True)

            # Logo équipe extérieure
            if away_logo:
                away_logo_label = ttk.Label(away_logo_frame, image=away_logo)
                away_logo_label.image = away_logo
                away_logo_label.pack(side=tk.LEFT)

            # Nom de l'équipe extérieure
            away_style = "bold" if str(away_id) == str(team_id) else "normal"
            away_color = "blue" if str(away_id) == str(team_id) else "black"
            away_label = ttk.Label(away_team_frame, text=away_name,
                                 font=("Arial", 10, away_style),
                                 foreground=away_color)
            away_label.pack(side=tk.LEFT)

            # Ajouter une étiquette pour indiquer que le clic affichera les statistiques
            if match['status'] == 'FINISHED':
                info_label = ttk.Label(match_frame, text="Cliquez pour voir les statistiques",
                                     font=("Arial", 8, "italic"),
                                     foreground="grey")
                info_label.pack(pady=(0, 5))

        return tab

    def show_matches(self):
        """Affiche les matchs de la compétition sélectionnée par journée"""
        if not self.selected_competition:
            messagebox.showinfo("Information", "Veuillez d'abord sélectionner une compétition")
            return

        self.clear_content()
        comp_name = self.selected_competition.get('name', 'N/A')
        ttk.Label(self.content_frame, text=f"Matchs - {comp_name}",
                  font=("Arial", 14, "bold")).pack(pady=10)


        filter_frame = ttk.Frame(self.content_frame)
        filter_frame.pack(fill=tk.X, pady=5)

        ttk.Label(filter_frame, text="Journée:").pack(side=tk.LEFT, padx=(0,5))

        max_matchdays = 38

        try:

             current_season = self.selected_competition.get('currentSeason')
             default_matchday = current_season.get('currentMatchday', 1) if current_season else 1
        except Exception:
             default_matchday = 1

        self.matchday_var = tk.StringVar(value=str(default_matchday))
        matchday_spinbox = ttk.Spinbox(filter_frame, from_=1, to=max_matchdays, textvariable=self.matchday_var, width=5, command=self._load_selected_matchday)

        matchday_spinbox.pack(side=tk.LEFT, padx=5)

        self.matches_display_frame = ttk.Frame(self.content_frame)
        self.matches_display_frame.pack(fill=tk.BOTH, expand=True, pady=10)


        self._load_selected_matchday()

    def _load_selected_matchday(self):
        """Charge et affiche les matchs pour la journée sélectionnée."""
        # Effacer le contenu précédent dans le frame des matchs
        for widget in self.matches_display_frame.winfo_children():
            widget.destroy()

        # Indicateur de chargement DANS le frame des matchs
        loading_label = ttk.Label(self.matches_display_frame, text="Chargement des matchs...")
        loading_label.pack(pady=20)
        self.root.update()

        try:
            matchday = int(self.matchday_var.get())
        except ValueError:
            messagebox.showerror("Erreur", "Journée invalide.", parent=self.root)
            if loading_label.winfo_exists(): loading_label.destroy()
            return

        # Fonction pour charger les données en arrière-plan
        def _load_data():
            matches_data = self.api.get_competition_matches(self.selected_competition['code'], matchday)
            # Planifier la mise à jour de l'UI
            self.root.after(0, self._display_matchday_matches, matches_data, loading_label, matchday)

        # Lancer le chargement
        threading.Thread(target=_load_data, daemon=True).start()


    def _display_matchday_matches(self, matches_data, loading_label, matchday):
        """Met à jour l'UI avec les matchs de la journée (appelé via root after)."""
        if not self.matches_display_frame.winfo_exists(): return # Vérifier si le frame parent existe
        if loading_label.winfo_exists():
            loading_label.destroy()

        # Vérifier erreur API
        if isinstance(matches_data, dict) and 'error' in matches_data:
            messagebox.showerror("Erreur API", f"Impossible de charger les matchs J{matchday}: {matches_data['error']}", parent=self.root)
            ttk.Label(self.matches_display_frame, text=f"Erreur chargement matchs J{matchday}: {matches_data['error']}").pack()
            return
        elif 'matches' not in matches_data:
            messagebox.showerror("Erreur Données", f"Format de réponse inattendu pour les matchs J{matchday}.", parent=self.root)
            ttk.Label(self.matches_display_frame, text="Format de réponse inattendu.").pack()
            return

        matches = matches_data.get('matches', [])
        matches.sort(key=lambda m: m.get('utcDate', '')) # Trier par date/heure

        if matches:

            matches_tab_content = self.create_matches_tab(self.matches_display_frame, matches, None)

            if matches_tab_content:
                 matches_tab_content.pack(fill=tk.BOTH, expand=True) # Packer le contenu créé
        else:
            ttk.Label(self.matches_display_frame, text=f"Aucun match trouvé pour la journée {matchday}.").pack(pady=20)


    def show_scorers(self):
        """Affiche les meilleurs buteurs avec correction threading"""
        if not self.selected_competition:
            messagebox.showinfo("Information", "Veuillez d'abord sélectionner une compétition")
            return

        self.clear_content()
        comp_name = self.selected_competition.get('name', 'N/A')
        ttk.Label(self.content_frame, text=f"Meilleurs buteurs - {comp_name}",
                  font=("Arial", 14, "bold")).pack(pady=10)

        # Indicateur de chargement
        loading_label = ttk.Label(self.content_frame, text="Chargement des données...")
        loading_label.pack(pady=20)
        self.root.update()

        # Fonction pour charger les données en arrière-plan
        def _load_data():
            scorers_data = self.api.get_competition_scorers(self.selected_competition['code'], limit=20) # Afficher top 20
            self.root.after(0, self._display_scorers, scorers_data, loading_label)

        threading.Thread(target=_load_data, daemon=True).start()

    def _display_scorers(self, scorers_data, loading_label):
        """Met à jour l'UI avec les buteurs (appelé via root after)."""
        if loading_label.winfo_exists():
            loading_label.destroy()

        if isinstance(scorers_data, dict) and 'error' in scorers_data:
            messagebox.showerror("Erreur API", f"Impossible de charger les buteurs : {scorers_data['error']}")
            ttk.Label(self.content_frame, text=f"Erreur chargement buteurs: {scorers_data['error']}").pack()
            return

        if 'scorers' in scorers_data and scorers_data['scorers']:
            # Frame pour contenir le tableau et la scrollbar
            table_frame = ttk.Frame(self.content_frame)
            table_frame.pack(fill=tk.BOTH, expand=True, pady=5)

            # Créer le tableau
            columns = ('rank', 'player', 'team_logo', 'team', 'goals', 'assists', 'penalties') # Ajout penalties
            tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
            self.current_scorers_tree = tree # Garder référence

            # Ajouter scrollbar
            vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
            vsb.pack(side='right', fill='y')
            tree.configure(yscrollcommand=vsb.set)

            tree.heading('rank', text='#')
            tree.column('rank', width=40, anchor='center', stretch=False)
            tree.heading('player', text='Joueur')
            tree.column('player', width=200)
            tree.heading('team_logo', text='')
            tree.column('team_logo', width=40, anchor='center', stretch=False)
            tree.heading('team', text='Équipe')
            tree.column('team', width=200)
            tree.heading('goals', text='Buts')
            tree.column('goals', width=60, anchor='center', stretch=False)
            tree.heading('assists', text='Passes D.')
            tree.column('assists', width=80, anchor='center', stretch=False)
            tree.heading('penalties', text='Pen.')
            tree.column('penalties', width=50, anchor='center', stretch=False)


            tree.pack(side='left', fill='both', expand=True)

            # Ajouter les données avec logos (chargement asynchrone)
            for i, scorer in enumerate(scorers_data['scorers'], 1):
                 player_info = scorer.get('player', {})
                 team_info = scorer.get('team', {})
                 team_id = team_info.get('id')
                 team_logo_url = team_info.get('crest')

                 if not team_id: continue # Nécessaire pour le chargement du logo

                 item_id = tree.insert('', tk.END, values=(
                    i,
                    player_info.get('name', 'N/A'),
                    '', # Placeholder logo
                    team_info.get('name', 'N/A'),
                    scorer.get('goals', 'N/A'),
                    scorer.get('assists', '-'), # Utiliser '-' si N/A
                    scorer.get('penalties', '-') # Utiliser '-' si N/A
                 ), tags=(str(team_id),))

                 # Lancer chargement logo
                 if team_logo_url:
                      threading.Thread(
                          target=self._fetch_and_schedule_logo_update,
                           args=(tree, item_id, team_id, team_logo_url),
                           daemon=True
                       ).start()
        else:
            ttk.Label(self.content_frame, text="Aucune donnée de buteurs disponible").pack()

    def show_match_statistics(self, match_id):
        """Affiche les statistiques d'un match dans une nouvelle fenêtre avec des graphiques"""
        # Récupérer les détails du match
        match_data = self.api.get_match_details(match_id)

        if not match_data or 'match' not in match_data:
            messagebox.showinfo("Information", "Aucune statistique disponible pour ce match")
            return

        match = match_data.get('match', {})

        # Vérifier si le match est terminé et s'il y a des statistiques
        if match.get('status') != 'FINISHED':
            messagebox.showinfo("Information", "Les statistiques ne sont disponibles que pour les matchs terminés")
            return

        # Créer une nouvelle fenêtre pour les statistiques
        stats_window = tk.Toplevel(self.root)
        stats_window.title(f"Statistiques: {match['homeTeam']['name']} vs {match['awayTeam']['name']}")
        stats_window.geometry("900x700")

        # Informations générales sur le match
        header_frame = ttk.Frame(stats_window, padding=10)
        header_frame.pack(fill=tk.X)

        # Date et compétition
        match_date = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
        date_str = match_date.strftime('%d/%m/%Y %H:%M')

        ttk.Label(header_frame, text=f"{match['competition']['name']} - {date_str}",
                  font=("Arial", 12, "bold")).pack(pady=5)

        # Score final
        score_frame = ttk.Frame(header_frame)
        score_frame.pack(pady=10)

        # Configurer les colonnes pour avoir un alignement centré
        score_frame.columnconfigure(0, weight=2)  # Équipe domicile
        score_frame.columnconfigure(1, weight=1)  # Logo domicile
        score_frame.columnconfigure(2, weight=1)  # Score
        score_frame.columnconfigure(3, weight=1)  # Logo extérieur
        score_frame.columnconfigure(4, weight=2)  # Équipe extérieure

        # Équipes et score
        home_team = match['homeTeam']
        away_team = match['awayTeam']

        # Charger les logos
        home_logo = self.load_team_logo(home_team['id'], home_team.get('crest'))
        away_logo = self.load_team_logo(away_team['id'], away_team.get('crest'))

        # Nom de l'équipe domicile
        ttk.Label(score_frame, text=home_team['name'], font=("Arial", 11, "bold")).grid(row=0, column=0, padx=10)

        # Logo équipe domicile
        if home_logo:
            home_logo_label = ttk.Label(score_frame, image=home_logo)
            home_logo_label.image = home_logo
            home_logo_label.grid(row=0, column=1, padx=5)

        # Score
        home_score = match['score']['fullTime']['home'] or 0
        away_score = match['score']['fullTime']['away'] or 0
        score_text = f"{home_score} - {away_score}"
        ttk.Label(score_frame, text=score_text, font=("Arial", 14, "bold")).grid(row=0, column=2, padx=20)

        # Logo équipe extérieure
        if away_logo:
            away_logo_label = ttk.Label(score_frame, image=away_logo)
            away_logo_label.image = away_logo
            away_logo_label.grid(row=0, column=3, padx=5)

        # Nom de l'équipe extérieure
        ttk.Label(score_frame, text=away_team['name'], font=("Arial", 11, "bold")).grid(row=0, column=4, padx=10)

        # Simuler des statistiques réalistes basées sur le score
        total_goals = home_score + away_score
        winning_team = 'home' if home_score > away_score else 'away' if away_score > home_score else None

        # Fonction pour simuler des statistiques réalistes
        def simulate_stats(base_value, winner_bonus=0, loser_penalty=0):
            if winning_team == 'home':
                return (base_value + winner_bonus, base_value - loser_penalty)
            elif winning_team == 'away':
                return (base_value - loser_penalty, base_value + winner_bonus)
            return (base_value, base_value)  # Match nul

        # Simuler des statistiques plus réalistes
        stats = {
            'Possession (%)': simulate_stats(50, 5, 5),
            'Tirs': (home_score * 3 + 8, away_score * 3 + 8),
            'Tirs cadrés': (home_score + 3, away_score + 3),
            'Corners': simulate_stats(6, 2, 1),
            'Fautes': simulate_stats(12, -2, 2),  # L'équipe qui gagne fait généralement moins de fautes
            'Cartons jaunes': (min(total_goals + 1, 3), min(total_goals + 1, 3)),
            'Cartons rouges': (1 if home_score < away_score and total_goals > 3 else 0,
                              1 if away_score < home_score and total_goals > 3 else 0),
            'Hors-jeu': simulate_stats(3, 1, 0),
            'Passes': simulate_stats(400, 50, 50),
            'Précision passes (%)': simulate_stats(80, 5, 5),
            'Duels gagnés': simulate_stats(52, 5, 5),
            'Distance parcourue (km)': simulate_stats(110, 2, 2),
        }

        # Créer un notebook pour organiser différentes visualisations
        notebook = ttk.Notebook(stats_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 1. Tableau de statistiques
        table_frame = ttk.Frame(notebook)
        notebook.add(table_frame, text="Statistiques")

        # Créer un tableau pour afficher les statistiques
        columns = ('stat', 'home', 'away')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=10)

        tree.heading('stat', text='Statistique')
        tree.heading('home', text=home_team['name'])
        tree.heading('away', text=away_team['name'])

        tree.column('stat', width=200)
        tree.column('home', width=100, anchor='center')
        tree.column('away', width=100, anchor='center')

        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Ajouter les données au tableau
        for stat_name, (home_value, away_value) in stats.items():
            tree.insert('', tk.END, values=(stat_name, home_value, away_value))

        # 2. Graphiques à barres horizontales
        bar_frame = ttk.Frame(notebook)
        notebook.add(bar_frame, text="Comparaison")

        # Créer la figure matplotlib
        fig_bar, ax_bar = plt.subplots(figsize=(8, 6))

        # Sélectionner quelques statistiques clés pour le graphique
        key_stats = ['Possession (%)', 'Tirs', 'Tirs cadrés', 'Corners', 'Duels gagnés']
        home_values = [stats[stat][0] for stat in key_stats]
        away_values = [stats[stat][1] for stat in key_stats]

        # Créer des positions pour les barres
        y_pos = np.arange(len(key_stats))
        bar_height = 0.35

        # Créer le graphique à barres horizontales
        ax_bar.barh(y_pos - bar_height / 2, home_values, bar_height, label=home_team['name'], color='blue', alpha=0.7)
        ax_bar.barh(y_pos + bar_height / 2, away_values, bar_height, label=away_team['name'], color='red', alpha=0.7)

        # Ajouter les étiquettes et la légende
        ax_bar.set_yticks(y_pos)
        ax_bar.set_yticklabels(key_stats)
        ax_bar.invert_yaxis()  # Les étiquettes apparaissent dans l'ordre de la liste
        ax_bar.set_xlabel('Valeurs')
        ax_bar.set_title('Statistiques clés du match')
        ax_bar.legend()

        # Ajouter la figure à l'interface Tkinter
        canvas_bar = FigureCanvasTkAgg(fig_bar, master=bar_frame)
        canvas_bar.draw()
        canvas_bar.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 3. Graphique radar pour une comparaison globale
        radar_frame = ttk.Frame(notebook)
        notebook.add(radar_frame, text="Radar")

        # Créer la figure matplotlib pour le graphique radar
        fig_radar = plt.figure(figsize=(8, 6))
        ax_radar = fig_radar.add_subplot(111, polar=True)

        # Sélectionner des statistiques pour le radar (convertir pour être sur la même échelle)
        radar_stats = [
            'Possession (%)',
            'Duels gagnés',
            'Précision passes (%)',
            'Tirs cadrés (normalisé)',
            'Distance parcourue (km)'
        ]

        # Normaliser les valeurs pour qu'elles soient sur la même échelle (0-100)
        max_shots = max(stats['Tirs cadrés'])
        max_distance = max(stats['Distance parcourue (km)'])

        radar_home = [
            stats['Possession (%)'][0],
            stats['Duels gagnés'][0],
            stats['Précision passes (%)'][0],
            stats['Tirs cadrés'][0] / max_shots * 100,
            stats['Distance parcourue (km)'][0] / max_distance * 100
        ]

        radar_away = [
            stats['Possession (%)'][1],
            stats['Duels gagnés'][1],
            stats['Précision passes (%)'][1],
            stats['Tirs cadrés'][1] / max_shots * 100,
            stats['Distance parcourue (km)'][1] / max_distance * 100
        ]

        # Nombre de variables
        N = len(radar_stats)

        # Créer des angles pour chaque variable
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # Fermer le graphique

        # Ajouter les données
        radar_home += radar_home[:1]
        radar_away += radar_away[:1]

        # Tracer le graphique radar
        ax_radar.plot(angles, radar_home, 'b-', linewidth=2, label=home_team['name'])
        ax_radar.fill(angles, radar_home, 'b', alpha=0.1)

        ax_radar.plot(angles, radar_away, 'r-', linewidth=2, label=away_team['name'])
        ax_radar.fill(angles, radar_away, 'r', alpha=0.1)

        # Ajouter les étiquettes
        ax_radar.set_thetagrids(np.degrees(angles[:-1]), radar_stats)

        # Ajouter la légende
        ax_radar.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))

        # Ajouter le titre
        ax_radar.set_title('Comparaison des performances', va='bottom')

        # Ajouter la figure à l'interface Tkinter
        canvas_radar = FigureCanvasTkAgg(fig_radar, master=radar_frame)
        canvas_radar.draw()
        canvas_radar.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 4. Graphique camembert pour la possession
        pie_frame = ttk.Frame(notebook)
        notebook.add(pie_frame, text="Possession")

        # Créer la figure matplotlib pour le graphique camembert
        fig_pie, ax_pie = plt.subplots(figsize=(6, 6))

        # Données pour le camembert (possession)
        possession = stats['Possession (%)']

        # Créer le camembert
        colors = ['blue', 'red']
        explode = (0.1, 0)  # Pour mettre en évidence l'équipe à domicile

        ax_pie.pie(possession, explode=explode, labels=[home_team['name'], away_team['name']],
                   colors=colors, autopct='%1.1f%%', shadow=True, startangle=90)

        # Égaliser la forme du graphique
        ax_pie.axis('equal')

        # Ajouter un titre
        ax_pie.set_title('Possession de balle (%)')

        # Ajouter la figure à l'interface Tkinter
        canvas_pie = FigureCanvasTkAgg(fig_pie, master=pie_frame)
        canvas_pie.draw()
        canvas_pie.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def show_today_matches(self):
        """Affiche les matchs de la semaine"""
        self.clear_content()
        ttk.Label(self.content_frame, text="Matchs de la semaine",
                  font=("Arial", 14, "bold")).pack(pady=10)

        # Indicateur de chargement
        loading_label = ttk.Label(self.content_frame, text="Chargement des matchs de la semaine...")
        loading_label.pack(pady=20)
        self.root.update()

        # Fonction pour charger les données en arrière-plan
        def _load_data():
            matches_data = self.api.get_today_matches()
            self.root.after(0, self._display_today_matches, matches_data, loading_label)

        # Lancer le chargement dans un thread
        threading.Thread(target=_load_data, daemon=True).start()

    def _display_today_matches(self, matches_data, loading_label):
        """Met à jour l'UI avec les matchs du jour"""
        if loading_label.winfo_exists():
            loading_label.destroy()

        if isinstance(matches_data, dict) and 'error' in matches_data:
            messagebox.showerror("Erreur API", f"Impossible de charger les matchs du jour : {matches_data['error']}")
            ttk.Label(self.content_frame, text=f"Erreur chargement matchs: {matches_data['error']}").pack()
            return

        matches = matches_data.get('matches', [])
        if matches:
            matches_tab_content = self.create_matches_tab(self.content_frame, matches, None)
            if matches_tab_content:
                matches_tab_content.pack(fill=tk.BOTH, expand=True)
        else:
            ttk.Label(self.content_frame, text="Aucun match prévu aujourd'hui.").pack(pady=20)

    def show_competition_statistics(self):
        """Affiche les statistiques détaillées de la compétition sélectionnée"""
        if not self.selected_competition:
            messagebox.showinfo("Information", "Veuillez d'abord sélectionner une compétition")
            return

        # Créer une nouvelle fenêtre pour les statistiques
        stats_window = tk.Toplevel(self.root)
        stats_window.title(f"Statistiques - {self.selected_competition['name']}")
        stats_window.geometry("1000x800")

        # Créer un notebook pour organiser différentes visualisations
        notebook = ttk.Notebook(stats_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Récupérer les données nécessaires
        standings_data = self.api.get_competition_standings(self.selected_competition['code'])
        scorers_data = self.api.get_competition_scorers(self.selected_competition['code'], limit=20)

        if isinstance(standings_data, dict) and 'standings' in standings_data:
            standings = standings_data['standings'][0]['table'] if standings_data['standings'] else []
        else:
            standings = []

        if isinstance(scorers_data, dict) and 'scorers' in scorers_data:
            scorers = scorers_data['scorers']
        else:
            scorers = []

        # 1. Graphique des points
        points_frame = ttk.Frame(notebook)
        notebook.add(points_frame, text="Points")

        fig_points, ax_points = plt.subplots(figsize=(12, 6))
        teams = [team['team']['name'] for team in standings]
        points = [team['points'] for team in standings]
        
        # Créer le graphique à barres
        bars = ax_points.bar(teams, points)
        
        # Personnaliser le graphique
        ax_points.set_title('Points par équipe')
        ax_points.set_xlabel('Équipes')
        ax_points.set_ylabel('Points')
        plt.xticks(rotation=45, ha='right')
        
        # Ajouter les valeurs sur les barres
        for bar in bars:
            height = bar.get_height()
            ax_points.text(bar.get_x() + bar.get_width()/2., height,
                         f'{int(height)}', ha='center', va='bottom')

        # Ajuster la mise en page
        plt.tight_layout()
        
        # Ajouter le graphique à l'interface Tkinter
        canvas_points = FigureCanvasTkAgg(fig_points, master=points_frame)
        canvas_points.draw()
        canvas_points.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 2. Graphique des buts
        goals_frame = ttk.Frame(notebook)
        notebook.add(goals_frame, text="Buts")

        fig_goals, (ax_goals_for, ax_goals_against) = plt.subplots(2, 1, figsize=(12, 8))
        
        goals_for = [team['goalsFor'] for team in standings]
        goals_against = [team['goalsAgainst'] for team in standings]
        
        # Graphique des buts marqués
        bars_for = ax_goals_for.bar(teams, goals_for, color='green')
        ax_goals_for.set_title('Buts marqués par équipe')
        ax_goals_for.set_xticklabels([])
        ax_goals_for.set_ylabel('Buts marqués')
        
        # Ajouter les valeurs sur les barres
        for bar in bars_for:
            height = bar.get_height()
            ax_goals_for.text(bar.get_x() + bar.get_width()/2., height,
                            f'{int(height)}', ha='center', va='bottom')
        
        # Graphique des buts encaissés
        bars_against = ax_goals_against.bar(teams, goals_against, color='red')
        ax_goals_against.set_title('Buts encaissés par équipe')
        ax_goals_against.set_xticklabels(teams, rotation=45, ha='right')
        ax_goals_against.set_ylabel('Buts encaissés')
        
        # Ajouter les valeurs sur les barres
        for bar in bars_against:
            height = bar.get_height()
            ax_goals_against.text(bar.get_x() + bar.get_width()/2., height,
                                f'{int(height)}', ha='center', va='bottom')

        plt.tight_layout()
        
        canvas_goals = FigureCanvasTkAgg(fig_goals, master=goals_frame)
        canvas_goals.draw()
        canvas_goals.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 3. Graphique des victoires/défaites
        record_frame = ttk.Frame(notebook)
        notebook.add(record_frame, text="V/N/D")

        fig_record, ax_record = plt.subplots(figsize=(12, 6))
        
        wins = [team['won'] for team in standings]
        draws = [team['draw'] for team in standings]
        losses = [team['lost'] for team in standings]
        
        # Créer le graphique empilé
        ax_record.bar(teams, wins, label='Victoires', color='green')
        ax_record.bar(teams, draws, bottom=wins, label='Nuls', color='gray')
        ax_record.bar(teams, losses, bottom=[w + d for w, d in zip(wins, draws)], label='Défaites', color='red')
        
        ax_record.set_title('Bilan des matchs par équipe')
        ax_record.set_xlabel('Équipes')
        ax_record.set_ylabel('Nombre de matchs')
        plt.xticks(rotation=45, ha='right')
        ax_record.legend()
        
        plt.tight_layout()
        
        canvas_record = FigureCanvasTkAgg(fig_record, master=record_frame)
        canvas_record.draw()
        canvas_record.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 4. Graphique des buteurs
        scorers_frame = ttk.Frame(notebook)
        notebook.add(scorers_frame, text="Buteurs")

        fig_scorers, ax_scorers = plt.subplots(figsize=(12, 6))
        
        player_names = [f"{scorer['player']['name']} ({scorer['team']['tla']})" for scorer in scorers[:10]]
        goals = [scorer['goals'] for scorer in scorers[:10]]
        
        # Créer le graphique à barres horizontales
        bars_scorers = ax_scorers.barh(player_names, goals)
        
        ax_scorers.set_title('Top 10 des buteurs')
        ax_scorers.set_xlabel('Nombre de buts')
        
        # Ajouter les valeurs sur les barres
        for bar in bars_scorers:
            width = bar.get_width()
            ax_scorers.text(width, bar.get_y() + bar.get_height()/2.,
                          f'{int(width)}', ha='left', va='center')
        
        plt.tight_layout()
        
        canvas_scorers = FigureCanvasTkAgg(fig_scorers, master=scorers_frame)
        canvas_scorers.draw()
        canvas_scorers.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def show_player_statistics(self, player_id=None):
        """Affiche les statistiques détaillées d'un joueur"""
        if not self.selected_competition:
            messagebox.showinfo("Information", "Veuillez d'abord sélectionner une compétition")
            return

        # Récupérer les données des buteurs
        scorers_data = self.api.get_competition_scorers(self.selected_competition['code'], limit=50)

        if not isinstance(scorers_data, dict) or 'scorers' not in scorers_data:
            messagebox.showerror("Erreur", "Impossible de récupérer les statistiques des joueurs")
            return

        scorers = scorers_data['scorers']

        # Créer une nouvelle fenêtre pour les statistiques
        stats_window = tk.Toplevel(self.root)
        stats_window.title(f"Statistiques des joueurs - {self.selected_competition['name']}")
        stats_window.geometry("1000x800")

        # Créer un notebook pour organiser différentes visualisations
        notebook = ttk.Notebook(stats_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 1. Graphique Buts vs Matchs joués
        goals_frame = ttk.Frame(notebook)
        notebook.add(goals_frame, text="Buts/Matchs")

        fig_goals, ax_goals = plt.subplots(figsize=(12, 6))
        
        player_names = [f"{scorer['player']['name']} ({scorer['team']['tla']})" for scorer in scorers[:15]]
        goals = [scorer['goals'] for scorer in scorers[:15]]
        matches = [scorer.get('playedMatches', 0) for scorer in scorers[:15]]
        
        x = range(len(player_names))
        width = 0.35
        
        bars1 = ax_goals.bar([i - width/2 for i in x], goals, width, label='Buts', color='blue')
        bars2 = ax_goals.bar([i + width/2 for i in x], matches, width, label='Matchs joués', color='green')
        
        ax_goals.set_ylabel('Nombre')
        ax_goals.set_title('Buts et matchs joués par joueur')
        ax_goals.set_xticks(x)
        ax_goals.set_xticklabels(player_names, rotation=45, ha='right')
        ax_goals.legend()
        
        plt.tight_layout()
        
        canvas_goals = FigureCanvasTkAgg(fig_goals, master=goals_frame)
        canvas_goals.draw()
        canvas_goals.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 2. Graphique de ratio buts/match
        ratio_frame = ttk.Frame(notebook)
        notebook.add(ratio_frame, text="Ratio buts/match")

        fig_ratio, ax_ratio = plt.subplots(figsize=(12, 6))
        
        ratios = [g/m if m > 0 else 0 for g, m in zip(goals, matches)]
        bars_ratio = ax_ratio.bar(player_names, ratios)
        
        ax_ratio.set_title('Ratio buts par match')
        ax_ratio.set_xlabel('Joueurs')
        ax_ratio.set_ylabel('Buts par match')
        plt.xticks(rotation=45, ha='right')
        
        # Ajouter les valeurs sur les barres
        for bar in bars_ratio:
            height = bar.get_height()
            ax_ratio.text(bar.get_x() + bar.get_width()/2., height,
                         f'{height:.2f}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        canvas_ratio = FigureCanvasTkAgg(fig_ratio, master=ratio_frame)
        canvas_ratio.draw()
        canvas_ratio.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 3. Tableau des statistiques détaillées
        table_frame = ttk.Frame(notebook)
        notebook.add(table_frame, text="Détails")

        # Créer le tableau
        columns = ('rank', 'player', 'team', 'goals', 'matches', 'ratio')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)

        tree.heading('rank', text='#')
        tree.heading('player', text='Joueur')
        tree.heading('team', text='Équipe')
        tree.heading('goals', text='Buts')
        tree.heading('matches', text='Matchs')
        tree.heading('ratio', text='Ratio')

        tree.column('rank', width=50, anchor='center')
        tree.column('player', width=200)
        tree.column('team', width=150)
        tree.column('goals', width=80, anchor='center')
        tree.column('matches', width=80, anchor='center')
        tree.column('ratio', width=80, anchor='center')

        for i, scorer in enumerate(scorers, 1):
            matches_played = scorer.get('playedMatches', 0)
            ratio = f"{scorer['goals']/matches_played:.2f}" if matches_played > 0 else "N/A"
            
            tree.insert('', tk.END, values=(
                i,
                scorer['player']['name'],
                scorer['team']['name'],
                scorer['goals'],
                matches_played,
                ratio
            ))

        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Ajouter une scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)

    def show_golden_boot(self):
        """Affiche les meilleurs buteurs d'Europe (Golden Boot)"""
        self.clear_content()
        ttk.Label(self.content_frame, text="Golden Boot - Meilleurs Buteurs d'Europe",
                  font=("Arial", 14, "bold")).pack(pady=10)

        # Indicateur de chargement
        loading_label = ttk.Label(self.content_frame, text="Chargement des données...")
        loading_label.pack(pady=20)
        self.root.update()

        # Fonction pour charger les données en arrière-plan
        def _load_data():
            scorers_data = self.api.get_european_scorers()
            self.root.after(0, self._display_golden_boot, scorers_data, loading_label)

        # Lancer le chargement dans un thread
        threading.Thread(target=_load_data, daemon=True).start()

    def _display_golden_boot(self, scorers_data, loading_label):
        """Met à jour l'UI avec les meilleurs buteurs d'Europe"""
        if loading_label.winfo_exists():
            loading_label.destroy()

        if isinstance(scorers_data, dict) and 'error' in scorers_data:
            messagebox.showerror("Erreur API", f"Impossible de charger les données : {scorers_data['error']}")
            ttk.Label(self.content_frame, text=f"Erreur chargement données: {scorers_data['error']}").pack()
            return

        # Créer un notebook pour différentes visualisations
        notebook = ttk.Notebook(self.content_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 1. Tableau des buteurs
        table_frame = ttk.Frame(notebook)
        notebook.add(table_frame, text="Classement")

        # Créer le tableau
        columns = ('rank', 'player', 'team_logo', 'team', 'competition', 'goals', 'coefficient', 'points', 'assists', 'matches')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)

        # Configurer les colonnes
        tree.heading('rank', text='#')
        tree.column('rank', width=40, anchor='center')
        tree.heading('player', text='Joueur')
        tree.column('player', width=200)
        tree.heading('team_logo', text='')
        tree.column('team_logo', width=40, anchor='center')
        tree.heading('team', text='Équipe')
        tree.column('team', width=150)
        tree.heading('competition', text='Compétition')
        tree.column('competition', width=100)
        tree.heading('goals', text='Buts')
        tree.column('goals', width=60, anchor='center')
        tree.heading('coefficient', text='Coeff.')
        tree.column('coefficient', width=60, anchor='center')
        tree.heading('points', text='Points')
        tree.column('points', width=60, anchor='center')
        tree.heading('assists', text='Passes D.')
        tree.column('assists', width=80, anchor='center')
        tree.heading('matches', text='Matchs')
        tree.column('matches', width=60, anchor='center')

        # Ajouter une scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side='right', fill='y')
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side='left', fill='both', expand=True)

        # Dictionnaire des noms de compétitions
        competition_names = {
            'PL': 'Premier League',
            'PD': 'La Liga',
            'BL1': 'Bundesliga',
            'SA': 'Serie A',
            'FL1': 'Ligue 1',
            'DED': 'Eredivisie',
            'PPL': 'Primeira Liga',
            'BJL': 'Jupiler Pro League',
            'RPL': 'Russian Premier League',
            'SSL': 'Super League',
            'EL1': 'Liga I',
            'CL': 'Champions League'
        }

        # Ajouter les données
        for i, scorer in enumerate(scorers_data.get('scorers', []), 1):
            player_info = scorer.get('player', {})
            team_info = scorer.get('team', {})
            team_id = team_info.get('id')
            team_logo_url = team_info.get('crest')
            competition = competition_names.get(scorer.get('competition', ''), scorer.get('competition', ''))

            if not team_id: continue

            item_id = tree.insert('', tk.END, values=(
                i,
                player_info.get('name', 'N/A'),
                '',  # Placeholder pour le logo
                team_info.get('name', 'N/A'),
                competition,
                scorer.get('goals', 'N/A'),
                scorer.get('coefficient', 'N/A'),
                f"{scorer.get('golden_boot_points', 0):.1f}",
                scorer.get('assists', '-'),
                scorer.get('playedMatches', '-')
            ), tags=(str(team_id),))

            # Charger le logo de l'équipe
            if team_logo_url:
                threading.Thread(
                    target=self._fetch_and_schedule_logo_update,
                    args=(tree, item_id, team_id, team_logo_url),
                    daemon=True
                ).start()

        # 2. Graphique des buteurs
        graph_frame = ttk.Frame(notebook)
        notebook.add(graph_frame, text="Graphique")

        # Créer la figure matplotlib
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Préparer les données
        players = [f"{scorer['player']['name']} ({scorer['team']['tla']})" for scorer in scorers_data.get('scorers', [])[:10]]
        points = [scorer['golden_boot_points'] for scorer in scorers_data.get('scorers', [])[:10]]
        
        # Créer le graphique à barres horizontales
        bars = ax.barh(players, points)
        
        # Personnaliser le graphique
        ax.set_title('Top 10 des Buteurs en Europe (Points Golden Boot)')
        ax.set_xlabel('Points Golden Boot')
        
        # Ajouter les valeurs sur les barres
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f'{width:.1f}', ha='left', va='center')
        
        plt.tight_layout()
        
        # Ajouter le graphique à l'interface Tkinter
        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def run(self):
        """Lance l'application"""
        self.root.mainloop()


if __name__ == "__main__":


    API_KEY = "7057bc93ed864b648356d2d588443800"
    if not API_KEY:
         print("ERREUR: Clé API non définie.")
         exit()

    # Lancer l'application
    app = FootballDataApp(API_KEY)
    app.run()

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

        # Sélection de compétition
        ttk.Label(menu_frame, text="Compétition:").pack(side=tk.LEFT)
        self.competition_var = tk.StringVar()
        self.competition_combo = ttk.Combobox(menu_frame, textvariable=self.competition_var, width=40, state='readonly')
        self.competition_combo.pack(side=tk.LEFT, padx=5)
        self.competition_combo.bind("<<ComboboxSelected>>", self.on_competition_selected)

        # Boutons pour les différentes fonctionnalités
        self.standings_button = ttk.Button(menu_frame, text="Classement", command=self.show_standings, state=tk.DISABLED)
        self.standings_button.pack(side=tk.LEFT, padx=5)
        self.matches_button = ttk.Button(menu_frame, text="Matchs", command=self.show_matches, state=tk.DISABLED)
        self.matches_button.pack(side=tk.LEFT, padx=5)
        self.scorers_button = ttk.Button(menu_frame, text="Buteurs", command=self.show_scorers, state=tk.DISABLED)
        self.scorers_button.pack(side=tk.LEFT, padx=5)

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
            # Afficher le classement par défaut
            self.show_standings()
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


    # --- NOUVELLE MÉTHODE ---
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

        # Parcourir les matchs
        for match in matches:
            # Créer un cadre pour chaque match
            match_frame = ttk.Frame(scrollable_frame, borderwidth=1, relief="solid")
            match_frame.pack(fill=tk.X, pady=5, padx=10)

            # Associer un événement de clic au cadre du match pour afficher les statistiques
            match_frame.bind("<Button-1>", lambda event, match_id=match['id']: self.show_match_statistics(match_id))

            # Pour montrer que ce cadre est cliquable
            match_frame.bind("<Enter>",
                             lambda e, frame=match_frame: frame.configure(cursor="hand2", background="#e0e0e0"))
            match_frame.bind("<Leave>",
                             lambda e, frame=match_frame: frame.configure(cursor="", background=self.root.cget(
                                 "background")))

            # Date et compétition
            match_date = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
            date_str = match_date.strftime('%d/%m/%Y %H:%M')

            header_frame = ttk.Frame(match_frame)
            header_frame.pack(fill=tk.X, pady=5)

            # Lier également l'événement aux widgets enfants
            header_frame.bind("<Button-1>", lambda event, match_id=match['id']: self.show_match_statistics(match_id))

            ttk.Label(header_frame, text=date_str).pack(side=tk.LEFT, padx=10)
            ttk.Label(header_frame, text=match['competition']['name']).pack(side=tk.RIGHT, padx=10)
            status_label = ttk.Label(header_frame, text=match['status'],
                                     foreground="green" if match['status'] == 'FINISHED' else "orange")
            status_label.pack(side=tk.RIGHT, padx=5)

            # Lier également les labels
            status_label.bind("<Button-1>", lambda event, match_id=match['id']: self.show_match_statistics(match_id))

            # Structure centrée pour les équipes et le score
            teams_score_frame = ttk.Frame(match_frame)
            teams_score_frame.pack(fill=tk.X, pady=10, padx=5)
            teams_score_frame.bind("<Button-1>",
                                   lambda event, match_id=match['id']: self.show_match_statistics(match_id))

            # Configurer les colonnes pour avoir un alignement centré
            teams_score_frame.columnconfigure(0, weight=2)  # Équipe domicile
            teams_score_frame.columnconfigure(1, weight=1)  # Logo domicile
            teams_score_frame.columnconfigure(2, weight=1)  # Score
            teams_score_frame.columnconfigure(3, weight=1)  # Logo extérieur
            teams_score_frame.columnconfigure(4, weight=2)  # Équipe extérieure

            # Récupérer les données des équipes
            home_id = match['homeTeam']['id']
            home_name = match['homeTeam']['name']
            home_logo_url = match['homeTeam'].get('crest')

            away_id = match['awayTeam']['id']
            away_name = match['awayTeam']['name']
            away_logo_url = match['awayTeam'].get('crest')

            # Charger les logos
            home_logo = self.load_team_logo(home_id, home_logo_url)
            away_logo = self.load_team_logo(away_id, away_logo_url)

            # Nom de l'équipe domicile (colonne 0)
            if str(home_id) == team_id:
                home_label = ttk.Label(teams_score_frame, text=home_name, font=("Arial", 10, "bold"), foreground="blue",
                                       anchor="e")
            else:
                home_label = ttk.Label(teams_score_frame, text=home_name, font=("Arial", 10), anchor="e")
            home_label.grid(row=0, column=0, sticky="e", padx=5)
            home_label.bind("<Button-1>", lambda event, match_id=match['id']: self.show_match_statistics(match_id))

            # Logo équipe domicile (colonne 1)
            if home_logo:
                home_logo_label = ttk.Label(teams_score_frame, image=home_logo)
                home_logo_label.image = home_logo  # Pour éviter que le garbage collector ne supprime l'image
                home_logo_label.grid(row=0, column=1, padx=5)
                home_logo_label.bind("<Button-1>",
                                     lambda event, match_id=match['id']: self.show_match_statistics(match_id))

            # Score au centre (colonne 2)
            if match['status'] == 'FINISHED':
                score_text = f"{match['score']['fullTime']['home']} - {match['score']['fullTime']['away']}"
            else:
                score_text = "vs"

            score_label = ttk.Label(teams_score_frame, text=score_text, font=("Arial", 12, "bold"))
            score_label.grid(row=0, column=2, padx=10)
            score_label.bind("<Button-1>", lambda event, match_id=match['id']: self.show_match_statistics(match_id))

            # Logo équipe extérieure (colonne 3)
            if away_logo:
                away_logo_label = ttk.Label(teams_score_frame, image=away_logo)
                away_logo_label.image = away_logo
                away_logo_label.grid(row=0, column=3, padx=5)
                away_logo_label.bind("<Button-1>",
                                     lambda event, match_id=match['id']: self.show_match_statistics(match_id))

            # Nom de l'équipe extérieure (colonne 4)
            if str(away_id) == team_id:
                away_label = ttk.Label(teams_score_frame, text=away_name, font=("Arial", 10, "bold"), foreground="blue",
                                       anchor="w")
            else:
                away_label = ttk.Label(teams_score_frame, text=away_name, font=("Arial", 10), anchor="w")
            away_label.grid(row=0, column=4, sticky="w", padx=5)
            away_label.bind("<Button-1>", lambda event, match_id=match['id']: self.show_match_statistics(match_id))

            # Ajouter une étiquette pour indiquer que le clic affichera les statistiques
            if match['status'] == 'FINISHED':  # Seulement pour les matchs terminés
                info_label = ttk.Label(match_frame, text="Cliquez pour voir les statistiques",
                                       font=("Arial", 8, "italic"), foreground="grey")
                info_label.pack(pady=(0, 5))
                info_label.bind("<Button-1>", lambda event, match_id=match['id']: self.show_match_statistics(match_id))

        return tab



        def _on_mousewheel(event):
            # Ajuster la sensibilité si nécessaire (delta est +/- 120 sur Windows)
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        # Lier sur le canvas ET le frame interne pour une meilleure couverture
        for widget in [canvas, scrollable_frame]:
             widget.bind_all("<MouseWheel>", _on_mousewheel) # Utiliser bind_all peut être trop large, préférer bind sur le widget spécifique

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        # Ajuster la largeur du frame interne à celle du canvas lors du redimensionnement
        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", _on_canvas_configure)


        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Dictionnaire pour stocker les références d'images pour cet onglet
        tab_logo_refs = {}

        # Parcourir les matchs
        for i, match in enumerate(matches):
            # Créer un cadre pour chaque match
            match_frame = ttk.Frame(scrollable_frame, borderwidth=1, relief="groove") # Relief différent
            match_frame.pack(fill=tk.X, pady=(5 if i > 0 else 0), padx=5) # Pas de pad y pour le premier

            home_team = match.get('homeTeam', {})
            away_team = match.get('awayTeam', {})
            competition = match.get('competition', {})
            score = match.get('score', {}).get('fullTime', {})
            status = match.get('status', 'N/A')

            # --- Header: Date & Compétition ---
            header_frame = ttk.Frame(match_frame, padding=(5,2))
            header_frame.pack(fill=tk.X)

            date_str = "Date inconnue"
            if match.get('utcDate'):
                try:
                    match_date = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
                    # Convertir en heure locale
                    local_date = match_date.astimezone(None)
                    date_str = local_date.strftime('%d/%m/%Y %H:%M')
                except ValueError:
                     date_str = match['utcDate'] # Afficher tel quel si format inconnu

            ttk.Label(header_frame, text=date_str, font=("Arial", 8)).pack(side=tk.LEFT)
            comp_name = competition.get('name', 'Compétition inconnue')
            ttk.Label(header_frame, text=comp_name, font=("Arial", 8, "italic")).pack(side=tk.RIGHT)

            # Séparateur léger
            ttk.Separator(match_frame, orient='horizontal').pack(fill=tk.X, padx=5, pady=2)

            # --- Body Équipes Score
            teams_frame = ttk.Frame(match_frame, padding=(5,5))
            teams_frame.pack(fill=tk.X)

            # Configurer les colonnes pour aligner
            teams_frame.columnconfigure(0, weight=4, uniform='team_info') # Équipe domicile
            teams_frame.columnconfigure(1, weight=1, uniform='team_info') # Score
            teams_frame.columnconfigure(2, weight=4, uniform='team_info') # Équipe extérieure

            #Équipe domicile
            home_frame = ttk.Frame(teams_frame)
            home_frame.grid(row=0, column=0, sticky="ew")

            home_id = str(home_team.get('id', ''))
            home_logo_url = home_team.get('crest')
            home_logo_photo = self.load_team_logo(home_id, home_logo_url, size=(24,24)) # Logo un peu plus petit

            if home_logo_photo:
                logo_label_h = ttk.Label(home_frame, image=home_logo_photo)
                logo_label_h.pack(side=tk.LEFT, padx=(0,5))
                # Garder la référence
                ref_key = f"match_{i}_home_{home_id}"
                tab_logo_refs[ref_key] = home_logo_photo


            home_name = home_team.get('name', 'N/A')
            home_label = ttk.Label(home_frame, text=home_name, anchor="w", font=("Arial", 10))
            if home_id == team_id_str: # Comparer les chaînes
                home_label.config(font=("Arial", 10, "bold")) # Mettre en gras si c'est l'équipe focus
            home_label.pack(side=tk.LEFT, fill=tk.X, expand=True)


            # -- Score --
            score_frame = ttk.Frame(teams_frame)
            score_frame.grid(row=0, column=1, sticky="nsew")

            score_text = "vs"
            home_score = score.get('home')
            away_score = score.get('away')

            if status == 'FINISHED' and home_score is not None and away_score is not None:
                score_text = f"{home_score} - {away_score}"
            elif status in ['IN_PLAY', 'PAUSED'] and home_score is not None and away_score is not None:
                 score_text = f"{home_score} - {away_score} ({status})" # Afficher score live
            elif status == 'SCHEDULED' or status == 'TIMED':
                 # score_text = match_date.strftime('%H:%M') if 'match_date' in locals() else 'À venir'
                 score_text = "vs" # Gardons 'vs' pour la clarté
            elif status == 'POSTPONED':
                 score_text = "Reporté"
            elif status == 'CANCELLED':
                 score_text = "Annulé"


            score_label = ttk.Label(score_frame, text=score_text, font=("Arial", 11, "bold"), anchor="center")
            score_label.pack(fill=tk.BOTH, expand=True)

            #Équipe extérieure
            away_frame = ttk.Frame(teams_frame)
            away_frame.grid(row=0, column=2, sticky="ew")

            away_id = str(away_team.get('id', ''))
            away_logo_url = away_team.get('crest')
            away_logo_photo = self.load_team_logo(away_id, away_logo_url, size=(24,24))

            away_name = away_team.get('name', 'N/A')
            away_label = ttk.Label(away_frame, text=away_name, anchor="e", font=("Arial", 10))
            if away_id == team_id_str: # Comparer les chaînes
                away_label.config(font=("Arial", 10, "bold"))
            away_label.pack(side=tk.RIGHT, fill=tk.X, expand=True)

            if away_logo_photo:
                logo_label_a = ttk.Label(away_frame, image=away_logo_photo)
                logo_label_a.pack(side=tk.RIGHT, padx=(5,0))
                # Garder la référence
                ref_key = f"match_{i}_away_{away_id}"
                tab_logo_refs[ref_key] = away_logo_photo


        # Stocker les références des logos avec le widget tab lui-même pour éviter GC
        tab.tab_logo_refs = tab_logo_refs

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
        score_text = f"{match['score']['fullTime']['home']} - {match['score']['fullTime']['away']}"
        ttk.Label(score_frame, text=score_text, font=("Arial", 14, "bold")).grid(row=0, column=2, padx=20)

        # Logo équipe extérieure
        if away_logo:
            away_logo_label = ttk.Label(score_frame, image=away_logo)
            away_logo_label.image = away_logo
            away_logo_label.grid(row=0, column=3, padx=5)

        # Nom de l'équipe extérieure
        ttk.Label(score_frame, text=away_team['name'], font=("Arial", 11, "bold")).grid(row=0, column=4, padx=10)

        # Extraire et structurer les statistiques
        # Créer des statistiques de démonstration si elles ne sont pas disponibles dans l'API
        # Note: L'API football-data.org ne fournit pas toujours des statistiques détaillées,
        # donc nous allons créer des données de démonstration basées sur le score

        home_score = match['score']['fullTime']['home'] or 0
        away_score = match['score']['fullTime']['away'] or 0

        # Créer des statistiques simulées basées sur le score
        stats = {
            'Possession (%)': (55, 45) if home_score >= away_score else (45, 55),
            'Tirs': (home_score * 3 + 5, away_score * 3 + 5),
            'Tirs cadrés': (home_score * 2 + 2, away_score * 2 + 2),
            'Corners': (home_score + 4, away_score + 4),
            'Fautes': (8, 10),
            'Cartons jaunes': (min(home_score, 3), min(away_score, 3)),
            'Cartons rouges': (0 if home_score < 3 else 1, 0 if away_score < 3 else 1),
            'Hors-jeu': (2, 3),
            'Passes': (450, 400) if home_score >= away_score else (400, 450),
            'Précision passes (%)': (85, 82) if home_score >= away_score else (82, 85)
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
        key_stats = ['Possession (%)', 'Tirs', 'Tirs cadrés', 'Corners', 'Cartons jaunes']
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
            'Tirs (normalisé)',
            'Tirs cadrés (normalisé)',
            'Corners (normalisé)',
            'Précision passes (%)'
        ]

        # Normaliser les valeurs pour qu'elles soient sur la même échelle (0-100)
        max_shots = max(stats['Tirs'])
        max_shots_on_target = max(stats['Tirs cadrés'])
        max_corners = max(stats['Corners'])

        radar_home = [
            stats['Possession (%)'][0],
            stats['Tirs'][0] / max_shots * 100,
            stats['Tirs cadrés'][0] / max_shots_on_target * 100,
            stats['Corners'][0] / max_corners * 100,
            stats['Précision passes (%)'][0]
        ]

        radar_away = [
            stats['Possession (%)'][1],
            stats['Tirs'][1] / max_shots * 100,
            stats['Tirs cadrés'][1] / max_shots_on_target * 100,
            stats['Corners'][1] / max_corners * 100,
            stats['Précision passes (%)'][1]
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

# Football Data Application

Une application de bureau Python pour suivre et analyser les statistiques de football en temps réel.

## Fonctionnalités

- 📊 Classements des compétitions
- ⚽ Matchs en direct et à venir
- 🏆 Meilleurs buteurs par compétition
- 🌟 Golden Boot (meilleurs buteurs d'Europe)
- 📈 Statistiques détaillées des matchs
- 🎯 Statistiques des joueurs
- 🏅 Statistiques des compétitions

## Prérequis

- Python 3.7 ou supérieur
- Une clé API de [Football-Data.org](https://www.football-data.org/)

## Installation

1. Clonez le repository :
```bash
git clone https://github.com/med-ta9i/MedScore
cd MedScore
```

2. Installez les dépendances requises :
```bash
pip install -r requirements.txt
```

3. Configurez votre clé API :
   - Obtenez une clé API gratuite sur [Football-Data.org](https://www.football-data.org/)
   - Remplacez la clé API dans le fichier `FootballDataApp.py` :
   ```python
   API_KEY = "VOTRE_CLE_API"
   ```

## Utilisation

Lancez l'application :
```bash
python FootballDataApp.py
```

### Interface utilisateur

L'application propose une interface graphique intuitive avec :

- Un menu de sélection des compétitions
- Des boutons pour accéder aux différentes fonctionnalités
- Des visualisations interactives des données
- Des graphiques et tableaux de statistiques

### Fonctionnalités principales

1. **Classement**
   - Affiche le classement actuel de la compétition sélectionnée
   - Inclut les logos des équipes
   - Double-clic sur une équipe pour voir ses matchs

2. **Matchs**
   - Affiche les matchs par journée
   - Permet de naviguer entre les journées
   - Affiche les statistiques détaillées des matchs terminés

3. **Buteurs**
   - Liste les meilleurs buteurs de la compétition
   - Affiche les statistiques détaillées (buts, passes décisives, etc.)

4. **Golden Boot**
   - Affiche les meilleurs buteurs d'Europe
   - Calcule les points selon le système Golden Boot
   - Prend en compte les coefficients des différentes compétitions

5. **Statistiques**
   - Statistiques détaillées des compétitions
   - Statistiques individuelles des joueurs
   - Visualisations graphiques des données

## Structure du projet

```
.
├── FootballDataApp.py      # Application principale
├── FootballDataAPi.py      # Classe d'interface avec l'API
├── requirements.txt        # Dépendances Python
├── cache/                  # Cache des données API
└── image_cache/           # Cache des logos d'équipes
```

## Limitations

- L'API gratuite de Football-Data.org a des limites de requêtes
- Certaines fonctionnalités peuvent être limitées selon votre plan d'abonnement
- Les données sont mises en cache pour optimiser les performances

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

##

## Remerciements

- [Football-Data.org](https://www.football-data.org/) pour leur API
- La communauté Python pour les bibliothèques utilisées 

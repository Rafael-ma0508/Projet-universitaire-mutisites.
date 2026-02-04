from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Création de l'instance SQLAlchemy non liée.
# Elle servira de pont entre le code Python et la base de données (SQLite).
db = SQLAlchemy()

def init_db(app):
    """
    Fonction d'initialisation appelée par l'application principale.
    Elle configure la base de données avec les paramètres de l'app Flask.
    """
    # Lie l'objet db à l'application Flask spécifique
    db.init_app(app)
    
    # Création du contexte d'application.
    # Nécessaire car Flask ne sait pas quelle config utiliser sans contexte actif.
    with app.app_context():
        # Crée toutes les tables définies dans models.py si elles n'existent pas déjà.
        db.create_all()
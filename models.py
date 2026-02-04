from database import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    """
    Modèle utilisateur. Hérite de UserMixin pour l'intégration avec Flask-Login
    (gestion automatique des sessions, fonction is_authenticated, etc.).
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # Sécurité : On stocke le HASH du mot de passe, jamais le mot de passe en clair.
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations SQLAlchemy (Liaisons virtuelles vers d'autres tables)
    # lazy=True signifie que les données ne sont chargées que quand on les demande.
    agenda_ownerships = db.relationship('Agenda', backref='owner', lazy=True)
    team_memberships = db.relationship('TeamMember', backref='user', lazy=True)
    
    def set_password(self, password):
        """Transforme le mot de passe texte en empreinte cryptographique (hash)."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Vérifie si le mot de passe entré correspond au hash stocké."""
        return check_password_hash(self.password_hash, password)

class Agenda(db.Model):
    """Table principale représentant un calendrier."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Clé étrangère reliant l'agenda à son créateur (Table User)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # cascade='all, delete-orphan' : Si l'agenda est supprimé, tout son contenu (teams, tickets)
    # est supprimé automatiquement pour ne pas laisser de données orphelines.
    teams = db.relationship('Team', backref='agenda', lazy=True, cascade='all, delete-orphan')
    tickets = db.relationship('Ticket', backref='agenda', lazy=True, cascade='all, delete-orphan')

class Team(db.Model):
    """Table représentant une équipe dans un agenda."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(7), default='#3498db')  # Stocke la couleur hexadécimale
    agenda_id = db.Column(db.Integer, db.ForeignKey('agenda.id'), nullable=False)
    
    members = db.relationship('TeamMember', backref='team', lazy=True, cascade='all, delete-orphan')
    tickets = db.relationship('Ticket', backref='team', lazy=True)

class TeamMember(db.Model):
    """
    Table d'association (Many-to-Many) entre User et Team.
    Stocke aussi le rôle local de l'utilisateur dans l'équipe.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='collaborator')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Empêche un utilisateur d'être ajouté deux fois à la même équipe
    __table_args__ = (db.UniqueConstraint('user_id', 'team_id', name='unique_membership'),)

class AgendaMember(db.Model):
    """Table d'association pour les membres d'un agenda global."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    agenda_id = db.Column(db.Integer, db.ForeignKey('agenda.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='collaborator')
    # Si le rôle est 'team_leader', ce champ indique quelle équipe il dirige.
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    invited_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'agenda_id', name='unique_agenda_membership'),)
    
    # Définition explicite des relations pour faciliter les requêtes complexes
    user = db.relationship('User', foreign_keys=[user_id])
    inviter = db.relationship('User', foreign_keys=[invited_by])
    agenda = db.relationship('Agenda')
    team = db.relationship('Team')

class Ticket(db.Model):
    """Table des événements/tickets du calendrier."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    color = db.Column(db.String(7), default='#2ecc71')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Liens vers Agenda, Équipe (optionnel) et Créateur
    agenda_id = db.Column(db.Integer, db.ForeignKey('agenda.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    history = db.relationship('TicketHistory', backref='ticket', lazy=True, cascade='all, delete-orphan')
    creator = db.relationship('User', foreign_keys=[created_by])

class TicketHistory(db.Model):
    """
    Table d'historique (Audit Log).
    Permet de savoir qui a fait quoi (créé, déplacé, modifié) et quand.
    """
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # Ex: created, updated, moved
    changes = db.Column(db.Text)  # Détails des changements
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')
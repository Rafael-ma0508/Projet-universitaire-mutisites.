from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user
from database import db, init_db
from models import AgendaMember, User, Agenda, Team, TeamMember, Ticket, TicketHistory
from auth import auth_bp
from datetime import datetime
import json

def check_permission(agenda_id, required_permission, team_id=None):
    """
    Vérifie si l'utilisateur courant a la permission requise
    
    Permissions possibles :
    - 'create_ticket' : créer un ticket
    - 'edit_ticket' : modifier un ticket
    - 'delete_ticket' : supprimer un ticket
    - 'move_ticket' : déplacer un ticket (drag & drop)
    - 'create_team' : créer une équipe
    - 'edit_team' : modifier une équipe
    - 'delete_team' : supprimer une équipe
    - 'invite_member' : inviter un membre
    - 'manage_roles' : gérer les rôles
    """
    agenda = Agenda.query.get(agenda_id)
    if not agenda:
        return False
    
    # Le propriétaire a toujours tous les droits
    if agenda.owner_id == current_user.id:
        return True
    
    # Récupérer le rôle de l'utilisateur dans cet agenda précis
    member = AgendaMember.query.filter_by(
        user_id=current_user.id,
        agenda_id=agenda_id
    ).first()
    
    if not member:
        return False
    
    # Restriction : Un chef d'équipe ne peut gérer que SON équipe
    if member.role == 'team_leader' and team_id:
        if member.team_id != team_id:
            return False
    
    # Liste des permissions autorisées par rôle
    permissions = {
        'admin': ['create_ticket', 'edit_ticket', 'delete_ticket', 
                  'move_ticket', 'create_team', 'edit_team', 
                  'delete_team', 'invite_member'],
        'team_leader': ['create_ticket', 'edit_ticket', 'move_ticket'],
        'collaborator': [] # Droits de lecture seule par défaut
    }
    
    return required_permission in permissions.get(member.role, [])

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre-cle-secrete-changez-cela' # Clé pour sécuriser les sessions
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db' # Fichier de la BDD
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuration de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    """Recharge l'objet User à partir de l'ID stocké dans la session."""
    return User.query.get(int(user_id))

# Initialisation BDD et Blueprints
init_db(app)
app.register_blueprint(auth_bp)

def get_user_role(user_id, agenda_id):
    """Fonction utilitaire pour récupérer le rôle d'un user."""
    if user_id == Agenda.query.get(agenda_id).owner_id:
        return 'owner'
    
    member = AgendaMember.query.filter_by(
        user_id=user_id,
        agenda_id=agenda_id
    ).first()
    
    return member.role if member else None

# --- ROUTES ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Affiche tous les agendas (ceux possédés et ceux rejoints)."""
    # 1. Agendas propriétaires
    user_agendas = Agenda.query.filter_by(owner_id=current_user.id).all()
    
    # 2. Agendas membres (jointure)
    member_agendas = Agenda.query.join(AgendaMember).filter(
        AgendaMember.user_id == current_user.id
    ).distinct().all()
    
    # Fusion des deux listes
    all_agendas = list(set(user_agendas + member_agendas))
    
    # Ajout du rôle pour l'affichage
    agendas_with_role = []
    for agenda in all_agendas:
        role = get_user_role(current_user.id, agenda.id)
        agendas_with_role.append({
            'agenda': agenda,
            'role': role
        })
    
    return render_template('dashboard.html', agendas=agendas_with_role)

@app.route('/api/assign_team_leader/<int:agenda_id>/<int:user_id>', methods=['POST'])
@login_required
def assign_team_leader(agenda_id, user_id):
    """Permet au propriétaire de nommer un chef d'équipe."""
    agenda = Agenda.query.get_or_404(agenda_id)
    
    if agenda.owner_id != current_user.id:
        flash('Permission refusée', 'danger')
        return redirect(url_for('agenda_view', agenda_id=agenda_id))
    
    team_id = request.form.get('team_id')
    if not team_id:
        flash('Veuillez sélectionner une équipe', 'danger')
        return redirect(url_for('agenda_view', agenda_id=agenda_id))
    
    team = Team.query.filter_by(id=team_id, agenda_id=agenda_id).first()
    if not team:
        flash('Équipe invalide', 'danger')
        return redirect(url_for('agenda_view', agenda_id=agenda_id))
    
    member = AgendaMember.query.filter_by(
        user_id=user_id,
        agenda_id=agenda_id
    ).first()
    
    if member:
        member.role = 'team_leader'
        member.team_id = team_id
        db.session.commit()
        flash(f'{member.user.username} est maintenant chef de l\'équipe {team.name}', 'success')
    else:
        flash('Membre non trouvé', 'danger')
    
    return redirect(url_for('agenda_view', agenda_id=agenda_id))

@app.route('/agenda/<int:agenda_id>')
@login_required
def agenda_view(agenda_id):
    """Affiche la vue principale de l'agenda avec le calendrier."""
    print(f"=== DEBUG: Accès à l'agenda {agenda_id} ===")
    
    agenda = Agenda.query.get_or_404(agenda_id)
    
    # Vérification d'accès (Propriétaire ou Membre)
    if agenda.owner_id != current_user.id:
        member = AgendaMember.query.filter_by(
            user_id=current_user.id,
            agenda_id=agenda_id
        ).first()
        if not member:
            flash('Accès non autorisé', 'danger')
            return redirect(url_for('dashboard'))
    
    agenda_members = AgendaMember.query.filter_by(agenda_id=agenda_id).all()
    teams = Team.query.filter_by(agenda_id=agenda_id).all()
    tickets = Ticket.query.filter_by(agenda_id=agenda_id).all()
    
    # Préparation des tickets au format JSON pour FullCalendar
    formatted_tickets = []
    for ticket in tickets:
        formatted_tickets.append({
            'id': ticket.id,
            'title': ticket.title,
            'start': ticket.start_time.isoformat(),
            'end': ticket.end_time.isoformat(),
            'color': ticket.color or '#2ecc71',
            'team': ticket.team.name if ticket.team else 'Sans équipe',
            'team_id': ticket.team_id
        })
    
    return render_template('agenda.html', 
                         agenda=agenda, 
                         teams=teams, 
                         tickets=json.dumps(formatted_tickets),
                         agenda_members=agenda_members,
                         current_user_role=get_user_role(current_user.id, agenda_id))

@app.route('/api/create_ticket', methods=['POST'])
@login_required
def create_ticket():
    """API (AJAX) pour créer un ticket sans recharger la page."""
    try:
        data = request.json
        agenda_id = data.get('agenda_id')
        
        # Vérification des permissions via RBAC
        if not check_permission(agenda_id, 'create_ticket'):
            return jsonify({'error': 'Permission refusée. Vous ne pouvez pas créer de ticket.'}), 403
        
        agenda = Agenda.query.get(agenda_id)
        if not agenda:
            return jsonify({'error': 'Agenda non trouvé'}), 404
        
        # Logique spécifique pour les chefs d'équipe
        member = AgendaMember.query.filter_by(
            user_id=current_user.id,
            agenda_id=agenda_id
        ).first()
        
        if member and member.role == 'team_leader':
            team_id = data.get('team_id')
            if not team_id:
                return jsonify({'error': 'Les chefs d\'équipe doivent attribuer un ticket à une équipe'}), 403
            
            # Vérifier que le chef est bien responsable de CETTE équipe
            team = Team.query.get(team_id)
            if not team or team.agenda_id != agenda_id:
                return jsonify({'error': 'Équipe invalide'}), 400
        
        ticket = Ticket(
            title=data['title'],
            description=data.get('description', ''),
            start_time=datetime.fromisoformat(data['start_time'].replace('Z', '+00:00')),
            end_time=datetime.fromisoformat(data['end_time'].replace('Z', '+00:00')),
            color=data.get('color', '#2ecc71'),
            agenda_id=agenda_id,
            team_id=data.get('team_id'),
            created_by=current_user.id
        )
        
        db.session.add(ticket)
        db.session.commit()
        
        return jsonify({'success': True, 'ticket_id': ticket.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create_agenda', methods=['POST'])
@login_required
def create_agenda():
    name = request.form.get('name')
    description = request.form.get('description', '')
    
    if not name:
        flash('Le nom est requis', 'danger')
        return redirect(url_for('dashboard'))
    
    agenda = Agenda(
        name=name,
        description=description,
        owner_id=current_user.id
    )
    
    db.session.add(agenda)
    db.session.commit()
    
    flash('Agenda créé avec succès', 'success')
    return redirect(url_for('dashboard'))

@app.route('/api/create_team/<int:agenda_id>', methods=['POST'])
@login_required
def create_team(agenda_id):
    agenda = Agenda.query.get_or_404(agenda_id)
    
    if agenda.owner_id != current_user.id:
        flash('Permission refusée', 'danger')
        return redirect(url_for('agenda_view', agenda_id=agenda_id))
    
    name = request.form.get('name')
    color = request.form.get('color', '#3498db')
    
    team = Team(
        name=name,
        color=color,
        agenda_id=agenda_id
    )
    
    db.session.add(team)
    db.session.commit()
    
    flash('Équipe créée avec succès', 'success')
    return redirect(url_for('agenda_view', agenda_id=agenda_id))

@app.route('/api/invite_to_agenda/<int:agenda_id>', methods=['POST'])
@login_required
def invite_to_agenda(agenda_id):
    """Inviter un utilisateur via son email."""
    agenda = Agenda.query.get_or_404(agenda_id)
    
    if agenda.owner_id != current_user.id:
        flash('Permission refusée', 'danger')
        return redirect(url_for('agenda_view', agenda_id=agenda_id))
    
    email = request.form.get('email')
    role = request.form.get('role', 'collaborator')
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Utilisateur non trouvé', 'danger')
        return redirect(url_for('agenda_view', agenda_id=agenda_id))
    
    existing = AgendaMember.query.filter_by(
        user_id=user.id,
        agenda_id=agenda_id
    ).first()
    
    if existing:
        flash('Cet utilisateur est déjà membre', 'info')
        return redirect(url_for('agenda_view', agenda_id=agenda_id))
    
    member = AgendaMember(
        user_id=user.id,
        agenda_id=agenda_id,
        role=role,
        invited_by=current_user.id
    )
    
    db.session.add(member)
    db.session.commit()
    
    flash(f'{user.username} a été invité en tant que {role}', 'success')
    return redirect(url_for('agenda_view', agenda_id=agenda_id))

@app.route('/api/remove_member/<int:agenda_id>/<int:user_id>', methods=['POST'])
@login_required
def remove_member(agenda_id, user_id):
    agenda = Agenda.query.get_or_404(agenda_id)
    
    if agenda.owner_id != current_user.id:
        flash('Permission refusée', 'danger')
        return redirect(url_for('agenda_view', agenda_id=agenda_id))
    
    member = AgendaMember.query.filter_by(
        user_id=user_id,
        agenda_id=agenda_id
    ).first()
    
    if member:
        db.session.delete(member)
        db.session.commit()
        flash('Membre retiré', 'success')
    
    return redirect(url_for('agenda_view', agenda_id=agenda_id))

@app.route('/api/update_role/<int:agenda_id>/<int:user_id>', methods=['POST'])
@login_required
def update_role(agenda_id, user_id):
    """Changer le rôle d'un membre (ex: passer de collaborateur à admin)."""
    agenda = Agenda.query.get_or_404(agenda_id)
    
    if agenda.owner_id != current_user.id:
        flash('Permission refusée', 'danger')
        return redirect(url_for('agenda_view', agenda_id=agenda_id))
    
    new_role = request.form.get('role')
    member = AgendaMember.query.filter_by(
        user_id=user_id,
        agenda_id=agenda_id
    ).first()
    
    if member and new_role in ['admin', 'team_leader', 'collaborator']:
        member.role = new_role
        db.session.commit()
        flash(f'Rôle changé en {new_role}', 'success')
    return redirect(url_for('agenda_view', agenda_id=agenda_id))

@app.route('/ticket_history/<int:ticket_id>')
@login_required
def ticket_history(ticket_id):
    """Page d'historique des modifications d'un ticket."""
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Vérification d'accès : Créateur OU Propriétaire Agenda OU Membre d'équipe
    if ticket.created_by != current_user.id and ticket.agenda.owner_id != current_user.id:
        if ticket.team_id:
            membership = TeamMember.query.filter_by(
                user_id=current_user.id,
                team_id=ticket.team_id
            ).first()
            if not membership:
                flash('Accès non autorisé', 'danger')
                return redirect(url_for('dashboard'))
        else:
            flash('Accès non autorisé', 'danger')
            return redirect(url_for('dashboard'))
    
    history = TicketHistory.query.filter_by(ticket_id=ticket_id)\
        .order_by(TicketHistory.timestamp.desc()).all()
    
    return render_template('ticket_history.html', ticket=ticket, history=history)

@app.route('/api/drag_ticket/<int:ticket_id>', methods=['POST'])
@login_required
def drag_ticket(ticket_id):
    """API pour gérer le déplacement (Drag & Drop) d'un ticket."""
    try:
        data = request.json
        ticket = Ticket.query.get_or_404(ticket_id)
        
        ticket.start_time = datetime.fromisoformat(data['new_start'].replace('Z', '+00:00'))
        if data.get('new_end'):
            ticket.end_time = datetime.fromisoformat(data['new_end'].replace('Z', '+00:00'))
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
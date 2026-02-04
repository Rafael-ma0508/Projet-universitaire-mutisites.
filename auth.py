from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User, db

# Blueprint permet de séparer les routes d'authentification du fichier principal app.py
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Gère la page de connexion."""
    # Debug pour vérifier le flux dans la console
    print("=== DEBUG: Page login appelée ===")
    print(f"Utilisateur authentifié: {current_user.is_authenticated}")
    
    if current_user.is_authenticated:
        print("DEBUG: Utilisateur déjà connecté, redirection vers dashboard")
        return redirect('/dashboard')
    
    if request.method == 'POST':
        print("DEBUG: Formulaire POST reçu")
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"DEBUG: Username: {username}")
        
        # Recherche de l'utilisateur dans la base de données
        user = User.query.filter_by(username=username).first()
        
        # Vérification du hash du mot de passe
        if user and user.check_password(password):
            print(f"DEBUG: Connexion réussie pour {username}")
            login_user(user) # Crée la session utilisateur Flask
            flash('Connexion réussie!', 'success')
            return redirect('/dashboard')
        else:
            print("DEBUG: Échec de connexion")
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Gère la page d'inscription."""
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Vérifications de base (mots de passe identiques, unicité, etc.)
        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Nom d\'utilisateur déjà utilisé', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email déjà utilisé', 'danger')
            return render_template('register.html')
        
        # Création du nouvel utilisateur
        user = User(username=username, email=email)
        user.set_password(password) # Hashage du mot de passe
        
        db.session.add(user)
        db.session.commit() # Sauvegarde en base de données
        
        flash('Inscription réussie! Vous pouvez maintenant vous connecter', 'success')
        return redirect('/login')
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required # Protection : il faut être connecté pour se déconnecter
def logout():
    logout_user() # Supprime la session
    flash('Vous avez été déconnecté', 'info')
    return redirect('/login')  # Chemin direct
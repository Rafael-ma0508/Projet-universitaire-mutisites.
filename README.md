# Projet-universitaire-mutisites.
Ceci a été un site crée en groupe lors d'une SAE dans le cadre de ma 2ème année de BUT Réseau et Télécommunications
Réaliser par Rafael, Andon, Adam, Hamza et Jawher / 2025/2026

Tables des matières :
1. Présentation générale du projet
2. Architecture générale 
3. Technologies utilisées 
4. Modèle de données
5. Organisation du code 
6. Fonctionnalités implémentées 
7. Installation et exécution 
7.1 Préparation 
7.2 Installation des dépendances
7.3 Lancement de l'application 
7.4 Accès à l'application 
8. Scénarios d'utilisation 
Scénario 1 – Créer un agenda et ajouter des équipes
Scénario 2 – Créer des tickets et les associer à des équipes 
Scénario 3 – Inviter des collaborateurs 
Scénario 4 – Consulter l'agenda partagé 

1. Présentation générale du projet
L’application Agenda Collaboratif est une application client–serveur permettant à plusieurs
utilisateurs de gérer des agendas partagés avec des équipes et des tickets colorés. Elle a été
réalisée dans le cadre de la SAE 3.02 « Développer des applications communicantes ».

Les objectifs principaux sont :
• Authentifier des utilisateurs et gérer leurs droits.
• Créer des agendas contenant des équipes.
• Associer des tickets (tâches/événements) aux équipes et aux agendas.
• Afficher les tickets sur un agenda avec drag & drop.
• Conserver l’historique des modifications des tickets.

2. Architecture générale
L’application suit une architecture client–serveur :
• Serveur : écrit en Python, il gère la logique métier, la base de données et les
communications réseau.
• Client : interface graphique (web) permettant à l’utilisateur de se connecter, de gérer
ses agendas, équipes et tickets.
Les échanges entre client et serveur sont transportés via des sockets TCP.

3. Technologies utilisées
• Langage : Python 3
• Framework web : Flask (micro‑framework)
• ORM : SQLAlchemy (gestion des modèles et requêtes)
• Gestion des sessions & login : Flask‑Login
• Formulaires : Flask‑WTF / WTForms (si présent dans requirements.txt)
• Base de données : SQLite (URI définie dans

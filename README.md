# Projet-universitaire-Agenta_collaboratif.
Ceci a été un site crée en groupe lors d'une SAE dans le cadre de ma 2ème année de BUT Réseau et Télécommunications
Documentation Technique - Agenda Collaboratif
============================================

Réaliser par : Rafael, Andon, Adam, Hamza et Jawher
Année : 2025/2026

TABLE DES MATIERES
==================
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

1. PRESENTATION GENERALE DU PROJET 
============================================
L'application Agenda Collaboratif est une application client-serveur permettant à plusieurs
utilisateurs de gérer des agendas partagés avec des équipes et des tickets colorés. Elle a été
réalisée dans le cadre de la SAE 3.02 "Développer des applications communicantes".

Objectifs principaux :
- Authentifier des utilisateurs et gérer leurs droits
- Créer des agendas contenant des équipes
- Associer des tickets (tâches/événements) aux équipes et aux agendas
- Afficher les tickets sur un agenda avec drag & drop
- Conserver l'historique des modifications des tickets

2. ARCHITECTURE GENERALE 
=================================
Architecture client-serveur :
- Serveur : Python, logique métier, base de données, communications réseau
- Client : Interface graphique web (connexion, gestion agendas/équipes/tickets)
- Échanges : sockets TCP

3. TECHNOLOGIES UTILISEES 
==================================
- Langage : Python 3
- Framework web : Flask (micro-framework)
- ORM : SQLAlchemy (modèles et requêtes)
- Sessions & login : Flask-Login
- Formulaires : Flask-WTF / WTForms
- Base de données : SQLite (remplaçable PostgreSQL/MySQL)

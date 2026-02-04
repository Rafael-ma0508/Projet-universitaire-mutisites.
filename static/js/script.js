// Fonctions JavaScript pour l'agenda

function createTicket() {
    // Récupération des données du formulaire HTML
    const form = document.getElementById('createTicketForm');
    const formData = {
        agenda_id: form.dataset.agendaId, // Récupération via attribut data-
        title: form.querySelector('#ticketTitle').value,
        description: form.querySelector('#ticketDescription').value,
        start_time: form.querySelector('#ticketStart').value,
        end_time: form.querySelector('#ticketEnd').value,
        team_id: form.querySelector('#ticketTeam').value,
        color: form.querySelector('#ticketColor').value
    };
    
    // Appel AJAX vers l'API Flask
    fetch('/api/create_ticket', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json', // Envoi en format JSON
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload(); // Recharger la page pour voir le nouveau ticket
        } else {
            alert('Erreur: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Une erreur est survenue');
    });
}

// Initialisation des sélecteurs de couleur au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    const colorInputs = document.querySelectorAll('.color-picker');
    colorInputs.forEach(input => {
        input.addEventListener('input', function() {
            this.style.backgroundColor = this.value;
        });
    });
});
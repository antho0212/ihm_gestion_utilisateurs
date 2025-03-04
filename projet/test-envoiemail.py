import smtplib
from email.mime.text import MIMEText

expediteur = "btssnfourcade2@gmail.com"
mot_de_passe_email = "wdkw adue hvub ikqm"
destinataire = "polaszykanthony702@gmail.com"  # Remplacez par une autre adresse email

msg = MIMEText("Ceci est un test d'email.")
msg["Subject"] = "Test d'email"
msg["From"] = expediteur
msg["To"] = destinataire

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as serveur:
        serveur.login(expediteur, mot_de_passe_email)
        serveur.send_message(msg)
    print("Email envoyé avec succès!")
except Exception as e:
    print(f"Erreur lors de l'envoi de l'email : {e}")
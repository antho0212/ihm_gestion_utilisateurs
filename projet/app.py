from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from werkzeug.security import generate_password_hash, check_password_hash
import time

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.static_folder = 'static'

FICHIER_UTILISATEURS = "utilisateurs.txt"

def lire_utilisateurs():
    utilisateurs = []
    if os.path.exists(FICHIER_UTILISATEURS):
        with open(FICHIER_UTILISATEURS, "r") as f:
            for ligne in f:
                ligne = ligne.strip()
                if ligne:
                    elements = ligne.split(";")
                    if len(elements) == 7:
                        nom, prenom, email, telephone, plaque, mot_de_passe, role = elements
                        utilisateurs.append({
                            "nom": nom,
                            "prenom": prenom,
                            "email": email,
                            "telephone": telephone,
                            "plaque_immatriculation": plaque,
                            "mot_de_passe": mot_de_passe,
                            "role": role
                        })
    return utilisateurs

def ecrire_utilisateurs(utilisateurs):
    with open(FICHIER_UTILISATEURS, "w") as f:
        for utilisateur in utilisateurs:
            f.write(f"{utilisateur['nom']};{utilisateur['prenom']};{utilisateur['email']};{utilisateur['telephone']};{utilisateur['plaque_immatriculation']};{utilisateur['mot_de_passe']};{utilisateur['role']}\n")

def creer_utilisateur_par_defaut():
    utilisateurs = lire_utilisateurs()
    admin_existe = False
    for utilisateur in utilisateurs:
        if utilisateur['nom'] == 'admin' and utilisateur['prenom'] == 'admin':
            admin_existe = True
            break

    if not admin_existe:
        mot_de_passe_hache = generate_password_hash("admin", method='pbkdf2:sha256')
        utilisateurs.append({
            "nom": "admin",
            "prenom": "admin",
            "email": "admin@example.com",
            "telephone": "00.00.00.00.00",
            "plaque_immatriculation": "nothing",
            "mot_de_passe": mot_de_passe_hache,
            "role": "admin"
        })
        ecrire_utilisateurs(utilisateurs)

with app.app_context():
    creer_utilisateur_par_defaut()

@app.route("/")
def index():
    if 'utilisateur_connecte' not in session:
        return redirect(url_for("login"))

    utilisateur = session['utilisateur_connecte']
    if check_password_hash(utilisateur['mot_de_passe'], 'admin'):
        flash("Veuillez changer votre mot de passe.", "danger")

    utilisateurs = lire_utilisateurs()
    return render_template("index.html", utilisateurs=utilisateurs, couleur_texte=session.get('couleur_texte', 'black'))

@app.route("/ajouter", methods=["GET", "POST"])
def ajouter():
    if 'utilisateur_connecte' not in session:
        return redirect(url_for("login"))

    if session['utilisateur_connecte']['role'] != 'admin':
        flash("Vous n'avez pas les droits pour ajouter un utilisateur.", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        nom = request.form["nom"]
        prenom = request.form["prenom"]
        email = request.form["email"]
        telephone = request.form["telephone"]
        plaque = request.form["plaque"]
        mot_de_passe = request.form["mot_de_passe"]
        role = request.form["role"]

        mot_de_passe_hache = generate_password_hash(mot_de_passe, method='pbkdf2:sha256')

        utilisateurs = lire_utilisateurs()
        utilisateurs.append({
            "nom": nom,
            "prenom": prenom,
            "email": email,
            "telephone": telephone,
            "plaque_immatriculation": plaque,
            "mot_de_passe": mot_de_passe_hache,
            "role": role
        })
        ecrire_utilisateurs(utilisateurs)
        return redirect(url_for("index"))
    return render_template("ajouter.html", couleur_texte=session.get('couleur_texte', 'black'))

@app.route("/modifier/<int:id>", methods=["GET", "POST"])
def modifier(id):
    if 'utilisateur_connecte' not in session:
        return redirect(url_for("login"))

    utilisateurs = lire_utilisateurs()
    if id < 0 or id >= len(utilisateurs):
        return "Utilisateur non trouvé"

    utilisateur_a_modifier = utilisateurs[id]
    utilisateur_connecte = session['utilisateur_connecte']

    if utilisateur_connecte['role'] != 'admin' and utilisateur_connecte['email'] != utilisateur_a_modifier['email']:
        flash("Vous n'avez pas les droits pour modifier cet utilisateur.", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        utilisateur_a_modifier["nom"] = request.form["nom"]
        utilisateur_a_modifier["prenom"] = request.form["prenom"]
        utilisateur_a_modifier["email"] = request.form["email"]
        utilisateur_a_modifier["telephone"] = request.form["telephone"]
        utilisateur_a_modifier["plaque_immatriculation"] = request.form["plaque"]
        if request.form["mot_de_passe"]:
            utilisateur_a_modifier["mot_de_passe"] = generate_password_hash(request.form["mot_de_passe"], method='pbkdf2:sha256')
        if utilisateur_connecte['role'] == 'admin':
            utilisateur_a_modifier["role"] = request.form["role"]
        ecrire_utilisateurs(utilisateurs)
        return redirect(url_for("index"))
    return render_template("modifier.html", utilisateur=utilisateur_a_modifier, id=id, couleur_texte=session.get('couleur_texte', 'black'))

@app.route("/supprimer/<int:id>")
def supprimer(id):
    if 'utilisateur_connecte' not in session:
        return redirect(url_for("login"))

    if session['utilisateur_connecte']['role'] != 'admin':
        flash("Vous n'avez pas les droits pour supprimer un utilisateur.", "danger")
        return redirect(url_for("index"))

    utilisateurs = lire_utilisateurs()
    if id < 0 or id >= len(utilisateurs):
        return "Utilisateur non trouvé"

    del utilisateurs[id]
    ecrire_utilisateurs(utilisateurs)
    return redirect(url_for("index"))

@app.route("/parametres", methods=["GET", "POST"])
def parametres():
    if 'utilisateur_connecte' not in session:
        return redirect(url_for("login"))

    utilisateurs = lire_utilisateurs()

    if request.method == "POST":
        if 'image_fond' in request.files:
            image = request.files['image_fond']
            if image.content_type.startswith('image/'):
                chemin_image = "static/images/fond.jpg"
                image.save(chemin_image)
                session['fond_cache_bust'] = str(time.time())
                flash("Fond d'écran changé avec succès!", "success")
        elif 'couleur_texte' in request.form:
            couleur_texte = request.form['couleur_texte']
            session['couleur_texte'] = couleur_texte
            flash("Couleur du texte changée avec succès!", "success")

    return render_template("parametres.html", fond_cache_bust=session.get('fond_cache_bust'), couleur_texte=session.get('couleur_texte', 'black'), utilisateurs=utilisateurs)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nom_utilisateur = request.form["nom_utilisateur"]
        mot_de_passe = request.form["mot_de_passe"]

        utilisateurs = lire_utilisateurs()
        for utilisateur in utilisateurs:
            if f"{utilisateur['prenom']}.{utilisateur['nom']}" == nom_utilisateur:
                if check_password_hash(utilisateur['mot_de_passe'], mot_de_passe):
                    session['utilisateur_connecte'] = utilisateur
                    return redirect(url_for("index"))

        return render_template("login.html", erreur="Nom d'utilisateur ou mot de passe incorrect", couleur_texte=session.get('couleur_texte', 'black'))

    return render_template("login.html", couleur_texte=session.get('couleur_texte', 'black'))

@app.route("/logout")
def logout():
    session.pop('utilisateur_connecte', None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
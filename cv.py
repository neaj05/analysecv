import streamlit as st
import spacy
import pdfplumber
import os
import sqlite3
import pytesseract
from passlib.hash import pbkdf2_sha256

# Charger le modèle spaCy pour le traitement du langage naturel
nlp = spacy.load("fr_core_news_sm")

# Configuration de Tesseract pour l'OCR
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Chemin vers votre installation Tesseract


# Fonction pour initialiser la base de données
def initialiser_base_de_donnees():
    conn = sqlite3.connect("utilisateurs.db")
    cursor = conn.cursor()

    # Créer une table pour stocker les informations d'identification des utilisateurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_utilisateur TEXT UNIQUE,
            mot_de_passe TEXT
        )
    ''')

    # Ajouter un utilisateur par défaut (à des fins de démonstration)
    nom_utilisateur_par_defaut = "admin"
    mot_de_passe_par_defaut = pbkdf2_sha256.hash("admin_password")

    cursor.execute('''
        INSERT OR IGNORE INTO utilisateurs (nom_utilisateur, mot_de_passe)
        VALUES (?, ?)
    ''', (nom_utilisateur_par_defaut, mot_de_passe_par_defaut))

    conn.commit()
    conn.close()

# Vérifier et initialiser la base de données
initialiser_base_de_donnees()

# Fonction pour vérifier les informations d'identification
def verifier_identification(nom_utilisateur, mot_de_passe):
    conn = sqlite3.connect("utilisateurs.db")
    cursor = conn.cursor()

    cursor.execute('''
        SELECT mot_de_passe FROM utilisateurs WHERE nom_utilisateur=?
    ''', (nom_utilisateur,))

    resultat = cursor.fetchone()

    if resultat and pbkdf2_sha256.verify(mot_de_passe, resultat[0]):
        return True
    else:
        return False

# Fonction pour ajouter un utilisateur (à des fins de démonstration)
def ajouter_utilisateur(nom_utilisateur, mot_de_passe):
    conn = sqlite3.connect("utilisateurs.db")
    cursor = conn.cursor()

    mot_de_passe_hash = pbkdf2_sha256.hash(mot_de_passe)

    cursor.execute('''
        INSERT INTO utilisateurs (nom_utilisateur, mot_de_passe)
        VALUES (?, ?)
    ''', (nom_utilisateur, mot_de_passe_hash))

    conn.commit()
    conn.close()

# Partie Streamlit
page = st.sidebar.selectbox("Navigation", ["Connexion", "Analyse de CV"])

if page == "Connexion":
    st.title("Connexion utilisateur")

    nom_utilisateur = st.text_input("Nom d'utilisateur:")
    mot_de_passe = st.text_input("Mot de passe:", type="password")

    if st.button("Se connecter"):
        if verifier_identification(nom_utilisateur, mot_de_passe):
            st.success("Connexion réussie!")
            st.session_state.utilisateur_connecte = True
        else:
            st.error("Nom d'utilisateur ou mot de passe incorrect.")

elif page == "Analyse de CV":
    if hasattr(st.session_state, "utilisateur_connecte") and st.session_state.utilisateur_connecte:
        st.title("Analyseur de CV en PDF")

        # ... (le reste du code pour l'analyse de CV)

        def extraire_texte_pdf(chemin_pdf):
            with pdfplumber.open(chemin_pdf) as pdf:
                texte = ""
                for page in pdf.pages:
                    texte += page.extract_text()
            return texte

        def analyser_cv(texte_cv, mots_cles):
            doc = nlp(texte_cv)
            mots_cles_trouves = [token.text for token in doc if token.text.lower() in mots_cles]
            return mots_cles_trouves


        # Uploader des fichiers PDF multiples
        fichiers_pdf = st.file_uploader("Uploader plusieurs fichiers PDF", type=["pdf"], accept_multiple_files=True)

        # Zone pour saisir les mots clés
        mots_cles_saisis = st.text_input("Mots clés (séparés par des virgules)")

        if fichiers_pdf is not None and mots_cles_saisis:
            mots_cles = [mot.strip().lower() for mot in mots_cles_saisis.split(',')]
            
            # Liste pour stocker les CVs qui respectent les mots clés
            cvs_respectant_mots_cles = []

            for fichier_pdf in fichiers_pdf:
                texte_cv = extraire_texte_pdf(fichier_pdf)

                st.subheader(f"Texte extrait du CV - {fichier_pdf.name}:")
                #st.write(texte_cv)

                mots_cles_trouves = analyser_cv(texte_cv, mots_cles)

                st.subheader("Mots clés trouvés dans le CV:")
                st.write(mots_cles_trouves)

                if mots_cles_trouves:
                    st.success(f"Le CV {fichier_pdf.name} correspond aux mots clés recherchés.")
                    cvs_respectant_mots_cles.append((fichier_pdf.name, texte_cv))
			
            # Champ de texte pour spécifier le dossier de destination
            dossier_cvs = st.text_input("Chemin du dossier de destination pour enregistrer les CVs", "CVs")
	    # Utilisation de st.secrets pour récupérer le chemin du dossier partagé
    	    # dossier_cvs = st.secrets["destination_folder"]
            if not os.path.exists(dossier_cvs):
                st.error("Le dossier de destination spécifié n'existe pas.")
            else:

            
                # Bouton pour enregistrer les CVs sélectionnés
                if cvs_respectant_mots_cles and st.button("Enregistrer les CVs sélectionnés"):
                    for nom_fichier, texte_cv in cvs_respectant_mots_cles:
                        nom_fichier = f"cv_{nom_fichier.replace(' ', '_')}"
                        chemin_fichier = os.path.join(dossier_cvs, f"{nom_fichier}")
                        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
                            fichier.write(texte_cv)
                        st.success(f"Le CV {nom_fichier} a été enregistré dans le dossier {dossier_cvs} avec le nom: {nom_fichier}")

    else:
        st.warning("Veuillez vous connecter pour accéder à cette page.")

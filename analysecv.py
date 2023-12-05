import streamlit as st
import spacy
import pdfplumber
import os

# Charger le modèle spaCy pour le traitement du langage naturel
nlp = spacy.load("fr_core_news_sm")

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

# Partie Streamlit
st.title("Analyse de CV en PDF")

# Créer un dossier pour stocker les CVs
dossier_cvs = "CVs"
if not os.path.exists(dossier_cvs):
    os.makedirs(dossier_cvs)

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

    # Bouton pour enregistrer les CVs sélectionnés
    if cvs_respectant_mots_cles and st.button("Enregistrer les CVs sélectionnés"):
        for nom_fichier, texte_cv in cvs_respectant_mots_cles:
            nom_fichier = f"cv_{nom_fichier.replace(' ', '_')}"
            chemin_fichier = os.path.join(dossier_cvs, f"{nom_fichier}")
            with open(chemin_fichier, "w", encoding="utf-8") as fichier:
                fichier.write(texte_cv)
            st.success(f"Le CV {nom_fichier} a été enregistré avec le nom: {nom_fichier}")

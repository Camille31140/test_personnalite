import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import os

# --- Charger le logo ---
logo_path = "logo.png"  # Assure-toi que le fichier est bien dans le dossier
st.sidebar.image(logo_path, width=150)

# --- Titre de l'application ---
st.title("Test de Personnalité")

# --- Demande du prénom et du nom ---
st.header("Informations personnelles")
prenom = st.text_input("Prénom")
nom = st.text_input("Nom")

# --- Charger les questions depuis le fichier CSV ---
questions = {}
try:
    df = pd.read_csv("Classeur1.csv", sep=";", encoding="utf-8")
    df.columns = ["Question", "Critère"]
    
    for _, row in df.iterrows():
        questions[row["Question"]] = row["Critère"]
except:
    st.error("Erreur : Le fichier Classeur1.csv est introuvable ou mal formaté.")

# --- Formulaire de test ---
st.header("Répondez aux questions")
responses = {}
for q, critere in questions.items():
    responses[q] = st.slider(q, 1, 5, 3)

# --- Fonction pour générer un PDF avec graphique radar ---
def generate_pdf(prenom, nom, responses, avg_scores):
    pdf_path = f"profil_{prenom}_{nom}.pdf"
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='', size=16)

    # Ajouter titre
    pdf.cell(200, 10, f"Profil de {prenom} {nom}", ln=True, align='C')

    # Ajouter les résultats sous forme de texte
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    for q, score in responses.items():
        pdf.multi_cell(0, 10, f"{q}: {score}/5")

    # --- Génération du graphique radar ---
    labels = list(avg_scores.keys())
    values = list(avg_scores.values())

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'projection': 'polar'})
    angles = [n / float(len(labels)) * 2 * 3.14159 for n in range(len(labels))]
    ax.set_xticks(angles)
    ax.set_xticklabels(labels)

    values += values[:1]
    angles += angles[:1]
    ax.plot(angles, values, 'o-', linewidth=2)
    ax.fill(angles, values, alpha=0.25)

    # Sauvegarde du graphique
    radar_chart_path = f"radar_{prenom}_{nom}.png"
    fig.savefig(radar_chart_path)
    plt.close(fig)

    # Ajouter le graphique au PDF
    pdf.ln(10)
    pdf.image(radar_chart_path, x=30, w=150)

    # Sauvegarde du PDF
    pdf.output(pdf_path)
    return pdf_path

# --- Enregistrement des réponses ---
if st.button("Envoyer mes réponses"):
    if prenom and nom:
        # Créer un dictionnaire avec les réponses et infos de l'élève
        student_data = {"Prénom": prenom, "Nom": nom}
        for q, critere in questions.items():
            student_data[q] = responses[q]
        
        # Charger ou créer le fichier correctement formaté
        try:
            df_existing = pd.read_csv("reponses.csv", sep=";", encoding="utf-8")
            df_new = pd.DataFrame([student_data])
            df_final = pd.concat([df_existing, df_new], ignore_index=True)
        except FileNotFoundError:
            df_final = pd.DataFrame([student_data])
        
        # Sauvegarde avec séparateur correct
        df_final.to_csv("reponses.csv", sep=";", encoding="utf-8", index=False)
        st.success(f"Merci {prenom}, tes réponses ont été enregistrées !")

        # Calcul de la moyenne des scores par critère
        critere_scores = {critere: [] for critere in set(questions.values())}
        for q, critere in questions.items():
            critere_scores[critere].append(responses[q])

        avg_scores = {critere: sum(values) / len(values) for critere, values in critere_scores.items()}

        # Générer et afficher le PDF
        pdf_path = generate_pdf(prenom, nom, responses, avg_scores)
        st.success(f"PDF généré : {pdf_path}")
        with open(pdf_path, "rb") as file:
            st.download_button(label="Télécharger mon profil PDF", data=file, file_name=f"{prenom}_{nom}_profil.pdf", mime="application/pdf")

    else:
        st.warning("Merci de renseigner ton prénom et ton nom avant de valider.")

# --- Affichage des résultats (réservé à toi) ---
st.header("Analyse des résultats")
if st.checkbox("Afficher les résultats (Admin seulement)"):
    try:
        df_results = pd.read_csv("reponses.csv", sep=";", encoding="utf-8")
        st.write("Liste des participants :")
        st.dataframe(df_results[["Prénom", "Nom"]])

        # Sélection d'un élève pour afficher son profil
        selected_student = st.selectbox("Choisissez un élève :", df_results["Prénom"] + " " + df_results["Nom"])
        
        if selected_student:
            student_data = df_results[df_results["Prénom"] + " " + df_results["Nom"] == selected_student].iloc[0]
            scores = {q: student_data[q] for q in questions.keys()}

            # Calcul de la moyenne des réponses par critère
            critere_scores = {critere: [] for critere in set(questions.values())}
            for q, critere in questions.items():
                critere_scores[critere].append(scores[q])

            avg_scores = {critere: sum(values) / len(values) for critere, values in critere_scores.items()}

            # Affichage du graphique radar
            labels = list(avg_scores.keys())
            values = list(avg_scores.values())

            fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'projection': 'polar'})
            angles = [n / float(len(labels)) * 2 * 3.14159 for n in range(len(labels))]
            ax.set_xticks(angles)
            ax.set_xticklabels(labels)

            values += values[:1]
            angles += angles[:1]
            ax.plot(angles, values, 'o-', linewidth=2)
            ax.fill(angles, values, alpha=0.25)

            st.pyplot(fig)

    except:
        st.error("Aucune réponse enregistrée encore.")

import streamlit as st
import pandas as pd
import re

def clean_double_text(text):
    """
    Si un texte est répété deux fois collées, ex: "Band DirectorBand Director", on garde une seule fois.
    """
    # ex: "Band DirectorBand Director"
    # on teste si moitié moitié identique
    half = len(text) // 2
    if len(text) % 2 == 0 and text[:half] == text[half:]:
        return text[:half].strip()
    return text.strip()

def parse_linkedin_experience_v2(text):
    blocs = re.split(r'Logo de ', text)
    experiences = []

    for bloc in blocs[1:]:  # ignorer tout avant 1er Logo de
        lines = [l.strip() for l in bloc.strip().split('\n') if l.strip()]
        entreprise = lines[0]

        # Ligne poste = ligne juste après entreprise
        # On récupère la 1ère ligne qui contient une répétition (poste poste)
        poste = None
        for line in lines[1:4]:  # en général dans les 3 lignes max
            cleaned = clean_double_text(line)
            if cleaned != entreprise and len(cleaned) > 0:
                poste = cleaned
                break

        # Chercher les dates dans les lignes suivantes (après poste)
        date_debut = None
        date_fin = None
        duree = None
        # Les dates sont dans une ligne contenant un pattern "mois année - aujourd’hui" ou "mois année - mois année"
        for line in lines[2:8]:  # fenêtre pour trouver dates
            # nettoyer doublons de date
            parts = re.split(r'De\s', line)
            date_line = parts[0].strip()

            # regex date de début-fin
            m = re.search(r'(\w+\.? \d{4})\s*-\s*(aujourd’hui|\w+\.? \d{4})', date_line)
            if m:
                date_debut = m.group(1)
                date_fin = m.group(2)
                # extra durée
                duree_search = re.search(r'·\s*([\d\w\s]+)$', date_line)
                duree = duree_search.group(1).strip() if duree_search else None
                break

        # Chercher description (lignes débutant par "-")
        description_lines = [l.lstrip('- ').strip() for l in lines if l.startswith('-')]
        description = " | ".join(description_lines) if description_lines else None

        experiences.append({
            "Entreprise": entreprise,
            "Poste": poste,
            "Date début": date_debut,
            "Date fin": date_fin,
            "Durée": duree,
            "Description": description
        })

    return experiences


st.title("Parser LinkedIn Expérience - V2")

input_text = st.text_area("Colle ici le texte de la section expérience LinkedIn :", height=350)

if st.button("Parser"):
    if input_text.strip():
        data = parse_linkedin_experience_v2(input_text)
        df = pd.DataFrame(data)
        st.dataframe(df)
    else:
        st.warning("Merci de coller un texte à parser.")

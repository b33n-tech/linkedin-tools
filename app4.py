import streamlit as st
import pandas as pd
import re
from datetime import datetime

def parse_linkedin_experience(text):
    # Séparer en blocs d'expérience via un pattern simple: logo + poste + entreprise + dates
    # En pratique ici, on découpe par "Logo de" ou "Logo de " pour détecter début expérience
    blocs = re.split(r'Logo de ', text)
    experiences = []

    for bloc in blocs[1:]:  # le premier avant le premier "Logo de" est vide/inutile
        lines = bloc.strip().split('\n')
        # Extrait entreprise : 1ere ligne (après "Logo de ")
        entreprise = lines[0].strip()

        # On cherche ensuite le ou les postes, on essaie d'identifier ligne(s) poste, type contrat, dates, description
        poste = None
        contrat = None
        date_debut = None
        date_fin = None
        duree = None
        localisation = None
        description = []

        # On parcourt les lignes suivantes pour trouver des infos
        for i, line in enumerate(lines[1:], start=1):
            line = line.strip()

            # Poste : souvent 1ère ligne après entreprise qui n'est pas "Stage", "Temps plein" etc
            # Parfois doublon poste poste (ex: InternIntern), on fait un fix simple
            if not poste and line and not re.search(r'Stage|Temps plein|CDI|CDD|contract|intern|full[- ]time', line, re.I):
                # retirer doublons de mots adjacents, ex: "InternIntern"
                match = re.match(r'([A-Za-z\s\-&]+)\1', line)
                if match:
                    poste = match.group(1).strip()
                else:
                    poste = line

            # Type contrat - s'il y a
            if re.search(r'Stage|Temps plein|CDI|CDD|contract|intern|full[- ]time', line, re.I):
                contrat = line

            # Dates : on peut tenter un pattern date simple: ex: "juil. 2025 - aujourd’hui · 1 mois"
            date_match = re.search(r'(\w+\.? \d{4})\s*-\s*(aujourd’hui|\w+\.? \d{4})', line)
            if date_match:
                date_debut_str = date_match.group(1)
                date_fin_str = date_match.group(2)
                date_debut = date_debut_str
                date_fin = date_fin_str

            # Localisation (ex: adresse souvent après date)
            if re.match(r'\d+ .*', line):
                localisation = line

            # Description : lignes avec "-"
            if line.startswith('-'):
                description.append(line.strip('- ').strip())

        experiences.append({
            'Entreprise': entreprise,
            'Poste': poste,
            'Type contrat': contrat,
            'Date début': date_debut,
            'Date fin': date_fin,
            'Localisation': localisation,
            'Description': " | ".join(description) if description else None
        })

    return experiences

st.title("Parsing LinkedIn Experience")

input_text = st.text_area("Colle ici le texte de la section expérience LinkedIn :", height=300)

if st.button("Parser"):
    if input_text.strip():
        results = parse_linkedin_experience(input_text)
        df = pd.DataFrame(results)
        st.write("Expériences extraites :")
        st.dataframe(df)
    else:
        st.warning("Merci de coller un texte à parser.")

import streamlit as st
import pandas as pd
import re

def extract_name(text):
    # Cherche un nom répété deux fois côte à côte (ex : Asmir KhanAsmir Khan)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for i in range(len(lines) - 1):
        if lines[i] == lines[i+1]:
            return lines[i]
    return "Nom inconnu"

def extract_experience_section(text):
    # Isole la section entre "ExpérienceExpérience" et "FormationFormation"
    match = re.search(r'ExpérienceExpérience(.*?)FormationFormation', text, re.DOTALL)
    return match.group(1) if match else ""

def clean_double_text(text):
    """Supprime les répétitions exactes collées ex: 'InternIntern' → 'Intern'"""
    half = len(text) // 2
    return text[:half] if len(text) % 2 == 0 and text[:half] == text[half:] else text

def parse_experiences(section_text):
    experiences = []
    blocs = re.split(r'Logo de ', section_text)
    
    for bloc in blocs[1:]:  # Skip the first empty split
        lines = [l.strip() for l in bloc.strip().split('\n') if l.strip()]
        entreprise = lines[0] if lines else ""

        # Poste : ligne suivante, avec doublon probable
        poste = clean_double_text(lines[1]) if len(lines) > 1 else ""

        # Contrat + dates : ligne suivante
        type_contrat = ""
        date_debut = ""
        date_fin = ""
        duree = ""
        if len(lines) > 2:
            contrat_line = lines[2]
            contrat_match = re.search(r'·\s*(Stage|Temps plein|Temps partiel|CDI|CDD)', contrat_line, re.I)
            type_contrat = contrat_match.group(1) if contrat_match else ""

            # Dates
            date_match = re.search(r'(\w+\.? \d{4})\s*-\s*(aujourd’hui|\w+\.? \d{4})', contrat_line, re.I)
            if date_match:
                date_debut = date_match.group(1)
                date_fin = date_match.group(2)

            # Durée
            duree_match = re.search(r'·\s*(\d+.*)$', contrat_line)
            if duree_match:
                duree = duree_match.group(1)

        # Description (lignes suivantes commençant par un tiret)
        description_lines = [l.strip('- ').strip() for l in lines[3:] if l.startswith('-')]
        description = " | ".join(description_lines) if description_lines else ""

        experiences.append({
            "Entreprise": entreprise,
            "Poste": poste,
            "Type de contrat": type_contrat,
            "Date début": date_debut,
            "Date fin": date_fin,
            "Durée": duree,
            "Description": description
        })

    return experiences

# STREAMLIT UI
st.title("🔍 Parser de profil LinkedIn (copié/collé complet)")

text_input = st.text_area("Collez ici tout le texte LinkedIn (Ctrl+A → Ctrl+C → Ctrl+V)", height=400)

if st.button("Analyser le profil"):
    if not text_input.strip():
        st.warning("Merci de coller un texte LinkedIn.")
    else:
        nom = extract_name(text_input)
        st.markdown(f"### 👤 Profil détecté : **{nom}**")

        section_experience = extract_experience_section(text_input)
        if not section_experience:
            st.error("Section Expérience introuvable.")
        else:
            data = parse_experiences(section_experience)
            df = pd.DataFrame(data)
            st.markdown("### 🧾 Expériences extraites :")
            st.dataframe(df)

            # Option d'export
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Télécharger en CSV", csv, "experiences_linkedin.csv", "text/csv")

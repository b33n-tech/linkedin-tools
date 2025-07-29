import streamlit as st
import pandas as pd
import re
import io

def extract_name(text):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for i in range(len(lines) - 1):
        if lines[i] == lines[i+1]:
            return lines[i]
    return "Nom inconnu"

def extract_experience_section(text):
    match = re.search(r'ExpérienceExpérience(.*?)FormationFormation', text, re.DOTALL)
    return match.group(1) if match else ""

def clean_double_text(text):
    half = len(text) // 2
    return text[:half] if len(text) % 2 == 0 and text[:half] == text[half:] else text

def parse_experiences(section_text):
    experiences = []
    blocs = re.split(r'Logo de ', section_text)
    for bloc in blocs[1:]:
        lines = [l.strip() for l in bloc.strip().split('\n') if l.strip()]
        entreprise = lines[0] if lines else ""
        poste = clean_double_text(lines[1]) if len(lines) > 1 else ""
        type_contrat = ""
        date_debut = ""
        date_fin = ""
        duree = ""
        if len(lines) > 2:
            contrat_line = lines[2]
            contrat_match = re.search(r'·\s*(Stage|Temps plein|Temps partiel|CDI|CDD)', contrat_line, re.I)
            type_contrat = contrat_match.group(1) if contrat_match else ""
            date_match = re.search(r'(\w+\.? \d{4})\s*-\s*(aujourd’hui|\w+\.? \d{4})', contrat_line, re.I)
            if date_match:
                date_debut = date_match.group(1)
                date_fin = date_match.group(2)
            duree_match = re.search(r'·\s*(\d+.*)$', contrat_line)
            if duree_match:
                duree = duree_match.group(1)
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

# Initialisation stockage en session pour profils multiples
if "profiles_data" not in st.session_state:
    st.session_state.profiles_data = []  # Liste de dict {name, df}

st.title("🔍 Parser LinkedIn multi-profils (copié/collé)")

text_input = st.text_area("Collez ici tout le texte LinkedIn du profil à analyser", height=400)

if st.button("Analyser ce profil"):
    if not text_input.strip():
        st.warning("Merci de coller un texte LinkedIn.")
    else:
        nom = extract_name(text_input)
        section_exp = extract_experience_section(text_input)
        if not section_exp:
            st.error("Section Expérience introuvable.")
        else:
            data = parse_experiences(section_exp)
            df = pd.DataFrame(data)
            # Sauvegarde dans session
            st.session_state.profiles_data.append({"name": nom, "df": df})
            st.success(f"Profil '{nom}' analysé et ajouté.")

if st.session_state.profiles_data:
    st.markdown("### Profils analysés :")
    for i, prof in enumerate(st.session_state.profiles_data):
        st.markdown(f"**{i+1}. {prof['name']}**")
        st.dataframe(prof['df'])

    # Export XLSX multi-feuilles
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        for prof in st.session_state.profiles_data:
            # Nom de feuille limité à 31 caractères Excel + sans caractères invalides
            sheet_name = prof['name'][:31].replace('/', '-').replace('\\', '-')
            prof['df'].to_excel(writer, sheet_name=sheet_name, index=False)
    st.download_button(
        label="📥 Télécharger tous les profils en XLSX (feuilles séparées)",
        data=buffer.getvalue(),
        file_name="profils_linkedin_multi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Export CSV du dernier profil uniquement
    last = st.session_state.profiles_data[-1]
    csv = last['df'].to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"📥 Télécharger le dernier profil ({last['name']}) en CSV",
        data=csv,
        file_name=f"profil_{last['name']}.csv",
        mime="text/csv"
    )

# Bouton pour tout réinitialiser
if st.button("🗑️ Réinitialiser tous les profils analysés"):
    st.session_state.profiles_data = []
    st.experimental_rerun()

import streamlit as st
import pandas as pd
import re
import io

def extract_full_experience_section(text):
    match = re.search(r'ExpérienceExpérience(.*?)FormationFormation', text, re.DOTALL)
    if match:
        return match.group(1)
    else:
        return ""

def extract_name_from_experience(section_text):
    lines = [l.strip() for l in section_text.split('\n') if l.strip()]
    for i in range(len(lines) - 1):
        if lines[i] == lines[i+1]:
            return lines[i]
    return "Nom inconnu"

def clean_double_text(text):
    half = len(text) // 2
    return text[:half] if len(text) % 2 == 0 and text[:half] == text[half:] else text

def extract_year(date_str):
    # Cherche 4 chiffres consécutifs dans la date (ex: "mars 2021" → 2021)
    match = re.search(r'(\d{4})', date_str)
    return match.group(1) if match else ""

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
        if len(lines) > 2:
            contrat_line = lines[2]
            contrat_match = re.search(r'·\s*(Stage|Temps plein|Temps partiel|CDI|CDD)', contrat_line, re.I)
            type_contrat = contrat_match.group(1) if contrat_match else ""
            date_match = re.search(r'(\w+\.? \d{4})\s*-\s*(aujourd’hui|\w+\.? \d{4})', contrat_line, re.I)
            if date_match:
                date_debut = date_match.group(1)
                date_fin = date_match.group(2)
        # Plus de description ni durée
        experiences.append({
            "Entreprise": entreprise,
            "Poste": poste,
            "Type de contrat": type_contrat,
            "Date début": date_debut,
            "Date fin": date_fin,
            "Année début": extract_year(date_debut),
            "Année fin": extract_year(date_fin)
        })
    return experiences

if "profiles_data" not in st.session_state:
    st.session_state.profiles_data = []

st.title("🔍 Parser LinkedIn multi-profils (copié/collé)")

url_input = st.text_input("URL du profil LinkedIn (optionnel)")
text_input = st.text_area("Collez ici tout le texte LinkedIn du profil à analyser", height=400)

if st.button("Analyser ce profil"):
    if not text_input.strip():
        st.warning("Merci de coller un texte LinkedIn.")
    else:
        section_exp = extract_full_experience_section(text_input)
        if not section_exp:
            st.error("Section Expérience introuvable.")
        else:
            nom = extract_name_from_experience(section_exp)
            data = parse_experiences(section_exp)
            df = pd.DataFrame(data)
            st.session_state.profiles_data.append({
                "name": nom,
                "url": url_input.strip() if url_input else "",
                "df": df
            })
            st.success(f"Profil '{nom}' analysé et ajouté.")

if st.session_state.profiles_data:
    st.markdown("### Profils analysés :")
    for i, prof in enumerate(st.session_state.profiles_data):
        st.markdown(f"**{i+1}. {prof.get('name', 'Nom inconnu')}** — URL: {prof.get('url', '') or 'Non renseignée'}")
        st.dataframe(prof['df'])

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        recap_df = pd.DataFrame([
            {"Nom": p.get('name', 'Nom inconnu'), "URL": p.get('url', '')}
            for p in st.session_state.profiles_data
        ])
        recap_df.to_excel(writer, sheet_name="Récap Profils", index=False)

        for prof in st.session_state.profiles_data:
            sheet_name = prof.get('name', 'Profil')[:31].replace('/', '-').replace('\\', '-')
            prof['df'].to_excel(writer, sheet_name=sheet_name, index=False)

    st.download_button(
        label="📥 Télécharger tous les profils en XLSX (Récap + CVs)",
        data=buffer.getvalue(),
        file_name="profils_linkedin_multi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    last = st.session_state.profiles_data[-1]
    csv = last['df'].to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"📥 Télécharger le dernier profil ({last.get('name', 'Nom inconnu')}) en CSV",
        data=csv,
        file_name=f"profil_{last.get('name', 'profil')}.csv",
        mime="text/csv"
    )

if st.button("🗑️ Réinitialiser tous les profils analysés"):
    st.session_state.profiles_data = []
    st.experimental_rerun()

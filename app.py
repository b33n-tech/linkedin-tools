import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Extractor LinkedIn vers Excel")

st.title("📄 LinkedIn ➜ Excel Extractor")
st.write("Copiez-collez ici un profil LinkedIn brut (texte copié directement depuis la page).")

input_text = st.text_area("📝 Coller ici le texte brut du profil", height=400)

def extract_experiences(text):
    experiences = []
    blocks = re.split(r'\n\s*\n', text)  # Séparation brute en blocs
    for block in blocks:
        if any(word in block for word in ['févr.', 'janv.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.', 'aujourd’hui']):
            poste = re.findall(r'^(.+?)\n', block)
            poste = poste[0].strip() if poste else ""
            dates = re.findall(r'(de|Du)\s([^\n]+?)\sà\s([^\n]+?)\s·\s([0-9a-zA-Z\s]+)', block)
            if dates:
                debut = dates[0][1]
                fin = dates[0][2]
                durée = dates[0][3]
            else:
                debut, fin, durée = "", "", ""
            contrat = 'CDI' if 'CDI' in block else ('CDD' if 'CDD' in block else '')
            employeur = ""
            lines = block.split('\n')
            for line in lines:
                if "University" in line or "Company" in line or "Lab" in line:
                    employeur = line.strip()
                    break
            experiences.append({
                'Poste': poste,
                'Employeur': employeur,
                'Type de contrat': contrat,
                'Date de début': debut,
                'Date de fin': fin,
                'Durée': durée
            })
    return pd.DataFrame(experiences)

def extract_education(text):
    education = []
    edu_blocks = re.findall(r'(.+University.+|.+École.+|.+Institute.+)\n(.+)\n([0-9]{4}.*[0-9]{4}|[0-9]{4} - aujourd’hui)', text)
    for school, degree, date in edu_blocks:
        education.append({
            'Établissement': school.strip(),
            'Diplôme': degree.strip(),
            'Période': date.strip()
        })
    return pd.DataFrame(education)

def extract_languages(text):
    langs = []
    matches = re.findall(r'([A-Za-zéèàêî ]+)\n(Capacité.*?|Compétence.*?|Bilingue.*?|Natif.*?)\n', text)
    for lang, level in matches:
        langs.append({
            'Langue': lang.strip(),
            'Niveau': level.strip()
        })
    return pd.DataFrame(langs)

def extract_awards(text):
    awards = []
    matches = re.findall(r'(.+Award.+)\n(.+)\n(janv\.|févr\.|mars|avr\.|mai|juin|juil\.|août|sept\.|oct\.|nov\.|déc\.) [0-9]{4}', text)
    for award, issuer, _ in matches:
        awards.append({
            'Distinction': award.strip(),
            'Émis par': issuer.strip()
        })
    return pd.DataFrame(awards)

def to_excel(dataframes: dict):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    for name, df in dataframes.items():
        df.to_excel(writer, sheet_name=name[:31], index=False)
    writer.close()
    output.seek(0)
    return output

if st.button("📤 Extraire et générer Excel"):
    if not input_text.strip():
        st.warning("Veuillez coller un texte de profil LinkedIn.")
    else:
        st.success("✅ Extraction en cours...")
        dfs = {
            "Expérience": extract_experiences(input_text),
            "Formation": extract_education(input_text),
            "Langues": extract_languages(input_text),
            "Distinctions": extract_awards(input_text)
        }

        excel_file = to_excel(dfs)

        st.download_button(
            label="📥 Télécharger le fichier Excel",
            data=excel_file,
            file_name="linkedin_profile_extract.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

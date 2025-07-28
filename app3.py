import streamlit as st
import pandas as pd
from io import BytesIO
import re

st.title("Extraction profils LinkedIn - Organisation (Personnes)")

def is_name(line):
    # Détecte si une ligne ressemble à un nom complet (2+ mots commençant par majuscule)
    # Exemple simple : "Ieva Gaigala"
    return bool(re.match(r"^[A-ZÀ-Ÿ][a-zà-ÿA-ZÀ-Ÿ\-']+( [A-ZÀ-Ÿ][a-zà-ÿA-ZÀ-Ÿ\-']+)+$", line.strip()))

def extract_profiles(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    profiles = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        # Ignore explicit "Utilisateur LinkedIn" profils
        if line == "Utilisateur LinkedIn":
            i += 1
            # On traite "Utilisateur LinkedIn" comme nom de profil (tu peux changer ici si besoin)
            name = line
            desc_lines = []
            # Collecte jusqu'au prochain nom ou fin
            i_start = i
            while i < n and not is_name(lines[i]):
                desc_lines.append(lines[i])
                i += 1
            profiles.append({"Profil": name, "Description": " | ".join(desc_lines)})
            continue

        if is_name(line):
            name = line

            # Si ligne suivante est la même => doublon immédiat, on saute la suivante
            if i + 1 < n and lines[i + 1] == line:
                i += 2
            else:
                i += 1

            desc_lines = []
            while i < n:
                if is_name(lines[i]) or lines[i] == "Utilisateur LinkedIn":
                    break
                desc_lines.append(lines[i])
                i += 1

            description = " | ".join(desc_lines)
            profiles.append({"Profil": name, "Description": description})
        else:
            i += 1
    return profiles

input_text = st.text_area("Collez le texte brut de la page 'Personnes' LinkedIn", height=400)

if st.button("Extraire et générer XLSX"):
    if not input_text.strip():
        st.warning("Veuillez coller le texte d'abord.")
    else:
        data = extract_profiles(input_text)
        if not data:
            st.warning("Aucun profil détecté. Assurez-vous que le texte est complet et formaté comme attendu.")
        else:
            df = pd.DataFrame(data)

            # Générer Excel en mémoire
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name="Profils")

            excel_data = output.getvalue()

            st.success(f"{len(data)} profils extraits.")

            st.download_button(
                label="Télécharger le fichier Excel",
                data=excel_data,
                file_name="linkedin_organisation_profils.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

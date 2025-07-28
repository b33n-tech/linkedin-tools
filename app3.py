import streamlit as st
import pandas as pd
from io import BytesIO
import re

st.title("Extraction profils LinkedIn - Organisation (Personnes)")

# Fonction qui extrait des profils et descriptions
def extract_profiles(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    profiles = []
    i = 0
    while i < len(lines):
        # Le nom est généralement une ligne seule (ex: "Ieva Gaigala")
        # On va détecter une ligne "Nom Prénom" ou au moins un mot avec une majuscule en début
        # puis on collecte les lignes suivantes comme description jusqu'à la prochaine ligne qui ressemble à un nom
        # ou la fin du texte.
        
        # Condition basique pour une ligne de nom : au moins un mot avec majuscule au début, peu de ponctuation
        if re.match(r"^[A-ZÀ-Ÿ][a-zà-ÿA-ZÀ-Ÿ\-']+( [A-ZÀ-Ÿ][a-zà-ÿA-ZÀ-Ÿ\-']+)+$", lines[i]):
            name = lines[i]
            i += 1
            desc_lines = []
            while i < len(lines):
                # Stoppe si on trouve une nouvelle ligne ressemblant à un nom
                if re.match(r"^[A-ZÀ-Ÿ][a-zà-ÿA-ZÀ-Ÿ\-']+( [A-ZÀ-Ÿ][a-zà-ÿA-ZÀ-Ÿ\-']+)+$", lines[i]):
                    break
                desc_lines.append(lines[i])
                i += 1
            description = " | ".join(desc_lines)
            profiles.append({"Profil": name, "Description": description})
        else:
            i += 1
    return profiles

# Interface
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

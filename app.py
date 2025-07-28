import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.title("Extracteur de Profil LinkedIn vers Excel")

st.write("Copiez-collez le contenu brut d’un profil LinkedIn (ex: expériences, en-tête, abonnés...) ci-dessous 👇")

input_text = st.text_area("Contenu du profil LinkedIn copié :", height=400)

def extract_profile_summary(text):
    lines = text.splitlines()
    data = {
        "Nom ou ID LinkedIn": "",
        "Titre": "",
        "Nombre d’abonnés": "",
        "Nombre de relations": "",
        "Autre info": []
    }

    for line in lines:
        if "abonné" in line.lower():
            match = re.search(r"(\d+[\d\s]*)\s*abonné", line.lower())
            if match:
                data["Nombre d’abonnés"] = match.group(1).strip()

        elif "relation" in line.lower():
            match = re.search(r"(\d+[\d\s]*)\s*relation", line.lower())
            if match:
                data["Nombre de relations"] = match.group(1).strip()

        elif not data["Titre"] and 2 < len(line) < 100 and not re.search(r'\d', line):
            data["Titre"] = line.strip()

        elif line.strip():
            data["Autre info"].append(line.strip())

    return pd.DataFrame([data])

def extract_experiences(text):
    experiences = []
    blocks = text.split("\n\n")

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue

        job = {"Poste": "", "Dates": "", "Établissement": "", "Type contrat": "", "Lieu": ""}

        for line in lines:
            if re.search(r'(CDI|CDD|Stage|Alternance|Temps plein|Temps partiel)', line, re.IGNORECASE):
                job["Type contrat"] = line.strip()
            elif re.search(r'\d{4}', line):
                job["Dates"] = line.strip()
            elif not job["Poste"]:
                job["Poste"] = line.strip()
            elif not job["Établissement"]:
                job["Établissement"] = line.strip()
            elif "Oulu" in line or "France" in line or "," in line:
                job["Lieu"] = line.strip()

        if job["Poste"] or job["Dates"]:
            experiences.append(job)

    return pd.DataFrame(experiences)

if st.button("📄 Générer le fichier Excel"):
    if input_text.strip():
        profile_df = extract_profile_summary(input_text)
        experience_df = extract_experiences(input_text)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            profile_df.to_excel(writer, sheet_name='Profil', index=False)
            experience_df.to_excel(writer, sheet_name='Expériences', index=False)

        st.success("✅ Fichier généré avec succès !")
        st.download_button(
            label="📥 Télécharger le fichier Excel",
            data=output.getvalue(),
            file_name="profil_linkedin.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⛔ Merci de coller d'abord un contenu de profil LinkedIn.")

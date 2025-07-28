import streamlit as st
import pandas as pd
import re
import io

st.title("Extracteur de profil LinkedIn en Excel (1 ligne synthétique)")

profile_text = st.text_area("📋 Collez ici le texte brut du profil LinkedIn", height=400)

def extract_info(text):
    lines = text.split('\n')
    data = {
        "Nom": "",
        "Titre": "",
        "Localisation": "",
        "Abonnés": "",
        "Relations": "",
        "Poste actuel": "",
        "Employeur": "",
        "Contrat": "",
        "Dates": "",
        "Lieu": "",
    }

    # Nettoyage de lignes vides
    lines = [l.strip() for l in lines if l.strip()]

    # Nom
    if lines:
        data["Nom"] = lines[0]

    # Titre professionnel
    for line in lines[1:4]:
        if len(line.split()) > 3:
            data["Titre"] = line
            break

    # Nombre d'abonnés / relations
    for line in lines:
        if "abonnés" in line.lower():
            data["Abonnés"] = re.search(r"(\d[\d\s]*) abonn", line).group(1).strip() if re.search(r"(\d[\d\s]*) abonn", line) else ""
        if "relations" in line.lower():
            data["Relations"] = re.search(r"(\d[\d\s]*) relations", line).group(1).strip() if re.search(r"(\d[\d\s]*) relations", line) else ""

    # Poste actuel
    poste_ligne = ""
    for i, line in enumerate(lines):
        if "professor" in line.lower() or "research" in line.lower() or "ceo" in line.lower() or "founder" in line.lower():
            poste_ligne = line
            # On cherche l’établissement juste après
            if i + 1 < len(lines):
                data["Employeur"] = lines[i + 1]
            break
    data["Poste actuel"] = poste_ligne

    # Contrat et dates
    for line in lines:
        if "CDI" in line or "CDD" in line or "Stage" in line or "Temps plein" in line:
            data["Contrat"] = line
        if re.search(r"(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc).*?\d{4}", line):
            data["Dates"] = line
        if re.search(r"[A-Z][a-z]+, [A-Z]", line) or "Finlande" in line or "France" in line:
            data["Lieu"] = line

    return data

if st.button("📄 Générer le fichier Excel"):
    if profile_text:
        extracted = extract_info(profile_text)
        df = pd.DataFrame([extracted])

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Profil LinkedIn')
            writer.save()
            st.download_button(
                label="📥 Télécharger le fichier Excel",
                data=buffer.getvalue(),
                file_name="profil_linkedin.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.warning("Merci de coller un profil avant de générer le fichier.")

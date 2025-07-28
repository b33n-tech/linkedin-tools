import streamlit as st
import pandas as pd
import re

st.title("Extracteur d'en-tête LinkedIn")

input_text = st.text_area("Collez ici l’en-tête LinkedIn", height=300)

if input_text:
    # Nettoyage initial
    clean_text = input_text.replace("\n", " ").strip()

    # Fonctions de détection
    def extract_name(text):
        match = re.search(r"^([A-Z][a-z]+\s+[A-Z][a-z]+)", text)
        return match.group(1).strip() if match else ""

    def extract_relation(text):
        match = re.search(r"(relation de \d+[e|ᵉ])", text)
        return match.group(1).strip() if match else ""

    def extract_title(text):
        # Titre souvent après le nom et la relation
        title_match = re.search(r"\d+[e|ᵉ]\s+(.*?)(?=(\d+ abonnés|Plus de \d+ relations|Coordonnées))", text)
        return title_match.group(1).strip() if title_match else ""

    def extract_location(text):
        match = re.search(r"([A-Za-zÀ-ÿ,\s]+Coordonnées)", text)
        return match.group(1).replace("Coordonnées", "").strip() if match else ""

    def extract_link(text):
        match = re.search(r"(https?://[^\s]+)", text)
        return match.group(1).strip() if match else ""

    def extract_followers(text):
        match = re.search(r"(\d[\d\s]* abonnés)", text)
        return match.group(1).strip() if match else ""

    def extract_connections(text):
        match = re.search(r"(Plus de \d+ relations)", text)
        return match.group(1).strip() if match else ""

    def extract_badge(text):
        if "Premium" in text:
            return "Premium"
        elif "badgeType" in text:
            return "Autre badge"
        else:
            return ""

    def extract_special_status(text):
        match = re.search(r"est une relation en commun", text)
        return "Relation en commun" if match else ""

    # Extraction
    data = {
        "Nom": extract_name(clean_text),
        "Relation": extract_relation(clean_text),
        "Titre": extract_title(clean_text),
        "Localisation": extract_location(clean_text),
        "Lien": extract_link(clean_text),
        "Abonnés": extract_followers(clean_text),
        "Relations": extract_connections(clean_text),
        "Badge": extract_badge(clean_text),
        "Autre Statut": extract_special_status(clean_text),
    }

    df = pd.DataFrame([data])
    st.dataframe(df)

    # Téléchargement
    @st.cache_data
    def convert_df(df):
        return df.to_excel(index=False, engine='openpyxl')

    excel_data = convert_df(df)
    st.download_button("📥 Télécharger le fichier Excel", excel_data, file_name="linkedin_en_tete.xlsx")

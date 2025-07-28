import streamlit as st
import pandas as pd
import re

st.title("Extracteur itératif de profils LinkedIn - nettoyage Relation & Titre")

# Initialisation mémoire session
if "profiles" not in st.session_state:
    st.session_state["profiles"] = []

def extract_name(text):
    match = re.search(r"^([A-Z][a-z]+\s+[A-Z][a-z]+)", text)
    return match.group(1).strip() if match else ""

def extract_relation(text):
    # Extrait uniquement "relation de 2e" ou similaire, sans "niveau 2e"
    match = re.search(r"(relation de \d+[e|ᵉ])", text, re.IGNORECASE)
    return match.group(1).strip() if match else ""

def extract_title(text):
    # On enlève la répétition "niveau 2e" en début de titre s'il y en a
    relation_pattern = r"(relation de \d+[e|ᵉ])"
    title_match = None

    relation_search = re.search(relation_pattern, text, re.IGNORECASE)
    if relation_search:
        start_pos = relation_search.end()
        substring = text[start_pos:].strip()
        # Suppression éventuelle de "niveau 2e" en début
        substring = re.sub(r"^niveau \d+[e|ᵉ]\s*", "", substring, flags=re.IGNORECASE)
        # Coupe avant "Coordonnées" ou "abonnés" ou "relations"
        end_cut = re.search(r"(Coordonnées|\d+ abonnés|Plus de \d+ relations)", substring)
        if end_cut:
            title_match = substring[:end_cut.start()].strip()
        else:
            title_match = substring.strip()
    else:
        title_match = ""

    return title_match

def extract_location(text):
    match = re.search(r"([A-Za-zÀ-ÿ,\s]+)Coordonnées", text)
    return match.group(1).strip() if match else ""

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

def parse_one_profile(text):
    clean_text = text.replace("\n", " ").strip()
    return {
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

with st.form("form_profile"):
    input_text = st.text_area("Collez un profil LinkedIn (en-tête)", height=300)
    submitted = st.form_submit_button("➕ Ajouter ce profil")

if submitted:
    if input_text.strip():
        profile_data = parse_one_profile(input_text)
        st.session_state["profiles"].append(profile_data)
        st.success("Profil ajouté !")
    else:
        st.warning("Merci de coller un profil valide.")

if st.session_state["profiles"]:
    st.write("### Profils ajoutés jusqu'à présent :")
    df = pd.DataFrame(st.session_state["profiles"])
    st.dataframe(df)

    def convert_df_to_excel(df):
        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    excel_data = convert_df_to_excel(df)
    st.download_button("📥 Télécharger tous les profils au format Excel", excel_data, file_name="linkedin_profiles.xlsx")
else:
    st.info("Collez un profil et cliquez sur Ajouter pour commencer.")

import streamlit as st
import pandas as pd
import re

st.title("Extracteur itératif de profils LinkedIn - version améliorée localisation")

# Initialisation mémoire session
if "profiles" not in st.session_state:
    st.session_state["profiles"] = []

def extract_name(text):
    match = re.search(r"^([A-Z][a-z]+\s+[A-Z][a-z]+)", text)
    return match.group(1).strip() if match else ""

def extract_relation(text):
    match = re.search(r"(relation de \d+[e|ᵉ])", text, re.IGNORECASE)
    return match.group(1).strip() if match else ""

def extract_title(text):
    relation_pattern = r"(relation de \d+[e|ᵉ])"
    title_match = None

    relation_search = re.search(relation_pattern, text, re.IGNORECASE)
    if relation_search:
        start_pos = relation_search.end()
        substring = text[start_pos:].strip()
        substring = re.sub(r"^niveau \d+[e|ᵉ]\s*", "", substring, flags=re.IGNORECASE)
        # On coupe avant "Coordonnées", "abonnés", "relations" s’ils apparaissent
        end_cut = re.search(r"(Coordonnées|\d+ abonnés|Plus de \d+ relations)", substring)
        if end_cut:
            title_match = substring[:end_cut.start()].strip()
        else:
            title_match = substring.strip()
    else:
        title_match = ""

    return title_match

def extract_location(text):
    # Essaie de détecter une localisation en fin de texte
    
    # On cherche la dernière portion après un pipe '|'
    parts = text.split('|')
    last_part = parts[-1].strip() if parts else ""
    
    if last_part and re.match(r"^[A-Za-zÀ-ÿ\s,.\-]+$", last_part) and len(last_part.split()) <= 6:
        return last_part
    
    # Sinon, cherche après un double espace
    double_space_split = re.split(r"\s{2,}", text)
    if len(double_space_split) > 1:
        candidate = double_space_split[-1].strip()
        if re.match(r"^[A-Za-zÀ-ÿ\s,.\-]+$", candidate) and len(candidate.split()) <= 6:
            return candidate

    # Sinon, cherche un motif de localisation à la fin (lettres, espaces, virgules, points, tirets)
    loc_match = re.search(r"([A-Za-zÀ-ÿ\s,.\-]{2,})$", text.strip())
    if loc_match:
        return loc_match.group(1).strip()
    
    return ""

def extract_link(text):
    match = re.search(r"(https?://[^\s]+)", text)
    return match.group(1).strip() if match else ""

def extract_followers(text):
    match = re.search(r"(\d[\d\s]* abonnés)", text)
    return match.group(1).strip() if match else ""

def extract_connections(text):
    match = re.search(r"(Plus de \d+ relations)", text)
    return match.group(1).strip() if match else ""

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

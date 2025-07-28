import streamlit as st
import pandas as pd
import re

st.title("Extracteur itératif de profils LinkedIn - version avec extraction pays")

# Initialisation mémoire session
if "profiles" not in st.session_state:
    st.session_state["profiles"] = []

def extract_name(text):
    match = re.search(r"^([A-ZÀ-Ÿ][a-zà-ÿ]+\s+[A-ZÀ-Ÿ][a-zà-ÿ]+)", text)
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

        coord_pos = substring.find("Coordonnées")
        if coord_pos != -1:
            substring = substring[:coord_pos].strip()

        if "|" in substring:
            substring = substring.rsplit("|", 1)[0].strip()

        substring = re.sub(r"^niveau \d+[e|ᵉ]\s*", "", substring, flags=re.IGNORECASE)
        
        title_match = substring.strip()
    else:
        title_match = ""

    return title_match

def extract_location(text):
    relation_pattern = r"(relation de \d+[e|ᵉ])"
    relation_search = re.search(relation_pattern, text, re.IGNORECASE)
    
    if relation_search:
        start_pos = relation_search.end()
        substring = text[start_pos:].strip()

        coord_pos = substring.find("Coordonnées")
        if coord_pos != -1:
            before_coord = substring[:coord_pos].strip()

            if "|" in before_coord:
                loc_candidate = before_coord.rsplit("|", 1)[-1].strip()
                if len(loc_candidate.split()) <= 6:
                    return loc_candidate

            parts = re.split(r"\s{2,}", before_coord)
            if len(parts) > 1:
                loc_candidate = parts[-1].strip()
                if len(loc_candidate.split()) <= 6:
                    return loc_candidate

            if len(before_coord.split()) <= 6:
                return before_coord
    
    loc_match = re.search(r"([A-Za-zÀ-ÿ\s,.\-]{2,})Coordonnées", text)
    if loc_match:
        return loc_match.group(1).strip()

    return ""

def extract_country(text):
    countries = [
        "Finlande", "France", "États-Unis", "Japon", "Allemagne", "Canada",
        "Royaume-Uni", "Espagne", "Italie", "Belgique", "Suisse", "Suède",
        "Norvège", "Danemark", "Pays-Bas", "Australie", "Chine", "Inde",
        "Brésil", "Mexique", "Russie", "Turquie"
    ]
    for country in countries:
        if country.lower() in text.lower():
            return country
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
    location = extract_location(clean_text)
    return {
        "Nom": extract_name(clean_text),
        "Relation": extract_relation(clean_text),
        "Titre": extract_title(clean_text),
        "Localisation": location,
        "Pays": extract_country(location),
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

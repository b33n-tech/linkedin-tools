import streamlit as st
import pandas as pd
import datetime
import re

REACTION_TYPES = ["like", "celebrate", "love", "funny", "insightful"]

def parse_reactions(raw_text):
    lines = [line.strip() for line in raw_text.splitlines() if line.strip() != ""]
    results = []
    i = 0
    while i < len(lines):
        reaction = lines[i].lower()
        if reaction not in REACTION_TYPES:
            i += 1
            continue
        i += 1
        
        if i >= len(lines):
            break
        name_line = lines[i]
        name = name_line.split("Voir le profil de")[0].strip()
        i += 1
        
        if i >= len(lines):
            position = ""
        else:
            position = lines[i]
            if not re.search(r"(network|niveau|et|\d+)", position, re.IGNORECASE):
                position = ""
            else:
                i += 1
        
        info_lines = []
        while i < len(lines) and lines[i].lower() not in REACTION_TYPES:
            info_lines.append(lines[i])
            i += 1
        
        info = " || ".join(info_lines)
        
        results.append({
            "Réaction": reaction,
            "Nom": name,
            "Position réseau": position,
            "Infos complémentaires": info
        })
    return results

def parse_post_header(raw_text):
    # Extraction auteur (première ligne)
    lines = [line.strip() for line in raw_text.splitlines() if line.strip() != ""]
    auteur = lines[0] if len(lines) > 0 else ""
    
    # Trouver la date relative (ex: "3 j", "2 sem", "1 mois", "5 h", "15 min")
    date_relative = ""
    for l in lines:
        match = re.search(r"(\d+)\s*(j|jour|jours|h|heure|heures|min|minute|minutes|sem|semaine|semaines|mois)", l)
        if match:
            date_relative = match.group(0)
            break
    
    # Extraire les premières lignes du post (après date, auteur etc.)
    # On prend par exemple les 3 premières lignes non vides après la date relative
    idx = 0
    for i, l in enumerate(lines):
        if date_relative in l:
            idx = i + 1
            break
    post_excerpt = " ".join(lines[idx:idx+3]) if idx+3 <= len(lines) else " ".join(lines[idx:])
    
    return auteur, date_relative, post_excerpt

def convert_relative_date_to_absolute(date_relative_str):
    today = datetime.datetime.now()
    if not date_relative_str:
        return ""
    
    # Parse number and unit
    m = re.match(r"(\d+)\s*(j|jour|jours|h|heure|heures|min|minute|minutes|sem|semaine|semaines|mois)", date_relative_str.lower())
    if not m:
        return ""
    
    num = int(m.group(1))
    unit = m.group(2)
    
    if unit in ["j", "jour", "jours"]:
        delta = datetime.timedelta(days=num)
    elif unit in ["h", "heure", "heures"]:
        delta = datetime.timedelta(hours=num)
    elif unit in ["min", "minute", "minutes"]:
        delta = datetime.timedelta(minutes=num)
    elif unit in ["sem", "semaine", "semaines"]:
        delta = datetime.timedelta(weeks=num)
    elif unit == "mois":
        # approx 30 days per month
        delta = datetime.timedelta(days=30*num)
    else:
        delta = datetime.timedelta(0)
    
    post_date = today - delta
    return post_date.strftime("%Y-%m-%d %H:%M")

# --- Streamlit app ---

st.title("Analyseur multi-posts LinkedIn avec ventilation des réactions")

if "data" not in st.session_state:
    st.session_state.data = []

with st.form("form_post"):
    st.markdown("### Colle ici les infos du post LinkedIn (auteur, date, contenu)")
    post_raw = st.text_area("Post brut", height=150)
    
    st.markdown("### Colle ici les réactions associées au post (texte brut)")
    reactions_raw = st.text_area("Réactions brut", height=200)
    
    submitted = st.form_submit_button("Ajouter ce post + réactions")

if submitted:
    if post_raw.strip() == "" or reactions_raw.strip() == "":
        st.warning("Merci de remplir les deux champs avant d'ajouter.")
    else:
        auteur, date_relative, post_excerpt = parse_post_header(post_raw)
        date_absolute = convert_relative_date_to_absolute(date_relative)
        reactions = parse_reactions(reactions_raw)
        
        # Pour chaque réaction, on ajoute les infos du post
        for r in reactions:
            r["Auteur post"] = auteur
            r["Date relative post"] = date_relative
            r["Date absolue post"] = date_absolute
            r["Extrait post"] = post_excerpt
        
        st.session_state.data.extend(reactions)
        st.success(f"Post ajouté avec {len(reactions)} réactions.")

if st.session_state.data:
    df_all = pd.DataFrame(st.session_state.data)
    
    st.markdown("### Données cumulées sur tous les posts")
    st.dataframe(df_all)
    
    # Statistique par post / réaction
    st.markdown("### Nombre de réactions par type (tous posts confondus)")
    counts = df_all["Réaction"].value_counts().reindex(REACTION_TYPES, fill_value=0)
    st.bar_chart(counts)
    
    # Option export Excel
    def to_excel(df):
        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Reactions")
        return output.getvalue()
    
    excel_data = to_excel(df_all)
    st.download_button(
        label="📥 Télécharger toutes les données en Excel",
        data=excel_data,
        file_name="linkedin_posts_reactions.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Ajoute un post avec ses réactions pour commencer l'analyse.")

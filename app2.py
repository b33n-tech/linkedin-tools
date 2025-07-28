import streamlit as st
import pandas as pd
import re

st.title("Analyseur de réactions LinkedIn")

REACTION_TYPES = ["like", "celebrate", "love", "funny", "insightful"]  # types courants de réactions LinkedIn

def parse_reactions(raw_text):
    lines = [line.strip() for line in raw_text.splitlines() if line.strip() != ""]
    
    results = []
    i = 0
    while i < len(lines):
        # 1) type de réaction
        reaction = lines[i].lower()
        if reaction not in REACTION_TYPES:
            i += 1
            continue
        i += 1
        
        # 2) nom (nettoyage pour enlever "Voir le profil de ...")
        if i >= len(lines):
            break
        name_line = lines[i]
        name = name_line.split("Voir le profil de")[0].strip()
        i += 1
        
        # 3) position réseau (ex: Out of network · 3e et +)
        if i >= len(lines):
            position = ""
        else:
            position = lines[i]
            if not re.search(r"(network|niveau|et|\d+)", position, re.IGNORECASE):
                position = ""
            else:
                i += 1
        
        # 4) infos complémentaires (jusqu'à la prochaine réaction ou fin)
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

with st.form("form_reactions"):
    raw_text = st.text_area("Collez les réactions LinkedIn (texte brut)", height=400)
    submitted = st.form_submit_button("Analyser")

if submitted and raw_text.strip():
    parsed = parse_reactions(raw_text)
    if parsed:
        df = pd.DataFrame(parsed)
        
        st.write("### Ventilation du nombre de réactions par type")
        counts = df["Réaction"].value_counts().reindex(REACTION_TYPES, fill_value=0)
        st.bar_chart(counts)
        
        st.write("### Tableau détaillé")
        st.dataframe(df)
        
        # Export Excel
        def to_excel(df):
            import io
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)
            return output.getvalue()
        
        excel_data = to_excel(df)
        st.download_button(
            label="📥 Télécharger les données en Excel",
            data=excel_data,
            file_name="linkedin_reactions.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Aucune réaction détectée, vérifie le format du texte collé.")
else:
    st.info("Colle le texte brut des réactions LinkedIn puis clique sur Analyser.")

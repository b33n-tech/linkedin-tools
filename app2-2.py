import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
from io import BytesIO

def parse_post(raw_text):
    """
    Extrait Auteur, Date relative, Date absolue, et Aperçu du post
    """
    lines = raw_text.strip().split("\n")

    auteur = None
    date_relative = None

    # Trouver la ligne auteur (première ligne non vide)
    for i, line in enumerate(lines):
        if line.strip():
            auteur = line.strip()
            start_idx = i + 1
            break
    else:
        return None  # pas trouvé

    if start_idx >= len(lines):
        return None

    date_line = lines[start_idx].strip()

    # Extraction propre de la date relative, sans la mention de visibilité
    # Ex : "3 j •", "Il y a 3 jours • Visible de tous sur LinkedIn et en dehors"
    date_relative = date_line.split("•")[0].strip()

    # Extraire date absolue approx
    match = re.search(r"Il y a\s*(\d+)\s*(jour|jours|j|heures|h|minutes|m)", date_relative)
    if match:
        number = int(match.group(1))
        unit = match.group(2)
    else:
        match = re.search(r"(\d+)\s*(j|h|m)", date_relative)
        if match:
            number = int(match.group(1))
            unit = match.group(2)
        else:
            number = None
            unit = None

    now = datetime.now()
    if number and unit:
        if unit.startswith("j"):
            date_abs = now - timedelta(days=number)
        elif unit.startswith("h"):
            date_abs = now - timedelta(hours=number)
        elif unit.startswith("m"):
            date_abs = now - timedelta(minutes=number)
        else:
            date_abs = None
    else:
        date_abs = None

    # Contenu post = lignes après la date_line
    post_content = lines[start_idx+1:]

    # Nettoyer toute ligne qui contient "Visible de tous sur LinkedIn"
    post_content = [l for l in post_content if not l.startswith("Visible de tous")]

    # Joindre les premières lignes (ex: 5) en aperçu, nettoyé de mentions superflues
    preview = " ".join(post_content[:5]).strip()

    return {
        "Auteur": auteur,
        "Date relative": date_relative,
        "Date absolue": date_abs.strftime("%Y-%m-%d %H:%M") if date_abs else "",
        "Aperçu post": preview
    }

def to_excel(posts_list):
    df = pd.DataFrame(posts_list)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Posts')
        writer.save()
    processed_data = output.getvalue()
    return processed_data

st.title("Analyseur LinkedIn Posts avec Réactions")

if 'posts_data' not in st.session_state:
    st.session_state.posts_data = []

# Zone de texte pour coller le post LinkedIn
raw_post_text = st.text_area("Collez ici le texte brut d'un post LinkedIn (avec auteur, date, contenu)")

if st.button("Ajouter ce post"):
    if raw_post_text.strip():
        parsed = parse_post(raw_post_text)
        if parsed:
            st.session_state.posts_data.append(parsed)
            st.success("Post ajouté !")
        else:
            st.error("Impossible de parser ce post, vérifiez la structure.")
    else:
        st.warning("Veuillez coller un texte non vide.")

if st.session_state.posts_data:
    st.subheader("Posts ajoutés")
    df_display = pd.DataFrame(st.session_state.posts_data)
    st.dataframe(df_display)

    excel_data = to_excel(st.session_state.posts_data)
    st.download_button(
        label="Télécharger Excel",
        data=excel_data,
        file_name="linkedin_posts.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if st.button("Réinitialiser tout"):
    st.session_state.posts_data = []
    st.experimental_rerun()

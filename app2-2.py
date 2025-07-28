import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
from io import BytesIO

def parse_post(raw_text):
    """
    Parse a raw LinkedIn post text with possible messy formatting:
    - Extracts Auteur
    - Extracts Date relative
    - Calculates Date absolue (approx)
    - Extracts preview text of post (without 'Visible de tous...' mention)
    """
    text = raw_text.strip()

    # 1) Extraire la date relative, souvent de la forme "Il y a 3 jours", "3 j", "5 j •"
    date_pattern = re.compile(r"(Il y a\s*\d+\s*(jours?|j|heures|h|minutes|m))|(\d+\s*(j|h|m))")
    date_match = date_pattern.search(text)

    if not date_match:
        return None

    date_relative = date_match.group(0)

    # 2) Séparer le texte autour de la date relative (tout avant = auteur, tout après = post)
    split_idx = date_match.start()

    before_date = text[:split_idx].strip()
    after_date = text[date_match.end():].strip()

    # Nettoyer l'auteur : retirer doublons (ex Ishaan PatilIshaan Patil)
    # On prend la première ligne "avant_date" sans répétition

    # Parfois auteur est écrit deux fois collé : Ishaan PatilIshaan Patil
    # Tentative simple : on prend le mot ou groupe de mots qui se répète (séparé par espace)
    words = before_date.split()
    if len(words) >= 2 and before_date.startswith(words[0]*2):
        auteur = words[0]
    else:
        # En général auteur est les premiers mots, on prend les 2 ou 3 premiers mots max pour le nom
        auteur = before_date.split("\n")[0]  # au cas il y a des sauts de ligne
        auteur = auteur.strip()

    # 3) Nettoyer le post (after_date)
    # Retirer mention "Visible de tous sur LinkedIn et en dehors" ou variantes similaires
    after_date = re.sub(r"Visible de tous sur LinkedIn.*", "", after_date, flags=re.DOTALL).strip()

    # Limiter l'aperçu à 300 caractères (ou 5 lignes max)
    preview = after_date[:300].replace("\n", " ").strip()

    # 4) Calcul date absolue (approx)
    number, unit = None, None
    num_match = re.search(r"\d+", date_relative)
    unit_match = re.search(r"(jour|jours|j|heure|heures|h|minute|minutes|m)", date_relative)
    if num_match and unit_match:
        number = int(num_match.group())
        unit = unit_match.group()
    now = datetime.now()
    if number is not None and unit is not None:
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

    date_abs_str = date_abs.strftime("%Y-%m-%d %H:%M") if date_abs else ""

    return {
        "Auteur": auteur,
        "Date relative": date_relative,
        "Date absolue": date_abs_str,
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

st.title("Analyseur LinkedIn Posts avec Réactions - Version robuste")

if 'posts_data' not in st.session_state:
    st.session_state.posts_data = []

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

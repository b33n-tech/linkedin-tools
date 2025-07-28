import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
import re

st.set_page_config(page_title="Analyse LinkedIn Posts & Réactions", layout="wide")

def parse_post(raw_text):
    """
    Extrait Auteur, Date relative, Date absolue, et Premières lignes du post
    """
    lines = raw_text.strip().split("\n")
    # Nettoyer première ligne "Il y a X jours • Visible de tous ..."
    # Puis Auteur est première ligne avant ce bloc
    # On suppose format copié : 
    # Auteur (ex: Arthur AuboeufArthur Auboeuf)
    # ligne date / visibilité : ex "3 j • " ou "Il y a 3 jours • Visible de tous sur LinkedIn et en dehors"
    # puis lignes de texte post

    # Identifier la ligne auteur : la première ligne non vide
    auteur = None
    date_relative = None
    post_lines = []
    # On va parser ligne par ligne
    # Exemple copypaste souvent donne Auteur en première ligne, 
    # puis ligne date (ex: "3 j •" ou "Il y a 3 jours • Visible ...")
    # puis contenu post

    for i, line in enumerate(lines):
        if line.strip():
            auteur = line.strip()
            start_idx = i + 1
            break
    else:
        return None  # pas trouvé

    # Chercher la ligne date relative et visibilité (souvent juste après auteur)
    if start_idx >= len(lines):
        return None
    date_line = lines[start_idx].strip()

    # Extraire date relative (ex: "3 j", "Il y a 3 jours")
    # Utiliser regex
    # Plusieurs formats possibles, on cherche "Il y a X jours" ou "3 j" ou "3h"
    match = re.search(r"Il y a\s*(\d+)\s*(jour|jours|j|heures|h|minutes|m)", date_line)
    if match:
        number = int(match.group(1))
        unit = match.group(2)
    else:
        # essayer format court ex "3 j •"
        match = re.search(r"(\d+)\s*(j|h|m)", date_line)
        if match:
            number = int(match.group(1))
            unit = match.group(2)
        else:
            # date non détectée
            number = None
            unit = None

    # Calcul date absolue (approx), avec timezone = maintenant en UTC +2 par ex
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

    # Extraire contenu post à partir de la ligne après date_line
    post_content = lines[start_idx+1:]
    # Enlever mentions "Visible de tous sur LinkedIn et en dehors" si présent en début
    if post_content and post_content[0].startswith("Visible de tous"):
        post_content = post_content[1:]
    # On peut prendre les 3-5 premières lignes comme "aperçu"
    preview = " ".join(post_content[:5]).strip()

    return {
        "Auteur": auteur,
        "Date relative": date_line,
        "Date absolue": date_abs.strftime("%Y-%m-%d %H:%M") if date_abs else "",
        "Aperçu post": preview
    }


def parse_reactions(raw_text):
    """
    Extrait liste des réactions en dict avec : 
    - Type réaction
    - Nom
    - Position dans réseau (ex: 2e, 3e, Out of network)
    - Infos (tout ce qui suit)
    """
    lines = [l.strip() for l in raw_text.strip().split("\n") if l.strip()]
    reaction_types = ["like", "love", "celebrate", "funny", "support"]
    data = []
    i = 0
    while i < len(lines):
        line = lines[i].lower()
        if line in reaction_types:
            reaction = line
            i += 1
            if i >= len(lines):
                break
            # Nom (on veut seulement la partie avant "Voir le profil de")
            name_line = lines[i]
            name = name_line.split("Voir le profil de")[0].strip()
            i += 1
            if i >= len(lines):
                break
            position_line = lines[i]
            # Ex: "Out of network · 3e et +"
            position = position_line
            i += 1
            if i >= len(lines):
                break
            info_line = lines[i]
            info = info_line
            i += 1
            data.append({
                "Type réaction": reaction,
                "Nom": name,
                "Position dans réseau": position,
                "Infos": info
            })
        else:
            i += 1
    return data

def to_excel(posts, reactions):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_posts = pd.DataFrame(posts)
        df_reactions = pd.DataFrame(reactions)

        df_posts.to_excel(writer, index=False, sheet_name="Posts")
        df_reactions.to_excel(writer, index=False, sheet_name="Réactions")

    return output.getvalue()


if "posts_data" not in st.session_state:
    st.session_state.posts_data = []

if "reactions_data" not in st.session_state:
    st.session_state.reactions_data = []

st.title("Analyse LinkedIn Posts & Réactions")

# --- Input Post ---
st.header("Ajouter un post LinkedIn")
post_text = st.text_area("Collez le texte complet du post LinkedIn (auteur, date relative, contenu)", height=150)
if st.button("Ajouter ce post"):
    parsed_post = parse_post(post_text)
    if parsed_post:
        st.session_state.posts_data.append(parsed_post)
        st.success("Post ajouté.")
    else:
        st.error("Impossible d'analyser ce post. Vérifiez le format.")

if st.session_state.posts_data:
    st.subheader("Posts ajoutés")
    st.dataframe(pd.DataFrame(st.session_state.posts_data))

# --- Input Reactions ---
st.header("Ajouter les réactions LinkedIn d'un post")
reaction_text = st.text_area("Collez le texte complet des réactions (format : type réaction, nom, position, infos)", height=250)
if st.button("Ajouter ces réactions"):
    parsed_reactions = parse_reactions(reaction_text)
    if parsed_reactions:
        st.session_state.reactions_data.extend(parsed_reactions)
        st.success(f"{len(parsed_reactions)} réactions ajoutées.")
    else:
        st.error("Aucune réaction détectée. Vérifiez le format.")

if st.session_state.reactions_data:
    st.subheader("Réactions ajoutées")
    st.dataframe(pd.DataFrame(st.session_state.reactions_data))

# --- Export Excel ---
if st.session_state.posts_data or st.session_state.reactions_data:
    st.header("Télécharger les données")
    excel_bytes = to_excel(st.session_state.posts_data, st.session_state.reactions_data)
    st.download_button(
        label="Télécharger les données LinkedIn au format Excel",
        data=excel_bytes,
        file_name="linkedin_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Optionnel : bouton pour réinitialiser les données
if st.button("Réinitialiser toutes les données"):
    st.session_state.posts_data = []
    st.session_state.reactions_data = []
    st.success("Données réinitialisées.")


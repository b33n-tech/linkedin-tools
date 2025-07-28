import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
import io

# --- Fonctions ---

def parse_post_header(raw_text):
    # Supprime la mention "Il y a X jours • Visible de tous sur LinkedIn et en dehors"
    raw_text = re.sub(r"Il y a \d+ (jours|j|heures|h|minutes|min|semaines|mois) • Visible de tous sur LinkedIn et en dehors", "", raw_text)

    lines = [line.strip() for line in raw_text.splitlines() if line.strip() != ""]
    auteur = lines[0] if len(lines) > 0 else ""

    date_relative = ""
    for l in lines:
        match = re.search(r"(\d+)\s*(j|jour|jours|h|heure|heures|min|minute|minutes|sem|semaine|semaines|mois)", l)
        if match:
            date_relative = match.group(0)
            break

    # Extrait les premières lignes du post après la ligne avec date relative
    idx = 0
    for i, l in enumerate(lines):
        if date_relative in l:
            idx = i + 1
            break
    post_excerpt = " ".join(lines[idx:idx+3]) if idx+3 <= len(lines) else " ".join(lines[idx:])

    return auteur, date_relative, post_excerpt

def convert_relative_date(date_str):
    now = datetime.now()
    if date_str == "":
        return ""
    try:
        number = int(re.findall(r'\d+', date_str)[0])
    except:
        return ""

    if "j" in date_str:
        return (now - timedelta(days=number)).strftime("%Y-%m-%d")
    elif "h" in date_str:
        return (now - timedelta(hours=number)).strftime("%Y-%m-%d %H:%M")
    elif "min" in date_str:
        return (now - timedelta(minutes=number)).strftime("%Y-%m-%d %H:%M")
    elif "sem" in date_str:
        return (now - timedelta(weeks=number)).strftime("%Y-%m-%d")
    elif "mois" in date_str:
        # Approximer un mois à 30 jours
        return (now - timedelta(days=30*number)).strftime("%Y-%m-%d")
    else:
        return ""

def parse_reactions(raw_text):
    lines = [line.strip() for line in raw_text.splitlines() if line.strip() != ""]
    reactions_list = []
    i = 0
    reaction_types = {"like", "love", "celebrate", "funny", "support", "insightful"}

    while i < len(lines):
        # Ligne réaction (ex: like)
        if lines[i].lower() in reaction_types:
            reaction = lines[i].lower()
            i += 1
            if i >= len(lines):
                break
            # Ligne nom (ex: Naman SharmaVoir le profil de Naman Sharma)
            full_name = lines[i]
            # Extraire nom avant "Voir le profil de"
            name_match = re.match(r"^(.*?)Voir le profil de", full_name)
            if name_match:
                name = name_match.group(1).strip()
            else:
                name = full_name.strip()
            i += 1
            if i >= len(lines):
                break
            # Ligne position dans réseau (ex: Out of network · 3e et +)
            position = lines[i]
            i += 1
            if i >= len(lines):
                info = ""
            else:
                # Ligne info (ex: Founder and Content Creator at SciencEpic Nepal YouTube || Attended Gandaki College of Engineering and Science)
                info = lines[i]
                i += 1

            reactions_list.append({
                "Reaction": reaction,
                "Nom": name,
                "Position LK": position,
                "Infos": info
            })
        else:
            i += 1
    return reactions_list

# --- Streamlit UI ---

st.title("Analyse de posts LinkedIn - extraction post et réactions")

st.markdown("""
Uploader les textes des posts LinkedIn (copier-coller brut), un par un.
Pour chaque post, on extrait : auteur, date relative, date exacte, extrait du post.
Ensuite, coller les réactions du post et extraire la ventilation des types de réactions avec détails.
Ajouter plusieurs posts, puis télécharger un Excel final avec toutes les données.
""")

# DataFrames pour stocker les résultats cumulés
if "posts_data" not in st.session_state:
    st.session_state.posts_data = []
if "reactions_data" not in st.session_state:
    st.session_state.reactions_data = []

with st.form("form_post"):
    raw_post = st.text_area("Coller le texte complet du post LinkedIn (y compris auteur, date, début du contenu)", height=150)
    submitted_post = st.form_submit_button("Ajouter ce post")

if submitted_post:
    if raw_post.strip() == "":
        st.warning("Merci de coller un texte de post valide.")
    else:
        auteur, date_rel, post_excerpt = parse_post_header(raw_post)
        date_exacte = convert_relative_date(date_rel)
        st.session_state.posts_data.append({
            "Auteur": auteur,
            "Date relative": date_rel,
            "Date exacte": date_exacte,
            "Extrait du post": post_excerpt
        })
        st.success(f"Post ajouté : {auteur} / {date_rel} / {date_exacte}")
        st.write(post_excerpt)

st.markdown("---")

with st.form("form_reactions"):
    raw_reactions = st.text_area("Coller les réactions d'un post LinkedIn (texte brut)", height=300)
    submitted_reactions = st.form_submit_button("Analyser les réactions")

if submitted_reactions:
    if raw_reactions.strip() == "":
        st.warning("Merci de coller un texte de réactions valide.")
    else:
        reactions_list = parse_reactions(raw_reactions)
        if len(reactions_list) == 0:
            st.warning("Aucune réaction détectée dans le texte.")
        else:
            # On associe la dernière entrée postée (sinon on pourrait demander à l'utilisateur de choisir)
            if len(st.session_state.posts_data) == 0:
                st.warning("Veuillez d'abord ajouter un post pour associer les réactions.")
            else:
                dernier_post = st.session_state.posts_data[-1]
                # Ajouter le champ post auteur + date à chaque réaction pour suivi
                for r in reactions_list:
                    r["Post auteur"] = dernier_post["Auteur"]
                    r["Post date relative"] = dernier_post["Date relative"]
                    r["Post date exacte"] = dernier_post["Date exacte"]
                st.session_state.reactions_data.extend(reactions_list)
                st.success(f"{len(reactions_list)} réactions ajoutées, associées au post de {dernier_post['Auteur']}")

st.markdown("---")

# Affichage des données ajoutées
if st.session_state.posts_data:
    st.subheader("Posts ajoutés")
    st.dataframe(pd.DataFrame(st.session_state.posts_data))

if st.session_state.reactions_data:
    st.subheader("Réactions extraites")
    st.dataframe(pd.DataFrame(st.session_state.reactions_data))

# Bouton pour télécharger fichier Excel combiné
def to_excel(posts, reactions):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine="xlsxwriter")

    df_posts = pd.DataFrame(posts)
    df_reactions = pd.DataFrame(reactions)

    df_posts.to_excel(writer, index=False, sheet_name="Posts")
    df_reactions.to_excel(writer, index=False, sheet_name="Réactions")

    writer.save()
    processed_data = output.getvalue()
    return processed_data

if st.session_state.posts_data or st.session_state.reactions_data:
    excel_data = to_excel(st.session_state.posts_data, st.session_state.reactions_data)
    st.download_button(
        label="Télécharger les données Excel (Posts + Réactions)",
        data=excel_data,
        file_name="linkedin_posts_reactions.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

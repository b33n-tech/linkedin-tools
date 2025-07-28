import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime, timedelta

st.set_page_config(page_title="LinkedIn Posts & Reactions Analyzer")

# Fonction pour parser la date relative (ex: "Il y a 3 jours") en date absolue
def parse_relative_date(text):
    # Exemples de formats possibles en français
    # "Il y a 3 jours", "Il y a 5 h", "Il y a 1 semaine", "Il y a 2 mois"
    match = re.search(r"Il y a (\d+)\s*(jour|jours|h|heure|heures|semaine|semaines|mois)", text.lower())
    if not match:
        return None
    value = int(match.group(1))
    unit = match.group(2)
    now = datetime.now()

    if unit.startswith('jour'):
        delta = timedelta(days=value)
    elif unit.startswith('h'):
        delta = timedelta(hours=value)
    elif unit.startswith('heure'):
        delta = timedelta(hours=value)
    elif unit.startswith('semaine'):
        delta = timedelta(weeks=value)
    elif unit.startswith('mois'):
        delta = timedelta(days=30*value)  # approximation
    else:
        return None

    date = now - delta
    return date.strftime("%Y-%m-%d %H:%M:%S")

# Extraction du post : 
# on retire la partie "Il y a X • Visible..." du début
def clean_post_text(text):
    # Supprime la partie "Il y a ... • Visible de tous sur LinkedIn et en dehors"
    text = re.sub(r"^Il y a [^•]+\s*•\s*Visible de tous sur LinkedIn et en dehors\s*", "", text, flags=re.I)
    return text.strip()

# Extraction des réactions
def parse_reactions(raw_text):
    lines = raw_text.strip().split('\n')
    reactions = []
    reaction_types = {"like", "love", "celebrate", "funny", "support", "insightful"}  # support & insightful sont d'autres réactions possibles sur LinkedIn
    idx = 0
    while idx < len(lines):
        line = lines[idx].strip().lower()
        if line in reaction_types:
            reaction = line
            idx += 1
            if idx >= len(lines):
                break
            # Le nom est sur la ligne suivante, enlever "Voir le profil de" si présent
            name_line = lines[idx].strip()
            name = re.sub(r"Voir le profil de .*", "", name_line).strip()
            idx += 1
            if idx >= len(lines):
                break
            # Position / réseau
            position = lines[idx].strip()
            idx += 1
            if idx >= len(lines):
                break
            # Info supplémentaire (souvent une ligne, peut être vide)
            info = lines[idx].strip()
            idx += 1
            reactions.append({
                "Reaction": reaction.capitalize(),
                "Name": name,
                "Position": position,
                "Info": info
            })
        else:
            idx += 1
    return reactions

# Fonction pour transformer en fichier Excel
def to_excel(posts, reactions_by_post):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_posts = pd.DataFrame(posts)
        df_posts.to_excel(writer, index=False, sheet_name='Posts')

        reactions_rows = []
        for idx, reactions in enumerate(reactions_by_post):
            for r in reactions:
                r_copy = r.copy()
                r_copy["Post n°"] = idx + 1
                reactions_rows.append(r_copy)
        df_reactions = pd.DataFrame(reactions_rows)
        df_reactions.to_excel(writer, index=False, sheet_name='Reactions')

    data = output.getvalue()
    return data

# Interface Streamlit

st.title("LinkedIn Posts & Reactions Analyzer")

nb_posts = st.number_input("Combien de posts voulez-vous saisir ?", min_value=1, max_value=50, value=1, step=1)

if 'posts_raw' not in st.session_state:
    st.session_state.posts_raw = ["" for _ in range(nb_posts)]
if 'reactions_raw' not in st.session_state:
    st.session_state.reactions_raw = ["" for _ in range(nb_posts)]

# Ajuster les listes si l'utilisateur modifie nb_posts
if len(st.session_state.posts_raw) != nb_posts:
    if len(st.session_state.posts_raw) < nb_posts:
        st.session_state.posts_raw.extend([""] * (nb_posts - len(st.session_state.posts_raw)))
    else:
        st.session_state.posts_raw = st.session_state.posts_raw[:nb_posts]

if len(st.session_state.reactions_raw) != nb_posts:
    if len(st.session_state.reactions_raw) < nb_posts:
        st.session_state.reactions_raw.extend([""] * (nb_posts - len(st.session_state.reactions_raw)))
    else:
        st.session_state.reactions_raw = st.session_state.reactions_raw[:nb_posts]

posts_clean = []
reactions_clean = []

for i in range(nb_posts):
    st.subheader(f"Post n°{i+1}")

    st.session_state.posts_raw[i] = st.text_area(
        f"Copier-coller le contenu complet du post n°{i+1} (incluant auteur, date, texte)",
        st.session_state.posts_raw[i],
        height=200,
        key=f"post_{i}"
    )
    st.session_state.reactions_raw[i] = st.text_area(
        f"Copier-coller les réactions du post n°{i+1}",
        st.session_state.reactions_raw[i],
        height=300,
        key=f"reactions_{i}"
    )

    # Extraction infos post
    raw_post = st.session_state.posts_raw[i].strip()
    if raw_post:
        # Extraction auteur = première ligne sans "Lien graphique..."
        lines = raw_post.split('\n')
        # Auteur : on récupère la 2e ligne (car la 1ère est souvent "Lien graphique pour ...")
        author = ""
        for line in lines:
            if line.strip() and not line.lower().startswith("lien graphique"):
                author = line.strip()
                break

        # Extraction date relative (ex: "Il y a 3 jours • Visible de tous ...") on cherche la 1ère ligne contenant "Il y a"
        date_relative = None
        for line in lines:
            if "il y a" in line.lower():
                date_relative = line.strip()
                break
        date_exacte = parse_relative_date(date_relative) if date_relative else ""

        # Nettoyer le texte du post
        post_text = clean_post_text(raw_post)

        posts_clean.append({
            "Auteur": author,
            "Date relative": date_relative if date_relative else "",
            "Date exacte": date_exacte,
            "Post": post_text
        })
    else:
        posts_clean.append({
            "Auteur": "",
            "Date relative": "",
            "Date exacte": "",
            "Post": ""
        })

    # Extraction réactions
    raw_reac = st.session_state.reactions_raw[i].strip()
    reactions_clean.append(parse_reactions(raw_reac) if raw_reac else [])

if st.button("Télécharger Excel"):
    excel_data = to_excel(posts_clean, reactions_clean)
    st.download_button(
        label="Télécharger le fichier Excel",
        data=excel_data,
        file_name="linkedin_posts_reactions.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

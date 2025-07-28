import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
from io import BytesIO
from collections import Counter

def parse_post(raw_text):
    # Même parse_post que précédemment, robuste
    text = raw_text.strip()
    date_pattern = re.compile(r"(Il y a\s*\d+\s*(jours?|j|heures|h|minutes|m))|(\d+\s*(j|h|m))")
    date_match = date_pattern.search(text)
    if not date_match:
        return None

    date_relative = date_match.group(0)
    split_idx = date_match.start()
    before_date = text[:split_idx].strip()
    after_date = text[date_match.end():].strip()

    # Nettoyer auteur : enlever répétition collée (ex: Ishaan PatilIshaan Patil)
    if len(before_date) > 3:
        parts = before_date.split()
        if len(parts) > 1 and before_date.startswith(parts[0] + parts[0]):
            auteur = parts[0]
        else:
            auteur = before_date.split("\n")[0].strip()
    else:
        auteur = before_date

    # Nettoyer post : enlever "Visible de tous sur LinkedIn..." et limiter preview
    after_date = re.sub(r"Visible de tous sur LinkedIn.*", "", after_date, flags=re.DOTALL).strip()
    preview = after_date[:300].replace("\n", " ").strip()

    # Date absolue approx
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

def parse_reactions(raw_text):
    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
    reactions_types = ["like", "celebrate", "love", "funny", "insightful", "curious"]
    # On va parser par blocs de 4 lignes :
    # 1 - réaction
    # 2 - nom + "Voir le profil de ..."
    # 3 - position réseau (ex: "Out of network · 3e et +")
    # 4 - info

    data = []
    i = 0
    while i < len(lines):
        if lines[i].lower() in reactions_types:
            reaction = lines[i].lower()
            if i + 3 < len(lines):
                full_name = lines[i+1]
                # Extraire nom avant "Voir le profil de" si présent
                name_match = re.match(r"^(.*?)Voir le profil de", full_name)
                if name_match:
                    name = name_match.group(1).strip()
                else:
                    name = full_name.strip()
                position = lines[i+2]
                info = lines[i+3]
                data.append({
                    "Reaction": reaction,
                    "Nom": name,
                    "Position": position,
                    "Info": info
                })
                i += 4
            else:
                break
        else:
            i += 1
    return data

def summarize_reactions(reactions_list):
    # Donne un dict {reaction_type: count}
    counter = Counter([r["Reaction"] for r in reactions_list])
    return dict(counter)

def to_excel(posts, reactions_by_post):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_posts = pd.DataFrame(posts)
        df_posts.to_excel(writer, index=False, sheet_name='Posts')

        # Flatten reactions by post into a dataframe with Post number
        reactions_rows = []
        for idx, reactions in enumerate(reactions_by_post):
            for r in reactions:
                r_copy = r.copy()
                r_copy["Post n°"] = idx + 1
                reactions_rows.append(r_copy)
        df_reactions = pd.DataFrame(reactions_rows)
        df_reactions.to_excel(writer, index=False, sheet_name='Reactions')

        writer.save()
    processed_data = output.getvalue()
    return processed_data

st.title("Outil LinkedIn : Analyse posts + réactions par lot")

# Étape 1 : Choix du nombre de posts
num_posts = st.number_input("Combien de posts voulez-vous analyser ?", min_value=1, max_value=50, value=3, step=1)

if 'posts' not in st.session_state:
    st.session_state.posts = [None]*num_posts
if 'reactions' not in st.session_state:
    st.session_state.reactions = [None]*num_posts

# Pour éviter que st.session_state.posts soit trop long ou trop court si on change num_posts à la volée
if len(st.session_state.posts) != num_posts:
    st.session_state.posts = [None]*num_posts
if len(st.session_state.reactions) != num_posts:
    st.session_state.reactions = [None]*num_posts

st.markdown("---")
st.write(f"Collez le texte complet du post, puis les réactions associées, pour chacun des {num_posts} posts.")

for i in range(num_posts):
    st.subheader(f"Post #{i+1}")
    post_raw = st.text_area(f"Texte brut du post #{i+1}", key=f"post_raw_{i}")
    reaction_raw = st.text_area(f"Réactions LinkedIn du post #{i+1}", key=f"reaction_raw_{i}")

    if post_raw.strip():
        parsed_post = parse_post(post_raw)
        if parsed_post:
            st.session_state.posts[i] = parsed_post
            st.success(f"Post #{i+1} parsé avec succès.")
        else:
            st.warning(f"Impossible de parser le post #{i+1}. Vérifiez la structure.")

    if reaction_raw.strip():
        parsed_reactions = parse_reactions(reaction_raw)
        if parsed_reactions:
            st.session_state.reactions[i] = parsed_reactions
            st.success(f"Réactions du post #{i+1} parsées avec succès.")
        else:
            st.warning(f"Aucune réaction valide trouvée pour le post #{i+1}.")

st.markdown("---")

if st.button("Télécharger tout en Excel"):
    # Filtrer None
    posts_clean = [p for p in st.session_state.posts if p]
    reactions_clean = [r if r else [] for r in st.session_state.reactions]

    if not posts_clean:
        st.error("Aucun post valide à exporter.")
    else:
        excel_data = to_excel(posts_clean, reactions_clean)
        st.download_button(
            label="Télécharger le fichier Excel",
            data=excel_data,
            file_name="linkedin_posts_reactions.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

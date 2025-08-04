import streamlit as st
import pandas as pd

# ========== TAGS & MOTS-CLÉS ==========
tags_keywords = {
    "Management": [
        "responsable", "chef de projet", "chief of staff", "coordinateur", "bras droit", "directeur", "manager",
        "program manager", "project manager", "pm", "gestion", "organisational development", "référent pédagogique",
        "chef·fe de service", "chef de projets", "operations", "product owner", "strategy"
    ],
    "Commercial / Vente": [
        "commercial", "business developer", "développement commercial", "affaires", "vente", "biz dev",
        "partenariats", "business development", "conseiller", "chargé d'affaires", "responsable commercial",
        "price manager", "partnership manager", "business manager", "sales"
    ],
    "Marketing / Communication": [
        "communication", "marketing", "fidélisation", "événementiel", "digital", "contenu", "promotion",
        "responsable communication", "campagne", "publicité"
    ],
    "Support / Administration": [
        "assistant", "administration", "admissions", "gestion", "support", "ressources humaines", "rh",
        "coordination", "secrétariat", "chargé d'accompagnement", "chargé de mission", "chargé de scolarité",
        "chargé de service client"
    ],
    "Technique / Ingénierie": [
        "consultant", "ingénieur", "technique", "data", "analyse", "innovation", "digital", "ia", "erp", "r&d",
        "product owner", "chef de projet digital", "chef de projet data"
    ],
    "Création / Design": [
        "design", "création", "animateur", "créatif", "rédaction", "ux", "ui", "animation"
    ]
}

def find_tags(title):
    if pd.isna(title):
        return "Autre"
    title_low = str(title).lower()
    found_tags = set()
    for tag, keywords in tags_keywords.items():
        for kw in keywords:
            if kw in title_low:
                found_tags.add(tag)
    return ", ".join(found_tags) if found_tags else "Autre"

# ========== STREAMLIT UI ==========
st.title("🧠 Taggage automatique des intitulés de postes (.xlsx)")

uploaded_file = st.file_uploader("📂 Upload un fichier Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("✅ Fichier chargé avec succès.")
    st.write("Aperçu des données :", df.head())

    col_options = df.columns.tolist()
    selected_col = st.selectbox("📌 Sélectionne la colonne contenant les intitulés de postes :", col_options)

    if st.button("🏷️ Générer les tags"):
        df["Tags"] = df[selected_col].apply(find_tags)
        st.write("✅ Tags générés :")
        st.dataframe(df[[selected_col, "Tags"]])

        # Fichier téléchargeable
        @st.cache_data
        def convert_df_to_excel(df):
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)
            return output.getvalue()

        st.download_button(
            label="📥 Télécharger le fichier avec tags",
            data=convert_df_to_excel(df),
            file_name="fichier_taggué.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

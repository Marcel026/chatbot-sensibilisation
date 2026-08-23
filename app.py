# Interface Streamlit pour le chatbot MTN
import streamlit as st
import json
from datetime import datetime
from pathlib import Path
from rag_mtn import obtenir_reponse, rechercher_information

# ========================
# Configuration Streamlit
# ========================
st.set_page_config(
    page_title="Sensibilisation aux MTN",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================
# Messages Centralisés
# ========================

MESSAGES_FR = {
    "titre": "🩺 Sensibilisation aux MTN",
    "description": (
        "Posez vos questions sur les maladies tropicales négligées (MTN), "
        "leurs symptômes, leur prévention, les signes d'alerte et la conduite à tenir."
    ),

    "maladies": [
        "Lèpre",
        "Dengue",
        "Envenimations par morsure de serpent (EMS)",
        "Schistosomiase",
        "Ulcère de Buruli",
        "Noma"
    ],

    "input_placeholder":
        "Exemple : Quels sont les symptômes de la schistosomiase ?",

    "erreur":
        "⚠️ Une erreur s'est produite. Veuillez réessayer.",

    "question_vide":
        "⚠️ Veuillez saisir une question avant d'envoyer votre message.",

    "suggestions": [
        "🦠 Quels sont les symptômes ?",
        "🛡️ Comment prévenir cette maladie ?",
        "🏥 Que faire en cas de suspicion ?",
        "⚠️ Quels sont les signes de gravité ?",
        "💊 Quel est le traitement recommandé ?"
    ],

    "feedback_prompt":
        "✅ Cette réponse vous a-t-elle été utile ?",

    "feedback_oui":
        "👍 Oui, cette réponse m'a aidé",

    "feedback_non":
        "👎 Non, je souhaite plus d'informations",

    "feedback_thanks_oui":
        "🙏 Merci pour votre retour et votre confiance.",

    "feedback_thanks_non":
        "🙏 Merci pour votre retour. Nous prendrons en compte votre remarque.",

    "plus_info":
        "🔎 Souhaitez-vous approfondir ce sujet ?",

    "plus_info_btn":
        "📚 Voir les suggestions",

    "aide":
        (
            "Vous pouvez poser des questions telles que :\n"
            "- Qu'est-ce que la lèpre ?\n"
            "- Comment prévenir la dengue ?\n"
            "- Que faire après une morsure de serpent ?\n"
            "- Quels sont les symptômes de la schistosomiase ?\n"
            "- Qu'est-ce que l'ulcère de Buruli ?\n"
            "- Quels sont les signes d'alerte du noma ?"
        ),

    "disclaimer":
        (
            "ℹ️ Cet assistant fournit des informations de sensibilisation. "
            "En cas de maladie ou d'urgence, consultez rapidement un professionnel de santé."
        )
}

# ========================
# Fichier de Feedback
# ========================
FEEDBACK_FILE = Path("feedback.json")

def sauvegarder_feedback(question, reponse, feedback):
    """Sauvegarde les feedbacks utilisateur."""
    try:
        feedback_data = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "reponse_preview": reponse[:100] + "..." if len(reponse) > 100 else reponse,
            "feedback": feedback
        }
        
        feedbacks = []
        if FEEDBACK_FILE.exists():
            with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
                feedbacks = json.load(f)
        
        feedbacks.append(feedback_data)
        
        with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
            json.dump(feedbacks, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde du feedback: {e}")

# ========================
# Configuration Session State
# ========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "derniere_question" not in st.session_state:
    st.session_state.derniere_question = None

if "derniere_reponse" not in st.session_state:
    st.session_state.derniere_reponse = None

if "feedback_donnee" not in st.session_state:
    st.session_state.feedback_donnee = False

if "derniere_resultat" not in st.session_state:
    st.session_state.derniere_resultat = None

# ========================
# Sidebar
# ========================
with st.sidebar:
    st.header("⚙️ Options")
    
    afficher_debug = st.checkbox("🐛 Mode DEBUG", value=False)
    
    if st.button("🗑️ Effacer l'historique"):
        st.session_state.messages = []
        st.session_state.derniere_question = None
        st.session_state.derniere_reponse = None
        st.session_state.feedback_donnee = False
        st.success("Historique effacé !")
    
    st.markdown("---")
    st.subheader("📋 Maladies Couvertes")
    for maladie in MESSAGES_FR["maladies"]:
        st.markdown(f"• {maladie}")
    
    st.markdown("---")
    st.subheader("📊 Statistiques")
    st.metric("Questions posées", len(st.session_state.messages) // 2)

# ========================
# Titre et Description
# ========================
st.title(MESSAGES_FR["titre"])
st.markdown(f"### {MESSAGES_FR['description']}")

st.markdown("""
### Vous pouvez poser des questions sur :
""")
for maladie in MESSAGES_FR["maladies"]:
    st.markdown(f"- **{maladie}**")

st.markdown("---")

# ========================
# Affichage de l'Historique
# ========================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ========================
# Traitement des Nouvelles Questions
# ========================
if prompt := st.chat_input(MESSAGES_FR["input_placeholder"]):
    
    # Validation entrée
    if not prompt or not prompt.strip():
        st.error(MESSAGES_FR["question_vide"])
        st.stop()
    
    # Ajouter la question à l'historique
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.derniere_question = prompt
    st.session_state.feedback_donnee = False
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Obtenir la réponse
    try:
        resultats = rechercher_information(prompt, top_k=3)
        response = resultats[0]["contenu"] if resultats and resultats[0].get("contenu") else ""
        st.session_state.derniere_resultat = resultats[0] if resultats else None
        
        if not response:
            st.error(MESSAGES_FR["erreur"])
            st.stop()
        
        st.session_state.derniere_reponse = response
        
        # Afficher la réponse
        with st.chat_message("assistant"):
            st.markdown(response)
        
        # Ajouter seulement la réponse à l'historique
        st.session_state.messages.append({"role": "assistant", "content": response})
        
    except Exception as e:
        st.error(MESSAGES_FR["erreur"])
        if afficher_debug:
            st.error(f"Détail de l'erreur: {str(e)}")
        st.stop()

# ========================
# Section Feedback et Suggestions
# ========================
if st.session_state.derniere_reponse and not st.session_state.feedback_donnee:
    st.markdown("---")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"### {MESSAGES_FR['feedback_prompt']}")
    
    with col2:
        if st.button(MESSAGES_FR["feedback_oui"], key="feedback_yes"):
            sauvegarder_feedback(
                st.session_state.derniere_question,
                st.session_state.derniere_reponse,
                "utile"
            )
            st.success(MESSAGES_FR["feedback_thanks_oui"])
            st.session_state.feedback_donnee = True
    
    with col3:
        if st.button(MESSAGES_FR["feedback_non"], key="feedback_no"):
            sauvegarder_feedback(
                st.session_state.derniere_question,
                st.session_state.derniere_reponse,
                "insuffisant"
            )
            st.warning(MESSAGES_FR["feedback_thanks_non"])
            st.session_state.feedback_donnee = True

# ========================
# Suggestions Supplémentaires
# ========================
if st.session_state.derniere_reponse:
    st.markdown("---")
    st.markdown(MESSAGES_FR["plus_info"])
    
    col1, col2, col3, col4 = st.columns(4)
    
    suggestions = [
        ("symptômes", "Quels sont les symptômes ?"),
        ("prévention", "Comment prévenir ?"),
        ("conduite", "Que faire en cas de suspicion ?"),
        ("gravité", "Quels sont les signes de gravité ?")
    ]
    
    cols = [col1, col2, col3, col4]
    for i, (key, question_auto) in enumerate(suggestions):
        with cols[i]:
            if st.button(f"ℹ️ {key.capitalize()}", key=f"suggest_{i}"):
                st.session_state.messages.append({"role": "user", "content": question_auto})
                response = obtenir_reponse(question_auto)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()

# ========================
# Debug Info
# ========================
if afficher_debug:
    st.markdown("---")
    with st.expander("🔧 Informations DEBUG"):
        st.json({
            "derniere_question": st.session_state.derniere_question,
            "dernier_reponse_preview": st.session_state.derniere_reponse[:100] if st.session_state.derniere_reponse else None,
            "dernier_resultat": {
                "maladie": st.session_state.derniere_resultat.get("maladie") if st.session_state.derniere_resultat else None,
                "categorie": st.session_state.derniere_resultat.get("categorie") if st.session_state.derniere_resultat else None,
                "score": st.session_state.derniere_resultat.get("score") if st.session_state.derniere_resultat else None,
            },
            "feedback_donnee": st.session_state.feedback_donnee,
            "nombre_messages": len(st.session_state.messages)
        })
import streamlit as st
import google.generativeai as genai
import json
import os
import random
from datetime import datetime

# --- CONFIGURATION & STYLES ---
st.set_page_config(page_title="TECHMATE", page_icon="🎓", layout="wide")
api_key = os.getenv("API_KEY")

# --- CSS STYLES ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at top right, #fdf2f8, #e0f2fe, #f1f5f9);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e1b4b 0%, #312e81 100%);
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    .module-card {
        background: white;
        border-radius: 1.5rem;
        padding: 1.5rem;
        border: 4px solid transparent;
        transition: all 0.3s ease;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    
    .module-card:hover {
        border-color: #06b6d4;
        transform: translateY(-5px);
    }
    
    .stButton>button {
        border-radius: 1rem;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        transition: all 0.2s;
        background-color: #0f172a;
        color: white !important;
    }

    .leaderboard-entry {
        display: flex;
        justify-content: space-between;
        padding: 1rem;
        background: white;
        border-radius: 1rem;
        margin-bottom: 0.5rem;
        border: 1px solid #e2e8f0;
    }
    
    .leaderboard-user {
        background: #2563eb !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTS & DATA ---
MODULES_DATA = {
    'fr': [
        {"id": 1, "title": "Matériel & Postes", "desc": "Assemblage et maintenance.", "cert": "CompTIA A+", "diff": "Débutant"},
        {"id": 2, "title": "Systèmes & Logiciels", "desc": "Windows & Linux CLI.", "cert": "Microsoft MD-102", "diff": "Intermédiaire"},
        {"id": 3, "title": "Réseautique", "desc": "LAN, TCP/IP & Serveurs.", "cert": "Cisco CCNA", "diff": "Avancé"},
        {"id": 4, "title": "Support Client", "desc": "Méthodologie ITIL.", "cert": "ITIL 4", "diff": "Intermédiaire"},
        {"id": 5, "title": "Carrière", "desc": "Mapping vers l'industrie.", "cert": "Pro Dev", "diff": "Débutant"},
        {"id": 6, "title": "Savoir-être", "desc": "Communication & Éthique.", "cert": "Soft Skills", "diff": "Débutant"},
    ],
    'en': [
        {"id": 1, "title": "Hardware", "desc": "Assembly & Maintenance.", "cert": "CompTIA A+", "diff": "Beginner"},
        {"id": 2, "title": "Software & OS", "desc": "Windows & Linux CLI.", "cert": "Microsoft MD-102", "diff": "Intermediate"},
        {"id": 3, "title": "Networking", "desc": "LAN, TCP/IP & Servers.", "cert": "Cisco CCNA", "diff": "Advanced"},
        {"id": 4, "title": "IT Support", "desc": "ITIL Methodology.", "cert": "ITIL 4", "diff": "Intermediate"},
        {"id": 5, "title": "Career Path", "desc": "Industry Mapping.", "cert": "Pro Dev", "diff": "Beginner"},
        {"id": 6, "title": "Soft Skills", "desc": "Comm & Ethics.", "cert": "Soft Skills", "diff": "Beginner"},
    ]
}

COMMANDS_FR = [
    {"q": "Windows : Afficher la config IP ?", "a": "ipconfig", "opts": ["ifconfig", "ipconfig", "netstat", "route"]},
    {"q": "Linux : Lister les fichiers ?", "a": "ls -la", "opts": ["ls -la", "dir", "ps", "cat"]},
    {"q": "Windows : Vider le cache DNS ?", "a": "ipconfig /flushdns", "opts": ["dns /clear", "ipconfig /flushdns", "netsh", "arp"]},
    {"q": "Linux : Changer permissions ?", "a": "chmod", "opts": ["chown", "chmod", "cat", "grep"]}
]

PORTS_DATA = [
    {"name": "SSH", "port": 22}, {"name": "HTTP", "port": 80}, {"name": "HTTPS", "port": 443},
    {"name": "DNS", "port": 53}, {"name": "RDP", "port": 3389}, {"name": "FTP", "port": 21}
]

# --- STATE MANAGEMENT ---
if 'lang' not in st.session_state: st.session_state.lang = 'fr'
if 'view' not in st.session_state: st.session_state.view = 'Home'
if 'messages' not in st.session_state: st.session_state.messages = []
if 'library' not in st.session_state: st.session_state.library = []
if 'game_score' not in st.session_state: st.session_state.game_score = 0
if 'game_joker' not in st.session_state: st.session_state.game_joker = True
if 'game_player' not in st.session_state: st.session_state.game_player = None
if 'game_over' not in st.session_state: st.session_state.game_over = False
if 'current_game_id' not in st.session_state: st.session_state.current_game_id = None
if 'game_question' not in st.session_state: st.session_state.game_question = None

# --- GEMINI INTEGRATION ---
def get_mentor_response(user_input):
    if not api_key:
        return "⚠️ ERREUR: Clé API manquante / API Key Missing."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        lang_prompt = "Français (Québec)" if st.session_state.lang == 'fr' else "English"
        system_prompt = f"""
        Tu es TECHMATE, un mentor Socratique pour étudiants en Soutien Informatique au Québec.
        Ton rôle est d'aider l'étudiant à comprendre ses compétences DEP.
        NE DONNE PAS DE RÉPONSES DIRECTES. Pose des questions pour guider sa réflexion.
        Langue: {lang_prompt}.
        """
        
        full_prompt = f"{system_prompt}\n\nHistorique: {str(st.session_state.messages[-3:])}\nUser: {user_input}"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Erreur: {str(e)}"

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown(f"<div style='text-align: center; margin-bottom: 2rem;'><h1 style='color: white; font-weight: 900;'>TECHMATE</h1><p style='color: #22d3ee; font-size: 0.8rem;'>EXPERT SOUTIEN TI</p></div>", unsafe_allow_html=True)
    
    if st.button("🏠 ACCUEIL / HOME"): st.session_state.view = 'Home'
    if st.button("💬 LABO SOCRATIQUE"): st.session_state.view = 'Chat'
    if st.button("📚 BIBLIOTHÈQUE"): st.session_state.view = 'Library'
    if st.button("🎮 ARCADE TI"): st.session_state.view = 'Games'
    if st.button("🌍 RESSOURCES"): st.session_state.view = 'Resources'
    
    st.divider()
    lang_btn = "🌐 FR 🇫🇷" if st.session_state.lang == 'fr' else "🌐 EN 🇺🇸"
    if st.button(lang_btn):
        st.session_state.lang = 'en' if st.session_state.lang == 'fr' else 'fr'
        st.rerun()

# --- VIEWS ---

def view_home():
    st.markdown("<h2 class='techmate-title'>MODULES DU DEP</h2>", unsafe_allow_html=True)
    cols = st.columns(3)
    modules = MODULES_DATA[st.session_state.lang]
    for i, mod in enumerate(modules):
        with cols[i % 3]:
            st.markdown(f"""
                <div class='module-card'>
                    <p style='color: #3b82f6 !important; font-weight: 900; font-size: 0.7rem;'>{mod['cert']}</p>
                    <h3 style='margin: 0; font-weight: 900; color:black;'>{mod['title']}</h3>
                    <p style='font-size: 0.8rem; color: #64748b !important;'>{mod['desc']}</p>
                    <span style='background: #f1f5f9; padding: 2px 8px; border-radius: 10px; font-size: 0.6rem; font-weight: 900; color: #333 !important;'>{mod['diff']}</span>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"GO: {mod['title']}", key=f"mod_{mod['id']}"):
                st.session_state.messages.append({"role": "user", "content": f"Aide-moi sur le module {mod['title']}"})
                st.session_state.view = 'Chat'
                st.rerun()

def view_chat():
    st.markdown("<h2 class='techmate-title'>LABO SOCRATIQUE</h2>", unsafe_allow_html=True)
    
    chat_container = st.container(height=500)
    for m in st.session_state.messages:
        with chat_container.chat_message(m['role']):
            st.write(m['content'])

    if prompt := st.chat_input("Pose une question technique..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container.chat_message("user"):
            st.write(prompt)
        
        with chat_container.chat_message("assistant"):
            with st.spinner("TECHMATE analyse..."):
                resp = get_mentor_response(prompt)
                st.write(resp)
                st.session_state.messages.append({"role": "assistant", "content": resp})

def view_library():
    st.markdown("<h2 class='techmate-title'>MA BIBLIOTHÈQUE</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("### 📥 Ajouter")
        uploaded_file = st.file_uploader("PDF / Doc", type=['pdf', 'docx', 'xlsx', 'txt'])
        if uploaded_file and st.button("Sauvegarder"):
            file_data = {
                "id": str(datetime.now().timestamp()),
                "name": uploaded_file.name,
                "type": uploaded_file.type,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            st.session_state.library.append(file_data)
            st.success("Fichier indexé !")
    
    with col2:
        st.markdown("### 📚 Mes Documents")
        if not st.session_state.library:
            st.info("Aucun document.")
        else:
            for doc in st.session_state.library:
                with st.expander(f"📄 {doc['name']}"):
                    st.write(f"Date: {doc['date']}")
                    if st.button("Supprimer", key=f"del_{doc['id']}"):
                        st.session_state.library = [d for d in st.session_state.library if d['id'] != doc['id']]
                        st.rerun()

def view_games():
    st.markdown("<h2 class='techmate-title'>ARCADE TI</h2>", unsafe_allow_html=True)
    
    if st.session_state.game_over:
        st.balloons()
        st.markdown("<h3 style='text-align: center;'>🏆 CLASSEMENT FINAL</h3>", unsafe_allow_html=True)
        leaderboard = [
            {"n": "ProTech_Master", "s": 1200},
            {"n": st.session_state.game_player or "Joueur", "s": st.session_state.game_score, "is_u": True},
        ]
        leaderboard.sort(key=lambda x: x['s'], reverse=True)
        
        for i, entry in enumerate(leaderboard):
            cls = "leaderboard-user" if entry.get("is_u") else ""
            st.markdown(f"<div class='leaderboard-entry {cls}'><span>{i+1}. {entry['n

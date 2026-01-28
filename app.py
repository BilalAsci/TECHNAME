import streamlit as st
import google.generativeai as genai
import base64
import json
import os
import random
from datetime import datetime
from PIL import Image
import io

# --- CONFIGURATION & STYLES ---
st.set_page_config(page_title="TECHMATE", page_icon="🎓", layout="wide")

# Custom CSS to mimic the React TECHMATE look
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
        color: white;
    }
    
    .main-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 2rem;
        padding: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    }
    
    .module-card {
        background: white;
        border-radius: 1.5rem;
        padding: 1.5rem;
        border: 4px solid transparent;
        transition: all 0.3s ease;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
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
    }
    
    .techmate-title {
        font-size: 2.5rem;
        font-weight: 900;
        color: #0f172a;
        letter-spacing: -0.05em;
        font-style: italic;
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
        transform: scale(1.02);
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

# Persistence Simulation (Library)
LIBRARY_FILE = "library_data.json"
def save_library():
    with open(LIBRARY_FILE, "w") as f:
        json.dump(st.session_state.library, f)

def load_library():
    if os.path.exists(LIBRARY_FILE):
        with open(LIBRARY_FILE, "r") as f:
            st.session_state.library = json.load(f)

# --- GEMINI INTEGRATION ---
def get_mentor_response(user_input, file=None):
    api_key = os.getenv("API_KEY") # Prioritize environment variable
    if not api_key:
        st.error("API Key missing! Set process.env.API_KEY or use Streamlit Secrets.")
        return "Erreur d'authentification API."
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3-flash-preview')
    
    system_prompt = f"""
    Tu es TECHMATE, un mentor Socratique pour étudiants en Soutien Informatique au Québec.
    Ton rôle est d'aider l'étudiant à comprendre ses compétences DEP.
    NE DONNE PAS DE RÉPONSES DIRECTES. Pose des questions pour guider sa réflexion.
    Langue: {'Français (Québec)' if st.session_state.lang == 'fr' else 'English'}.
    """
    
    history = []
    for m in st.session_state.messages[-5:]:
        history.append({"role": "user" if m['role'] == 'user' else "model", "parts": [m['content']]})
    
    chat = model.start_chat(history=history)
    
    content_parts = [user_input]
    if file:
        # Simplification for demo: assuming text/pdf simulation via SDK
        content_parts.append(f"Analyse ce fichier: {file['name']}")

    response = chat.send_message(content_parts, generation_config={"temperature": 0.7})
    return response.text

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown(f"<div style='text-align: center; margin-bottom: 2rem;'><h1 style='color: white; font-weight: 900;'>TECHMATE</h1><p style='color: #22d3ee; font-size: 0.8rem;'>EXPERT SOUTIEN TI</p></div>", unsafe_allow_html=True)
    
    btn_style = "display: block; width: 100%; text-align: left; padding: 10px; margin-bottom: 5px; background: rgba(255,255,255,0.05); color: white; border: none; border-radius: 8px; cursor: pointer;"
    
    if st.button("🏠 ACCUEIL / HOME"): st.session_state.view = 'Home'
    if st.button("💬 LABO SOCRATIQUE"): st.session_state.view = 'Chat'
    if st.button("📚 BIBLIOTHÈQUE"): st.session_state.view = 'Library'
    if st.button("🎮 ARCADE TI"): st.session_state.view = 'Games'
    if st.button("🌍 RESSOURCES"): st.session_state.view = 'Resources'
    
    st.divider()
    if st.button("🌐 LANGUE: " + ("FR" if st.session_state.lang == 'fr' else "EN")):
        st.session_state.lang = 'en' if st.session_state.lang == 'fr' else 'fr'
        st.rerun()

    st.markdown("<div style='position: fixed; bottom: 20px; left: 20px;'><p style='font-size: 10px; color: #64748b;'>v2.5 PREVIEW-09-2025</p></div>", unsafe_allow_html=True)

# --- VIEWS ---

def view_home():
    st.markdown("<h2 class='techmate-title'>MODULES DU DEP</h2>", unsafe_allow_html=True)
    cols = st.columns(3)
    modules = MODULES_DATA[st.session_state.lang]
    for i, mod in enumerate(modules):
        with cols[i % 3]:
            st.markdown(f"""
                <div class='module-card'>
                    <p style='color: #3b82f6; font-weight: 900; font-size: 0.7rem;'>{mod['cert']}</p>
                    <h3 style='margin: 0; font-weight: 900;'>{mod['title']}</h3>
                    <p style='font-size: 0.8rem; color: #64748b;'>{mod['desc']}</p>
                    <span style='background: #f1f5f9; padding: 2px 8px; border-radius: 10px; font-size: 0.6rem; font-weight: 900;'>{mod['diff']}</span>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"S'entraîner: {mod['title']}", key=f"mod_{mod['id']}"):
                st.session_state.messages.append({"role": "user", "content": f"Aide-moi sur le module {mod['title']}"})
                st.session_state.view = 'Chat'
                st.rerun()

def view_chat():
    st.markdown("<h2 class='techmate-title'>LABO SOCRATIQUE</h2>", unsafe_allow_html=True)
    
    chat_container = st.container(height=500)
    for m in st.session_state.messages:
        with chat_container.chat_message(m['role']):
            st.markdown(m['content'])

    if prompt := st.chat_input("Pose une question technique ou téléverse un doc..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container.chat_message("user"):
            st.markdown(prompt)
        
        with chat_container.chat_message("assistant"):
            with st.spinner("TECHMATE analyse..."):
                resp = get_mentor_response(prompt)
                st.markdown(resp)
                st.session_state.messages.append({"role": "assistant", "content": resp})

def view_library():
    st.markdown("<h2 class='techmate-title'>MA BIBLIOTHÈQUE</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("### 📥 Ajouter")
        uploaded_file = st.file_uploader("PDF / Doc", type=['pdf', 'docx', 'xlsx', 'txt'])
        if uploaded_file and st.button("Sauvegarder en local"):
            file_data = {
                "id": str(datetime.now().timestamp()),
                "name": uploaded_file.name,
                "type": uploaded_file.type,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "size": uploaded_file.size
            }
            st.session_state.library.append(file_data)
            save_library()
            st.success("Fichier indexé !")
    
    with col2:
        st.markdown("### 📚 Mes Documents Permanents")
        if not st.session_state.library:
            st.info("Aucun document. Télécharge tes notes de cours.")
        else:
            for doc in st.session_state.library:
                with st.expander(f"📄 {doc['name']}"):
                    st.write(f"Type: {doc['type']} | Ajouté le: {doc['date']}")
                    st.button(f"Analyser avec TECHMATE", key=f"analyze_{doc['id']}")
                    if st.button("Supprimer", key=f"del_{doc['id']}"):
                        st.session_state.library = [d for d in st.session_state.library if d['id'] != doc['id']]
                        save_library()
                        st.rerun()

def view_games():
    st.markdown("<h2 class='techmate-title'>ARCADE TI</h2>", unsafe_allow_html=True)
    
    if st.session_state.game_over:
        st.balloons()
        st.markdown("<h3 style='text-align: center;'>🏆 CLASSEMENT FINAL</h3>", unsafe_allow_html=True)
        leaderboard = [
            {"n": "ProTech_Master", "s": 1200},
            {"n": "SysAdmin_Expert", "s": 950},
            {"n": st.session_state.game_player, "s": st.session_state.game_score, "is_u": True},
            {"n": "BitsWizard", "s": 600},
            {"n": "JuniorDev", "s": 400}
        ]
        leaderboard.sort(key=lambda x: x['s'], reverse=True)
        
        for i, entry in enumerate(leaderboard):
            cls = "leaderboard-user" if entry.get("is_u") else ""
            st.markdown(f"<div class='leaderboard-entry {cls}'><span>{i+1}. {entry['n']}</span> <b>{entry['s']} XP</b></div>", unsafe_allow_html=True)
        
        if st.button("RETOURNER À L'ARCADE"):
            st.session_state.game_over = False
            st.session_state.game_score = 0
            st.session_state.game_joker = True
            st.rerun()
        return

    if not st.session_state.game_player:
        st.markdown("### Identifie-toi pour jouer")
        name = st.text_input("Ton nom de joueur:")
        if st.button("Lancer la session") and name:
            st.session_state.game_player = name
            st.rerun()
        return

    st.markdown(f"**Joueur:** {st.session_state.game_player} | **Score:** {st.session_state.game_score} XP | **Joker:** {'✅ Disponible' if st.session_state.game_joker else '❌ Utilisé'}")
    
    if st.session_state.current_game_id is None:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚀 Maître des Ports"): st.session_state.current_game_id = 'ports' ; st.rerun()
        with c2:
            if st.button("💻 Terminal Héros"): st.session_state.current_game_id = 'commands' ; st.rerun()
    else:
        # Game logic
        if st.session_state.game_question is None:
            if st.session_state.current_game_id == 'ports':
                st.session_state.game_question = random.choice(PORTS_DATA)
            else:
                st.session_state.game_question = random.choice(COMMANDS_FR)
        
        q = st.session_state.game_question
        if st.session_state.current_game_id == 'ports':
            st.info(f"Quel est le numéro de port du protocole: **{q['name']}** ?")
            guess = st.number_input("Port #", value=0)
            if st.button("Vérifier"):
                if guess == q['port']:
                    st.session_state.game_score += 50
                    st.success("Correct !")
                    st.session_state.game_question = None
                    st.rerun()
                else:
                    if st.session_state.game_joker:
                        st.session_state.game_joker = False
                        st.warning("Erreur ! Joker utilisé. Réessaie !")
                    else:
                        st.error(f"Fini ! La réponse était {q['port']}")
                        st.session_state.game_over = True
                        st.rerun()
        else:
            st.info(f"Commande pour: **{q['q']}**")
            ans = st.radio("Options:", q['opts'])
            if st.button("Soumettre"):
                if ans == q['a']:
                    st.session_state.game_score += 100
                    st.success("Héro du terminal !")
                    st.session_state.game_question = None
                    st.rerun()
                else:
                    if st.session_state.game_joker:
                        st.session_state.game_joker = False
                        st.warning("Presque ! Joker utilisé.")
                    else:
                        st.error(f"Terminé. C'était: {q['a']}")
                        st.session_state.game_over = True
                        st.rerun()

def view_resources():
    st.markdown("<h2 class='techmate-title'>RESSOURCES UTILES</h2>", unsafe_allow_html=True)
    res = [
        {"n": "Inforoute FPT", "u": "https://www.inforoutefpt.org", "d": "Programme officiel DEP 5229."},
        {"n": "Cisco Skills", "u": "https://skillsforall.com", "d": "Bases réseaux gratuites."},
        {"n": "Microsoft Learn", "u": "https://learn.microsoft.com", "d": "Certifications Windows/Azure."},
        {"n": "Professor Messer", "u": "https://www.professormesser.com", "d": "Cours vidéo A+, Network+."}
    ]
    for r in res:
        st.markdown(f"#### [{r['n']}]({r['u']})")
        st.write(r['d'])
        st.divider()

# --- MAIN ROUTING ---
load_library()
if st.session_state.view == 'Home': view_home()
elif st.session_state.view == 'Chat': view_chat()
elif st.session_state.view == 'Library': view_library()
elif st.session_state.view == 'Games': view_games()
elif st.session_state.view == 'Resources': view_resources()

# Disclaimer for educational purposes
st.caption("TECHMATE: Outil de soutien pédagogique. Utilise l'IA Gemini 3 Preview.")

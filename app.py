import streamlit as st
import google.generativeai as genai
import json
import os
import random
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="TECHMATE", page_icon="🎓", layout="wide")
api_key = os.getenv("API_KEY")

# --- CSS (TASARIM VE RENK DÜZELTMELERİ) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Ana Arka Plan */
    .stApp {
        background: radial-gradient(circle at top right, #fdf2f8, #e0f2fe, #f1f5f9);
    }
    
    /* Yan Menü (Sidebar) */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e1b4b 0%, #312e81 100%);
    }
    [data-testid="stSidebar"] * {
        color: white !important; /* Yan menü yazıları beyaz */
    }
    
    /* Kart Tasarımı */
    .module-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 1.5rem;
        padding: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.5);
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
        margin-bottom: 1rem;
        color: #1e293b; /* Kart içi yazı rengi (KOYU) */
    }
    
    .module-card:hover {
        border-color: #06b6d4;
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    }
    
    /* Kart içi başlıklar ve yazılar */
    .module-card h3 {
        color: #0f172a !important;
        font-weight: 900;
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
    }
    .module-card p {
        color: #475569 !important;
        font-size: 0.9rem;
    }
    .badge {
        background-color: #e0f2fe;
        color: #0369a1 !important;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 800;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 0.5rem;
    }

    /* Butonlar */
    .stButton>button {
        background: linear-gradient(90deg, #0f172a 0%, #334155 100%);
        color: white;
        border: none;
        border-radius: 0.8rem;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    /* Başlıklar */
    .techmate-title {
        font-size: 3rem;
        font-weight: 900;
        color: #1e1b4b;
        letter-spacing: -0.05em;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- İÇERİK (SENİN ORİJİNAL VERİLERİN) ---
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
        return "⚠️ ERREUR: Clé API manquante. / API Key missing."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        lang_prompt = "Français" if st.session_state.lang == 'fr' else "English"
        system_prompt = f"""
        Tu es TECHMATE, un mentor Socratique pour étudiants en Soutien Informatique.
        Langue: {lang_prompt}.
        Ne donne pas de réponses directes. Pose des questions pour guider.
        Sois bref et encourageant.
        """
        
        full_prompt = f"{system_prompt}\n\nHistorique:\n{str(st.session_state.messages[-3:])}\n\nUser: {user_input}"
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
                    <span class='badge'>{mod['cert']}</span>
                    <h3>{mod['title']}</h3>
                    <p>{mod['desc']}</p>
                    <div style='margin-top: 10px; font-size: 0.8rem; font-weight: bold; color: #64748b;'>{mod['diff']}</div>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"GO: {mod['title']}", key=f"mod_{mod['id']}"):
                st.session_state.messages.append({"role": "user", "content": f"Aide-moi sur le module {mod['title']}"})
                st.session_state.view = 'Chat'
                st.rerun()

def view_chat():
    st.markdown("<h2 class='techmate-title'>LABO SOCRATIQUE</h2>", unsafe_allow_html=True)
    
    for m in st.session_state.messages:
        with st.chat_message(m['role']):
            st.write(m['content'])

    if prompt := st.chat_input("Pose une question technique..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("TECHMATE analyse..."):
                resp = get_mentor_response(prompt)
                st.write(resp)
                st.session_state.messages.append({"role": "assistant", "content": resp})

def view_library():
    st.markdown("<h2 class='techmate-title'>MA BIBLIOTHÈQUE</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### 📥 Ajouter")
        uploaded_file = st.file_uploader("PDF / Doc", type=['pdf', 'docx', 'txt'])
        if uploaded_file:
            st.success(f"Fichier {uploaded_file.name} reçu ! (Simulation)")
    
    with col2:
        st.info("Cette section simule le stockage de tes fichiers de cours.")

def view_games():
    st.markdown("<h2 class='techmate-title'>ARCADE TI</h2>", unsafe_allow_html=True)
    
    if st.session_state.game_over:
        st.error("GAME OVER!")
        if st.button("REJOUER / RESTART"):
            st.session_state.game_over = False
            st.session_state.game_score = 0
            st.session_state.game_joker = True
            st.rerun()
        return

    st.markdown(f"#### Score: {st.session_state.game_score} XP | Joker: {'✅' if st.session_state.game_joker else '❌'}")
    
    if st.session_state.current_game_id is None:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚀 Maître des Ports"): st.session_state.current_game_id = 'ports'; st.rerun()
        with c2:
            if st.button("💻 Terminal Héros"): st.session_state.current_game_id = 'commands'; st.rerun()
    else:
        if st.session_state.game_question is None:
            if st.session_state.current_game_id == 'ports':
                st.session_state.game_question = random.choice(PORTS_DATA)
            else:
                st.session_state.game_question = random.choice(COMMANDS_FR)
        
        q = st.session_state.game_question
        
        # Oyun Arayüzü
        st.markdown(f"<div class='module-card' style='text-align:center;'><h3>{q.get('name') or q.get('q')}</h3></div>", unsafe_allow_html=True)
        
        if st.session_state.current_game_id == 'ports':
            guess = st.number_input("Port #", value=0)
            if st.button("Vérifier"):
                if guess == q['port']:
                    st.session_state.game_score += 50
                    st.success("Correct!")
                    st.session_state.game_question = None
                    st.rerun()
                else:
                    st.error(f"Non! C'était {q['port']}")
                    st.session_state.game_over = True
                    st.rerun()
        else:
            ans = st.radio("Options:", q['opts'])
            if st.button("Valider"):
                if ans == q['a']:
                    st.session_state.game_score += 100
                    st.success("Bravo!")
                    st.session_state.game_question = None
                    st.rerun()
                else:
                    st.error("Perdu!")
                    st.session_state.game_over = True
                    st.rerun()
            
        if st.button("⬅️ Menu Arcade"):
            st.session_state.current_game_id = None
            st.session_state.game_question = None
            st.rerun()

def view_resources():
    st.markdown("<h2 class='techmate-title'>RESSOURCES</h2>", unsafe_allow_html=True)
    st.markdown("- [Inforoute FPT](https://www.inforoutefpt.org)\n- [Cisco Skills](https://skillsforall.com)")

# --- MAIN ROUTING ---
if st.session_state.view == 'Home': view_home()
elif st.session_state.view == 'Chat': view_chat()
elif st.session_state.view == 'Library': view_library()
elif st.session_state.view == 'Games': view_games()
elif st.session_state.view == 'Resources': view_resources()

import streamlit as st
import google.generativeai as genai
import os
import random
from datetime import datetime

# --- AYARLAR ---
st.set_page_config(page_title="TECHMATE", page_icon="🎓", layout="wide")
api_key = os.getenv("API_KEY")

# --- CSS (TASARIM) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;900&display=swap');
    
    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
    .stApp { background: radial-gradient(circle at top right, #fdf2f8, #e0f2fe, #f1f5f9); }
    
    .main p, .main h1, .main h2, .main h3, .main h4, .main li, .main span, .main div {
        color: #0f172a !important;
    }

    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1e1b4b 0%, #312e81 100%); }
    [data-testid="stSidebar"] * { color: white !important; }
    
    .module-card {
        background: white; border-radius: 1.5rem; padding: 1.5rem;
        border: 4px solid transparent; transition: all 0.3s ease;
        cursor: pointer; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 1rem;
    }
    .module-card:hover { border-color: #06b6d4; transform: translateY(-5px); }
    
    .stButton>button {
        border-radius: 1rem; font-weight: 900; text-transform: uppercase;
        letter-spacing: 0.1em; transition: all 0.2s; color: white !important;
        background-color: #0f172a;
    }
    
    /* Yeni M365 Kart Stili */
    .m365-card {
        border-left: 5px solid #ea580c;
        background: #fff7ed;
    }
    </style>
    """, unsafe_allow_html=True)

# --- VERİLER ---

# 1. STANDART MODÜLLER
MODULES_DATA = {
    'fr': [
        {"id": 1, "title": "Microsoft 365", "desc": "Administration, Cloud & Apps.", "cert": "MS-900", "diff": "Essentiel"},
        {"id": 2, "title": "Matériel (Hardware)", "desc": "Dépannage PC & Laptop.", "cert": "CompTIA A+", "diff": "Débutant"},
        {"id": 3, "title": "Systèmes OS", "desc": "Windows 10/11 & Linux.", "cert": "MD-102", "diff": "Intermédiaire"},
        {"id": 4, "title": "Réseautique", "desc": "TCP/IP, DNS, DHCP.", "cert": "CCNA", "diff": "Avancé"},
        {"id": 5, "title": "Cybersécurité", "desc": "Phishing & Pare-feu.", "cert": "Security+", "diff": "Avancé"},
        {"id": 6, "title": "Service Client", "desc": "Gestion tickets & ITIL.", "cert": "ITIL 4", "diff": "Débutant"},
    ],
    'en': [
        {"id": 1, "title": "Microsoft 365", "desc": "Admin, Cloud & Apps.", "cert": "MS-900", "diff": "Essential"},
        {"id": 2, "title": "Hardware", "desc": "PC Troubleshooting.", "cert": "CompTIA A+", "diff": "Beginner"},
        {"id": 3, "title": "OS Systems", "desc": "Windows 10/11 & Linux.", "cert": "MD-102", "diff": "Intermediate"},
        {"id": 4, "title": "Networking", "desc": "TCP/IP, DNS, DHCP.", "cert": "CCNA", "diff": "Advanced"},
        {"id": 5, "title": "Cybersecurity", "desc": "Phishing & Firewalls.", "cert": "Security+", "diff": "Advanced"},
        {"id": 6, "title": "Customer Service", "desc": "Ticket Mgmt & ITIL.", "cert": "ITIL 4", "diff": "Beginner"},
    ]
}

# 2. KOMUT SORULARI
COMMANDS_FR = [
    {"q": "Windows : Afficher la config IP ?", "a": "ipconfig", "opts": ["ifconfig", "ipconfig", "netstat", "route"]},
    {"q": "Linux : Lister les fichiers ?", "a": "ls -la", "opts": ["ls -la", "dir", "ps", "cat"]},
    {"q": "Windows : Tester la connexion ?", "a": "ping", "opts": ["ping", "echo", "Connect-MsolService", "tracert"]},
    {"q": "M365 : PowerShell connexion ?", "a": "Connect-MsolService", "opts": ["Connect-MsolService", "Login-365", "Start-AD", "ping 365"]}
]

# 3. PORT SORULARI
PORTS_DATA = [
    {"name": "SMTP (Email Send)", "port": 25}, 
    {"name": "HTTP (Web)", "port": 80}, 
    {"name": "HTTPS (Secure Web)", "port": 443},
    {"name": "DNS (Name Service)", "port": 53}, 
    {"name": "RDP (Remote Desktop)", "port": 3389}, 
    {"name": "IMAP (Email Receive)", "port": 143},
    {"name": "POP3 (Email Receive)", "port": 110},
    {"name": "SSH (Secure Shell)", "port": 22}
]

# 4. YENİ MICROSOFT 365 SORULARI
M365_DATA = [
    {"q": "Outlook: Quel protocole synchronise tout (mails, calendrier, contacts) ?", "a": "Exchange / MAPI", "opts": ["POP3", "IMAP", "Exchange / MAPI", "SMTP"]},
    {"q": "Teams: Où sont stockés les fichiers d'une conversation PRIVÉE ?", "a": "OneDrive for Business", "opts": ["SharePoint", "OneDrive for Business", "Local C:", "Azure Blob"]},
    {"q": "Teams: Où sont stockés les fichiers d'une ÉQUIPE (Channel) ?", "a": "SharePoint Online", "opts": ["OneDrive", "SharePoint Online", "Exchange", "Google Drive"]},
    {"q": "Excel: Quelle fonction additionne des cellules ?", "a": "=SOMME() / =SUM()", "opts": ["=ADD()", "=PLUS()", "=SOMME() / =SUM()", "=COUNT()"]},
    {"q": "Admin: Où réinitialiser le mot de passe d'un utilisateur ?", "a": "Admin Center (M365)", "opts": ["Outlook", "Admin Center (M365)", "Teams Settings", "Word"]},
    {"q": "Licence: Quelle licence inclut la version DESKTOP (Bureau) d'Office ?", "a": "Business Standard", "opts": ["Business Basic", "Business Standard", "E1", "Exchange Online"]},
    {"q": "Sécurité: Qu'est-ce que le MFA ?", "a": "Multi-Factor Authentication", "opts": ["Main File Access", "Multi-Factor Authentication", "Microsoft Fast Access", "Mail Filter App"]},
    {"q": "OneDrive: Quelle icône indique qu'un fichier est UNIQUEMENT dans le nuage ?", "a": "Nuage bleu", "opts": ["Coche verte", "Coche verte pleine", "Nuage bleu", "Rond rouge"]},
    {"q": "Word: Raccourci pour 'Sauvegarder' ?", "a": "Ctrl + S", "opts": ["Ctrl + C", "Ctrl + V", "Ctrl + S", "Alt + F4"]},
    {"q": "PowerShell: Commande pour lister les utilisateurs Azure AD ?", "a": "Get-AzureADUser", "opts": ["Show-Users", "List-M365", "Get-AzureADUser", "dir user"]}
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

# --- GEMINI INTEGRATION (OTOMATİK MODEL SEÇİCİ) ---
def get_mentor_response(user_input):
    if not api_key:
        return "⚠️ ERREUR: Clé API manquante."
    
    genai.configure(api_key=api_key)
    try:
        model_list = genai.list_models()
        available_models = [m.name for m in model_list if 'generateContent' in m.supported_generation_methods]
        
        selected_model = None
        for m in available_models:
            if 'flash' in m.lower(): selected_model = m; break
        if not selected_model:
            for m in available_models:
                if 'pro' in m.lower(): selected_model = m; break
        if not selected_model and available_models: selected_model = available_models[0]
            
        model = genai.GenerativeModel(selected_model)
        
        system_prompt = """
        Tu es TECHMATE, expert Microsoft 365 et Support TI.
        Sujets: Outlook, Teams, SharePoint, OneDrive, Windows, Hardware.
        Style: Professionnel mais amical.
        Si on te demande de l'aide sur Office, donne des étapes claires (1, 2, 3).
        """
        full_prompt = f"{system_prompt}\n\nHistorique: {str(st.session_state.messages[-3:])}\nUser: {user_input}"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e: return f"Hata: {str(e)}"

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"<div style='text-align: center; margin-bottom: 2rem;'><h1 style='color: white; font-weight: 900;'>TECHMATE</h1><p style='color: #22d3ee; font-size: 0.8rem;'>M365 & SUPPORT TI</p></div>", unsafe_allow_html=True)
    if st.button("🏠 ACCUEIL"): st.session_state.view = 'Home'
    if st.button("☁️ MICROSOFT 365"): st.session_state.view = 'Chat'; st.session_state.messages.append({"role": "user", "content": "J'ai besoin d'aide avec Microsoft 365 (Outlook/Teams)."})
    if st.button("🎮 ARCADE TI"): st.session_state.view = 'Games'
    if st.button("📚 BIBLIOTHÈQUE"): st.session_state.view = 'Library'
    st.divider()
    if st.button("🌐 LANGUE: " + ("FR" if st.session_state.lang == 'fr' else "EN")):
        st.session_state.lang = 'en' if st.session_state.lang == 'fr' else 'fr'
        st.rerun()

# --- VIEWS ---
def view_home():
    st.markdown("<h2 class='techmate-title'>CENTRE DE FORMATION TI</h2>", unsafe_allow_html=True)
    cols = st.columns(3)
    modules = MODULES_DATA[st.session_state.lang]
    for i, mod in enumerate(modules):
        with cols[i % 3]:
            # M365 için özel renk
            card_style = "m365-card" if "Microsoft" in mod['title'] else "module-card"
            st.markdown(f"""
                <div class='module-card {card_style}'>
                    <p style='color: #ea580c !important; font-weight: 900; font-size: 0.7rem;'>{mod['cert']}</p>
                    <h3 style='margin: 0; font-weight: 900;'>{mod['title']}</h3>
                    <p style='font-size: 0.8rem; color: #64748b !important;'>{mod['desc']}</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"ÉTUDIER: {mod['title']}", key=f"mod_{mod['id']}"):
                st.session_state.messages.append({"role": "user", "content": f"Je veux apprendre le module {mod['title']}."})
                st.session_state.view = 'Chat'
                st.rerun()

def view_chat():
    st.markdown("<h2 class='techmate-title'>MENTOR IA (M365 EXPERT)</h2>", unsafe_allow_html=True)
    chat_container = st.container(height=500)
    for m in st.session_state.messages:
        with chat_container.chat_message(m['role']): st.write(m['content'])
    if prompt := st.chat_input("Ex: Comment créer une règle dans Outlook ?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container.chat_message("user"): st.write(prompt)
        with chat_container.chat_message("assistant"):
            with st.spinner("Recherche dans la base de connaissances M365..."):
                resp = get_mentor_response(prompt)
                st.write(resp)
                st.session_state.messages.append({"role": "assistant", "content": resp})

def view_library():
    st.markdown("<h2 class='techmate-title'>BIBLIOTHÈQUE M365</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])
    with col1:
        st.info("📂 Déposez vos guides PDF ici.")
        st.file_uploader("Upload", label_visibility="collapsed")
    with col2:
        st.markdown("### 📘 Guides Rapides")
        st.markdown("""
        - **Outlook**: [Configuration POP/IMAP](https://support.microsoft.com)
        - **Teams**: [Guide Admin](https://learn.microsoft.com)
        - **Excel**: [Liste des Fonctions FR](https://support.microsoft.com)
        """)

def view_games():
    st.markdown("<h2 class='techmate-title'>ARCADE TI & M365</h2>", unsafe_allow_html=True)
    
    if st.session_state.game_over:
        st.balloons()
        st.error("GAME OVER!")
        if st.button("REJOUER"):
            st.session_state.game_over = False; st.session_state.game_score = 0; st.session_state.game_joker = True; st.rerun()
        return

    if not st.session_state.game_player:
        name = st.text_input("Ton nom (Gamer Tag):"); 
        if st.button("START") and name: st.session_state.game_player = name; st.rerun()
        return

    st.markdown(f"**Agent:** {st.session_state.game_player} | **Score:** {st.session_state.game_score} XP | **Joker:** {'✅' if st.session_state.game_joker else '❌'}")
    
    # OYUN SEÇİM EKRANI
    if st.session_state.current_game_id is None:
        c1, c2, c3 = st.columns(3)
        with c1: 
            if st.button("☁️ QUIZ M365 (YENİ!)"): st.session_state.current_game_id = 'm365'; st.rerun()
        with c2: 
            if st.button("🚀 PORTS & RÉSEAU"): st.session_state.current_game_id = 'ports'; st.rerun()
        with c3:
            if st.button("💻 COMMANDES CLI"): st.session_state.current_game_id = 'commands'; st.rerun()
    else:
        # SORU SEÇİMİ
        if st.session_state.game_question is None:
            if st.session_state.current_game_id == 'ports':
                st.session_state.game_question = random.choice(PORTS_DATA)
            elif st.session_state.current_game_id == 'commands':
                st.session_state.game_question = random.choice(COMMANDS_FR)
            elif st.session_state.current_game_id == 'm365':
                st.session_state.game_question = random.choice(M365_DATA)
        
        q = st.session_state.game_question
        
        # SORU KARTI
        st.markdown(f"<div class='module-card' style='text-align:center; border-top: 5px solid #0ea5e9;'><h3>{q.get('name') or q.get('q')}</h3></div>", unsafe_allow_html=True)
        
        # OYUN TİPİNE GÖRE CEVAP ALANI
        if st.session_state.current_game_id == 'ports':
            guess = st.number_input("Numéro de Port :", value=0)
            if st.button("Vérifier"):
                if guess == q['port']: st.session_state.game_score += 50; st.success("Correct !"); st.session_state.game_question = None; st.rerun()
                else: st.error(f"Faux ! C'était {q['port']}"); st.session_state.game_over = True; st.rerun()
        else:
            # M365 ve Komutlar için Şıklı Seçim
            ans = st.radio("Choisis la bonne réponse :", q['opts'])
            if st.button("Valider la réponse"):
                if ans == q['a']: 
                    st.session_state.game_score += 100
                    st.success("Excellent !")
                    st.session_state.game_question = None
                    st.rerun()
                else: 
                    if st.session_state.game_joker:
                        st.session_state.game_joker = False
                        st.warning("Joker utilisé ! Attention, c'est ta dernière chance.")
                    else:
                        st.error(f"Échec de la mission ! La réponse était : {q['a']}")
                        st.session_state.game_over = True
                        st.rerun()
        
        st.write("")
        if st.button("⬅️ Retour au Menu Arcade"):
            st.session_state.current_game_id = None
            st.session_state.game_question = None
            st.rerun()

# --- ROUTING ---
if st.session_state.view == 'Home': view_home()
elif st.session_state.view == 'Chat': view_chat()
elif st.session_state.view == 'Library': view_library()
elif st.session_state.view == 'Games': view_games()

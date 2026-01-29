import streamlit as st
import google.generativeai as genai
import json
import os
import random
from datetime import datetime

# --- CONFIGURATION & STYLES ---
st.set_page_config(page_title="TECHMATE", page_icon="🎓", layout="wide")

# API Key Ayarı (Hata almamak için güvenli erişim)
api_key = os.getenv("API_KEY")

# --- CSS DÜZELTMELERİ (RENKLER İÇİN) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;900&display=swap');
    
    /* Genel Yazı Tipi */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Arka Plan Rengi */
    .stApp {
        background: radial-gradient(circle at top right, #f8fafc, #e0f2fe, #f1f5f9);
    }
    
    /* Yan Menü (Sidebar) */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e3a8a 100%);
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] p {
        color: white !important;
    }

    /* Kart Tasarımları (Okunabilirlik İçin Siyah Yazı Zorunluluğu) */
    .module-card {
        background: white !important;
        border-radius: 1.5rem;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        margin-bottom: 1rem;
    }
    
    .module-card:hover {
        border-color: #0ea5e9;
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }

    /* KART İÇİNDEKİ YAZILARI ZORLA SİYAH YAP */
    .module-card h3 {
        color: #1e293b !important; /* Koyu Lacivert Başlık */
        font-weight: 900 !important;
        margin-top: 0 !important;
    }
    .module-card p {
        color: #475569 !important; /* Gri Açıklama */
        font-size: 0.9rem !important;
    }
    .cert-badge {
        color: #0284c7 !important;
        font-weight: 800;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Ana Başlık Rengi */
    .techmate-title {
        font-size: 2.5rem;
        font-weight: 900;
        color: #0f172a !important; /* Koyu renk */
        margin-bottom: 2rem;
    }

    /* Butonlar */
    .stButton>button {
        background-color: #0f172a;
        color: white;
        border-radius: 0.75rem;
        font-weight: 600;
        border: none;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #334155;
        color: white;
    }

    /* Input Alanları */
    .stTextInput>div>div>input {
        border-radius: 0.75rem;
        border: 1px solid #cbd5e1;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTS & DATA ---
MODULES_DATA = {
    'fr': [
        {"id": 1, "title": "Matériel & Postes", "desc": "Assemblage, CPU, RAM & Dépannage matériel.", "cert": "CompTIA A+", "diff": "Débutant"},
        {"id": 2, "title": "Systèmes & OS", "desc": "Windows 10/11, Linux & Virtualisation.", "cert": "Microsoft MD-102", "diff": "Intermédiaire"},
        {"id": 3, "title": "Réseautique", "desc": "TCP/IP, Switchs, Routeurs & Wi-Fi.", "cert": "Cisco CCNA", "diff": "Avancé"},
        {"id": 4, "title": "Support Client", "desc": "Gestion des tickets & Service ITIL.", "cert": "ITIL 4", "diff": "Intermédiaire"},
        {"id": 5, "title": "Cybersécurité", "desc": "Malwares, Phishing & Pare-feu.", "cert": "Security+", "diff": "Avancé"},
        {"id": 6, "title": "Carrière TI", "desc": "CV, Entrevue & Marché du travail.", "cert": "Pro", "diff": "Débutant"},
    ],
    'en': [
        {"id": 1, "title": "Hardware", "desc": "Assembly, CPU, RAM & Hardware troubleshooting.", "cert": "CompTIA A+", "diff": "Beginner"},
        {"id": 2, "title": "Systems & OS", "desc": "Windows 10/11, Linux & Virtualization.", "cert": "Microsoft MD-102", "diff": "Intermediate"},
        {"id": 3, "title": "Networking", "desc": "TCP/IP, Switches, Routers & Wi-Fi.", "cert": "Cisco CCNA", "diff": "Advanced"},
        {"id": 4, "title": "IT Support", "desc": "Ticket Management & ITIL Service.", "cert": "ITIL 4", "diff": "Intermediate"},
        {"id": 5, "title": "Cybersecurity", "desc": "Malware, Phishing & Firewalls.", "cert": "Security+", "diff": "Advanced"},
        {"id": 6, "title": "IT Career", "desc": "Resume, Interview & Job Market.", "cert": "Pro", "diff": "Beginner"},
    ]
}

# --- STATE MANAGEMENT ---
if 'lang' not in st.session_state: st.session_state.lang = 'fr'
if 'view' not in st.session_state: st.session_state.view = 'Home'
if 'messages' not in st.session_state: st.session_state.messages = []

# --- GEMINI AI MODEL ---
def get_response(prompt):
    if not api_key:
        return "⚠️ HATA: API Anahtarı bulunamadı. Lütfen Streamlit Secrets ayarlarını kontrol et."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        system_instruction = f"""
        Sen 'TECHMATE' adında, IT ve Bilgisayar Destek öğrencileri için yardımcı bir mentorsun.
        Dil: {'Fransızca' if st.session_state.lang == 'fr' else 'İngilizce'}.
        Cevapların kısa, cesaret verici ve teknik olarak doğru olsun.
        Öğrenciye doğrudan cevabı vermek yerine onu düşünmeye yönelt.
        """
        
        full_prompt = f"{system_instruction}\n\nUser: {prompt}"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Bir hata oluştu: {str(e)}"

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; font-weight: 900; letter-spacing: -1px;'>⚡ TECHMATE</h1>", unsafe_allow_html=True)
    st.caption("Asistan Öğrenci Platformu")
    st.divider()
    
    if st.button("🏠 Ana Sayfa / Home"): st.session_state.view = 'Home'
    if st.button("💬 Sohbet / Chat"): st.session_state.view = 'Chat'
    
    st.divider()
    current_lang = "FR 🇫🇷" if st.session_state.lang == 'fr' else "EN 🇺🇸"
    if st.button(f"Dil / Language: {current_lang}"):
        st.session_state.lang = 'en' if st.session_state.lang == 'fr' else 'fr'
        st.rerun()

# --- PAGES ---

def home_page():
    st.markdown(f"<div class='techmate-title'>{'MODULES DU COURS' if st.session_state.lang == 'fr' else 'COURSE MODULES'}</div>", unsafe_allow_html=True)
    
    cols = st.columns(3)
    modules = MODULES_DATA[st.session_state.lang]
    
    for i, mod in enumerate(modules):
        with cols[i % 3]:
            # HTML Kart Yapısı
            st.markdown(f"""
            <div class='module-card'>
                <p class='cert-badge'>{mod['cert']}</p>
                <h3>{mod['title']}</h3>
                <p>{mod['desc']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"{'Çalış' if st.session_state.lang == 'tr' else 'Start'}: {mod['title']}", key=mod['id']):
                st.session_state.messages.append({"role": "user", "content": f"I want to study {mod['title']}."})
                st.session_state.view = 'Chat'
                st.rerun()

def chat_page():
    st.markdown(f"<div class='techmate-title'>{'MENTOR AI' if st.session_state.lang == 'fr' else 'AI MENTOR'}</div>", unsafe_allow_html=True)
    
    # Mesaj Geçmişini Göster
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    # Yeni Mesaj Girişi
    if prompt := st.chat_input("Sorunu sor... / Ask your question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_response(prompt)
                st.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# --- MAIN ROUTING ---
if st.session_state.view == 'Home':
    home_page()
elif st.session_state.view == 'Chat':
    chat_page()

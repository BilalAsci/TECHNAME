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

# --- VERİLER (İÇERİK BURADA DOLDURULUYOR) ---

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
    {"name": "IMAP

import streamlit as st
import os
import sys

st.set_page_config(page_title="Hata Teşhis Ekranı", layout="wide")

st.title("🕵️‍♂️ Teşhis Modu (Diagnostic Mode)")

# 1. API Anahtarı Kontrolü
api_key = os.getenv("API_KEY")
if not api_key:
    st.error("❌ API Anahtarı Bulunamadı! Secrets ayarlarını kontrol et.")
    st.stop()
else:
    st.success(f"✅ API Anahtarı mevcut (Başlangıç: {api_key[:6]}...)")

# 2. Kütüphane Sürüm Kontrolü
try:
    import google.generativeai as genai
    import importlib.metadata
    
    try:
        ver = importlib.metadata.version("google-generativeai")
    except:
        ver = "Bilinmiyor (Çok eski)"

    st.info(f"📦 Yüklü Kütüphane Sürümü: **{ver}**")
    
    # KRİTİK KONTROL: Sürüm 0.8.3'ten küçükse hata buradadır.
    if ver < "0.8.3":
        st.error("""
        ⛔ **SORUN BULUNDU!**
        Kütüphane sürümün çok eski. Bu yüzden yeni modelleri tanımıyor.
        Streamlit 'requirements.txt' dosyanı okumuyor olabilir.
        """)
    else:
        st.success("✅ Kütüphane sürümü güncel.")

    # 3. Modelleri Listeleme Testi
    st.write("---")
    st.write("📡 Google'dan Model Listesi İsteniyor...")
    
    genai.configure(api_key=api_key)
    
    try:
        models = list(genai.list_models())
        found_models = [m.name for m in models]
        st.write("📋 **Erişilebilir Modeller:**")
        st.code(found_models)
        
        if 'models/gemini-1.5-flash' in found_models:
            st.success("✅ 'gemini-1.5-flash' listede var! Kodun çalışması lazım.")
        else:
            st.warning("⚠️ 'gemini-1.5-flash' listede YOK. Başka bir model seçmeliyiz.")
            
    except Exception as e:
        st.error(f"❌ Model listesi alınamadı. Hata detayı:\n{e}")

except ImportError:
    st.error("❌ google-generativeai kütüphanesi HİÇ YÜKLENMEMİŞ!")

st.write("---")
st.info("Bu ekranı gördükten sonra sorunu bana söyle, ona göre kesin çözümü vereyim.")

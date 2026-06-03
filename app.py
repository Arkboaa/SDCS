import streamlit as st
import simpy
import random
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="SDCS", layout="wide")
st.title("🚀 SDCS: Gelişmiş Yazılım Süreç Simülasyonu")

with st.sidebar:
    st.header("👥 Ekip ve Kaynak Ayarları")
    senior_count = st.slider("Senior Yazılımcı Sayısı", 0, 5, 2)
    junior_count = st.slider("Junior Yazılımcı Sayısı", 1, 10, 4)
    tester_count = st.slider("Test Uzmanı Sayısı", 1, 5, 2)
    
    st.header("📅 Zaman ve İş Yükü")
    sim_days = st.number_input("Simülasyon Süresi (Gün)", min_value=1, max_value=90, value=14)
    arrival_rate = st.slider("Görev Geliş Sıklığı (Dakika)", 30, 300, 120)

SIM_TIME = sim_days * 1440
data = []

def gorev_sureci(env, name, ekip):
    gelis = env.now
    
    if ekip.senior.count < ekip.senior.capacity:
        pool = ekip.senior
        hiz_araligi = (200, 400)
        rol = "Senior"
    else:
        pool = ekip.junior
        hiz_araligi = (500, 800)
        rol = "Junior"

    with pool.request() as req:
        yield req
        baslama = env.now
        bekleme_suresi = baslama - gelis
        
        gelistirme_suresi_degeri = random.randint(*hiz_araligi)
        yield env.timeout(gelistirme_suresi_degeri)

    with ekip.tester.request() as req:
        yield req
        test_suresi_degeri = random.randint(80, 150)
        yield env.timeout(test_suresi_degeri)
    
    bitis = env.now

    toplam_saf_calisma = gelistirme_suresi_degeri + test_suresi_degeri
    gecen_mesai_gunu = toplam_saf_calisma / 480 
    
    bitis_gunu = (gelis / 1440) + gecen_mesai_gunu
    
    data.append({
        "Görev": name,
        "Geliş Zamanı (Dk)": int(gelis),
        "Üstlenen Rol": rol,
        "Bekleme Süresi (Dk)": int(bekleme_suresi),
        "Geliştirme Süresi (Dk)": gelistirme_suresi_degeri, 
        "Test Süresi (Dk)": test_suresi_degeri,   
        "Toplam Süre (Dk)": int(toplam_saf_calisma + bekleme_suresi),
        "Bitiş Günü": round(bitis_gunu, 1)
    })

class YazilimEkibi:
    def __init__(self, env, n_senior, n_junior, n_test):
        self.senior = simpy.Resource(env, capacity=n_senior)
        self.junior = simpy.Resource(env, capacity=n_junior)
        self.tester = simpy.Resource(env, capacity=n_test)

def jenerator(env, ekip, interval):
    i = 1
    while True:
        yield env.timeout(random.expovariate(1.0 / interval))
        env.process(gorev_sureci(env, f"Grv{i}", ekip))
        i += 1

if st.button("Final Simülasyonunu Başlat"):
    data.clear()
    
    env = simpy.Environment()
    ekip = YazilimEkibi(env, senior_count, junior_count, tester_count)
    
    env.process(jenerator(env, ekip, arrival_rate))
    env.run(until=SIM_TIME)

    if data:
        df = pd.DataFrame(data)
        df = df[df['Bitiş Günü'] <= sim_days].reset_index(drop=True)
        
        if not df.empty:
            st.write("---")
            m1, m2, m3 = st.columns(3)
            m1.metric("📊 Toplam Teslim Edilen İş", len(df))
            m2.metric("⏱️ Ortalama Çözüm Süresi", f"{df['Toplam Süre (Dk)'].mean()/60:.1f} Saat")
            
            senior_tasks = len(df[df['Üstlenen Rol'] == 'Senior'])
            m3.metric("👥 Senior / Junior Dağılımı", f"{senior_tasks} / {len(df)-senior_tasks}")
            st.write("---")

            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("👨‍💻 Rol Bazlı İş Yükü")
                fig1, ax1 = plt.subplots()
                df['Üstlenen Rol'].value_counts().plot(kind='bar', color=['#2ecc71', '#3498db'], ax=ax1)
                ax1.set_ylabel("Gorev Sayisi")
                plt.xticks(rotation=0)
                st.pyplot(fig1)

            with col2:
                st.subheader("📅 Günlük Teslimat Dağılımı")
                fig2, ax2 = plt.subplots()
                ax2.hist(df['Bitiş Günü'], bins=max(1, int(sim_days)), color='#9b59b6', edgecolor='white')
                ax2.set_xlabel("Simulasyon Gunleri")
                ax2.set_ylabel("Kapatilan Gorev Sayisi")
                st.pyplot(fig2)
                
            with col3:
                st.subheader("⏳ Bekleme Süresi Trendi")
                fig3, ax3 = plt.subplots()
                ax3.plot(df.index, df['Bekleme Süresi (Dk)'], marker='o', color='#f1c40f', label='Bekleme (Dk)')
                ax3.axhline(y=df['Bekleme Süresi (Dk)'].mean(), color='r', linestyle='--', label='Ortalama')
                ax3.set_xlabel("Gorev Sirasi")
                ax3.set_ylabel("Dakika")
                ax3.legend()
                st.pyplot(fig3)

            st.subheader("📋 Detaylı Görev Tablosu")

            def highlight_waiting(val):
                color = '#ffcccc' if val > 0 else ''
                return f'background-color: {color}'
            
            styled_df = df.style.applymap(highlight_waiting, subset=['Bekleme Süresi (Dk)'])
            st.dataframe(styled_df)
        else:
            st.warning("Bu süre sınırları içinde hiçbir görev tamamen sonuçlanamadı.")
    else:
        st.warning("Belirtilen gün süresinde hiçbir görev tamamlanamadı. Süreyi veya geliş sıklığını artırın.")
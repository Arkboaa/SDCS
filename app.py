import streamlit as st
import simpy
import random
import pandas as pd
import matplotlib.pyplot as plt


st.set_page_config(page_title="Yazılım Süreç Simülasyonu", layout="wide")
st.title("Yazılım Geliştirme Süreç Simülasyonu")

with st.sidebar:
    st.header("Simülasyon Ayarları")
    dev_count = st.slider("Yazılımcı Sayısı", 1, 10, 3)
    tester_count = st.slider("Test Uzmanı Sayısı", 1, 5, 1)
    sim_time = st.number_input("Simülasyon Süresi (Dakika)", value=3000)
    arrival_rate = st.slider("Görev Geliş Sıklığı (Dakika)", 30, 300, 120)


data = []

def gorev_sureci(env, name, ekip):
    gelis = env.now
    
    with ekip.developer.request() as req:
        yield req
        baslama = env.now
        bekleme_suresi = baslama - gelis
        
        gelistirme_suresi_degeri = random.randint(200, 800)
        yield env.timeout(gelistirme_suresi_degeri)
    
    with ekip.tester.request() as req:
        yield req
        test_suresi_degeri = random.randint(50, 150)
        yield env.timeout(test_suresi_degeri)
    
    bitis = env.now
    data.append({
        "Görev": name,
        "Geliş Zamanı": f"{gelis:.1f}",
        "Bekleme Süresi": f"{bekleme_suresi:.1f}",
        "Geliştirme Süresi": gelistirme_suresi_degeri, 
        "Test Süresi": test_suresi_degeri,   
        "Toplam Süre": bitis - gelis,
        "Bitiş Zamanı": f"{bitis:.1f}"
    })

class YazilimEkibi:
    def __init__(self, env, n_dev, n_test):
        self.developer = simpy.Resource(env, capacity=n_dev)
        self.tester = simpy.Resource(env, capacity=n_test)

def jenerator(env, ekip, interval):
    i = 1
    while True:
        yield env.timeout(random.expovariate(1.0 / interval))
        env.process(gorev_sureci(env, f"Grv{i}", ekip))
        i += 1


if st.button("Simülasyonu Başlat"):
    data.clear()
    env = simpy.Environment()
    ekip = YazilimEkibi(env, dev_count, tester_count)
    env.process(jenerator(env, ekip, arrival_rate))
    env.run(until=sim_time)

    if data:
        df = pd.DataFrame(data)
        
        
        st.subheader("Görev Bazlı Süre Dağılımı")
        fig, ax = plt.subplots(figsize=(10, 5))
    
        
        plot_df = df.head(15) 
    
        ax.bar(plot_df['Görev'], plot_df['Geliştirme Süresi'], label='Geliştirme')
        ax.bar(plot_df['Görev'], plot_df['Test Süresi'], bottom=plot_df['Geliştirme Süresi'], label='Test')
    
        ax.set_ylabel("Dakika")
        ax.set_title("Geliştirme ve Test Sürelerinin Dağılımı")
        ax.legend()
        st.pyplot(fig)

        
        st.dataframe(df)
    else:
        st.warning("Bu süre zarfında hiçbir görev tamamlanamadı. Süreyi artırmayı deneyin. 1000 değeri iyi bir başlangıç olabilir :)")
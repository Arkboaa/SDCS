import simpy
import random as rd
import pandas as pd


gelistirici= 6
test_uzmani = 1
gorev_araligi = 120
gorev_suresi = (240, 960)
test_suresi = (60, 180)

data = []

def gorev(env, isim, yazilim_ekibi):
    gelis_zamani = env.now

    with yazilim_ekibi.developer.request() as istek:
        yield istek
        baslama_zamani = env.now
        bekleme_suresi = baslama_zamani - gelis_zamani

        sure = rd.randint(*gorev_suresi)
        yield env.timeout(sure)
        print(f"{isim} geliştirildi. Süre: {sure} dk.")

    with yazilim_ekibi.tester.request() as istek:
        yield istek
        test_sure = rd.randint(*test_suresi)
        yield env.timeout(test_sure)
        print(f"{isim} testten geçti.")

    data.append(
        {
            'Görev': isim,
            'Bekleme Süresi': bekleme_suresi,
            'Toplam Süre' : env.now - gelis_zamani
        }
    )

class YazilimEkibi:
    def __init__(self,env):
        self.developer = simpy.Resource(env, capacity=gelistirici)
        self.tester= simpy.Resource(env, capacity=test_uzmani)

def gorev_olusturucu(env, yazilim_ekibi):
    i = 0
    while True:
        yield env.timeout(rd.expovariate(1.0 /gorev_araligi))
        i += 1
        env.process(gorev(env, f"Görev {i}", yazilim_ekibi))

env = simpy.Environment()
ekip = YazilimEkibi(env)
env.process(gorev_olusturucu(env,ekip))
env.run(until=5000)

df = pd.DataFrame(data)
print(f"\nOrtalama Görev Tamamlama Süresi: {df['Toplam Süre'].mean():.2f} dk")
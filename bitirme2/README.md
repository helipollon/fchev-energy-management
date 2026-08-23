# MAT 4902E — Bitirme Projesi II: Plug-in FCHEV Enerji Yönetimi Simülasyonu

**Öğrenci:** Ahmet Yeşil (090220359) · **Danışman:** Prof. Dr. Semra Ahmetolan
**Önceki aşama:** MAT 4901E raporu (`../bitirme1/report/MAT4901E_Report_final_v2.pdf`) — problemin matematiksel formülasyonu

Bu depo, Bitirme Projesi I'de (MAT 4901E) formüle edilen optimal kontrol probleminin
**sayısal çözümünü** içerir: plug-in hidrojen yakıt pilli hibrit elektrikli araçta
(FCHEV, Toyota Mirai II tabanlı) dört enerji yönetim stratejisinin (DP, A-ECMS, MPC,
BLFS) iki katmanlı bir Python simülasyon ortamında gerçeklenmesi ve karşılaştırılması.
Raporun 3.7 bölümünde ilan edilen dört iş paketinin tamamı gerçeklenmiştir:

1. İki katmanlı simülasyon ortamı (yüksek doğruluklu tesis + basitleştirilmiş kontrolcü modeli)
2. Yığın (stack) katsayılarının PSO ile metasezgisel tanılanması ve verim haritasının üretilmesi
3. Dört stratejinin gerçeklenmesi: DP kıyas ölçütü, A-ECMS, MPC, BLFS koruma katmanı
4. Referans gezi üzerinde karşılaştırma + fiyat senaryosu ve γ ceza ağırlığı duyarlılık analizi

---

## İçindekiler

1. [Hızlı başlangıç](#1-hızlı-başlangıç)
2. [Klasör yapısı](#2-klasör-yapısı)
3. [Problemin özeti ve mimari kararlar](#3-problemin-özeti-ve-mimari-kararlar)
4. [Modül modül kod dokümantasyonu](#4-modül-modül-kod-dokümantasyonu)
5. [Rapor formülasyonundan sapmalar ve gerekçeleri](#5-rapor-formülasyonundan-sapmalar-ve-gerekçeleri)
6. [Sonuçlar](#6-sonuçlar)
7. [Ayar (tuning) süreci](#7-ayar-tuning-süreci)
8. [Doğrulama ve sağlamlık kontrolleri](#8-doğrulama-ve-sağlamlık-kontrolleri)
9. [Sınırlamalar ve gelecek çalışmalar](#9-sınırlamalar-ve-gelecek-çalışmalar)
10. [Kaynaklar](#10-kaynaklar)

---

## 1. Hızlı başlangıç

```bash
cd bitirme2
pip install -r requirements.txt     # numpy + matplotlib yeterli
cd src
python3 run_all.py                  # tüm sonuçları yeniden üretir (~2 dk)
```

`run_all.py` bittiğinde:

* `results/results_default.csv` — varsayılan fiyat senaryosunda 5 strateji karşılaştırması
* `results/results_all_scenarios.csv` — 3 fiyat senaryosu × 5 strateji
* `results/gamma_sweep.json` — γ ceza ağırlığı taraması (DP)
* `results/figures/fig01…fig09.png` — tüm şekiller

Her modül tek başına da çalıştırılıp test edilebilir (her dosyanın sonunda
`if __name__ == '__main__':` altında doğrulama kodu vardır):

```bash
python3 drive_cycle.py    # gezi enerjisi kontrolü
python3 fuel_cell.py      # nominal GSSEM'in yetersizliğini gösterir
python3 param_id.py       # PSO tanılamayı baştan koşar
python3 battery.py        # batarya enerji dengesi kontrolü
```

**Rastgelelik ve tekrarlanabilirlik:** Projedeki iki rastgele süreç (polarizasyon
verisindeki ölçüm gürültüsü ve PSO başlangıç sürüsü) sabit tohumludur
(`seed=42`, `seed=7`). Kod iki kez çalıştırıldığında **bit düzeyinde aynı**
sonuçları üretir.

---

## 2. Klasör yapısı

```
bitirme2/
├── README.md                    ← bu dosya
├── requirements.txt
├── data/
│   ├── wltp_class3b_kmh.csv         resmi WLTC Class 3b hız izi (1 Hz, 1801 örnek)
│   ├── mirai_polarization.csv       tanılama hedefi polarizasyon verisi (35 nokta)
│   └── identified_stack_params.json PSO çıktısı (önbellek; silinirse yeniden koşar)
├── src/
│   ├── config.py                MERKEZI parametre dosyası (tüm sabitler burada)
│   ├── drive_cycle.py           WLTP → P_load(t) yük yörüngesi        [Denk. 3-4]
│   ├── fuel_cell.py             Mann–Amphlett GSSEM yığın modeli      [Denk. 5-11]
│   ├── make_polarization_data.py tanılama hedef verisinin üretimi
│   ├── param_id.py              PSO ile katsayı tanılama              [Bölüm 3.3.2]
│   ├── battery.py               1-RC + histerezis ve Rint modelleri   [Denk. 12-15, 17-18]
│   ├── cost_model.py            güç akışı + parasal maliyet + SoC referansı [Denk. 16, 19-23]
│   ├── simulate.py              iki katmanlı kapalı çevrim simülatörü
│   ├── run_all.py               ana betik: tüm sonuçlar + şekiller
│   └── ems/
│       ├── dp.py                Dinamik Programlama kıyas ölçütü      [Denk. 27]
│       ├── aecms.py             Uyarlamalı ECMS                       [Denk. 28-29]
│       ├── mpc.py               Model Öngörülü Kontrol                [Denk. 30]
│       └── blfs.py              Sınır Katmanı Yüzey İzleme            [Denk. 31]
└── results/
    ├── results_default.csv, results_all_scenarios.csv, gamma_sweep.json
    └── figures/fig01…fig09.png
```

---

## 3. Problemin özeti ve mimari kararlar

### 3.1 Optimal kontrol problemi (rapor Denk. 25-26)

Tek karar değişkeni, DC/DC dönüştürücünün baraya verdiği güçtür: `u(t) ≡ P_dc(t) ≥ 0`.
Bara güç dengesi `P_bat = P_load − P_dc` (Denk. 2) sayesinde tek değişken güç
paylaşımını tamamen belirler. Tek durum değişkeni bataryanın şarj durumudur
(`x ≡ SoC`). Amaç, gezinin toplam parasal maliyetini (hidrojen + şebeke-eşdeğeri
elektrik + terminal SoC cezası) en aza indirmektir:

```
min Σ L_k(SoC_k, P_dc,k) + γ(SoC_N − 0.25)²,   L_k = C_fc,k + C_bat,k
```

N = 3600 karar noktası (Δt = 1 s), SoC penceresi [0.20, 0.95],
SoC₀ = 0.90 → hedef 0.25 (şarj tüketen / charge-depleting plug-in senaryosu).

### 3.2 Neden bu mimari kararlar?

| Karar | Seçim | Gerekçe |
|---|---|---|
| Dil | Python 3 + NumPy | Raporda (Bölüm 3.7) taahhüt edildi; vektörleştirilmiş NumPy ile DP arka geçişi 2.5 s sürer — MATLAB'a ihtiyaç bırakmaz; ücretsiz ve tekrarlanabilir. |
| Bağımlılık | Yalnızca numpy + matplotlib | Kurulum sürtünmesini sıfırlamak, sürüm çürümesini önlemek. SciPy'siz PSO ve grid-DP zaten yeterli (skaler durum!). |
| İki katman | Tesis: GSSEM + 1-RC+histerezis; Kontrolcü: verim LUT + Rint | Onori'nin [14] iki seviyeli yaklaşımı (rapor Bölüm 3.3.3). Gerçek araçta kontrolcü asla mükemmel model bilgisine sahip değildir; RAPORLANAN HER SAYI tesis modelinden gelir, kontrolcü modeli yalnızca karar üretir. Model uyumsuzluğunun maliyeti böylece dürüstçe ölçülür. |
| Topoloji | T4 (FC → tek yönlü DC/DC → bara; batarya doğrudan barada) | Rapor Bölüm 3.2'de sabitlendi; Mirai'nin gerçek mimarisi. |
| Zaman çözünürlüğü | Δt = 1 s | WLTP izi 1 Hz; EMS saniye ölçeğinde çalışır, yığın sıcaklığı gibi dakika ölçekli dinamikler kapsam dışı (rapor, izotermal varsayım). |
| Tekrarlanabilirlik | Sabit RNG tohumları + önbelleğe alınmış tanılama | Bilimsel raporlanabilirlik: `identified_stack_params.json` silinmedikçe PSO tekrar koşmaz; silinirse aynı tohumla aynı sonucu üretir. |

### 3.3 Veri kaynakları

* **Hız profili:** Resmi WLTC Class 3b izi (UN GTR 15 [21]), `wltp` Python paketinin
  regülasyon sağlama toplamı doğrulanmış veri tabanından dışa aktarıldı
  (1801 örnek, 23.27 km, v_max = 131.3 km/h). İki çevrim ardışık eklenerek
  46.53 km / 3600 s'lik referans gezi elde edildi. İki çevrim gerekli, çünkü
  7.92 kWh'lik paketin anlamlı miktarda boşalması ancak bu mesafede mümkün
  (rapor Bölüm 3.2).
* **Polarizasyon verisi:** [17]'de yayımlanan Mirai II FCB130 çalışma noktaları
  (ayrıntı: Bölüm 4.4 ve 5.1).
* **Batarya parametreleri:** Nejad ve ark. [11] hücre parametreleri (LFP,
  A123 ANR26650M1B), 96s10p paket ölçekli.

---

## 4. Modül modül kod dokümantasyonu

### 4.1 `config.py` — merkezi parametre dosyası

**Ne yapar:** Projede kullanılan HER sabit (fiziksel sabitler, Mirai parametreleri
Tablo 2, batarya paketi, fiyat senaryoları Tablo 3, çözücü ayarları) tek dosyada
toplanır.

**Neden böyle:** Parametrelerin koda dağılması, "raporda 0.95 yazıyor ama kodda
0.92 kullanılmış" türü tutarsızlıkların bir numaralı kaynağıdır. Tek dosya →
tek gerçek. Türetilmiş büyüklükler (paket direnci `Rs_pack = Rs_cell·Ns/Np`,
paket kapasitesi, akım limitleri) da burada hesaplanır ki ölçekleme kuralı
(seri: gerilim ve direnç çarpanı; paralel: kapasite çarpanı, direnç böleni;
RC zaman sabiti ölçeklemeden bağımsız — rapor Bölüm 3.3.3) tek yerde görünsün.

Önemli türetilmiş değerler:
`Q_pack = 25 Ah`, `Rs_pack = 76.8 mΩ`, `R1_pack = 57.6 mΩ`, `τ₁ = R₁C₁ = 180 s`,
`E_nom ≈ 7.92 kWh`, `P_dc_max = 104.5 kW` (110 kW net × 0.95 dönüştürücü verimi).

### 4.2 `drive_cycle.py` — yük yörüngesi

**Ne yapar:** Boylamsal araç dinamiği dengesi (Denk. 3) ile tekerlek gücünü,
yön-bağımlı aktarma organı verimi (Denk. 4) ile bara yükünü hesaplar:

```
P_wheel = [m·a + m·g·Cr + ½·ρ·Cd·Af·v²] · v        (düz yol, α = 0)
P_load  = P_wheel/η_dt   (çekiş)   |   P_wheel·η_dt   (rejeneratif frenleme)
```

**Kod içi seçimler:**

* İvme **ileri fark** ile hesaplanır (`a_k = (v_{k+1} − v_k)/Δt`): karar
  değişkenindeki sıfırıncı derece tutucu (ZOH) ile tutarlıdır — k. aralığın güç
  talebi, aracı v_k'dan v_{k+1}'e taşıyan güçtür.
* Yuvarlanma direnci `v > 0.1 m/s` maskesiyle çarpılır: araç dururken
  yuvarlanma direnci kuvveti uygulanmaz (aksi halde duraklarda hayalet güç
  talebi doğar).
* Yük, motor anma gücünde (134 kW) doyurulur — WLTP'de hiç etkin olmaz
  (maks. 54.4 kW) ama fiziksel tutarlılık için durur.

**Doğrulama çıktısı:** 46.53 km, çekiş enerjisi 8.56 kWh, geri kazanılabilir
2.13 kWh. Net talep (~6.4 kWh) batarya bütçesini (0.65·7.92 ≈ 5.15 kWh)
aştığı için yakıt pili kullanımı ZORUNLUDUR — problem dejenere değildir
(yalnız-batarya çözümü SoC penceresini ihlal eder; `battery.py` testi bunu
SoC_f = 0.053 < 0.20 ile doğrular).

### 4.3 `fuel_cell.py` — Mann–Amphlett GSSEM

**Ne yapar:** Tek hücre gerilimini dört terimden kurar (Denk. 5-9):

```
V_FC = E_Nernst − V_act − V_ohm − V_con
```

* `E_Nernst` (Denk. 6): termodinamik potansiyel, sıcaklık ve kısmi basınç düzeltmeli.
* `V_act` (Denk. 7): yarı-ampirik Tafel tipi aktivasyon kaybı; çözünmüş O₂
  derişimi Henry yasasından: `C*_O2 = p*_O2 / (5.08·10⁶·e^(−498/T))`.
* `V_ohm` (Denk. 8): membran özdirenci Mann korelasyonu ile — etkin su içeriği
  λ, akım yoğunluğu ve sıcaklığın fonksiyonu; `R_M = ρ_M·l/A` + temas direnci.
* `V_con` (Denk. 9): `−β·ln(1 − J/J_max)` derişim kaybı.

**Kritik tasarım noktası — hidrojen tüketimi:** Kütle debisi ampirik değil,
**Faraday yasasından kesin** hesaplanır:

```
ṁ_H2 = N_cell · I · M_H2 / (2F)
```

Bunun sonucu, LHV yığın veriminin hücre gerilimiyle orantılı olmasıdır:
`η_fc = V_cell / 1.254 V`. Yani Denk. (11)'deki verim haritası TAMAMEN
polarizasyon eğrisinden türetilir — tanılama kalitesi doğrudan tüketim
doğruluğuna çevrilir. Raporun "verim haritası çevrimdışı türetilip 1-B arama
tablosu olarak saklanacak" taahhüdü `build_lut()` ile yerine getirilir.

**`build_lut()` inceliği:** P(J) eğrisinin yalnızca tepe güce kadarki monoton
artan dalı tutulur. Tepenin ötesinde aynı güç daha düşük J'de (daha az
hidrojenle) elde edilebildiğinden rasyonel bir kontrolcü orada asla çalışmaz;
dalın atılması arama tablosunun tersinir (birebir) olmasını garanti eder.

**Dosya sonu testi** nominal Mann katsayılarının Mirai'yi temsil ETMEDİĞİNİ
gösterir (tepe 50.9 kW ≪ 128 kW, verim 0.27-0.51): tanılamanın gerekliliğinin
sayısal kanıtı.

### 4.4 `make_polarization_data.py` — tanılama hedef verisi

**Ne yapar:** [17]'de raporlanan Mirai II çapa noktalarından tanılama hedefi
polarizasyon veri seti üretir:

* η ≈ 0.70 @ 12 kW brüt → V_cell = 0.70·1.254 = 0.878 V (J ≈ 0.138 A/cm²)
* η ≈ 0.54 @ 128 kW brüt → V_cell = 0.677 V (J ≈ 1.91 A/cm²)
* Hava katotlu açık devre ≈ 0.95-0.98 V

Çapalar arası, otomotiv yığınlarının kanonik eğri şekliyle (aktivasyon bölgesinde
ln(J)'de doğrusal) 35 noktaya yoğunlaştırılır ve σ = 3 mV Gauss ölçüm gürültüsü
eklenir.

**Neden gürültü ekleniyor?** Gürültüsüz sentetik veri, tanılama problemini
yapay biçimde kolaylaştırır (mükemmel uyum mümkün olur); 3 mV, polarizasyon
ölçümlerinin tipik tekrarlanabilirlik bandıdır ve PSO'nun gerçekçi bir RMSE
tabanına yakınsamasını sağlar.

**Şeffaflık notu:** [17]'nin ham sayısallaştırılmış verisi elimizde olmadığından
bu YENİDEN İNŞA EDİLMİŞ temsili veridir. Gerçek sayısallaştırılmış veri temin
edildiğinde tek yapılacak şey `data/mirai_polarization.csv`'yi değiştirmek ve
`data/identified_stack_params.json`'u silmektir — boru hattının kalanı aynen
çalışır (bkz. Bölüm 5.1).

### 4.5 `param_id.py` — PSO ile katsayı tanılama

**Ne yapar:** 8 boyutlu karar vektörünü
`θ = [ξ₁, ξ₂, ξ₃, ξ₄, λ, R_C, β, J_max]`
polarizasyon RMSE'sini en aza indirerek tanılar. Sınırlar Fang ve ark. [7]'nin
taradığı literatür aralıklarıdır.

**Neden PSO (gradyan tabanlı değil)?**

1. Amaç fonksiyonu **konveks değildir**: ξ₁ saf kaydırma, ξ₃ ise `ln(C*_O2)`
   çarpanı olduğundan ikisi arasında uzun korelasyon vadileri oluşur; λ ile R_C
   düşük akımda neredeyse değiştirilebilirdir. Gradyan yöntemleri bu vadilerde
   durur.
2. Model cebirseldir → binlerce değerlendirme bedavadır (35 nokta × 6000
   parçacık-iterasyon < 1 s).
3. PSO, PEMFC tanılama literatürünün referans yöntemidir [7] ve raporda
   taahhüt edilmiştir ("PSO/GA").

**Algoritma ayrıntıları (hepsi kodda gerekçeli):**

* Kanonik küresel-en-iyi PSO, Clerc daralma katsayıları
  `w = 0.7298, c₁ = c₂ = 1.4962` (literatür standardı, kararlılık garantili).
* 40 parçacık × 150 iterasyon; hız, kutu genişliğinin %20'sine kelepçeli
  (patlamayı önler); sınır ihlalinde **yansıtma** (parçacıklar fiziksel kutuda
  kalır, sınıra yapışma azalır).
* Fiziksellik koruması: V ≤ 0 veya NaN üreten parçacığa 10³ ceza.

**Sonuç:** RMSE = **6.4 mV** (35 nokta üzerinde), tanılanan yığın tepe gücü
138 kW, η(12 kW) = 0.703, η(128 kW) = 0.52. PSO yakınsama eğrisi ve uyum
`results/figures/fig02_polarization_pso.png`'de.

### 4.6 `battery.py` — iki batarya modeli

**`PlantBattery` (tesis katmanı):** 3 durumlu yüksek doğruluklu model.

* **SoC** — Coulomb sayımı (Denk. 13), `η_i = 0.995`.
* **V_RC1** — difüzyon/rölaksasyon gerilimi (Denk. 12):
  `V_RC1(k+1) = a·V_RC1(k) + b·i_k`, `a = e^(−Δt/τ)`, `τ = 180 s`.
* **V_OC** — histerezisli açık devre gerilimi (Huria yasası, Denk. 15): OCV,
  şarj yönüne göre şarj/deşarj referans dalına `m_hyst = 150` oranıyla ve
  **şarj çıkışı |ΔSoC| üzerinden** gevşer (histerezis zamanla değil, işlenen
  yükle ilerler — LFP histerezisinin deneysel karakteri [12]).

Uç gerilim denklemi (Denk. 14) `V = V_OC − i·Rs − V_RC1` güç talebiyle
birleştirilince akım için ikinci derece denklem doğar; fiziksel kök (Denk. 17):

```
I = [(V_OC − V_RC1) − √((V_OC − V_RC1)² − 4·Rs·P_bat)] / (2·Rs)
```

Diskriminantın negatifliği paket güç kabiliyet sınırını doğal biçimde kodlar
(rapor, Denk. 17 altı). Ek olarak veri sayfası akım limitleri uygulanır:
sürekli şarj 4C (100 A paket), deşarj 20C (500 A paket). 4C sınırını aşan
rejeneratif güç **sürtünme frenlerine** gider (`P_friction` olarak raporlanır,
ne maliyet ne kazanç yazar).

**Neden LFP'de histerezis vazgeçilmez?** LFP'nin OCV eğrisi %20-80 SoC arası
neredeyse düzdür (paket düzeyinde ~5 V'luk bant); şarj/deşarj dalları arası
25-40 mV/hücre fark, düz bölgede SoC kestirimini domine eder [11],[12].
OCV dalları, [11]'deki gibi **8. derece polinomlarla** temsil edilir; polinom,
yoğun yeniden örneklenmiş düğüm eğrisine uydurulur (Runge salınımının plato
bölgesini bozmasını önlemek için).

**`RintModel` (kontrolcü katmanı):** Durumsuz, vektörleştirilmiş statik model —
ortalama OCV dalı + yalnız Rs. KASITLI olarak tesisten daha az doğrudur:
gerçek kontrolcünün model bilgisi eksiktir; iki katman arasındaki fark, model
uyumsuzluğunun maliyet etkisini ölçer (rapor Bölüm 3.3.3'ün iki seviyeli
yaklaşımı). DP'nin 151×105'lik geçiş tensörünü tek NumPy geçişinde
değerlendirebilmesi de bu modelin cebirselliği sayesindedir.

### 4.7 `cost_model.py` — güç akışı, maliyet ve SoC referansı

**Güç akış zinciri (Denk. 16):** `P_dc → P_fc,net = P_dc/η_dc → P_fc,gross`
(yardımcı tüketim eklenerek) `→ ṁ_H2` (verim LUT'u).

**Yardımcı tüketim modeli (rapordan bilinçli sapma — bkz. Bölüm 5.2):**
`P_aux = 1.0 kW + 0.09·P_gross` (FC açıkken). Rapor sabit oran (~0.10-0.13
[17]) der; sabit oran, tank-bara verimini güçte monoton yapar ve yakıt pilinin
İÇ optimum çalışma noktasını yok eder — oysa Mirai'nin ölçülen sistem verimi
12 kW civarında tepe yapar [17]. Sabit taban (kompresör rölantisi, pompalar,
kontrol elektroniği) + orantısal terim, hem 30 kW üzerinde 0.10-0.13 bandında
kalır hem de iç tepeyi yeniden üretir (fig03).

**Maliyetler:**

* `C_fc` (Denk. 19): `M_H2 · ṁ_H2 · Δt` — karardan bağımsız durumla, her zaman ≥ 0.
* `C_bat` (Denk. 20-21): yön-bağımlı verimle şebeke-eşdeğeri değerleme.
  Deşarjda bara enerjisi başına yatırılan şebeke enerjisi 1'i aşar
  (gidiş-dönüş çarpanına bölme); şarjda yalnız geri kazanılabilir kesir
  alacaklandırılır (çarpma). η_dis = V_uç/V_OC ve η_chg = V_OC/V_uç Rint
  modelinden anlık hesaplanır; 0.98 çarpanı kulombik/şarj cihazı payını
  simetrik dağıtır. Frenleme kazancı böylece şebeke değerinden otomatik
  alacaklandırılır (C_bat şarjda negatif).
* Terminal ceza (Denk. 23): `γ(SoC_N − 0.25)²`, γ = 1000 €.

**Şarj kısıtlaması (curtailment) — kritik uygulama detayı:** `stage_cost()`
şarj gücünü iki fiziksel mekanizmayla kırpar: (1) 4C veri sayfası sınırı,
(2) SoC_max tavanı (BMS konikleştirmesi). (2) olmadan DP durum ızgarasının
üst sınırı, SoC_max yakınında rejenerasyon olan HER adımda sahte biçimde
"olanaksız" olur ve sonsuz maliyet, doğrusal interpolasyon yoluyla iç
düğümlere sızarak TÜM değer fonksiyonunu zehirler (geliştirme sırasında
birebir yaşandı: V₀ = inf). Kırpılan güç sürtünme frenine gider ve
alacaklandırılmaz.

**SoC referansı — enerji tabanlı (rapordan gerekçeli sapma, bkz. Bölüm 5.3):**
Denk. (29)'un zamanda doğrusal referansı kapalı çevrimde İZLENEMEZ çıktı:
duraklarda ve son yavaşlamada çekiş yükü yokken batarya fiziksel olarak
boşaltılamaz, referans ise düşmeye devam eder → tüm gerçek zamanlı stratejiler
hedefin ~0.025 üstünde mahsur kalıp stratejinin değil referans tasarımının
cezasını öder. Çözüm (plug-in EMS literatüründe standart, örn. [14] Böl. 6):
referansı **birikimli pozitif çekiş enerjisinde** doğrusal yapmak:

```
ref(k) = SoC₀ + (SoC_hedef − SoC₀) · E_cum(k)/E_toplam
```

E_cum çevrim istatistiğidir; DP'nin zaten yaptığı "gezi önceden biliniyor"
varsayımının aynısını kullanır (gerçek araçta navigasyondan gelir).
`set_reference()` çağrılmazsa kod Denk. (29)'un zaman-doğrusal referansına
geri düşer.

### 4.8 `ems/dp.py` — Dinamik Programlama kıyas ölçütü

**Ne yapar:** Bellman geri özyinelemesini (Denk. 27) raporun ızgaralarında
(ΔSoC = 0.005 → 151 düğüm; ΔP_dc = 1 kW → 105 karar) çözer; Sundström &
Guzzella'nın [15] uygulama yapısını izler.

**Uygulama kararları:**

* **Değer interpolasyonu:** Ardıl durum SoC' genelde düğümler arasına düşer;
  V_{k+1}(SoC') doğrusal interpolasyonla alınır. Alternatif olan en-yakın-düğüm
  ataması, ızgara nicemleme gürültüsünü politikaya çevirir (bilinen çatırdama
  problemi [15]).
* **Vektörleştirme:** Her zaman adımında 151×105'lik maliyet+geçiş tensörü tek
  NumPy geçişiyle değerlendirilir → 3600 adımlık geri geçiş **2.5 saniye**.
  Bu hız, statik FC modeli seçiminin (rapor Bölüm 3.1.2: dinamik modele göre
  iki kertelik işlem tasarrufu) somut karşılığıdır.
* **Politika tablosu + kapalı çevrim ileri geçiş:** Geri geçiş u*(k, SoC)
  tablosu üretir; ileri geçiş bu politikayı TESİS modeline karşı kapalı
  çevrimde oynatır (SoC düğümleri arasında kontrol de interpolasyonlu).
  Böylece DP'nin raporlanan maliyeti bile model uyumsuzluğunu içerir —
  kontrolcü-modeli-içinde-açık-çevrim maliyet raporlamanın iyimser yanlılığı
  yoktur. (Geri geçişin kendi öngörüsü 2.733 €, tesiste gerçekleşen 2.718 € —
  %0.5 uyum, model uyumsuzluğunun küçüklüğünün de göstergesi.)
* Tüm gezi yükü önceden bilindiğinden DP yalnızca çevrimdışı kıyas ölçütüdür
  (rapor Tablo 4).

### 4.9 `ems/aecms.py` — Uyarlamalı ECMS

**Ne yapar:** Her adımda Hamiltonyeni (Denk. 28) 1 kW'lık karar ızgarasında
noktasal en aza indirir:

```
H(u) = L(SoC, u) + s(t)·(SoC_k − SoC_{k+1}(u))
```

PMP eş-durumu λ'nın yerini alan eşdeğerlik çarpanı s(t), SoC izleme hatası
üzerinde PI yasasıyla uyarlanır (Denk. 29, Gao [5]):

```
s(t) = s₀ + k_p·e + k_i·∫e,    e = SoC_ref − SoC
```

**Plug-in inceliği (rapor Bölüm 3.5.2 + Xu [4]):** Klasik ECMS'te s, yakıt
eşdeğerliğini TEK BAŞINA kurar. Burada L zaten batarya enerjisini şebeke
fiyatıyla parasallaştırdığından ekonomik takas tamamen L'nin içindedir;
s'nin tek görevi şarj-tüketen referansı izletmektir. Bu yüzden **s₀ = 0**
seçilir — sezgisel taban değere gerek yoktur, tasarım temizlenir.
Sabit çarpanın stratejiyi fiziksel sınırlara savurduğu [4]'te gösterilmişti;
PI geri beslemesi bunu önler.

* **Anti-windup:** İntegratör `|k_i·∫e| ≤ 2 €/SoC` ile kelepçelidir; gezi
  sonunda eyleyici doyunca integral patlamasını önler.
* SoC alt penceresi ihlali üreten kararlara H = ∞ (üst pencere, maliyet
  modelindeki kısıtlamayla zaten korunur).

### 4.10 `ems/mpc.py` — Model Öngörülü Kontrol

**Ne yapar:** Her adımda Denk. (30)'un sonlu ufuklu kısıtlamasını çözer:
N_p = 15 s ufuk, sabit-yük varsayımı (`P_load(j) = P_load(k)` — telematik
önizleme yok), yalnız ilk hamle uygulanır.

**Neden QP değil grid-DP? (rapordan gerekçeli sapma, bkz. Bölüm 5.4):**
Aşama maliyeti P_dc'de **konveks değildir** (hidrojen haritası tanılanan
polarizasyonun eğriliğini taşır; Denk. 20'nin yön-bağımlı verimi P_bat = 0'da
kırılma yaratır). QP konveks vekil ister ve vekilin minimumunu döndürür.
Durum skaler olduğundan yerel kapsamlı DP ucuzdur: SoC en fazla ~0.002/s
hareket eder → mevcut SoC ±0.03 penceresi (31 düğüm × 0.002) ufkun
erişebileceği her yörüngeyi örter; 2 kW karar ızgarasıyla alt problem
milisaniyeler içinde ızgara çözünürlüğünde KESİN çözülür (ölçülen: 0.59
ms/adım). Sabit-yük varsayımı geçiş/maliyet tensörlerini ufuk boyunca ortak
kılar → tensörler adım başına bir kez kurulur.

**Ofsetsiz düzeltme:** Sabit-yük varsayımı yanlıdır — çekiş piklerinde
kontrolcü pikin tüm ufuk boyunca süreceğini sanıp bataryayı aşırı korur
(FC'yi tam da boşaltma fırsatı varken yakar); hiçbir sonlu γ_mpc bu kalıcı
model yanlılığını gideremez (MPC'nin klasik ofset problemi). Standart çare,
izleme hatasında integral etki: izlenen referans, alçak geçirenle biriktirilen
yanlılık kadar kaydırılır (`β = 0.005`, taramayla seçildi — Bölüm 7.3).

### 4.11 `ems/blfs.py` — koruma katmanı

**Ne yapar:** Bağımsız strateji DEĞİL; A-ECMS veya MPC'nin altına sarılan
kural tabanlı koruma (rapor Bölüm 3.6.5). Referans etrafında ±0.05 histerezis
bandı:

* bandın ÜSTÜnde → FC minimumda (P_dc = 0): batarya banda geri boşaltılır;
* bandın ALTInda → FC **tepe sistem verimi** noktasında: batarya en ucuz
  hidrojen maliyetiyle şarj edilir;
* bandın İÇİnde → üst katman kararı aynen geçer.

Tepe verim noktası, tank-bara verimi `η_sys = P_dc/(ṁ·LHV)` en büyükleyicisi
olarak LUT'tan BİR KEZ hesaplanır (dönüştürücü + yardımcı kayıplar dahil —
bataryaya FC üzerinden konan bir joule'ün en ucuz olduğu nokta).

Ek olarak yakıt pili yük rampası sınırlanır (Denk. 31): `|dP_fc/dt| ≤ 5 kW/s`
— gaz açlığı ve membran yıpranmasına karşı; maliyet fonksiyonuna girmeden
dayanıklılığı korur. Sınır bara tarafı komuta uygulanır; P_dc ↔ P_gross
eşlemesi düzgün ve monoton olduğundan brüt tarafta da (hafifçe daha sıkı)
bir sınır ima eder.

### 4.12 `simulate.py` — iki katmanlı kapalı çevrim

Adım döngüsü: (1) kontrolcü kararı `u_k` (duvar saatiyle zamanlanır →
adım başına CPU süresi metriği), (2) `P_bat = P_load − u` tesise uygulanır
(kırpma + sürtünme freni tesiste), (3) hidrojen debisi LUT zincirinden,
(4) parasal muhasebe TESİS yörüngesi üzerinden (Denk. 19-22).

Raporlanan metrikler (rapor Bölüm 3.7 listesiyle bire bir): toplam işletme
maliyeti [€ ve €/100 km], H₂ kütlesi [kg], batarya elektriği [kWh], terminal
SoC hatası, FC yarı-kararlılığı (ortalama |ΔP_fc| ve açma/kapama sayısı),
adım başına ortalama CPU süresi.

### 4.13 `run_all.py` — ana betik

Tüm boru hattını sırayla koşar ve HER şekli koddan üretir (elle çizim yok —
dokümantasyon kodla senkron kalır). Kontrolcü nesneleri durum taşıdığından
(integratörler, rampa hafızası) her senaryo için taze örnekler kurulur
(`make_controllers`).

---

## 5. Rapor formülasyonundan sapmalar ve gerekçeleri

Uygulama, MAT 4901E formülasyonuna sadık kalmayı hedefledi; aşağıdaki dört
noktada gerekçeli sapma vardır. Her biri kod içinde de belgelidir.

### 5.1 Polarizasyon verisi temsilidir

[17]'nin ham verisi sayısallaştırılamadığından tanılama hedefi, [17]'nin
yayımlanmış çapa noktalarından yeniden inşa edildi (Bölüm 4.4). Boru hattı
veri-agnostiktir: gerçek veri geldiğinde tek CSV değişir.

### 5.2 Yardımcı tüketim: sabit oran yerine afin model

`P_aux = 1 kW + 0.09·P_gross`. Sabit oran iç verim tepesini yok ediyordu;
afin model hem [17]'nin 0.10-0.13 bandını (>30 kW) hem de ölçülen ~12 kW'lık
sistem tepe noktasını yeniden üretir. BLFS'in "tepe verim noktası" kavramı
ancak bu tepe varsa anlamlıdır.

### 5.3 SoC referansı: zamanda değil enerjide doğrusal

Zaman-doğrusal referans (Denk. 29) son yavaşlamada fiziksel olarak izlenemez
ve tüm gerçek zamanlı stratejilere ~0.5-0.8 € haksız terminal cezası yüklüyordu
(geliştirme günlüğü: A-ECMS SoC_f = 0.227, MPC = 0.275). Enerji tabanlı
referans bu yapısal hatayı kaynağında giderdi; DP'ye dokunmaz (DP referans
kullanmaz).

### 5.4 MPC: QP yerine yerel grid-DP + ofsetsiz integral düzeltme

Konveks olmayan aşama maliyeti QP'yi vekile mahkûm eder; skaler durumda
yerel kapsamlı arama hem kesin hem gerçek-zaman-uyumludur (0.59 ms/adım).
Sabit-yük varsayımının kalıcı SoC ofseti, standart ofsetsiz-MPC integral
etkisiyle (β = 0.005) giderildi. Her iki karar da Bölüm 4.10'da ayrıntılı.

---

## 6. Sonuçlar

### 6.1 Varsayılan senaryo (Almanya 2026: 11 €/kg H₂, 0.35 €/kWh)

| Strateji | Toplam [€] | DP'ye fark | İşletme [€/100km] | H₂ [g] | Elektrik [kWh] | SoC_f | FC aç/kapa | CPU [ms/adım] |
|---|---|---|---|---|---|---|---|---|
| **DP** (kıyas) | **2.718** | — | 5.84 | 77.6 | 5.15 | 0.249 | 85 | 0.016 |
| MPC | 2.746 | +%1.0 | 5.85 | 79.5 | 5.11 | 0.255 | 64 | 0.59 |
| MPC+BLFS | 2.752 | +%1.2 | 5.86 | 80.0 | 5.11 | 0.255 | 50 | 0.60 |
| A-ECMS | 2.783 | +%2.4 | 5.85 | 80.3 | 5.09 | 0.258 | 154 | 0.21 |
| A-ECMS+BLFS | 2.795 | +%2.8 | 5.86 | 80.8 | 5.08 | 0.258 | 54 | 0.25 |

**Okuma:**

* Beklenen hiyerarşi doğrulandı: küresel optimum DP en ucuz; gerçek zamanlı
  stratejiler %1-3 bandında — literatürdeki tipik ECMS/MPC boşluğuyla uyumlu.
* Grid elektriği LHV bazında hidrojenden ucuz olduğundan (rapor Bölüm 3.5.2
  öngörüsü) tüm stratejiler bataryayı sınırına kadar kullanır: 5.1-5.15 kWh
  batarya, ~78-81 g H₂. Yakıt pili yalnız batarya bütçesinin yetmediği açığı
  kapatır — teorik beklentinin sayısal doğrulaması.
* **BLFS maliyeti ~%0.2-0.4 artırır ama FC aç/kapa sayısını 154 → 54 ve
  104 → 50'ye düşürür, ortalama rampayı yarılar** (654 → 306 W/adım):
  membran ömrü için küçük parasal prim — koruma katmanı rolü aynen raporda
  öngörüldüğü gibi.
* CPU süreleri gerçek zaman bütçesinin çok altında (≤ 0.6 ms ≪ 1000 ms):
  A-ECMS ve MPC üretim adayı, DP çevrimdışı — rapor Tablo 4 doğrulandı.
* Gezi maliyeti ~5.9 €/100 km; karşılaştırma: aynı fiyatlarla salt-hidrojen
  Mirai ~76 kWh_H2/100km·(11/33.3) ≈ 8+ €/100 km — plug-in mimarinin
  ekonomik gerekçesi.

### 6.2 Fiyat senaryosu duyarlılığı (rapor Tablo 3)

| Senaryo | H₂ [€/kg] | Elek. [€/kWh] | DP [€] | A-ECMS [€] | MPC [€] |
|---|---|---|---|---|---|
| Yüksek | 13.85 | 0.40 | 3.203 | 3.242 | 3.228 |
| Varsayılan | 11.00 | 0.35 | 2.718 | 2.783 | 2.746 |
| Düşük | 8.00 | 0.32 | 2.325 | 2.431 | 2.361 |

Üç senaryoda da elektrik hidrojenden ucuz kaldığından optimal politika yapısı
değişmez (maks. batarya + açık kapatan FC); maliyetler fiyatlarla ölçeklenir,
strateji sıralaması korunur. H₂ tüketimi senaryolar arasında yalnız %±2 oynar
— politika fiyat oranına bu bölgede duyarsızdır (kısıt bağlayıcıdır: batarya
bütçesi zaten tükenmektedir).

### 6.3 γ ceza ağırlığı taraması (DP)

| γ [€] | 100 | 300 | 1000 | 3000 | 10000 |
|---|---|---|---|---|---|
| SoC_f | 0.2395 | 0.2449 | 0.2494 | 0.2495 | 0.2495 |
| İşletme maliyeti [€] | 2.694 | 2.706 | 2.717 | 2.721 | 2.726 |

γ = 1000 (raporun boyut analizine dayalı seçimi, Denk. 23): terminal hata
< 0.001'e iner, işletme maliyeti henüz şişmez — **raporun seçimi taramayla
doğrulanmıştır.** γ < 300'de kontrolcü cezayı "satın alıp" hedefi kaçırır;
γ > 3000'de kazanç yok, maliyet katılaşır.

### 6.4 Şekiller (`results/figures/`)

| Dosya | İçerik |
|---|---|
| fig01_cycle_load.png | 2×WLTC 3b hız izi + P_load yörüngesi (Denk. 3-4) |
| fig02_polarization_pso.png | Polarizasyon uyumu (veri/tanılanmış/nominal) + PSO yakınsaması |
| fig03_efficiency_map.png | Yığın LHV verimi ve tank-bara sistem verimi; sistem tepesi işaretli |
| fig04_ocv_hysteresis.png | LFP OCV şarj/deşarj dalları, histerezis bandı, çalışma penceresi |
| fig05_soc_trajectories.png | 5 stratejinin SoC yörüngeleri + enerji tabanlı referans |
| fig06_pdc_profiles.png | Strateji başına P_dc(t) profilleri (yük gölgeli) |
| fig07_cost_breakdown.png | Maliyet ayrışımı: H₂ / elektrik / terminal ceza |
| fig08_sensitivity.png | 3 fiyat senaryosu × 5 strateji toplam maliyet |
| fig09_gamma_sweep.png | γ'ya karşı terminal SoC ve işletme maliyeti (DP) |

---

## 7. Ayar (tuning) süreci

Tüm ayar deneyleri varsayılan senaryoda, aynı tohumlarla yapıldı; nihai
değerler `config.py`'de gerekçe yorumlarıyla durur.

### 7.1 Ayarsız kalanlar

DP ve modellerin hiçbir parametresi ayarlanmadı (rapor + birincil kaynak
değerleri). Izgara çözünürlükleri raporun belirttiği değerlerdir
(ΔSoC = 0.005, ΔP_dc = 1 kW).

### 7.2 A-ECMS PI kazançları

| (k_p, k_i) | Toplam [€] | SoC_f | Not |
|---|---|---|---|
| (60, 0.1) | 3.198 | 0.227 | gevşek izleme, büyük terminal ceza |
| **(150, 0.3)** | **2.783** | **0.258** | seçilen |
| (300, 0.5) | 3.144 | 0.270 | aşırı agresif, FC gereksiz yanıyor |
| (150, 1.0) | 3.064 | 0.267 | integral baskın, salınım |

### 7.3 MPC ofsetsiz-integral kazancı β

| β | 0 | 0.005 | 0.01 | 0.02 |
|---|---|---|---|---|
| Toplam [€] | 3.013 | **2.746** | 3.011 | 3.220 |
| SoC_f | 0.267 | 0.255 | 0.266 | 0.272 |

β küçük ama sıfırdan farklı olmalı: 0.005 kalan yanlılığı süzer; büyük β
referansı gürültüyle oynatıp FC'yi kararsızlaştırır. γ_mpc = 200 tutuldu
(200→5000 taraması SoC_f'yi değiştirmedi — ofset probleminin ağırlıkla değil
integral etkiyle çözüldüğünün kanıtı, bkz. Bölüm 4.10).

---

## 8. Doğrulama ve sağlamlık kontrolleri

1. **Çevrim doğrulaması:** 46.53 km ≈ 2×23.27 km (GTR 15 resmi değeri);
   çekiş 8.56 kWh (≈ 184 Wh/km — WLTP'de D-segment BEV tüketimiyle tutarlı).
2. **Batarya enerji dengesi:** 10 kW × 10 dk deşarj → ΔSoC·E_nom = 1.672 kWh
   vs beslenen 1.667 kWh (%0.3, iç kayıplar). Tam gezi yalnız-batarya testi:
   ΔSoC = 0.851 ↔ tesiste ölçülen 8.56−2.12 kWh net akış — kapanıyor.
3. **DP iç tutarlılığı:** geri geçiş öngörüsü (2.733 €) vs tesiste kapalı
   çevrim (2.718 €): %0.5 — interpolasyonlu politika + model uyumsuzluğu payı.
4. **Optimallik sıralaması:** her üç senaryoda DP ≤ MPC ≤ A-ECMS (kıyas
   ölçütünün altında kalan gerçek zamanlı strateji yok — olsaydı hata olurdu).
5. **PSO:** 150 iterasyonun son 60'ında iyileşme < 0.1 mV (yakınsama, fig02);
   RMSE 6.4 mV ≈ eklenen gürültü tabanı 3 mV'nin ~2 katı (aşırı uyum yok).
6. **Sınır testleri:** SoC_max yakınında rejen kırpması (V₀ = inf hatasının
   giderimi, Bölüm 4.7); u = 0 tüm gezi → SoC 0.053 (pencere ihlali) →
   FC zorunluluğu.

---

## 9. Sınırlamalar ve gelecek çalışmalar

* **İzotermal yığın (T = 343 K):** sıcaklık dinamiği ve yaşlanmanın EMS
  etkileşimi [20] kapsam dışı (raporda da dışlanmıştı).
* **Bozulma maliyetleri** amaç fonksiyonunda yok (rapor kararı); BLFS rampa
  sınırı dolaylı koruma sağlar. FC/batarya yaşlanma maliyetli genişletme
  doğal bir devam konusudur.
* **Temsili polarizasyon verisi** (Bölüm 5.1): gerçek sayısallaştırılmış
  veriyle tek-CSV değişimi.
* **Sabit-yük MPC öngörüsü:** navigasyon/telematik önizlemeli MPC (gerçek
  hız tahmini) DP-MPC boşluğunu daha da kapatır.
* **Eğim α = 0:** WLTP tanımı gereği; gerçek rota profilleriyle genişletme
  `drive_cycle.py`'de tek satırlık değişikliktir (Denk. 3 eğim terimi kodda
  yorumdadır).

---

## 10. Kaynaklar

Numaralama MAT 4901E raporuyla ortaktır; başlıca kullanılanlar:

* [4] Xu et al. 2013 — PMP, plug-in FCEV (parasal eşdeğerlik yaklaşımı)
* [5] Gao et al. 2021 — A-ECMS PI uyarlaması
* [6] Mann et al. 2000 — GSSEM
* [7] Fang et al. 2026 — 0-B PEMFC modelleri + metasezgisel tanılama derlemesi
* [11] Nejad et al. 2016 — 1-RC+histerezis ECM, LFP parametreleri
* [12] Huria et al. 2014 — histerezis yasası
* [14] Onori et al. 2016 — HEV EMS kitabı (iki seviye, referans tasarımı)
* [15] Sundström & Guzzella 2009 — jenerik DP fonksiyonu
* [17] Mirai II enerji dengesi (2025) — yığın/yardımcı/verim çapaları
* [21] UN GTR 15 — WLTP; [22] Toyota Mirai teknik özellikleri
* [23] H2.LIVE, [24] BDEW — Almanya 2026 fiyatları

Tam liste ve bağlantılar için MAT 4901E raporuna bakınız
(`../bitirme1/report/MAT4901E_Report_final_v2.pdf`, Bölüm 4).

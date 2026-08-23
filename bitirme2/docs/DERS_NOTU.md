# DERS ÇALIŞMA NOTU — Plug-in FCHEV Enerji Yönetimi: Teorik Temeller

Bu not, MAT 4901E/4902E bitirme projesini (formülasyon + simülasyon) anlamak
için gereken TÜM teorik altyapıyı, projedeki kullanım yerleriyle bağlayarak
anlatır. Her bölümün sonunda "projede nerede?" kutusu ve notun sonunda
çalışma soruları vardır. Denklem numaraları MAT 4901E raporuna atıftır.

---

## 1. Büyük Resim: Problem Neden Var?

### 1.1 Yakıt pilli araç neden hibritlenir?

Bir PEM yakıt pili (PEMFC) tek başına araca yetmez; üç yapısal zayıflığı vardır:

1. **Yavaş dinamik yanıt:** Gaz besleme (kompresör) ve membran su dengesi
   saniyeler mertebesinde oturur; ani gaz pedalı talebini anlık karşılayamaz.
2. **Tek yönlülük:** Elektroliz yapamaz — rejeneratif frenleme enerjisini
   yutamaz. Frenleme enerjisi (bizim gezide 2.13 kWh ≈ çekişin %25'i!)
   bataryasız mimaride tamamen ısıya gider.
3. **Yük çevrimi yaşlanması:** Sık güç iniş-çıkışı membranı ve katalizörü
   yıpratır (gaz açlığı, potansiyel çevrimi).

Çözüm: yakıt pili + lityum-iyon batarya **hibridi**. Batarya hızlı, çift
yönlü ve çevrim toleranslıdır; yakıt pili menzili ve ortalama gücü taşır.

### 1.2 Plug-in ne değiştirir?

Klasik FCHEV'de (örn. seri üretim Mirai) batarya küçüktür (~1.2 kWh) ve tüm
enerji hidrojenden gelir; EMS'in amacı **şarj koruyucu** (charge-sustaining)
çalışmaktır: gezi sonunda SoC başlangıçtakine döner. Plug-in'de batarya
büyütülür (bizde 7.92 kWh) ve şebekeden şarj edilir; artık iki FARKLI
fiyatlı enerji kaynağı vardır (H₂: 11 €/kg ≈ 0.33 €/kWh_LHV; şebeke:
0.35 €/kWh ama batarya yolu verimli). EMS'in amacı **şarj tüketen**
(charge-depleting) çalışmaktır: ucuz şebeke enerjisini gezi boyunca planlı
biçimde tüketip hedef SoC'de bitirmek. Bu, problemi "verim optimizasyonundan"
"parasal optimizasyona" dönüştürür — kritik kavramsal sıçrama budur.

### 1.3 Kontrol problemi tek cümlede

> Her saniye, sürücünün istediği `P_load(t)` gücünün ne kadarının yakıt
> pilinden (`P_dc ≥ 0`), ne kadarının bataryadan (`P_bat = P_load − P_dc`)
> geleceğine karar ver; gezinin toplam parasını (H₂ + elektrik + hedef SoC
> cezası) en küçükle.

**Projede nerede?** `config.py` (parametreler), rapor Bölüm 1-3.2.

---

## 2. Araç Boylamsal Dinamiği

Newton'un ikinci yasasının tekerlek eksenine yazılmış hali. Araca etkiyen
dört boyuna kuvvet:

| Kuvvet | İfade | Fiziksel köken |
|---|---|---|
| Atalet | `m·a` | hızlanma direnci (d'Alembert) |
| Yuvarlanma | `m·g·C_r·cos α` | lastik histerezisi; hıza zayıf bağımlı, sabit alınır |
| Aerodinamik | `½·ρ·C_d·A_f·v²` | basınç + sürtünme direnci; hızın karesiyle büyür |
| Eğim | `m·g·sin α` | yerçekimi bileşeni (WLTP'de α = 0) |

Tekerlek gücü: `P_wheel = F_toplam · v` (Denk. 3). Güç, kuvvet × hız
olduğundan atalet terimi `m·a·v` olur — bu yüzden yüksek hızda hızlanmak
düşük hızdakinden çok daha pahalıdır.

**Aktarma organı verimi yön bağımlıdır (Denk. 4):** Çekişte motor+invertör+
dişli kayıpları talebi BÜYÜTÜR (`P_load = P_wheel/η_dt`), frenlemede geri
kazanılabilir gücü KÜÇÜLTÜR (`P_load = P_wheel·η_dt`). Aynı η ile bölme/çarpma
asimetrisi, tüm tersinir enerji dönüşümlerinin ortak kalıbıdır — bataryada da
(Bölüm 4) aynen karşımıza çıkar.

**Sayısal incelik:** İvme ileri farkla alınır (`a_k = (v_{k+1}−v_k)/Δt`)
çünkü k. adımın kararı, aracı k'dan k+1'e taşıyan güce karşılık gelir
(sıfırıncı derece tutucu tutarlılığı).

**Projede nerede?** `drive_cycle.py`; şekil fig01.

---

## 3. PEMFC Elektrokimyası

### 3.1 Temel prensip

PEMFC, `H₂ + ½O₂ → H₂O` tepkimesinin Gibbs serbest enerjisini doğrudan
elektriğe çevirir. Anotta H₂ protonlara ve elektronlara ayrılır; protonlar
polimer membrandan (Nafion), elektronlar dış devreden geçer; katotta O₂ ile
birleşip su oluşturur. Tek yan ürün sudur.

### 3.2 Termodinamik tavan: Nernst potansiyeli (Denk. 6)

İdeal (kayıpsız) hücre gerilimi, standart potansiyelin sıcaklık ve reaktan
kısmi basınçlarıyla düzeltilmiş halidir:

```
E_Nernst = 1.229 − 8.5·10⁻⁴(T − 298.15) + 4.308·10⁻⁵ · T · [ln p*H₂ + ½ ln p*O₂]
```

1.229 V, sıvı su ürünlü tepkimenin 25 °C standart potansiyeli (ΔG/2F).
Sıcaklık terimi negatiftir (ΔS < 0); basınç terimi Nernst denkleminin
`(RT/nF)·ln Q` biçiminin özelleşmesidir. Gerçek hücre bu değere yalnız açık
devrede yaklaşır.

### 3.3 Üç kayıp mekanizması → polarizasyon eğrisi (Denk. 5, 7-9)

Akım çekildikçe gerilim üç mekanizmayla düşer; her biri eğrinin farklı
bölgesini domine eder:

**a) Aktivasyon kaybı (düşük akım, dik düşüş).** Elektrot yüzeyindeki yük
transferinin kinetik bariyeri. Tam ifade Butler-Volmer denklemidir; yüksek
aşırı gerilimde Tafel yaklaşımına indirgenir: `V_act ∝ ln(i/i₀)`. GSSEM bunu
yarı-ampirik biçimde parametreler (Denk. 7):

```
V_act = −[ξ₁ + ξ₂T + ξ₃T·ln(C*O₂) + ξ₄T·ln(i)]
```

ξ katsayıları hücreye özgüdür (katalizör yükü, aktif alan yapısı) —
tanılamanın hedefi bunlardır. `C*O₂`, katalizör arayüzündeki çözünmüş O₂
derişimi; Henry yasasıyla kısmi basınçtan hesaplanır. Logaritmik biçim,
Tafel kinetiğinin doğrudan mirasıdır.

**b) Ohmik kayıp (orta akım, doğrusal bölge).** `V_ohm = i(R_M + R_C)`
(Denk. 8). Baskın bileşen membran protonik direncidir; Mann korelasyonu
membran özdirencini su içeriği λ'ya bağlar: kuru membran (λ≈7) kötü, tam
nemli (λ≈14) iyi, aşırı beslemeli (λ≈22-23) en iyi iletir. λ bizde etkin
(topaklanmış) parametredir; PSO 23.9'a itmiştir — yüksek basınçlı, iyi
nemlendirilmiş otomotiv yığını için tutarlı.

**c) Derişim (kütle taşınımı) kaybı (yüksek akım, ani çöküş).**
Reaktan, tüketildiği hızda katalizöre taşınamaz; sınır akım yoğunluğu
`J_max`'a yaklaşırken arayüz derişimi sıfıra gider:
`V_con = −β·ln(1 − J/J_max)` (Denk. 9). J → J_max limitinde gerilim
−∞'a ıraksar: fiziksel "duvar".

### 3.4 Faraday yasası ve verim — projenin kilit bağlantısı

Hidrojen tüketimi kimyasal stokiyometriden KESİN olarak çıkar: her H₂
molekülü 2 elektron verir →

```
ṁ_H₂ = N_cell · I · M_H₂ / (2F)        (F = 96485 C/mol)
```

Bunun güzel sonucu: LHV verimi yalnız hücre gerilimine bağlıdır:

```
η_LHV = P_el / (ṁ·LHV) = V_cell / 1.254 V
```

1.254 V = LHV'nin gerilim eşdeğeri (`M_H₂·LHV/2F`). (HHV bazında 1.482 V.)
Yani polarizasyon eğrisini bilmek = tüketim haritasını bilmek. Verim düşük
akımda yüksektir (V yüksek) → yakıt pilini kısmi yükte gezdirmek isteriz;
ama yardımcı yükler (kompresör, pompalar) sabit taban tükettiğinden SİSTEM
verimi çok düşük güçte de kötüleşir → içte bir tepe oluşur (Mirai: ~12 kW,
η≈0.70). BLFS'in "tepe verim noktası" bu tepedir.

**Projede nerede?** `fuel_cell.py`, `make_polarization_data.py`; fig02, fig03.

---

## 4. Lityum-İyon Batarya Modellemesi

### 4.1 Eşdeğer devre modelleri (ECM) ailesi

Elektrokimyasal (PDE tabanlı, örn. DFN) modeller doğru ama EMS için ağırdır;
veri güdümlü modeller genelleme riskir. Ara yol, davranışı devre elemanlarıyla
taklit eden ECM'lerdir:

* **Rint:** ideal kaynak `V_OC(SoC)` + seri direnç `R_s`. Anlık kayıpları
  yakalar, dinamiği yakalamaz. → bizim KONTROLCÜ modeli.
* **1-RC (Thevenin):** + paralel R₁C₁ çifti — difüzyon/polarizasyon
  geçişlerini (τ = R₁C₁ = 180 s) yakalar.
* **1-RC + histerezis:** + OCV'nin yön hafızası. → bizim TESİS modeli.
  Nejad ve ark. [11], LFP için en düşük SoC kestirim hatasını bu yapıya verdi.

### 4.2 SoC ve Coulomb sayımı (Denk. 13)

SoC, kalan yükün kapasiteye oranıdır. Akımın integrali ile izlenir:
`SoC(k+1) = SoC(k) − η_i·i·Δt/Q`. η_i = 0.995 kulombik verim; işaret
uzlaşımı: i > 0 deşarj. Basit ama açık çevrim: başlangıç hatası ve akım
sensörü sapması birikir — gerçek BMS'te OCV/EKF düzeltmesiyle birleştirilir
(Plett [13]); bizim simülasyonda gerçek SoC bilindiğinden gerekmez.

### 4.3 LFP'nin özel sorunu: düz OCV + histerezis (Denk. 14-15)

LiFePO₄'ün OCV-SoC eğrisi %20-80 arasında NEREDEYSE DÜZDÜR (iki faz birlikte
var olduğundan kimyasal potansiyel sabitlenir). Sonuç: gerilimden SoC okumak
imkânsıza yakındır ve 25-40 mV'lik şarj/deşarj histerezisi, düz bölgede tüm
bilgiyi domine eder. Huria yasası (Denk. 15) OCV'yi dinamik durum yapar:
aktif dalın (şarj/deşarj) referans eğrisine, işlenen yük |ΔSoC| ile üstel
gevşer (`m_hyst = 150` gevşeme hızı). Histerezisin zamanla değil YÜKLE
ilerlemesi deneysel gözlemdir — modelde `|d_soc|` çarpanının nedeni.

### 4.4 Güç → akım: ikinci derece denklem (Denk. 17)

EMS güç konuşur, devre akım konuşur. `P = V_term·I` ve `V_term = V_OC − I·R_s`
birleşince `R_s·I² − V_OC·I + P = 0`; fiziksel (küçük) kök:

```
I = [V_OC − √(V_OC² − 4·R_s·P)] / (2·R_s)
```

Diskriminant < 0 ⇔ talep, paketin verebileceği maksimum gücü
(`P_max = V_OC²/4R_s`, maksimum güç transferi teoremi) aşıyor — güç sınırı
denkleme gömülü gelir; ayrıca kısıt yazmak gerekmez.

### 4.5 Paket ölçekleme

96s10p: seri sayısı gerilimi ve direnci çarpar, paralel sayısı kapasiteyi
çarpar/direnci böler: `R_pack = R_cell·Ns/Np`. τ = R·C ölçeklemeden
bağımsız kalır (R×Ns/Np, C×Np/Ns). C-oranı (1C = kapasiteyi 1 saatte
boşaltan akım) kimyasal sınırdır: A123 hücresi sürekli 4C şarj / 20C deşarj.

**Projede nerede?** `battery.py`; fig04.

---

## 5. Optimal Kontrol Problemi Olarak EMS

### 5.1 Standart biçim

Ayrık zamanlı optimal kontrol problemi dört bileşenden oluşur:

* **Durum** `x_k`: sistemin hafızası — geçmişin geleceği etkileyen özeti.
  Bizde tek durum: `SoC` (H₂ tank seviyesi durum DEĞİL çünkü maliyeti
  koşu maliyetine zaten giriyor ve tank kısıtı bağlayıcı değil).
* **Karar** `u_k`: `P_dc` (tek karar — bara dengesi gerisini belirler).
* **Dinamik** `x_{k+1} = f(x_k, u_k)`: Denk. 2→17→18 zinciri.
* **Maliyet** `J = Σ L_k(x_k,u_k) + Φ(x_N)`: koşu maliyeti (H₂ € + elektrik €)
  + terminal ceza `γ(SoC_N − 0.25)²`.

Kısıtlar: `0 ≤ P_dc ≤ P_dc_max` (tek yönlü dönüştürücü!), SoC penceresi,
SoC-bağımlı batarya güç sınırları.

### 5.2 Neden yumuşak terminal ceza? (Denk. 23)

Sert kısıt `SoC_N = 0.25` problemi olurluk riskine sokar (gezi, hedefe tam
inecek kadar yük içermeyebilir). Kuadratik ceza her zaman olurlu kalır ve
γ ile sertlik ayarlanır. γ seçimi boyut analiziyle: birim SoC sapması, gezi
maliyetinin (5-15 €) çok üstünde cezalanmalı → γ = 1000 €. (γ taraması bunu
deneysel doğruladı: bkz. README Bölüm 6.3 — teori ve deneyin buluşması.)

### 5.3 Çözüm ailelerinin haritası

```
                      EMS yöntemleri
        ┌────────────────┼─────────────────┐
   Kural tabanlı    Optimizasyon tabanlı   Öğrenme tabanlı
   (BLFS, CDCS)     ┌───────┴────────┐     (kapsam dışı)
                Küresel/çevrimdışı  Anlık/çevrimiçi
                (DP)               (ECMS←PMP, MPC)
```

Temel takas: **bilgi ufku ↔ optimallik**. DP tüm geziyi bilir → küresel
optimum ama araçta koşamaz. ECMS yalnız şu anı bilir → PMP sayesinde yine de
optimuma yakın. MPC kısa ufku bilir → arada.

---

## 6. Dinamik Programlama (DP)

### 6.1 Bellman optimallik ilkesi

> Optimal bir yörüngenin herhangi bir ara noktasından itibaren kalan parçası,
> o noktadan başlayan alt problemin de optimal çözümüdür.

Bu ilke, N adımlı problemi N tane tek-adımlık probleme böler. **Maliyet-gitti
fonksiyonu** `V_k(x)` tanımlanır: k anında x durumundayken, optimal davranışla
gezi sonuna kadar ödenecek en küçük maliyet. Geri özyineleme (Denk. 27):

```
V_N(x) = Φ(x)                                        (terminalden başla)
V_k(x) = min_u { L_k(x,u) + V_{k+1}(f(x,u)) }        (geriye doğru)
```

`argmin`, politika tablosu `u*(k,x)`'i verir. İleri geçişte politika
oynatılır.

### 6.2 Sayısal gerçekleme incelikleri

* **Izgara + interpolasyon:** V sürekli x'te tanımlı; ızgarada saklanır.
  `f(x,u)` düğüme denk gelmez → `V_{k+1}` DOĞRUSAL İNTERPOLE edilir.
  En-yakın-düğüm kullanmak nicemleme gürültüsünü politikaya çevirir
  (Sundström & Guzzella [15] bunun standart çözümünü verir).
* **Olanaksızlık:** pencere dışına çıkaran (x,u) çiftine +∞. DİKKAT:
  ∞, interpolasyona girerse komşu düğümleri zehirler — projede SoC_max
  tarafı bu yüzden ∞ ile değil FİZİKSEL kırpmayla (BMS şarj konikleştirmesi)
  modellenmiştir (README Bölüm 4.7'deki hata hikâyesi).
* **Boyutluluk laneti:** maliyet ~ O(N · n_x^d · n_u). d = 1 durumda
  (151 düğüm × 105 karar × 3600 adım ≈ 57M değerlendirme) 2.5 s; durum
  sayısı d üstel patlatır — DP'nin skaler-durum formülasyonunu bu kadar
  değerli yapan budur (rapor, H₂ tankını durumdan çıkararak d=1'e indirdi).

### 6.3 DP'nin rolü: cetvel

DP gerçek zamanda koşamaz (geleceği ister) ama her gerçek zamanlı stratejinin
"optimumdan yüzde kaç uzak?" sorusunun cetvelidir. Bizim sonuç: A-ECMS %2.4,
MPC %1.0 — bu sayılar ancak DP varsa söylenebilir.

**Projede nerede?** `ems/dp.py`; fig05-07, gamma taraması fig09.

---

## 7. Pontryagin Minimum Prensibi (PMP) ve ECMS

### 7.1 PMP'nin özü

PMP, kısıtlı optimal kontrol için GEREKLİ koşullar verir. **Hamiltonyen**
tanımlanır (Denk. 28):

```
H(x, u, λ, t) = L(x, u) + λ · ẋ(x, u)
```

λ **eş-durum** (costate): durumun "gölge fiyatı" — SoC'nin marjinal değeri
(€/SoC birimi). PMP der ki: optimal `u*(t)`, HER ANDA Hamiltonyeni en küçükler:

```
u*(t) = argmin_u H(x*, u, λ*, t)
```

ve λ kendi diferansiyel denklemine uyar: `λ̇ = −∂H/∂x`. Kilit gözlem: bizim
problemde L'nin SoC'ye bağımlılığı zayıftır (OCV düz — LFP!) → `∂H/∂SoC ≈ 0`
→ **λ yaklaşık sabittir**. O zaman N boyutlu yörünge optimizasyonu, TEK
skaler λ'yı doğru seçme problemine çöker: λ öyle seçilir ki SoC yörüngesi
sınır koşullarını (0.90 → 0.25) sağlasın (two-point boundary value problem).

### 7.2 ECMS: PMP'nin mühendis hali

ECMS (Paganelli [3]) aynı fikri "eşdeğerlik faktörü" s ile yazar: batarya
enerjisini yakıt eşdeğerine çevirip toplam eşdeğer tüketimi anlık en küçükler.
Matematiksel olarak s, λ'nın ölçeklenmiş halidir; ECMS ≈ PMP'nin gerçek
zamanlı gerçeklemesi (Sciarretta & Guzzella [2]).

**s'nin anlamı sezgisel:** s büyük → batarya "pahalı" görünür → yakıt pili
çalışır → SoC korunur. s küçük → batarya "ucuz" → batarya boşalır. Doğru
sabit s ile ECMS, DP'ye çok yaklaşır — AMA doğru s geziye bağlıdır ve önceden
bilinemez.

### 7.3 Uyarlamalı ECMS (A-ECMS): s'yi geri beslemeyle bul

Çare: s'yi SoC izleme hatasıyla çevrimiçi ayarla (Denk. 29, Gao [5]):

```
s(t) = s₀ + k_p·e(t) + k_i·∫e,     e = SoC_ref − SoC
```

Bu bir PI kontrolördür; "plant"i SoC dinamiği, eyleyicisi s'dir. SoC referansın
altına düşerse e > 0 → s artar → FC devreye girer → SoC toparlar. Kararlılık/
performans takası klasik PI ayarıdır (k_p küçük: gevşek izleme; büyük:
çatırdama). **Anti-windup** şarttır: gezi sonunda FC zaten sınırındayken
integral birikirse, kısıt kalkınca patlama olur — integratör kelepçelenir.

**Plug-in inceliği:** Klasikte s, enerji eşdeğerliğinin TAMAMINI kurar. Bizim
maliyet zaten parasal (Denk. 21 bataryayı şebeke fiyatıyla değerliyor) →
ekonomi L'nin içinde → s₀ = 0 alınır, s yalnız izleme yapar. Xu [4]'ün
gösterdiği "sabit faktör fiziksel sınıra savurur" patolojisi de böyle önlenir.

### 7.4 SoC referansı tasarımı — göründüğünden derin

Şarj tüketen modda referans "0.90'dan 0.25'e azalan bir eğri"dir; ama NEYE
göre azalmalı? Zamana göre doğrusal (Denk. 29) sezgisel ama hatalı: duraklarda
ve son yavaşlamada YÜK YOKKEN batarya boşaltılamaz, referans düşmeye devam
eder → kontrolcü sonunda cezayı yer. Doğrusu, boşaltma FIRSATI ile orantılı
ilerlemek: birikimli pozitif çekiş enerjisi (veya mesafe). Bu, "reference
shaping"in EMS'teki karşılığıdır ve plug-in literatüründe standarttır
(Onori [14] Böl. 6). Projede bu fark 0.5-0.8 €'luk yapay ceza olarak
ölçüldü — teorik detayın parasal karşılığı.

**Projede nerede?** `ems/aecms.py`, `cost_model.set_reference()`.

---

## 8. Model Öngörülü Kontrol (MPC)

### 8.1 Kayan ufuk fikri

Her adımda: (1) mevcut durumdan başlayan N_p adımlık SONLU problemi çöz,
(2) yalnız İLK kararı uygula, (3) bir adım kay, tekrarla (Denk. 30).
Kapalı çevrimde geri besleme, model hatalarını her adımda düzeltir. Sonsuz
problemin kuyruğu, ufuk sonuna konan **terminal maliyetle** temsil edilir —
bizde `γ_mpc(SoC_ufuk_sonu − ref)²`.

### 8.2 Öngörü modeli sorunu

MPC'nin kalitesi = öngörüsünün kalitesi. Gelecek yükü bilmiyoruz →
**sabit yük varsayımı**: `P_load(j) = P_load(k)`. Bu SİSTEMATİK yanlıdır:
çekiş pikinde kontrolcü pikin 15 s süreceğini sanır → bataryayı korur →
FC'yi tam boşaltma fırsatında yakar. Rölantide tersini yapar. Net etki:
kalıcı SoC ofseti — ve kalıcı model yanlılığını hiçbir terminal ağırlığı
gideremez (γ_mpc 200→5000 taramasında SoC_f'nin kımıldamaması bunun deneysel
kanıtı). Teorik teşhis: **offset-free MPC** literatürünün konusu; standart
çare, bozucu/yanlılık kestirimi + referans düzeltmesi (integral etki).
Projede `β = 0.005` alçak geçiren integratörle çözüldü.

### 8.3 Konvekslik meselesi: neden QP değil?

QP (karesel program) çözücüler konveks maliyet ister. Bizim aşama maliyeti
iki yerden konvekslik bozar: (1) H₂ haritası polarizasyon eğriliğini taşır,
(2) Denk. 20'nin yön-bağımlı verimi P_bat = 0'da kırık (kink) yaratır.
Konveks olmayan problemde QP ancak vekil (surrogate) çözer — vekilin optimumu
modelin optimumu olmayabilir. Durum SKALER olduğu için kaba kuvvet meşrudur:
ufuk boyunca erişilebilir SoC bandı ±0.03 → 31 düğümlük yerel ızgarada kesin
DP, 0.6 ms/adımda. Ders: **çözücü seçimi problem yapısından çıkar** — durum
boyutu 1 olan yerde konveksleştirme cambazlığına gerek yok.

**Projede nerede?** `ems/mpc.py`.

---

## 9. Kural Tabanlı Katman: BLFS

Optimizasyon stratejileri ortalamada iyidir ama iki şeyi garanti etmez:
SoC'nin referans etrafında kalması ve FC'nin sarsılmaması. BLFS (rapor
Bölüm 3.6.5) bunu ±0.05'lik histerezis bandıyla kurallaştırır: bandın
üstünde FC kapalı (boşalt), altında FC tepe verim noktasında (en ucuz €/J
ile şarj et), içinde üst katman serbest. Histerezis bandının varlık nedeni
klasiktir: tek eşik olsaydı, eşik üstünde sürekli aç/kapa (chattering)
olurdu; bant, anahtarlamaya "ölü bölge" koyar.

Rampa sınırı `|dP_fc/dt| ≤ 5 kW/s` (Denk. 31) ayrı bir koruma: ani yük
artışında gaz beslemesi gecikir (kompresör ataleti) → katalizör gaz açlığı →
karbon korozyonu. Sınır, maliyet fonksiyonuna bozulma terimi eklemeden
dayanıklılık sağlar — "kısıtla koru, cezayla değil" yaklaşımı.

**Ölçülen etkisi:** maliyet +%0.2-0.4 karşılığında aç/kapa 154→54, ortalama
rampa yarıya. Koruma katmanları neredeyse bedavadır — pratik EMS tasarımının
önemli dersi.

**Projede nerede?** `ems/blfs.py`.

---

## 10. Parçacık Sürüsü Optimizasyonu (PSO)

### 10.1 Neden metasezgisel?

GSSEM tanılama problemi: 8 parametreli, konveks olmayan, türev bilgisi
anlamsız (parametreler arası korelasyon vadileri: ξ₁ saf kayma ↔ ξ₃·ln C*O₂;
λ ↔ R_C düşük akımda değiştirilebilir). Gradyan inişi vadilerde durur.
Model cebirsel → değerlendirme bedava → popülasyon tabanlı arama ideal.
PEMFC tanılamada fiili standart PSO/GA'dır (Fang [7] derlemesi).

### 10.2 Algoritma

Her parçacık bir aday çözümdür; konumu `x_i`, hızı `v_i`. Güncelleme:

```
v_i ← w·v_i + c₁·r₁·(p_i − x_i) + c₂·r₂·(g − x_i)
x_i ← x_i + v_i
```

Üç terim üç içgüdü: atalet (keşfe devam), bilişsel çekim (kendi en iyine dön),
sosyal çekim (sürünün en iyisine yönel). r₁, r₂ ∈ U(0,1) stokastiklik katar.

**Clerc daralma katsayıları** `w = 0.7298, c₁ = c₂ = 1.4962`: sürü
dinamiğinin (beklenen değerde) yakınsamasını garanti eden analitik ayar —
keyfî değil, kararlılık analizinin sonucu. Pratik korumalar: hız kelepçesi
(kutunun %20'si — patlamayı önler), sınırda yansıtma (parçacığı fiziksel
kutuda tutar, sınıra yapışmayı azaltır), fiziksellik cezası (V ≤ 0 → 10³).

### 10.3 Tanılama iyi mi? Nasıl anlarız?

* RMSE (6.4 mV), veri gürültü tabanının (3 mV) ~2 katı → aşırı uyum yok
  (RMSE < gürültü olsaydı ezber şüphesi doğardı).
* Yakınsama eğrisi son ~60 iterasyonda düz → durdurma yeterli.
* Tanılanan parametreler fiziksel aralıklarda (λ = 23.9: iyi nemlendirilmiş
  yığın; J_max = 2.98: yüksek güç yoğunluklu otomotiv hücresi) → çözüm
  yalnız eğri uydurmuyor, fiziksel olarak yorumlanabilir.

**Projede nerede?** `param_id.py`; fig02.

---

## 11. WLTP Çevrimi

WLTC Class 3b (güç/ağırlık > 34 W/kg araçlar — tüm modern binekler), dört
fazlı 1800 s'lik standart hız izidir: Low (şehir içi, dur-kalk yoğun),
Medium, High, Extra-High (otoyol, v_max = 131.3 km/h); 23.27 km. NEDC'nin
yapay sabit-hız platolarının aksine gerçek sürüş istatistiklerinden
türetilmiştir (UN GTR 15 [21]). Bizde 2 çevrim art arda: 46.5 km / 1 saat —
7.92 kWh'lik paketin anlamlı boşalması için gerekli mesafe.

EMS araştırması için önemi: yük profili ÇEŞİTLİLİĞİ (rölanti %13, piki
54 kW, rejenerasyon %25) stratejilerin tüm rejimlerini tetikler; DP'nin
"çevrim önceden bilinir" varsayımının da meşru zeminidir (tip onay çevrimi
tanım gereği bilinir).

---

## 12. Maliyet Fonksiyonunun Ekonomisi (Denk. 19-24)

### 12.1 İki enerji taşıyıcısını ortak paydaya getirmek

H₂ kg ile elektrik kWh toplanamaz; ortak payda PARA'dır (€). Hidrojen tarafı
doğrudan: `C_fc = M_H₂·ṁ·Δt`. Batarya tarafı incelikli: paketten çıkan her
joule aslında şebekeden (şarjda kayıplarla) alınmış joule'dür → deşarj,
şebeke fiyatının gidiş-dönüş verimine bölünmüşüyle fiyatlanır; rejeneratif
şarj ise ancak geri kazanılabilir kesriyle alacaklandırılır (Denk. 20-21).
Üstel `sgn(P_bat)` gösterimi bu böl/çarp asimetrisinin kompakt yazımıdır —
Bölüm 2'deki aktarma organı asimetrisiyle aynı kalıp.

### 12.2 Neden "her zaman batarya" değil?

Şebeke→teker verimi (~0.87) > H₂ tank→teker tepe verimi (~0.61) VE şebeke
kWh'si ucuz → batarya hep tercih edilir... bütçesi yetene kadar. Gezi net
talebi (~6.4 kWh) > batarya bütçesi (5.15 kWh) → FC farkı kapatMAK ZORUNDA.
Optimizasyonun gerçek sorusu şudur: **FC'nin vereceği ~1.5 kWh'yi NE ZAMAN
ve HANGİ GÜÇTE vermeli?** Cevap: verim haritasının tepesine yakın, ramp
kısıtlarına saygılı, SoC penceresini ihlal etmeyen anlarda — üç stratejinin
tüm farkı bu zamanlama/güç seçimindedir (fig06'yı bu gözle inceleyin).

### 12.3 Duyarlılık mantığı

Fiyat oranı değişince ne olur? Elektrik hâlâ ucuzsa politika YAPISI değişmez,
yalnız maliyet ölçeklenir (bizim üç senaryo da böyle). Yapısal kırılma,
H₂'nin kWh başına elektrikle eşitlendiği yerdedir (M_H₂/33.3 ≈ M_ele/0.87
⇒ M_H₂ ≈ 10 €/kg iken M_ele ≈ 0.26 €/kWh): o noktadan sonra FC yükü taşır,
batarya yalnız pik törpüler (şarj koruyucu davranışa dönüş). Duyarlılık
analizi bu kırılmanın hangi tarafında olduğumuzu söyler.

---

## 13. İki Katmanlı Simülasyon Felsefesi

Kontrolcüye tesisin TAM modelini vermek metodolojik hatadır: gerçek araçta
kontrolcü hiçbir zaman tam modele sahip değildir; ayrıca "kendi modelinde
optimal" ile "gerçekte optimal" farkı kaybolur. Doğru düzen (Onori [14]):

```
KONTROLCÜ katmanı: Rint + verim LUT     →  karar üretir (u)
TESİS katmanı:     1-RC + histerezis + GSSEM  →  gerçeği oynatır, METRİKLERİ üretir
```

DP'nin geri geçiş öngörüsü (2.733 €) ile tesiste gerçekleşen (2.718 €)
arasındaki %0.5 fark, model uyumsuzluğunun ölçülmüş bedelidir. Raporlanan
her sayının tesis katmanından gelmesi, sonuçların iyimser yanlılık
taşımamasının güvencesidir.

---

## 14. Kavram Sözlüğü

| Terim | Karşılık / tanım |
|---|---|
| EMS | Enerji yönetim stratejisi — güç paylaşım kararı kuralı |
| Charge-depleting / sustaining | Şarj tüketen (plug-in) / şarj koruyucu mod |
| SoC | State of Charge — şarj durumu (0-1) |
| OCV | Open Circuit Voltage — açık devre gerilimi |
| ECM | Equivalent Circuit Model — eşdeğer devre batarya modeli |
| GSSEM | Genelleştirilmiş kararlı hal elektrokimyasal modeli (Mann) |
| Polarizasyon eğrisi | V_cell(J) — hücre geriliminin akım yoğunluğuna karşı grafiği |
| LHV / HHV | Alt / üst ısıl değer (su buharı / sıvı ürün bazı) |
| Costate (λ) | Eş-durum: durumun gölge fiyatı (€/SoC) |
| Eşdeğerlik faktörü (s) | ECMS'te λ'nın rolünü üstlenen çarpan |
| Hamiltonyen | Anlık maliyet + λ·(durum türevi): PMP'nin en küçüklenen niceliği |
| Cost-to-go (V_k) | Maliyet-gitti: k'dan sona optimal kalan maliyet |
| Kayan ufuk | MPC'nin her adımda yeniden çözüp ilk kararı uygulaması |
| Offset-free MPC | Kalıcı model yanlılığını integral etkiyle silen MPC ailesi |
| Chattering | Eşik etrafında hızlı aç/kapa salınımı; histerezis bandıyla önlenir |
| Curse of dimensionality | DP maliyetinin durum boyutuyla üstel patlaması |
| C-oranı | Kapasiteye normalize akım (1C = 1 saatte boşaltma) |
| Curtailment | Şarj kısma: kabul edilemeyen rejen gücünün frene atılması |
| ZOH | Sıfırıncı derece tutucu — kararın örnekleme aralığında sabit tutulması |

---

## 15. Çalışma Soruları

Savunma/sınav provası için — hepsinin cevabı bu notta ve README'dedir.

1. Yakıt pili neden tek başına araca yetmez? Üç yapısal neden sayınız.
2. `P_bat > 0` işaret uzlaşımı nedir ve Denk. 17'deki karekökün önündeki
   eksi işareti neden fiziksel kökü seçer?
3. Polarizasyon eğrisinin üç bölgesini, her birinin baskın kayıp mekanizmasını
   ve GSSEM'deki karşılık terimini eşleştiriniz.
4. `η_LHV = V_cell/1.254` özdeşliğini Faraday yasasından türetiniz. Bu özdeşlik
   projede hangi tasarım kararını mümkün kılar? (İpucu: LUT zinciri.)
5. LFP kimyasında histerezis durumu neden "vazgeçilmez"dir? NMC'de de öyle
   olur muydu?
6. DP'de değer fonksiyonu interpolasyonu yapılmasaydı ne olurdu? SoC_max
   sınırında +∞ kullanmak neden tehlikelidir; projede yerine ne yapıldı?
7. PMP'de λ'nın yaklaşık sabit çıkmasının fiziksel nedeni nedir? (İpucu:
   LFP OCV eğrisi.) Bu, ECMS'i nasıl mümkün kılar?
8. A-ECMS'te s₀ = 0 seçiminin gerekçesi nedir? Klasik (plug-in olmayan)
   ECMS'te de s₀ = 0 alınabilir miydi?
9. Zaman-doğrusal SoC referansı hangi durumlarda izlenemez hale gelir?
   Enerji tabanlı referans bunu nasıl çözer ve hangi ek bilgiye ihtiyaç duyar?
10. MPC'deki kalıcı SoC ofsetinin kökü nedir ve neden γ_mpc'yi büyütmek
    çözmez? Çözen mekanizmanın adı ve çalışma ilkesi nedir?
11. Aşama maliyetinin P_dc'de konveks olmamasının İKİ kaynağını gösterin.
    Bu, MPC alt probleminin çözücü seçimini nasıl belirledi?
12. BLFS'teki histerezis bandı tek eşikle değiştirilse ne gözlenirdi?
    Rampa sınırı hangi bozulma mekanizmalarına karşı koruma sağlar?
13. PSO'da daralma katsayılarının rolü nedir? RMSE'nin gürültü tabanının
    altına inmesi neden İYİ değil, ŞÜPHELİ olurdu?
14. Üç fiyat senaryosunda politika yapısının değişmemesinin nedeni nedir?
    Hangi fiyat oranında yapısal kırılma beklersiniz, hesaplayınız.
15. "Raporlanan her sayı tesis katmanından gelir" ilkesi hangi metodolojik
    yanlılığı önler? DP öngörüsü ile tesiste gerçekleşen maliyet arasındaki
    fark neyi ölçer?

---

*Bu not `bitirme2/docs/` altındadır; denklem numaraları MAT 4901E raporuna,
bölüm/şekil atıfları `bitirme2/README.md`'ye işaret eder. Kaynaklar için:
`docs/KAYNAKCA.md`.*

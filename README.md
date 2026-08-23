# Plug-in Hidrojen Yakıt Pilli Hibrit Araçlarda (FCHEV) Enerji Yönetimi

**Matematiksel modelleme, optimal kontrol formülasyonu ve sayısal çözüm**

İstanbul Teknik Üniversitesi — Matematik Mühendisliği
Bitirme Projesi I (MAT 4901E) ve Bitirme Projesi II (MAT 4902E), 2026

**Öğrenci:** Ahmet Yeşil (090220359) · **Danışman:** Prof. Dr. Semra Ahmetolan

---

## Proje özeti

Plug-in hidrojen yakıt pilli hibrit elektrikli bir araçta (Toyota Mirai II tabanlı
FCHEV) yakıt pili ile batarya arasındaki güç paylaşımı, bir **optimal kontrol
problemi** olarak kurulur ve sayısal olarak çözülür. Tek karar değişkeni DC/DC
dönüştürücünün baraya verdiği güç `u(t) = P_dc(t)`, tek durum değişkeni bataryanın
şarj durumu `SoC`'dur. Amaç, WLTP referans gezisi boyunca toplam parasal maliyeti
(hidrojen + şebeke elektriği + terminal SoC cezası) en aza indirmektir:

```
min  Σ L_k(SoC_k, P_dc,k) + γ (SoC_N − 0.25)²      L_k = C_yakıt pili,k + C_batarya,k
```

Depo iki aşamadan oluşur:

| Aşama | İçerik |
|---|---|
| **[`bitirme1/`](bitirme1/)** — MAT 4901E | Literatür taraması, araç/yakıt pili/batarya modellerinin matematiksel türetimi, optimal kontrol probleminin formülasyonu, çözüm stratejilerinin seçimi. Rapor + savunma sunumu. |
| **[`bitirme2/`](bitirme2/)** — MAT 4902E | Formülasyonun Python'da sayısal çözümü: iki katmanlı simülasyon ortamı, yığın katsayılarının PSO ile tanılanması ve dört enerji yönetim stratejisinin (DP, A-ECMS, MPC, BLFS) karşılaştırılması. Kod + rapor. |

---

## Ana sonuçlar

Varsayılan fiyat senaryosunda (11 €/kg H₂, 0.35 €/kWh), 2×WLTC Class 3b referans gezisi:

| Strateji | Toplam maliyet [€] | DP'ye fark | H₂ [g] | Elektrik [kWh] | FC aç/kapa | CPU [ms/adım] |
|---|---|---|---|---|---|---|
| **DP** (küresel kıyas ölçütü) | **2.718** | — | 77.6 | 5.15 | 85 | 0.016 |
| MPC | 2.746 | +%1.0 | 79.5 | 5.11 | 64 | 0.59 |
| MPC + BLFS | 2.752 | +%1.2 | 80.0 | 5.11 | 50 | 0.60 |
| A-ECMS | 2.783 | +%2.4 | 80.3 | 5.09 | 154 | 0.21 |
| A-ECMS + BLFS | 2.795 | +%2.8 | 80.8 | 5.08 | 54 | 0.25 |

* Gerçek zamanlı stratejiler küresel optimumun **%1-3** bandında kalır — literatürdeki
  tipik ECMS/MPC boşluğuyla uyumlu.
* BLFS koruma katmanı maliyeti ~%0.2-0.4 artırırken yakıt pili aç/kapa sayısını
  **154 → 54**'e düşürür: membran ömrü için küçük parasal prim.
* Tüm çevrim içi stratejiler ≤ 0.6 ms/adım — 1 s'lik gerçek zaman bütçesinin çok altında.

Ayrıntılı analiz, fiyat senaryosu duyarlılığı ve γ taraması için
[`bitirme2/README.md`](bitirme2/README.md) (tam kod dokümantasyonu) ve
`bitirme2/MAT4902_GraduationProject2_Report.pdf` dosyalarına bakınız.

---

## Hızlı başlangıç

```bash
git clone https://github.com/<kullanıcı-adı>/fchev-energy-management.git
cd fchev-energy-management/bitirme2
pip install -r requirements.txt      # numpy + matplotlib
cd src
python3 run_all.py                   # tüm sonuçları ve şekilleri yeniden üretir (~2 dk)
```

Rastgele süreçler sabit tohumludur (`seed=42`, `seed=7`); kod iki kez
çalıştırıldığında bit düzeyinde aynı sonuçları verir.

---

## Klasör yapısı

```
.
├── bitirme1/                        MAT 4901E — formülasyon
│   ├── report/                      rapor (final + taslak, .pdf ve .docx)
│   ├── presentation/                savunma sunumu (Beamer .tex + .pptx)
│   ├── figures/                     WLTP profili, OCV-SoC düz bölge şekilleri
│   └── kaynaklar/                   literatür listesi (PDF'ler telif nedeniyle hariç)
│
└── bitirme2/                        MAT 4902E — sayısal çözüm
    ├── src/                         simülasyon ve EMS kodu
    │   └── ems/                     dp.py · aecms.py · mpc.py · blfs.py
    ├── data/                        WLTC hız izi, polarizasyon verisi, PSO çıktısı
    ├── results/                     csv/json sonuçlar + figures/fig01…fig09.png
    ├── docs/                        ders notu, kaynakça, rapor üreteci
    └── README.md                    modül modül tam kod dokümantasyonu
```

---

## Yöntemler

* **Yakıt pili:** Mann–Amphlett genelleştirilmiş kararlı-hal elektrokimyasal modeli (GSSEM);
  katsayılar Parçacık Sürü Optimizasyonu (PSO) ile polarizasyon verisine tanılanmıştır.
* **Batarya:** 1-RC eşdeğer devre + OCV histerezisi (LFP), ayrıca Rint modeli.
* **Sürüş çevrimi:** UN GTR No. 15 WLTC Class 3b (1 Hz, resmi hız izi).
* **Enerji yönetimi:** Dinamik Programlama (çevrimdışı küresel kıyas), Uyarlamalı ECMS,
  Model Öngörülü Kontrol, Sınır Katmanı Yüzey İzleme (koruma katmanı).

## Lisans

Kod [MIT Lisansı](LICENSE) ile sunulmaktadır. `bitirme1/report`, `bitirme2/docs` ve
rapor PDF'lerindeki metin, şekil ve analizler yazarın akademik çalışmasıdır;
atıf vererek kullanılabilir. `bitirme1/kaynaklar/` altındaki üçüncü taraf yayınlar
telifli oldukları için depoya dahil edilmemiştir.

## Atıf

```bibtex
@mastersthesis{yesil2026fchev,
  author = {Ye{\c{s}}il, Ahmet},
  title  = {Plug-in Hidrojen Yak{\i}t Pilli Hibrit Ara{\c{c}}larda Enerji Y{\"o}netimi:
            Matematiksel Modelleme ve Optimal Kontrol},
  school = {{\.I}stanbul Teknik {\"U}niversitesi, Matematik M{\"u}hendisli{\u{g}}i},
  year   = {2026},
  note   = {Bitirme Projesi I--II (MAT 4901E / MAT 4902E)}
}
```

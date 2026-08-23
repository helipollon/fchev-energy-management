# KAYNAKÇA — Bitirme Projesi II (MAT 4902E)

İki bölümden oluşur:

* **Bölüm A:** MAT 4901E raporunun kaynak listesi [1]–[24] — numaralama
  raporla ortaktır, rapor ve kodda bu numaralarla atıf yapılır. PDF'leri
  `../kaynaklar/` klasöründedir.
* **Bölüm B:** Bitirme II uygulamasında kullanılan EK kaynaklar [25]–[38] —
  PSO teorisi, ofsetsiz MPC, referans tasarımı ve temel ders kitapları.
  Bunlar rapora eklenmelidir.

Sonda konu → kaynak okuma rehberi vardır.

---

## Bölüm A — MAT 4901E ortak kaynakları [1]–[24]

**EMS derlemeleri ve temel strateji makaleleri**

[1] Khalatbarisoltani, A., Kandidayeni, M., Boulon, L., & Hu, X. (2024).
Energy management strategies for fuel cell vehicles: A comprehensive review.
*IEEE Transactions on Intelligent Transportation Systems, 25*(1), 14–32.
https://ieeexplore.ieee.org/abstract/document/10247150
→ `kaynaklar/01…pdf` · EMS sınıflandırması, T1–T5 topolojileri (Şekil 2).

[2] Sciarretta, A., & Guzzella, L. (2007). Control of hybrid electric
vehicles. *IEEE Control Systems Magazine, 27*(2), 60–70.
https://ieeexplore.ieee.org/abstract/document/4140747
→ ECMS ↔ PMP bağlantısının klasik anlatımı.

[3] Paganelli, G., Delprat, S., Guerra, T. M., Rimaux, J., & Santin, J. J.
(2002). Equivalent consumption minimization strategy for parallel hybrid
powertrains. *IEEE Vehicular Technology Conference*, 2076–2081.
→ ECMS'in doğduğu makale.

[4] Xu, L., Ouyang, M., Li, J., Yang, F., Lu, L., & Hua, J. (2013).
Application of Pontryagin's Minimal Principle to the energy management
strategy of plugin fuel cell electric vehicles. *International Journal of
Hydrogen Energy, 38*(24), 10104–10115.
https://www.sciencedirect.com/science/article/abs/pii/S0360319913013578
→ Plug-in parasal değerleme + sabit-faktör patolojisi; projenin ana şablonu.

[5] Gao, J., Li, Y., Liu, Y., & Li, X. (2021). Adaptive real-time optimal
energy management strategy based on equivalent factors optimization for
hybrid fuel cell system. *International Journal of Hydrogen Energy, 46*,
4329–4338.
https://www.sciencedirect.com/science/article/abs/pii/S0360319920340830
→ A-ECMS PI uyarlama yasası (Denk. 29'un kaynağı).

**PEMFC modelleme**

[6] Mann, R. F., Amphlett, J. C., Hooper, M. A. I., Jensen, H. M.,
Peppley, B. A., & Roberge, P. R. (2000). Development and application of a
generalised steady-state electrochemical model for a PEM fuel cell.
*Journal of Power Sources, 86*(1–2), 173–180.
https://www.sciencedirect.com/science/article/abs/pii/S037877539900484X
→ GSSEM: Denk. 5–10'un kaynağı; membran özdirenç korelasyonu.

[7] Fang, Y., Yang, F., Xing, Y., Zhang, X., Wang, W., & Lin, S. (2026).
A comparative review of modeling and metaheuristic parameter identification
strategies for zero-dimensional PEMFC polarization models. *Energies, 19*,
1438. https://www.mdpi.com/1996-1073/19/6/1438
→ Tanılama metodolojisi ve parametre sınırları (`param_id.py` BOUNDS).

[8] Springer, T. E., Zawodzinski, T. A., & Gottesfeld, S. (1991). Polymer
electrolyte fuel cell model. *Journal of the Electrochemical Society, 138*,
2334–2342. https://iopscience.iop.org/article/10.1149/1.2085971/meta
→ Membran su içeriği λ kavramının kaynağı.

[9] Kim, J., Lee, S., Srinivasan, S., & Chamberlin, C. E. (1995). Modeling
of proton-exchange membrane fuel-cell performance with an empirical
equation. *Journal of the Electrochemical Society, 142*, 2670–2674.
https://iopscience.iop.org/article/10.1149/1.2050072/meta
→ Ampirik polarizasyon denklemi (derişim kaybının üstel biçimi).

[10] Ziogou, C., Voutetakis, S., Papadopoulou, S., & Georgiadis, M. C.
(2011). Modeling, simulation and experimental validation of a PEM fuel
cell system. *Computers & Chemical Engineering, 35*, 1886–1900.
→ Dinamik 0-B model — statik seçimin karşılaştırma tabanı.

**Batarya modelleme**

[11] Nejad, S., Gladwin, D. T., & Stone, D. A. (2016). A systematic review
of lumped-parameter equivalent circuit models for real-time estimation of
lithium-ion battery states. *Journal of Power Sources, 316*, 183–196.
https://www.sciencedirect.com/science/article/abs/pii/S0378775316302427
→ 1-RC+histerezis seçiminin gerekçesi; hücre parametreleri (Rs, R1, C1);
8. derece OCV polinomları.

[12] Huria, T., Ludovici, G., & Lutzemberger, G. (2014). State of charge
estimation of high power lithium iron phosphate cells. *Journal of Power
Sources, 249*, 92–102.
→ Histerezis diferansiyel yasası (Denk. 15).

[13] Plett, G. L. (2004). Extended Kalman filtering for battery management
systems of LiPB-based HEV battery packs — Part 3: State and parameter
estimation. *Journal of Power Sources, 134*, 277–292.
→ Durum/parametre kestirim çerçevesi.

**Optimal kontrol ve DP**

[14] Onori, S., Serrao, L., & Rizzoni, G. (2016). *Hybrid electric
vehicles: Energy management strategies.* Springer.
https://link.springer.com/book/10.1007/978-1-4471-6781-5
→ İki seviyeli model yaklaşımı, referans tasarımı; alan için EN İYİ tek kitap.

[15] Sundström, O., & Guzzella, L. (2009). A generic dynamic programming
Matlab function. *IEEE Control Applications & Intelligent Control*,
1625–1630. https://ieeexplore.ieee.org/abstract/document/5281131
→ DP ızgara + interpolasyon uygulama yapısı (`ems/dp.py`).

[16] Bertsekas, D. P. (2005). *Dynamic programming and optimal control*
(3rd ed.). Athena Scientific.
→ Bellman özyinelemesinin teorik temeli.

**Referans araç, çevrim, fiyatlar**

[17] (2025). Energy balance and hydrogen exhaust emissions of the
second-generation Toyota Mirai. *International Journal of Hydrogen Energy.*
https://www.sciencedirect.com/science/article/pii/S0360319925034093
→ Yığın/verim çapaları, yardımcı tüketim oranı, polarizasyon hedef noktaları.

[18] Hu, X., Murgovski, N., Johannesson, L. M., & Egardt, B. (2013). Energy
efficiency analysis of a series plug-in hybrid electric bus with different
energy management strategies and battery sizes. *Applied Energy, 111*,
1001–1009.

[19] Tribioli, L., Cozzolino, R., Chiappini, D., & Iora, P. (2016). Energy
management of a plug-in fuel cell/battery hybrid vehicle with on-board fuel
processing. *Applied Energy, 184*, 140–154.

[20] Kandidayeni, M., Macias, A., Boulon, L., & Kelouwani, S. (2020).
Investigating the impact of ageing and thermal management of a fuel cell
system on energy management strategies. *Applied Energy, 274*, 115293.
→ İzotermal varsayımın kapsam-dışı bıraktığı etkiler.

[21] United Nations Economic Commission for Europe. (2022). *UN Global
Technical Regulation No. 15: Worldwide harmonized Light vehicles Test
Procedure (WLTP)* (ECE/TRANS/WP.29/2022/42/Rev.1).
https://unece.org/sites/default/files/2022-04/ECE_TRANS_WP.29_2022_42_Rev.1E.pdf
→ WLTC Class 3b izinin resmî tanımı (`data/wltp_class3b_kmh.csv`).

[22] Toyota Motor Corporation. (2022). *Toyota Mirai technical
specifications.* Toyota (GB) Media Site.
https://media.toyota.co.uk/wp-content/uploads/sites/5/pdf/220203M-Mirai-Tech-Spec.pdf

[23] H2 MOBILITY Deutschland GmbH. (2026). *H2.LIVE: Hydrogen stations in
Germany and Europe — fuel pricing.* https://h2.live/en/

[24] BDEW Bundesverband der Energie- und Wasserwirtschaft. (2026).
*BDEW-Strompreisanalyse Januar 2026.*
https://www.bdew.de/media/documents/BDEW_Strompreisanalyse_012026_1.pdf

---

## Bölüm B — Bitirme II'de eklenen kaynaklar [25]–[38]

*Not: [25]–[38] arası künyeler klasik ve yaygın bilinen yayınlardır; DOI/URL
verilmeyenler Google Scholar'da başlıkla tek sonuçta bulunur. Rapora
eklenmeden önce künyelerin son kontrolü önerilir.*

**PSO teorisi (`param_id.py` gerekçesi)**

[25] Kennedy, J., & Eberhart, R. (1995). Particle swarm optimization.
*Proceedings of ICNN'95 — International Conference on Neural Networks*,
Vol. 4, 1942–1948. IEEE.
→ PSO'nun doğduğu makale; hız/konum güncelleme yapısı.

[26] Clerc, M., & Kennedy, J. (2002). The particle swarm — explosion,
stability, and convergence in a multidimensional complex space. *IEEE
Transactions on Evolutionary Computation, 6*(1), 58–73.
→ Daralma katsayıları w = 0.7298, c₁ = c₂ = 1.4962'nin analitik türetimi
(kodda kullanılan değerler).

[27] Shi, Y., & Eberhart, R. (1998). A modified particle swarm optimizer.
*IEEE International Conference on Evolutionary Computation*, 69–73.
→ Atalet ağırlığı kavramı; hız kelepçeleme pratiği.

**ECMS / PMP derinleştirme (`ems/aecms.py`)**

[28] Musardo, C., Rizzoni, G., Guezennec, Y., & Staccia, B. (2005).
A-ECMS: An adaptive algorithm for hybrid electric vehicle energy
management. *European Journal of Control, 11*(4–5), 509–524.
→ "Uyarlamalı ECMS" kavramının isim babası; s'nin çevrimiçi güncellenmesi.

[29] Serrao, L., Onori, S., & Rizzoni, G. (2011). A comparative analysis of
energy management strategies for hybrid electric vehicles. *Journal of
Dynamic Systems, Measurement, and Control, 133*(3), 031012.
→ DP–PMP–ECMS eşdeğerliğinin sistematik karşılaştırması; sonuç tablomuzun
(DP < MPC < A-ECMS, %1–3 bandı) literatür bağlamı.

[30] Kim, N., Cha, S., & Peng, H. (2011). Optimal control of hybrid
electric vehicles based on Pontryagin's minimum principle. *IEEE
Transactions on Control Systems Technology, 19*(5), 1279–1287.
→ λ'nın yaklaşık sabitliği argümanının titiz hali (ders notu Bölüm 7.1).

**MPC teorisi (`ems/mpc.py` gerekçesi)**

[31] Rawlings, J. B., Mayne, D. Q., & Diehl, M. (2017). *Model predictive
control: Theory, computation, and design* (2nd ed.). Nob Hill Publishing.
→ Kayan ufuk, terminal maliyet, kararlılık; ücretsiz PDF yayıncı sitesinde.

[32] Pannocchia, G., & Rawlings, J. B. (2003). Disturbance models for
offset-free model-predictive control. *AIChE Journal, 49*(2), 426–437.
→ Ofsetsiz MPC: kalıcı model yanlılığının integral/bozucu kestirimi ile
silinmesi — `beta_int` düzeltmesinin teorik dayanağı.

[33] Borhan, H., Vahidi, A., Phillips, A. M., Kuang, M. L., Kolmanovsky,
I. V., & Di Cairano, S. (2012). MPC-based energy management of a
power-split hybrid electric vehicle. *IEEE Transactions on Control Systems
Technology, 20*(3), 593–603.
→ HEV'de MPC'nin temsilci uygulaması; öngörü modeli seçiminin etkisi.

**Ders kitapları (ders notunun genel arka planı)**

[34] Guzzella, L., & Sciarretta, A. (2013). *Vehicle propulsion systems:
Introduction to modeling and optimization* (3rd ed.). Springer.
→ Boylamsal dinamik (Denk. 3–4), yarı-statik modelleme felsefesi, EMS'e
giriş — ders notu Bölüm 2 ve 5'in kaynağı.

[35] Larminie, J., & Dicks, A. (2003). *Fuel cell systems explained*
(2nd ed.). Wiley.
→ PEMFC kayıp mekanizmaları, Nernst/Tafel türetimleri (ders notu Bölüm 3)
için en okunabilir giriş.

[36] Barbir, F. (2013). *PEM fuel cells: Theory and practice* (2nd ed.).
Academic Press.
→ Polarizasyon eğrisi, su yönetimi, yardımcı sistemler (kompresör tabanı
argümanı).

[37] Plett, G. L. (2015). *Battery management systems, Volume I: Battery
modeling.* Artech House.
→ ECM aileleri, OCV-histerezis modelleri, Coulomb sayımı (ders notu Bölüm 4).

[38] Kirk, D. E. (2004). *Optimal control theory: An introduction.* Dover.
→ PMP ve varyasyonel temellerin özlü klasiği (ders notu Bölüm 7).

---

## Konu → kaynak okuma rehberi

| Çalışılacak konu | Önce | Sonra derinleşme |
|---|---|---|
| FCHEV genel resim + topolojiler | [1] | [14] Böl. 1–2 |
| Araç dinamiği, çevrim, yarı-statik model | [34] Böl. 2 | [21] |
| PEMFC elektrokimyası | [35] Böl. 3 | [6], [8], [9], [36] |
| PEMFC parametre tanılama | [7] | [25], [26], [27] |
| Batarya ECM + LFP histerezisi | [37] Böl. 2–3 | [11], [12], [13] |
| Optimal kontrol temelleri | [38] | [16] |
| DP uygulaması | [15] | [16], [14] Böl. 4 |
| PMP → ECMS → A-ECMS | [2] | [3], [30], [28], [5], [29] |
| Plug-in parasal formülasyon | [4] | [18], [19] |
| MPC | [31] Böl. 1–2 | [32], [33] |
| Referans (SoC) tasarımı | [14] Böl. 6 | [4] |
| Sonuçların literatürle kıyası | [29] | [1] |

### Atıf kullanım notları

* Kod içi atıflar ([6], [11], [15]…) rapor numaralarıdır; Bölüm B kaynakları
  MAT 4902E raporu yazılırken kaynakçaya [25]'ten itibaren eklenmelidir.
* README'nin "rapordan sapmalar" bölümündeki üç ana karar için önerilen
  atıflar: enerji-tabanlı referans → [14]; ofsetsiz MPC düzeltmesi → [32];
  grid-DP alt çözücü → [15] + konvekslik tartışması [31].
* PSO ayarları (daralma katsayıları) için [26]; sınır aralıkları için [7].

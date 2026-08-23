# MAT 4901E — Bitirme Projesi I: Matematiksel Modelleme ve Formülasyon

**Mathematical Modeling & Control Strategies for Hybrid Hydrogen Systems**
Teslim: 14 Haziran 2026 · Ahmet Yeşil (090220359) · Danışman: Prof. Dr. Semra Ahmetolan

Bu aşamada plug-in FCHEV enerji yönetimi problemi **matematiksel olarak kurulmuştur**:
araç boyuna dinamiği, PEMFC yığınının Mann–Amphlett GSSEM modeli, batarya eşdeğer
devre modelleri (1-RC + histerezis), güç akışı ve maliyet fonksiyonu türetilmiş;
problem sonlu ufuklu bir optimal kontrol problemi olarak ifade edilmiş ve çözüm
stratejileri (DP, A-ECMS, MPC, BLFS) gerekçelendirilmiştir. Sayısal çözüm
[`../bitirme2/`](../bitirme2/) klasöründedir.

## İçerik

| Dosya | İçerik |
|---|---|
| **`report/MAT4901E_Report.pdf`** | **Teslim edilen nihai rapor** (22 sayfa) |
| `report/taslaklar/` | Önceki sürümler (`_v1`, `_v2`; .pdf ve düzenlenebilir .docx kaynakları) |
| `presentation/presentation.tex` | Savunma sunumu — Beamer kaynağı (TikZ/pgfplots, harici şekil gerektirmez) |
| `presentation/FCHEV_Presentation.pptx` | Sunumun PowerPoint sürümü |
| `figures/` | WLTP hız profili ve OCV–SoC düz bölge şekilleri |
| `kaynaklar/` | Kullanılan 22 kaynağın listesi (PDF'ler telif nedeniyle depoda değildir) |

## Raporun yapısı

1. Tasarımın tanımı ve amacı · 2. Kapsam ve kullanım alanları
3. Yürütülen çalışmalar — literatür taraması (EMS, PEMFC ve Li-ion modelleme),
   sistem mimarisi ve referans araç/sürüş çevrimi, güç aktarma organı bileşenlerinin
   matematiksel modellenmesi, güç akışı modeli, maliyet fonksiyonunun türetimi,
   EMS yöntemleri (DP, A-ECMS, MPC, BLFS) ve Bitirme Projesi II'nin iş planı
4. Kaynaklar (24 kaynak)

Sunumu derlemek için:

```bash
cd presentation
pdflatex -shell-escape presentation.tex   # iki kez çalıştırın
```

# MAT 4901E — Bitirme Projesi I: Matematiksel Modelleme ve Formülasyon

Bu aşamada plug-in FCHEV enerji yönetimi problemi **matematiksel olarak kurulmuştur**:
araç boyuna dinamiği, PEMFC yığınının Mann–Amphlett GSSEM modeli, batarya eşdeğer
devre modelleri, maliyet fonksiyonu ve kısıtlar türetilmiş; problem sonlu ufuklu bir
optimal kontrol problemi olarak ifade edilmiş ve çözüm stratejileri (DP, ECMS/PMP,
MPC, BLFS) gerekçelendirilmiştir. Sayısal çözüm [`../bitirme2/`](../bitirme2/)
klasöründedir.

| Dosya | İçerik |
|---|---|
| `report/MAT4901E_Report_final_v2.pdf` | **Teslim edilen nihai rapor** (.docx kaynağı yanındadır) |
| `report/MAT4901E_Report_draft.pdf` | Erken taslak sürüm |
| `presentation/presentation.tex` | Savunma sunumu — Beamer kaynağı (TikZ/pgfplots, harici şekil gerektirmez) |
| `presentation/FCHEV_Presentation.pptx` | Sunumun PowerPoint sürümü |
| `figures/` | WLTP hız profili ve OCV–SoC düz bölge şekilleri |
| `kaynaklar/` | Kullanılan 22 kaynağın listesi (PDF'ler telif nedeniyle depoda değildir) |

Sunumu derlemek için:

```bash
cd presentation
pdflatex -shell-escape presentation.tex   # iki kez çalıştırın
```

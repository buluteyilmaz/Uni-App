# Başvuru Kütüphanesi

Üniversite başvurularını 3D bir kütüphane odasında gösteren tek sayfalık web uygulaması.
Raflardaki her kitap bir üniversite/bölüm; kitaba tıklayınca uçarak önüne gelir ve açılır.

## Çalıştırma
`index.html` dosyasını tarayıcıda açman yeterli (internet gerekli: three.js ve fontlar CDN'den gelir).

## Tabloyu güncelleme
1. `veri/Universite_Basvuru_Tablosu.xlsx` dosyasını düzenle.
2. `pip install openpyxl && python3 tools/excel_to_data.py`
3. Sayfayı yenile; kitaplar `data.js` dosyasından yeniden oluşur.

## Kontroller
- Sürükle: etrafına bak · Tekerlek / iki parmak: yakınlaş
- Kitaba tıkla: aç · ← → : önceki/sonraki kitap · Esc: rafa koy
- Katalog: arama, yaklaşan tarihler, ülkeye göre liste
- Kitapların üstündeki renkli sekme: kırmızı = 3 haftadan az kaldı, yeşil = açık, sarı = açılacak, gri = kapandı
- "Eksiklerim" maddeleri işaretlenebilir (yalnızca o tarayıcıda saklanır)

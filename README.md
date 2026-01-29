# filmoneri-llm

# tmdb_fetch_tv.py — Ham veri toplama

TMDB’den dizi listesini çeker

Sadece temel bilgiler alır (ad, özet, puan vb.)

Amaç: aday dizi havuzu oluşturmak

 "Hangi diziler var?” sorusunun cevabını alırız.

# tmdb_enrich_tv.py — Veriyi zenginleştirme

Veriyi zenginleştirmek için kullanırız

Ham dizi listesini alır (tmbd_fetch_tv.py dosyasından üretilen)

Her dizi için TMDB’den detay bilgileri çeker

Tür isimleri, keyword’ler, sezon/bölüm sayısı, oyuncular vb. ekler

“Bu diziler ne anlatıyor?” sorusunun cevabını alırız.


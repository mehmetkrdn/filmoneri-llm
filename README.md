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

# build_llm_jsonl.py ne yapıyor?

Bu script: titles_enriched.jsonl dosyasını okur Her dizinin dağınık bilgilerini tek, anlamlı bir metne (doc_text) dönüştürür

Çıktıyı LLM / RAG / embedding için hazır hale getirir

“Her satır = 1 dizi + doc_text” ne demek?

llm_titles.jsonl dosyasında: Her satır tek bir diziyi temsil eder

doc_text alanı: Dizinin adı, Konusu,Türleri,Anahtar kelimeleri,Oyuncuları,Sezon / bölüm bilgileri,tek bir metin halinde içerir

 Bu metin:

Embedding modeline verilir

Benzerlik hesabının temelini oluşturur

LLM’e bağlam (context) olarak sunulur

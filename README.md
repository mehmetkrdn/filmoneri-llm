# LLM ile Dizi Öneri Sistemi

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

Bu kod, zenginleştirilmiş dizi verisini LLM’in gerçekten “anlayabileceği” forma sokar ve her diziyi embedding + RAG için hazır hale getirir.

# build_embeddings.py ne yapıyor?

Zenginleştirilmiş dizi verilerindeki (llm_titles.jsonl) metinleri embedding (sayısal vektör) haline getirir. Bu vektörler, diziler arası anlamsal benzerlik hesaplamak için kullanılır.

Niçin kullandık?

LLM ve öneri sistemlerinin metni doğrudan değil, sayısal temsil (embedding) üzerinden karşılaştırması gerektiği için.

Nasıl çalıştırılır?

python build_embeddings.py --infile llm_data/llm_titles.jsonl --outdir embedding

# recommend.py ne yapıyor?

Üretilmiş embedding’leri kullanarak, kullanıcının verdiği metin sorgusuna en benzer dizileri (Top-K) cosine similarity ile bulur.

Niçin kullandık?

LLM’e gitmeden önce, aday dizileri hızlı ve matematiksel olarak doğru şekilde filtrelemek (retrieval aşaması) için.

Nasıl çalıştırılır?

python recommend.py --store embedding --query "mafya suç karanlık" --k 5

RAG kısmının 'R' kısmıdır. Retrieval, kullanıcının isteğine anlamsal olarak en yakın dizileri bulma işlemidir.

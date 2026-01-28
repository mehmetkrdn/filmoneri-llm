# filmoneri-llm

# tmdb_fetch_tv.py — Dizi Verisi Toplama Scripti

Bu script, TMDB (The Movie Database) API kullanarak dizi öneri sistemi için gerekli olan ham dizi verilerini otomatik olarak toplamak amacıyla geliştirilmiştir. Projenin veri toplama aşamasındaki ilk adımı temsil eder.

Amaç

tmdb_fetch_tv.py, TMDB üzerinde yer alan popüler dizileri belirli filtreler altında çekerek, öneri sisteminde kullanılacak aday dizi havuzunu oluşturur. Bu aşamada toplanan veriler daha sonra detaylandırılmak ve zenginleştirilmek üzere saklanır.

Ne Yapar?

Script aşağıdaki işlemleri gerçekleştirir:

TMDB’nin Discover TV endpoint’ini kullanarak dizi listelerini çeker

Sayfalama (pagination) yaparak binlerce diziyi otomatik olarak toplar

Belirli bir oy sayısının (vote_count) altındaki dizileri filtreler

Verileri satır satır JSON Lines (.jsonl) formatında kaydeder

Daha önce çekilmiş dizileri tekrar indirmez (kaldığı yerden devam edebilir)


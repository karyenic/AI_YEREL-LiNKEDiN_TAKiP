# AI_YEREL-LiNKEDiN_TAKiP - Proje Son Durum

Guncelleme tarihi: 2026-10-05 01:57:22

## 1. Ana veri modeli

Adayin temel kimligi ve mevcut durumu ile surec/gecmis birbirinden ayrilacaktir.

### ADAY PROFILI
- id
- isim
- linkedin_url
- telefon
- email
- adres
- kayit_tarihi
- durum

### SUREC / OLAY GECMISI
Adayla ilgili gerceklesen islemler ve notlar olay/gecmis olarak tutulabilir:
- Gorüsme
- Not
- Davet
- Randevu
- Plan
- Takip
- Kayit sonrasi baslatma
- Diger surec olaylari

## 2. Ana aday durumlari

Adayin tek bir guncel ana durumu olacaktir:

- 🔥 Sicak
- 🟢 Aktif
- ⚪ Degerlendirilecek
- ❄️ DeepFreeze
- 🔴 Olumsuz

## 3. Durumlarin yasam dongusu

Yeni aday ilk kez programa girdiginde:

- 🔥 Sicak
- 🟢 Aktif
- ⚪ Degerlendirilecek

secenekleri kullanilabilir.

Asagidaki durumlar ilk kayitta ana durum olarak secilmemelidir:

- ❄️ DeepFreeze
- 🔴 Olumsuz

Bunlar surec icerisinde ortaya cikabilecek sonuc durumlaridir.

DeepFreeze kalici arsiv/silme anlamina gelmez. Gerektiginde aday tekrar:
- 🔥 Sicak
- 🟢 Aktif
- ⚪ Degerlendirilecek

durumlarindan birine alinabilir.

## 4. Eski statulerin yeni anlamlandirilmasi

Asagidaki alanlar adayin ana statuleri olmaktan cikarilmalidir:

- 🆕 Yeni
- 🟡 Bekliyor
- 🔔 Takip
- 🚀 Kayit Sonrasi Baslatma

Bunlar gerekiyorsa olay/gecmis kaydi olarak tutulabilir.

Ayrica eski checkbox mantigi:
- Davet
- Randevu
- Plan
- Kayit
- Takip
- Hayir
- Is Ariyor

tek bir "ana durum" mantigi ile karistirilmamalidir. Gereken bilgiler surec olaylari/gecmisi olarak modellenmelidir.

## 5. Kayit Tarihi kurali

"Kayıt Tarihi" adayın bu programa ilk kez kaydedildigi tarihtir.

Kaynak ne olursa olsun:
- Excel
- Keep
- Manuel giris
- Gelecekte eklenecek baska kaynaklar

aday ilk kez programa girdigi anda program kayit tarihi olusturulur.

Bu tarih:
- tekrar Excel aktariminda degismemeli,
- Keep tekrar aktariminda degismemeli,
- mevcut aday guncellendiginde degismemeli,
- kaynak dosyanin/eski notun tarihi tarafindan ezilmemelidir.

Kaynak veya olay tarihi gerekiyorsa ayri olay/gecmis alaninda tutulmalidir.

## 6. Aday kimligi

LinkedIn URL mevcutsa aday eslestirmede guclu kimlik olarak kullanilmalidir.

Ayni adli kisilerin yanlis birlestirilmesini onlemek icin isim tek basina guvenilir ana kimlik olarak kullanilmamalidir.

## 7. UI hedefi

Aday listesi sadeletilecektir:

ID | Isim | Kayit Tarihi | Aciklama | Durum | Islem

"Sil" butonu, "Islem" basliginin altinda yer almalidir.

## 8. AI stratejisi

AI modelinin karar/strateji uretmesi icin:

1. Aday profili
2. Mevcut ana durum
3. Olay/gecmis kayitlari
4. Son gelismeler
5. Kaynak bilgisi

ayri katmanlar olarak modele sunulmalidir.

Model, eski checkbox/status alanlarini adayın mevcut ana durumu ile karistirmamalidir.

## 9. Bu asamanin amaci

Bu commit kod davranisini degistirmekten once projenin veri ve surec mimarisini net bir referans halinde GitHub'da saklamaktir.

Sonraki kodlama adiminda once:
- database.py
- excel_io.py
- routes/keep.py
- routes/candidates.py
- static/app.js
- templates/index.html

arasindaki veri akisinin tamamlanmasi ve mevcut migration/schema durumunun kontrol edilmesi gerekir.

Kod degisikligi bu haritalama sonrasinda, kucuk ve test edilebilir adimlarla yapilmalidir.

# ▶ ÇALIŞTIR (tek tık, HİÇBİR ŞEY YAZMA): https://phomphachi.github.io/Toogx/go.html

> Adres çubuğu olmayan kiosk WebView'i için: bu linke **tıkla**, gerisi kendiliğinden olur (hash gerekmez).
> Aracın WebView'inde bu adresi aç → test **otomatik başlar**, sonuçlar `ntfy.sh/toggx-ivi-7f3k9q2m`'e düşer.
> 🛡️ **Sıkı mod (varsayılan):** her vektör sandbox'lı bir iframe'de denenir; web sayfası **üst çerçeveyi hiç terk etmez** (üst-gezinme/pencere-açma kapalı). Sayfa seni bırakmaz → GitHub'a baştan girmen gerekmez.
> Ekran kararır/blackout olsa bile her adım anında ntfy'ye gider; sayfayı yeniden açınca **kaldığı yerden devam eder, baştan başlamaz.**
> Kök `https://phomphachi.github.io/Toogx/` de çalışan bir test varsa açılışta otomatik `exploit.html#auto`'ya geçer.

---

# Toogx — Togg IVI WebView Paneli

Kendi aracının (Togg) IVI/WebView yüzeyini **park hâlinde** test eden statik sayfalar.

## 🔗 Doğrudan geçiş (canlı)
- **▶ TEK TIK ÇALIŞTIR (adres çubuğu gerekmez):** https://phomphachi.github.io/Toogx/go.html  (hash'siz; açılınca `exploit.html#auto`'ya geçer)
- **Panel:** https://phomphachi.github.io/Toogx/
- **Ortam / WebView:** https://phomphachi.github.io/Toogx/probe.html#auto  (açılınca oto-recon + ntfy)
- **Klavye / Seçim:** https://phomphachi.github.io/Toogx/klavye.html
- **Exploit / Oto-Test:** https://phomphachi.github.io/Toogx/exploit.html#auto  (açılınca otomatik başlar; **sıkı mod = üst sayfa asla terk edilmez**)
- **Exploit / Oto-Test (SERBEST NAV — dikkat):** https://phomphachi.github.io/Toogx/exploit.html#auto&nav  (`sandbox` yok; `location.href` ile şema dener — "sayfa kaldı" = blok, "terk edildi" = sinyal. Bu modda sayfa kaybolabilir; sadece bilinçli kullan.)
- **S4 Intent:** https://phomphachi.github.io/Toogx/intent.html
- **Sürüm / UA-CH:** https://phomphachi.github.io/Toogx/uach.html  (motor/UA-CH sürüm ölçümü + ntfy)
- **Yüzey tarayıcı:** https://phomphachi.github.io/Toogx/surface.html  (JS köprü/sink/global + GPU yüzeyi)
- **KILL probu:** https://phomphachi.github.io/Toogx/kill.html  (KILL-flag yüzey taraması)
- **Invoke:** https://phomphachi.github.io/Toogx/invoke.html  (kademeli KILL-probe + kaçış tespiti)
- **Dosya seçici:** https://phomphachi.github.io/Toogx/upload.html  (WebView file-chooser/focus-trap/IME)
- **DevOptions:** https://phomphachi.github.io/Toogx/devopt.html  (FLAG_SECURE/navigasyon ayrım probu)

> Not: `github.com/.../blob/...` adresi **kaynak kodu** gösterir, sayfayı çalıştırmaz.
> Çalışan site her zaman **`.github.io`** adresidir (GitHub Pages).

## Sayfalar
| Sayfa | İş |
|-------|----|
| `index.html` | Bypass paneli — intent/app-link/şema denemeleri, Özel Intent formu, Fuzz, kopyala |
| `probe.html` | Ortam ölçümü — UA/kiosk tipi, köprü taraması, şema matrisi, file/`window.open` testleri |
| `klavye.html` | Klavye + metin-seçim menüsü testi, giriş gecikmesi ölçer, manuel geçiş yolları |
| `portal.html` | Captive-portal yükü — sistem WebView'inde OOB vektörlerini sırayla dener, kaçış sinyalini loglar |
| `exploit.html` | **YENİ!** WebView exploit paneli — kritik sistem erişimi için önceden hazırlanmış intent exploit'leri |
| `uach.html` | Motor/UA-CH sürüm ölçümü — `navigator.userAgentData`, UA-izolasyon sinyalleri, API→min Chromium tablosu, GPU unmasked (ntfy) |
| `surface.html` | JS yüzey tarayıcı — köprü/sink metot, enjekte globals, GPU/GL ext |
| `kill.html` | KILL-flag yüzey taraması (bridge+globals+GPU+UA) |
| `invoke.html` | Kademeli KILL-probe (no-arg/empty/benign/intent) + kaçış tespiti |
| `upload.html` | WebView dosya-seçici/focus-trap/IME kanal probu |
| `devopt.html` | FLAG_SECURE/navigasyon ayrım probu (heartbeat+visibility+pagehide) |
| `captive_server.py` | Laptop AP'si için minimal portal sunucusu (bağımlılıksız): DNS hijack + HTTP `302` → `portal.html` |

## Kullanım
1. Aracın WebView'inde yukarıdaki `.github.io` adresini aç (örn. Google → GitHub → link).
2. Sekmeler birbirine linkli; `index.html` giriştir.
3. Yalnız **kendi aracında, park hâlinde**.

## Captive portal (laptop AP'si)
Aracı laptopun AP'sine bağlayıp **sistem WebView'inde** `portal.html`'i açtırmak için:
1. Laptop'ta **Mobile Hotspot**'u aç (SSID/şifre belirle).
2. Yönetici PowerShell'de sunucuyu başlat: `python captive_server.py`
3. Firewall (bir kez): `netsh advfirewall firewall add rule name="portal-http" dir=in action=allow protocol=TCP localport=80` (ve UDP 53 için aynısı).
4. Aracı AP'ye bağla → `connectivitycheck` isteği `302` alır → portal açılır.

> Düz hotspot portal **tetiklemez**; tetikleyen şey DNS'i laptop IP'sine çevirip HTTP'yi `302`'lemektir (bu sunucu onu yapar).

## Yapı
`index.html` · `probe.html` · `klavye.html` · `portal.html` · `exploit.html` · `intent.html` · `uach.html` · `surface.html` · `kill.html` · `invoke.html` · `upload.html` · `devopt.html` · `style.css` (ortak tema) · `common.js` (`ToggKit` — intent üretici) · `captive_server.py` (yerel portal sunucusu)

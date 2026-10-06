# Toogx — Togg IVI WebView Paneli

Kendi aracının (Togg) IVI/WebView yüzeyini **park hâlinde** test eden statik sayfalar.

## 🔗 Doğrudan geçiş (canlı)
- **Panel:** https://phomphachi.github.io/Toogx/
- **Ortam / WebView:** https://phomphachi.github.io/Toogx/probe.html
- **Klavye / Seçim:** https://phomphachi.github.io/Toogx/klavye.html

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
`index.html` · `probe.html` · `klavye.html` · `portal.html` · `style.css` (ortak tema) · `common.js` (`ToggKit` — intent üretici) · `captive_server.py` (yerel portal sunucusu)

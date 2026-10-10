# ▶ ÇALIŞTIR (tek tık, HİÇBİR ŞEY YAZMA)

## **https://phomphachi.github.io/Toogx/go.html**

> Adres çubuğu olmayan kiosk WebView'i için: bu linke **tıkla**, gerisi kendiliğinden olur (hash gerekmez).
> Aracın WebView'inde bu adresi aç → test **otomatik başlar**, sonuçlar `ntfy.sh/toggx-ivi-7f3k9q2m`'e düşer.
> 🛡️ **Sıkı mod (varsayılan):** her vektör sandbox'lı bir iframe'de denenir; web sayfası **üst çerçeveyi hiç terk etmez** (üst-gezinme/pencere-açma kapalı). Sayfa seni bırakmaz → GitHub'a baştan girmen gerekmez.
> Ekran kararır/blackout olsa bile her adım anında ntfy'ye gider; sayfayı yeniden açınca **kaldığı yerden devam eder, baştan başlamaz.**
> Kök `https://phomphachi.github.io/Toogx/` de çalışan bir test varsa açılışta otomatik `exploit.html#auto`'ya geçer.

---

# Toogx — Togg IVI WebView Test Paneli

Kendi aracının (**Togg T10X**) IVI / WebView yüzeyini **park hâlinde**, non-invazif olarak test eden statik
(bağımlılıksız) sayfalar. Motor sürümünden native köprüye, intent kaçışından captive-portal'a kadar tüm
ölçümler tek panelde toplanır; sonuçlar gerçek zamanlı olarak `ntfy` kanalına akar.

| | |
|---|---|
| 🌐 **Canlı site** | https://phomphachi.github.io/Toogx/ |
| 📡 **Sonuç kanalı (ntfy)** | `toggx-ivi-7f3k9q2m` → https://ntfy.sh/toggx-ivi-7f3k9q2m |
| ▶ **Tek tık başlat** | https://phomphachi.github.io/Toogx/go.html |

> Not: `github.com/.../blob/...` adresi **kaynak kodu** gösterir, sayfayı çalıştırmaz.
> Çalışan site her zaman **`.github.io`** adresidir (GitHub Pages).

## 🔗 Sayfalar (canlı)

| # | Sayfa | İş | Oto |
|---|-------|----|:--:|
| ▶ | [`go.html`](https://phomphachi.github.io/Toogx/go.html) | **Tek tık başlatıcı** — açılınca `exploit.html#auto`'ya geçer | ✅ |
| 1 | [`index.html`](https://phomphachi.github.io/Toogx/) | **Bypass paneli** — intent / app-link / şema denemeleri, Özel Intent formu, Fuzz, kopyala | — |
| 2 | [`exploit.html`](https://phomphachi.github.io/Toogx/exploit.html#auto) | **Exploit / Oto-Test** — hazır intent exploit'leri; `#auto` ile otomatik | ✅ |
| 3 | [`probe.html`](https://phomphachi.github.io/Toogx/probe.html#auto) | **Ortam / WebView** — UA/kiosk tipi, köprü taraması, şema matrisi, file/`window.open` | ✅ |
| 4 | [`surface.html`](https://phomphachi.github.io/Toogx/surface.html) | **JS yüzey** — köprü/sink metot, enjekte global'ler, GPU/GL ext + **WebView hardening** (CSP/TT/CORS/sourcemap) | — |
| 5 | [`uach.html`](https://phomphachi.github.io/Toogx/uach.html) | **Sürüm / UA-CH** — `navigator.userAgentData`, UA izolasyonu, GPU unmasked | — |
| 6 | [`intent.html`](https://phomphachi.github.io/Toogx/intent.html) | **S4 Intent** — intent/app-link/şema üretimi ve denemesi | — |
| 7 | [`klavye.html`](https://phomphachi.github.io/Toogx/klavye.html) | **Klavye / Seçim** — metin-seçim menüsü, giriş gecikmesi ölçer, manuel geçiş | — |
| 8 | [`kill.html`](https://phomphachi.github.io/Toogx/kill.html) | **KILL probu** — KILL-flag yüzey taraması (bridge + globals + GPU + UA) | — |
| 9 | [`invoke.html`](https://phomphachi.github.io/Toogx/invoke.html) | **Invoke** — kademeli KILL-probe (no-arg/empty/benign/intent) + kaçış tespiti | — |
| 10 | [`upload.html`](https://phomphachi.github.io/Toogx/upload.html) | **Dosya seçici** — WebView file-chooser / focus-trap / IME kanal probu | — |
| 11 | [`devopt.html`](https://phomphachi.github.io/Toogx/devopt.html) | **DevOptions** — FLAG_SECURE / navigasyon ayrım probu (heartbeat+visibility+pagehide) | — |
| 12 | [`portal.html`](https://phomphachi.github.io/Toogx/portal.html) | **Captive portal** — sistem WebView'inde OOB vektörlerini sırayla dener, kaçış sinyalini loglar | — |

## ⚙️ İki mod

- **Sıkı mod (varsayılan)** — her vektör sandbox'lı iframe'de; **üst çerçeve asla terk edilmez**. Sayfa sende kalır, kaybolmaz.
- **Serbest nav (`exploit.html#auto&nav`)** — `sandbox` yok, `location.href` ile şema denenir. "Sayfa kaldı" = blok, "terk edildi" = sinyal. ⚠️ Bu modda sayfa kaybolabilir; **yalnız bilinçli kullan**.

## 🚀 Kullanım

1. Aracın WebView'inde yukarıdaki `.github.io` adresini aç (örn. Google → GitHub → link).
2. Sekmeler birbirine linkli; `index.html` giriştir.
3. Yalnız **kendi aracında, park hâlinde**.

## 📡 Captive portal (laptop AP'si)

Aracı laptopun AP'sine bağlayıp **sistem WebView'inde** `portal.html`'i açtırmak için:

1. Laptop'ta **Mobile Hotspot**'u aç (SSID/şifre belirle).
2. Yönetici PowerShell'de sunucuyu başlat: `python captive_server.py`
3. Firewall (bir kez): `netsh advfirewall firewall add rule name="portal-http" dir=in action=allow protocol=TCP localport=80` (UDP 53 için aynısı).
4. Aracı AP'ye bağla → `connectivitycheck` isteği `302` alır → portal açılır.

> Düz hotspot portal **tetiklemez**; tetikleyen şey DNS'i laptop IP'sine çevirip HTTP'yi `302`'lemektir (bu sunucu onu yapar).

## 🗂️ Yapı

| Dosya | İş |
|-------|----|
| `go.html` | Tek tık başlatıcı (otomatik `exploit.html#auto`) |
| `index.html` | Bypass paneli (giriş) |
| `probe.html` · `surface.html` · `uach.html` | Ortam / yüzey / sürüm ölçümü |
| `intent.html` · `exploit.html` | Intent üretimi + exploit/oto-test |
| `kill.html` · `invoke.html` | KILL-flag / invoke probları |
| `klavye.html` · `upload.html` · `devopt.html` | Klavye, dosya seçici, DevOptions probları |
| `portal.html` · `captive_server.py` | Captive portal yükü + laptop portal sunucusu (DNS hijack + `302`) |
| `common.js` | `ToggKit` — intent üretici + ortak yardımcılar |
| `style.css` | Ortak tema |

## 🛡️ Kısıtlar

Statik · bağımlılıksız · non-invazif · **yalnız kendi aracında, park hâlinde** kullanım için.

#!/usr/bin/env python3
"""captive_server.py - Windows'ta laptop AP'si icin minimal CAPTIVE PORTAL (bagimlilik yok).

Amac: arac, laptopun Wi-Fi AP'sine baglaninca Android'in connectivity-check istegine
302 donup "captive portal" algilatmak ve SISTEM WebView'inde portal.html'i actirmak.

Iki servis:
  * DNS  (UDP :53)  -> TUM A sorgularini laptop IP'sine cevirir (AAAA bos -> A'ya duser)
  * HTTP (TCP :80)  -> her yolu 302 ile /portal.html'e yonlendirir; static dosyalari serve eder

Proxy (adres cubugu olmayan kiosk WebView icin):
  * HTTP GET /p?u=<url>  -> hedef sayfayi sunucu tarafi ceker, HTML/CSS icindeki
    linkleri /p?u=... uzerinden yeniden yazar ve ayni origin'den servis eder.
    Boylece HTTPS hedefler bile CA/sertifika olmadan gezilebilir (laptop HTTP'de kalir).
  * GET /p  (u yok)      -> basit URL formu.

Kullanim (YONETICI PowerShell):
  python captive_server.py                 # IP otomatik (192.168.137.1)
  python captive_server.py --ip 192.168.137.1 --http-port 80 --dns-port 53
  python captive_server.py --no-dns        # yalniz HTTP (DNS'i baska yere birak)

Firewall (yonetici, bir kez):
  netsh advfirewall firewall add rule name="portal-http" dir=in action=allow protocol=TCP localport=80
  netsh advfirewall firewall add rule name="portal-dns"  dir=in action=allow protocol=UDP localport=53

NOT: Mobile Hotspot acikken ICS kendi DNS'ini :53'e baglayabilir. O durumda once
  netstat -ano | findstr :53   ile bak; cakisma varsa ICS'i degil, bu scripti once baslat.
"""
import argparse
import os
import re
import socket
import struct
import sys
import threading
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
MIME = {".html": "text/html; charset=utf-8", ".js": "application/javascript",
        ".css": "text/css", ".json": "application/json", ".ico": "image/x-icon",
        ".png": "image/png", ".txt": "text/plain; charset=utf-8"}

PROXY_UA = ("Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36")
PROXY_SCHEMES = ("http", "https")
PROXY_SKIP_SCHEMES = ("data", "javascript", "mailto", "tel", "sms", "blob",
                      "about", "geo", "market", "intent", "file", "content")
PROXY_TIMEOUT = 20.0

_ATTR_RE = re.compile(r"""(\b(?:href|src|action|poster)\s*=\s*)(["'])(.*?)\2""", re.I | re.S)
_SRCSET_RE = re.compile(r"""(\bsrcset\s*=\s*)(["'])(.*?)\2""", re.I | re.S)
_CSSURL_RE = re.compile(r"""url\(\s*(['"]?)(.*?)\1\s*\)""", re.I | re.S)
_CSSIMPORT_RE = re.compile(r"""(@import\s+)(["'])(.*?)\2""", re.I | re.S)


def _proxy_wrap(url):
    """Mutlak URL'yi /p?u= bicimine cevir (yuzde-encode; hedefteki & bozmaz)."""
    return "/p?u=" + urllib.parse.quote(url, safe="")


def _proxy_abs(base, raw):
    """raw linkini base'e gore cozer; yalniz http/https ise proxy'ye sarar, degilse dokunmaz."""
    raw = (raw or "").strip()
    if not raw or raw.startswith("#"):
        return raw
    scheme = raw.split(":", 1)[0].lower() if ":" in raw else ""
    if scheme in PROXY_SKIP_SCHEMES:
        return raw
    try:
        absu = urllib.parse.urljoin(base, raw)
    except ValueError:
        return raw
    if urllib.parse.urlparse(absu).scheme.lower() not in PROXY_SCHEMES:
        return raw
    return _proxy_wrap(absu)


def _rewrite_css(text, base):
    def _url(m):
        return "url(" + m.group(1) + _proxy_abs(base, m.group(2)) + m.group(1) + ")"
    text = _CSSURL_RE.sub(_url, text)

    def _imp(m):
        return m.group(1) + m.group(2) + _proxy_abs(base, m.group(3)) + m.group(2)
    return _CSSIMPORT_RE.sub(_imp, text)


def _rewrite_html(text, base):
    def _attr(m):
        return m.group(1) + m.group(2) + _proxy_abs(base, m.group(3)) + m.group(2)
    text = _ATTR_RE.sub(_attr, text)

    def _srcset(m):
        parts = []
        for cand in m.group(3).split(","):
            cand = cand.strip()
            if not cand:
                continue
            bits = cand.split(None, 1)
            bits[0] = _proxy_abs(base, bits[0])
            parts.append(" ".join(bits))
        return m.group(1) + m.group(2) + ", ".join(parts) + m.group(2)
    text = _SRCSET_RE.sub(_srcset, text)
    return _rewrite_css(text, base)


def hosts_ip():
    """Hotspot arayuz IP'sini tahmin et (192.168.137.1), yoksa ilk ozel IP."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.137.1", 53))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            return ip
    except OSError:
        pass
    for probe_ip in ("192.168.137.1",):
        try:
            t = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            t.bind((probe_ip, 0))
            t.close()
            return probe_ip
        except OSError:
            continue
    return "192.168.137.1"


def _qname_end(data, off):
    while off < len(data):
        ln = data[off]
        if ln == 0:
            return off + 1
        if ln & 0xC0:
            return off + 2
        off += 1 + ln
    return off


def _relay(data, upstream):
    """Hotspot-disi istemciler icin sorguyu gercek DNS'e ilet (laptop DNS'i bozulmasin)."""
    r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    r.settimeout(2.0)
    try:
        r.sendto(data, (upstream, 53))
        yanit, _ = r.recvfrom(4096)
        return yanit
    except OSError:
        return None
    finally:
        r.close()


def dns_servis(ip, dns_port, durdur, upstream="1.1.1.1"):
    """Hotspot subnet'inden gelen TUM A sorgularini `ip`'ye cevaplar; digerlerini upstream'e iletir."""
    prefix = ip.rsplit(".", 1)[0] + "."
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((ip, dns_port))
        print("[dns] bagli %s:%d (ozel)" % (ip, dns_port))
    except PermissionError:
        print("[!] DNS :%d icin YONETICI gerekli." % dns_port)
        return
    except OSError as e:
        try:
            sock.bind(("0.0.0.0", dns_port))
            print("[dns] %s:%d olmadi (%s) -> 0.0.0.0" % (ip, dns_port, e))
        except OSError:
            print("[!] DNS :%d baglanamadi (baska servis tutuyor?)" % dns_port)
            return
    sock.settimeout(1.0)
    print("[dns] UDP :%d  -> %s* = %s ; digerleri %s" % (dns_port, prefix, ip, upstream))
    while not durdur.is_set():
        try:
            data, addr = sock.recvfrom(512)
        except socket.timeout:
            continue
        except OSError:
            break
        print("[dns] pkt %s:%d %db" % (addr[0], addr[1], len(data)), flush=True)
        if not addr[0].startswith(prefix):
            yanit = _relay(data, upstream)
            if yanit:
                try:
                    sock.sendto(yanit, addr)
                except OSError:
                    pass
            continue
        if len(data) < 12:
            continue
        qend = _qname_end(data, 12)
        if qend + 4 > len(data):
            continue
        qtype = struct.unpack(">H", data[qend:qend + 2])[0]
        cevap = bytearray(data[:2]) + b"\x81\x80" + struct.pack(">H", 1)
        cevap += struct.pack(">H", 1 if qtype == 1 else 0) + b"\x00\x00\x00\x00"
        cevap += data[12:qend + 4]
        if qtype == 1:
            cevap += b"\xc0\x0c" + struct.pack(">HHIH", 1, 1, 20, 4) + socket.inet_aton(ip)
        try:
            sock.sendto(bytes(cevap), addr)
        except OSError:
            pass


class Portal(BaseHTTPRequestHandler):
    server_version = "Portal/1.0"
    bind_ip = "192.168.137.1"
    http_port = 80

    def log_message(self, fmt, *args):
        sys.stdout.write("[http] %s %s\n" % (self.address_string(), fmt % args))
        sys.stdout.flush()

    def _hedef(self):
        return "http://%s:%d/portal.html" % (self.bind_ip, self.http_port)

    def _yonlendir(self, kod=302):
        self.send_response(kod)
        self.send_header("Location", self._hedef())
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()

    def _captive_api(self):
        govde = ('{"captive":true,"user-portal-url":"%s"}' % self._hedef()).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/captive+json")
        self.send_header("Content-Length", str(len(govde)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(govde)

    def _html(self, govde, kod=200):
        self.send_response(kod)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(govde)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(govde)

    def _proxy_hata(self, msg):
        govde = ("<!DOCTYPE html><meta charset='utf-8'>"
                 "<meta name=viewport content='width=device-width,initial-scale=1'>"
                 "<body style='font:16px sans-serif;background:#111;color:#eee;padding:24px'>"
                 "<b>Proxy</b><br>" + msg +
                 "<br><br><a style='color:#4da3ff' href='/p'>&larr; yeni URL</a></body>").encode("utf-8")
        self._html(govde)

    def _proxy_form(self):
        govde = ("<!DOCTYPE html><meta charset='utf-8'>"
                 "<meta name=viewport content='width=device-width,initial-scale=1'>"
                 "<body style='font:18px sans-serif;background:#111;color:#eee;padding:24px'>"
                 "<h2>&#127760; Proxy</h2>"
                 "<form method='get' action='/p'>"
                 "<input name='u' autofocus autocomplete='off' spellcheck='false' "
                 "style='width:72%;padding:10px;font-size:16px' placeholder='https://...'> "
                 "<button style='padding:10px 16px;font-size:16px'>Ac</button></form>"
                 "<p style='opacity:.7'>Linkler otomatik olarak /p?u= uzerinden yeniden yazilir.</p>"
                 "</body>").encode("utf-8")
        self._html(govde)

    def _proxy_get(self, url):
        p = urllib.parse.urlparse(url)
        if p.scheme.lower() not in PROXY_SCHEMES or not p.netloc:
            self._proxy_hata("Gecersiz URL (yalniz http/https).")
            return
        istek = urllib.request.Request(url, headers={
            "User-Agent": PROXY_UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr,en;q=0.8",
        })
        try:
            with urllib.request.urlopen(istek, timeout=PROXY_TIMEOUT) as y:
                ham = y.read()
                ctype = y.headers.get("Content-Type", "application/octet-stream")
                son = y.geturl() or url
        except Exception as e:  # proxy siniri: hatayi kullaniciya goster, gizleme
            self._proxy_hata("Proxy hata: %s" % e)
            return
        ana, _, cset = ctype.partition(";")
        ana = ana.strip().lower()
        if ana in ("text/html", "application/xhtml+xml"):
            charset = "utf-8"
            m = re.search(r"charset=([\w\-]+)", cset, re.I)
            if m:
                charset = m.group(1)
            try:
                metin = ham.decode(charset, "replace")
            except LookupError:
                metin = ham.decode("utf-8", "replace")
            govde = _rewrite_html(metin, son).encode("utf-8")
            out_ct = "text/html; charset=utf-8"
        elif ana == "text/css":
            try:
                metin = ham.decode("utf-8", "replace")
            except Exception:
                metin = ""
            govde = _rewrite_css(metin, son).encode("utf-8")
            out_ct = "text/css; charset=utf-8"
        else:
            govde = ham
            out_ct = ctype
        self.send_response(200)
        self.send_header("Content-Type", out_ct)
        self.send_header("Content-Length", str(len(govde)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(govde)

    def _serve(self, ad, gonder=True):
        yol = os.path.join(BASE, os.path.basename(ad))
        if not os.path.isfile(yol):
            self._yonlendir()
            return
        with open(yol, "rb") as f:
            govde = f.read()
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(os.path.splitext(ad)[1].lower(), "application/octet-stream"))
        self.send_header("Content-Length", str(len(govde)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if gonder:
            self.wfile.write(govde)

    def do_GET(self):
        yol = self.path.split("?", 1)[0]
        if yol == "/p":
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            hedef = (q.get("u") or [""])[0].strip()
            if hedef:
                self._proxy_get(hedef)
            else:
                self._proxy_form()
            return
        if yol in ("/", "/portal.html"):
            self._serve("portal.html")
        elif yol in ("/_/captiveportal", "/captiveportal", "/captive-portal"):
            self._captive_api()
        elif "generate_204" in yol or "gen_204" in yol:
            self._yonlendir()
        else:
            ad = os.path.basename(yol)
            if os.path.isfile(os.path.join(BASE, ad)):
                self._serve(ad)
            else:
                self._yonlendir()

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        self._yonlendir()


def main():
    ap = argparse.ArgumentParser(description="Minimal captive portal (DNS hijack + HTTP redirect).")
    ap.add_argument("--ip", default=None, help="portal IP (varsayilan: otomatik)")
    ap.add_argument("--http-port", type=int, default=80)
    ap.add_argument("--dns-port", type=int, default=53)
    ap.add_argument("--no-dns", action="store_true", help="DNS servisini baslatma")
    ap.add_argument("--upstream", default="1.1.1.1", help="hotspot-disi sorgular icin gercek DNS")
    a = ap.parse_args()

    ip = a.ip or hosts_ip()
    durdur = threading.Event()
    if not a.no_dns:
        threading.Thread(target=dns_servis, args=(ip, a.dns_port, durdur, a.upstream), daemon=True).start()

    Portal.bind_ip = ip
    Portal.http_port = a.http_port
    try:
        sunucu = ThreadingHTTPServer(("0.0.0.0", a.http_port), Portal)
    except PermissionError:
        print("[!] HTTP :%d icin YONETICI gerekli." % a.http_port)
        return 2
    print("[http] TCP :%d  -> 302 http://%s:%d/portal.html" % (a.http_port, ip, a.http_port))
    print("[*] Arac AP'ye baglaninca portal.html sistem WebView'inde acilmali. Ctrl+C ile cik.")
    try:
        sunucu.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        durdur.set()
        sunucu.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

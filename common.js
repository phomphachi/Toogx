/* Togg IVI toolkit — ortak yardımcılar (index.html + probe.html) */
window.ToggKit = (function () {
  'use strict';

  function verdict(ua) {
    ua = ua || navigator.userAgent || '';
    if (/;\s*wv\)/.test(ua)) {
      return { c:'bad', t:'PLAIN WEBVIEW',
        s:'intent:// · android-app:// · app-link ÇÖZÜLMEZ. Tarayıcı-native vektörler ölü → köprü / file erişimi ve fiziksel fazlara geç.' };
    }
    if (/Chrome\/|CriOS/.test(ua)) {
      return { c:'ok', t:'CHROME / CUSTOM TAB',
        s:'intent:// ve android-app:// çalışabilir → aşağıdaki testleri sırayla dene.' };
    }
    if (/WebView|Version\/\d+\.\d+/.test(ua)) {
      return { c:'try', t:'BELİRSİZ (olası WebView)',
        s:'UA net değil; belirleyici olan test sonuçlarıdır.' };
    }
    return { c:'try', t:'BELİRSİZ', s:'UA tanınmadı; test sonuçlarına bak.' };
  }

  function engineRisk(ua) {
    var m = /Chrome\/(\d+)\./.exec(ua || '');
    if (!m) return { v:null, cls:'try', txt:"Chromium sürümü UA'da yok (gizli WebView olabilir)" };
    var v = parseInt(m[1], 10);
    if (v < 90)  return { v:v, cls:'bad', txt:'ESKİ (Chrome/' + v + ') → WebView/V8 RCE zinciri araştır' };
    if (v < 110) return { v:v, cls:'try', txt:'ORTA (Chrome/' + v + ') → sürüme özel CVE olabilir' };
    return { v:v, cls:'ok', txt:'GÜNCEL (Chrome/' + v + ') → motor-CVE olasılığı düşük' };
  }

  /* Chrome yalnızca "intent://<host>/#Intent;...;end" biçimini çözer.
     Doğru extra tür öneki: S.=String, B.=Boolean, i.=Integer, l.=Long */
  function buildIntent(o, baseHref) {
    o = o || {};
    var base = (baseHref || location.href).split('#')[0];
    var fallback = base + '#nores=' + (o.id != null ? o.id : Date.now());
    var pkg = o.package || (o.component && o.component.indexOf('/') > 0 ? o.component.split('/')[0] : '');
    var p = [];
    if (o.action) p.push('action=' + o.action);
    if (pkg) p.push('package=' + pkg);
    if (o.component) p.push('component=' + o.component);
    if (o.scheme) p.push('scheme=' + o.scheme);
    if (o.flags) p.push('launchFlags=' + o.flags);
    if (o.type) p.push('type=' + o.type);
    if (o.category) p.push('category=' + o.category);
    if (o.data) p.push('data=' + o.data);
    if (o.extraKey && o.extraVal !== '' && o.extraVal != null) {
      p.push((o.extraType || 'S') + '.' + o.extraKey + '=' + o.extraVal);
    }
    p.push('S.browser_fallback_url=' + encodeURIComponent(fallback));
    return 'intent://' + (pkg || 'x') + '/#Intent;' + p.join(';') + ';end';
  }

  function hrefFor(it, baseHref) {
    if (it.kind === 'android-app') return 'android-app://' + it.package + '/';
    if (it.kind === 'url')    return it.url;
    if (it.kind === 'scheme') return it.schemeUrl;
    return buildIntent(it, baseHref);
  }

  function copy(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      try {
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.style.cssText = 'position:fixed;top:-1000px;opacity:0';
        document.body.appendChild(ta);
        ta.focus(); ta.select();
        var ok = document.execCommand('copy');
        ta.remove();
        ok ? resolve() : reject(new Error('execCommand copy failed'));
      } catch (e) { reject(e); }
    });
  }

  function $(id) { return document.getElementById(id); }

  return { verdict:verdict, engineRisk:engineRisk, buildIntent:buildIntent, hrefFor:hrefFor, copy:copy, $:$ };
})();

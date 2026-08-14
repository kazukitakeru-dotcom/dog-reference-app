#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""犬 ファクトチェック資料 — HTML版からPWA版を生成する。

正となるのは HTML 版。このスクリプトはそれを読み込んで、
PWA として成立させるための最小限の追記だけを行う。

  1. </head> の直前に manifest / アイコン / theme-color などを差し込む
  2. </body> の直前に Service Worker 登録と「戻る」対応スクリプトを差し込む
  3. sw.js を CACHE_VERSION 付きで書き出す
  4. アイコン元画像から icons/ 一式を作り直す

本文の中身には一切手を触れない。内容の修正は HTML 版で行うこと。

使い方:  python build_pwa.py
"""

import io
import os
import sys

# ---- 入力 ---------------------------------------------------------------

SRC_HTML = r"C:\Users\kazuk\iCloudDrive\犬_ファクトチェック資料.html"
ICON_SRC = r"C:\Users\kazuk\iCloudDrive\犬.png"

# ---- 出力先(GitHubリポジトリと、iPhoneに渡すためのiCloud側) --------------

OUT_DIRS = [
    os.path.dirname(os.path.abspath(__file__)),
    r"C:\Users\kazuk\iCloudDrive\dog-reference-app",
]

# 内容を更新したら必ず上げること。上げないと端末に古い版が残り続ける。
CACHE_VERSION = "dog-ref-v9"

# アイコンの地の色(元画像の背景に合わせている)
ICON_BG = (251, 241, 221)

# ---- </head> の直前に入れるもの -----------------------------------------

HEAD_EXTRA = """<meta name="theme-color" content="#c2673a">
<meta name="description" content="犬の俗説検証・犬種図鑑・しつけ・健康の資料">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="犬資料">
"""

# ---- </body> の直前に入れるもの -----------------------------------------

BODY_EXTRA = """<script>
// --- PWA: Service Worker 登録 ---
if('serviceWorker' in navigator){
  addEventListener('load',function(){navigator.serviceWorker.register('sw.js').catch(function(){})});
}
// --- 端末の「戻る」でひとつ前の画面に戻る ---
addEventListener('DOMContentLoaded',function(){
  var radios=[].slice.call(document.querySelectorAll('input[name=t]'));
  var suppress=false;
  function currentId(){for(var i=0;i<radios.length;i++)if(radios[i].checked)return radios[i].id.slice(2);return 'home'}
  history.replaceState({v:currentId()},'');
  radios.forEach(function(r){r.addEventListener('change',function(){
    if(suppress)return;
    history.pushState({v:r.id.slice(2)},'');
  })});
  addEventListener('popstate',function(e){
    var v=(e.state&&e.state.v)||'home';
    var el=document.getElementById('r-'+v);
    if(el){suppress=true;el.checked=true;el.dispatchEvent(new Event('change',{bubbles:true}));suppress=false;scrollTo(0,0);}
  });
});
</script>
"""

SW_JS = """// 犬 ファクトチェック資料 — Service Worker
// build_pwa.py が生成する。版数は CACHE_VERSION で管理しているので手で直さない。
const CACHE = '%(cache)s';
const ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// HTML はネット優先(更新を拾う)、それ以外はキャッシュ優先。
// オフライン時は常にキャッシュにフォールバックする。
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const isHTML = req.mode === 'navigate' ||
                 (req.headers.get('accept') || '').includes('text/html');
  if (isHTML) {
    e.respondWith(
      fetch(req)
        .then(res => {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req).then(r => r || caches.match('./index.html')))
    );
  } else {
    e.respondWith(caches.match(req).then(r => r || fetch(req)));
  }
});
"""


def build_html():
    """HTML版を読んで、PWA用の追記を入れた index.html の中身を返す。"""
    html = io.open(SRC_HTML, encoding="utf-8").read()

    for tag in ("</head>", "</body>"):
        if html.count(tag) != 1:
            sys.exit("想定外: %s が %d 個ある。HTML版の構造を確認すること。"
                     % (tag, html.count(tag)))

    # 二重に入らないよう、既に入っている場合は素通し
    if "manifest.webmanifest" in html:
        sys.exit("想定外: HTML版に既に manifest への参照がある。")

    html = html.replace("</head>", HEAD_EXTRA + "</head>", 1)
    html = html.replace("</body>", BODY_EXTRA + "</body>", 1)
    return html


def build_icons():
    """元画像から icons/ 一式を作る。周囲の黒い余白は地の色で埋めて正方形にする。

    余白の厚みは元画像によって違うので、外周からの距離では判定しない。
    1px の黒枠を足した上でその角から塗りつぶすことで、
    「画像の外周とつながっている黒」だけが対象になる。絵の中の黒は残る。
    """
    from PIL import Image, ImageDraw

    im = Image.open(ICON_SRC).convert("RGB")
    w, h = im.size

    padded = Image.new("RGB", (w + 2, h + 2), (0, 0, 0))
    padded.paste(im, (1, 1))
    ImageDraw.floodfill(padded, (0, 0), ICON_BG, thresh=60)
    base = padded.crop((1, 1, w + 1, h + 1)).resize((1024, 1024), Image.LANCZOS)

    # maskable は端が切られるので、中身を80%に縮めて安全領域をとる
    maskable = Image.new("RGB", (512, 512), ICON_BG)
    maskable.paste(base.resize((410, 410), Image.LANCZOS), (51, 51))


    return {
        "icon-512.png": base.resize((512, 512), Image.LANCZOS),
        "icon-192.png": base.resize((192, 192), Image.LANCZOS),
        "apple-touch-icon.png": base.resize((180, 180), Image.LANCZOS),
        "icon-maskable-512.png": maskable,
    }


def main():
    html = build_html()
    sw = SW_JS % {"cache": CACHE_VERSION}
    icons = build_icons()

    for d in OUT_DIRS:
        icon_dir = os.path.join(d, "icons")
        os.makedirs(icon_dir, exist_ok=True)
        io.open(os.path.join(d, "index.html"), "w", encoding="utf-8", newline="").write(html)
        io.open(os.path.join(d, "sw.js"), "w", encoding="utf-8", newline="").write(sw)
        for name, img in icons.items():
            img.save(os.path.join(icon_dir, name))
        print("生成: %s  (index.html %.2fMB, CACHE=%s)"
              % (d, len(html.encode("utf-8")) / 1024 / 1024, CACHE_VERSION))


if __name__ == "__main__":
    main()

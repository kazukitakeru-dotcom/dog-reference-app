# 犬 ファクトチェック資料(アプリ版)

犬の俗説検証・犬種図鑑・しつけ・問題行動・健康をまとめた資料の、
オフラインで使える擬似アプリ(PWA)版。

## 位置づけ

- **正となるのは HTML 版**(`犬_ファクトチェック資料.html`)。情報とUIの整理はそちらで行う。
- このアプリ版と Markdown 版は、HTML 版が完成した時点で追随させる**下流の成果物**。
- 生成は `build_pwa.py` が HTML 版を読み込んで行う。手でこの中を編集しない。

## 公開先

https://kazukitakeru-dotcom.github.io/dog-reference-app/

リポジトリ: `kazukitakeru-dotcom/dog-reference-app`(public)
GitHub Pages は Settings → Pages で `main` ブランチのルートを公開する設定。
`main` に push すれば自動で再デプロイされる(反映まで1〜2分)。

Service Worker は https でないと動かない。GitHub Pages は https なので問題ない
(ローカル確認時は `localhost` なら動く)。

## 更新するとき

1. HTML 版(`犬_ファクトチェック資料.html`)を更新する
2. `build_pwa.py` の `CACHE_VERSION` を上げる(`dog-ref-v3` → `dog-ref-v4`)
3. `python build_pwa.py` を実行する
4. `git commit` して `main` に push する

```bash
python build_pwa.py
```

`CACHE_VERSION` を上げ忘れると、一度アクセスした端末に古い版が残り続けて
更新が反映されない。`sw.js` は生成物なので手で直さない。

## 構成

| ファイル | 役割 |
|---|---|
| `build_pwa.py` | HTML版から `index.html`・`sw.js`・`icons/` を生成する。入力パスは冒頭の定数 |
| `index.html` | 本体(生成物)。画像も含めて1ファイルに埋め込み済み |
| `manifest.webmanifest` | アプリ名・アイコン・表示モード。ここだけは手で管理する |
| `sw.js` | オフライン用キャッシュ(生成物)。HTMLはネット優先、他はキャッシュ優先 |
| `icons/` | ホーム画面用アイコン(生成物)。元画像は `iCloudDrive\犬.png` |

`build_pwa.py` が HTML 版に足しているのは2箇所だけ。
`</head>` の直前に manifest・アイコン・theme-color などのメタ、
`</body>` の直前に Service Worker 登録と端末の「戻る」対応スクリプト。
本文には一切触らない。

## 既知の制約

- `index.html` が約5.5MBある(写真140枚を base64 で埋め込んでいるため)。
  初回読み込みは少し待つが、2回目以降はキャッシュから即座に開く。
  軽くするなら、画像を外部ファイルに分離する改修が必要。
- 写真は Wikimedia Commons のクリエイティブ・コモンズ/パブリックドメイン画像。
  各犬種ページに撮影者とライセンスを表示している。

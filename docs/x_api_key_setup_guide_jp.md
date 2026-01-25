# 初心者向け：X APIキー（4つの鍵）の取得手順完全ガイド

X（旧Twitter）へ自動投稿を行うための「4つの鍵」を入手する手順を解説します。
少し画面が複雑ですが、この手順通りに進めれば確実に取得できます。

**所要時間:** 約 10〜15分

---

## ステップ 1: X Developer Portal にアクセスする

1.  パソコンで X にログインした状態で、以下のURLを開きます。
    *   **Developer Portal**: [https://developer.twitter.com/en/portal/dashboard](https://developer.twitter.com/en/portal/dashboard)
2.  初めてアクセスする場合、登録画面が出ます。
    *   使用目的などを聞かれた場合、「**Making a bot**（ボットの作成）」などを選択し、目的欄には「Post news updates automatically（ニュースを自動投稿するため）」と入力して登録を完了させてください。
    *   ※「Free（無料）」プランで登録してください。

---

## ステップ 2: プロジェクトとアプリを作成する

1.  ダッシュボート（左メニュー）の **「Projects & Apps」** をクリックします。
2.  **「Default Project」** という項目があるはずです（なければ「Create Project」で作ります）。
3.  その中にあるアプリ（あなたの名前や数字の羅列になっているもの）をクリックします。
    *   まだアプリがない場合は **「Add App」** を押して、「NewsBot」など好きな名前を付けて作成してください。

---

## ステップ 3: 【重要】書き込み権限（Write）を設定する

**ここが一番のつまずきポイントです！** デフォルトでは「読むだけ」の設定になっているため、これを「投稿できる」設定に変える必要があります。

1.  アプリの管理画面の下の方にある **「User authentication settings」** の **「Set up」**（または「Edit」）ボタンを押します。
2.  以下の通りに設定します：
    *   **App permissions**: **「Read and Write」** を選択（ここが重要！）
    *   **Type of App**: **「Web App, Automated App or Bot」** を選択
    *   **App info**:
        *   **Callback URI / Redirect URL**: `https://localhost` と入力（実際には使いませんが必須入力です）
        *   **Website URL**: `https://localhost` と入力（同上）
3.  **「Save」** を押して保存します。

---

## ステップ 4: 4つの鍵を生成する

権限設定ができたら、いよいよ鍵を発行します。アプリ設定画面の上部にある **「Keys and tokens」** タブをクリックしてください。

### 1 & 2. Consumer Keys (API Key and Secret)
*   **「Consumer Keys」** という項目の横にある **「Regenerate」**（または「Generate」）ボタンを押します。
*   画面に **API Key** と **API Key Secret** が表示されます。
*   **重要:** この画面は一度しか表示されません！必ずメモ帳などにコピーして保存してください。
    *   これが **1つ目と2つ目の鍵** です。

### 3 & 4. Authentication Tokens (Access Token and Secret)
*   同じ画面の下の方にある **「Authentication Tokens」** の **「Access Token and Secret」** という項目を探します。
*   **「Generate」**（すでに作成済みの場合は「Regenerate」）ボタンを押します。
*   画面に **Access Token** と **Access Token Secret** が表示されます。
*   これも必ずコピーして保存してください。
    *   これが **3つ目と4つ目の鍵** です。

---

## 最終チェック

手元に以下の4つの文字列が揃いましたか？

1.  `API Key` (Consumer Key)
2.  `API Key Secret` (Consumer Secret)
3.  `Access Token`
4.  `Access Token Secret`

これらを、GitHub の **Settings > Secrets and variables > Actions** に登録すれば完了です！

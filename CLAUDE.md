# demo：投稿審查系統（期中個人專題）

以 `../DB-Basic Example` 為基礎（沿用 `db.py`、單一 `main.py` 寫法、`sessionLogin.py` 的登入方式）。需求來源：`~/Downloads/1151 期中個人專題.pptx`。

## 啟動
```bash
uv run --with "fastapi[standard]" --with "psycopg[binary]" --with psycopg_pool --with itsdangerous fastapi dev main.py
```
- 網址：http://127.0.0.1:8000/
- DB：本機 PostgreSQL 17 的 `mydb`，`papers` 表由 `schema.sql` 建立（重跑會清空資料並重建）

## 設計決定（已與使用者確認）
- 帳號寫死在 `main.py` 的 `USERS`，登入頁會顯示：作者 `author/author123`、編輯 `editor/editor123`
- 類別用下拉選單，選項在 `CATEGORIES`（資訊、管理、教育、其他）
- 所有路由寫在 `main.py`（不用 router）
- 狀態：編輯中 → 審查中（作者送出）→ 已通過（編輯通過）／編輯中（編輯退回）
- 作者只能編輯、刪除、送出自己「編輯中」的稿件；編輯只能處理「審查中」的稿件（SQL 的 WHERE 條件裡也有檢查）

- 畫面：卡片式清爽風（上方導覽列、稿件卡片、作者頁可依狀態篩選），樣式集中在 `templates/base.html` 的 `:root`
- 看資料庫：Adminer，`~/三上/軟工/phpweb` 執行 `php -S localhost:9000 -t www`，網址 http://localhost:9000/adminer/adminer.php?pgsql=&username=postgres

## 待辦
- git init 和 commit：使用者說下次再做

-- 投稿審查系統：稿件表（匯入 mydb）
-- 帳號為 demo 用，寫死在 main.py，不建 users 表
DROP TABLE IF EXISTS papers;

CREATE TABLE papers (
	id       SERIAL PRIMARY KEY,
	author   VARCHAR(50)  NOT NULL,                 -- 作者帳號
	category VARCHAR(20)  NOT NULL,                 -- 類別（下拉選單）
	title    VARCHAR(200) NOT NULL,
	content  TEXT         NOT NULL,
	status   VARCHAR(10)  NOT NULL DEFAULT '編輯中'
		CHECK (status IN ('編輯中', '審查中', '已通過'))
);

-- 測試資料
INSERT INTO papers (author, category, title, content, status) VALUES
	('author', '資訊', 'FastAPI 入門心得', '這是一篇編輯中的稿件。', '編輯中'),
	('author', '管理', '專案管理的時程規劃', '這是一篇審查中的稿件。', '審查中'),
	('author', '教育', '翻轉教室實施成效', '這是一篇已通過的稿件。', '已通過');

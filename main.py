# main.py：投稿審查系統
from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from db import getDB, lifespan

templates = Jinja2Templates(directory="templates")
app = FastAPI(lifespan=lifespan)

app.add_middleware(
	SessionMiddleware,
	secret_key="demo-secret-key",
	max_age=None,
	same_site="lax",
	https_only=False,
)

# demo 用帳號（寫死，登入頁會顯示）
USERS = {
	"author": {"password": "author123", "role": "author", "label": "作者"},
	"editor": {"password": "editor123", "role": "editor", "label": "編輯"},
}
CATEGORIES = ["資訊", "管理", "教育", "其他"]


# 登入檢查：未登入或角色不符回傳 None
def chkLogin(role: str | None = None):
	def checker(request: Request):
		user = request.session.get("user")
		if user and (role is None or user["role"] == role):
			return user
		return None
	return checker


def toLogin():
	return RedirectResponse(url="/login", status_code=302)


# ===== 登入 / 登出 =====
@app.get("/")
async def home(user=Depends(chkLogin())):
	if user is None:
		return toLogin()
	if user["role"] == "author":
		return RedirectResponse(url="/author/papers", status_code=302)
	return RedirectResponse(url="/editor/papers", status_code=302)


@app.get("/login")
async def loginPage(request: Request):
	return templates.TemplateResponse(name="login.html", request=request, context={"users": USERS})


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
	u = USERS.get(username)
	if u and u["password"] == password:
		request.session["user"] = {"username": username, "role": u["role"], "label": u["label"]}
		return RedirectResponse(url="/", status_code=303)
	return templates.TemplateResponse(name="login.html", request=request,
		context={"users": USERS, "error": "帳號或密碼錯誤", "username": username})


@app.get("/logout")
async def logout(request: Request):
	request.session.clear()
	return toLogin()


# ===== 作者功能 =====
@app.get("/author/papers")
async def authorList(request: Request, user=Depends(chkLogin("author")), db=Depends(getDB)):
	if user is None:
		return toLogin()
	cur = await db.execute("SELECT * FROM papers WHERE author=%s ORDER BY id;", (user["username"],))
	data = await cur.fetchall()
	return templates.TemplateResponse(name="authorList.html", request=request,
		context={"user": user, "papers": data})


@app.get("/author/paper/add")
async def paperAdd(request: Request, user=Depends(chkLogin("author"))):
	if user is None:
		return toLogin()
	return templates.TemplateResponse(name="paperForm.html", request=request,
		context={"user": user, "categories": CATEGORIES, "paper": {}})


@app.post("/author/paper/insert")
async def paperInsert(request: Request, category: str = Form(...), title: str = Form(...),
		content: str = Form(...), user=Depends(chkLogin("author")), db=Depends(getDB)):
	if user is None:
		return toLogin()
	if category not in CATEGORIES:
		return templates.TemplateResponse(name="paperForm.html", request=request,
			context={"user": user, "categories": CATEGORIES, "error": "類別不正確",
				"paper": {"category": category, "title": title, "content": content}})
	await db.execute("INSERT INTO papers (author, category, title, content, status) VALUES (%s, %s, %s, %s, '編輯中');",
		(user["username"], category, title, content))
	return RedirectResponse(url="/author/papers", status_code=303)


@app.get("/author/paper/edit/{id}")
async def paperEdit(id: int, request: Request, user=Depends(chkLogin("author")), db=Depends(getDB)):
	if user is None:
		return toLogin()
	cur = await db.execute("SELECT * FROM papers WHERE id=%s AND author=%s AND status='編輯中';",
		(id, user["username"]))
	data = await cur.fetchone()
	if data is None:  # 不存在、不是自己的、或已送出 → 不能編輯
		return RedirectResponse(url="/author/papers", status_code=303)
	return templates.TemplateResponse(name="paperForm.html", request=request,
		context={"user": user, "categories": CATEGORIES, "paper": data})


@app.post("/author/paper/update")
async def paperUpdate(request: Request, id: int = Form(...), category: str = Form(...), title: str = Form(...),
		content: str = Form(...), user=Depends(chkLogin("author")), db=Depends(getDB)):
	if user is None:
		return toLogin()
	if category not in CATEGORIES:
		return templates.TemplateResponse(name="paperForm.html", request=request,
			context={"user": user, "categories": CATEGORIES, "error": "類別不正確",
				"paper": {"id": id, "category": category, "title": title, "content": content}})
	await db.execute("UPDATE papers SET category=%s, title=%s, content=%s WHERE id=%s AND author=%s AND status='編輯中';",
		(category, title, content, id, user["username"]))
	return RedirectResponse(url="/author/papers", status_code=303)


@app.get("/author/paper/delete/{id}")
async def paperDelete(id: int, user=Depends(chkLogin("author")), db=Depends(getDB)):
	if user is None:
		return toLogin()
	await db.execute("DELETE FROM papers WHERE id=%s AND author=%s AND status='編輯中';", (id, user["username"]))
	return RedirectResponse(url="/author/papers", status_code=303)


@app.get("/author/paper/submit/{id}")
async def paperSubmit(id: int, user=Depends(chkLogin("author")), db=Depends(getDB)):
	if user is None:
		return toLogin()
	await db.execute("UPDATE papers SET status='審查中' WHERE id=%s AND author=%s AND status='編輯中';",
		(id, user["username"]))
	return RedirectResponse(url="/author/papers", status_code=303)


# ===== 編輯功能 =====
@app.get("/editor/papers")
async def editorList(request: Request, user=Depends(chkLogin("editor")), db=Depends(getDB)):
	if user is None:
		return toLogin()
	cur = await db.execute("SELECT * FROM papers WHERE status='審查中' ORDER BY id;")
	data = await cur.fetchall()
	return templates.TemplateResponse(name="editorList.html", request=request,
		context={"user": user, "papers": data})


@app.get("/editor/paper/{id}")
async def paperView(id: int, request: Request, user=Depends(chkLogin("editor")), db=Depends(getDB)):
	if user is None:
		return toLogin()
	cur = await db.execute("SELECT * FROM papers WHERE id=%s AND status='審查中';", (id,))
	data = await cur.fetchone()
	if data is None:
		return RedirectResponse(url="/editor/papers", status_code=303)
	return templates.TemplateResponse(name="paperView.html", request=request,
		context={"user": user, "paper": data})


@app.get("/editor/paper/approve/{id}")
async def paperApprove(id: int, user=Depends(chkLogin("editor")), db=Depends(getDB)):
	if user is None:
		return toLogin()
	await db.execute("UPDATE papers SET status='已通過' WHERE id=%s AND status='審查中';", (id,))
	return RedirectResponse(url="/editor/papers", status_code=303)


@app.get("/editor/paper/reject/{id}")
async def paperReject(id: int, user=Depends(chkLogin("editor")), db=Depends(getDB)):
	if user is None:
		return toLogin()
	await db.execute("UPDATE papers SET status='編輯中' WHERE id=%s AND status='審查中';", (id,))
	return RedirectResponse(url="/editor/papers", status_code=303)

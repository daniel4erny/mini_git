import fastapi
import hmac
import os
from fastapi.responses import JSONResponse
import git
import web

SITE_PASSWORD = os.environ.get("SITE_PASSWORD")
if not SITE_PASSWORD:
	raise RuntimeError("SITE_PASSWORD is not set, BROTHA")

app = fastapi.FastAPI()
app.include_router(git.router)
app.include_router(web.router)

# heslo pro celý server (web i git), posílá se v hlavičce X-Password
# git: git clone -c http.extraHeader="X-Password: <heslo>" <url>
@app.middleware("http")
async def check_site_password(request: fastapi.Request, call_next):
	password = request.headers.get("x-password", "")
	if not hmac.compare_digest(password.encode(), SITE_PASSWORD.encode()):
		return JSONResponse(status_code=403, content={"detail": "BROTHA WRONG PASSWORD"})
	return await call_next(request)

@app.get("/test")
async def root():
	return {"message": "Welcome to mini_git API!"}

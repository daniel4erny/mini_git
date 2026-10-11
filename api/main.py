import fastapi
import git
import web

app = fastapi.FastAPI()
app.include_router(git.router)
app.include_router(web.router)

@app.get("/test")
async def root():
	return {"message": "Welcome to mini_git API!"}

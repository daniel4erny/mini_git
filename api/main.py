import fastapi
import git
import web

app = fastapi.FastAPI()
app.include_router(git.router)
app.include_router(web.router)

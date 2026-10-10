import fastapi
import git

app = fastapi.FastAPI()
app.include_router(git.router)

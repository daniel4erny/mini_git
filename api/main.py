import fastapi
import subprocess
import os
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from db import Database

db = Database("database.db")
app = fastapi.FastAPI()
GIT_ROOT = os.path.expanduser("~/git-server-repos")
os.makedirs(GIT_ROOT, exist_ok=True)

def get_repo_path(repo_name: str) -> str:
    path = os.path.join(GIT_ROOT, repo_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Repozitář nenalezen")
    return path



@app.get("/repos/{repo_name}.git/info/refs")
def get_info_refs(repo_name: str, service: str):
	if service not in {"git-upload-pack", "git-receive-pack"}:
		return fastapi.responses.Response(status_code=400, content="Unsupported service")
	repo_path = get_repo_path(repo_name)
	cmd = [service, "--stateless-rpc", "--advertise-refs", repo_path]
	try:
		process = subprocess.Popen(cmd, cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = process.communicate()
		if process.returncode != 0:
			raise HTTPException(status_code=500, detail=f"Git command failed: {stderr.decode()}")
		media_type = f"application/x-{service}-advertisement"
		return fastapi.responses.Response(content=stdout, media_type=media_type)
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/repos/{repo_name}.git/git-upload-pack")
async def git_clone_pull(repo_name: str, request: fastapi.Request):
    repo_path = get_repo_path(repo_name)
    body = await request.body()

    cmd = ["git-upload-pack", "--stateless-rpc", repo_path]
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout, stderr = process.communicate(input=body)
    if process.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Git command failed: {stderr.decode()}")
    return fastapi.responses.Response(content=stdout, media_type="application/x-git-upload-pack-result")


@app.post("/repos/{repo_name}.git/git-receive-pack")
async def git_push(repo_name: str, request: fastapi.Request):
    repo_path = get_repo_path(repo_name)
    body = await request.body()

    cmd = ["git-receive-pack", "--stateless-rpc", repo_path]
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout, stderr = process.communicate(input=body)
    if process.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Git command failed: {stderr.decode()}")
    return fastapi.responses.Response(content=stdout, media_type="application/x-git-receive-pack-result")

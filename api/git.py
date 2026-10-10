import fastapi
import asyncio
import subprocess
import os
import gzip
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Depends
from auth import get_user_role

router = APIRouter(prefix="/repos", dependencies=[Depends(get_user_role)])
GIT_ROOT = os.environ.get("GIT_ROOT", os.path.expanduser("~/git-server-repos"))
os.makedirs(GIT_ROOT, exist_ok=True)

def pkt_line(data: str) -> bytes:
	return f"{len(data) + 4:04x}{data}".encode()

async def read_body(request: fastapi.Request) -> bytes:
	body = await request.body()
	if request.headers.get("content-encoding") == "gzip":
		body = gzip.decompress(body)
	return body

def get_repo_path(repo_name: str) -> str:
    path = os.path.realpath(os.path.join(GIT_ROOT, repo_name))
    if os.path.dirname(path) != os.path.realpath(GIT_ROOT):
        raise HTTPException(status_code=400, detail="BROTHA DONT TRY ME")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Repozitář nenalezen")
    return path


@router.get("/{repo_name}.git/info/refs")
def get_info_refs(repo_name: str, service: str):
	if service not in {"git-upload-pack", "git-receive-pack"}:
		return fastapi.responses.Response(status_code=400, content="BROTHA DONT TRY ME")
	repo_path = get_repo_path(repo_name)
	cmd = [service, "--stateless-rpc", "--advertise-refs", repo_path]
	try:
		process = subprocess.Popen(cmd, cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = process.communicate()
		if process.returncode != 0:
			raise HTTPException(status_code=500, detail=f"Git command failed: {stderr.decode()}")
		media_type = f"application/x-{service}-advertisement"
		content = pkt_line(f"# service={service}\n") + b"0000" + stdout
		return fastapi.responses.Response(content=content, media_type=media_type)
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.post("/{repo_name}.git/git-upload-pack")
async def git_clone_pull(repo_name: str, request: fastapi.Request):
    repo_path = get_repo_path(repo_name)
    body = await read_body(request)

    cmd = ["git-upload-pack", "--stateless-rpc", repo_path]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout, stderr = await process.communicate(input=body)
    if process.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Git command failed: {stderr.decode()}")
    return fastapi.responses.Response(content=stdout, media_type="application/x-git-upload-pack-result")

@router.post("/{repo_name}.git/git-receive-pack")
async def git_push(repo_name: str, request: fastapi.Request):
    repo_path = get_repo_path(repo_name)
    body = await read_body(request)

    cmd = ["git-receive-pack", "--stateless-rpc", repo_path]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout, stderr = await process.communicate(input=body)
    if process.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Git command failed: {stderr.decode()}")
    return fastapi.responses.Response(content=stdout, media_type="application/x-git-receive-pack-result")

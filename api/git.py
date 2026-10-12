import fastapi
import asyncio
import subprocess
import os
import zlib
from fastapi.responses import StreamingResponse
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Depends
from fastapi.security import HTTPBasicCredentials
from auth import get_user_role
from auth import db, security

router = APIRouter(prefix="/repos", dependencies=[Depends(get_user_role)])
GIT_ROOT = os.environ.get("GIT_ROOT", os.path.expanduser("~/git-server-repos"))
os.makedirs(GIT_ROOT, exist_ok=True)

def pkt_line(data: str) -> bytes:
	return f"{len(data) + 4:04x}{data}".encode()

def get_repo_path(repo_name: str) -> str:
	path = os.path.realpath(os.path.join(GIT_ROOT, repo_name))
	if os.path.dirname(path) != os.path.realpath(GIT_ROOT):
		raise HTTPException(status_code=400, detail="BROTHA DONT TRY ME")
	if not os.path.exists(path):
		raise HTTPException(status_code=404, detail="Repozitář nenalezen")
	return path

async def stream_git(cmd: list[str], request: fastapi.Request, media_type: str):
	process = await asyncio.create_subprocess_exec(
		*cmd,
		stdin=subprocess.PIPE,
		stdout=subprocess.PIPE,
		stderr=subprocess.DEVNULL
	)
	assert process.stdin and process.stdout
	stdin, stdout = process.stdin, process.stdout

	decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS) if request.headers.get("content-encoding") == "gzip" else None
	try:
		async for chunk in request.stream():
			if decompressor:
				chunk = decompressor.decompress(chunk)
			stdin.write(chunk)
			await stdin.drain()
		if decompressor:
			stdin.write(decompressor.flush())
		stdin.close()
	except BaseException:
		process.kill()
		raise

	async def generator():
		try:
			while chunk := await stdout.read(65536):
				yield chunk
			await process.wait()
		finally:
			if process.returncode is None:
				process.kill()
				await process.wait()

	return StreamingResponse(generator(), media_type=media_type)


@router.get("/{repo_name}.git/info/refs")
async def get_info_refs(repo_name: str, service: str):
	if service not in {"git-upload-pack", "git-receive-pack"}:
		return fastapi.responses.Response(status_code=400, content="BROTHA DONT TRY ME")
	repo_path = get_repo_path(repo_name)
	cmd = [service, "--stateless-rpc", "--advertise-refs", repo_path]
	try:
		process = await asyncio.create_subprocess_exec(
			*cmd,
			cwd=repo_path,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE
		)
		stdout, stderr = await process.communicate()
		if process.returncode != 0:
			raise HTTPException(status_code=500, detail=f"Git command failed: {stderr.decode()}")
		media_type = f"application/x-{service}-advertisement"
		content = pkt_line(f"# service={service}\n") + b"0000" + stdout
		return fastapi.responses.Response(content=content, media_type=media_type)
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.post("/{repo_name}.git/git-upload-pack")
async def git_clone_pull(repo_name: str, request: fastapi.Request):
	#here we dont make sure the user is the owner of the repo
	repo_path = get_repo_path(repo_name)
	cmd = ["git-upload-pack", "--stateless-rpc", repo_path]
	return await stream_git(cmd, request, "application/x-git-upload-pack-result")

@router.post("/{repo_name}.git/git-receive-pack")
async def git_push(repo_name: str, request: fastapi.Request, user: dict = Depends(get_user_role)):
	#here we dont make sure the user (TODO - COLLABORATORS) is the owner of the repo
	if not db.check_ownership(repo_name, user["username"]):
		raise HTTPException(status_code=403, detail="BROTHA DONT TRY ME")

	repo_path = get_repo_path(repo_name)
	cmd = ["git-receive-pack", "--stateless-rpc", repo_path]
	return await stream_git(cmd, request, "application/x-git-receive-pack-result")

@router.post("/{repo_name}.git/create")
async def create_repo(repo_name: str, request: fastapi.Request):
	if repo_name in ("repos", "api"):
		raise HTTPException(status_code=400, detail="Invalid repo name. BROTHA DONT TRY ME")
	credentials= await security(request)
	if not credentials:
		raise HTTPException(status_code=401, detail="BROTHA DONT TRY ME", headers={"WWW-Authenticate": 'Basic realm="mini_git"'})

	user: dict = await get_user_role(credentials)
	if user["role"] not in ["admin", "root"]:
		raise HTTPException(status_code=403, detail="BROTHA DONT TRY ME")

	repo_path = os.path.join(GIT_ROOT, repo_name)
	if os.path.exists(repo_path):
		raise HTTPException(status_code=400, detail="GG BROTHA, REPO ALREADY EXISTS")

	try:
		os.makedirs(repo_path)
		subprocess.run(["git", "init", "--bare"], cwd=repo_path, check=True)
		owner_id = db.get_user(user["username"])[0]
		db.create_repo(repo_name, repo_path, owner_id)
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

	return {"message": f"REPO '{repo_name}' created successfully", "path": repo_path, "owner": user["username"]}

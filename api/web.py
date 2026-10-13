from fastapi import APIRouter, HTTPException
from fastapi import Depends
from pydantic import BaseModel
from auth import db
from auth import get_user_role
import asyncio
import subprocess
from git import get_repo_path

router = APIRouter(prefix="/web", dependencies=[Depends(get_user_role)])

class NewUser(BaseModel):
	username: str
	password: str
	role: str = "user"

class UserUpdate(BaseModel):
	password: str | None = None
	role: str | None = None

@router.get("/")
async def dashboard(user: dict = Depends(get_user_role)):
	role = user["role"]
	if role == "root" or role == "admin":
		repos = db.list_repos()
		users = db.list_users()
	else:
		raise HTTPException(status_code=403, detail="Access denied")
	return {"repos": repos, "users": users}

@router.post("/users")
async def add_user(new_user: NewUser, user: dict = Depends(get_user_role)):
	role = user["role"]
	if role == "root" or role == "admin":
		db.add_user(new_user.username, new_user.password, new_user.role)
	else:
		raise HTTPException(status_code=403, detail="Access denied")
	return {"message": f"USER '{new_user.username}' created successfully"}

@router.patch("/users/{username}")
async def update_user(username: str, update: UserUpdate, user: dict = Depends(get_user_role)):
	role = user["role"]
	if role == "root" or role == "admin":
		db.update_user(username, update.password, update.role)
	else:
		raise HTTPException(status_code=403, detail="Access denied")
	return {"message": f"USER '{username}' updated successfully"}

@router.delete("/users/{username}")
async def delete_user(username: str, user: dict = Depends(get_user_role)):
	role = user["role"]
	if role == "root" or role == "admin":
		db.delete_user(username)
	else:
		raise HTTPException(status_code=403, detail="Access denied")
	return {"message": f"USER '{username}' deleted successfully"}

async def ls_tree(repo_path: str, ref: str = "HEAD", path: str = "") -> list[dict]:
	target = f"{ref}:{path}" if path else ref
	process = await asyncio.create_subprocess_exec(
		"git", "-C", repo_path, "ls-tree", "-z", "-l", target,
		stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
	)
	stdout, _ = await process.communicate()
	if process.returncode != 0:
		return []
	entries = []
	for record in stdout.decode().split("\0"):
		if not record:
			continue
		meta, name = record.split("\t", 1)
		mode, type_, sha, size = meta.split()
		entries.append({"name": name, "type": type_, "size": None if size == "-" else int(size)})
	entries.sort(key=lambda e: (e["type"] != "tree", e["name"].lower()))
	return entries

async def git_show(repo_path: str, ref: str = "HEAD", path: str = "") -> bytes | None:
	process = await asyncio.create_subprocess_exec(
		"git", "-C", repo_path, "cat-file", "blob", f"{ref}:{path}",
		stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
	)
	stdout, _ = await process.communicate()
	if process.returncode != 0:
		return None
	return stdout

@router.get("/{repo_name}/")
async def get_repo(repo_name: str, user: dict = Depends(get_user_role)):
	return await get_tree(repo_name, "", user)

@router.get("/{repo_name}/tree/{path:path}")
async def get_tree(repo_name: str, path: str, user: dict = Depends(get_user_role)):
	role = user["role"]
	username = user["username"]
	if role == "root" or role == "admin":
		repo_path = get_repo_path(repo_name)
		entries = await ls_tree(repo_path, path=path)
	else:
		raise HTTPException(status_code=403, detail="Access denied")
	return {"repo": repo_name, "path": path, "entries": entries}

@router.get("/{repo_name}/blob/{path:path}")
async def get_blob(repo_name: str, path: str, user: dict = Depends(get_user_role)):
	role = user["role"]
	username = user["username"]
	if role == "root" or role == "admin":
		repo_path = get_repo_path(repo_name)
		content = await git_show(repo_path, path=path)
	else:
		raise HTTPException(status_code=403, detail="Access denied")
	if content is None:
		raise HTTPException(status_code=404, detail="Soubor nenalezen")
	if b"\0" in content:
		return {"repo": repo_name, "path": path, "binary": True, "content": None}
	return {"repo": repo_name, "path": path, "binary": False, "content": content.decode(errors="replace")}

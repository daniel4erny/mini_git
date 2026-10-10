import os
from fastapi import HTTPException
from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from db import Database

db = Database(os.environ.get("DB_PATH", "database.db"))
security = HTTPBasic(realm="mini_git")

async def get_user_role(credentials: HTTPBasicCredentials = Depends(security)) -> str:
	role = db.get_user_role(credentials.username, credentials.password)
	if role is None:
		raise HTTPException(status_code=401, detail="BROTHA DONT TRY ME", headers={"WWW-Authenticate": 'Basic realm="mini_git"'})
	return role

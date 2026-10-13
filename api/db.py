import sqlite3
from fastapi import HTTPException

class Database:
	def __init__(self, db_name):
		self.conn = sqlite3.connect(db_name, check_same_thread=False)
		self.cursor = self.conn.cursor()
		self.__create_tables()
		self.__create_root_user()

	def __create_tables(self):
		self.cursor.executescript('''
			CREATE TABLE IF NOT EXISTS users (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				username TEXT NOT NULL UNIQUE,
				password TEXT NOT NULL,
				role TEXT NOT NULL
			);
			CREATE TABLE IF NOT EXISTS repos (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL UNIQUE,
				path TEXT NOT NULL,
				owner INTEGER NOT NULL,
				FOREIGN KEY (owner) REFERENCES users(id)
			)
		''')
		self.conn.commit()

	def create_repo(self, name, path, owner):
		if name in ("repos", "api"):
			raise HTTPException(status_code=400, detail="Invalid repo name.")

		try:
			self.cursor.execute('INSERT INTO repos (name, path, owner) VALUES (?, ?, ?)', (name, path, owner))
			self.conn.commit()
			return True
		except sqlite3.IntegrityError:
			raise HTTPException(status_code=400, detail="GG BROTHA, REPO ALREADY EXISTS")

	def check_ownership(self, repo_name, username):
		self.cursor.execute('''
			SELECT u.username FROM users u
			JOIN repos r ON u.id = r.owner
			WHERE r.name = ?
		''', (repo_name,))
		result = self.cursor.fetchone()
		if result and result[0] == username:
			return True
		return False

	def list_repos(self):
		self.cursor.execute('''
			SELECT r.name, u.username FROM repos r
			LEFT JOIN users u ON u.id = r.owner
			ORDER BY r.name
		''')
		return [{"name": name, "owner": owner} for name, owner in self.cursor.fetchall()]

	def __create_root_user(self):
		self.cursor.execute('INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)', ("daniel", "nesnasimgulyho#67", "root"))
		self.conn.commit()

	def add_user(self, username, password, role):
		if not username or not password:
			raise HTTPException(status_code=400, detail="Username and password can't be empty.")
		if role not in ["admin", "user"]:
			raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin' or 'user'.")
		try:
			self.cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, password, role))
			self.conn.commit()
			return True
		except sqlite3.IntegrityError:
			raise HTTPException(status_code=400, detail="GG BROTHA, USER ALREADY EXISTS")

	def get_user(self, username):
		self.cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
		return self.cursor.fetchone()

	def get_user_role(self, username, password):
		try:
			self.cursor.execute('SELECT role FROM users WHERE username = ? AND password = ?', (username, password))
			result = self.cursor.fetchone()
			if result:
				return result[0]
			else:
				return None
		except sqlite3.Error as e:
			raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

	def list_users(self):
		self.cursor.execute('''
			SELECT u.username, u.role, COUNT(r.id) FROM users u
			LEFT JOIN repos r ON r.owner = u.id
			GROUP BY u.id
			ORDER BY u.id
		''')
		return [{"username": username, "role": role, "repos": repos} for username, role, repos in self.cursor.fetchall()]

	def __get_editable_user(self, username):
		user = self.get_user(username)
		if user is None:
			raise HTTPException(status_code=404, detail="Uživatel nenalezen")
		if user[3] == "root":
			raise HTTPException(status_code=403, detail="BROTHA DONT TRY ME")
		return user

	def update_user(self, username, password=None, role=None):
		user = self.__get_editable_user(username)
		if role is not None and role not in ["admin", "user"]:
			raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin' or 'user'.")
		if password is not None and not password:
			raise HTTPException(status_code=400, detail="Password can't be empty.")
		if password is not None:
			self.cursor.execute('UPDATE users SET password = ? WHERE id = ?', (password, user[0]))
		if role is not None:
			self.cursor.execute('UPDATE users SET role = ? WHERE id = ?', (role, user[0]))
		self.conn.commit()
		return True

	def delete_user(self, username):
		user = self.__get_editable_user(username)
		self.cursor.execute('SELECT COUNT(*) FROM repos WHERE owner = ?', (user[0],))
		if self.cursor.fetchone()[0] > 0:
			raise HTTPException(status_code=400, detail="GG BROTHA, USER STILL OWNS REPOS")
		self.cursor.execute('DELETE FROM users WHERE id = ?', (user[0],))
		self.conn.commit()
		return True

	def close(self):
		self.conn.close()

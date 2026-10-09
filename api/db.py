import sqlite3
from fastapi import HTTPException

class Database:
	def __init__(self, db_name):
		self.conn = sqlite3.connect(db_name)
		self.cursor = self.conn.cursor()
		self.__create_tables()
		self.__create_root_user()

	def __create_tables(self):
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS users (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				username TEXT NOT NULL UNIQUE,
				password TEXT NOT NULL,
				role TEXT NOT NULL
			)
		''')
		self.conn.commit()

	def __create_root_user(self):
		try:
			self.cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', ("daniel", "nesnasimgulyho#67", "root"))
			self.conn.commit()
			return True
		except sqlite3.IntegrityError:
			return False

	def add_user(self, username, password, role):
		if role not in ["admin", "user"]:
			raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin' or 'user'.")
		try:
			self.cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, password, role))
			self.conn.commit()
			return True
		except sqlite3.IntegrityError:
			return False

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


	def close(self):
		self.conn.close()

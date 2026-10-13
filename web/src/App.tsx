import { useEffect } from "react"
import { useState } from "react"
import { Link } from "react-router"
import { api, json, enc } from "./api"

type Repo = {
	name : string
	owner : string | null
}

type User = {
	username : string
	role : string
	repos : number
}

type Data = {
	repos : Repo[]
	users : User[]
}

function App() {
	const [data, setData] = useState<Data | null>(null)
	const [error, setError] = useState<string | null>(null)
	const [repoName, setRepoName] = useState("")
	const [username, setUsername] = useState("")
	const [password, setPassword] = useState("")
	const [role, setRole] = useState("user")

	// provede akci, pak znovu načte dashboard
	const run = async (action : () => Promise<unknown>) => {
		setError(null)
		try {
			await action()
			setData(await api<Data>("/api/web/"))
		} catch (e) {
			setError((e as Error).message)
		}
	}

	useEffect(() => {
		run(async () => {})
	}, [])

	const createRepo = (e : React.FormEvent) => {
		e.preventDefault()
		run(async () => {
			await api(`/repos/${encodeURIComponent(repoName)}.git/create`, { method: "POST" })
			setRepoName("")
		})
	}

	const addUser = (e : React.FormEvent) => {
		e.preventDefault()
		run(async () => {
			await api("/api/web/users", json("POST", { username, password, role }))
			setUsername("")
			setPassword("")
		})
	}

	const changeRole = (user : string, role : string) => {
		run(() => api(`/api/web/users/${encodeURIComponent(user)}`, json("PATCH", { role })))
	}

	const changePassword = (user : string) => {
		const password = prompt(`nové heslo pro ${user}`)
		if (password) {
			run(() => api(`/api/web/users/${encodeURIComponent(user)}`, json("PATCH", { password })))
		}
	}

	const deleteUser = (user : string) => {
		if (confirm(`smazat ${user}?`)) {
			run(() => api(`/api/web/users/${encodeURIComponent(user)}`, { method: "DELETE" }))
		}
	}

	return (
		<>
		<h1>mini_git</h1>
		{error && <p className="error">{error}</p>}
		{!data && !error && <p>loading...</p>}
		{data && (
			<>
			<h2>repa</h2>
			<table>
				<tbody>
					{data.repos.map(repo => (
						<tr key={repo.name}>
							<td><Link to={`/${enc(repo.name)}`}>{repo.name}</Link></td>
							<td>{repo.owner}</td>
						</tr>
					))}
				</tbody>
			</table>
			<form onSubmit={createRepo}>
				<input value={repoName} onChange={e => setRepoName(e.target.value)} placeholder="nové repo" pattern="[A-Za-z0-9_\-][A-Za-z0-9._\-]*" title="jen a-z 0-9 . _ -" required />
				<button>vytvořit</button>
			</form>

			<h2>uživatelé</h2>
			<table>
				<tbody>
					{data.users.map(user => (
						<tr key={user.username}>
							<td>{user.username}</td>
							<td>
								{user.role === "root" ? "root" : (
									<select value={user.role} onChange={e => changeRole(user.username, e.target.value)}>
										<option>user</option>
										<option>admin</option>
									</select>
								)}
							</td>
							<td>{user.repos} rep</td>
							<td>
								{user.role !== "root" && (
									<>
									<button onClick={() => changePassword(user.username)}>heslo</button>
									<button onClick={() => deleteUser(user.username)}>smazat</button>
									</>
								)}
							</td>
						</tr>
					))}
				</tbody>
			</table>
			<form onSubmit={addUser}>
				<input value={username} onChange={e => setUsername(e.target.value)} placeholder="jméno" required />
				<input value={password} onChange={e => setPassword(e.target.value)} placeholder="heslo" type="password" required />
				<select value={role} onChange={e => setRole(e.target.value)}>
					<option>user</option>
					<option>admin</option>
				</select>
				<button>přidat</button>
			</form>
			</>
		)}
		</>
	)
}

export default App

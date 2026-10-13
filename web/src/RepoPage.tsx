import { useState } from "react"
import { useEffect } from "react"
import { Link, useParams } from "react-router"
import { api, enc } from "./api"

type Entry = {
	name : string
	type : string
	size : number | null
}

type Data = {
	repo : string
	path : string
	entries : Entry[]
}

// mini_git / repo / src / utils, poslední část není odkaz
export function Crumbs({ repo, path } : { repo : string, path : string }) {
	const parts = path ? path.split("/") : []
	return (
		<h2>
			<Link to="/">mini_git</Link> / <Link to={`/${enc(repo)}`}>{repo}</Link>
			{parts.map((part, i) => (
				<span key={i}>
					{" / "}
					{i === parts.length - 1 ? part : <Link to={`/${enc(repo)}/tree/${enc(parts.slice(0, i + 1).join("/"))}`}>{part}</Link>}
				</span>
			))}
		</h2>
	)
}

export default function RepoPage() {
	const [data, setData] = useState<Data | null>(null)
	const [error, setError] = useState<string | null>(null)
	const { repoName = "", "*": splat = "" } = useParams()
	const path = splat.replace(/\/+$/, "")

	useEffect(() => {
		setData(null)
		setError(null)
		api<Data>(`/api/web/${enc(repoName)}/tree/${enc(path)}`)
			.then(setData)
			.catch(e => setError(e.message))
	}, [repoName, path])

	const link = (entry : Entry) => {
		const full = path ? `${path}/${entry.name}` : entry.name
		return `/${enc(repoName)}/${entry.type === "tree" ? "tree" : "blob"}/${enc(full)}`
	}

	return (
		<>
		<Crumbs repo={repoName} path={path} />
		{!path && <pre>git clone -c http.extraHeader="X-Password: &lt;heslo&gt;" {location.origin}/repos/{repoName}.git</pre>}
		{error && <p className="error">{error}</p>}
		{!data && !error && <p>loading...</p>}
		{data && data.entries.length === 0 && <p>prázdné</p>}
		{data && data.entries.length > 0 && (
			<table>
				<tbody>
					{data.entries.map(entry => (
						<tr key={entry.name}>
							<td>
								<Link to={link(entry)}>{entry.type === "tree" ? `${entry.name}/` : entry.name}</Link>
							</td>
							<td>{entry.size ?? ""}</td>
						</tr>
					))}
				</tbody>
			</table>
		)}
		</>
	)
}

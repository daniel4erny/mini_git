import { useState } from "react"
import { useEffect } from "react"
import { useParams } from "react-router"
import { api, enc } from "./api"
import { Crumbs } from "./RepoPage"

type Data = {
	repo : string
	path : string
	binary : boolean
	content : string | null
}

export default function BlobPage() {
	const [data, setData] = useState<Data | null>(null)
	const [error, setError] = useState<string | null>(null)
	const { repoName = "", "*": path = "" } = useParams()

	useEffect(() => {
		setData(null)
		setError(null)
		api<Data>(`/api/web/${enc(repoName)}/blob/${enc(path)}`)
			.then(setData)
			.catch(e => setError(e.message))
	}, [repoName, path])

	return (
		<>
		<Crumbs repo={repoName} path={path} />
		{error && <p className="error">{error}</p>}
		{!data && !error && <p>loading...</p>}
		{data && (data.binary ? <p>binární soubor</p> : <pre>{data.content}</pre>)}
		</>
	)
}

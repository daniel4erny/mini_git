import { useState } from "react"
import { useEffect } from "react"
import { useParams } from "react-router"

// {
//   "repo": "projekt",
//   "path": "src/utils",
//   "entries": [
//     { "name": "helpers.py", "type": "blob", "size": 210 }
//   ]
// }
//
// {
//   "repo": "projekt",
//   "path": "src/main.py",
//   "binary": false, || true, jestli to je binární soubor nebo ne
//   "content": "print('ahoj')\n" || null, pokud je binární soubor
// }

type Entry = {
	name : string
	type : string
	size : number
}

type Data = {
	repo : string
	path : string
	entries : Entry[]
}



export default function RepoPage() {
	const [data, setData] = useState<Data | null>(null)
	const [loading, setLoading] = useState(true)
	const { repoName } = useParams<{ repoName: string }>()

	useEffect(() => {
		const fetchData = async () => {
			res = await fetch(`/repos/${repoName}.git`)
		}
		fetchData()
	}, [])

	return (
		<>
		<div>
			(loading && <p>loading...</p>)
		</div>
		</>
  )
}

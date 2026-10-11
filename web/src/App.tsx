import { useEffect } from "react"
import { useState } from "react"

function App() {
	const [data, setData] = useState<{ message: string } | null>(null)
	useEffect(() => {
		const fetchData = async () => {
			const info = await fetch("/api/test")
			const data = await info.json()
			setData(data)
		}
		fetchData()
	}, [])
	return (
    <>
		<p>{data?.message}</p>
	</>
  )
}

export default App

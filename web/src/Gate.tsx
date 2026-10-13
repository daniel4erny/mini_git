import { useState } from "react"
import { getPassword, setPassword } from "./api"

// dokud není heslo, ukazuje se jen tohle
export default function Gate({ children } : { children : React.ReactNode }) {
	const [password, setStored] = useState(getPassword())
	const [input, setInput] = useState("")

	if (password) {
		return children
	}

	const submit = (e : React.FormEvent) => {
		e.preventDefault()
		setPassword(input)
		setStored(input)
	}

	return (
		<form onSubmit={submit}>
			<h1>mini_git</h1>
			<input value={input} onChange={e => setInput(e.target.value)} placeholder="heslo" type="password" autoFocus required />
			<button>dál</button>
		</form>
	)
}

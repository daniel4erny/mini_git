const PASSWORD_KEY = "mini_git_password"
const WRONG_PASSWORD = "BROTHA WRONG PASSWORD"

// heslo pro celý server, viz middleware v api/main.py
export function getPassword() : string {
	try {
		return localStorage.getItem(PASSWORD_KEY) ?? ""
	} catch {
		return ""
	}
}

export function setPassword(password : string) {
	try {
		if (password) {
			localStorage.setItem(PASSWORD_KEY, password)
		} else {
			localStorage.removeItem(PASSWORD_KEY)
		}
	} catch {
		// private okno apod., heslo se pak bude chtít znova
	}
}

// fetch na API, chyba z FastAPI ({"detail": "..."}) se vyhodí jako Error
// auth řeší prohlížeč sám (basic auth dialog po prvním 401)
export async function api<T>(url : string, init? : RequestInit) : Promise<T> {
	const headers = new Headers(init?.headers)
	headers.set("X-Password", getPassword())
	const res = await fetch(url, { ...init, headers })
	const data = await res.json().catch(() => null)
	// špatné heslo -> zahodit a zpátky na Gate
	if (res.status === 403 && data?.detail === WRONG_PASSWORD) {
		setPassword("")
		location.reload()
	}
	if (!res.ok) {
		throw new Error(typeof data?.detail === "string" ? data.detail : res.statusText)
	}
	return data
}

export function json(method : string, body : unknown) : RequestInit {
	return {
		method,
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(body),
	}
}

// "src/a b.py" -> "src/a%20b.py", lomítka zůstanou
export const enc = (path : string) => path.split("/").map(encodeURIComponent).join("/")

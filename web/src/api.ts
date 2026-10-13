// fetch na API, chyba z FastAPI ({"detail": "..."}) se vyhodí jako Error
// auth řeší prohlížeč sám (basic auth dialog po prvním 401)
export async function api<T>(url : string, init? : RequestInit) : Promise<T> {
	const res = await fetch(url, init)
	const data = await res.json().catch(() => null)
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

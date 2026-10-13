import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router'
import App from './App.tsx'
import RepoPage from './RepoPage.tsx'
import BlobPage from './BlobPage.tsx'
import Gate from './Gate.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Gate>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/:repoName" element={<RepoPage />} />
          <Route path="/:repoName/tree/*" element={<RepoPage />} />
          <Route path="/:repoName/blob/*" element={<BlobPage />} />
        </Routes>
      </BrowserRouter>
    </Gate>
  </StrictMode>,
)

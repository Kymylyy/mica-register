import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        {/* Default route redirects to CASP */}
        <Route path="/" element={<Navigate to="/casp" replace />} />

        {/* Routes for each register type */}
        <Route path="/casp" element={<App registerType="casp" />} />
        <Route path="/casp/:entityId" element={<App registerType="casp" />} />
        <Route path="/other" element={<App registerType="other" />} />
        <Route path="/other/:entityId" element={<App registerType="other" />} />
        <Route path="/art" element={<App registerType="art" />} />
        <Route path="/art/:entityId" element={<App registerType="art" />} />
        <Route path="/emt" element={<App registerType="emt" />} />
        <Route path="/emt/:entityId" element={<App registerType="emt" />} />
        <Route path="/ncasp" element={<App registerType="ncasp" />} />
        <Route path="/ncasp/:entityId" element={<App registerType="ncasp" />} />

        {/* Catch-all: redirect unknown routes to CASP */}
        <Route path="*" element={<Navigate to="/casp" replace />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)

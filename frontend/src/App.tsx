import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/layout/AppShell'
import { AnalyzePage } from '@/pages/AnalyzePage'
import { HistoryPage } from '@/pages/HistoryPage'
import { LandingPage } from '@/pages/LandingPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<LandingPage />} />
          <Route path="/analyze" element={<AnalyzePage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

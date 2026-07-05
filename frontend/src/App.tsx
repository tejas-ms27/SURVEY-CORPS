import { Navigate, Route, Routes } from 'react-router-dom'

import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Landing } from '@/pages/Landing'
import { CaseWorkflow } from '@/pages/CaseWorkflow'
import { Chatbot } from '@/pages/Chatbot'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route element={<DashboardLayout />}>
        {/* One guided "Open Case File" flow replaces the separate Extraction / Analysis /
            Reports pages. The old paths redirect so existing links keep working. */}
        <Route path="/case" element={<CaseWorkflow />} />
        <Route path="/chatbot" element={<Chatbot />} />
        <Route path="/extraction" element={<Navigate to="/case" replace />} />
        <Route path="/analysis" element={<Navigate to="/case" replace />} />
        <Route path="/reports" element={<Navigate to="/case" replace />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App

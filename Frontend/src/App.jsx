import { Routes, Route } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Transactions from './pages/Transactions.jsx'
import TransactionDetails from './pages/TransactionDetails.jsx'
import Pipeline from './pages/Pipeline.jsx'
import ComingSoon from './pages/ComingSoon.jsx'
import NotFound from './pages/NotFound.jsx'

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/transactions" element={<Transactions />} />
        <Route path="/transactions/:id" element={<TransactionDetails />} />
        <Route path="/pipeline" element={<Pipeline />} />
        <Route path="/risk-analysis" element={<ComingSoon title="Risk Analysis" />} />
        <Route path="/alerts" element={<ComingSoon title="Alerts" />} />
        <Route path="/analytics" element={<ComingSoon title="Analytics" />} />
        <Route path="/audit-logs" element={<ComingSoon title="Audit Logs" />} />
        <Route path="/settings" element={<ComingSoon title="Settings" />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}

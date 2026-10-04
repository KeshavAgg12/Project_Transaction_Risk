import { ArrowLeftRight, BarChart3, Bell, LayoutDashboard, ScrollText, Settings, Target, Workflow } from 'lucide-react'

export const NAV_ITEMS = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/transactions', label: 'Transactions', icon: ArrowLeftRight },
  { to: '/risk-analysis', label: 'Risk Analysis', icon: Target },
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/pipeline', label: 'Pipeline', icon: Workflow },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/audit-logs', label: 'Audit Logs', icon: ScrollText },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export const getPageTitle = (pathname) =>
  NAV_ITEMS.find((item) => item.to !== '/' && pathname.startsWith(item.to))?.label || 'Overview'

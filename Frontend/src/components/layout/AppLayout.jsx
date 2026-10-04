import './AppLayout.css'
import { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar.jsx'
import Topbar from './Topbar.jsx'
import { getPageTitle } from './navItems.js'
import { useTheme } from '../../hooks/useTheme.js'

export default function AppLayout() {
  const { theme, toggleTheme } = useTheme()
  const [collapsed, setCollapsed] = useState(false)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const { pathname } = useLocation()
  const title = getPageTitle(pathname)

  useEffect(() => setDrawerOpen(false), [pathname])
  useEffect(() => { document.title = `${title} · RiskFlow` }, [title])

  return (
    <div className={`shell ${collapsed ? 'collapsed' : ''}`}>
      <Sidebar open={drawerOpen} theme={theme} onToggleTheme={toggleTheme} />
      <div>
        <Topbar title={title} onOpenMenu={() => setDrawerOpen((open) => !open)} onToggleCollapse={() => setCollapsed((value) => !value)} />
        <main className="main"><Outlet /></main>
      </div>
    </div>
  )
}

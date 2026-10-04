import './Sidebar.css'
import { NavLink } from 'react-router-dom'
import { Activity, Moon, Sun } from 'lucide-react'
import { NAV_ITEMS } from './navItems.js'

export default function Sidebar({ open, theme, onToggleTheme }) {
  const ThemeIcon = theme === 'dark' ? Sun : Moon

  return (
    <aside className={`sidebar ${open ? 'open' : ''}`} aria-label="Primary">
      <div className="brand">
        <b>RiskFlow</b>
        <small>Transaction Risk Pipeline</small>
      </div>

      {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
        <NavLink key={to} to={to} end={to === '/'} title={label} className={({ isActive }) => `nav ${isActive ? 'active' : ''}`}>
          <Icon size={18} />
          <span>{label}</span>
        </NavLink>
      ))}

      <div className="spacer" />

      <div className="nav static"><Activity size={18} className="status-dot" /><span>All systems operational</span></div>
      <button className="nav" onClick={onToggleTheme}>
        <ThemeIcon size={18} />
        <span>{theme === 'dark' ? 'Light' : 'Dark'} theme</span>
      </button>
      <div className="nav static"><b className="nav-initial">A</b><span>Analyst (demo)</span></div>
    </aside>
  )
}

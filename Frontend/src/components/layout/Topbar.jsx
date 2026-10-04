import '../ui/Input.css'
import './Topbar.css'
import { Bell, Menu, PanelLeft, Search } from 'lucide-react'
import Breadcrumbs from './Breadcrumbs.jsx'

export default function Topbar({ title, onOpenMenu, onToggleCollapse }) {
  return (
    <header className="top">
      <button className="iconbtn menu" aria-label="Open menu" onClick={onOpenMenu}><Menu size={18} /></button>
      <button className="iconbtn desktop-only" aria-label="Collapse sidebar" onClick={onToggleCollapse}><PanelLeft size={18} /></button>
      <Breadcrumbs title={title} />
      <label className="search">
        <Search size={16} />
        <input className="input" placeholder="Search transactions, IDs, users..." aria-label="Global search" />
      </label>
      <span className="spacer" />
      <button className="iconbtn" aria-label="Notifications"><Bell size={18} /></button>
    </header>
  )
}

import { useMemo, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { Activity, ArrowRight, BarChart3, BriefcaseBusiness, ChevronDown, ClipboardList, GraduationCap, Gauge, GitCompareArrows, Lightbulb, Menu, Network, Search, Settings2, UserRound, WalletCards, X } from 'lucide-react';
import { useApp } from '../app/AppContext';

const navigation = [
  { title: 'Workspace', links: [
    { to: '/', label: 'Overview', icon: Gauge },
    { to: '/profile', label: 'Student profile', icon: UserRound },
    { to: '/placement', label: 'Placement prediction', icon: Activity },
  ] },
  { title: 'Career analysis', links: [
    { to: '/skills', label: 'Skill gap', icon: GitCompareArrows },
    { to: '/recommendations', label: 'Recommendations', icon: Lightbulb },
    { to: '/what-if', label: 'What-if analysis', icon: Network },
    { to: '/salary', label: 'Salary prediction', icon: WalletCards },
  ] },
  { title: 'Model & data', links: [
    { to: '/eda', label: 'Data analysis', icon: BarChart3 },
    { to: '/models', label: 'Model performance', icon: ClipboardList },
  ] },
];

function describeStudent(student: unknown, label: string) {
  if (!student || typeof student !== 'object') return label;
  const entries = Object.entries(student as Record<string, unknown>).slice(0, 2);
  return entries.map(([key, value]) => `${key}: ${typeof value === 'object' ? '…' : String(value)}`).join(' · ') || label;
}

export function StudentPicker() {
  const { selectedStudent, setSelectedStudent, studentRows, studentLabel, runCapability, states, errors, settings } = useApp();
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const selectedLabel = selectedStudent ? studentLabel(selectedStudent, 0) : '';
  const filtered = useMemo(() => studentRows.map((student, index) => ({ student, index, label: studentLabel(student, index) }))
    .filter((row) => !query || row.label.toLowerCase().includes(query.toLowerCase())), [studentRows, studentLabel, query]);
  const bound = Boolean(settings.bindings.students.operationId);
  const refresh = () => void runCapability('students').catch(() => undefined);
  return <div className="student-picker">
    <div className="picker-label">CURRENT STUDENT</div>
    <div className={`picker-control ${open ? 'picker-open' : ''}`}>
      <Search size={16} className="picker-search-icon" />
      <input value={open ? query : selectedLabel} placeholder={selectedLabel || 'Search or select a student'}
        aria-label="Search and select student" onFocus={() => { setOpen(true); setQuery(''); }}
        onChange={(event) => { setQuery(event.target.value); setOpen(true); }} onKeyDown={(event) => { if (event.key === 'Escape') setOpen(false); }} />
      <button className="picker-caret" aria-label="Toggle student list" onClick={() => setOpen((value) => !value)}><ChevronDown size={15} /></button>
      {open && <>
          <button className="popover-dismiss" aria-label="Close student selector" onClick={() => setOpen(false)} />
          <div className="picker-menu">
          <div className="picker-menu-head"><span>{studentRows.length ? `${studentRows.length} backend records` : 'Student records'}</span><button onClick={refresh} disabled={states.students === 'loading' || !bound}>{states.students === 'loading' ? 'Loading…' : 'Load directory'}</button></div>
          {!bound && <div className="picker-hint">Map a student-directory operation in Backend connection.</div>}
          {errors.students && <div className="picker-error">{errors.students} <button onClick={refresh}>Retry</button></div>}
          {Boolean(selectedStudent) && <button className="picker-option selected-option" onClick={() => { setSelectedStudent(null); setOpen(false); }}><span className="option-avatar"><X size={13} /></span><span><b>Clear selection</b><small>Keep the current session, no student selected</small></span></button>}
          {filtered.length ? filtered.map(({ student, index, label }) => <button className="picker-option" key={index} onClick={() => { setSelectedStudent(student); setOpen(false); setQuery(''); }}>
            <span className="option-avatar"><GraduationCap size={15} /></span><span><b>{label}</b><small>{describeStudent(student, `Record ${index + 1}`)}</small></span><ArrowRight size={14} className="option-arrow" />
          </button>) : <div className="picker-empty">{studentRows.length ? 'No matching backend records.' : 'No directory data loaded yet.'}</div>}
          {studentRows.length > 0 && !settings.bindings.students.fieldPaths.name && <div className="picker-hint">Student labels are record numbers until a name field is mapped.</div>}
        </div>
      </>}
    </div>
  </div>;
}

export default function Shell() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const { settings, operations, selectedStudent, studentLabel } = useApp();
  const isConnected = Boolean(settings.baseUrl && operations.length);
  return <div className="app-frame">
    <aside className={`sidebar ${mobileOpen ? 'sidebar-mobile-open' : ''}`}>
      <div className="brand-lockup"><img src="/logo.svg" alt="" /><div><strong>Placement</strong><span>INTELLIGENCE</span></div><button className="sidebar-close" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X size={18} /></button></div>
      <div className="workspace-tag"><span className="workspace-dot" /> CAREER INTELLIGENCE</div>
      <nav aria-label="Main navigation">
        {navigation.map((group) => <div className="nav-group" key={group.title}><div className="nav-group-title">{group.title}</div>{group.links.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} end={to === '/'} onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-link ${isActive ? 'nav-active' : ''}`}><Icon size={17} strokeWidth={1.8} /><span>{label}</span>{location.pathname === to && <span className="nav-indicator" />}</NavLink>)}</div>)}
      </nav>
      <div className="sidebar-spacer" />
      <NavLink to="/connection" onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-link connection-nav ${isActive ? 'nav-active' : ''}`}><Settings2 size={17} /><span>Backend connection</span><span className={`connection-state-dot ${isConnected ? 'connected' : ''}`} /></NavLink>
      <div className="sidebar-foot"><div className="status-indicator"><span className={`status-dot ${isConnected ? 'online' : ''}`} /><span>{isConnected ? 'API described' : 'API not connected'}</span></div><span className="sidebar-foot-caption">Outputs appear only when returned by your backend.</span></div>
    </aside>
    {mobileOpen && <button className="mobile-scrim" onClick={() => setMobileOpen(false)} aria-label="Close menu" />}
    <main className="main-column">
      <header className="topbar"><button className="mobile-menu-button" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={19} /></button>
        <div className="breadcrumb"><span>Placement Intelligence</span><span className="breadcrumb-slash">/</span><strong>{navigation.flatMap((group) => group.links).find((link) => link.to === location.pathname)?.label || (location.pathname === '/connection' ? 'Backend connection' : 'Analysis')}</strong></div>
        <div className="topbar-right"><div className="selected-student-chip"><span className="chip-avatar"><GraduationCap size={14} /></span><span className="student-chip-copy"><small>ANALYZING</small><b>{selectedStudent ? studentLabel(selectedStudent) : 'No student selected'}</b></span></div><NavLink className="topbar-setting" to="/connection" aria-label="Backend connection"><Settings2 size={17} /></NavLink></div>
      </header>
      <div className="mobile-picker"><StudentPicker /></div>
      <div className="page-shell"><div className="desktop-context"><StudentPicker /><div className="context-divider" /><div className="context-note"><BriefcaseBusiness size={15} /><span>Student-level analysis · backend-sourced</span></div></div><div className="page-content"><Outlet /></div></div>
      <footer className="app-footer"><span>PLACEMENT INTELLIGENCE <i>·</i> FRONTEND ANALYSIS WORKSPACE</span><span>Predictions are model outputs, not guarantees.</span></footer>
    </main>
  </div>;
}

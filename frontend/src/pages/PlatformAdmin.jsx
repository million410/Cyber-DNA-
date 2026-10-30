import React, { useCallback, useEffect, useState } from 'react';
import { Building2, Users, Activity, Radio, RefreshCw, ShieldAlert, FileText } from 'lucide-react';
import { apiGet, apiPatch } from '../api/client';
import { Panel, PageHead, DataTable, StatusBadge } from '../components/ui';

const metricItems = [
  ['organizations', 'Organizations', Building2],
  ['active_organizations', 'Active organizations', Activity],
  ['users', 'Customer users', Users],
  ['events', 'Stored events', FileText],
  ['alerts', 'Alerts', ShieldAlert],
  ['active_collector_keys', 'Active collector keys', Radio],
];

const dateLabel = (value) => value ? new Date(value).toLocaleString() : '—';

export default function PlatformAdmin() {
  const [overview, setOverview] = useState(null);
  const [organizations, setOrganizations] = useState([]);
  const [users, setUsers] = useState([]);
  const [audit, setAudit] = useState([]);
  const [tab, setTab] = useState('organizations');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');

  const refresh = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [summary, orgs, people, logs] = await Promise.all([
        apiGet('/platform/overview'),
        apiGet('/platform/organizations', { search, limit: 100 }),
        apiGet('/platform/users'),
        apiGet('/platform/audit-logs', { limit: 100 }),
      ]);
      setOverview(summary);
      setOrganizations(orgs.items || []);
      setUsers(people || []);
      setAudit(logs || []);
    } catch (err) {
      setError('Unable to load Platform Admin data. Confirm that this account has platform administrator access.');
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => { refresh(); }, [refresh]);

  const toggleUser = async (user) => {
    try {
      await apiPatch(`/platform/users/${user.id}/access`, { is_active: !user.is_active });
      await refresh();
    } catch {
      setError(`Could not update access for ${user.username}.`);
    }
  };

  return <>
    <PageHead
      title="Platform Admin"
      desc="Manage customer organizations, accounts, platform usage, and audit activity."
      actions={<button type="button" className="btn btn-secondary" onClick={refresh} disabled={loading}><RefreshCw size={14} /> {loading ? 'Refreshing…' : 'Refresh'}</button>}
    />
    {error && <div className="notice notice-error" role="alert">{error}</div>}
    <div className="grid">
      {metricItems.map(([key, label, Icon]) => <Panel className="col-2" key={key}>
        <div className="metric-label"><Icon size={15} /> {label}</div>
        <div className="metric-value">{overview?.[key] ?? '—'}</div>
      </Panel>)}
      <Panel className="col-12" title="Customer management" subtitle="Each organization has its own users, events, alerts, incidents, and collector credentials.">
        <div className="toolbar" style={{ marginBottom: '1rem' }}>
          <div className="segmented" role="tablist" aria-label="Platform administration sections">
            {['organizations', 'users', 'audit'].map((value) => <button key={value} type="button" role="tab" aria-selected={tab === value} className={tab === value ? 'active' : ''} onClick={() => setTab(value)}>{value === 'audit' ? 'Audit log' : value[0].toUpperCase() + value.slice(1)}</button>)}
          </div>
          {tab === 'organizations' && <input aria-label="Search organizations" className="input" placeholder="Search organizations…" value={search} onChange={(event) => setSearch(event.target.value)} />}
        </div>
        {tab === 'organizations' && <DataTable
          rows={organizations}
          rowKey={(org) => org.id}
          empty={<div className="empty"><Building2 size={24} /><b>No organizations found</b><span>Organizations created by the platform administrator will appear here.</span></div>}
          columns={[
            { key: 'name', label: 'Organization', primary: true, render: (org) => <><b>{org.name}</b><span className="cell-sub">{org.country || 'Country not set'} · {org.industry || 'Industry not set'}</span></> },
            { key: 'status', label: 'Status', render: (org) => <StatusBadge status={org.status} /> },
            { key: 'users', label: 'Users', align: 'right', render: (org) => org.users },
            { key: 'events', label: 'Events', align: 'right', render: (org) => org.events },
            { key: 'alerts', label: 'Alerts', align: 'right', render: (org) => org.alerts },
            { key: 'active_collectors', label: 'Collectors', align: 'right', render: (org) => org.active_collectors },
            { key: 'plan_status', label: 'Plan', render: (org) => org.plan_status },
            { key: 'activation_status', label: 'Activation', render: (org) => org.activation_status },
          ]}
        />}
        {tab === 'users' && <DataTable
          rows={users}
          rowKey={(user) => user.id}
          empty={<div className="empty"><Users size={24} /><b>No customer accounts</b></div>}
          columns={[
            { key: 'username', label: 'Account', primary: true, render: (user) => <><b>{user.username}</b><span className="cell-sub">{user.email || 'No email recorded'}</span></> },
            { key: 'organization_id', label: 'Organization', render: (user) => user.organization_id ?? '—' },
            { key: 'role', label: 'Role', render: (user) => user.role },
            { key: 'last_login_at', label: 'Last login', render: (user) => dateLabel(user.last_login_at) },
            { key: 'is_active', label: 'Access', render: (user) => <button type="button" className={user.is_active ? 'btn btn-secondary' : 'btn btn-danger'} onClick={() => toggleUser(user)}>{user.is_active ? 'Disable' : 'Enable'}</button> },
          ]}
        />}
        {tab === 'audit' && <DataTable
          rows={audit}
          rowKey={(entry) => entry.id}
          empty={<div className="empty"><FileText size={24} /><b>No audit activity yet</b></div>}
          columns={[
            { key: 'created_at', label: 'Time', render: (entry) => dateLabel(entry.created_at) },
            { key: 'action', label: 'Action', primary: true, render: (entry) => entry.action },
            { key: 'organization_id', label: 'Organization', render: (entry) => entry.organization_id ?? 'Platform' },
            { key: 'actor_user_id', label: 'Actor', render: (entry) => entry.actor_user_id ?? 'System' },
            { key: 'details', label: 'Details', render: (entry) => JSON.stringify(entry.details || {}) },
          ]}
        />}
      </Panel>
    </div>
    <p className="muted">Billing provider integration, email verification, and organization self-service registration are not enabled yet. This console does not pretend those external services are connected.</p>
  </>;
}

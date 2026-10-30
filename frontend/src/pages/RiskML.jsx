import React, { useEffect, useState } from 'react';
import { BrainCircuit, HelpCircle, Info, Lightbulb, Cpu } from 'lucide-react';
import { useData } from '../data/DataContext';
import { Panel, PageHead, DataTable, Risk, RiskBadge, useSort } from '../components/ui';
import { BarChart, LineAreaChart } from '../components/charts';
import { apiGet, apiPost } from '../api/client';
import { riskLevel } from '../hooks/utils';
import { matches } from './shared';
import { useAssistantContext } from '../components/assistant/AssistantProvider';
import { userContext } from '../components/assistant/contextBuilders';
import AnalystExplanation from '../components/AnalystExplanation';

export default function RiskML({ query }) {
  const { users, detection } = useData();
  const [sel, setSel] = useState(null);
  const [aiStatus, setAiStatus] = useState(null);
  const [aiCheck, setAiCheck] = useState(false);
  const [aiError, setAiError] = useState('');
  useEffect(() => { let active = true; apiGet('/analyst/status').then((value) => { if (active) setAiStatus(value); }).catch(() => { if (active) setAiStatus({ status: 'offline', configured: false }); }); return () => { active = false; }; }, []);
  const checkAiConnection = async () => { setAiCheck(true); setAiError(''); try { const value = await apiPost('/analyst/status/check', {}); setAiStatus(value); } catch (error) { setAiError(error?.message || 'Connection check failed'); } finally { setAiCheck(false); } };
  const modelReady = detection?.ml_status === 'available';
  const modelVersion = detection?.model_version || 'Not loaded';
  const threshold = Number.isFinite(Number(detection?.ml_compatibility?.threshold_p99)) ? Number(detection.ml_compatibility.threshold_p99).toFixed(4) : (detection?.ml_threshold_p99 != null ? Number(detection.ml_threshold_p99).toFixed(4) : 'Not available');
  const base = users.filter((u) => matches(query, u.username, u.behavior, u.dept));
  const { sorted, sort, onSort } = useSort(base, { key: 'risk', dir: 'desc' });
  const cur = sorted.find((u) => u.username === sel) || sorted[0];
  useAssistantContext(cur ? { selection: userContext(cur) } : null);
  const bands = [['0–29', 0, 29], ['30–49', 30, 49], ['50–69', 50, 69], ['70–84', 70, 84], ['85–100', 85, 100]];
  const dist = bands.map(([, lo, hi]) => users.filter((u) => u.risk >= lo && u.risk <= hi).length);
  return (
    <>
      <PageHead title="Risk & ML" desc="Review user risk indicators and the actual detection-engine status. Risk scores shown here are user records unless explicitly identified as model findings." />
      <div className="grid">
        <Panel className="col-4" title="Model information" subtitle="Behavioral analytics engine" action={<span className="node-ico"><BrainCircuit size={18} /></span>}>
          <dl className="kv-list">
            <div><dt>Model</dt><dd>{modelReady ? (detection?.model || 'Isolation Forest') : detection?.ml_status === 'disabled' ? 'Disabled' : 'Not loaded'}</dd></div>
            <div><dt>Platform release</dt><dd>1.25.0</dd></div>
            <div><dt>Model artifact version</dt><dd>{modelVersion}</dd></div>
            <div><dt>Approach</dt><dd>{modelReady ? 'Trained Isolation Forest · unsupervised anomaly detection' : 'Unavailable until the trained artifact loads'}</dd></div>
            <div><dt>Behavior window</dt><dd>{modelReady ? 'Consecutive user/host hourly buckets (minimum 2)' : 'Not active'}</dd></div>
            <div><dt>Anomaly threshold (p99)</dt><dd>{modelReady ? threshold : 'Not configured / model unavailable'}</dd></div>
            <div><dt>Rule engine</dt><dd>{detection?.status === 'available' ? 'Available' : detection?.status === 'disabled' ? 'Disabled' : 'Unknown / offline'}</dd></div>
            <div><dt>ML engine</dt><dd>{detection?.ml_status === 'available' ? 'Available' : detection?.ml_status === 'disabled' ? 'Disabled' : detection?.ml_status === 'unavailable' ? 'Unavailable' : 'Not verified'}</dd></div>
          </dl>
          <div className="sub-title" style={{ marginTop: '1rem' }}><Cpu size={13} style={{ verticalAlign: '-2px' }} /> Model input features ({detection?.ml_features?.length || 9})</div>
          <div className="chips">{(detection?.ml_features || ['successful_logons', 'failed_logons', 'logoffs', 'explicit_credential_events', 'privilege_events', 'process_starts', 'kerberos_tgt_events', 'kerberos_service_ticket_events', 'credential_validation_events']).map((f) => <span className="chip" key={f}>{f.replaceAll('_', ' ')}</span>)}</div>
          <p className="muted" style={{ marginTop: '.65rem' }}>Feature mapping is implemented as a Windows Security event-ID compatibility adapter. It still requires validation against the original training aggregation pipeline.</p>
        </Panel>
        <Panel className="col-8" title="Detection engine status" subtitle="Live status from the backend when available">
          <div className="empty">
            <b>{detection?.engine === 'rule_and_ml' ? 'Rule-based and ML engines available' : detection?.engine === 'rule_only' ? 'Rule-based detection available' : 'Detection status not verified'}</b>
            <p>{detection?.ml_warning || (detection?.ml_status === 'available' ? 'The model artifact is available. This does not by itself establish production accuracy or prove that every event has been scored.' : 'Connect to the backend and verify the detection status endpoint to confirm model availability.')}</p>
            {detection && <p className="muted">Rules enabled: {detection.rules_enabled ?? '—'} · Persisted findings: {detection.findings_total ?? '—'} · Events available: {detection.events_available ?? '—'}</p>}
          </div>
        </Panel>
        <Panel className="col-4" title="AI explanation API" subtitle="External provider status">
          <div className="empty">
            <b>{aiStatus?.status === 'connected' ? 'AI API connected' : aiStatus?.status === 'configured_not_checked' ? 'API configured · not yet tested' : aiStatus?.status === 'error' ? 'API connection failed' : aiStatus?.configured ? 'API configured' : 'AI API not configured / unavailable'}</b>
            <p>{aiStatus?.message || 'Checking AI provider configuration…'}</p>
            {aiStatus?.provider && <p className="muted">Provider: {aiStatus.provider} · Model: {aiStatus.model || 'Not configured'}</p>}
            <button type="button" className="btn btn-secondary" onClick={checkAiConnection} disabled={aiCheck || !aiStatus?.configured}>{aiCheck ? 'Testing connection…' : 'Test AI API connection'}</button>
            {aiError && <p className="muted">{aiError}</p>}
          </div>
        </Panel>
        <Panel className="col-4" title="Users by risk band" subtitle="Count of users per score range">
          <BarChart labels={bands.map((b) => b[0])} values={dist} highlight={[3, 4]} height={210} name="Users" ariaLabel="Users by risk band" />
        </Panel>
        <Panel className="col-8" flush title="Scored users" subtitle="Select a row to read the explanation">
          <DataTable rows={sorted} rowKey={(u) => u.username} sort={sort} onSort={onSort} columns={[
            { key: 'username', label: 'User', sortable: true, primary: true, render: (u) => <button type="button" className="link-btn" style={{ padding: 0, fontSize: '.875rem' }} onClick={() => setSel(u.username)}>{u.username}</button> },
            { key: 'risk', label: 'Risk score', sortable: true, render: (u) => <Risk value={u.risk} /> },
            { key: 'anomaly', label: 'Anomaly score', sortable: true, render: (u) => <span className="num cell-strong">{typeof u.anomaly === 'number' && Number.isFinite(u.anomaly) ? u.anomaly.toFixed(2) : 'N/A'}{typeof u.anomaly === 'number' && Number.isFinite(u.anomaly) && detection?.ml_threshold_p99 != null && u.anomaly >= detection.ml_threshold_p99 && <span className="cell-sub">above threshold</span>}</span> },
            { key: 'behavior', label: 'Behavior type', render: (u) => u.behavior },
            { key: 'lvl', label: 'Level', render: (u) => <RiskBadge risk={u.risk} /> },
          ]} />
        </Panel>
        {cur && (
          <Panel className="col-12" title={`Explanation — ${cur.username}`} subtitle={`${cur.behavior} · risk ${cur.risk} · anomaly ${typeof cur.anomaly === 'number' && Number.isFinite(cur.anomaly) ? cur.anomaly.toFixed(2) : 'N/A'} · platform 1.25.0 · model ${modelVersion}`}>
            <div className="narrative" style={{ padding: 0 }}>
              <div className="nar n-what"><h3><HelpCircle size={16} color="var(--c1)" />What happened</h3><p>{cur.what}</p></div>
              <div className="nar n-means"><h3><Info size={16} color="var(--med-solid)" />What it means</h3><p>{cur.means}</p></div>
              <div className="nar n-rec"><h3><Lightbulb size={16} color="var(--ok-solid)" />Recommendation</h3><p>{cur.recommendation}</p></div>
            </div>
            <AnalystExplanation
              context={{ page: 'Risk & ML', selection: userContext(cur) }}
              question={`Give a concise explanation of the selected user's risk indicators. Do not describe a stored risk score as a model prediction unless backend evidence confirms that. Explain the available evidence, limitations, and up to three next steps.`}
              title={`AI Analyst explanation · ${cur.username}`}
            />
          </Panel>
        )}
      </div>
    </>
  );
}

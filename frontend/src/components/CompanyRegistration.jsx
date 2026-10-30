import React, { useState } from 'react';
import { ArrowLeft, ArrowRight } from 'lucide-react';

const API = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export default function CompanyRegistration({ onBack }) {
  const [form, setForm] = useState({ company_name: '', email: '', country: '', industry: '', password: '' });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [sent, setSent] = useState(false);
  const change = (key) => (event) => setForm((old) => ({ ...old, [key]: event.target.value }));

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true); setError('');
    try {
      const response = await fetch(`${API}/registration`, {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify(form),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof payload.detail === 'string' ? payload.detail : 'Registration could not be completed.');
      setSent(true);
    } catch (err) { setError(err.message || 'Unable to submit registration.'); }
    finally { setBusy(false); }
  };

  if (sent) return <div className="company-registration">
    <h2>Check your email</h2>
    <p>We sent a verification link to <strong>{form.email}</strong>. Open it to verify your address, then return here to log in and complete onboarding.</p>
    <button type="button" className="btn btn-primary" onClick={onBack}>Back to log in</button>
  </div>;

  return <div className="company-registration">
    <button type="button" className="link-btn" onClick={onBack}><ArrowLeft size={14}/> Back to log in</button>
    <h2>Register your company</h2>
    <p className="lead">Create your company and its first administrator account.</p>
    <form onSubmit={submit} noValidate>
      <label className="fld">Company name<input required minLength={2} maxLength={200} value={form.company_name} onChange={change('company_name')} autoComplete="organization" /></label>
      <label className="fld">Work email<input required type="email" value={form.email} onChange={change('email')} autoComplete="email" /></label>
      <label className="fld">Country<input required value={form.country} onChange={change('country')} autoComplete="country-name" /></label>
      <label className="fld">Industry<input required value={form.industry} onChange={change('industry')} placeholder="e.g. Education, Finance, Healthcare" /></label>
      <label className="fld">Administrator password<input required type="password" minLength={12} maxLength={256} value={form.password} onChange={change('password')} autoComplete="new-password" /><small>Use at least 12 characters.</small></label>
      {error && <div className="form-note err" role="alert">{error}</div>}
      <button className="btn btn-primary" type="submit" disabled={busy}>{busy ? 'Submitting…' : 'Create company account'} <ArrowRight size={16}/></button>
    </form>
  </div>;
}

import React, { useState } from 'react';
import { ArrowRight, Eye, EyeOff, ShieldCheck, Stethoscope, UserRound } from 'lucide-react';

const Login = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!username || !password) {
      setError('Please enter both username and password.');
      return;
    }
    // Simulate login (replace with real auth later)
    setError('');
    onLogin(username);
  };

  return (
    <div
      className="min-h-screen relative overflow-hidden bg-hospital-bg"
      style={{
        backgroundImage: 'radial-gradient(circle at top left, rgba(0,86,179,0.16), transparent 34%), radial-gradient(circle at top right, rgba(25,135,84,0.12), transparent 28%), linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%)'
      }}
    >
      <div
        className="absolute inset-0 pointer-events-none opacity-60"
        style={{
          backgroundImage: 'linear-gradient(rgba(255,255,255,0.45) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.45) 1px, transparent 1px)',
          backgroundSize: '48px 48px'
        }}
      />
      <div className="relative min-h-screen grid place-items-center p-4 sm:p-6">
        <div className="w-full max-w-5xl overflow-hidden rounded-3xl border border-hospital-border bg-white/80 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur-xl">
          <div className="grid lg:grid-cols-[1.05fr_0.95fr]">
            <aside
              className="relative overflow-hidden p-8 sm:p-10 text-white"
              style={{ backgroundImage: 'linear-gradient(160deg, #0b3d91 0%, #0a2f6b 52%, #08244f 100%)' }}
            >
              <div
                className="absolute inset-0 opacity-25"
                style={{
                  backgroundImage: 'radial-gradient(circle at top right, rgba(255,255,255,0.3), transparent 30%), radial-gradient(circle at bottom left, rgba(255,255,255,0.18), transparent 28%)'
                }}
              />
              <div className="relative flex h-full flex-col justify-between gap-10">
                <div className="space-y-6">
                  <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-[10px] font-bold uppercase tracking-[0.24em] backdrop-blur-sm">
                    <ShieldCheck size={14} /> Secure Doctor Access
                  </div>

                  <div className="space-y-4 max-w-md">
                    <div className="flex items-center gap-3 text-white/95">
                      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10 ring-1 ring-white/20">
                        <Stethoscope size={24} />
                      </div>
                      <div>
                        <div className="text-lg font-semibold leading-none">GenomixAI</div>
                        <div className="text-[11px] uppercase tracking-[0.22em] text-white/70">Clinical Decision Support Console</div>
                      </div>
                    </div>

                    <h1 className="text-3xl sm:text-4xl font-bold leading-tight tracking-tight">
                      Doctor sign-in for patient review, simulation, and prescription workflow.
                    </h1>
                    <p className="text-sm sm:text-base leading-6 text-white/78 max-w-prose">
                      Use your clinical access to review records, run pharmacogenomic simulations, and finalize medication decisions in a guided demo flow.
                    </p>
                  </div>
                </div>

                <div className="relative grid gap-3 sm:grid-cols-3">
                  <div className="rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur-sm">
                    <div className="text-[10px] uppercase tracking-[0.22em] text-white/60">Workflow</div>
                    <div className="mt-2 text-sm font-semibold">Login → Search → Chart → Simulate</div>
                  </div>
                  <div className="rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur-sm">
                    <div className="text-[10px] uppercase tracking-[0.22em] text-white/60">Data</div>
                    <div className="mt-2 text-sm font-semibold">Live backend records</div>
                  </div>
                  <div className="rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur-sm">
                    <div className="text-[10px] uppercase tracking-[0.22em] text-white/60">Mode</div>
                    <div className="mt-2 text-sm font-semibold">Demo-ready access</div>
                  </div>
                </div>
              </div>
            </aside>

            <section className="p-6 sm:p-8 lg:p-10">
              <div className="mx-auto flex h-full max-w-md flex-col justify-center">
                <div className="mb-8 space-y-2">
                  <div className="text-[10px] font-bold uppercase tracking-[0.24em] text-hospital-muted">Physician Portal</div>
                  <h2 className="text-2xl sm:text-3xl font-bold text-hospital-text">Sign in to continue</h2>
                  <p className="text-sm text-hospital-muted">
                    Enter your doctor credentials to open the clinical dashboard.
                  </p>
                </div>

                <div className="mb-6 rounded-2xl border border-hospital-border bg-hospital-bg/50 p-4">
                  <div className="flex items-start gap-3">
                    <div className="rounded-xl bg-hospital-blue/10 p-2 text-hospital-blue">
                      <UserRound size={18} />
                    </div>
                    <div className="text-sm">
                      <div className="font-semibold text-hospital-text">Demo access</div>
                      <div className="mt-1 text-hospital-muted">
                        Any username and password will open the demo. Use a doctor name like <span className="font-semibold text-hospital-text">Dr. Ahmed</span> for the signed-in display.
                      </div>
                    </div>
                  </div>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                  {error && (
                    <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-hospital-red">
                      {error}
                    </div>
                  )}

                  <div className="space-y-2">
                    <label className="block text-[11px] font-bold uppercase tracking-[0.22em] text-hospital-muted">
                      Doctor ID or Email
                    </label>
                    <div className="relative">
                      <UserRound className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-hospital-muted" size={18} />
                      <input
                        type="text"
                        className="w-full rounded-2xl border border-hospital-border bg-white px-10 py-3 text-sm shadow-sm outline-none transition focus:border-hospital-blue focus:ring-4 focus:ring-hospital-blue/10"
                        value={username}
                        onChange={e => setUsername(e.target.value)}
                        placeholder="dr.jones@genomixai.local"
                        autoFocus
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="block text-[11px] font-bold uppercase tracking-[0.22em] text-hospital-muted">
                      Password
                    </label>
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        className="w-full rounded-2xl border border-hospital-border bg-white px-4 py-3 pr-12 text-sm shadow-sm outline-none transition focus:border-hospital-blue focus:ring-4 focus:ring-hospital-blue/10"
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        placeholder="••••••••"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(v => !v)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg p-1 text-hospital-muted transition hover:bg-hospital-bg hover:text-hospital-text"
                        aria-label={showPassword ? 'Hide password' : 'Show password'}
                      >
                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-hospital-muted">
                    <span>Protected clinical access</span>
                    <span>Demo mode enabled</span>
                  </div>

                  <button
                    type="submit"
                    className="group inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-hospital-blue px-4 py-3.5 font-bold text-white shadow-lg shadow-blue-950/10 transition hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-hospital-blue/20"
                  >
                    Enter Doctor Portal
                    <ArrowRight size={16} className="transition-transform group-hover:translate-x-0.5" />
                  </button>
                </form>

                <div className="mt-6 flex flex-wrap gap-2 text-[11px] text-hospital-muted">
                  <span className="rounded-full border border-hospital-border bg-white px-3 py-1">HIPAA-style workflow demo</span>
                  <span className="rounded-full border border-hospital-border bg-white px-3 py-1">No database required</span>
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;

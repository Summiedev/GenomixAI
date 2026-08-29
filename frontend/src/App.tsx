/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect, useMemo } from 'react';
import { 
  Search, 
  User, 
  Bell, 
  Activity, 
  FileText, 
  FlaskConical, 
  Pill, 
  AlertTriangle, 
  History, 
  ClipboardList,
  ChevronRight,
  Loader2,
  Plus,
  Minus,
  CheckCircle2,
  X,
  Info,
  ArrowRight,
  ShieldAlert,
  Zap,
  Play,
  Building
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { Patient, Medication, DrugInfo, SimulationResult } from './types';
import { MOCK_PATIENTS, MOCK_DRUGS } from './constants';
import { Auth } from './components/Auth';
import { MedicationAssessment } from './components/MedicationAssessment';
import { LandingPage } from './components/LandingPage';

import { PharmacistWorkspace } from './components/PharmacistWorkspace';

// --- Types & State ---
type Screen = 'SEARCH' | 'RETRIEVAL' | 'CHART' | 'SIMULATION';
type AppState = 'LANDING' | 'UNAUTHENTICATED' | 'AUTHENTICATED';

// --- Components ---


const Header = ({ doctorName = "Dr. Sarah Ade", organization = "Lagos Heart Institute", department = "Cardiology" }) => {
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfile, setShowProfile] = useState(false);

  return (
    <header className="h-12 border-b border-hospital-border bg-white flex items-center justify-between px-4 sticky top-0 z-50 shadow-sm">
      <div className="flex items-center gap-2 cursor-pointer" onClick={() => window.location.reload()}>
        <div className="w-8 h-8 bg-hospital-blue rounded flex items-center justify-center text-white font-bold text-lg italic">G</div>
        <span className="font-bold tracking-tight text-hospital-blue uppercase text-sm hidden sm:inline">GenomixAI <span className="text-hospital-text/40 font-normal">EHR v4.2</span></span>
      </div>
      
      <div className="flex items-center gap-3 sm:gap-6">
        <div className="relative">
          <button 
            onClick={() => setShowNotifications(!showNotifications)}
            className="flex items-center gap-2 text-hospital-muted hover:text-hospital-blue transition-colors p-1 rounded hover:bg-hospital-bg"
          >
            <Bell size={18} />
            <div className="absolute top-0 right-0 w-2 h-2 bg-hospital-red rounded-full border border-white"></div>
          </button>
          
          <AnimatePresence>
            {showNotifications && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="absolute right-0 mt-2 w-64 bg-white border border-hospital-border rounded-lg shadow-xl p-4 z-[100]"
              >
                <h4 className="text-[10px] font-bold text-hospital-muted uppercase mb-3 tracking-widest">Recent Notifications</h4>
                <div className="space-y-3">
                  <div className="text-xs p-2 bg-blue-50 rounded border border-blue-100">
                    <div className="font-bold text-hospital-blue">Genomic Lab Ready</div>
                    <div className="text-hospital-muted mt-0.5">Results for Patient MRN-882910 are now available.</div>
                  </div>
                  <div className="text-xs p-2 hover:bg-hospital-bg rounded cursor-pointer">
                    <div className="font-bold">System Update</div>
                    <div className="text-hospital-muted mt-0.5">GenomixAI v4.2.1 deployment scheduled for 02:00 UTC.</div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="h-6 w-[1px] bg-hospital-border"></div>
        
        <div className="relative">
          <button 
            onClick={() => setShowProfile(!showProfile)}
            className="flex items-center gap-2 hover:bg-hospital-bg p-1 rounded transition-colors"
          >
            <div className="text-right hidden md:block">
              <div className="text-[11px] font-semibold leading-none">{doctorName}</div>
              <div className="text-[10px] text-hospital-muted leading-none mt-1">{department}</div>
            </div>
            <div className="w-8 h-8 bg-hospital-blue/10 rounded-full flex items-center justify-center overflow-hidden border border-hospital-blue/20">
              <User size={18} className="text-hospital-blue" />
            </div>
          </button>

          <AnimatePresence>
            {showProfile && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="absolute right-0 mt-2 w-56 bg-white border border-hospital-border rounded-lg shadow-xl overflow-hidden z-[100]"
              >
                <div className="p-3 border-b border-hospital-border bg-hospital-bg/30">
                  <div className="text-xs font-bold">{doctorName}</div>
                  <div className="text-[10px] text-hospital-muted mb-1">{organization}</div>
                  <div className="text-[10px] text-hospital-muted uppercase tracking-wider">{department}</div>
                </div>
                <div className="py-1">
                  <button className="w-full text-left px-3 py-2 text-xs hover:bg-hospital-bg flex items-center gap-2">
                    <User size={14} /> Profile Settings
                  </button>
                  <button className="w-full text-left px-3 py-2 text-xs hover:bg-hospital-bg flex items-center gap-2">
                    <ShieldAlert size={14} /> Security & Access
                  </button>
                  <button onClick={() => window.location.reload()} className="w-full text-left px-3 py-2 text-xs hover:bg-hospital-bg text-hospital-red flex items-center gap-2 border-t border-hospital-border mt-1">
                    <X size={14} /> Sign Out
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
};

const Dashboard = ({ onSelect, user }: { onSelect: (p: Patient) => void, user?: any }) => {
  const [query, setQuery] = useState('');

  const filteredPatients = useMemo(() => {
    if (!query) return [];
    return MOCK_PATIENTS.filter(p => 
      p.name.toLowerCase().includes(query.toLowerCase()) || 
      p.mrn.toLowerCase().includes(query.toLowerCase())
    );
  }, [query]);

  return (
    <div className="max-w-7xl mx-auto mt-8 px-4 pb-20">
      {user && (
        <div className="mb-8 bg-white border border-slate-200 rounded-xl shadow-sm p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 mb-1">Welcome, {user.name}</h1>
            <p className="text-slate-500 text-sm">Your secure clinical workspace is ready.</p>
          </div>
          <div className="flex flex-wrap gap-4 md:gap-8 text-sm">
            <div>
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Organization</div>
              <div className="font-medium text-slate-800 flex items-center gap-1.5"><Building size={14} className="text-hospital-blue" /> {user.organization}</div>
            </div>
            <div>
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Department</div>
              <div className="font-medium text-slate-800">{user.department}</div>
            </div>
            <div>
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Role</div>
              <div className="font-medium text-slate-800">{user.role}</div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Main Content (Left) */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Search Section */}
          <section>
            <div className="mb-4">
              <h2 className="text-lg font-bold text-slate-900">Patient Search</h2>
              <p className="text-sm text-slate-500">Search by Patient Name, MRN, or GenomixAI Patient ID.</p>
            </div>
            <div className="relative">
              <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                <Search size={20} className="text-slate-400" />
              </div>
              <input 
                type="text"
                placeholder="Search patient records..."
                className="w-full h-14 pl-12 pr-4 bg-white border border-slate-200 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-hospital-blue/20 focus:border-hospital-blue text-lg transition-all"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                autoFocus
              />
            </div>
          </section>

          {/* Patients List */}
          <section className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50 flex justify-between items-center">
              <h3 className="text-xs font-bold text-slate-600 uppercase tracking-widest">
                {query ? `Search Results (${filteredPatients.length})` : 'Recently Accessed Patients'}
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider bg-slate-50/50">
                    <th className="py-3 px-6 font-medium">Patient Name</th>
                    <th className="py-3 px-6 font-medium">MRN</th>
                    <th className="py-3 px-6 font-medium">Age/Sex</th>
                    <th className="py-3 px-6 font-medium">Primary Diagnosis</th>
                    <th className="py-3 px-6 font-medium">Last Visit</th>
                    <th className="py-3 px-6"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {(query ? filteredPatients : MOCK_PATIENTS).map(p => (
                    <tr key={p.id} className="hover:bg-slate-50 transition-colors cursor-pointer group" onClick={() => onSelect(p)}>
                      <td className="py-4 px-6 font-bold text-slate-900 group-hover:text-hospital-blue transition-colors">{p.name}</td>
                      <td className="py-4 px-6 text-sm text-slate-500 font-mono">{p.mrn}</td>
                      <td className="py-4 px-6 text-sm text-slate-600">{p.age}y / {p.sex}</td>
                      <td className="py-4 px-6 text-sm text-slate-600 max-w-[200px] truncate">{p.conditions[0]}</td>
                      <td className="py-4 px-6 text-sm text-slate-500">{p.lastVisit}</td>
                      <td className="py-4 px-6 text-right">
                        <ChevronRight size={16} className="text-slate-400 inline opacity-0 group-hover:opacity-100 transition-opacity" />
                      </td>
                    </tr>
                  ))}
                  {query && filteredPatients.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-slate-500 italic">
                        No patient records found matching "{query}"
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>

        {/* Sidebar (Right) */}
        <div className="space-y-6">
          {/* Pending Reviews */}
          <section className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-200 flex items-center gap-2">
              <ClipboardList size={18} className="text-hospital-blue" />
              <h3 className="text-sm font-bold text-slate-900">Pending Medication Reviews</h3>
              <span className="ml-auto bg-blue-100 text-hospital-blue text-[10px] font-bold px-2 py-0.5 rounded-full">2</span>
            </div>
            <div className="divide-y divide-slate-100">
              <div className="p-4 hover:bg-slate-50 cursor-pointer transition-colors">
                <div className="flex justify-between items-start mb-1">
                  <div className="font-bold text-sm text-slate-900">MRN-92014</div>
                  <div className="text-[10px] text-slate-500 font-medium">2h ago</div>
                </div>
                <div className="text-xs text-slate-600 mb-2">Review requested for <span className="font-medium text-slate-900">Warfarin</span> dosage.</div>
                <div className="text-[10px] font-bold text-hospital-blue uppercase tracking-wider">High Risk Alert</div>
              </div>
              <div className="p-4 hover:bg-slate-50 cursor-pointer transition-colors">
                <div className="flex justify-between items-start mb-1">
                  <div className="font-bold text-sm text-slate-900">MRN-11029</div>
                  <div className="text-[10px] text-slate-500 font-medium">5h ago</div>
                </div>
                <div className="text-xs text-slate-600">Review alternative therapies for <span className="font-medium text-slate-900">Simvastatin</span>.</div>
              </div>
            </div>
          </section>

          {/* Clinical Notifications */}
          <section className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-200 flex items-center gap-2">
              <Bell size={18} className="text-slate-400" />
              <h3 className="text-sm font-bold text-slate-900">Clinical Notifications</h3>
            </div>
            <div className="divide-y divide-slate-100">
              <div className="p-4 flex gap-3">
                <div className="w-2 h-2 rounded-full bg-hospital-blue mt-1.5 shrink-0"></div>
                <div>
                  <div className="text-sm font-medium text-slate-900 mb-0.5">Genomic Lab Results Ready</div>
                  <div className="text-xs text-slate-500">Results for Patient MRN-882910 are now available for review.</div>
                </div>
              </div>
              <div className="p-4 flex gap-3">
                <div className="w-2 h-2 rounded-full bg-slate-300 mt-1.5 shrink-0"></div>
                <div>
                  <div className="text-sm font-medium text-slate-900 mb-0.5">Guideline Update</div>
                  <div className="text-xs text-slate-500">CPIC guidelines for Clopidogrel have been updated in the system.</div>
                </div>
              </div>
            </div>
          </section>
        </div>

      </div>
    </div>
  );
};

const RecordRetrieval = ({ onComplete }: { onComplete: () => void }) => {
  const [step, setStep] = useState(0);
  const steps = [
    "Retrieving patient records...",
    "Analyzing medical history...",
    "Checking medication profile...",
    "Evaluating pharmacological risk factors...",
    "Finalizing GenomixAI clinical insights..."
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setStep(s => {
        if (s >= steps.length - 1) {
          clearInterval(timer);
          setTimeout(onComplete, 500);
          return s;
        }
        return s + 1;
      });
    }, 800);
    return () => clearInterval(timer);
  }, [onComplete, steps.length]);

  return (
    <div className="fixed inset-0 bg-hospital-bg z-[100] flex flex-col items-center justify-center">
      <div className="w-64">
        <div className="flex justify-center mb-6">
          <Loader2 size={48} className="text-hospital-blue animate-spin" />
        </div>
        <div className="space-y-4">
          {steps.map((s, i) => (
            <div key={i} className={`flex items-center gap-3 transition-opacity duration-300 ${i > step ? 'opacity-20' : i === step ? 'opacity-100' : 'opacity-50'}`}>
              {i < step ? <CheckCircle2 size={16} className="text-hospital-green" /> : <div className={`w-4 h-4 rounded-full border-2 ${i === step ? 'border-hospital-blue border-t-transparent animate-spin' : 'border-hospital-border'}`}></div>}
              <span className="text-sm font-medium">{s}</span>
            </div>
          ))}
        </div>
        <div className="mt-8 h-1 bg-hospital-border rounded-full overflow-hidden">
          <motion.div 
            className="h-full bg-hospital-blue"
            initial={{ width: 0 }}
            animate={{ width: `${((step + 1) / steps.length) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
};

const TrendLine = ({ values, width = 200, height = 40, stroke = "#2563eb" }: { values: number[], width?: number, height?: number, stroke?: string }) => {
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const range = maxVal - minVal || 1;
  const padding = 6;
  const points = values.map((val, index) => {
    const x = (index / (values.length - 1)) * (width - padding * 2) + padding;
    const y = height - ((val - minVal) / range) * (height - padding * 2) - padding;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width={width} height={height} className="overflow-visible">
      {/* Background guide line */}
      <line x1="0" y1={height / 2} x2={width} y2={height / 2} stroke="#f1f5f9" strokeWidth="1" strokeDasharray="3,3" />
      <polyline
        fill="none"
        stroke={stroke}
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
      {values.map((val, index) => {
        const x = (index / (values.length - 1)) * (width - padding * 2) + padding;
        const y = height - ((val - minVal) / range) * (height - padding * 2) - padding;
        return (
          <g key={index} className="group/dot">
            <circle
              cx={x}
              cy={y}
              r="4"
              className="fill-white stroke-[2.5] transition-all cursor-pointer"
              style={{ stroke }}
            />
            <title>{val}</title>
          </g>
        );
      })}
    </svg>
  );
};

const PatientChart = ({ patient, onAddMedication }: { patient: Patient, onAddMedication: () => void }) => {
  const [activeTab, setActiveTab] = useState('Overview');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  
  // Interactive physician notes state
  const [notes, setNotes] = useState([
    {
      id: 1,
      author: "Dr. Sarah Ade",
      specialty: "Cardiology",
      date: "18 July 2026",
      title: "Medication Review Requested",
      observation: "Patient reports increased fatigue and occasional palpitations. Expresses anxiety regarding future adverse events post her 2025 myocardial infarction.",
      assessment: "Atrial Fibrillation is currently rate-controlled. INR is stable but on the high end. Dual antiplatelet therapy may have genomic efficacy variances.",
      plan: "Ordered GenomixAI medication assessment for further clopidogrel and antiplatelet therapeutic safety review. Monitor lipid panels and renal functions next consultation."
    },
    {
      id: 2,
      author: "Dr. Ahmed Ibrahim",
      specialty: "Cardiology",
      date: "12 March 2026",
      title: "Atrial Fibrillation Diagnosis Note",
      observation: "Patient presented to Lagos Heart Institute with rapid irregular heart palpitations and lightheadedness.",
      assessment: "ECG confirms new-onset Atrial Fibrillation. Hemodynamically stable, normal LV ejection fraction (55%).",
      plan: "Initiate Rate Control therapy. Initiated Warfarin 3mg once daily as anticoagulation prophylaxis. Targeted INR therapeutic range 2.0 - 3.0."
    }
  ]);

  const [newNote, setNewNote] = useState({ title: '', observation: '', assessment: '', plan: '' });
  const [showNoteForm, setShowNoteForm] = useState(false);

  const handleAddNoteSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.title || !newNote.observation) return;
    
    const formattedNote = {
      id: notes.length + 1,
      author: "Dr. Sarah Ade",
      specialty: "Cardiology",
      date: "18 July 2026",
      title: newNote.title,
      observation: newNote.observation,
      assessment: newNote.assessment || "Clinical assessment pending.",
      plan: newNote.plan || "Follow up as clinically indicated."
    };

    setNotes([formattedNote, ...notes]);
    setNewNote({ title: '', observation: '', assessment: '', plan: '' });
    setShowNoteForm(false);
  };

  const tabs = [
    { id: 'Overview', icon: FileText },
    { id: 'History', icon: History },
    { id: 'Vitals', icon: Activity },
    { id: 'Labs', icon: FlaskConical },
    { id: 'Medications', icon: Pill },
    { id: 'Allergies', icon: AlertTriangle },
    { id: 'Notes', icon: ClipboardList },
    { id: 'Genomic Profile', icon: Zap },
    { id: 'Assessments', icon: ShieldAlert },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'Overview':
        return (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-500">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* Active Conditions */}
              <section className="lg:col-span-1 bg-white p-6 border border-slate-200 rounded-xl shadow-sm flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-4 pb-2 border-b border-slate-100">
                    <Activity size={18} className="text-hospital-blue" />
                    <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Active Conditions</h3>
                  </div>
                  <div className="space-y-3">
                    {patient.conditions.map(c => (
                      <div key={c} className="flex items-center justify-between p-3 bg-slate-50 border border-slate-200 rounded-lg">
                        <span className="text-sm font-bold text-slate-800">{c}</span>
                        <span className="px-2.5 py-0.5 bg-blue-50 text-hospital-blue font-semibold text-[10px] uppercase rounded border border-blue-100">Confirmed</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="mt-6 text-xs text-slate-500 italic">Verified across multi-hospital synchronized records.</div>
              </section>

              {/* Current Medications */}
              <section className="lg:col-span-2 bg-white p-6 border border-slate-200 rounded-xl shadow-sm">
                <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <Pill size={18} className="text-hospital-blue" />
                    <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Active Medications</h3>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-4 bg-amber-50/50 border border-amber-200/60 rounded-xl hover:border-amber-300 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-white border border-amber-200 rounded-full flex items-center justify-center text-amber-600 shadow-sm">
                        <Pill size={18} />
                      </div>
                      <div>
                        <div className="font-bold text-slate-950">Warfarin</div>
                        <div className="text-xs font-semibold text-amber-800">3mg daily • Oral • Started March 2026</div>
                      </div>
                    </div>
                    <span className="px-2 py-0.5 bg-amber-100/80 text-amber-800 text-[10px] font-bold rounded uppercase tracking-wider border border-amber-200">Needs Review</span>
                  </div>

                  {patient.medications.map(m => (
                    <div key={m.id} className="flex items-center justify-between p-4 bg-slate-50 border border-slate-200 rounded-xl hover:border-slate-300 transition-colors">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-white border border-slate-200 rounded-full flex items-center justify-center text-hospital-blue shadow-sm">
                          <Pill size={18} />
                        </div>
                        <div>
                          <div className="font-bold text-slate-900">{m.name}</div>
                          <div className="text-xs text-slate-500 font-medium">{m.dose} • {m.frequency} • {m.route} • Started {m.startDate}</div>
                        </div>
                      </div>
                      <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] font-bold rounded uppercase tracking-wider border border-emerald-100">Active</span>
                    </div>
                  ))}
                </div>
              </section>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* Allergies Summary */}
              <section className="lg:col-span-1 bg-white p-6 border border-slate-200 rounded-xl shadow-sm">
                <div className="flex items-center gap-2 mb-4 pb-2 border-b border-slate-100">
                  <AlertTriangle size={18} className="text-hospital-red" />
                  <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Allergies</h3>
                </div>
                <div className="p-4 bg-red-50/50 border border-red-200 rounded-xl">
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-bold text-hospital-red text-base">Penicillin</span>
                    <span className="px-2.5 py-0.5 bg-hospital-red text-white font-bold text-[10px] uppercase rounded">Severe</span>
                  </div>
                  <p className="text-xs font-semibold text-slate-700 leading-relaxed">
                    Reaction: Anaphylaxis & Severe cutaneous reactions.<br />
                    <span className="text-slate-400 font-mono">Recorded: 2025</span>
                  </p>
                </div>
              </section>

              {/* Recent Clinical Summary */}
              <section className="lg:col-span-2 bg-white p-6 border border-slate-200 rounded-xl shadow-sm">
                <div className="flex items-center gap-2 mb-4 pb-2 border-b border-slate-100">
                  <FileText size={18} className="text-hospital-blue" />
                  <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Recent Clinical Summary</h3>
                </div>
                <div className="space-y-4">
                  <div className="p-4 bg-blue-50/30 border border-blue-100 rounded-xl text-slate-700 text-sm leading-relaxed font-medium">
                    "Patient is currently clinically stable but reports increasing mild fatigue. Primary diagnosis is rate-controlled non-valvular Atrial Fibrillation. Due to a history of myocardial infarction in late 2025 and multiple therapeutic interventions, a complete medication review is initiated. Personalized pharmacogenomic testing ordered to analyze drug sensitivity variants."
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-medium text-slate-500">
                    <div>Primary Caregiver: <span className="text-slate-900 font-bold">Dr. Ahmed Ibrahim</span></div>
                    <div>Last Sync: <span className="text-slate-900 font-mono font-bold">Today 02:07:19 UTC</span></div>
                  </div>
                </div>
              </section>
            </div>
          </div>
        );

      case 'History':
        return (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
            <div className="bg-white p-6 border border-slate-200 rounded-xl shadow-sm">
              <div className="flex items-center justify-between mb-6 pb-2 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <History size={18} className="text-hospital-blue" />
                  <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Patient History Timeline</h3>
                </div>
                <span className="text-xs font-bold text-hospital-blue bg-blue-50 px-3 py-1 rounded-full border border-blue-100">Multi-Hospital Journey</span>
              </div>

              {/* Clinical Timeline Loop */}
              <div className="relative pl-6 sm:pl-8 border-l-2 border-slate-200 space-y-8 ml-4">
                
                {/* Event 1 */}
                <div className="relative">
                  <div className="absolute -left-[41px] sm:-left-[49px] top-1.5 w-8 h-8 rounded-full border-2 border-yellow-200 bg-yellow-50 flex items-center justify-center text-hospital-yellow">
                    <ClipboardList size={14} />
                  </div>
                  <div>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2">
                      <span className="text-xs font-bold text-slate-400 font-mono uppercase">July 18, 2026</span>
                      <span className="px-2 py-0.5 bg-yellow-50 border border-yellow-100 text-hospital-yellow text-[10px] font-bold rounded uppercase w-fit">Medication Assessment</span>
                    </div>
                    <h4 className="text-base font-bold text-slate-900">Reviewed Warfarin Prescription</h4>
                    <div className="text-xs font-medium text-slate-500 mt-0.5">Lagos Heart Institute • Dr. Sarah Ade (Cardiology)</div>
                    <p className="text-sm text-slate-600 mt-2 bg-slate-50 p-3 rounded-lg border border-slate-200">
                      Initiated clinical compatibility analysis. Dose adjustment consideration recommended based on metabolic pathways and borderline elevated INR profile.
                    </p>
                  </div>
                </div>

                {/* Event 2 */}
                <div className="relative">
                  <div className="absolute -left-[41px] sm:-left-[49px] top-1.5 w-8 h-8 rounded-full border-2 border-blue-200 bg-blue-50 flex items-center justify-center text-hospital-blue">
                    <FlaskConical size={14} />
                  </div>
                  <div>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2">
                      <span className="text-xs font-bold text-slate-400 font-mono uppercase">June 05, 2026</span>
                      <span className="px-2 py-0.5 bg-blue-50 border border-blue-100 text-hospital-blue text-[10px] font-bold rounded uppercase w-fit">Laboratory Investigation</span>
                    </div>
                    <h4 className="text-base font-bold text-slate-900">INR & Kidney Function Panel</h4>
                    <div className="text-xs font-medium text-slate-500 mt-0.5">University Medical Center • Clinical Laboratories</div>
                    <p className="text-sm text-slate-600 mt-2 bg-slate-50 p-3 rounded-lg border border-slate-200">
                      INR results evaluated at <span className="font-bold text-hospital-red">2.9</span> (elevated, upper therapeutic boundary). Kidney panel indicates normal creatinine levels and eGFR of 85 mL/min/1.73m².
                    </p>
                  </div>
                </div>

                {/* Event 3 */}
                <div className="relative">
                  <div className="absolute -left-[41px] sm:-left-[49px] top-1.5 w-8 h-8 rounded-full border-2 border-emerald-200 bg-emerald-50 flex items-center justify-center text-hospital-green">
                    <Activity size={14} />
                  </div>
                  <div>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2">
                      <span className="text-xs font-bold text-slate-400 font-mono uppercase">March 12, 2026</span>
                      <span className="px-2 py-0.5 bg-emerald-50 border border-emerald-100 text-hospital-green text-[10px] font-bold rounded uppercase w-fit">Clinical Encounter</span>
                    </div>
                    <h4 className="text-base font-bold text-slate-900">Diagnosis of Atrial Fibrillation</h4>
                    <div className="text-xs font-medium text-slate-500 mt-0.5">Lagos Heart Institute • Dr. Ahmed Ibrahim (Cardiologist)</div>
                    <p className="text-sm text-slate-600 mt-2 bg-slate-50 p-3 rounded-lg border border-slate-200">
                      Patient presented with sudden-onset palpitations. ECG confirmed Atrial Fibrillation. Initiated anticoagulation prophylaxis with Warfarin 3mg daily to mitigate thromboembolic risks.
                    </p>
                  </div>
                </div>

                {/* Event 4 */}
                <div className="relative">
                  <div className="absolute -left-[41px] sm:-left-[49px] top-1.5 w-8 h-8 rounded-full border-2 border-red-200 bg-red-50 flex items-center justify-center text-hospital-red">
                    <Pill size={14} />
                  </div>
                  <div>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2">
                      <span className="text-xs font-bold text-slate-400 font-mono uppercase">January 20, 2026</span>
                      <span className="px-2 py-0.5 bg-red-50 border border-red-100 text-hospital-red text-[10px] font-bold rounded uppercase w-fit">Prescription Event</span>
                    </div>
                    <h4 className="text-base font-bold text-slate-900">Aspirin Discontinued</h4>
                    <div className="text-xs font-medium text-slate-500 mt-0.5">University Teaching Hospital • Emergency Department</div>
                    <p className="text-sm text-slate-600 mt-2 bg-slate-50 p-3 rounded-lg border border-slate-200">
                      Aspirin 81mg discontinued following mild clinical bleeding symptoms (epistaxis and hematuria). Decision made to suspend standard dual antiplatelet prophylaxis temporarily.
                    </p>
                  </div>
                </div>

              </div>
            </div>
          </div>
        );

      case 'Vitals':
        return (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Blood Pressure */}
              <div className="bg-white p-6 border border-slate-200 rounded-xl shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Blood Pressure</div>
                    <div className="text-2xl font-bold text-slate-900 mt-1">128/82 <span className="text-xs text-slate-400 font-medium">mmHg</span></div>
                  </div>
                  <span className="px-2.5 py-1 bg-emerald-50 text-emerald-700 text-xs font-bold rounded uppercase">Controlled</span>
                </div>
                <div className="py-4 flex justify-center bg-slate-50/50 rounded-lg border border-slate-100">
                  <TrendLine values={[145, 138, 132, 128]} stroke="#10b981" />
                </div>
                <div className="flex justify-between text-[10px] text-slate-400 font-mono font-bold mt-2 px-1">
                  <span>Jan</span>
                  <span>Mar</span>
                  <span>May</span>
                  <span>Jul</span>
                </div>
              </div>

              {/* Heart Rate */}
              <div className="bg-white p-6 border border-slate-200 rounded-xl shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Heart Rate</div>
                    <div className="text-2xl font-bold text-slate-900 mt-1">72 <span className="text-xs text-slate-400 font-medium">bpm</span></div>
                  </div>
                  <span className="px-2.5 py-1 bg-blue-50 text-hospital-blue text-xs font-bold rounded uppercase">Rate Controlled</span>
                </div>
                <div className="py-4 flex justify-center bg-slate-50/50 rounded-lg border border-slate-100">
                  <TrendLine values={[88, 80, 75, 72]} stroke="#2563eb" />
                </div>
                <div className="flex justify-between text-[10px] text-slate-400 font-mono font-bold mt-2 px-1">
                  <span>Jan</span>
                  <span>Mar</span>
                  <span>May</span>
                  <span>Jul</span>
                </div>
              </div>

              {/* Weight */}
              <div className="bg-white p-6 border border-slate-200 rounded-xl shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Weight</div>
                    <div className="text-2xl font-bold text-slate-900 mt-1">68 <span className="text-xs text-slate-400 font-medium">kg</span></div>
                  </div>
                  <span className="px-2.5 py-1 bg-slate-50 text-slate-500 text-xs font-bold rounded uppercase">Stable</span>
                </div>
                <div className="py-4 flex justify-center bg-slate-50/50 rounded-lg border border-slate-100">
                  <TrendLine values={[69.5, 68.8, 68.2, 68]} stroke="#64748b" />
                </div>
                <div className="flex justify-between text-[10px] text-slate-400 font-mono font-bold mt-2 px-1">
                  <span>Jan</span>
                  <span>Mar</span>
                  <span>May</span>
                  <span>Jul</span>
                </div>
              </div>

              {/* Temperature */}
              <div className="bg-white p-6 border border-slate-200 rounded-xl shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Temperature</div>
                    <div className="text-2xl font-bold text-slate-900 mt-1">36.8 <span className="text-xs text-slate-400 font-medium">°C</span></div>
                  </div>
                  <span className="px-2.5 py-1 bg-emerald-50 text-emerald-700 text-xs font-bold rounded uppercase">Normal</span>
                </div>
                <div className="py-4 flex justify-center bg-slate-50/50 rounded-lg border border-slate-100">
                  <TrendLine values={[36.5, 36.7, 36.6, 36.8]} stroke="#10b981" />
                </div>
                <div className="flex justify-between text-[10px] text-slate-400 font-mono font-bold mt-2 px-1">
                  <span>Jan</span>
                  <span>Mar</span>
                  <span>May</span>
                  <span>Jul</span>
                </div>
              </div>

            </div>
          </div>
        );

      case 'Labs':
        return (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
            <div className="bg-white p-6 border border-slate-200 rounded-xl shadow-sm">
              <div className="flex items-center gap-2 mb-6 pb-2 border-b border-slate-100">
                <FlaskConical size={18} className="text-hospital-blue" />
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Clinical Biomarkers & Lab Results</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* INR */}
                <div className="p-5 border border-slate-200 rounded-xl bg-slate-50 hover:bg-white transition-all">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">INR (Anticoagulation Metric)</div>
                      <div className="text-3xl font-light text-slate-900 mt-1">2.1</div>
                    </div>
                    <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 font-bold text-[10px] rounded border border-emerald-100 uppercase">Within Target</span>
                  </div>
                  <div className="text-xs font-semibold text-slate-500 mb-4">Therapeutic Target: 2.0 - 3.0</div>
                  <div className="py-2 flex justify-center bg-white rounded border border-slate-100">
                    <TrendLine values={[1.2, 2.1, 2.5, 2.1]} stroke="#10b981" />
                  </div>
                </div>

                {/* LDL */}
                <div className="p-5 border border-slate-200 rounded-xl bg-slate-50 hover:bg-white transition-all">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">LDL Cholesterol</div>
                      <div className="text-3xl font-bold text-hospital-red mt-1">110 <span className="text-xs text-slate-400 font-medium">mg/dL</span></div>
                    </div>
                    <span className="px-2 py-0.5 bg-red-50 text-hospital-red font-bold text-[10px] rounded border border-red-100 uppercase">Elevated</span>
                  </div>
                  <div className="text-xs font-semibold text-slate-500 mb-4">Cardiac Target: &lt; 70 mg/dL</div>
                  <div className="py-2 flex justify-center bg-white rounded border border-slate-100">
                    <TrendLine values={[140, 128, 115, 110]} stroke="#ef4444" />
                  </div>
                </div>

                {/* Kidney panel */}
                <div className="p-5 border border-slate-200 rounded-xl bg-slate-50 hover:bg-white transition-all">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">eGFR (Kidney Function)</div>
                      <div className="text-3xl font-light text-slate-900 mt-1">85 <span className="text-xs text-slate-400 font-medium">mL/min/1.73m²</span></div>
                    </div>
                    <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 font-bold text-[10px] rounded border border-emerald-100 uppercase">Normal</span>
                  </div>
                  <div className="text-xs font-semibold text-slate-500 mb-4">Reference range: &gt; 60</div>
                  <div className="py-2 flex justify-center bg-white rounded border border-slate-100">
                    <TrendLine values={[82, 84, 83, 85]} stroke="#10b981" />
                  </div>
                </div>

                {/* Liver function ALT */}
                <div className="p-5 border border-slate-200 rounded-xl bg-slate-50 hover:bg-white transition-all">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">ALT (Liver Enzyme)</div>
                      <div className="text-3xl font-light text-slate-900 mt-1">24 <span className="text-xs text-slate-400 font-medium">U/L</span></div>
                    </div>
                    <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 font-bold text-[10px] rounded border border-emerald-100 uppercase">Normal</span>
                  </div>
                  <div className="text-xs font-semibold text-slate-500 mb-4">Reference range: 7 - 56 U/L</div>
                  <div className="py-2 flex justify-center bg-white rounded border border-slate-100">
                    <TrendLine values={[28, 26, 25, 24]} stroke="#10b981" />
                  </div>
                </div>

              </div>
            </div>
          </div>
        );

      case 'Medications':
        return (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
            <div className="bg-white p-6 border border-slate-200 rounded-xl shadow-sm">
              <div className="flex items-center gap-2 mb-6 pb-2 border-b border-slate-100">
                <Pill size={18} className="text-hospital-blue" />
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Complete Medication Journey</h3>
              </div>

              <div className="space-y-6">
                
                {/* Active Section */}
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Active Regimen</h4>
                  <div className="space-y-3">
                    <div className="p-4 border border-slate-200 rounded-xl bg-slate-50 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-slate-300 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-white border border-slate-200 rounded-full flex items-center justify-center text-hospital-blue shadow-sm">
                          <Pill size={18} />
                        </div>
                        <div>
                          <div className="font-bold text-slate-900">Warfarin</div>
                          <div className="text-sm text-slate-600 font-medium">3mg Daily • Oral • AFib Management</div>
                        </div>
                      </div>
                      <div className="text-left sm:text-right text-xs">
                        <div>Prescribed by: <span className="font-bold text-slate-800">Dr. Ahmed Ibrahim</span></div>
                        <div className="text-slate-400 font-mono mt-0.5">Started: 2026-03-12</div>
                      </div>
                    </div>

                    <div className="p-4 border border-slate-200 rounded-xl bg-slate-50 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-slate-300 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-white border border-slate-200 rounded-full flex items-center justify-center text-hospital-blue shadow-sm">
                          <Pill size={18} />
                        </div>
                        <div>
                          <div className="font-bold text-slate-900">Atorvastatin</div>
                          <div className="text-sm text-slate-600 font-medium">40mg Daily • Oral • Hyperlipidemia</div>
                        </div>
                      </div>
                      <div className="text-left sm:text-right text-xs">
                        <div>Prescribed by: <span className="font-bold text-slate-800">Dr. Sarah Ade</span></div>
                        <div className="text-slate-400 font-mono mt-0.5">Started: 2025-11-20</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Discontinued Section */}
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Discontinued History</h4>
                  <div className="p-4 border border-red-200 rounded-xl bg-red-50/20 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-white border border-red-100 rounded-full flex items-center justify-center text-hospital-red shadow-sm">
                        <Pill size={18} />
                      </div>
                      <div>
                        <div className="font-bold text-slate-900">Aspirin</div>
                        <div className="text-sm text-slate-600 font-medium">81mg Daily • Oral • Discontinued</div>
                      </div>
                    </div>
                    <div className="text-left sm:text-right text-xs">
                      <div className="text-hospital-red font-bold">Reason: Bleeding concern</div>
                      <div className="text-slate-400 font-mono mt-0.5">Duration: Nov 20, 2025 - Jan 20, 2026</div>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>
        );

      case 'Allergies':
        return (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
            <div className="bg-white p-6 border border-slate-200 rounded-xl shadow-sm">
              <div className="flex items-center gap-2 mb-6 pb-2 border-b border-slate-100">
                <AlertTriangle size={18} className="text-hospital-red" />
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Patient Allergy Registry</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                <div className="p-5 border border-red-200 bg-red-50/30 rounded-xl relative overflow-hidden">
                  <div className="absolute right-4 top-4 text-hospital-red/15"><AlertTriangle size={64} /></div>
                  <div className="flex justify-between items-start mb-3">
                    <span className="font-bold text-lg text-hospital-red">Penicillin</span>
                    <span className="px-2.5 py-0.5 bg-hospital-red text-white font-bold text-[10px] uppercase rounded">Severe / Critical</span>
                  </div>
                  <div className="space-y-2 text-xs font-semibold text-slate-700 leading-relaxed z-10 relative">
                    <div><span className="text-slate-400">Reaction Type:</span> Anaphylaxis & Cutaneous swelling</div>
                    <div><span className="text-slate-400">Recorded By:</span> Lagos Emergency Medical Services</div>
                    <div><span className="text-slate-400">Date Logged:</span> October 15, 2025</div>
                  </div>
                </div>

                <div className="p-5 border border-slate-200 bg-slate-50/50 rounded-xl relative overflow-hidden">
                  <div className="absolute right-4 top-4 text-slate-300/20"><AlertTriangle size={64} /></div>
                  <div className="flex justify-between items-start mb-3">
                    <span className="font-bold text-lg text-slate-900">Sulfa Drugs</span>
                    <span className="px-2.5 py-0.5 bg-slate-200 text-slate-700 font-bold text-[10px] uppercase rounded">Mild</span>
                  </div>
                  <div className="space-y-2 text-xs font-semibold text-slate-700 leading-relaxed z-10 relative">
                    <div><span className="text-slate-400">Reaction Type:</span> Mild localized skin rash</div>
                    <div><span className="text-slate-400">Recorded By:</span> Dr. Ahmed Ibrahim</div>
                    <div><span className="text-slate-400">Date Logged:</span> August 22, 2021</div>
                  </div>
                </div>

              </div>
            </div>
          </div>
        );

      case 'Notes':
        return (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
            
            {/* Notes Header with action */}
            <div className="flex justify-between items-center bg-white p-6 border border-slate-200 rounded-xl shadow-sm">
              <div>
                <h3 className="text-base font-bold text-slate-900">Physician Clinical Notes</h3>
                <p className="text-xs text-slate-500 mt-0.5">View and append official documentation to the patient record.</p>
              </div>
              <button 
                onClick={() => setShowNoteForm(!showNoteForm)}
                className="bg-hospital-blue text-white px-4 py-2 rounded-lg text-xs font-bold hover:bg-blue-800 transition-colors flex items-center gap-1.5"
              >
                {showNoteForm ? 'Cancel Note' : 'Add New Note'}
              </button>
            </div>

            {/* Note Entry Form */}
            {showNoteForm && (
              <motion.section 
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white p-6 border border-hospital-blue rounded-xl shadow-md"
              >
                <div className="flex items-center gap-2 mb-4 pb-2 border-b border-slate-100">
                  <ClipboardList size={16} className="text-hospital-blue" />
                  <h4 className="text-xs font-bold text-hospital-blue uppercase tracking-widest">New Progress Note Form</h4>
                </div>
                <form onSubmit={handleAddNoteSubmit} className="space-y-4">
                  <div>
                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1 block">Note Title</label>
                    <input 
                      type="text" 
                      required
                      placeholder="e.g., Cardiology Progress Evaluation"
                      className="w-full px-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-hospital-blue font-medium"
                      value={newNote.title}
                      onChange={(e) => setNewNote({ ...newNote, title: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1 block">Clinical Observation</label>
                    <textarea 
                      required
                      placeholder="What observations or symptoms are noted..."
                      className="w-full px-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-hospital-blue h-20"
                      value={newNote.observation}
                      onChange={(e) => setNewNote({ ...newNote, observation: e.target.value })}
                    />
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1 block">Assessment</label>
                      <textarea 
                        placeholder="Current clinical evaluation..."
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-hospital-blue h-20"
                        value={newNote.assessment}
                        onChange={(e) => setNewNote({ ...newNote, assessment: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1 block">Plan</label>
                      <textarea 
                        placeholder="Planned actions or interventions..."
                        className="w-full px-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-hospital-blue h-20"
                        value={newNote.plan}
                        onChange={(e) => setNewNote({ ...newNote, plan: e.target.value })}
                      />
                    </div>
                  </div>
                  <button 
                    type="submit" 
                    className="w-full bg-hospital-blue text-white py-3 rounded-lg text-sm font-bold hover:bg-blue-800 transition-colors"
                  >
                    Save & Append to EHR Chart
                  </button>
                </form>
              </motion.section>
            )}

            {/* Note Feed */}
            <div className="space-y-4">
              {notes.map(note => (
                <div key={note.id} className="bg-white p-6 border border-slate-200 rounded-xl shadow-sm hover:border-slate-300 transition-colors">
                  <div className="flex justify-between items-start mb-4 pb-2 border-b border-slate-100">
                    <div>
                      <h4 className="text-base font-bold text-slate-900">{note.title}</h4>
                      <div className="text-xs font-semibold text-slate-500 mt-0.5">{note.author} ({note.specialty})</div>
                    </div>
                    <span className="text-xs font-bold text-slate-400 font-mono">{note.date}</span>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <span className="text-[10px] font-bold text-hospital-blue uppercase tracking-wider block mb-1">Clinical Observation</span>
                      <p className="text-xs text-slate-700 leading-relaxed font-medium bg-slate-50 p-2.5 rounded border border-slate-100">"{note.observation}"</p>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                      <div>
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Clinical Assessment</span>
                        <p className="text-xs text-slate-600 leading-relaxed">{note.assessment}</p>
                      </div>
                      <div>
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Therapeutic Plan</span>
                        <p className="text-xs text-slate-600 leading-relaxed">{note.plan}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

          </div>
        );

      case 'Genomic Profile':
        return (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
            <div className="bg-white p-6 border border-slate-200 rounded-xl shadow-sm">
              <div className="flex items-center justify-between mb-6 pb-2 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <Zap size={18} className="text-hospital-blue" />
                  <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Patient Pharmacogenomic Profile</h3>
                </div>
                <span className="text-xs font-bold text-slate-400">純粹生物特徵 (Purely Biological Data)</span>
              </div>

              <div className="space-y-4">
                
                {/* Variant 1 */}
                <div className="p-5 border border-slate-200 rounded-xl bg-slate-50">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h4 className="font-bold text-lg text-slate-900">CYP2C19</h4>
                      <div className="text-xs font-semibold text-slate-400 font-mono mt-0.5">Variant: *2/*2 (Homozygous Loss-of-Function)</div>
                    </div>
                    <span className="px-2.5 py-0.5 bg-red-50 text-hospital-red border border-red-100 text-[10px] font-bold rounded uppercase">Poor Metabolizer</span>
                  </div>
                  <div className="text-xs font-semibold text-slate-700 leading-relaxed border-t border-slate-200 pt-3">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Biological Characterization</span>
                    No functional CYP2C19 enzyme activity is produced. Affects the biological conversion and bioactivation of all prodrugs requiring CYP2C19 first-pass or second-pass hepatic metabolism.
                  </div>
                </div>

                {/* Variant 2 */}
                <div className="p-5 border border-slate-200 rounded-xl bg-slate-50">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h4 className="font-bold text-lg text-slate-900">SLCO1B1</h4>
                      <div className="text-xs font-semibold text-slate-400 font-mono mt-0.5">Variant: *5/*5 (T/T at c.521T&gt;C)</div>
                    </div>
                    <span className="px-2.5 py-0.5 bg-amber-50 text-amber-700 border border-amber-100 text-[10px] font-bold rounded uppercase">Low Transporter Activity</span>
                  </div>
                  <div className="text-xs font-semibold text-slate-700 leading-relaxed border-t border-slate-200 pt-3">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Biological Characterization</span>
                    Significantly decreased activity of the OATP1B1 hepatic influx transporter. This leads to reduced hepatic drug clearance and elevated plasma levels of specific substrates.
                  </div>
                </div>

                {/* Variant 3 */}
                <div className="p-5 border border-slate-200 rounded-xl bg-slate-50">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h4 className="font-bold text-lg text-slate-900">VKORC1</h4>
                      <div className="text-xs font-semibold text-slate-400 font-mono mt-0.5">Variant: -1639G&gt;A (A/A Homozygous Variant)</div>
                    </div>
                    <span className="px-2.5 py-0.5 bg-yellow-50 text-hospital-yellow border border-yellow-100 text-[10px] font-bold rounded uppercase">High Sensitivity Phenotype</span>
                  </div>
                  <div className="text-xs font-semibold text-slate-700 leading-relaxed border-t border-slate-200 pt-3">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Biological Characterization</span>
                    Reduced basal VKORC1 expression. Biological pathways exhibit heightened pharmacological sensitivity to Vitamin K antagonist agents.
                  </div>
                </div>

              </div>

              <div className="mt-6 p-4 bg-slate-100 border border-slate-200 rounded-xl flex items-start gap-2.5 text-xs text-slate-500 font-medium leading-relaxed">
                <Info size={16} className="text-slate-400 shrink-0 mt-0.5" />
                <span>Notice: This genomic profile panel displays absolute patient biological and sequencing parameters only. Actual clinical recommendations or drug selection choices are surfaced exclusively during the active Medication Assessment process.</span>
              </div>
            </div>
          </div>
        );

      case 'Assessments':
        return (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
            <div className="bg-white p-6 border border-slate-200 rounded-xl shadow-sm">
              <div className="flex items-center gap-2 mb-6 pb-2 border-b border-slate-100">
                <ShieldAlert size={18} className="text-hospital-blue" />
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Historical GenomixAI Assessments</h3>
              </div>

              <div className="space-y-4">
                
                <div className="p-4 border border-red-200 bg-red-50/20 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <div className="font-bold text-slate-900 text-base">Clopidogrel Compatibility Assessment</div>
                    <div className="text-xs text-slate-500 font-semibold mt-0.5">Evaluated: Today 02:07 UTC • Initiated by: Dr. Sarah Ade</div>
                  </div>
                  <span className="px-3 py-1 bg-red-50 text-hospital-red border border-red-200 text-xs font-bold rounded-full uppercase tracking-wider w-fit">High Risk (Poor Metabolizer)</span>
                </div>

                <div className="p-4 border border-yellow-200 bg-yellow-50/20 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <div className="font-bold text-slate-900 text-base">Warfarin Compatibility Assessment</div>
                    <div className="text-xs text-slate-500 font-semibold mt-0.5">Evaluated: Today 02:07 UTC • Initiated by: Dr. Sarah Ade</div>
                  </div>
                  <span className="px-3 py-1 bg-yellow-50 text-hospital-yellow border border-yellow-200 text-xs font-bold rounded-full uppercase tracking-wider w-fit">Caution (VKORC1 Sensitive)</span>
                </div>

              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col lg:flex-row h-[calc(100vh-48px)] overflow-hidden bg-slate-50">
      {/* Left Panel - Sidebar */}
      <aside className={`${isSidebarOpen ? 'w-full lg:w-64' : 'w-full lg:w-16'} border-b lg:border-b-0 lg:border-r border-slate-200 bg-white flex flex-col transition-all duration-300 ease-in-out z-40 shrink-0`}>
        <div className="p-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between h-[68px]">
          {isSidebarOpen && <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Clinical Chart Navigation</div>}
          <button 
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-1.5 hover:bg-slate-100 rounded text-slate-400 hover:text-slate-600 hidden lg:block transition-colors"
          >
            <ChevronRight size={16} className={`transition-transform duration-300 ${isSidebarOpen ? 'rotate-180' : ''}`} />
          </button>
          <div className="lg:hidden flex gap-2 overflow-x-auto pb-1 no-scrollbar w-full">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3 py-1.5 text-xs rounded-full whitespace-nowrap transition-colors font-semibold border ${activeTab === tab.id ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}
              >
                <tab.icon size={14} />
                <span>{tab.id}</span>
              </button>
            ))}
          </div>
        </div>
        <nav className="hidden lg:flex flex-col flex-1 py-4 overflow-y-auto gap-1 px-3">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all group ${activeTab === tab.id ? 'bg-blue-50 text-hospital-blue font-bold' : 'text-slate-600 font-semibold hover:bg-slate-50 hover:text-slate-900'}`}
            >
              <tab.icon size={18} className={`${activeTab === tab.id ? 'text-hospital-blue animate-pulse' : 'text-slate-400 group-hover:text-slate-600'}`} />
              {isSidebarOpen && <span>{tab.id}</span>}
            </button>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto relative">
        {/* Patient Header */}
        <div className="p-6 border-b border-slate-200 bg-white sticky top-0 z-30 shadow-sm">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h2 className="text-2xl font-bold text-slate-900 tracking-tight">{patient.name}</h2>
                <span className="flex items-center gap-1.5 text-xs font-bold text-emerald-700 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-full uppercase tracking-wider"><CheckCircle2 size={12} /> Active Patient</span>
              </div>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-slate-500 font-medium">
                <span className="text-sm">{patient.age}y / {patient.sex}</span>
                <span className="text-slate-300">|</span>
                <span className="font-mono text-sm">MRN: {patient.mrn}</span>
                <span className="text-slate-300">|</span>
                <span className="text-sm">Risk: <span className="font-bold text-amber-700">Medication Review Required</span></span>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
              <button 
                onClick={onAddMedication}
                className="flex-1 md:flex-none bg-hospital-blue text-white px-5 py-2.5 rounded-lg font-bold text-xs flex items-center justify-center gap-1.5 hover:bg-blue-800 transition-colors shadow-sm"
              >
                <Plus size={16} /> New Medication Assessment
              </button>
              <button 
                onClick={() => { setActiveTab('Notes'); setShowNoteForm(true); }}
                className="flex-1 md:flex-none bg-slate-100 text-slate-700 hover:bg-slate-200 px-4 py-2.5 rounded-lg font-bold text-xs transition-colors border border-slate-200"
              >
                Add Clinical Note
              </button>
            </div>
          </div>
        </div>

        {/* Clinical Data Sections */}
        <div className="p-6 max-w-5xl mx-auto">
          {renderTabContent()}
        </div>
      </main>
    </div>
  );
};
// --- Main App ---

export default function App() {
  const [appState, setAppState] = useState<AppState>('LANDING');
  const [authInitialView, setAuthInitialView] = useState<'LOGIN' | 'REQUEST_ACCESS'>('LOGIN');
  const [user, setUser] = useState<any>(null);
  
  const [screen, setScreen] = useState<Screen>('SEARCH');
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [selectedDrug, setSelectedDrug] = useState<DrugInfo | null>(null);
  const [selectedDose, setSelectedDose] = useState<number>(0);
  const [selectedFrequency, setSelectedFrequency] = useState<string>('');
  const [isAddingMed, setIsAddingMed] = useState(false);
  const [showFinal, setShowFinal] = useState(false);

  const handlePatientSelect = (p: Patient) => {
    setSelectedPatient(p);
    setScreen('RETRIEVAL');
  };

  const handleRetrievalComplete = () => {
    setScreen('CHART');
  };

  const handleAddMedication = () => {
    setIsAddingMed(true);
  };

  const handleDrugSelect = (d: DrugInfo, dose: number, frequency: string) => {
    setSelectedDrug(d);
    setSelectedDose(dose);
    setSelectedFrequency(frequency);
    setIsAddingMed(false);
    setScreen('SIMULATION');
  };

  const handleSwitchMed = () => {
    setSelectedDrug(null);
    setIsAddingMed(true);
    setScreen('CHART');
  };

  const handleFinalize = () => {
    setShowFinal(true);
    setScreen('CHART');
    setTimeout(() => setShowFinal(false), 5000);
  };

  if (appState === 'LANDING') {
    return (
      <LandingPage 
        onSignIn={() => {
          setAuthInitialView('LOGIN');
          setAppState('UNAUTHENTICATED');
        }}
        onRequestAccess={() => {
          setAuthInitialView('REQUEST_ACCESS');
          setAppState('UNAUTHENTICATED');
        }}
      />
    );
  }

  if (appState === 'UNAUTHENTICATED') {
    return (
      <Auth 
        initialView={authInitialView}
        onBack={() => setAppState('LANDING')}
        onAuthenticated={(user) => {
          setUser(user);
          setAppState('AUTHENTICATED');
        }} 
      />
    );
  }

  if (user?.role === 'Pharmacist') {
    return (
      <div className="min-h-screen bg-hospital-bg flex flex-col">
        <Header doctorName={user?.name} organization={user?.organization} department={user?.department} />
        <PharmacistWorkspace user={user} onSignOut={() => setAppState('LANDING')} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-hospital-bg flex flex-col">
      <Header doctorName={user?.name} organization={user?.organization} department={user?.department} />

      <div className="flex-1 relative">
        <AnimatePresence mode="wait">
          {screen === 'SEARCH' && (
            <motion.div key="search" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <Dashboard onSelect={handlePatientSelect} user={user} />
            </motion.div>
          )}

          {screen === 'RETRIEVAL' && (
            <motion.div key="retrieval" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <RecordRetrieval onComplete={handleRetrievalComplete} />
            </motion.div>
          )}

          {screen === 'CHART' && selectedPatient && (
            <motion.div key="chart" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              {showFinal && (
                <div className="fixed top-16 left-1/2 -translate-x-1/2 z-[300]">
                  <motion.div 
                    initial={{ y: -20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    className="bg-hospital-green text-white px-6 py-3 rounded-full shadow-xl flex items-center gap-3 font-bold"
                  >
                    <CheckCircle2 size={20} /> Prescription order finalized
                  </motion.div>
                </div>
              )}
              <PatientChart patient={selectedPatient} onAddMedication={handleAddMedication} />
            </motion.div>
          )}

          {screen === 'SIMULATION' && selectedPatient && selectedDrug && (
            <motion.div key="simulation" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 z-50 bg-hospital-bg">
              <MedicationAssessment 
                patient={selectedPatient} 
                drug={selectedDrug}
                initialDose={selectedDose}
                initialFrequency={selectedFrequency}
                onBack={() => setScreen('CHART')}
                onComplete={handleFinalize}
                onModify={handleSwitchMed}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Medication Selection Modal */}
        <AnimatePresence>
          {isAddingMed && (
            <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[150] flex items-center justify-center p-4">
              <motion.div 
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="bg-white w-full max-w-md rounded-lg shadow-2xl border border-hospital-border overflow-hidden"
              >
                <div className="p-4 border-b border-hospital-border flex justify-between items-center bg-hospital-bg/50">
                  <div className="flex items-center gap-2">
                    <Pill size={18} className="text-hospital-blue" />
                    <h3 className="font-bold">New Prescription Entry</h3>
                  </div>
                  <button onClick={() => setIsAddingMed(false)} className="text-hospital-muted hover:text-hospital-text"><X size={20} /></button>
                </div>
                
                <form 
                  className="p-6 space-y-4"
                  onSubmit={(e) => {
                    e.preventDefault();
                    const formData = new FormData(e.currentTarget);
                    const drugName = formData.get('drugName') as string;
                    const doseVal = parseInt(formData.get('dose') as string) || 0;
                    const freqVal = formData.get('frequency') as string;
                    
                    const foundDrug = MOCK_DRUGS.find(d => d.name.toLowerCase() === drugName.toLowerCase()) || {
                      id: 'custom',
                      name: drugName,
                      class: 'Unknown',
                      standardDose: `${doseVal}mg`,
                      indications: []
                    };
                    
                    handleDrugSelect(foundDrug, doseVal, freqVal);
                  }}
                >
                  <div>
                    <label className="text-[10px] font-bold text-hospital-muted uppercase mb-1.5 block tracking-widest">Drug Name</label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-hospital-muted" size={16} />
                      <input 
                        name="drugName"
                        type="text" 
                        required
                        placeholder="Search or enter drug name..." 
                        className="w-full pl-10 pr-4 py-2.5 border border-hospital-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-hospital-blue/20 focus:border-hospital-blue"
                        list="drug-suggestions"
                      />
                      <datalist id="drug-suggestions">
                        {MOCK_DRUGS.map(d => <option key={d.id} value={d.name} />)}
                      </datalist>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="text-[10px] font-bold text-hospital-muted uppercase mb-1.5 block tracking-widest">Dose (mg)</label>
                      <input 
                        name="dose"
                        type="number" 
                        required
                        placeholder="e.g. 75" 
                        className="w-full px-4 py-2.5 border border-hospital-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-hospital-blue/20 focus:border-hospital-blue"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-bold text-hospital-muted uppercase mb-1.5 block tracking-widest">Frequency</label>
                      <select 
                        name="frequency"
                        className="w-full px-3 py-2.5 border border-hospital-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-hospital-blue/20 focus:border-hospital-blue"
                      >
                        <option>Once Daily</option>
                        <option>BID (Twice Daily)</option>
                        <option>TID (Three times Daily)</option>
                        <option>PRN</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="text-[10px] font-bold text-hospital-muted uppercase mb-1.5 block tracking-widest">Duration</label>
                    <input 
                      name="duration"
                      type="text" 
                      placeholder="e.g. 30 days, Indefinite" 
                      className="w-full px-4 py-2.5 border border-hospital-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-hospital-blue/20 focus:border-hospital-blue"
                    />
                  </div>

                  <button 
                    type="submit"
                    className="w-full bg-hospital-blue text-white py-3 rounded-lg font-bold text-sm hover:bg-blue-700 transition-colors mt-4"
                  >
                    Enter Prescription
                  </button>
                </form>
              </motion.div>
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

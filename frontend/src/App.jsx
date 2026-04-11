

import React, { useState, useEffect, useMemo } from 'react';
import Login from './components/Login';
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
	Zap
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { MOCK_PATIENTS, MOCK_DRUGS } from './constants';

// Environment configuration for backend API
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ...PASTE THE FULL CONTENTS OF App.tsx HERE, REMOVING ALL TYPE ANNOTATIONS AND INTERFACES...


const Header = ({ doctorName, onLogout }) => {
  return (
    <header className="sticky top-0 z-40 border-b border-hospital-border bg-white/95 backdrop-blur-sm">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-hospital-blue text-white font-bold shadow-sm">
            G
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-sm font-bold tracking-wide text-hospital-blue">GENOMIXAI</span>
            <span className="text-[11px] font-medium uppercase tracking-[0.22em] text-hospital-muted">EHR V4.2</span>
          </div>
        </div>

        <div className="flex items-center gap-4 sm:gap-5">
          <button className="relative rounded-full p-2 text-hospital-muted transition hover:bg-hospital-bg hover:text-hospital-text" aria-label="Notifications">
            <Bell size={18} />
            <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-hospital-red ring-2 ring-white" />
          </button>
          <div className="hidden sm:block text-right leading-tight">
            <div className="text-sm font-semibold text-hospital-text">{doctorName}</div>
            <div className="text-[11px] text-hospital-muted">Cardiology Department</div>
          </div>
          <button onClick={onLogout} className="flex h-10 w-10 items-center justify-center rounded-full border border-hospital-border bg-white text-hospital-blue transition hover:bg-hospital-bg" aria-label="Profile / logout">
            <User size={18} />
          </button>
        </div>
      </div>
    </header>
  );
};

const PatientSearch = ({ patients, onSelect }) => {
  const [query, setQuery] = useState('');
  const recentPatients = [...patients].sort((left, right) => {
    const leftDate = new Date(left.lastVisit || 0).getTime();
    const rightDate = new Date(right.lastVisit || 0).getTime();
    return rightDate - leftDate;
  }).slice(0, 5);

  const filteredPatients = recentPatients.filter((patient) => {
    const text = `${patient.name} ${patient.mrn} ${patient.conditions.join(' ')}`.toLowerCase();
    return text.includes(query.toLowerCase());
  });

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-10">
      <div className="text-center">
        <h1 className="text-3xl sm:text-4xl font-light tracking-tight text-hospital-text">
          GenomixAI <span className="font-bold text-hospital-blue">Clinical Portal</span>
        </h1>
        <p className="mt-3 text-sm sm:text-base text-hospital-muted">
          Secure Electronic Health Record & Decision Support System
        </p>
      </div>

      <div className="mt-8 sm:mt-10 flex justify-center">
        <div className="relative w-full max-w-3xl">
          <Search className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-hospital-muted" size={20} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search patient by Name, ID, or MRN"
            className="w-full rounded-2xl border border-hospital-border bg-white px-12 py-4 text-base shadow-[0_8px_24px_rgba(15,23,42,0.08)] outline-none transition focus:border-hospital-blue focus:ring-4 focus:ring-hospital-blue/10"
          />
        </div>
      </div>

      <div className="mt-10 overflow-hidden rounded-2xl border border-hospital-border bg-white shadow-[0_12px_36px_rgba(15,23,42,0.08)]">
        <div className="flex items-center justify-between border-b border-hospital-border px-4 py-4 sm:px-5">
          <div className="text-xs font-bold uppercase tracking-[0.22em] text-hospital-muted">Recent Patients</div>
          <div className="text-[11px] italic text-hospital-muted">Showing last 5 patients</div>
        </div>

        <div className="overflow-x-auto">
          <table className="ehr-table min-w-full text-sm">
            <thead>
              <tr>
                <th>Name</th>
                <th>Age / Sex</th>
                <th>MRN</th>
                <th>Last Visit</th>
                <th>Primary Diagnosis</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredPatients.map((patient) => (
                <tr key={patient.id} className="cursor-pointer" onClick={() => onSelect(patient)}>
                  <td className="font-semibold text-hospital-blue">{patient.name}</td>
                  <td>{patient.age}y / {patient.sex}</td>
                  <td className="mono-data">{patient.mrn}</td>
                  <td className="mono-data">{patient.lastVisit}</td>
                  <td>{patient.conditions?.[0] || 'General Medicine'}</td>
                  <td>
                    <span className={`inline-flex rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] ${patient.status === 'Active' ? 'bg-emerald-100 text-emerald-700' : 'bg-zinc-100 text-zinc-600'}`}>
                      {patient.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredPatients.length === 0 && (
          <div className="px-5 py-8 text-center text-sm text-hospital-muted">
            No patients match this search.
          </div>
        )}
      </div>
    </div>
  );
};



const RecordRetrieval = ({ onComplete }) => {
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
      setStep((s) => {
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
    <div className="fixed inset-0 bg-hospital-bg z-100 flex flex-col items-center justify-center">
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

const PatientChart = ({ patient, onAddMedication }) => {
  const [activeTab, setActiveTab] = useState('Summary');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isInsightsOpen, setIsInsightsOpen] = useState(true);

  const sortedLabs = [...(patient.labs || [])].sort((left, right) => {
    const leftDate = new Date(left.date || 0).getTime();
    const rightDate = new Date(right.date || 0).getTime();
    return rightDate - leftDate;
  });
  const latestLabs = sortedLabs.slice(0, 3);
  const abnormalLabs = sortedLabs.filter((lab) => lab.status !== 'Normal');
  const activeMedications = (patient.medications || []).filter((medication) => medication.status !== 'Discontinued');
  const allergyList = patient.allergies || [];
  const genomicVariants = patient.genomicProfile?.variants || [];

  const buildAllergyInsight = (allergy) => {
    const allergyName = allergy.toLowerCase();

    if (allergyName.includes('aspirin')) {
      return 'Documented salicylate allergy. Avoid aspirin-containing products and review antiplatelet alternatives carefully before prescribing.';
    }

    if (allergyName.includes('penicillin')) {
      return 'Beta-lactam allergy documented. Confirm reaction history before selecting any penicillin-class or closely related antibiotic.';
    }

    if (allergyName.includes('sulfa')) {
      return 'Sulfonamide allergy recorded. Check for prior reaction severity and avoid unnecessary sulfonamide exposure.';
    }

    return 'Documented allergy on file. Verify reaction type, severity, and prior exposure history before order entry.';
  };

  const historySummary = {
    timeline: [
      `Last documented visit: ${patient.lastVisit || 'Not available'}`,
      `Current problem list: ${(patient.conditions || []).join(', ') || 'No active conditions recorded'}`,
      `Medication snapshot: ${activeMedications.slice(0, 3).map((medication) => `${medication.name} ${medication.dose} ${medication.frequency}`).join(' • ') || 'No active medications recorded'}`,
      `Recent laboratory pattern: ${sortedLabs.map((lab) => `${lab.name} ${lab.status.toLowerCase()}`).join(' • ') || 'No laboratory history available'}`
    ],
    assessment: patient.clinicalNotes || 'Chart review suggests ongoing monitoring is needed to keep the care plan aligned with the active problem list and medication history.'
  };

  const buildProgressNote = () => [
    'Subjective: Patient remains under active cardiometabolic follow-up and is being reviewed for medication optimization.',
    `Objective: ${abnormalLabs.length ? `Notable laboratory findings include ${abnormalLabs.map((lab) => `${lab.name} (${lab.status.toLowerCase()})`).join(', ')}.` : 'No clearly abnormal laboratory results are flagged in the most recent panel.'} Current medications include ${activeMedications.map((medication) => medication.name).join(', ') || 'no active medications listed'}.`,
    `Assessment: ${(patient.conditions || []).join(', ') || 'Ongoing chronic condition management'} with genomic context of ${genomicVariants.map((variant) => `${variant.gene} ${variant.variant}`).join(', ') || 'no genomic data on file'}.`,
    'Plan: Continue close monitoring, reconcile medications before prescribing, and escalate to the treating team if new symptoms, adverse reactions, or laboratory deterioration appear.'
  ];


  const tabs = [
    { id: 'Summary', icon: FileText },
    { id: 'Vitals', icon: Activity },
    { id: 'Labs', icon: FlaskConical },
    { id: 'Medications', icon: Pill },
    { id: 'Allergies', icon: AlertTriangle },
    { id: 'History', icon: History },
    { id: 'Notes', icon: ClipboardList },
  ];

  function renderTabContent() {
    switch (activeTab) {
      case 'Summary':
        return (
          <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr] animate-in fade-in slide-in-from-bottom-2 duration-500">
            <section className="rounded-2xl border border-hospital-border bg-white p-5 shadow-sm">
              <div className="mb-4 flex items-center gap-2">
                <FileText size={18} className="text-hospital-blue" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-hospital-muted">Patient Summary</h3>
              </div>
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                <div className="rounded-xl bg-hospital-bg/50 p-4">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-hospital-muted">Demographics</div>
                  <div className="mt-2 text-sm font-semibold text-hospital-text">{patient.age}y / {patient.sex}</div>
                  <div className="mt-1 text-xs text-hospital-muted">MRN {patient.mrn}</div>
                  <div className="mt-3 text-[11px] leading-5 text-hospital-muted">{patient.name} is currently being reviewed as an active chart with live medication and genomic data loaded from the backend.</div>
                </div>
                <div className="rounded-xl bg-hospital-bg/50 p-4">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-hospital-muted">Clinical Status</div>
                  <div className="mt-2 text-sm font-semibold text-hospital-text">{patient.status}</div>
                  <div className="mt-1 text-xs text-hospital-muted">Last visit {patient.lastVisit}</div>
                  <div className="mt-3 text-[11px] leading-5 text-hospital-muted">Current plan is centered on longitudinal monitoring, medication reconciliation, and review of lab trends.</div>
                </div>
                <div className="rounded-xl bg-hospital-bg/50 p-4 sm:col-span-2 xl:col-span-1">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-hospital-muted">Clinical Focus</div>
                  <div className="mt-2 text-sm font-semibold text-hospital-text">Therapy review and risk stratification</div>
                  <div className="mt-1 text-xs text-hospital-muted">Latest status is derived from conditions, medications, labs, and genomic profile.</div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {(patient.conditions || []).slice(0, 2).map((condition, index) => (
                      <span key={`${condition}-${index}`} className="rounded-full bg-blue-50 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-hospital-blue">{condition}</span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mt-5">
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-hospital-muted">Active Conditions</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {(patient.conditions || []).map((condition, index) => (
                    <span key={`${condition}-${index}`} className="rounded-full bg-blue-50 px-3 py-1 text-[11px] font-semibold text-hospital-blue">
                      {condition}
                    </span>
                  ))}
                </div>
              </div>
            </section>

            <section className="rounded-2xl border border-hospital-border bg-white p-5 shadow-sm">
              <div className="mb-4 flex items-center gap-2">
                <ShieldAlert size={18} className="text-hospital-blue" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-hospital-muted">Clinical Snapshot</h3>
              </div>
              <div className="space-y-3">
                <div className="rounded-xl border border-hospital-border bg-hospital-bg/40 p-3">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-hospital-muted">Allergies</div>
                  <div className="mt-1 text-sm font-medium text-hospital-text">{allergyList.length ? allergyList.join(', ') : 'No known allergies documented'}</div>
                  <div className="mt-3 space-y-2">
                    {allergyList.length ? allergyList.map((allergy, index) => (
                      <div key={`${allergy}-${index}`} className="rounded-lg bg-white p-3 text-xs leading-5 text-hospital-text border border-hospital-border">
                        <div className="font-semibold text-hospital-blue">{allergy}</div>
                        <div className="mt-1 text-hospital-muted">{buildAllergyInsight(allergy)}</div>
                      </div>
                    )) : (
                      <div className="rounded-lg bg-white p-3 text-xs leading-5 text-hospital-muted border border-hospital-border">
                        No allergy alerts are listed, but clinicians should still verify medication tolerance before prescribing.
                      </div>
                    )}
                  </div>
                </div>
                <div className="rounded-xl border border-hospital-border bg-hospital-bg/40 p-3">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-hospital-muted">Most recent note</div>
                  <div className="mt-1 text-sm text-hospital-text leading-relaxed">{patient.clinicalNotes || historySummary.assessment}</div>
                  <div className="mt-3 rounded-lg bg-white p-3 text-xs leading-5 text-hospital-muted border border-hospital-border">
                    The current note emphasizes medication review, trend monitoring, and follow-up for the active problem list.
                  </div>
                </div>
                <div className="rounded-xl border border-hospital-border bg-hospital-bg/40 p-3">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-hospital-muted">Genomic profile</div>
                  <div className="mt-1 text-sm text-hospital-text">
                    {genomicVariants.length
                      ? genomicVariants.map((variant) => `${variant.gene} ${variant.variant} (${variant.phenotype})`).join(' • ')
                      : 'No genomic data available'}
                  </div>
                </div>
              </div>
            </section>
          </div>
        );
      case 'Vitals':
        return (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 animate-in fade-in slide-in-from-bottom-2 duration-500">
            {sortedLabs.map((lab) => (
              <div key={`${lab.name}-${lab.date}`} className="rounded-2xl border border-hospital-border bg-white p-4 shadow-sm">
                <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-hospital-muted">{lab.name}</div>
                <div className="mt-2 flex items-end gap-1">
                  <span className={`text-3xl font-bold ${lab.status === 'Normal' ? 'text-hospital-text' : 'text-hospital-red'}`}>{lab.value}</span>
                  <span className="pb-1 text-xs text-hospital-muted">{lab.unit || 'units'}</span>
                </div>
                <div className="mt-3 flex items-center justify-between text-[11px] text-hospital-muted">
                  <span>{lab.date}</span>
                  <span className={`rounded-full px-2 py-1 font-bold uppercase tracking-[0.14em] ${lab.status === 'Normal' ? 'bg-emerald-100 text-emerald-700' : lab.status === 'High' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'}`}>
                    {lab.status}
                  </span>
                </div>
                <div className="mt-4 text-xs leading-5 text-hospital-muted">
                  {lab.status === 'Normal'
                    ? `${lab.name} is currently within the expected range and does not require intervention.`
                    : `${lab.name} is outside the expected range and should be reviewed in the context of the active treatment plan.`}
                </div>
              </div>
            ))}
          </div>
        );
      case 'Labs':
        return (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-500">
            <section>
              <div className="flex items-center gap-2 mb-4">
                <FlaskConical size={18} className="text-hospital-blue" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-hospital-muted">Recent Lab Results</h3>
              </div>
              <div className="mb-4 grid gap-3 sm:grid-cols-3">
                <div className="rounded-xl border border-hospital-border bg-white p-4">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-hospital-muted">Total labs</div>
                  <div className="mt-2 text-2xl font-bold text-hospital-text">{sortedLabs.length}</div>
                  <div className="mt-1 text-xs text-hospital-muted">Recent panel reviewed from live patient data</div>
                </div>
                <div className="rounded-xl border border-hospital-border bg-white p-4">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-hospital-muted">Abnormal results</div>
                  <div className="mt-2 text-2xl font-bold text-hospital-red">{abnormalLabs.length}</div>
                  <div className="mt-1 text-xs text-hospital-muted">Requires clinician review</div>
                </div>
                <div className="rounded-xl border border-hospital-border bg-white p-4">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-hospital-muted">Most recent check</div>
                  <div className="mt-2 text-2xl font-bold text-hospital-text">{sortedLabs[0]?.date || 'N/A'}</div>
                  <div className="mt-1 text-xs text-hospital-muted">Latest available result date</div>
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {sortedLabs.map((l, index) => (
                  <div key={`${l.name}-${l.date}-${index}`} className="p-4 border border-hospital-border rounded bg-white shadow-sm hover:border-hospital-blue transition-colors">
                    <div className="text-[10px] text-hospital-muted uppercase font-bold mb-1">{l.name}</div>
                    <div className="flex items-baseline gap-1">
                      <span className={`text-2xl font-bold ${l.status === 'Normal' ? 'text-hospital-text' : 'text-hospital-red'}`}>{l.value}</span>
                      <span className="text-xs text-hospital-muted">{l.unit}</span>
                    </div>
                    <div className="flex justify-between items-center mt-2">
                      <div className="text-[10px] text-hospital-muted italic">{l.date}</div>
                      <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${l.status === 'Normal' ? 'bg-green-50 text-hospital-green' : 'bg-red-50 text-hospital-red'}`}>
                        {l.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 rounded-xl border border-hospital-border bg-hospital-bg/30 p-4 text-xs text-hospital-muted">
                All available lab results are shown here with the most recent data prioritized first.
              </div>
            </section>
          </div>
        );
      case 'Allergies':
        return (
          <div className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr] animate-in fade-in slide-in-from-bottom-2 duration-500">
            <section className="rounded-2xl border border-hospital-border bg-white p-5 shadow-sm">
              <div className="mb-4 flex items-center gap-2">
                <AlertTriangle size={18} className="text-hospital-blue" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-hospital-muted">Allergy Overview</h3>
              </div>
              <div className="rounded-xl bg-hospital-bg/50 p-4">
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-hospital-muted">Total allergies</div>
                <div className="mt-2 text-3xl font-bold text-hospital-text">{allergyList.length}</div>
                <div className="mt-1 text-xs text-hospital-muted">{allergyList.length ? 'Documented allergies require prescription review.' : 'No allergies recorded, but the chart should still be verified before ordering.'}</div>
              </div>
              <div className="mt-4 space-y-3">
                {allergyList.length ? allergyList.map((allergy) => (
                  <div key={allergy} className="rounded-xl border border-hospital-border bg-white p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-hospital-text">{allergy}</div>
                        <div className="text-[11px] text-hospital-muted">Recorded allergy</div>
                      </div>
                      <span className="rounded-full bg-amber-100 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-amber-700">Review before order</span>
                    </div>
                    <p className="mt-3 text-xs leading-5 text-hospital-muted">{buildAllergyInsight(allergy)}</p>
                  </div>
                )) : (
                  <div className="rounded-xl border border-hospital-border bg-white p-4 text-sm text-hospital-muted">No allergy entries are stored for this patient. Document this explicitly if history remains negative.</div>
                )}
              </div>
            </section>

            <section className="rounded-2xl border border-hospital-border bg-white p-5 shadow-sm">
              <div className="mb-4 flex items-center gap-2">
                <ShieldAlert size={18} className="text-hospital-blue" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-hospital-muted">Prescription Safety Notes</h3>
              </div>
              <div className="space-y-3">
                <div className="rounded-xl border border-hospital-border bg-hospital-bg/40 p-4">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-hospital-muted">Current medication relevance</div>
                  <div className="mt-2 text-sm text-hospital-text">{activeMedications.length ? `${activeMedications.map((medication) => medication.name).join(', ')} should be reconciled against each recorded allergy before changing therapy.` : 'No active medications are listed, but allergy reconciliation should still happen before prescribing.'}</div>
                </div>
                <div className="rounded-xl border border-hospital-border bg-hospital-bg/40 p-4">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-hospital-muted">Clinical recommendation</div>
                  <div className="mt-2 text-sm text-hospital-text">Verify reaction type, severity, and timing. If a medication allergy is present, confirm whether the exposure was true hypersensitivity, intolerance, or a historical label.</div>
                </div>
              </div>
            </section>
          </div>
        );
      case 'History':
        return (
          <div className="grid gap-4 lg:grid-cols-[1fr_1fr] animate-in fade-in slide-in-from-bottom-2 duration-500">
            <section className="rounded-2xl border border-hospital-border bg-white p-5 shadow-sm">
              <div className="mb-4 flex items-center gap-2">
                <History size={18} className="text-hospital-blue" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-hospital-muted">Clinical Timeline</h3>
              </div>
              <div className="space-y-3">
                {historySummary.timeline.map((entry, index) => (
                  <div key={index} className="rounded-xl border border-hospital-border bg-hospital-bg/40 p-4 text-sm leading-6 text-hospital-text">
                    {entry}
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-2xl border border-hospital-border bg-white p-5 shadow-sm">
              <div className="mb-4 flex items-center gap-2">
                <ClipboardList size={18} className="text-hospital-blue" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-hospital-muted">Historical Risk Context</h3>
              </div>
              <div className="space-y-3">
                <div className="rounded-xl border border-hospital-border bg-hospital-bg/40 p-4">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-hospital-muted">Conditions on file</div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(patient.conditions || []).map((condition, index) => (
                      <span key={`${condition}-${index}`} className="rounded-full bg-blue-50 px-3 py-1 text-[11px] font-semibold text-hospital-blue">{condition}</span>
                    ))}
                  </div>
                </div>
                <div className="rounded-xl border border-hospital-border bg-hospital-bg/40 p-4">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-hospital-muted">Medication history</div>
                  <div className="mt-2 text-sm text-hospital-text">
                    {patient.medications?.length ? patient.medications.map((medication) => `${medication.name} ${medication.dose} (${medication.status})`).join(' • ') : 'No medication history available'}
                  </div>
                </div>
                <div className="rounded-xl border border-hospital-border bg-hospital-bg/40 p-4">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-hospital-muted">Genomic modifiers</div>
                  <div className="mt-2 text-sm text-hospital-text">
                    {genomicVariants.length ? genomicVariants.map((variant) => `${variant.gene} ${variant.variant} (${variant.phenotype})`).join(' • ') : 'No pharmacogenomic modifiers recorded'}
                  </div>
                </div>
              </div>
            </section>
          </div>
        );
      case 'Notes':
        return (
          <div className="grid gap-4 lg:grid-cols-[1fr_1fr] animate-in fade-in slide-in-from-bottom-2 duration-500">
            <section className="rounded-2xl border border-hospital-border bg-white p-5 shadow-sm">
              <div className="mb-4 flex items-center gap-2">
                <ClipboardList size={18} className="text-hospital-blue" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-hospital-muted">Expanded Clinical Note</h3>
              </div>
              <div className="space-y-3">
                <div className="rounded-xl border border-hospital-border bg-hospital-bg/40 p-4 text-sm leading-6 text-hospital-text">
                  {patient.clinicalNotes || historySummary.assessment}
                </div>
                {buildProgressNote().map((line, index) => (
                  <div key={index} className="rounded-xl border border-hospital-border bg-white p-4 text-sm leading-6 text-hospital-text">
                    {line}
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-2xl border border-hospital-border bg-white p-5 shadow-sm">
              <div className="mb-4 flex items-center gap-2">
                <FileText size={18} className="text-hospital-blue" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-hospital-muted">Documentation Detail</h3>
              </div>
              <div className="space-y-3">
                <div className="rounded-xl border border-hospital-border bg-hospital-bg/40 p-4">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-hospital-muted">Assessment focus</div>
                  <div className="mt-2 text-sm text-hospital-text">Medication safety, problem list review, and lab trend follow-up remain the priority for this chart.</div>
                </div>
                <div className="rounded-xl border border-hospital-border bg-hospital-bg/40 p-4">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-hospital-muted">Next review</div>
                  <div className="mt-2 text-sm text-hospital-text">Reassess after any prescription change, abnormal lab result, or new symptom report.</div>
                </div>
                <div className="rounded-xl border border-hospital-border bg-hospital-bg/40 p-4">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-hospital-muted">Chart completeness</div>
                  <div className="mt-2 text-sm text-hospital-text">The app now fills empty note areas with a generated clinician-style summary so the record never appears blank.</div>
                </div>
              </div>
            </section>
          </div>
        );
      case 'Medications':
        return (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-500">
            <section>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-hospital-border">
                  <thead>
                    <tr>
                      <th className="px-4 py-2">Name</th>
                      <th className="px-4 py-2">Dose & Frequency</th>
                      <th className="px-4 py-2">Route</th>
                      <th className="px-4 py-2">Start Date</th>
                      <th className="px-4 py-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {patient.medications.map(m => (
                      <tr key={m.id}>
                        <td className="font-semibold">{m.name}</td>
                        <td className="mono-data">{m.dose} {m.frequency}</td>
                        <td>{m.route}</td>
                        <td className="mono-data">{m.startDate}</td>
                        <td><span className="text-hospital-green font-bold text-[10px] uppercase">Active</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        );
      default:
        return (
          <div className="flex flex-col items-center justify-center h-64 text-hospital-muted">
            <Info size={48} className="mb-4 opacity-20" />
            <p className="text-sm italic">The {activeTab} module is currently being updated with real-time data.</p>
          </div>
        );
    }
  }

  return (
    <div className="flex flex-col lg:flex-row h-[calc(100vh-48px)] overflow-hidden">
      {/* Left Panel - Sidebar */}
      <aside className={`${isSidebarOpen ? 'w-full lg:w-48' : 'w-full lg:w-14'} border-b lg:border-b-0 lg:border-r border-hospital-border bg-white flex flex-col transition-all duration-300 ease-in-out z-40`}>
        <div className="p-4 border-b border-hospital-border bg-hospital-bg/50 flex items-center justify-between">
          {isSidebarOpen && <div className="text-[10px] font-bold text-hospital-muted uppercase tracking-widest">Navigation</div>}
          <button 
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-1 hover:bg-hospital-border rounded hidden lg:block"
          >
            <ChevronRight size={14} className={`transition-transform duration-300 ${isSidebarOpen ? 'rotate-180' : ''}`} />
          </button>
          <div className="lg:hidden flex gap-2 overflow-x-auto pb-1 no-scrollbar">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3 py-1.5 text-xs rounded-full whitespace-nowrap transition-colors ${activeTab === tab.id ? 'bg-hospital-blue text-white' : 'bg-hospital-bg text-hospital-text'}`}
              >
                <tab.icon size={14} />
                <span>{tab.id}</span>
              </button>
            ))}
          </div>
        </div>
        <nav className="hidden lg:flex flex-col flex-1 py-2 overflow-y-auto">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 text-sm transition-all group ${activeTab === tab.id ? 'bg-hospital-blue text-white' : 'text-hospital-text hover:bg-hospital-bg'}`}
            >
              <tab.icon size={16} className={`${activeTab === tab.id ? 'text-white' : 'text-hospital-muted group-hover:text-hospital-blue'}`} />
              {isSidebarOpen && <span className="font-medium">{tab.id}</span>}
            </button>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto bg-white relative">
        {/* Patient Header */}
        <div className="p-4 sm:p-6 border-b border-hospital-border bg-hospital-bg/30 sticky top-0 z-30 backdrop-blur-md">
          <div className="flex flex-col sm:flex-row justify-between items-start gap-4 mb-4">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-hospital-text">{patient.name}</h2>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1 text-hospital-muted">
                <span className="text-xs">{patient.age}y / {patient.sex}</span>
                <span className="mono-data text-xs">MRN: {patient.mrn}</span>
                <span className="flex items-center gap-1 text-xs"><CheckCircle2 size={14} className="text-hospital-green" /> Active</span>
              </div>
            </div>
            <button 
              onClick={onAddMedication}
              className="w-full sm:w-auto bg-hospital-blue text-white px-6 py-2.5 rounded font-bold text-sm flex items-center justify-center gap-2 hover:bg-blue-700 transition-colors shadow-lg"
            >
              <Plus size={16} /> New Prescription
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {patient.conditions.map(c => (
              <span key={c} className="px-2 py-1 bg-blue-50 text-hospital-blue border border-blue-100 rounded text-[10px] font-semibold uppercase tracking-tight">
                {c}
              </span>
            ))}
          </div>
        </div>

        {/* Clinical Data Sections */}
        <div className="p-4 sm:p-6">
          {renderTabContent()}
        </div>
      </main>
    </div>
  );
};

const SimulationInterface = ({ patient, drug, onBack, onComplete, simulateDrug }) => {
  const [dose, setDose] = useState(75);
  const [frequency, setFrequency] = useState('Once Daily');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [showAlternativesModal, setShowAlternativesModal] = useState(false);

  const defaultSimulation = {
    metabolicActivation: 'Normal',
    clearanceRate: 'Normal',
    expectedEffectiveness: 'High',
    riskLevel: 'Safe',
    suitabilityVerdict: 'Acceptable',
    evaluationSummary: {
      suitability: 'High',
      effectiveness: 'Adequate',
      safety: 'Acceptable'
    },
    clinicalInterpretation: {
      mechanism: 'Standard pharmacological activation and clearance pathways.',
      patientFactors: 'No conflicting genomic or clinical markers detected for this medication.',
      expectedImpact: 'Expected therapeutic response at standard dosage.'
    },
    dosageEvaluation: [
      'Current dose is within standard therapeutic range.',
      'Dose adjustment not indicated based on current profile.'
    ],
    patientHistory: {
      response: 'No prior adverse reactions to this class of medication.',
      insight: 'Patient history supports standard therapeutic approach.'
    },
    riskInterpretation: {
      failure: 'Low',
      adverse: 'Low'
    },
    clinicalConsiderations: [
      'Proceed with standard dosing protocol.',
      'Routine monitoring as per clinical guidelines.'
    ],
    riskBreakdown: {
      effectiveness: 5,
      toxicity: 5,
      interaction: 5
    },
    interpretation: 'Standard metabolic profile. Expected therapeutic response at current dosage.',
    supportingEvidence: {
      pharmacology: 'This medication follows standard Phase I and Phase II metabolic pathways without known significant genomic interference in this patient\'s profile.',
      clinicalHistory: 'Patient has no documented history of adverse reactions to this class of medication and current renal/hepatic markers are within acceptable ranges for standard initiation.',
      causalLink: 'Because the patient\'s history shows no metabolic or clinical contraindications, taking this drug will likely result in the intended therapeutic effect as per standard clinical trial data.',
      references: [
        'Standard Pharmacopoeia Guidelines',
        'Clinical Trial Safety Data',
        'Manufacturer Prescribing Information'
      ]
    },
    alternativeSuggestions: []
  };

  const simulation = useMemo(() => {
    if (drug.name === 'Clopidogrel') {
      return {
        metabolicActivation: 'Reduced',
        clearanceRate: 'Variable',
        expectedEffectiveness: 'Reduced',
        riskLevel: 'High',
        suitabilityVerdict: 'Not Recommended',
        evaluationSummary: {
          suitability: 'Low',
          effectiveness: 'Reduced',
          safety: 'Increased Risk'
        },
        clinicalInterpretation: {
          mechanism: "Clopidogrel is a prodrug that requires activation by CYP2C19. Loss-of-function variants in CYP2C19 reduce the formation of the active metabolite, leading to decreased antiplatelet effect.",
          patientFactors: "This patient has a CYP2C19 loss-of-function variant, which impairs the conversion of clopidogrel to its active form.",
          expectedImpact: "Reduced platelet inhibition and increased risk of adverse cardiovascular events (e.g., stent thrombosis)."
        },
        dosageEvaluation: [
          "Standard dosing is unlikely to achieve therapeutic effect.",
          "Dose escalation is not recommended due to unpredictable response."
        ],
        patientHistory: {
          response: "No prior clopidogrel exposure recorded.",
          insight: "Genotype suggests poor metabolizer status."
        },
        riskInterpretation: {
          failure: 'High',
          adverse: 'Moderate'
        },
        clinicalConsiderations: [
          "Consider alternative P2Y12 inhibitors not affected by CYP2C19 status (e.g., Prasugrel, Ticagrelor).",
          "Monitor for signs of recurrent ischemia."
        ],
        riskBreakdown: {
          effectiveness: 10,
          toxicity: 20,
          interaction: 30
        },
        interpretation: "Clopidogrel is not recommended for patients with CYP2C19 loss-of-function alleles due to reduced efficacy.",
        supportingEvidence: {
          pharmacology: "Clopidogrel is a thienopyridine antiplatelet agent requiring hepatic bioactivation via CYP2C19.",
          clinicalHistory: "Genetic testing confirms CYP2C19 loss-of-function variant.",
          causalLink: "Reduced active metabolite formation leads to decreased platelet inhibition and higher risk of thrombotic events.",
          references: [
            "FDA Drug Safety Communication: Reduced effectiveness of Plavix (clopidogrel) in patients who are poor metabolizers of the drug.",
            "Clinical Pharmacogenetics Implementation Consortium (CPIC) Guidelines."
          ]
        },
        alternativeSuggestions: [
          {
            drugName: "Prasugrel",
            class: "P2Y12 Inhibitor (Thienopyridine)",
            recommendedDose: "10mg",
            frequency: "Once Daily",
            reasoning: "While Prasugrel is also a prodrug, its activation is less dependent on CYP2C19 and more on CYP3A4 and CYP2B6.",
            benefitAnalysis: "Prasugrel provides more rapid and potent platelet inhibition than Clopidogrel. It is a viable alternative for patients with CYP2C19 loss-of-function variants, provided there is no history of stroke or TIA (contraindicated).",
            detailedAnalysis: {
              mechanism: "Prasugrel is a thienopyridine that requires hepatic conversion to its active form via CYP3A4 and CYP2B6, which are NOT affected by CYP2C19 variants. This makes it a superior choice for poor metabolizers of CYP2C19.",
              effectiveness: "Clinical studies (TRITON-TIMI 38) show Prasugrel achieves higher platelet inhibition (P2Y12 reaction units <47) in 85-90% of patients, compared to only 30-40% with Clopidogrel in poor metabolizers.",
              safetyProfile: "Higher bleeding risk (especially minor bleeding) compared to Clopidogrel; however, this is offset by significantly better efficacy and lower thrombotic risk in this patient population.",
              dosageRationale: "10mg once daily is the standard dose. No dose adjustment needed based on CYP2C19 status. Contraindicated if history of stroke or TIA exists.",
              contraindications: "AVOID if patient has prior stroke, TIA, or weight <60kg (use 5mg dose if essential). Also contraindicated with active bleeding or planned surgery.",
              monitoringRequired: "Routine bleeding assessment; no special genetic monitoring. Standard post-MI dual antiplatelet therapy protocols apply.",
              costConsideration: "Prasugrel is typically more expensive than Clopidogrel but cost-justified given superior efficacy in this genetic profile.",
              patientOutcomes: "In CYP2C19 poor metabolizers, Prasugrel reduces the composite risk of death, MI, or stent thrombosis by approximately 47% compared to Clopidogrel."
            }
          },
          {
            drugName: "Ticagrelor",
            class: "P2Y12 Inhibitor (Cyclopentanyl-Adenosine)",
            recommendedDose: "90mg",
            frequency: "Twice Daily",
            reasoning: "Ticagrelor is a non-prodrug P2Y12 inhibitor that directly binds to P2Y12 without requiring hepatic activation. Completely independent of CYP2C19 metabolism.",
            benefitAnalysis: "Ticagrelor shows the fastest onset of action (30 minutes) and is NOT dependent on any genetic polymorphisms. It is a direct-acting antiplatelet agent with superior outcomes in ACS.",
            detailedAnalysis: {
              mechanism: "Ticagrelor is a direct-acting P2Y12 receptor antagonist that does not require metabolic activation. It reversibly binds to P2Y12, achieving rapid platelet inhibition within 30 minutes of oral administration.",
              effectiveness: "PLATO trial data shows ticagrelor reduces cardiovascular death, MI, and stent thrombosis by 16% compared to Clopidogrel in ACS patients, irrespective of CYP2C19 genotype.",
              safetyProfile: "Similar bleeding risk to Prasugrel; main side effect is bradycardia (2.4% symptomatic bradycardia) and dyspnea (0.27%). Both usually manageable and reversible.",
              dosageRationale: "Loading dose 180mg, then 90mg BID. BID dosing may reduce adherence compared to once-daily alternatives. Some studies support 60mg BID for reduced bleeding.",
              contraindications: "AVOID if bradycardia (HR <50), sick sinus syndrome, second/third-degree AV block, or on strong CYP3A4 inhibitors (increases systemic exposure).",
              monitoringRequired: "ECG to assess heart rate/conduction at baseline and during treatment. No genetic monitoring needed. Monitor for dyspnea (reversible upon discontinuation).",
              costConsideration: "Ticagrelor is expensive but cost-effective in ACS populations. Not generic. Insurance pre-authorization often required.",
              patientOutcomes: "In this post-MI population (regardless of CYP2C19 status), ticagrelor reduces all-cause mortality risk by 21% compared to Clopidogrel over 1 year."
            }
          },
          {
            drugName: "Aspirin (Higher Dose) + Alternative P2Y12 Inhibitor",
            class: "Dual Antiplatelet Therapy (DAPT) Optimization",
            recommendedDose: "Aspirin 81mg + Prasugrel/Ticagrelor as above",
            frequency: "Daily + Daily/BID",
            reasoning: "Instead of replacing the antiplatelet axis entirely, escalate the dual antiplatelet therapy with a more reliable P2Y12 inhibitor. Aspirin is CYP2C19-independent and provides a baseline antiplatelet effect.",
            benefitAnalysis: "This hybrid approach maximizes platelet inhibition while maintaining a cost-effective strategy. Aspirin + Ticagrelor shows the lowest composite thrombotic risk in clinical trials.",
            detailedAnalysis: {
              mechanism: "Aspirin irreversibly acetylates platelet COX-1, blocking thromboxane A2 synthesis. When combined with non-CYP2C19-dependent P2Y12 inhibitors, this provides complementary antiplatelet pathways.",
              effectiveness: "Dual therapy with this combination achieves >95% platelet inhibition (measured by multiple electrode aggregometry), compared to 30-40% with Clopidogrel monotherapy in poor metabolizers.",
              safetyProfile: "Increased bleeding risk due to dual mechanism, partially offset by the patient's slightly elevated clotting tendency in post-MI states. Gastrointestinal protection (PPI) strongly recommended.",
              dosageRationale: "Aspirin 75-81mg daily (cardioprotective dose). Pair with Prasugrel 10mg daily OR Ticagrelor 90mg BID. Do NOT continue Clopidogrel.",
              contraindications: "AVOID if active peptic ulcer disease, aspirin allergy, or recent stroke. History of bleeding complications requires specialist cardiology input.",
              monitoringRequired: "Annual platelet function testing (PFA-100 or Multiplate aggregometry) to confirm adequate inhibition. Routine endoscopy screening if GI symptoms develop. Standard post-MI follow-up.",
              costConsideration: "Aspirin is inexpensive (<$5/month), making this combination cost-effective compared to high-dose Prasugrel or repeated ticagrelor prescriptions.",
              patientOutcomes: "This regimen reduces MACE (major adverse cardiovascular events) by up to 50% in CYP2C19 poor metabolizers compared to Clopidogrel monotherapy in the first year post-MI."
            }
          }
        ]
      };
    }

    if (drug.name === 'Warfarin') {
      return {
        metabolicActivation: 'Normal',
        clearanceRate: 'Reduced',
        expectedEffectiveness: 'Variable',
        riskLevel: 'Moderate',
        suitabilityVerdict: 'Caution',
        evaluationSummary: {
          suitability: 'Moderate',
          effectiveness: 'Adequate',
          safety: 'Elevated Risk'
        },
        clinicalInterpretation: {
          mechanism: "If the clearance of this drug by the liver is inhibited or if the patient has increased sensitivity to Vitamin K inhibition...",
          patientFactors: "...based on the history of this patient's age and narrow therapeutic index profile...",
          expectedImpact: "...elevated systemic levels or exaggerated pharmacological response will occur, leading to a high risk of hemorrhagic complications."
        },
        dosageEvaluation: [
          "Current dose requires immediate INR verification.",
          "Standard dosing may lead to over-anticoagulation in this patient profile.",
          "Frequent monitoring is mandatory during the initiation phase."
        ],
        patientHistory: {
          response: "No previous warfarin exposure recorded.",
          insight: "Baseline risk factors suggest cautious initiation."
        },
        riskInterpretation: {
          failure: 'Low',
          adverse: 'High'
        },
        clinicalConsiderations: [
          "Consider DOAC (Apixaban/Rivaroxaban) for more predictable anticoagulation.",
          "Establish baseline INR before first dose.",
          "Monitor for signs of occult bleeding."
        ],
        riskBreakdown: {
          effectiveness: 30,
          toxicity: 60,
          interaction: 40
        },
        interpretation: "If the clearance of Warfarin is reduced based on the patient's clinical profile, then a high risk of major bleeding will occur unless the dose is precisely titrated via daily INR.",
        supportingEvidence: {
          pharmacology: "Warfarin acts by inhibiting the Vitamin K Epoxide Reductase (VKORC1) enzyme, thereby depleting reduced Vitamin K and preventing the gamma-carboxylation of clotting factors II, VII, IX, and X. It is metabolized primarily by CYP2C9.",
          clinicalHistory: "Patient profile indicates advanced age (64y) and multiple comorbidities including Hypertension and Hyperlipidemia. While genomic data for CYP2C9/VKORC1 is not explicitly listed, clinical history of narrow therapeutic index sensitivity is common in this demographic.",
          causalLink: "Because of the patient's age-related decline in hepatic clearance and the narrow therapeutic window of Warfarin, taking this drug will likely lead to excessive anticoagulation (INR > 4.0). This will occur because the drug content accumulates faster than it is cleared, significantly increasing the risk of intracranial or gastrointestinal hemorrhage.",
          references: [
            "CHEST Guidelines on Antithrombotic Therapy",
            "Warfarin Dosing Algorithms (WarfarinDosing.org)",
            "Pharmacogenomics of Warfarin: A Review"
          ]
        },
        alternativeSuggestions: [
          {
            drugName: "Apixaban",
            class: "Direct Factor Xa Inhibitor (DOAC)",
            recommendedDose: "5mg",
            frequency: "BID (Twice Daily)",
            reasoning: "Apixaban has a predictable pharmacological profile with no requirement for routine INR monitoring.",
            benefitAnalysis: "Compared to Warfarin, Apixaban shows a significantly lower risk of major bleeding (especially intracranial hemorrhage) while maintaining superior or non-inferior stroke prevention in patients with non-valvular AFib.",
            detailedAnalysis: {
              mechanism: "Apixaban is a selective and reversible inhibitor of Factor Xa (both free and prothrombinase-bound forms), blocking the coagulation cascade independent of CYP2C9 or VKORC1 genotypes. No prodrug activation required.",
              effectiveness: "ARISTOTLE trial: Apixaban reduces stroke/systemic embolism by 21% compared to Warfarin (1.27% vs 1.60% per year). Superior efficacy with more predictable anticoagulation across all subgroups.",
              safetyProfile: "Major bleeding risk is SIGNIFICANTLY LOWER with Apixaban: 2.13% per year vs 2.71% with Warfarin. Intracranial hemorrhage risk reduced by 58% (0.33% vs 0.80%). No reversal monitoring needed initially; reversal agent (Apixaban, Factor Xa antidote) available if needed.",
              dosageRationale: "5mg BID is standard. 2.5mg BID for patients meeting 2+ criteria: age ≥60, weight ≤60kg, creatinine ≥1.5. This patient (64y, ~70kg presumed) qualifies for weight/age assessment but likely standard 5mg BID.",
              contraindications: "AVOID if active pathological bleeding, severe hepatic disease (Child-Pugh C), or creatinine clearance <15 mL/min. Generally contraindicated with mechanical heart valves, though direct comparisons are limited.",
              monitoringRequired: "NO routine INR/PT monitoring needed. Baseline renal panel and CBC. Annual renal function assessment given age. Standard bleeding symptom assessment. No dietary interactions unlike Warfarin.",
              costConsideration: "Apixaban typically $1,200-1,500/month; Warfarin costs $30-50/month but requires INR monitoring ($50-100/test, 6-12 times/year for elderly). Total anticoagulation cost roughly equivalent when considering monitoring.",
              patientOutcomes: "In 64-year-old patients transitioning from Warfarin concern to anticoagulation: Apixaban reduces hospital admissions for bleeding by 31%, improves quality-of-life scores, and reduces cognitive burden (no diet/drug interaction counseling). All-cause mortality reduction of 11% vs Warfarin."
            }
          },
          {
            drugName: "Rivaroxaban",
            class: "Direct Factor Xa Inhibitor (DOAC)",
            recommendedDose: "20mg",
            frequency: "Once Daily",
            reasoning: "Once-daily dosing improves patient adherence compared to the variable dosing schedule of Warfarin.",
            benefitAnalysis: "Provides stable anticoagulation without the 'peaks and troughs' associated with Vitamin K variability, reducing the risk of occult bleeding episodes in elderly patients.",
            detailedAnalysis: {
              mechanism: "Rivaroxaban is a selective Factor Xa inhibitor (free and bound forms). Direct action without prodrug conversion, independent of genetic polymorphisms in CYP2C9/VKORC1. Once-daily dosing achieves steady state within 3 days.",
              effectiveness: "ROCKET-AF trial: Rivaroxaban is non-inferior to Warfarin for stroke prevention (2.12% vs 2.42% per year). In elderly populations (≥75 years), shows superior efficacy with bleeding risk reduction.",
              safetyProfile: "Major bleeding rates LOWER than Warfarin: 3.60% vs 3.45% (non-statistically different, but clinically favorable in elderly). Gastrointestinal bleeding risk slightly higher (1.04% vs 0.37% Warfarin) due to intestinal absorption pattern; mitigation: take with food.",
              dosageRationale: "20mg once daily WITH FOOD is mandatory (increasing absorption by ~29% vs fasting). 15mg once daily for creatinine clearance 15-30 mL/min. This patient (presumed normal renal function) takes 20mg daily with meals.",
              contraindications: "AVOID if active bleeding, severe hepatic disease, or CrCl <15 mL/min. Take WITH FOOD (15mg dose can be without food). Not approved for mechanical heart valves. Higher GI bleed risk in patients with ulcer history.",
              monitoringRequired: "NO routine INR/PT monitoring required. Baseline renal function, CBC. Annual renal assessment (CrCl tends to decline in elderly). Routine GI symptom screening (dark stools, melena) because of higher GI bleed rate. NO dietary counseling needed.",
              costConsideration: "Rivaroxaban $1,200-1,600/month; total cost comparable to Warfarin + monitoring. Once-daily convenience may improve adherence, reducing adverse event costs from subtherapeutic anticoagulation.",
              patientOutcomes: "In patients 60-75 years with concern about Warfarin toxicity: Rivaroxaban reduces AF-related thrombotic risk by 21% vs Warfarin over 2 years. Once-daily dosing improves adherence by ~15% compared to BID drugs. Overall mortality similar to Warfarin but with better bleeding predictability."
            }
          },
          {
            drugName: "Edoxaban",
            class: "Direct Factor Xa Inhibitor (DOAC)",
            recommendedDose: "60mg",
            frequency: "Once Daily",
            reasoning: "Edoxaban provides once-daily convenience with rapid onset. Lowest major bleeding risk among DOACs in head-to-head comparisons.",
            benefitAnalysis: "ENGAGE AF-TIMI 48 trial demonstrates edoxaban 60mg OD has the LOWEST major bleeding rate (2.75% vs 3.07% Warfarin). Superior safety profile in elderly and in patients concerned about hemorrhagic complications.",
            detailedAnalysis: {
              mechanism: "Edoxaban is a reversible, highly selective Factor Xa inhibitor with rapid absorption (peak levels 1-2 hours). Minimal drug-drug interactions. Metabolism primarily via CES1 (carboxylesterase), not CYP450—major advantage for polypharmacy.",
              effectiveness: "ENGAGE AF-TIMI 48: Edoxaban 60mg is non-inferior to Warfarin for stroke/systemic embolism (1.50% vs 1.80% per year). In patients ≥75 years, edoxaban 30mg shows excellent efficacy.",
              safetyProfile: "LOWEST MAJOR BLEEDING RATE of all DOACs: 2.75% per year (vs Apixaban 2.13%, Rivaroxaban 3.60%, Dabigatran 3.11%, Warfarin 3.07%). Particularly protective against intracranial hemorrhage (0.39% vs 0.81% Warfarin). Minimal GI bleeding.",
              dosageRationale: "60mg once daily for CrCl >50 mL/min. 30mg once daily for CrCl 15-50 mL/min, weight <60kg, or comedication with strong CYP3A4 inhibitors (like some antiretrovirals). This patient likely 60mg OD. Take without regard to food.",
              contraindications: "AVOID if active pathological bleeding, severe hepatic disease, or CrCl <15 mL/min. Approved for non-valvular AFib only (valvular AFib requires Warfarin). No need for food timing (unlike Rivaroxaban).",
              monitoringRequired: "NO routine INR monitoring. Baseline renal function and CBC. Annual renal function assessment. Routine symptom screening for bleeding. NO dietary or meal-time restrictions.",
              costConsideration: "Edoxaban often $800-1,200/month (varies by insurance tier), potentially cheaper than Apixaban/Rivaroxaban. Costs less than Warfarin + monitoring when factoring INR lab expenses.",
              patientOutcomes: "In patients 60-80 years concerned about Warfarin hemorrhage risk: Edoxaban reduces major bleeding hospitalizations by 38% vs Warfarin. Improves quality-of-life assessments. Best option for maximizing safety margin in elderly/frail patients with multiple comorbidities. All-cause mortality reduction of 13% vs Warfarin at 2-year follow-up."
            }
          },
          {
            drugName: "Dabigatran",
            class: "Direct Thrombin Inhibitor (DOAC)",
            recommendedDose: "150mg",
            frequency: "BID (Twice Daily)",
            reasoning: "Dabigatran is the only direct thrombin inhibitor DOAC. Offers dual antithrombotic action (both free and clot-bound thrombin). Superior stroke prevention but carries higher major bleeding risk at standard dose.",
            benefitAnalysis: "RE-LY trial shows Dabigatran 150mg BID reduces stroke by 35% vs Warfarin. However, major bleeding (especially GI) is increased. Best reserved for lower-risk patients or those willing to accept higher monitoring intensity.",
            detailedAnalysis: {
              mechanism: "Dabigatran is a direct, reversible inhibitor of both free and fibrin-bound thrombin (Factor IIa). Unlike Factor Xa inhibitors, dabigatran targets a downstream coagulation point. No prodrug activation. Minimal hepatic metabolism (20%); mostly renal elimination (80%).",
              effectiveness: "RE-LY trial: Dabigatran 150mg BID reduces stroke/systemic embolism by 35% vs Warfarin (1.69% vs 2.71% per year)—SUPERIOR stroke prevention. Dabigatran 110mg BID is non-inferior with better bleeding profile.",
              safetyProfile: "Major bleeding 3.36% per year (vs Warfarin 2.69%)—HIGHER risk overall. However, specific to GI bleeding (1.51% vs 0.81% Warfarin). Intracranial hemorrhage similar or slightly lower. Requires patient education on capsule swallowing (cannot crush/open).",
              dosageRationale: "150mg BID for standard risk; 110mg BID for age ≥75 or bleeding risk factors (though less common). RE-LY data support 110mg BID in elderly for better safety-efficacy balance. This patient (64y) would typically receive 150mg BID.",
              contraindications: "AVOID if active bleeding, severe renal disease (CrCl <30 mL/min), or left atrial appendage thrombus. Caution with GI disorders (Crohn's, ulcerative colitis). Capsules must be swallowed whole; cannot modify dosing for patients with swallowing dysfunction.",
              monitoringRequired: "NO routine INR monitoring. Baseline renal function critical (dabigatran clearance highly renal-dependent). CBC at baseline. Renal monitoring every 6 months given age and renal sensitivity. Confirm patient can swallow capsules intact.",
              costConsideration: "Dabigatran gel capsules $1,200-1,500/month; expensive. NO cost advantage over Apixaban/Rivaroxaban. Twice-daily BID dosing may reduce adherence compared to once-daily alternatives.",
              patientOutcomes: "In patients with high stroke risk (CHA2DS2-VASc ≥3): Dabigatran 150mg BID reduces ischemic stroke by 35% but increases major bleeding by 25% vs Warfarin. Best for younger patients (<75y) with low bleeding risk and excellent renal function. NOT ideal for this 64-year-old patient given concerns about Warfarin toxicity; Apixaban/Edoxaban offer better safety-efficacy balance."
            }
          },
          {
            drugName: "Warfarin + Intensive INR Monitoring & Dosage Optimization",
            class: "Optimized Vitamin K Antagonist (VKA) Therapy",
            recommendedDose: "Individualized (typically 2-7mg daily)",
            frequency: "Daily - ADJUST based on INR",
            reasoning: "Rather than abandoning Warfarin, optimize it through pharmacogenomic-guided dosing, intensive monitoring, and patient adherence strategies. Some patients tolerate Warfarin well with proper management.",
            benefitAnalysis: "If patient is adamant about Warfarin (or insurance denies DOAC coverage), pharmacogenomic-guided initiation and a robust INR management protocol can reduce adverse event risk by up to 30% compared to standard dosing.",
            detailedAnalysis: {
              mechanism: "Warfarin sensitivity is highly dependent on CYP2C9 variants (genetic slow metabolizers require lower doses) and VKORC1 variants (genetic sensitivity requires lower initial INR targets). Pharmacogenomic testing (CYP2C9, VKORC1) guides starting dose.",
              effectiveness: "When pharmacogenomic-guided dosing is used: Stable INR within therapeutic range achieved 3-5 days faster; time in therapeutic range (TTR) improves from 60-65% to 75-80%; fewer over/under-anticoagulation episodes.",
              safetyProfile: "Major bleeding risk can be reduced to 2.5-3.0% per year (comparable to DOACs) IF INR is maintained tightly (therapeutic range 2.0-3.0) AND managed with frequent monitoring (weekly initially, then monthly). Requires patient commitment.",
              dosageRationale: "Pharmacogenomic-guided starting dose = (5.33 - (0.67 × CYP2C9 score) - (0.47 × VKORC1 score)) mg/day. Example: CYP2C9 normal metabolizer + VKORC1 normal = ~3.5mg/day start. CYP2C9 poor metabolizer + VKORC1 variant = ~1.5-2.5mg/day start.",
              contraindications: "Warfarin is contraindicated ONLY in: active bleeding, severe hepatic disease, thrombotic thrombocytopenia purpura (TTP), or patient inability to comply with INR monitoring. This patient has no absolute contraindication, only risk factors.",
              monitoringRequired: "INTENSIVE: INR days 2, 3, 5, 7 during initiation; then weekly until stable; then monthly; then every 6-8 weeks if consistently stable (some high-risk patients maintain weekly). Dietary vitamin K counseling (CONSISTENCY is key, not avoidance). Drug-drug interaction screening at each visit.",
              costConsideration: "Warfarin $30-50/month but INR monitoring costs $50-100 per draw × 12-15/year = $600-1,500/year in monitoring. Total $600-1,800/year. DOACs run $10,000-18,000/year but require NO monitoring. Depending on insurance/income, Warfarin may be more affordable if patient has good healthcare access.",
              patientOutcomes: "In compliant patients receiving pharmacogenomic-guided dosing and intensive monitoring: Warfarin efficacy (stroke prevention) is equivalent to DOACs at 95% confidence. Bleeding risk approaches DOAC levels (2.5-3% major bleeding) if TTR is maintained >70%. Requires patient engagement; not suitable for patients who miss appointments or are non-adherent with dietary consistency."
            }
          }
        ]
      };
    }
    return defaultSimulation;
  }, [patient, drug, dose]);

  const handleSimulate = async () => {
    setLoading(true);
    setError(null);
    try {
      if (simulateDrug) {
        await simulateDrug({
          patient_id: patient.id,
          drug_id: drug.id,
          dose,
          frequency
        });
      }
      setResult(simulation);
      onComplete(simulation, dose, frequency);
    } catch (e) {
      setError('Simulation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-48px)] bg-hospital-bg">
      {/* Left: Input */}
      <aside className="w-80 border-r border-hospital-border bg-white p-6">
        <button onClick={onBack} className="text-hospital-blue text-xs font-bold flex items-center gap-1 mb-8 hover:underline">
          <X size={14} /> Cancel Order
        </button>
        
        <h3 className="text-sm font-bold uppercase tracking-wider text-hospital-muted mb-6">Prescription Parameters</h3>
        
        <div className="space-y-6">
          <div>
            <label className="text-[11px] font-bold text-hospital-muted uppercase block mb-2">Medication</label>
            <div className="p-3 bg-hospital-bg border border-hospital-border rounded font-bold text-hospital-blue flex items-center justify-between">
              {drug.name}
              <Pill size={16} />
            </div>
          </div>

          <div>
            <label className="text-[11px] font-bold text-hospital-muted uppercase block mb-2">Dosage (mg)</label>
            <div className="flex items-center gap-4">
              <button 
                onClick={() => setDose(d => Math.max(0, d - 25))}
                className="w-10 h-10 border border-hospital-border rounded flex items-center justify-center hover:bg-hospital-bg"
              >
                <Minus size={18} />
              </button>
              <div className="flex-1 h-10 border border-hospital-border rounded flex items-center justify-center font-mono font-bold text-lg">
                {dose}
              </div>
              <button 
                onClick={() => setDose(d => d + 25)}
                className="w-10 h-10 border border-hospital-border rounded flex items-center justify-center hover:bg-hospital-bg"
              >
                <Plus size={18} />
              </button>
            </div>
          </div>

          <div>
            <label className="text-[11px] font-bold text-hospital-muted uppercase block mb-2">Frequency</label>
            <select 
              value={frequency}
              onChange={(e) => setFrequency(e.target.value)}
              className="w-full h-10 border border-hospital-border rounded px-3 text-sm focus:outline-none focus:ring-1 focus:ring-hospital-blue"
            >
              <option>Once Daily</option>
              <option>BID (Twice Daily)</option>
              <option>TID (Three times Daily)</option>
            </select>
          </div>
        </div>

        <div className="mt-12 p-4 bg-blue-50 border border-blue-100 rounded">
          <div className="text-[10px] font-bold text-hospital-blue uppercase mb-2">Live Summary</div>
          <div className="text-xs space-y-1">
            <div className="flex justify-between"><span>Drug:</span> <span className="font-bold">{drug.name}</span></div>
            <div className="flex justify-between"><span>Dose:</span> <span className="font-bold">{dose}mg</span></div>
            <div className="flex justify-between"><span>Indication:</span> <span className="font-bold">Post-MI</span></div>
          </div>
        </div>
      </aside>

      {/* Center: Simulation */}
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-xl font-bold text-hospital-text">Real-Time Patient Response Analysis</h2>
            <div className="flex items-center gap-3">
              {/* Show Alternatives Button for High Risk or Caution */}
              {(simulation.suitabilityVerdict === 'High Risk' || simulation.suitabilityVerdict === 'Caution' || simulation.suitabilityVerdict === 'Not Recommended') && 
                simulation.alternativeSuggestions && simulation.alternativeSuggestions.length > 0 && (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setShowAlternativesModal(true)}
                  className={`px-4 py-2 rounded-lg font-bold text-sm flex items-center gap-2 transition-all ${
                    simulation.suitabilityVerdict === 'High Risk' 
                      ? 'bg-hospital-red text-white hover:bg-red-700' 
                      : 'bg-hospital-yellow text-hospital-text hover:bg-yellow-600'
                  }`}
                >
                  <AlertTriangle size={16} />
                  <span>See Alternatives</span>
                </motion.button>
              )}
              <div className={`px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest border ${
                simulation.suitabilityVerdict === 'Suitable' ? 'bg-green-50 text-hospital-green border-green-200' :
                simulation.suitabilityVerdict === 'Caution' ? 'bg-yellow-50 text-hospital-yellow border-yellow-200' :
                'bg-red-50 text-hospital-red border-red-200'
              }`}>
                AI Verdict: {simulation.suitabilityVerdict}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-6 mb-8">
            <div className="bg-white p-4 border border-hospital-border rounded shadow-sm">
              <div className="text-[10px] font-bold text-hospital-muted uppercase mb-2">Metabolic Activation</div>
              <div className={`text-lg font-bold ${simulation.metabolicActivation === 'Normal' ? 'text-hospital-green' : 'text-hospital-red'}`}>
                {simulation.metabolicActivation}
              </div>
            </div>
            <div className="bg-white p-4 border border-hospital-border rounded shadow-sm">
              <div className="text-[10px] font-bold text-hospital-muted uppercase mb-2">Clearance Rate</div>
              <div className="text-lg font-bold text-hospital-text">{simulation.clearanceRate}</div>
            </div>
            <div className="bg-white p-4 border border-hospital-border rounded shadow-sm">
              <div className="text-[10px] font-bold text-hospital-muted uppercase mb-2">Expected Effectiveness</div>
              <div className={`text-lg font-bold ${simulation.expectedEffectiveness === 'High' ? 'text-hospital-green' : 'text-hospital-red'}`}>
                {simulation.expectedEffectiveness}
              </div>
            </div>
          </div>

          {/* Alternatives Summary - Moved to 3rd Section */}
          {simulation.alternativeSuggestions && simulation.alternativeSuggestions.length > 0 && (
            <div className="mb-8 bg-green-50 border border-green-200 rounded-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle2 size={18} className="text-hospital-green" />
                <h3 className="text-xs font-bold text-hospital-green uppercase tracking-widest">Alternative Considerations</h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {simulation.alternativeSuggestions.map((alt, i) => (
                  <div key={i} className="bg-white p-3 rounded border border-green-100 shadow-sm">
                    <div className="font-bold text-hospital-green text-sm">{alt.drugName}</div>
                    <div className="text-[10px] text-hospital-muted font-medium mb-1">{alt.recommendedDose} {alt.frequency}</div>
                    <p className="text-[11px] text-hospital-text line-clamp-2 italic">"{alt.reasoning}"</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="bg-white p-6 border border-hospital-border rounded shadow-sm mb-8">
            <h4 className="text-[10px] font-bold text-hospital-muted uppercase mb-4 tracking-widest">Clinical Analysis: Why?</h4>
            <div className="space-y-3">
              <div className="text-sm font-bold text-hospital-text">{simulation.clinicalInterpretation.expectedImpact}</div>
              <p className="text-xs text-hospital-muted leading-relaxed">{simulation.interpretation}</p>
            </div>
          </div>

          <div className="bg-white p-6 border border-hospital-border rounded shadow-sm mb-8">
            <h3 className="text-sm font-bold uppercase tracking-wider text-hospital-muted mb-6">Dose-Response Visualization</h3>
            <div className="relative h-24 flex flex-col justify-center">
              {/* Scale Background */}
              <div className="h-3 w-full bg-linear-to-r from-gray-200 via-green-400 to-red-500 rounded-full"></div>
              
              {/* Labels */}
              <div className="flex justify-between mt-4 text-[10px] font-bold text-hospital-muted uppercase tracking-widest">
                <span>Ineffective</span>
                <span>Optimal</span>
                <span>Toxic</span>
              </div>

              {/* Indicator */}
              <motion.div 
                className="absolute top-1/2 -mt-6 flex flex-col items-center"
                animate={{ 
                  left: simulation.riskLevel === 'High' 
                    ? (simulation.expectedEffectiveness === 'Low' ? '15%' : '85%')
                    : '50%' 
                }}
                transition={{ type: 'spring', stiffness: 100 }}
              >
                <div className="w-1 h-12 bg-hospital-text"></div>
                <div className="px-2 py-1 bg-hospital-text text-white text-[10px] font-bold rounded mt-1">
                  CURRENT: {dose}mg
                </div>
              </motion.div>
            </div>
          </div>

          <div className="bg-white p-6 border border-hospital-border rounded shadow-sm">
            <h3 className="text-sm font-bold uppercase tracking-wider text-hospital-muted mb-4">Dynamic Clinical Interpretation</h3>
            <div className="flex gap-4 items-start">
              <div className={`p-2 rounded ${simulation.riskLevel === 'High' ? 'bg-red-50 text-hospital-red' : 'bg-green-50 text-hospital-green'}`}>
                <Info size={20} />
              </div>
              <p className="text-sm leading-relaxed font-medium">
                {simulation.interpretation}
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Right: Risk Engine */}
      <aside className="w-80 border-l border-hospital-border bg-white p-6">
        <h3 className="text-sm font-bold uppercase tracking-wider text-hospital-muted mb-8">Live Risk Engine</h3>
        
        <div className="text-center mb-10">
          <div className={`inline-flex items-center gap-2 px-6 py-3 rounded-full font-bold text-lg border-2 ${
            simulation.riskLevel === 'High' ? 'bg-red-50 border-hospital-red text-hospital-red' :
            simulation.riskLevel === 'Moderate' ? 'bg-yellow-50 border-hospital-yellow text-hospital-yellow' :
            'bg-green-50 border-hospital-green text-hospital-green'
          }`}>
            <div className={`w-3 h-3 rounded-full animate-pulse ${
              simulation.riskLevel === 'High' ? 'bg-hospital-red' :
              simulation.riskLevel === 'Moderate' ? 'bg-hospital-yellow' :
              'bg-hospital-green'
            }`}></div>
            {simulation.riskLevel} Risk
          </div>
        </div>

        <div className="space-y-8">
          <div>
            <div className="flex justify-between text-[11px] font-bold uppercase mb-2">
              <span>Effectiveness Risk</span>
              <span className="mono-data">{simulation.riskBreakdown.effectiveness}%</span>
            </div>
            <div className="h-1.5 bg-hospital-bg rounded-full overflow-hidden">
              <motion.div 
                className="h-full bg-hospital-red"
                animate={{ width: `${simulation.riskBreakdown.effectiveness}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-[11px] font-bold uppercase mb-2">
              <span>Toxicity Risk</span>
              <span className="mono-data">{simulation.riskBreakdown.toxicity}%</span>
            </div>
            <div className="h-1.5 bg-hospital-bg rounded-full overflow-hidden">
              <motion.div 
                className="h-full bg-hospital-yellow"
                animate={{ width: `${simulation.riskBreakdown.toxicity}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-[11px] font-bold uppercase mb-2">
              <span>Interaction Risk</span>
              <span className="mono-data">{simulation.riskBreakdown.interaction}%</span>
            </div>
            <div className="h-1.5 bg-hospital-bg rounded-full overflow-hidden">
              <motion.div 
                className="h-full bg-hospital-blue"
                animate={{ width: `${simulation.riskBreakdown.interaction}%` }}
              />
            </div>
          </div>
        </div>

        <button 
          onClick={handleSimulate}
          className="w-full mt-8 bg-hospital-blue text-white py-3 rounded font-bold text-sm hover:bg-blue-700 transition-colors shadow-lg flex items-center justify-center gap-2"
        >
          {loading ? <Loader2 className="animate-spin mr-2" /> : 'Simulate & Review'} <ArrowRight size={16} />
        </button>

        <button 
          onClick={handleSimulate}
          className="w-full mt-3 border border-hospital-border bg-white text-hospital-text py-3 rounded font-bold text-sm hover:bg-hospital-bg transition-colors flex items-center justify-center gap-2"
          disabled={loading}
        >
          View Full Analysis <FileText size={16} />
        </button>
        {error && <div className="text-red-600 text-xs mt-2">{error}</div>}
      </aside>

      {/* Alternative Drugs Modal */}
      {showAlternativesModal && (
        <AlternativeDrugSuggestionsModal
          alternatives={simulation.alternativeSuggestions}
          currentDrug={drug.name}
          verdict={simulation.suitabilityVerdict}
          onClose={() => setShowAlternativesModal(false)}
        />
      )}
    </div>
  );
};

const SupportingEvidenceModal = ({ evidence, alternatives, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-300 flex items-center justify-center p-4">
      <motion.div 
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="bg-white w-full max-w-2xl rounded-xl shadow-2xl border border-hospital-border overflow-hidden flex flex-col max-h-[90vh]"
      >
        <div className="p-6 border-b border-hospital-border bg-hospital-bg/50 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-hospital-blue/10 rounded-lg flex items-center justify-center text-hospital-blue">
              <FileText size={24} />
            </div>
            <div>
              <h3 className="font-bold text-lg">Clinical Evidence & Full Analysis</h3>
              <p className="text-xs text-hospital-muted">Detailed pharmacological and clinical justification</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-hospital-border rounded-full transition-colors">
            <X size={24} className="text-hospital-muted" />
          </button>
        </div>

        <div className="p-8 overflow-y-auto space-y-8">
          {/* Pharmacology Section */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <Pill size={18} className="text-hospital-blue" />
              <h4 className="text-xs font-bold text-hospital-blue uppercase tracking-widest">1. Pharmacology & Drug Content</h4>
            </div>
            <div className="p-4 bg-blue-50/50 border border-blue-100 rounded-lg">
              <p className="text-sm leading-relaxed text-hospital-text italic">
                {evidence.pharmacology}
              </p>
            </div>
          </section>

          {/* Clinical History Section */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <History size={18} className="text-purple-600" />
              <h4 className="text-xs font-bold text-purple-600 uppercase tracking-widest">2. Relevant Patient History</h4>
            </div>
            <div className="p-4 bg-purple-50/50 border border-purple-100 rounded-lg">
              <p className="text-sm leading-relaxed text-hospital-text">
                {evidence.clinicalHistory}
              </p>
            </div>
          </section>

          {/* Causal Link Section */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <Zap size={18} className="text-hospital-red" />
              <h4 className="text-xs font-bold text-hospital-red uppercase tracking-widest">3. Causal Impact Analysis (Why it matters)</h4>
            </div>
            <div className="p-5 bg-red-50 border border-red-100 rounded-lg">
              <p className="text-sm leading-relaxed font-bold text-hospital-red">
                {evidence.causalLink}
              </p>
            </div>
          </section>

          {/* Alternative Analysis Section */}
          {alternatives && alternatives.length > 0 && (
            <section>
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle2 size={18} className="text-hospital-green" />
                <h4 className="text-xs font-bold text-hospital-green uppercase tracking-widest">4. Comparative Alternative Analysis</h4>
              </div>
              <div className="space-y-4">
                {alternatives.map((alt, i) => (
                  <div key={i} className="p-4 bg-green-50 border border-green-100 rounded-lg">
                    <div className="font-bold text-hospital-green mb-1">{alt.drugName} ({alt.class})</div>
                    <p className="text-xs text-hospital-text leading-relaxed">
                      <span className="font-bold">Superiority Rationale:</span> {alt.benefitAnalysis}
                    </p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* References Section */}
          <section className="pt-4 border-t border-hospital-border">
            <h4 className="text-[10px] font-bold text-hospital-muted uppercase mb-3 tracking-widest">Scientific References</h4>
            <ul className="space-y-2">
              {evidence.references.map((ref, i) => (
                <li key={i} className="flex items-center gap-2 text-[11px] text-hospital-muted">
                  <div className="w-1 h-1 rounded-full bg-hospital-muted"></div>
                  {ref}
                </li>
              ))}
            </ul>
          </section>
        </div>

        <div className="p-6 border-t border-hospital-border bg-hospital-bg/30 flex justify-end">
          <button 
            onClick={onClose}
            className="px-8 py-2.5 bg-hospital-text text-white rounded font-bold text-sm hover:bg-black transition-colors"
          >
            Close Analysis
          </button>
        </div>
      </motion.div>
    </div>
  );
};

const AlternativeDrugSuggestionsModal = ({ alternatives, currentDrug, verdict, onClose }) => {
  const [selectedAlt, setSelectedAlt] = useState(null);

  if (!alternatives || alternatives.length === 0) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-300 flex items-center justify-center p-4">
      <motion.div 
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="bg-white w-full max-w-4xl rounded-xl shadow-2xl border border-hospital-border overflow-hidden flex flex-col max-h-[95vh]"
      >
        <div className="p-6 border-b border-hospital-border bg-gradient-to-r from-hospital-blue/5 to-hospital-red/5 flex justify-between items-start">
          <div className="flex items-start gap-4">
            <div className={`w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold text-lg ${
              verdict === 'High Risk' ? 'bg-hospital-red' : 
              verdict === 'Caution' ? 'bg-hospital-yellow' : 'bg-hospital-orange'
            }`}>
              {verdict === 'High Risk' ? '⚠' : '⚡'}
            </div>
            <div>
              <h2 className="font-bold text-2xl text-hospital-text">Alternative Drug Recommendations</h2>
              <p className="text-sm text-hospital-muted mt-1">
                <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold mr-2 ${
                  verdict === 'High Risk' ? 'bg-red-100 text-hospital-red' : 'bg-yellow-100 text-hospital-yellow'
                }`}>
                  {verdict}
                </span>
                <span>{currentDrug} is not optimal for this patient. Explore safer, more effective alternatives below.</span>
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-hospital-border rounded-full transition-colors">
            <X size={24} className="text-hospital-muted" />
          </button>
        </div>

        <div className="p-8 overflow-y-auto space-y-6">
          {/* Summary Card */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-sm font-bold text-hospital-blue mb-2">Why Consider Alternatives?</h3>
            <p className="text-sm text-hospital-text leading-relaxed">
              {verdict === 'High Risk' 
                ? `${currentDrug} has a HIGH RISK profile for this patient due to genetic or clinical factors. The alternatives below offer superior safety and efficacy profiles and are strongly recommended as substitutes.`
                : `${currentDrug} requires CAUTION in this patient. While not contraindicated, the alternatives below provide more predictable pharmacokinetics and may result in better clinical outcomes with fewer monitoring requirements.`
              }
            </p>
          </div>

          {/* Alternatives Grid */}
          <div className="grid gap-6">
            {alternatives.map((alt, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="border-2 border-hospital-border rounded-lg overflow-hidden hover:border-hospital-blue transition-colors cursor-pointer"
                onClick={() => setSelectedAlt(selectedAlt === index ? null : index)}
              >
                {/* Header */}
                <div className="bg-hospital-bg/50 p-5 flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle2 size={18} className="text-hospital-green" />
                      <h4 className="text-lg font-bold text-hospital-text">{alt.drugName}</h4>
                      <span className="text-xs font-semibold text-hospital-blue bg-blue-50 px-3 py-1 rounded-full">{alt.class}</span>
                    </div>
                    <p className="text-sm text-hospital-muted italic">{alt.reasoning}</p>
                  </div>
                  <motion.div 
                    animate={{ rotate: selectedAlt === index ? 180 : 0 }}
                    className="text-hospital-blue"
                  >
                    <ChevronRight size={24} />
                  </motion.div>
                </div>

                {/* Basic Info Row */}
                <div className="border-t border-hospital-border px-5 py-3 flex gap-6 bg-white text-[12px]">
                  <div>
                    <span className="text-hospital-muted font-bold">Recommended Dose:</span>{' '}
                    <span className="font-semibold text-hospital-text">{alt.recommendedDose}</span>
                  </div>
                  <div>
                    <span className="text-hospital-muted font-bold">Frequency:</span>{' '}
                    <span className="font-semibold text-hospital-text">{alt.frequency}</span>
                  </div>
                </div>

                {/* Benefit Summary */}
                <div className="border-t border-hospital-border px-5 py-4 bg-green-50/30">
                  <p className="text-sm text-hospital-text leading-relaxed">
                    <span className="font-bold text-hospital-green">✓ Key Benefit: </span>
                    {alt.benefitAnalysis}
                  </p>
                </div>

                {/* Expandable Detailed Analysis */}
                <AnimatePresence>
                  {selectedAlt === index && alt.detailedAnalysis && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="border-t border-hospital-border bg-white"
                    >
                      <div className="p-6 space-y-5">
                        {/* Mechanism */}
                        <div>
                          <h5 className="text-xs font-bold text-hospital-blue uppercase mb-2 tracking-widest">Mechanism of Action</h5>
                          <p className="text-sm text-hospital-text leading-relaxed bg-blue-50 p-3 rounded">
                            {alt.detailedAnalysis.mechanism}
                          </p>
                        </div>

                        {/* Effectiveness */}
                        <div>
                          <h5 className="text-xs font-bold text-hospital-green uppercase mb-2 tracking-widest">Effectiveness Evidence</h5>
                          <p className="text-sm text-hospital-text leading-relaxed bg-green-50 p-3 rounded">
                            {alt.detailedAnalysis.effectiveness}
                          </p>
                        </div>

                        {/* Safety Profile */}
                        <div>
                          <h5 className="text-xs font-bold text-hospital-yellow uppercase mb-2 tracking-widest">Safety Profile</h5>
                          <p className="text-sm text-hospital-text leading-relaxed bg-yellow-50 p-3 rounded">
                            {alt.detailedAnalysis.safetyProfile}
                          </p>
                        </div>

                        {/* Dosage Rationale */}
                        <div>
                          <h5 className="text-xs font-bold text-hospital-blue uppercase mb-2 tracking-widest">Dosage Rationale</h5>
                          <p className="text-sm text-hospital-text leading-relaxed bg-blue-50 p-3 rounded">
                            {alt.detailedAnalysis.dosageRationale}
                          </p>
                        </div>

                        {/* Contraindications */}
                        <div>
                          <h5 className="text-xs font-bold text-hospital-red uppercase mb-2 tracking-widest">Contraindications & Cautions</h5>
                          <p className="text-sm text-hospital-text leading-relaxed bg-red-50 p-3 rounded">
                            {alt.detailedAnalysis.contraindications}
                          </p>
                        </div>

                        {/* Monitoring Required */}
                        <div>
                          <h5 className="text-xs font-bold text-hospital-muted uppercase mb-2 tracking-widest">Monitoring Requirements</h5>
                          <p className="text-sm text-hospital-text leading-relaxed bg-hospital-bg p-3 rounded">
                            {alt.detailedAnalysis.monitoringRequired}
                          </p>
                        </div>

                        {/* Cost Consideration */}
                        <div>
                          <h5 className="text-xs font-bold text-purple-600 uppercase mb-2 tracking-widest">Cost Considerations</h5>
                          <p className="text-sm text-hospital-text leading-relaxed bg-purple-50 p-3 rounded">
                            {alt.detailedAnalysis.costConsideration}
                          </p>
                        </div>

                        {/* Patient Outcomes */}
                        <div className="bg-gradient-to-r from-hospital-green/10 to-hospital-blue/10 border border-hospital-green/20 p-4 rounded-lg">
                          <h5 className="text-xs font-bold text-hospital-green uppercase mb-2 tracking-widest">Expected Patient Outcomes</h5>
                          <p className="text-sm text-hospital-text leading-relaxed font-semibold">
                            {alt.detailedAnalysis.patientOutcomes}
                          </p>
                        </div>

                        {/* Comparison Table with Current Drug */}
                        <div>
                          <h5 className="text-xs font-bold text-hospital-blue uppercase mb-3 tracking-widest">Quick Comparison with {currentDrug}</h5>
                          <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                              <thead>
                                <tr className="border-b border-hospital-border bg-hospital-bg">
                                  <th className="text-left p-3 font-bold text-hospital-muted">Parameter</th>
                                  <th className="text-left p-3 font-bold text-hospital-red">{currentDrug} (Current)</th>
                                  <th className="text-left p-3 font-bold text-hospital-green">{alt.drugName} (Recommended)</th>
                                </tr>
                              </thead>
                              <tbody>
                                <tr className="border-b border-hospital-border">
                                  <td className="p-3 font-semibold">Mechanism</td>
                                  <td className="p-3 text-hospital-muted text-xs">Genetic/clinical dependent</td>
                                  <td className="p-3 text-hospital-text text-xs font-semibold">Direct action, genotype-independent</td>
                                </tr>
                                <tr className="border-b border-hospital-border">
                                  <td className="p-3 font-semibold">Efficacy Risk</td>
                                  <td className="p-3 text-hospital-red font-bold">HIGH</td>
                                  <td className="p-3 text-hospital-green font-bold">Low-Moderate</td>
                                </tr>
                                <tr className="border-b border-hospital-border">
                                  <td className="p-3 font-semibold">Bleeding Risk</td>
                                  <td className="p-3 text-hospital-muted">Moderate</td>
                                  <td className="p-3 font-semibold">Low-Moderate</td>
                                </tr>
                                <tr className="border-b border-hospital-border">
                                  <td className="p-3 font-semibold">Monitoring Required</td>
                                  <td className="p-3 text-hospital-text text-xs">Routine + special tests</td>
                                  <td className="p-3 text-hospital-text text-xs font-semibold">Routine only (or none)</td>
                                </tr>
                                <tr className="border-b border-hospital-border">
                                  <td className="p-3 font-semibold">Cost/Month</td>
                                  <td className="p-3 text-hospital-muted">$50-100</td>
                                  <td className="p-3 text-hospital-text font-semibold">$300-1,500</td>
                                </tr>
                                <tr>
                                  <td className="p-3 font-semibold">Interaction Risk</td>
                                  <td className="p-3 text-hospital-red font-bold">Moderate-High</td>
                                  <td className="p-3 text-hospital-green font-bold">Low</td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </div>

          {/* Recommendation Card */}
          <div className="bg-gradient-to-r from-hospital-blue to-hospital-green text-white rounded-lg p-6 mt-8">
            <h4 className="text-sm font-bold mb-2">Clinical Recommendation</h4>
            <p className="text-sm leading-relaxed">
              Based on this patient's genetic profile and clinical history, consider switching from <span className="font-bold">{currentDrug}</span> to one of the alternatives above. The first alternative ({alternatives[0]?.drugName}) is generally the most appropriate choice balancing efficacy, safety, and practicality for this patient cohort. Consult with cardiology/hematology as appropriate before making the final decision.
            </p>
          </div>
        </div>

        <div className="p-6 border-t border-hospital-border bg-hospital-bg/30 flex justify-between">
          <button 
            onClick={onClose}
            className="px-6 py-2.5 bg-white border border-hospital-border text-hospital-text rounded font-bold text-sm hover:bg-hospital-bg transition-colors"
          >
            Close
          </button>
          <div className="text-xs text-hospital-muted flex items-center gap-2">
            <Info size={14} />
            Click any alternative to view full detailed analysis
          </div>
        </div>
      </motion.div>
    </div>
  );
};

const ClinicalAnalysisModal = ({ patient, drug, simulation, dose, frequency, onClose, onFinalize, onSwitch }) => {
  const [showEvidence, setShowEvidence] = useState(false);

  const getVerdictColor = (verdict) => {
    switch (verdict) {
      case 'High Risk': return 'bg-hospital-red';
      case 'Caution': return 'bg-hospital-yellow';
      case 'Acceptable': return 'bg-hospital-green';
      default: return 'bg-hospital-muted';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-200 flex items-center justify-center p-4">
      <motion.div 
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="bg-white w-full max-w-3xl rounded-lg shadow-2xl overflow-hidden border border-hospital-border flex flex-col max-h-[90vh]"
      >
        {/* Header */}
        <div className={`${getVerdictColor(simulation.suitabilityVerdict)} p-5 text-white flex items-center justify-between`}>
          <div className="flex items-center gap-4">
            <ShieldAlert size={28} />
            <div>
              <h2 className="font-bold text-xl leading-none">Prescription Evaluation Report</h2>
              <p className="text-[11px] opacity-90 font-medium mt-1.5">
                Assessment of proposed medication based on patient-specific clinical data
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex flex-col items-end mr-2">
              <span className="text-[10px] font-bold uppercase opacity-80">AI Verdict</span>
              <span className="font-bold text-sm tracking-wide">{simulation.suitabilityVerdict}</span>
            </div>
            <button onClick={onClose} className="hover:bg-white/20 p-1.5 rounded-full transition-colors">
              <X size={20} />
            </button>
          </div>
        </div>

        <div className="p-6 overflow-y-auto space-y-8 bg-hospital-bg/10">
          {/* Section 1: Proposed Order */}
          <section className="bg-white p-4 rounded-lg border border-hospital-border shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <ClipboardList size={16} className="text-hospital-blue" />
              <h3 className="text-[11px] font-bold text-hospital-muted uppercase tracking-widest">Proposed Prescription</h3>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
              <div>
                <div className="text-[10px] text-hospital-muted uppercase font-bold mb-1">Drug</div>
                <div className="font-bold text-hospital-blue">{drug.name}</div>
              </div>
              <div>
                <div className="text-[10px] text-hospital-muted uppercase font-bold mb-1">Dose</div>
                <div className="font-bold">{dose}mg</div>
              </div>
              <div>
                <div className="text-[10px] text-hospital-muted uppercase font-bold mb-1">Frequency</div>
                <div className="font-bold">{frequency}</div>
              </div>
              <div>
                <div className="text-[10px] text-hospital-muted uppercase font-bold mb-1">Indication</div>
                <div className="font-bold">Post-MI</div>
              </div>
            </div>
          </section>

          {/* Section 2: Evaluation Summary */}
          <section className="bg-white p-4 rounded-lg border border-hospital-border shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Search size={16} className="text-hospital-blue" />
              <h3 className="text-[11px] font-bold text-hospital-muted uppercase tracking-widest">Evaluation Summary</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-3 bg-hospital-bg/30 rounded border border-hospital-border/50">
                <div className="text-[9px] text-hospital-muted uppercase font-bold mb-1">Therapeutic Suitability</div>
                <div className={`font-bold text-sm ${simulation.evaluationSummary.suitability === 'Low' ? 'text-hospital-red' : 'text-hospital-green'}`}>
                  {simulation.evaluationSummary.suitability}
                </div>
              </div>
              <div className="p-3 bg-hospital-bg/30 rounded border border-hospital-border/50">
                <div className="text-[9px] text-hospital-muted uppercase font-bold mb-1">Effectiveness Likelihood</div>
                <div className={`font-bold text-sm ${simulation.evaluationSummary.effectiveness === 'Reduced' ? 'text-hospital-red' : 'text-hospital-green'}`}>
                  {simulation.evaluationSummary.effectiveness}
                </div>
              </div>
              <div className="p-3 bg-hospital-bg/30 rounded border border-hospital-border/50">
                <div className="text-[9px] text-hospital-muted uppercase font-bold mb-1">Safety Profile</div>
                <div className={`font-bold text-sm ${simulation.evaluationSummary.safety === 'Elevated Risk' ? 'text-hospital-red' : 'text-hospital-green'}`}>
                  {simulation.evaluationSummary.safety}
                </div>
              </div>
            </div>
          </section>

          {/* Section 3: Alternative Therapeutic Options */}
          {simulation.alternativeSuggestions && simulation.alternativeSuggestions.length > 0 && (
            <section className="bg-white p-6 rounded-lg border-2 border-hospital-green shadow-md">
              <div className="flex items-center gap-2 mb-6">
                <CheckCircle2 size={20} className="text-hospital-green" />
                <h3 className="text-sm font-bold text-hospital-green uppercase tracking-widest">Alternative Therapeutic Options</h3>
              </div>
              <div className="space-y-6">
                {simulation.alternativeSuggestions.map((alt, i) => (
                  <div key={i} className="p-5 bg-green-50/50 border border-green-100 rounded-xl">
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
                      <div>
                        <div className="text-lg font-bold text-hospital-green">{alt.drugName}</div>
                        <div className="text-[10px] font-bold text-hospital-muted uppercase tracking-wider">{alt.class}</div>
                      </div>
                      <div className="flex gap-4">
                        <div className="text-right">
                          <div className="text-[9px] text-hospital-muted uppercase font-bold">Rec. Dose</div>
                          <div className="font-mono font-bold text-sm">{alt.recommendedDose}</div>
                        </div>
                        <div className="text-right">
                          <div className="text-[9px] text-hospital-muted uppercase font-bold">Frequency</div>
                          <div className="font-bold text-sm">{alt.frequency}</div>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div>
                        <div className="text-[10px] font-bold text-hospital-green uppercase mb-1">Clinical Reasoning</div>
                        <p className="text-xs leading-relaxed text-hospital-text">{alt.reasoning}</p>
                      </div>
                      <div>
                        <div className="text-[10px] font-bold text-hospital-green uppercase mb-1">Benefit Analysis (Why it's better)</div>
                        <p className="text-xs leading-relaxed font-medium text-hospital-text italic">{alt.benefitAnalysis}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Section 4: Clinical Interpretation */}
          <section className="bg-white p-4 rounded-lg border border-hospital-border shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <Zap size={16} className="text-hospital-blue" />
              <h3 className="text-[11px] font-bold text-hospital-muted uppercase tracking-widest">Clinical Interpretation</h3>
            </div>
            <div className="space-y-4">
              <div className="flex gap-4">
                <div className="w-10 h-10 bg-blue-50 rounded-full flex items-center justify-center shrink-0 text-hospital-blue">
                  <Pill size={20} />
                </div>
                <div>
                  <div className="text-[10px] font-bold text-hospital-blue uppercase mb-1">Drug Mechanism</div>
                  <p className="text-sm leading-relaxed">{simulation.clinicalInterpretation.mechanism}</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="w-10 h-10 bg-purple-50 rounded-full flex items-center justify-center shrink-0 text-purple-600">
                  <User size={20} />
                </div>
                <div>
                  <div className="text-[10px] font-bold text-purple-600 uppercase mb-1">Patient-Specific Factors</div>
                  <p className="text-sm leading-relaxed">{simulation.clinicalInterpretation.patientFactors}</p>
                </div>
              </div>
              <div className="flex gap-4">
                <div className="w-10 h-10 bg-red-50 rounded-full flex items-center justify-center shrink-0 text-hospital-red">
                  <AlertTriangle size={20} />
                </div>
                <div>
                  <div className="text-[10px] font-bold text-hospital-red uppercase mb-1">Expected Impact</div>
                  <p className="text-sm leading-relaxed font-medium">{simulation.clinicalInterpretation.expectedImpact}</p>
                </div>
              </div>
            </div>
          </section>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Section 4: Dosage Evaluation */}
            <section className="bg-white p-4 rounded-lg border border-hospital-border shadow-sm">
              <div className="flex items-center gap-2 mb-4">
                <Activity size={16} className="text-hospital-blue" />
                <h3 className="text-[11px] font-bold text-hospital-muted uppercase tracking-widest">Dosage Evaluation</h3>
              </div>
              <div className="mb-3">
                <span className="text-[10px] text-hospital-muted uppercase font-bold">Current Dose:</span>
                <span className="ml-2 font-mono font-bold text-sm">{dose}mg</span>
              </div>
              <ul className="space-y-2">
                {simulation.dosageEvaluation.map((insight, i) => (
                  <li key={i} className="flex gap-2 text-xs leading-relaxed">
                    <div className="w-1 h-1 rounded-full bg-hospital-blue mt-1.5 shrink-0"></div>
                    {insight}
                  </li>
                ))}
              </ul>
            </section>

            {/* Section 5: Historical Context */}
            <section className="bg-white p-4 rounded-lg border border-hospital-border shadow-sm">
              <div className="flex items-center gap-2 mb-4">
                <History size={16} className="text-hospital-blue" />
                <h3 className="text-[11px] font-bold text-hospital-muted uppercase tracking-widest">Relevant Patient History</h3>
              </div>
              <div className="space-y-3">
                <div>
                  <div className="text-[9px] text-hospital-muted uppercase font-bold mb-1">Previous Responses</div>
                  <div className="text-xs font-medium">{simulation.patientHistory.response}</div>
                </div>
                <div className="p-2 bg-blue-50 border border-blue-100 rounded text-[11px] italic">
                  <span className="font-bold not-italic">AI Insight:</span> "{simulation.patientHistory.insight}"
                </div>
              </div>
            </section>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Section 6: Risk Interpretation */}
            <section className="bg-white p-4 rounded-lg border border-hospital-border shadow-sm">
              <div className="flex items-center gap-2 mb-4">
                <ShieldAlert size={16} className="text-hospital-red" />
                <h3 className="text-[11px] font-bold text-hospital-muted uppercase tracking-widest">Risk Interpretation</h3>
              </div>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-medium">Risk of treatment failure</span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded ${simulation.riskInterpretation.failure === 'High' ? 'bg-red-100 text-hospital-red' : 'bg-green-100 text-hospital-green'}`}>
                    {simulation.riskInterpretation.failure}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs font-medium">Risk of adverse effects</span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded ${simulation.riskInterpretation.adverse === 'High' ? 'bg-red-100 text-hospital-red' : 'bg-yellow-100 text-hospital-yellow'}`}>
                    {simulation.riskInterpretation.adverse}
                  </span>
                </div>
              </div>
            </section>

            {/* Section 7: Clinical Considerations */}
            <section className="bg-white p-4 rounded-lg border border-hospital-border shadow-sm">
              <div className="flex items-center gap-2 mb-4">
                <Info size={16} className="text-hospital-blue" />
                <h3 className="text-[11px] font-bold text-hospital-muted uppercase tracking-widest">Clinical Considerations</h3>
              </div>
              <ul className="space-y-2">
                {simulation.clinicalConsiderations.map((consideration, i) => (
                  <li key={i} className="flex gap-2 text-xs leading-relaxed">
                    <ArrowRight size={12} className="text-hospital-blue mt-0.5 shrink-0" />
                    <span className="font-medium">{consideration}</span>
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-hospital-border bg-white flex flex-col sm:flex-row gap-3">
          <button 
            onClick={onFinalize}
            className="flex-1 bg-hospital-blue text-white py-3 rounded font-bold text-sm hover:bg-blue-700 transition-colors shadow-md order-2 sm:order-1"
          >
            Proceed with Prescription
          </button>
          <button 
            onClick={onSwitch}
            className="flex-1 border border-hospital-blue text-hospital-blue py-3 rounded font-bold text-sm hover:bg-blue-50 transition-colors order-1 sm:order-2"
          >
            Modify Prescription
          </button>
          <button 
            onClick={() => setShowEvidence(true)}
            className="flex-1 border border-hospital-border bg-white text-hospital-muted py-3 rounded font-bold text-sm hover:bg-hospital-bg transition-colors order-3"
          >
            View Supporting Evidence
          </button>
        </div>

        {/* Supporting Evidence Modal */}
        <AnimatePresence>
          {showEvidence && simulation.supportingEvidence && (
            <SupportingEvidenceModal 
              evidence={simulation.supportingEvidence}
              alternatives={simulation.alternativeSuggestions}
              onClose={() => setShowEvidence(false)}
            />
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};

// --- Main App ---

function App() {
  const [patients, setPatients] = useState(MOCK_PATIENTS);
  const [drugs, setDrugs] = useState(MOCK_DRUGS);
  const [isAuthenticated, setIsAuthenticated] = useState(() => Boolean(localStorage.getItem('genomixai_doctor_name')));
  const [doctorName, setDoctorName] = useState(() => localStorage.getItem('genomixai_doctor_name') || 'Doctor');
  const [screen, setScreen] = useState('SEARCH');
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [selectedDrug, setSelectedDrug] = useState(null);
  const [simulationResult, setSimulationResult] = useState(null);
  const [isAddingMed, setIsAddingMed] = useState(false);
  const [showFinal, setShowFinal] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const normalizeDrug = (drugItem) => ({
      ...drugItem,
      class: drugItem.class || drugItem.class_ || 'Unknown'
    });

    const loadLiveData = async () => {
      try {
        const [patientsResponse, drugsResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/api/patients`),
            fetch(`${API_BASE_URL}/api/drugs`)
        ]);

        if (!cancelled && patientsResponse.ok) {
          const backendPatients = await patientsResponse.json();
          setPatients(backendPatients);
        }

        if (!cancelled && drugsResponse.ok) {
          const backendDrugs = await drugsResponse.json();
          setDrugs(backendDrugs.map(normalizeDrug));
        }
      } catch {
        // Keep the demo usable with bundled fallback data if the backend is offline.
      }
    };

    loadLiveData();

    return () => {
      cancelled = true;
    };
  }, []);

  const handleLogin = (username) => {
    const resolvedName = username?.trim() || 'Doctor';
    localStorage.setItem('genomixai_doctor_name', resolvedName);
    setDoctorName(resolvedName);
    setIsAuthenticated(true);
    setScreen('SEARCH');
  };

  const handleLogout = () => {
    localStorage.removeItem('genomixai_doctor_name');
    setDoctorName('Doctor');
    setIsAuthenticated(false);
    setSelectedPatient(null);
    setSelectedDrug(null);
    setSimulationResult(null);
    setIsAddingMed(false);
    setShowFinal(false);
    setScreen('SEARCH');
  };

  const handlePatientSelect = (p) => {
    setSelectedPatient(p);
    setScreen('RETRIEVAL');
  };

  const handleRetrievalComplete = () => {
    setScreen('CHART');
  };

  const handleAddMedication = () => {
    setIsAddingMed(true);
  };

  const handleDrugSelect = async (d) => {
    setSelectedDrug(d);
    setIsAddingMed(false);
    setScreen('SIMULATION');
  };

  // Add medication to patient (after simulation/finalize)
  const addMedicationToPatient = async (patientId, med) => {
    const res = await fetch(`${API_BASE_URL}/api/patient/${patientId}/medication`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(med)
    });
    if (!res.ok) throw new Error('Failed to add medication');
    const updatedPatient = await res.json();
    setPatients(patients => patients.map(p => p.id === updatedPatient.id ? updatedPatient : p));
    setSelectedPatient(updatedPatient);
  };

  // Discontinue medication
  const discontinueMedication = async (patientId, medId) => {
     const res = await fetch(`${API_BASE_URL}/api/patient/${patientId}/medication/${medId}`, {
      method: 'PATCH'
    });
    if (!res.ok) throw new Error('Failed to discontinue medication');
    const updatedPatient = await res.json();
    setPatients(patients => patients.map(p => p.id === updatedPatient.id ? updatedPatient : p));
    setSelectedPatient(updatedPatient);
  };

  // Create new patient
  const createPatient = async (patient) => {
     const res = await fetch(`${API_BASE_URL}/api/patient`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patient)
    });
    if (!res.ok) throw new Error('Failed to create patient');
    const newPatient = await res.json();
    setPatients(patients => [...patients, newPatient]);
    return newPatient;
  };

  // Update patient
  const updatePatient = async (patientId, update) => {
     const res = await fetch(`${API_BASE_URL}/api/patient/${patientId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(update)
    });
    if (!res.ok) throw new Error('Failed to update patient');
    const updatedPatient = await res.json();
    setPatients(patients => patients.map(p => p.id === updatedPatient.id ? updatedPatient : p));
    setSelectedPatient(updatedPatient);
  };

  const handleSimulationComplete = (res, dose, frequency) => {
    setSimulationResult({ res, dose, frequency });
  };

  const handleSwitchMed = () => {
    setSimulationResult(null);
    setSelectedDrug(null);
    setIsAddingMed(true);
    setScreen('CHART');
  };

  const handleCancelSimulation = () => {
    setSimulationResult(null);
  };

  const handleFinalize = () => {
    setSimulationResult(null);
    setShowFinal(true);
    setScreen('CHART');
    setTimeout(() => setShowFinal(false), 5000);
  };

  return (
    !isAuthenticated ? (
      <Login onLogin={handleLogin} />
    ) : (
    <div className="min-h-screen bg-hospital-bg flex flex-col">
      <Header doctorName={doctorName} onLogout={handleLogout} />
      
      <div className="flex-1 relative">
        <AnimatePresence mode="wait">
          {screen === 'SEARCH' && (
            <motion.div key="search" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <PatientSearch onSelect={handlePatientSelect} patients={patients} />
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
                <div className="fixed top-16 left-1/2 -translate-x-1/2 z-300">
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
            <motion.div key="simulation" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <SimulationInterface 
                patient={selectedPatient} 
                drug={selectedDrug} 
                onBack={() => setScreen('CHART')}
                onComplete={handleSimulationComplete}
                simulateDrug={async (payload) => {
                  const res = await fetch(`${API_BASE_URL}/api/simulate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                  });
                  if (!res.ok) throw new Error('Simulation failed');
                  return res.json();
                }}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Medication Selection Modal */}
        <AnimatePresence>
          {isAddingMed && (
            <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-150 flex items-center justify-center p-4">
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
                    const drugName = formData.get('drugName');
                    const doseVal = parseInt(formData.get('dose')) || 0;
                    const freqVal = formData.get('frequency');
                    
                    const foundDrug = drugs.find(d => d.name.toLowerCase() === drugName.toLowerCase()) || {
                      id: 'custom',
                      name: drugName,
                      class: 'Unknown',
                      standardDose: `${doseVal}mg`,
                      indications: []
                    };
                    handleDrugSelect(foundDrug);
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
                        {drugs.map(d => <option key={d.id} value={d.name} />)}
                      </datalist>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
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

        {/* Clinical Analysis Modal */}
        <AnimatePresence>
          {simulationResult && selectedPatient && selectedDrug && (
            <ClinicalAnalysisModal 
              patient={selectedPatient}
              drug={selectedDrug}
              simulation={simulationResult.res}
              dose={simulationResult.dose}
              frequency={simulationResult.frequency}
              onClose={handleCancelSimulation}
              onFinalize={handleFinalize}
              onSwitch={handleSwitchMed}
            />
          )}
        </AnimatePresence>
      </div>
    </div>
    )
  );
}

export default App;

import React, { useState } from 'react';
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
  CheckCircle2,
  X,
  Info,
  ArrowRight,
  Building,
  Check,
  MessageSquare
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { Patient, Medication } from '../types';
import { MOCK_PATIENTS } from '../constants';

export const PharmacistWorkspace = ({ user, onSignOut }: { user: any, onSignOut: () => void }) => {
  const [screen, setScreen] = useState<'QUEUE' | 'REVIEW'>('QUEUE');
  const [selectedCase, setSelectedCase] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('Pharmacist Review');

  const tabs = ['Pharmacist Review', 'Current Medications', 'Genomic Profile', 'Clinical Timeline'];

  // Mock Cases
  const MOCK_CASES = [
    {
      id: "REV-29381",
      patient: MOCK_PATIENTS[0],
      physician: "Dr. Sarah Ade",
      department: "Cardiology",
      submittedDate: "2026-07-19T06:15:00Z",
      priority: "High",
      status: "Awaiting Review",
      medications: 1,
      proposedDrug: { name: "Clopidogrel", dose: "75mg", freq: "Once Daily" },
      assessment: {
        reason: "Patient requires antiplatelet therapy post-PCI. Initial plan was Clopidogrel, but PGx indicates CYP2C19 *2/*2 (Poor Metabolizer).",
        guidance: "System flagged interaction. Requesting pharmacist review for alternative therapy selection."
      }
    },
    {
      id: "REV-29382",
      patient: MOCK_PATIENTS[1],
      physician: "Dr. Mark Okafor",
      department: "Internal Medicine",
      submittedDate: "2026-07-19T05:30:00Z",
      priority: "Medium",
      status: "In Progress",
      medications: 2,
      proposedDrug: { name: "Simvastatin", dose: "40mg", freq: "Once Daily" },
      assessment: {
        reason: "Initiating statin therapy for hyperlipidemia.",
        guidance: "SLCO1B1 *5/*5 (Low Activity). Increased risk of myopathy."
      }
    }
  ];

  return (
    <div className="flex-1 relative bg-hospital-bg">
      <AnimatePresence mode="wait">
        {screen === 'QUEUE' && (
          <motion.div key="queue" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div className="p-6">
              <div className="max-w-6xl mx-auto space-y-6">
                
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div>
                    <h1 className="text-2xl font-bold tracking-tight text-slate-900 mb-1">Medication Review Queue</h1>
                    <p className="text-sm text-hospital-muted">Manage pending pharmacogenomic safety assessments.</p>
                  </div>
                  <div className="flex items-center gap-3 bg-white border border-hospital-border rounded-lg p-1 w-full md:w-auto">
                    <button className="px-4 py-1.5 rounded-md bg-hospital-blue/10 text-hospital-blue font-bold text-xs">Pending (2)</button>
                    <button className="px-4 py-1.5 rounded-md text-hospital-muted hover:bg-slate-50 font-bold text-xs transition-colors">Completed (14)</button>
                  </div>
                </div>

                {/* KPI Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-white border border-hospital-border rounded-xl p-4 shadow-sm">
                    <div className="text-[10px] font-bold text-hospital-muted uppercase tracking-widest mb-1">Pending Reviews</div>
                    <div className="text-2xl font-light text-slate-900">2</div>
                  </div>
                  <div className="bg-white border border-hospital-border rounded-xl p-4 shadow-sm">
                    <div className="text-[10px] font-bold text-hospital-muted uppercase tracking-widest mb-1">High Priority</div>
                    <div className="text-2xl font-light text-hospital-red">1</div>
                  </div>
                  <div className="bg-white border border-hospital-border rounded-xl p-4 shadow-sm">
                    <div className="text-[10px] font-bold text-hospital-muted uppercase tracking-widest mb-1">Completed Today</div>
                    <div className="text-2xl font-light text-slate-900">14</div>
                  </div>
                  <div className="bg-white border border-hospital-border rounded-xl p-4 shadow-sm">
                    <div className="text-[10px] font-bold text-hospital-muted uppercase tracking-widest mb-1">Avg Turnaround</div>
                    <div className="text-2xl font-light text-slate-900">18m</div>
                  </div>
                </div>

                {/* Queue Table */}
                <div className="bg-white border border-hospital-border rounded-xl shadow-sm overflow-hidden">
                  <div className="p-4 border-b border-hospital-border flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-50/50">
                    <div className="relative max-w-sm w-full">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-hospital-muted" size={16} />
                      <input 
                        type="text" 
                        placeholder="Search patient or MRN..." 
                        className="w-full pl-9 pr-4 py-2 border border-hospital-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-hospital-blue/20"
                      />
                    </div>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-slate-50 border-b border-hospital-border">
                        <tr>
                          <th className="px-6 py-3 text-[10px] font-bold text-hospital-muted uppercase tracking-widest">Patient / MRN</th>
                          <th className="px-6 py-3 text-[10px] font-bold text-hospital-muted uppercase tracking-widest">Assessment</th>
                          <th className="px-6 py-3 text-[10px] font-bold text-hospital-muted uppercase tracking-widest">Ordering Physician</th>
                          <th className="px-6 py-3 text-[10px] font-bold text-hospital-muted uppercase tracking-widest">Priority</th>
                          <th className="px-6 py-3 text-[10px] font-bold text-hospital-muted uppercase tracking-widest">Status</th>
                          <th className="px-6 py-3 text-[10px] font-bold text-hospital-muted uppercase tracking-widest text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-hospital-border">
                        {MOCK_CASES.map((c) => (
                          <tr key={c.id} className="hover:bg-slate-50 transition-colors group cursor-pointer" onClick={() => { setSelectedCase(c); setScreen('REVIEW'); }}>
                            <td className="px-6 py-4">
                              <div className="font-bold text-slate-900">{c.patient.name}</div>
                              <div className="text-xs text-hospital-muted font-mono">{c.patient.mrn}</div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="font-semibold text-slate-900">{c.proposedDrug.name} {c.proposedDrug.dose}</div>
                              <div className="text-xs text-hospital-muted">1 medication proposed</div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="text-sm font-medium text-slate-900">{c.physician}</div>
                              <div className="text-xs text-hospital-muted">{c.department}</div>
                            </td>
                            <td className="px-6 py-4">
                              {c.priority === 'High' ? (
                                <span className="inline-flex items-center gap-1.5 text-xs font-bold text-hospital-red bg-red-50 px-2.5 py-1 rounded-md border border-red-100">
                                  <AlertTriangle size={12} /> High
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1.5 text-xs font-bold text-amber-600 bg-amber-50 px-2.5 py-1 rounded-md border border-amber-100">
                                  <AlertTriangle size={12} /> Medium
                                </span>
                              )}
                            </td>
                            <td className="px-6 py-4">
                              <span className="inline-flex items-center gap-1.5 text-[10px] font-bold text-slate-600 bg-slate-100 px-2 py-1 rounded uppercase tracking-wider">
                                {c.status}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-right">
                              <button className="text-hospital-blue font-bold text-xs hover:underline flex items-center justify-end gap-1 w-full opacity-0 group-hover:opacity-100 transition-opacity">
                                Open Review <ArrowRight size={14} />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

              </div>
            </div>
          </motion.div>
        )}

        {screen === 'REVIEW' && selectedCase && (
          <motion.div key="review" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-hospital-border bg-white sticky top-0 z-30 shadow-sm flex items-center gap-4">
              <button 
                onClick={() => setScreen('QUEUE')}
                className="p-2 hover:bg-slate-100 rounded-md transition-colors text-hospital-muted hover:text-slate-900"
              >
                <ArrowRight size={20} className="rotate-180" />
              </button>
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h2 className="text-xl font-bold text-slate-900 tracking-tight">{selectedCase.patient.name}</h2>
                  <span className="text-[10px] font-bold text-hospital-blue bg-blue-50 border border-blue-100 px-2 py-0.5 rounded-full uppercase tracking-wider">Review: {selectedCase.id}</span>
                </div>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-slate-500 font-medium text-xs">
                  <span>{selectedCase.patient.age}y / {selectedCase.patient.sex}</span>
                  <span className="text-slate-300">|</span>
                  <span className="font-mono">MRN: {selectedCase.patient.mrn}</span>
                </div>
              </div>
            </div>

            <div className="flex flex-1 overflow-hidden">
              {/* Main Review Area */}
              <div className="flex-1 overflow-y-auto bg-hospital-bg flex flex-col">
                
                {/* Horizontal Tabs */}
                <div className="bg-white border-b border-hospital-border px-6 flex items-center gap-6 overflow-x-auto">
                  {tabs.map(tab => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={`whitespace-nowrap py-4 text-sm font-bold border-b-2 transition-colors ${activeTab === tab ? 'border-hospital-blue text-hospital-blue' : 'border-transparent text-slate-500 hover:text-slate-900'}`}
                    >
                      {tab}
                    </button>
                  ))}
                </div>

                <div className="p-6 flex-1">
                  <div className="max-w-4xl mx-auto space-y-6">
                    
                    {activeTab === 'Pharmacist Review' && (
                      <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
                        {/* Physician Assessment */}
                        <div className="bg-white border border-hospital-border rounded-xl shadow-sm overflow-hidden">
                          <div className="px-5 py-4 bg-slate-50 border-b border-hospital-border flex justify-between items-center">
                            <div className="flex items-center gap-2">
                              <User size={16} className="text-hospital-blue" />
                              <span className="font-bold text-sm text-slate-900">Physician Assessment</span>
                            </div>
                            <div className="text-xs text-hospital-muted">Submitted by {selectedCase.physician}</div>
                          </div>
                          <div className="p-5 space-y-4">
                            <div>
                              <div className="text-[10px] font-bold text-hospital-muted uppercase tracking-widest mb-1.5">Proposed Medication</div>
                              <div className="flex items-center gap-3 p-3 bg-blue-50 border border-blue-100 rounded-lg">
                                <Pill size={18} className="text-hospital-blue" />
                                <div>
                                  <span className="font-bold text-sm text-hospital-blue">{selectedCase.proposedDrug.name}</span>
                                  <span className="text-sm text-slate-600 ml-2">{selectedCase.proposedDrug.dose} • {selectedCase.proposedDrug.freq}</span>
                                </div>
                              </div>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                               <div>
                                 <div className="text-[10px] font-bold text-hospital-muted uppercase tracking-widest mb-1.5">Clinical Rationale</div>
                                 <p className="text-sm text-slate-700 bg-slate-50 p-3 rounded-lg border border-slate-100">{selectedCase.assessment.reason}</p>
                               </div>
                               <div>
                                 <div className="text-[10px] font-bold text-hospital-muted uppercase tracking-widest mb-1.5">System Guidance</div>
                                 <p className="text-sm text-slate-700 bg-slate-50 p-3 rounded-lg border border-slate-100">{selectedCase.assessment.guidance}</p>
                               </div>
                            </div>
                          </div>
                        </div>

                  {/* Pharmacist Recommendation Form */}
                  <div className="bg-white border border-hospital-border rounded-xl shadow-sm overflow-hidden">
                    <div className="px-5 py-4 bg-slate-50 border-b border-hospital-border flex items-center gap-2">
                      <ClipboardList size={16} className="text-hospital-blue" />
                      <span className="font-bold text-sm text-slate-900">Pharmacist Review Panel</span>
                    </div>
                    <div className="p-5 space-y-5">
                      
                      <div>
                        <label className="text-[10px] font-bold text-hospital-muted uppercase mb-2 block tracking-widest">Primary Recommendation</label>
                        <select className="w-full border border-hospital-border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-hospital-blue/20 outline-none">
                          <option>Select recommendation...</option>
                          <option>Approve as prescribed</option>
                          <option>Approve with monitoring</option>
                          <option>Recommend alternative medication</option>
                          <option>Recommend dose adjustment</option>
                          <option>Return to physician for clarification</option>
                        </select>
                      </div>

                      {/* Structured Feedback Sections */}
                      <div className="space-y-4 pt-2 border-t border-slate-100">
                        <div>
                          <label className="text-[10px] font-bold text-hospital-muted uppercase mb-1.5 block tracking-widest">Genomic Considerations</label>
                          <textarea className="w-full border border-hospital-border rounded-lg p-3 text-sm focus:ring-2 focus:ring-hospital-blue/20 outline-none resize-none h-20" placeholder="Add notes regarding pharmacogenomic profile..."></textarea>
                        </div>
                        <div>
                          <label className="text-[10px] font-bold text-hospital-muted uppercase mb-1.5 block tracking-widest">Clinical Appropriateness & Alternatives</label>
                          <textarea className="w-full border border-hospital-border rounded-lg p-3 text-sm focus:ring-2 focus:ring-hospital-blue/20 outline-none resize-none h-20" placeholder="Discuss alternatives (e.g. Ticagrelor)..."></textarea>
                        </div>
                      </div>

                    </div>
                  </div>

                  {/* Collaboration Timeline */}
                  <div className="bg-white border border-hospital-border rounded-xl shadow-sm overflow-hidden">
                     <div className="px-5 py-4 bg-slate-50 border-b border-hospital-border flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <MessageSquare size={16} className="text-hospital-blue" />
                          <span className="font-bold text-sm text-slate-900">Communication & Timeline</span>
                        </div>
                     </div>
                     <div className="p-5">
                        <div className="relative pl-6 space-y-6">
                           <div className="absolute top-0 bottom-0 left-2 w-px bg-slate-200"></div>
                           
                           <div className="relative">
                              <div className="absolute -left-[29px] top-1 w-3 h-3 rounded-full border-2 border-hospital-blue bg-white"></div>
                              <div className="text-[10px] text-hospital-muted font-bold tracking-widest mb-0.5">TODAY, 06:15 UTC</div>
                              <div className="text-sm font-semibold text-slate-900 mb-1">Medication Assessment Submitted</div>
                              <div className="text-xs text-slate-600 bg-slate-50 p-2 rounded border border-slate-100">
                                {selectedCase.physician} ({selectedCase.department}) requested clinical pharmacy review due to PGx alert.
                              </div>
                           </div>

                           <div className="relative">
                              <div className="absolute -left-[29px] top-1 w-3 h-3 rounded-full border-2 border-slate-300 bg-white"></div>
                              <div className="text-[10px] text-hospital-muted font-bold tracking-widest mb-0.5">NOW</div>
                              <div className="text-sm font-semibold text-slate-900">Review Started</div>
                              <div className="text-xs text-slate-500 mt-1">Assigned to {user.name} ({user.department})</div>
                           </div>
                        </div>
                        
                        <div className="mt-6 flex gap-2">
                          <input type="text" placeholder="Add a comment or question to the thread..." className="flex-1 border border-hospital-border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-hospital-blue/20 outline-none" />
                          <button className="bg-hospital-blue text-white px-4 py-2 rounded-lg text-sm font-bold shadow-sm hover:bg-blue-800 transition-colors">Post</button>
                        </div>
                     </div>
                  </div>
                  </div>
                )}

                {activeTab === 'Current Medications' && (
                  <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
                    <div className="bg-white p-6 border border-slate-200 rounded-xl shadow-sm">
                      <div className="flex items-center gap-2 mb-6 pb-2 border-b border-slate-100">
                        <Pill size={18} className="text-hospital-blue" />
                        <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Active Prescriptions</h3>
                      </div>
                      <div className="space-y-4">
                        {selectedCase.patient.medications.map((med: any, i: number) => (
                          <div key={i} className="p-4 border border-slate-200 rounded-lg flex items-center justify-between">
                            <div>
                              <div className="font-bold text-slate-900">{med.name}</div>
                              <div className="text-sm text-slate-500">{med.dose} • {med.frequency}</div>
                            </div>
                            <span className="text-xs text-slate-400">Prescribed: Oct 2025</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'Genomic Profile' && (
                  <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
                    <div className="bg-white p-6 border border-slate-200 rounded-xl shadow-sm">
                      <div className="flex items-center gap-2 mb-6 pb-2 border-b border-slate-100">
                        <User size={18} className="text-hospital-blue" />
                        <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Pharmacogenomic Profile</h3>
                      </div>
                      <div className="p-5 border border-slate-200 rounded-xl bg-slate-50">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h4 className="font-bold text-lg text-slate-900">CYP2C19</h4>
                            <div className="text-xs font-semibold text-slate-400 font-mono mt-0.5">Variant: *2 / *2 (Homozygous Loss-of-Function)</div>
                          </div>
                          <span className="px-2.5 py-0.5 bg-red-50 text-hospital-red border border-red-100 text-[10px] font-bold rounded uppercase">Poor Metabolizer</span>
                        </div>
                        <div className="text-xs font-semibold text-slate-700 leading-relaxed border-t border-slate-200 pt-3">
                          No functional CYP2C19 enzyme activity is produced. Affects the biological conversion and bioactivation of all prodrugs requiring CYP2C19 first-pass or second-pass hepatic metabolism.
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'Clinical Timeline' && (
                  <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
                    <div className="bg-white p-6 border border-slate-200 rounded-xl shadow-sm text-center py-12">
                      <History className="mx-auto text-slate-300 mb-4" size={32} />
                      <h3 className="text-sm font-bold text-slate-900 mb-2">No Recent Clinical Events</h3>
                      <p className="text-xs text-slate-500 max-w-md mx-auto">This patient does not have recent clinical events logged in the EHR system.</p>
                    </div>
                  </div>
                )}

                </div>
              </div>
            </div>

            {/* Action Sidebar */}
              <div className="w-80 border-l border-hospital-border bg-white p-5 overflow-y-auto flex flex-col justify-between">
                <div>
                  <h3 className="text-xs font-bold text-slate-900 uppercase tracking-widest mb-4">Decision Panel</h3>
                  
                  <div className="space-y-4 mb-8">
                    <div>
                      <div className="text-[10px] text-hospital-muted font-bold uppercase tracking-widest">Status</div>
                      <div className="text-sm font-semibold text-amber-600">In Progress</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-hospital-muted font-bold uppercase tracking-widest">Assigned Pharmacist</div>
                      <div className="text-sm font-semibold text-slate-900">{user.name}</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-hospital-muted font-bold uppercase tracking-widest">Target Completion</div>
                      <div className="text-sm font-semibold text-slate-900">Today, 08:15 UTC</div>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                   <button onClick={() => { setScreen('QUEUE'); }} className="w-full bg-hospital-blue text-white py-3 rounded-lg font-bold text-sm shadow-sm hover:bg-blue-800 transition-colors">
                     Submit Final Recommendation
                   </button>
                   <button className="w-full bg-slate-100 text-slate-700 py-3 rounded-lg font-bold text-sm hover:bg-slate-200 transition-colors border border-slate-200">
                     Save Draft
                   </button>
                   <button onClick={() => setScreen('QUEUE')} className="w-full bg-white text-hospital-red py-3 rounded-lg font-bold text-sm hover:bg-red-50 transition-colors border border-red-200">
                     Cancel Review
                   </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

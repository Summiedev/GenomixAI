import React, { useState } from 'react';
import { 
  Lock, 
  Building, 
  User, 
  FileText, 
  Upload, 
  CheckCircle, 
  Shield, 
  Stethoscope, 
  Microscope, 
  Pill, 
  Activity, 
  Check,
  ArrowLeft
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

type AuthView = 'LOGIN' | 'REQUEST_ACCESS' | 'SUBMITTED';

export const Auth = ({ 
  onAuthenticated, 
  initialView = 'LOGIN', 
  onBack 
}: { 
  onAuthenticated: (user: any) => void;
  initialView?: 'LOGIN' | 'REQUEST_ACCESS';
  onBack?: () => void;
}) => {
  const [view, setView] = useState<AuthView>(initialView);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Mock successful authentication based on email
    if (email.toLowerCase().includes('pharmacist')) {
      onAuthenticated({
        name: "Dr. James Okafor",
        organization: "Lagos Heart Institute",
        department: "Clinical Pharmacy",
        role: "Pharmacist"
      });
    } else {
      onAuthenticated({
        name: "Dr. Sarah Ade",
        organization: "Lagos Heart Institute",
        department: "Cardiology",
        role: "Physician"
      });
    }
  };

  const handleRequestAccessSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setView('SUBMITTED');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex font-sans text-slate-900">
      <AnimatePresence mode="wait">
        {view === 'LOGIN' && (
          <motion.div 
            key="login"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex w-full min-h-screen"
          >
            {/* Left Pane - Branding & Introduction (55%) */}
            <div className="hidden lg:flex w-[55%] bg-white border-r border-slate-200 flex-col p-16 xl:p-24 relative overflow-y-auto">
              
              <div className="max-w-xl mx-auto flex flex-col h-full">
                
                {/* Header */}
                <div className="mb-16">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-hospital-blue text-white rounded flex items-center justify-center font-bold text-2xl italic shadow-sm">G</div>
                    <span className="font-bold tracking-tight text-2xl text-hospital-blue uppercase">GenomixAI</span>
                  </div>
                  <p className="text-hospital-muted font-medium uppercase tracking-widest text-xs">
                    Precision Medicine. Personalized Prescribing.
                  </p>
                </div>
                
                {/* Main Content */}
                <div className="flex-1">
                  <h1 className="text-4xl lg:text-5xl font-light mb-6 leading-tight text-slate-900 tracking-tight">
                    Transforming medication decisions through <span className="font-bold text-hospital-blue">pharmacogenomic intelligence.</span>
                  </h1>
                  
                  <p className="text-slate-600 text-lg leading-relaxed mb-12">
                    GenomixAI helps healthcare professionals evaluate medication compatibility using patient-specific genomic profiles, clinical history, and evidence-based insights.
                  </p>

                  {/* Feature Blocks */}
                  <div className="space-y-8">
                    
                    <div className="flex gap-4">
                      <div className="w-12 h-12 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center shrink-0">
                        <User size={24} className="text-hospital-blue" />
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-slate-900 mb-1">Patient-Centered Insights</h3>
                        <p className="text-sm text-slate-600 leading-relaxed">
                          Understand how individual biological differences influence medication response.
                        </p>
                      </div>
                    </div>

                    <div className="flex gap-4">
                      <div className="w-12 h-12 rounded-lg bg-emerald-50 border border-emerald-100 flex items-center justify-center shrink-0">
                        <Shield size={24} className="text-emerald-600" />
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-slate-900 mb-1">Safer Prescribing</h3>
                        <p className="text-sm text-slate-600 leading-relaxed">
                          Identify potential medication risks before treatment decisions are made.
                        </p>
                      </div>
                    </div>

                    <div className="flex gap-4">
                      <div className="w-12 h-12 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center shrink-0">
                        <Activity size={24} className="text-indigo-600" />
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-slate-900 mb-1">Clinical Decision Support</h3>
                        <p className="text-sm text-slate-600 leading-relaxed">
                          Support physicians with transparent, evidence-backed assessments.
                        </p>
                      </div>
                    </div>

                  </div>
                </div>

                {/* Footer */}
                <div className="pt-12 mt-12 border-t border-slate-100">
                  <div className="flex items-center gap-3 text-sm text-slate-500 font-medium">
                    <Building size={18} className="text-slate-400" />
                    Trusted clinical intelligence for healthcare organizations
                  </div>
                </div>

              </div>
            </div>

            {/* Right Pane - Login Portal (45%) */}
            <div className="w-full lg:w-[45%] bg-slate-50 flex flex-col items-center justify-center p-8 lg:p-16 relative">
              
              {onBack && (
                <button 
                  onClick={onBack}
                  className="absolute top-6 left-6 text-xs font-bold text-slate-500 hover:text-slate-800 flex items-center gap-1.5 transition-colors"
                >
                  <ArrowLeft size={14} /> Back to Home
                </button>
              )}
              
              <div className="w-full max-w-md">
                
                {/* Mobile Header */}
                <div className="lg:hidden flex flex-col items-center mb-10 text-center">
                  <div className="w-12 h-12 bg-hospital-blue text-white rounded-lg flex items-center justify-center font-bold text-2xl italic shadow-sm mb-4">G</div>
                  <span className="font-bold tracking-tight text-xl text-hospital-blue uppercase mb-2">GenomixAI</span>
                  <p className="text-slate-500 text-sm">Secure clinical workspace</p>
                </div>

                {/* Login Card */}
                <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-8 md:p-10">
                  
                  <div className="mb-8 text-center">
                    <h2 className="text-2xl font-bold text-slate-900 mb-2">Welcome back</h2>
                    <p className="text-sm text-slate-500">Sign in to your healthcare workspace</p>
                  </div>

                  <form onSubmit={handleLoginSubmit} className="space-y-5">
                    
                    <div>
                      <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-2">
                        Email Address
                      </label>
                      <input 
                        type="email" 
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-hospital-blue/20 focus:border-hospital-blue transition-colors text-sm bg-slate-50 focus:bg-white"
                        placeholder="doctor@hospital.com or pharmacist@hospital.com"
                      />
                    </div>
                    
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                          Password
                        </label>
                        <a href="#" className="text-xs font-medium text-hospital-blue hover:underline">Forgot password?</a>
                      </div>
                      <input 
                        type="password" 
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-hospital-blue/20 focus:border-hospital-blue transition-colors text-sm bg-slate-50 focus:bg-white"
                        placeholder="Enter password"
                      />
                    </div>

                    <div className="flex items-center mt-4">
                      <input 
                        id="remember-me" 
                        name="remember-me" 
                        type="checkbox" 
                        className="h-4 w-4 text-hospital-blue focus:ring-hospital-blue border-slate-300 rounded"
                      />
                      <label htmlFor="remember-me" className="ml-2 block text-sm text-slate-600">
                        Remember this device
                      </label>
                    </div>

                    <button 
                      type="submit"
                      className="w-full bg-hospital-blue text-white py-3.5 rounded-lg font-bold text-sm hover:bg-blue-800 transition-colors mt-6 shadow-sm"
                    >
                      Sign In
                    </button>
                    
                  </form>

                  <div className="mt-6 pt-6 border-t border-slate-100">
                    <button 
                      onClick={() => setView('REQUEST_ACCESS')}
                      className="w-full border border-slate-300 text-slate-700 py-3.5 rounded-lg font-bold text-sm hover:bg-slate-50 transition-colors"
                    >
                      Request Professional Access
                    </button>
                  </div>

                </div>

                {/* Security Footers */}
                <div className="mt-8 text-center">
                  <p className="text-xs text-slate-500 font-medium mb-4">
                    Access is restricted to verified healthcare professionals.
                  </p>
                  
                  <div className="flex justify-center gap-6 text-xs text-slate-400">
                    <div className="flex items-center gap-1.5">
                      <Check size={14} className="text-emerald-500" />
                      Organization verified
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Check size={14} className="text-emerald-500" />
                      Secure healthcare environment
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </motion.div>
        )}

        {view === 'REQUEST_ACCESS' && (
          <motion.div 
            key="request"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="w-full min-h-screen py-12 px-4 flex flex-col items-center"
          >
            <div className="w-full max-w-3xl">
              <div className="flex justify-between items-center mb-6">
                <button 
                  onClick={() => setView('LOGIN')}
                  className="text-sm text-slate-500 hover:text-slate-900 flex items-center gap-2 transition-colors"
                >
                  ← Back to Login
                </button>
                {onBack && (
                  <button 
                    onClick={onBack}
                    className="text-sm text-slate-500 hover:text-slate-900 flex items-center gap-2 transition-colors"
                  >
                    Back to Home →
                  </button>
                )}
              </div>

              <div className="mb-8">
                <h1 className="text-3xl font-bold text-slate-900 mb-2">Request Professional Access</h1>
                <p className="text-slate-600">
                  GenomixAI is restricted to verified healthcare professionals. Please provide your credentials for organization review.
                </p>
              </div>

              <form onSubmit={handleRequestAccessSubmit} className="space-y-6">
                {/* Section 1: Professional Info */}
                <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                  <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex items-center gap-3">
                    <User size={18} className="text-hospital-blue" />
                    <h2 className="font-bold text-slate-900">Professional Information</h2>
                  </div>
                  <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Full Name</label>
                      <input type="text" required className="w-full px-3 py-2 border border-slate-300 rounded focus:ring-2 focus:ring-hospital-blue/20 focus:border-hospital-blue text-sm" placeholder="Dr. First Last" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Professional Email</label>
                      <input type="email" required className="w-full px-3 py-2 border border-slate-300 rounded focus:ring-2 focus:ring-hospital-blue/20 focus:border-hospital-blue text-sm" placeholder="name@hospital.org" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Phone Number</label>
                      <input type="tel" required className="w-full px-3 py-2 border border-slate-300 rounded focus:ring-2 focus:ring-hospital-blue/20 focus:border-hospital-blue text-sm" placeholder="+1 (555) 000-0000" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Professional Role</label>
                      <select required className="w-full px-3 py-2 border border-slate-300 rounded focus:ring-2 focus:ring-hospital-blue/20 focus:border-hospital-blue text-sm bg-white">
                        <option value="">Select Role...</option>
                        <option>Physician</option>
                        <option>Clinical Pharmacist</option>
                        <option>Genetic Counselor</option>
                        <option>Laboratory Scientist</option>
                        <option>Healthcare Researcher</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Specialty</label>
                      <select required className="w-full px-3 py-2 border border-slate-300 rounded focus:ring-2 focus:ring-hospital-blue/20 focus:border-hospital-blue text-sm bg-white">
                        <option value="">Select Specialty...</option>
                        <option>Cardiology</option>
                        <option>Internal Medicine</option>
                        <option>Oncology</option>
                        <option>Pharmacy</option>
                        <option>Genomics</option>
                        <option>Other</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Professional License Number</label>
                      <input type="text" required className="w-full px-3 py-2 border border-slate-300 rounded focus:ring-2 focus:ring-hospital-blue/20 focus:border-hospital-blue text-sm" placeholder="e.g. MD123456" />
                    </div>
                  </div>
                </div>

                {/* Section 2: Organization Info */}
                <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                  <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex items-center gap-3">
                    <Building size={18} className="text-hospital-blue" />
                    <h2 className="font-bold text-slate-900">Organization Verification</h2>
                  </div>
                  <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="md:col-span-2">
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Hospital / Clinic Name</label>
                      <input type="text" required className="w-full px-3 py-2 border border-slate-300 rounded focus:ring-2 focus:ring-hospital-blue/20 focus:border-hospital-blue text-sm" placeholder="Enter full organization name" />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Department</label>
                      <select required className="w-full px-3 py-2 border border-slate-300 rounded focus:ring-2 focus:ring-hospital-blue/20 focus:border-hospital-blue text-sm bg-white">
                        <option value="">Select Department...</option>
                        <option>Cardiology</option>
                        <option>Internal Medicine</option>
                        <option>Pharmacy</option>
                        <option>Laboratory</option>
                        <option>Research</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Position</label>
                      <input type="text" required className="w-full px-3 py-2 border border-slate-300 rounded focus:ring-2 focus:ring-hospital-blue/20 focus:border-hospital-blue text-sm" placeholder="e.g. Consultant Physician" />
                    </div>
                  </div>
                </div>

                {/* Section 3: Document Upload */}
                <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                  <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex items-center gap-3">
                    <FileText size={18} className="text-hospital-blue" />
                    <h2 className="font-bold text-slate-900">Verification Documents</h2>
                  </div>
                  <div className="p-6">
                    <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center hover:bg-slate-50 transition-colors cursor-pointer">
                      <Upload size={32} className="mx-auto text-slate-400 mb-4" />
                      <p className="text-sm font-medium text-slate-900 mb-1">Click to upload professional license or hospital ID</p>
                      <p className="text-xs text-slate-500">PDF, JPG, or PNG (Max 5MB)</p>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end gap-4">
                  <button 
                    type="button"
                    onClick={() => setView('LOGIN')}
                    className="px-6 py-3 border border-slate-300 text-slate-700 rounded-lg font-bold text-sm hover:bg-slate-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit"
                    className="px-8 py-3 bg-hospital-blue text-white rounded-lg font-bold text-sm hover:bg-blue-800 transition-colors"
                  >
                    Submit Request
                  </button>
                </div>
              </form>
            </div>
          </motion.div>
        )}

        {view === 'SUBMITTED' && (
          <motion.div 
            key="submitted"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full min-h-screen flex items-center justify-center p-4"
          >
            <div className="bg-white border border-slate-200 rounded-xl shadow-sm max-w-md w-full p-8 text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle size={32} className="text-green-600" />
              </div>
              
              <h1 className="text-2xl font-bold text-slate-900 mb-2">Access Request Submitted</h1>
              <p className="text-sm text-slate-600 mb-8 leading-relaxed">
                Your professional credentials have been received and will be reviewed by your organization administrator. You will receive an email once your access is approved.
              </p>

              <div className="text-left bg-slate-50 border border-slate-200 rounded-lg p-5 mb-8">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4">Verification Status</h3>
                
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center text-white shrink-0">
                      <CheckCircle size={12} />
                    </div>
                    <span className="text-sm font-medium text-slate-900">Request Submitted</span>
                  </div>
                  <div className="flex items-center gap-3 opacity-50">
                    <div className="w-5 h-5 rounded-full border-2 border-slate-300 shrink-0"></div>
                    <span className="text-sm font-medium text-slate-900">Credential Verification</span>
                  </div>
                  <div className="flex items-center gap-3 opacity-50">
                    <div className="w-5 h-5 rounded-full border-2 border-slate-300 shrink-0"></div>
                    <span className="text-sm font-medium text-slate-900">Organization Approval</span>
                  </div>
                  <div className="flex items-center gap-3 opacity-50">
                    <div className="w-5 h-5 rounded-full border-2 border-slate-300 shrink-0"></div>
                    <span className="text-sm font-medium text-slate-900">Account Activated</span>
                  </div>
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <button 
                  onClick={() => setView('LOGIN')}
                  className="w-full bg-slate-900 text-white py-3 rounded-lg font-bold text-sm hover:bg-slate-800 transition-colors"
                >
                  Return to Login
                </button>
                {onBack && (
                  <button 
                    onClick={onBack}
                    className="w-full border border-slate-300 text-slate-700 py-3 rounded-lg font-bold text-sm hover:bg-slate-50 transition-colors"
                  >
                    Go back to Home Page
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

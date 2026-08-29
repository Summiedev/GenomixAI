import React, { useState, useEffect } from 'react';
import { 
  Building, Shield, Search, History, ClipboardList, 
  AlertTriangle, FileText, Users, User, ArrowRight, Menu, 
  Lock, Activity, CheckCircle2, Stethoscope, Pill, Check, 
  ChevronRight, X, ArrowUpRight, Database, Dna, FileSearch, HeartPulse
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface LandingPageProps {
  onSignIn: () => void;
  onRequestAccess: () => void;
}

const FADE_UP = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] } }
};

const STAGGER = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.15 } }
};

export const LandingPage: React.FC<LandingPageProps> = ({ onSignIn, onRequestAccess }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [heroStep, setHeroStep] = useState(0);
  const [activeTab, setActiveTab] = useState<'genomic' | 'review'>('genomic');

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setHeroStep((prev) => (prev + 1) % 3);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  const workflowSteps = [
    { num: 1, title: "EHR Synchronization", desc: "Genomix seamlessly syncs with existing EHR to pull patient medical history and previous genomic testing results." },
    { num: 2, title: "Data Integration", desc: "The platform integrates existing genetic markers with clinical history, mapping genotypes to precise clinical phenotypes." },
    { num: 3, title: "Prescribing Workflow", desc: "Physicians order medications as usual within their clinical interface." },
    { num: 4, title: "Real-time Assessment", desc: "Proposed therapies are instantly cross-referenced against the patient's genetic profile and clinical context." },
    { num: 5, title: "Evidence-Based Guidance", desc: "Actionable CPIC guidelines trigger if a gene-drug interaction is detected." },
    { num: 6, title: "Safer Outcomes", desc: "Alternative drugs or adjusted doses are selected, preventing adverse drug events." }
  ];

  const HeroShowcase = () => (
    <div className="relative w-full aspect-[4/3] md:aspect-auto md:h-[540px] bg-slate-900 border border-slate-800 rounded-2xl shadow-[0_20px_50px_rgb(0,0,0,0.3)] overflow-hidden flex flex-col group">
      <div className="h-12 bg-slate-900 border-b border-slate-800 flex items-center px-4 justify-between shrink-0">
        <div className="flex gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-slate-700 group-hover:bg-red-500 transition-colors duration-300" />
          <div className="w-2.5 h-2.5 rounded-full bg-slate-700 group-hover:bg-amber-500 transition-colors duration-300 delay-75" />
          <div className="w-2.5 h-2.5 rounded-full bg-slate-700 group-hover:bg-emerald-500 transition-colors duration-300 delay-150" />
        </div>
        <div className="text-[10px] font-mono text-slate-500 uppercase tracking-widest font-semibold flex items-center gap-2">
          <Dna size={12} />
          PGx Engine Activity
        </div>
      </div>
      <div className="flex-1 relative bg-slate-950 overflow-hidden p-4 sm:p-6 md:p-8 flex items-center justify-center">
        {/* Animated Background Grid */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:2rem_2rem] [mask-image:radial-gradient(ellipse_60%_60%_at_50%_50%,#000_10%,transparent_100%)] opacity-20 pointer-events-none" />

        <AnimatePresence mode="wait">
          {heroStep === 0 && (
            <motion.div 
              key="step0"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20, filter: 'blur(4px)' }}
              transition={{ duration: 0.6 }}
              className="w-full max-w-sm bg-slate-900 border border-slate-700 rounded-xl shadow-2xl p-6 flex flex-col items-center text-center relative z-10"
            >
              <div className="w-16 h-16 rounded-full bg-blue-900/30 border border-blue-500/30 flex items-center justify-center text-blue-400 mb-6">
                <Dna size={32} />
              </div>
              <h3 className="text-white font-medium text-lg mb-2">Syncing Existing Records</h3>
              <p className="text-slate-400 text-sm leading-relaxed mb-6">
                Pulling existing genomic data from EHR and analyzing against 120+ pharmacogenomic pathways...
              </p>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: '100%' }}
                  transition={{ duration: 4.5, ease: "linear" }}
                  className="h-full bg-blue-500"
                />
              </div>
            </motion.div>
          )}

          {heroStep === 1 && (
            <motion.div 
              key="step1"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20, filter: 'blur(4px)' }}
              transition={{ duration: 0.6 }}
              className="w-full flex flex-col gap-4 relative z-10"
            >
              <div className="flex gap-4 items-center justify-center">
                <motion.div 
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  className="w-48 bg-slate-900 border border-slate-700 rounded-xl p-4 shadow-xl"
                >
                  <div className="text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-1">Genotype</div>
                  <div className="text-base font-semibold text-white mb-2">CYP2C19 *2/*2</div>
                  <div className="text-xs text-blue-400 bg-blue-900/20 border border-blue-800/50 px-2 py-1 rounded inline-block">
                    Poor Metabolizer
                  </div>
                </motion.div>

                <div className="w-8 h-px bg-slate-700 relative">
                  <motion.div 
                    animate={{ x: [0, 32] }}
                    transition={{ repeat: Infinity, duration: 1.5 }}
                    className="absolute w-2 h-2 rounded-full bg-blue-500 -top-[3px]"
                  />
                </div>

                <motion.div 
                  initial={{ x: 20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.2 }}
                  className="w-48 bg-slate-900 border border-slate-700 rounded-xl p-4 shadow-xl"
                >
                  <div className="text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-1">Proposed Therapy</div>
                  <div className="text-base font-semibold text-white mb-2">Clopidogrel</div>
                  <div className="text-xs text-slate-400 bg-slate-800 px-2 py-1 rounded inline-block">
                    Antiplatelet (75mg)
                  </div>
                </motion.div>
              </div>

              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.8 }}
                className="mx-auto mt-4 bg-red-950/40 border border-red-900/50 rounded-xl p-4 max-w-sm w-full text-center"
              >
                <div className="flex items-center justify-center gap-2 text-red-400 mb-2">
                  <AlertTriangle size={16} />
                  <span className="text-sm font-semibold">Interaction Detected</span>
                </div>
                <div className="text-xs text-red-200/70">
                  Patient metabolism indicates severely reduced active metabolite formation.
                </div>
              </motion.div>
            </motion.div>
          )}

          {heroStep === 2 && (
            <motion.div 
              key="step2"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, filter: 'blur(4px)' }}
              transition={{ duration: 0.6 }}
              className="w-full max-w-md bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden relative z-10"
            >
              <div className="bg-emerald-950/40 border-b border-emerald-900/50 p-4 flex items-center justify-between">
                <div className="flex items-center gap-2 text-emerald-400">
                  <CheckCircle2 size={18} />
                  <span className="font-semibold text-sm">Evidence-Based Alternative</span>
                </div>
                <span className="text-[10px] font-bold text-emerald-500 bg-emerald-900/30 px-2 py-0.5 rounded">CPIC Level A</span>
              </div>
              <div className="p-6">
                <div className="mb-6">
                  <div className="text-xl font-semibold text-white mb-1">Ticagrelor 90mg</div>
                  <div className="text-sm text-slate-400">Recommended Alternative Therapy</div>
                </div>
                <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 mb-6">
                  <div className="text-sm text-slate-300 leading-relaxed">
                    Unlike Clopidogrel, Ticagrelor does not require hepatic activation via CYP2C19. It provides consistent platelet inhibition regardless of the patient's poor metabolizer status.
                  </div>
                </div>
                <div className="flex justify-end gap-3">
                  <div className="px-5 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-semibold shadow-md flex items-center gap-2">
                    <Check size={16} /> Update Prescription
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-white font-sans text-slate-900 selection:bg-blue-100 overflow-x-hidden">
      
      {/* Navigation */}
      <header 
        className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
          scrolled ? 'bg-white/90 backdrop-blur-md border-b border-slate-200 shadow-sm py-3' : 'bg-transparent py-5'
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-blue-600 text-white rounded-lg flex items-center justify-center font-bold shadow-sm">
              <Dna size={18} />
            </div>
            <span className="font-bold tracking-tight text-slate-900 text-xl">Genomix</span>
          </div>
            
          <nav className="hidden md:flex items-center gap-8">
            <a href="#platform" className="text-sm font-semibold text-slate-600 hover:text-slate-900 transition-colors relative group">
              Platform
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-blue-600 transition-all group-hover:w-full"></span>
            </a>
            <a href="#workflow" className="text-sm font-semibold text-slate-600 hover:text-slate-900 transition-colors relative group">
              Workflow
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-blue-600 transition-all group-hover:w-full"></span>
            </a>
            <a href="#organizations" className="text-sm font-semibold text-slate-600 hover:text-slate-900 transition-colors relative group">
              Organizations
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-blue-600 transition-all group-hover:w-full"></span>
            </a>
            <a href="#security" className="text-sm font-semibold text-slate-600 hover:text-slate-900 transition-colors relative group">
              Security
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-blue-600 transition-all group-hover:w-full"></span>
            </a>
          </nav>

          <div className="flex items-center gap-4">
            <button 
              onClick={onSignIn}
              className="hidden sm:inline-block text-sm font-semibold text-slate-600 hover:text-slate-900 transition-colors"
            >
              Sign In
            </button>
            <button 
              onClick={onRequestAccess}
              className="hidden sm:inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm px-4 py-2 rounded-lg transition-all hover:shadow-md hover:-translate-y-0.5"
            >
              Request Access
            </button>
            <button 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            >
              {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden border-t border-slate-200 bg-white px-4 py-4 space-y-4 shadow-lg absolute top-full inset-x-0"
            >
              <a href="#platform" onClick={() => setMobileMenuOpen(false)} className="block text-sm font-semibold text-slate-600 p-2 hover:bg-slate-50 rounded">Platform</a>
              <a href="#workflow" onClick={() => setMobileMenuOpen(false)} className="block text-sm font-semibold text-slate-600 p-2 hover:bg-slate-50 rounded">Workflow</a>
              <a href="#organizations" onClick={() => setMobileMenuOpen(false)} className="block text-sm font-semibold text-slate-600 p-2 hover:bg-slate-50 rounded">Organizations</a>
              <a href="#security" onClick={() => setMobileMenuOpen(false)} className="block text-sm font-semibold text-slate-600 p-2 hover:bg-slate-50 rounded">Security</a>
              <div className="pt-4 border-t border-slate-100 flex flex-col gap-3">
                <button onClick={() => { onSignIn(); setMobileMenuOpen(false); }} className="w-full text-center text-sm font-semibold text-slate-700 py-2 border border-slate-200 rounded-lg">Sign In</button>
                <button onClick={() => { onRequestAccess(); setMobileMenuOpen(false); }} className="w-full bg-blue-600 text-white text-sm font-medium px-4 py-2.5 rounded-lg text-center">Request Access</button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      {/* Hero Section */}
      <section className="pt-32 pb-20 md:pt-40 md:pb-32 bg-slate-50 relative border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-24 items-center">
            
            <motion.div 
              initial="hidden"
              animate="visible"
              variants={STAGGER}
              className="space-y-8"
            >
              <motion.h1 variants={FADE_UP} className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-slate-900 leading-[1.15]">
                Actionable insights from patient history and genomic data.
              </motion.h1>

              <motion.p variants={FADE_UP} className="text-slate-600 text-lg leading-relaxed max-w-lg">
                Genomix integrates a patient's existing medical history and genetic profile to provide precise, personalized medication insights. Prevent adverse drug events and optimize therapies right at the point of care.
              </motion.p>

              <motion.div variants={FADE_UP} className="flex flex-col sm:flex-row gap-4 pt-2">
                <button 
                  onClick={onRequestAccess}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm md:text-base px-6 py-3.5 rounded-lg transition-all shadow-[0_4px_14px_0_rgb(37,99,235,0.2)] hover:shadow-[0_6px_20px_rgba(37,99,235,0.3)] hover:-translate-y-0.5 flex items-center justify-center gap-2"
                >
                  Request Professional Access
                </button>
                <button 
                  onClick={onSignIn}
                  className="bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-medium text-sm md:text-base px-6 py-3.5 rounded-lg transition-all flex items-center justify-center gap-2"
                >
                  Sign In
                </button>
              </motion.div>
            </motion.div>

            <motion.div 
              initial={{ opacity: 0, scale: 0.95, filter: 'blur(10px)' }}
              animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
              <HeroShowcase />
            </motion.div>

          </div>
        </div>
      </section>

      {/* Core Value / Features */}
      <section className="py-20 bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10 lg:gap-16">
            
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.5 }}
              className="flex flex-col items-center text-center space-y-4"
            >
              <div className="w-16 h-16 bg-slate-50 border border-slate-200 rounded-2xl flex items-center justify-center text-blue-600 mb-2">
                <Dna size={28} />
              </div>
              <h3 className="text-xl font-semibold text-slate-900">Phenotype Translation</h3>
              <p className="text-slate-600 leading-relaxed">
                Automatically convert raw genetic variants (e.g., CYP2C19 *2/*2) into clear, standardized metabolizer phenotypes.
              </p>
            </motion.div>

            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="flex flex-col items-center text-center space-y-4"
            >
              <div className="w-16 h-16 bg-slate-50 border border-slate-200 rounded-2xl flex items-center justify-center text-blue-600 mb-2">
                <FileSearch size={28} />
              </div>
              <h3 className="text-xl font-semibold text-slate-900">CPIC Guidelines Built-in</h3>
              <p className="text-slate-600 leading-relaxed">
                Clinical Pharmacogenetics Implementation Consortium (CPIC) guidelines are deeply integrated into the assessment engine.
              </p>
            </motion.div>

            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="flex flex-col items-center text-center space-y-4"
            >
              <div className="w-16 h-16 bg-slate-50 border border-slate-200 rounded-2xl flex items-center justify-center text-blue-600 mb-2">
                <HeartPulse size={28} />
              </div>
              <h3 className="text-xl font-semibold text-slate-900">Prevent Adverse Events</h3>
              <p className="text-slate-600 leading-relaxed">
                Catch severe gene-drug interactions before the prescription is finalized, recommending safer, more effective alternatives.
              </p>
            </motion.div>

          </div>
        </div>
      </section>

      {/* Clinical Workflow Section */}
      <section id="workflow" className="py-24 md:py-32 bg-slate-50 border-b border-slate-200 overflow-hidden relative">
        <motion.div 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={STAGGER}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10"
        >
          <motion.div variants={FADE_UP} className="mb-20 max-w-2xl">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900 mb-4">
              Designed around the prescribing workflow.
            </h2>
            <p className="text-lg text-slate-600">
              Physicians don't need to be geneticists. Genomix surfaces actionable pharmacogenomic data only when it's clinically relevant to the patient's treatment and history.
            </p>
          </motion.div>

          <div className="relative">
            {/* Connecting line for desktop */}
            <div className="absolute top-[36px] left-8 right-8 h-px bg-slate-300 hidden lg:block" />
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-8 relative">
              {workflowSteps.map((step, idx) => (
                <motion.div 
                  key={idx} 
                  variants={FADE_UP}
                  className="relative group flex flex-row lg:flex-col items-start gap-4 lg:gap-0"
                >
                  <div className="w-16 h-16 lg:w-20 lg:h-20 shrink-0 rounded-2xl border-2 border-slate-200 bg-white flex items-center justify-center text-slate-900 font-bold text-lg lg:mb-6 shadow-sm group-hover:-translate-y-1.5 group-hover:shadow-md group-hover:border-blue-500 group-hover:text-blue-600 transition-all duration-300 relative z-10">
                    {step.num}
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900 mb-2 leading-snug">
                      {step.title}
                    </h3>
                    <p className="text-xs text-slate-500 leading-relaxed">
                      {step.desc}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>
      </section>

      {/* Platform Preview Section */}
      <section id="platform" className="py-24 md:py-32 bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6 }}
            className="flex flex-col lg:flex-row gap-12 lg:gap-20 items-center"
          >
            <div className="lg:w-1/3 space-y-8">
              <div>
                <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900 mb-4">
                  A unified view of patient DNA and medications.
                </h2>
                <p className="text-lg text-slate-600 leading-relaxed">
                  Toggle between a comprehensive view of the patient's genetic metabolizer status and the specific medication safety reviews generated by the platform.
                </p>
              </div>
              
              <div className="flex flex-col gap-3">
                <button 
                  onClick={() => setActiveTab('genomic')}
                  className={`text-left px-5 py-4 rounded-xl border transition-all duration-300 flex items-center justify-between group ${
                    activeTab === 'genomic' 
                      ? 'border-blue-200 bg-blue-50 text-blue-900 shadow-sm' 
                      : 'border-transparent text-slate-500 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  <div className="flex items-center gap-3 font-semibold text-sm">
                    <Dna size={18} className={activeTab === 'genomic' ? 'text-blue-600' : 'text-slate-400 group-hover:text-slate-600'} />
                    Genomic Profile
                  </div>
                  <ChevronRight size={16} className={`transition-transform duration-300 ${activeTab === 'genomic' ? 'translate-x-1 text-blue-500' : 'opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0'}`} />
                </button>
                <button 
                  onClick={() => setActiveTab('review')}
                  className={`text-left px-5 py-4 rounded-xl border transition-all duration-300 flex items-center justify-between group ${
                    activeTab === 'review' 
                      ? 'border-blue-200 bg-blue-50 text-blue-900 shadow-sm' 
                      : 'border-transparent text-slate-500 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  <div className="flex items-center gap-3 font-semibold text-sm">
                    <ClipboardList size={18} className={activeTab === 'review' ? 'text-blue-600' : 'text-slate-400 group-hover:text-slate-600'} />
                    Medication Review
                  </div>
                  <ChevronRight size={16} className={`transition-transform duration-300 ${activeTab === 'review' ? 'translate-x-1 text-blue-500' : 'opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0'}`} />
                </button>
              </div>
            </div>

            <div className="lg:w-2/3 w-full">
              <AnimatePresence mode="wait">
                {activeTab === 'genomic' && (
                  <motion.div 
                    key="genomic-view"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.4 }}
                    className="bg-white border border-slate-200 rounded-2xl shadow-xl overflow-hidden"
                  >
                    <div className="border-b border-slate-200 px-6 py-4 bg-slate-50 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-slate-800">
                        <Dna size={16} className="text-blue-600" />
                        <span className="font-semibold text-sm">Patient Pharmacogenomic Profile</span>
                      </div>
                      <span className="text-xs text-slate-500 bg-white border border-slate-200 px-2 py-1 rounded">Sarah Jenkins</span>
                    </div>
                    <div className="p-6 md:p-8 grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="border border-slate-200 rounded-xl p-5 bg-white shadow-sm">
                        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Gene</div>
                        <div className="text-lg font-semibold text-slate-900 mb-2">CYP2C19</div>
                        <div className="flex justify-between items-end mt-4">
                          <div>
                            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Variant</div>
                            <div className="text-sm font-mono text-slate-700 bg-slate-100 px-2 py-1 rounded">*2/*2</div>
                          </div>
                          <div className="text-right">
                            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Phenotype</div>
                            <div className="text-sm font-semibold text-blue-700 bg-blue-50 px-2 py-1 rounded">Poor Metabolizer</div>
                          </div>
                        </div>
                      </div>

                      <div className="border border-slate-200 rounded-xl p-5 bg-white shadow-sm">
                        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Gene</div>
                        <div className="text-lg font-semibold text-slate-900 mb-2">SLCO1B1</div>
                        <div className="flex justify-between items-end mt-4">
                          <div>
                            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Variant</div>
                            <div className="text-sm font-mono text-slate-700 bg-slate-100 px-2 py-1 rounded">*5/*5</div>
                          </div>
                          <div className="text-right">
                            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Phenotype</div>
                            <div className="text-sm font-semibold text-amber-700 bg-amber-50 px-2 py-1 rounded">Low Activity</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}

                {activeTab === 'review' && (
                  <motion.div 
                    key="review-view"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.4 }}
                    className="bg-white border border-slate-200 rounded-2xl shadow-xl overflow-hidden"
                  >
                    <div className="border-b border-slate-200 px-6 py-4 bg-slate-50 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-slate-800">
                        <Pill size={16} className="text-blue-600" />
                        <span className="font-semibold text-sm">Medication Safety Review</span>
                      </div>
                    </div>
                    <div className="p-6 md:p-8 space-y-6">
                      <div className="border border-red-200 rounded-xl overflow-hidden bg-white shadow-sm">
                        <div className="bg-red-50 px-4 py-3 border-b border-red-100 flex justify-between items-center">
                           <div className="text-[10px] font-bold text-red-800 uppercase tracking-widest flex items-center gap-1"><AlertTriangle size={12}/> PGx Alert</div>
                           <span className="text-[10px] font-bold text-white bg-red-600 px-2 py-0.5 rounded">High Risk</span>
                        </div>
                        <div className="p-5">
                          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-6">
                            <div>
                              <div className="text-lg font-semibold text-slate-900 mb-1">Clopidogrel 75mg</div>
                              <div className="text-xs text-slate-500">Proposed Therapy</div>
                            </div>
                            <div className="bg-slate-50 rounded-lg p-3 border border-slate-100 w-full sm:w-auto">
                              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Metabolic Pathway</div>
                              <div className="text-sm font-semibold text-slate-800">CYP2C19 (Prodrug)</div>
                            </div>
                          </div>
                          
                          <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 mb-6">
                            <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">
                              Clinical Evidence
                            </div>
                            <div className="text-sm text-slate-700 leading-relaxed font-medium">
                              Patient is a CYP2C19 Poor Metabolizer. Clopidogrel will have severely reduced efficacy. Alternative therapy strongly recommended per CPIC guidelines to prevent adverse cardiovascular events.
                            </div>
                          </div>
                          
                          <div className="flex flex-col sm:flex-row justify-end gap-3 pt-2">
                            <button className="px-5 py-2.5 rounded-lg border border-slate-200 text-sm font-semibold text-slate-600 hover:bg-slate-50 transition-colors">Document Override</button>
                            <button className="px-5 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 transition-colors shadow-sm">Select Alternative</button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>

        </div>
      </section>

      {/* Security Section */}
      <section id="security" className="py-24 md:py-32 bg-slate-900 text-white border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-24 items-center">
            
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.6 }}
            >
              <div className="w-12 h-12 bg-slate-800 border border-slate-700 rounded-xl flex items-center justify-center mb-6 text-slate-300">
                <Shield size={24} />
              </div>
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white mb-6">
                Enterprise security for sensitive genetic data.
              </h2>
              <p className="text-lg text-slate-400 leading-relaxed mb-8">
                Genomic data is the most sensitive form of Protected Health Information (PHI). Our platform is built from the ground up to protect DNA profiles while keeping them accessible to authorized clinicians.
              </p>
              
              <div className="flex flex-col gap-4">
                <div className="flex items-center gap-3 text-sm font-semibold text-slate-300 bg-slate-800/50 border border-slate-700 rounded-lg p-3">
                  <CheckCircle2 size={18} className="text-blue-400" /> End-to-end genetic data encryption
                </div>
                <div className="flex items-center gap-3 text-sm font-semibold text-slate-300 bg-slate-800/50 border border-slate-700 rounded-lg p-3">
                  <CheckCircle2 size={18} className="text-blue-400" /> HIPAA & GDPR compliant architecture
                </div>
                <div className="flex items-center gap-3 text-sm font-semibold text-slate-300 bg-slate-800/50 border border-slate-700 rounded-lg p-3">
                  <CheckCircle2 size={18} className="text-blue-400" /> Granular RBAC for physicians and pharmacists
                </div>
              </div>
            </motion.div>

            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.6 }}
              className="bg-slate-800 border border-slate-700 rounded-2xl p-8 shadow-2xl relative overflow-hidden"
            >
               <div className="absolute top-0 right-0 p-32 bg-blue-500 opacity-5 blur-[100px] rounded-full pointer-events-none" />
               <div className="space-y-6 relative z-10">
                  <div className="border-b border-slate-700 pb-6">
                    <h3 className="text-lg font-semibold text-white mb-2">Secure Tenant Isolation</h3>
                    <p className="text-sm text-slate-400 leading-relaxed">Each hospital organization receives a strictly isolated environment, preventing cross-tenant data exposure of genomic records.</p>
                  </div>
                  <div className="border-b border-slate-700 pb-6">
                    <h3 className="text-lg font-semibold text-white mb-2">Cryptographic Audit History</h3>
                    <p className="text-sm text-slate-400 leading-relaxed">Comprehensive logging of all clinical reviews, alert overrides, and inter-departmental consultations involving genetic data.</p>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-2">SSO Integration</h3>
                    <p className="text-sm text-slate-400 leading-relaxed">Seamless integration with hospital Identity Providers (IdP) for frictionless, secure access by authorized medical staff.</p>
                  </div>
               </div>
            </motion.div>

          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="py-32 bg-white relative overflow-hidden">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10 space-y-10">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <div className="w-16 h-16 bg-blue-50 border border-blue-100 rounded-full flex items-center justify-center text-blue-600 mx-auto mb-8">
              <Dna size={32} />
            </div>
            <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-slate-900 leading-[1.15] mb-6">
              Bring precision medicine into everyday clinical decisions.
            </h2>
            <p className="text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
              Genomix supports healthcare professionals with structured pharmacogenomic insights while keeping physicians at the center of every decision.
            </p>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <button 
              onClick={onRequestAccess}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-base px-8 py-4 rounded-xl transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5"
            >
              Request Professional Access
            </button>
            <button className="bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold text-base px-8 py-4 rounded-xl transition-colors">
              Contact Organization
            </button>
          </motion.div>
        </div>
      </section>

      <footer className="py-12 border-t border-slate-200 bg-slate-50 text-center">
        <div className="flex items-center justify-center gap-2 mb-4">
          <div className="w-6 h-6 bg-blue-600 rounded flex items-center justify-center font-bold text-[10px] text-white">
            <Dna size={12} />
          </div>
          <span className="font-semibold tracking-tight text-slate-700 text-sm">Genomix</span>
        </div>
        <p className="text-xs text-slate-500 font-medium">
          © {new Date().getFullYear()} Genomix Healthcare Solutions. All rights reserved.
        </p>
      </footer>
    </div>
  );
};

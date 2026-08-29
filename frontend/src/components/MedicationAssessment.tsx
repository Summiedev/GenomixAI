import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, CheckCircle2, ShieldAlert, ArrowRight, FileText, Pill, History, Zap, Activity, Info, User, 
  ClipboardList, AlertTriangle, Search, Plus, Trash2, Copy, Settings, Bell, ChevronDown, ChevronUp,
  FileDown, Clock, ArrowLeftRight, Loader2, Check, Send, Award, FileSpreadsheet, Sparkles
} from 'lucide-react';
import { Patient, DrugInfo } from '../types';

// Clinical database of medications supported for smart clinical/genomic analysis
interface ClinicalDrug {
  name: string;
  class: string;
  strengths: string[];
  routes: string[];
  frequencies: string[];
  defaultDuration: string;
  defaultIndication: string;
  mechanism: string;
}

const CLINICAL_DRUGS: ClinicalDrug[] = [
  {
    name: 'Warfarin',
    class: 'Anticoagulant (Vitamin K Antagonist)',
    strengths: ['1mg', '2mg', '3mg', '5mg'],
    routes: ['Oral', 'IV'],
    frequencies: ['Once daily', 'Twice daily'],
    defaultDuration: 'Indefinite',
    defaultIndication: 'Atrial Fibrillation Stroke Prevention',
    mechanism: 'Inhibits Vitamin K Epoxide Reductase (VKORC1), reducing synthesis of active clotting factors II, VII, IX, and X.'
  },
  {
    name: 'Clopidogrel',
    class: 'Antiplatelet (P2Y12 Inhibitor Prodrug)',
    strengths: ['75mg', '300mg'],
    routes: ['Oral'],
    frequencies: ['Once daily', 'Twice daily'],
    defaultDuration: '30 days',
    defaultIndication: 'Post-MI Prophylaxis',
    mechanism: 'Irreversibly inhibits platelet P2Y12 ADP receptors, requiring CYP2C19 hepatic bioactivation.'
  },
  {
    name: 'Atorvastatin',
    class: 'HMG-CoA Reductase Inhibitor (Statin)',
    strengths: ['10mg', '20mg', '40mg', '80mg'],
    routes: ['Oral'],
    frequencies: ['Once daily'],
    defaultDuration: 'Indefinite',
    defaultIndication: 'Hyperlipidemia Control',
    mechanism: 'Inhibits hepatic cholesterol synthesis. Hepatic uptake mediated by SLCO1B1 transporter.'
  },
  {
    name: 'Ticagrelor',
    class: 'Antiplatelet (Direct-Acting P2Y12 Inhibitor)',
    strengths: ['60mg', '90mg'],
    routes: ['Oral'],
    frequencies: ['Twice daily'],
    defaultDuration: '30 days',
    defaultIndication: 'Acute Coronary Syndrome',
    mechanism: 'Directly and reversibly binds P2Y12 ADP receptors, bypassing hepatic bioactivation pathways.'
  },
  {
    name: 'Prasugrel',
    class: 'Antiplatelet (Thienopyridine Prodrug)',
    strengths: ['5mg', '10mg'],
    routes: ['Oral'],
    frequencies: ['Once daily'],
    defaultDuration: '30 days',
    defaultIndication: 'Post-PCI Prophylaxis',
    mechanism: 'Irreversibly inhibits P2Y12 ADP receptors with minimal CYP2C19 dependency.'
  },
  {
    name: 'Apixaban',
    class: 'Anticoagulant (Direct Factor Xa Inhibitor)',
    strengths: ['2.5mg', '5mg'],
    routes: ['Oral'],
    frequencies: ['Twice daily'],
    defaultDuration: 'Indefinite',
    defaultIndication: 'AFib Stroke Prevention',
    mechanism: 'Directly and selectively inhibits free and clot-bound Factor Xa, suppressing thrombin generation.'
  },
  {
    name: 'Lisinopril',
    class: 'ACE Inhibitor',
    strengths: ['5mg', '10mg', '20mg', '40mg'],
    routes: ['Oral'],
    frequencies: ['Once daily'],
    defaultDuration: 'Indefinite',
    defaultIndication: 'Hypertension',
    mechanism: 'Competitive inhibitor of angiotensin-converting enzyme, preventing conversion of angiotensin I to angiotensin II.'
  }
];

export const MedicationAssessment = ({ 
  patient, 
  drug, 
  initialDose,
  initialFrequency,
  onBack, 
  onComplete,
  onModify
}: { 
  patient: Patient, 
  drug: DrugInfo, 
  initialDose: number,
  initialFrequency: string,
  onBack: () => void,
  onComplete: () => void,
  onModify: () => void
}) => {

  // Multi-medication proposed order state
  const [proposedMeds, setProposedMeds] = useState<any[]>([
    {
      id: 'pm-1',
      name: drug.name,
      strength: `${initialDose}mg`,
      dose: '1 tablet',
      route: 'Oral',
      frequency: initialFrequency,
      duration: '30 days',
      indication: patient.conditions.includes('Post-MI') ? 'Post-MI Prophylaxis' : 'Stroke Prevention',
      startDate: '2026-07-18'
    }
  ]);

  // Drug search dropdown states per card index
  const [activeSearchIndex, setActiveSearchIndex] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Interactive UI states
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({ 'pm-1': true });
  const [checklist, setChecklist] = useState<Record<string, boolean>>({
    entered: true,
    interactions: true,
    genomics: true,
    evidence: false,
    reasoning: false
  });
  
  // Clinical status of the assessment
  const [assessmentStatus, setAssessmentStatus] = useState<'Draft' | 'Pending Review' | 'Pharmacist Review' | 'Approved' | 'Finalized'>('Draft');
  
  // Interactive audit trail log
  const [auditLog, setAuditLog] = useState<any[]>([
    { date: '18 Jul 2026', time: '09:42', event: 'Medication Assessment Created', detail: 'By Dr. Sarah Ade' }
  ]);

  // Expandable Accordions for Supporting Evidence & other collapsible sections
  const [expandedEvidence, setExpandedEvidence] = useState<Record<string, boolean>>({});
  const [expandedAlternatives, setExpandedAlternatives] = useState<Record<string, boolean>>({});

  // Pharmacist collaboration modal
  const [showPharmacistModal, setShowPharmacistModal] = useState(false);
  const [pharmPriority, setPharmPriority] = useState<'Routine' | 'Urgent' | 'STAT'>('Routine');
  const [assignedPharmacist, setAssignedPharmacist] = useState('Dr. Clara Uzor, PharmD');
  const [pharmacistMessage, setPharmacistMessage] = useState('');

  // Physician note modal/popup state
  const [showNoteModal, setShowNoteModal] = useState(false);
  const [physicianNoteText, setPhysicianNoteText] = useState('');

  // Handler to toggle medication collapsible card
  const toggleCard = (id: string) => {
    setExpandedCards(prev => ({ ...prev, [id]: !prev[id] }));
  };

  // Add a medication to the proposed list
  const addMedication = () => {
    const nextId = `pm-${Date.now()}`;
    const firstUnadded = CLINICAL_DRUGS.find(d => !proposedMeds.some(pm => pm.name === d.name)) || CLINICAL_DRUGS[0];
    const newMed = {
      id: nextId,
      name: firstUnadded.name,
      strength: firstUnadded.strengths[0],
      dose: '1 tablet',
      route: firstUnadded.routes[0],
      frequency: firstUnadded.frequencies[0],
      duration: firstUnadded.defaultDuration,
      indication: firstUnadded.defaultIndication,
      startDate: '2026-07-18'
    };
    setProposedMeds([...proposedMeds, newMed]);
    setExpandedCards(prev => ({ ...prev, [nextId]: true }));
    setAssessmentStatus('Draft');
    
    // Log audit trail
    const timeStr = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });
    setAuditLog(prev => [
      ...prev, 
      { date: '18 Jul 2026', time: timeStr, event: 'Medication Added', detail: `Added ${newMed.name} to proposed therapy order` }
    ]);
  };

  // Duplicate a medication
  const duplicateMedication = (index: number) => {
    const medToDup = proposedMeds[index];
    const nextId = `pm-${Date.now()}`;
    const duplicated = {
      ...medToDup,
      id: nextId,
    };
    const updated = [...proposedMeds];
    updated.splice(index + 1, 0, duplicated);
    setProposedMeds(updated);
    setExpandedCards(prev => ({ ...prev, [nextId]: true }));
    setAssessmentStatus('Draft');

    const timeStr = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });
    setAuditLog(prev => [
      ...prev, 
      { date: '18 Jul 2026', time: timeStr, event: 'Medication Duplicated', detail: `Copied prescription template for ${medToDup.name}` }
    ]);
  };

  // Remove a medication
  const removeMedication = (id: string, name: string) => {
    if (proposedMeds.length <= 1) return;
    setProposedMeds(proposedMeds.filter(pm => pm.id !== id));
    setAssessmentStatus('Draft');
    
    const timeStr = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });
    setAuditLog(prev => [
      ...prev, 
      { date: '18 Jul 2026', time: timeStr, event: 'Medication Removed', detail: `Removed ${name} from proposed order` }
    ]);
  };

  // Edit fields dynamically
  const updateMedicationField = (id: string, field: string, value: string) => {
    setAssessmentStatus('Draft');
    setProposedMeds(proposedMeds.map(pm => {
      if (pm.id === id) {
        // If changing drug name, pre-fill defaults for that drug
        if (field === 'name') {
          const match = CLINICAL_DRUGS.find(d => d.name === value);
          if (match) {
            return {
              ...pm,
              name: value,
              strength: match.strengths[0],
              route: match.routes[0],
              frequency: match.frequencies[0],
              duration: match.defaultDuration,
              indication: match.defaultIndication
            };
          }
        }
        return { ...pm, [field]: value };
      }
      return pm;
    }));
  };

  // Real-time Pharmacogenomic & Clinical Assessment Core Engine
  const simulation = useMemo(() => {
    const hasClopidogrel = proposedMeds.some(m => m.name === 'Clopidogrel');
    const hasWarfarin = proposedMeds.some(m => m.name === 'Warfarin');
    const hasAtorvastatin = proposedMeds.some(m => m.name === 'Atorvastatin') || patient.medications.some(m => m.name === 'Atorvastatin');
    const hasLisinopril = proposedMeds.some(m => m.name === 'Lisinopril');
    
    const isPoorCyp2c19 = patient.genomicProfile?.variants.some(v => v.gene === 'CYP2C19' && v.phenotype === 'Poor Metabolizer');
    const isLowSlco1b1 = patient.genomicProfile?.variants.some(v => v.gene === 'SLCO1B1' && v.phenotype === 'Low Transporter Activity');

    let overallRec = 'Requires Caution';
    let clinicalPriority: 'High' | 'Moderate' | 'Low' = 'Moderate';
    let evidenceStrength: 'High' | 'Moderate' | 'Low' = 'High';
    let alertCount = 0;
    let recCount = 0;
    const interactions: any[] = [];

    // Check allergies
    const hasPenicillinAllergy = patient.allergies.some(a => a.toLowerCase().includes('penicillin'));

    // Analyze Drug-Drug Interactions
    if (hasWarfarin && hasClopidogrel) {
      interactions.push({
        severity: 'Major',
        meds: 'Warfarin + Clopidogrel',
        mechanism: 'Synergistic bleeding risk. Warfarin impairs fibrin formation; Clopidogrel inhibits platelet ADP aggregation. Dual therapy dramatically compromises primary and secondary hemostasis.',
        recommendation: 'Avoid combination if possible. If dual therapy is strictly required (e.g., recent PCI with active AFib), target low therapeutic INR (2.0 - 2.5), enforce a strict duration limit, and schedule weekly coagulation assays.'
      });
      alertCount += 1;
    }
    if (hasWarfarin && patient.medications.some(m => m.name === 'Aspirin')) {
      interactions.push({
        severity: 'Major',
        meds: 'Warfarin + Aspirin',
        mechanism: 'Additive bleeding risk. Aspirin irreversibly acetylates COX-1 platelets, while Warfarin limits clotting factor synthesis.',
        recommendation: 'Aspirin should be suspended or strictly capped at 81mg daily. (Patient has recorded bleeding events post-discontinuation in January 2026).'
      });
      alertCount += 1;
    }
    if (hasClopidogrel && hasAtorvastatin) {
      interactions.push({
        severity: 'Moderate',
        meds: 'Clopidogrel + Atorvastatin',
        mechanism: 'Atorvastatin is a CYP3A4 substrate and competitive inhibitor. Theoretically reduces Clopidogrel prodrug bioactivation via CYP3A4 pathways.',
        recommendation: 'Monitor antiplatelet efficacy or consider switching to a non-CYP3A4 statin like Rosuvastatin or Pravastatin.'
      });
      alertCount += 1;
    }

    // Determine Overall Status
    if ((hasClopidogrel && isPoorCyp2c19) || (hasWarfarin && hasClopidogrel)) {
      overallRec = 'Requires Caution / High Risk';
      clinicalPriority = 'High';
      evidenceStrength = 'High';
      recCount = 3;
    } else if (hasWarfarin || (hasAtorvastatin && isLowSlco1b1)) {
      overallRec = 'Requires Caution';
      clinicalPriority = 'Moderate';
      evidenceStrength = 'High';
      recCount = 2;
    } else {
      overallRec = 'Acceptable';
      clinicalPriority = 'Low';
      evidenceStrength = 'Moderate';
      recCount = 1;
    }

    // Build medication breakdowns for each proposed med
    const breakdowns = proposedMeds.map(m => {
      const isClopidogrel = m.name === 'Clopidogrel';
      const isWarfarin = m.name === 'Warfarin';
      const isStatin = m.name === 'Atorvastatin';
      const isTicagrelor = m.name === 'Ticagrelor';
      const isPrasugrel = m.name === 'Prasugrel';
      const isApixaban = m.name === 'Apixaban';
      const isLisinopril = m.name === 'Lisinopril';

      let verdict: 'High Risk' | 'Caution' | 'Acceptable' = 'Acceptable';
      let pgxGene = 'N/A';
      let pgxPheno = 'N/A';
      let pgxSig = 'No high-risk genomic variants identified influencing this therapy.';
      let pgxConsiderations = 'Standard prescribing guidelines apply. Standard dosing is biochemically sound.';
      
      let compAge = 'Appropriate for age 64.';
      let compRenal = 'Normal renal excretion (eGFR 85 mL/min/1.73m²).';
      let compHepatic = 'Adequate hepatic reserve (ALT 24 U/L).';
      let compAllergies = 'No allergic conflicts identified.';
      
      let bleedRisk: 'Low' | 'Moderate' | 'High' = 'Low';
      let toxRisk: 'Low' | 'Moderate' | 'High' = 'Low';
      let failRisk: 'Low' | 'Moderate' | 'High' = 'Low';
      let monitorReq = 'Routine clinical checkups and primary symptom assessment.';

      let outcomeEff = 'High expected therapeutic response.';
      let outcomeTime = '1-2 hours';
      let outcomeComplication = 'No abnormal risks anticipated outside of standard side-effects.';
      let outcomeFollowUp = 'Standard review in 4 weeks.';

      let mechanism = '';
      let interpretation = 'No special genomic action required.';
      let alternativeSuggestions: any[] = [];
      let references: string[] = [];

      // Drug class mapping
      const matchedConfig = CLINICAL_DRUGS.find(d => d.name === m.name);
      const drugClass = matchedConfig ? matchedConfig.class : 'Cardiovascular Agent';
      mechanism = matchedConfig ? matchedConfig.mechanism : 'Standard receptor-mediated pharmacology.';

      if (isClopidogrel) {
        if (isPoorCyp2c19) {
          verdict = 'High Risk';
          pgxGene = 'CYP2C19';
          pgxPheno = 'Poor Metabolizer (*2/*2)';
          pgxSig = 'Severely reduced bioactivation of prodrug to active metabolite.';
          pgxConsiderations = 'The patient carries two copy of non-functional CYP2C19 *2 allele. This homozygous variant abolishes CYP2C19 enzymatic function, meaning the active clopidogrel metabolite cannot be formed, leaving the patient unprotected against ischemic events.';
          
          bleedRisk = 'Low';
          toxRisk = 'Low';
          failRisk = 'High';
          monitorReq = 'Perform platelet reactivity assays if clopidogrel is continued. However, switching therapy is strongly recommended.';
          
          outcomeEff = 'Minimal expected efficacy due to lack of metabolic activation.';
          outcomeTime = 'Immediate therapeutic gap';
          outcomeComplication = 'Unresolved risk of stent thrombosis and secondary cardiovascular events.';
          outcomeFollowUp = 'Substitute with a direct-acting agent immediately.';

          interpretation = "Impending therapeutic failure. Due to the CYP2C19 *2/*2 Poor Metabolizer phenotype, the clopidogrel prodrug cannot be bioactivated, causing zero platelet inhibition.";
          
          alternativeSuggestions = [
            {
              drugName: 'Ticagrelor',
              class: 'Direct-Acting P2Y12 Inhibitor',
              recommendedDose: '90mg',
              frequency: 'Twice daily',
              advantages: 'Bypasses hepatic conversion. Rapid onset, fully independent of CYP2C19 genetics.',
              disadvantages: 'Increased incidence of dyspnea, strict twice-daily compliance required.',
              reasonRecommended: 'Recommended by CPIC as preferred alternative to bypass the genetic block.',
              evidenceLevel: 'CPIC Level A (Strong Recommendation)',
              comparison: {
                prevention: '96% (Superior)',
                bleeding: '11% (Moderate)',
                monitoring: 'No routine assay required',
                interactions: 'Avoid strong CYP3A4 inhibitors',
                genomics: 'Completely independent'
              }
            },
            {
              drugName: 'Prasugrel',
              class: 'Thienopyridine Prodrug',
              recommendedDose: '10mg',
              frequency: 'Once daily',
              advantages: 'Once-daily dosing. Metabolic activation is not heavily dependent on CYP2C19.',
              disadvantages: 'Strictly contraindicated if history of stroke/TIA. Higher bleeding rate.',
              reasonRecommended: 'Highly potent antiplatelet agent with very low genomic variance sensitivity.',
              evidenceLevel: 'CPIC Level A',
              comparison: {
                prevention: '93% (High)',
                bleeding: '14% (Higher)',
                monitoring: 'No routine assay required',
                interactions: 'Low interaction potential',
                genomics: 'Negligible sensitivity'
              }
            }
          ];

          references = [
            'CPIC Guidelines for CYP2C19 and Antiplatelet Therapy (2023 Update)',
            'FDA Plavix Boxed Warning regarding Poor Metabolizers',
            'PLATO and TRITON-TIMI 38 genomic sub-analyses'
          ];
        } else {
          verdict = 'Acceptable';
          references = ['ACC/AHA Dual Antiplatelet Therapy Guidelines'];
        }
      } else if (isWarfarin) {
        verdict = 'Caution';
        pgxGene = 'VKORC1 / CYP2C9';
        pgxPheno = 'Increased Sensitivity Profile';
        pgxSig = 'VKORC1 AA genotype and CYP2C9 *3 carrier state inferred by clinical models.';
        pgxConsiderations = 'The patient has clinical characteristics predicting a highly sensitive response. Increased risk of excessive anticoagulation with standard starter doses.';
        
        compAge = 'Caution: Patient is 64 years. Age-related vascular fragility increases major bleed hazard.';
        bleedRisk = 'High';
        toxRisk = 'Moderate';
        failRisk = 'Low';
        monitorReq = 'Acquire baseline INR. Re-test INR 2-3 times during first week. Adjust dose dynamically.';
        
        outcomeEff = 'Highly variable; requires careful titration.';
        outcomeTime = '3-5 days to steady state';
        outcomeComplication = 'Extreme risk of mucosal bleeding or gastrointestinal hemorrhage.';
        outcomeFollowUp = 'Weekly INR check. Goal therapeutic range 2.0 - 3.0.';

        interpretation = "Narrow therapeutic window. Bleeding risk is significantly heightened due to patient age and concurrent antiplatelet use. Coagulation monitoring is vital.";

        alternativeSuggestions = [
          {
            drugName: 'Apixaban',
            class: 'Direct Factor Xa Inhibitor (DOAC)',
            recommendedDose: '5mg',
            frequency: 'Twice daily',
            advantages: 'Predictable kinetics, no routine coagulation checks, superior safety margins.',
            disadvantages: 'Higher out-of-pocket cost. Requires strict twice-daily adherence.',
            reasonRecommended: 'Apixaban demonstrated superior stroke protection and lower bleeding risk compared to Warfarin in ARISTOTLE trial.',
            evidenceLevel: 'AHA/ACC Class I Recommendation',
            comparison: {
              prevention: '98% (Excellent)',
              bleeding: '3% (Very Low)',
              monitoring: 'No routine monitoring',
              interactions: 'Strong CYP3A4 + P-gp inhibitors',
              genomics: 'Not affected'
            }
          }
        ];

        references = [
          'CHEST Guidelines on Antithrombotic Therapy (2021)',
          'FDA Coumadin (Warfarin) Labeling & Genetic Dosing Algorithms'
        ];
      } else if (isStatin) {
        if (isLowSlco1b1) {
          verdict = 'Caution';
          pgxGene = 'SLCO1B1';
          pgxPheno = 'Low Transporter Activity (*5/*5)';
          pgxSig = 'Markedly decreased hepatic uptake of statin, leading to high systemic concentrations.';
          pgxConsiderations = 'The SLCO1B1 gene encodes the organic anion transporter OATP1B1, which pumps statins into the liver. With low activity (*5/*5), Atorvastatin builds up systemically in muscle tissue, creating a high risk of statin-induced myalgia or rhabdomyolysis.';
          
          toxRisk = 'High';
          failRisk = 'Low';
          monitorReq = 'Check baseline Creatine Kinase (CK) and liver function enzymes. Educate on muscle pain.';
          
          outcomeEff = 'Effective lipid lowering, but high risk of intolerance.';
          outcomeTime = '2-4 weeks';
          outcomeComplication = 'Myalgias, skeletal muscle breakdown, and potential acute kidney injury.';
          outcomeFollowUp = 'Evaluate muscle pain in 2 weeks. Limit daily dose of Atorvastatin to 20mg max.';

          interpretation = "Low SLCO1B1 transport. homozygous *5/*5 variant restricts liver uptake, raising systemic exposure and muscle toxicity without cardiovascular benefit.";

          alternativeSuggestions = [
            {
              drugName: 'Rosuvastatin',
              class: 'HMG-CoA Reductase Inhibitor',
              recommendedDose: '10mg',
              frequency: 'Once daily',
              advantages: 'Hydrophilic statin, lower muscle penetration, reduced dependency on SLCO1B1 transporter.',
              disadvantages: 'Slightly higher cost; watch for renal proteinuria at high doses.',
              reasonRecommended: 'Excellent lipid-lowering with lower risk of statin-associated muscle symptoms.',
              evidenceLevel: 'CPIC Guideline for Statin-Induced Myopathy (2022)',
              comparison: {
                prevention: '97% (High)',
                bleeding: 'N/A',
                monitoring: 'Routine lipid panels',
                interactions: 'Low CYP3A4 potential',
                genomics: 'Lower myopathy risk'
              }
            }
          ];

          references = [
            'CPIC Guideline for SLCO1B1 and Statin-Associated Muscle Symptoms (2022)',
            'ACC/AHA Cholesterol Clinical Practice Guidelines'
          ];
        } else {
          verdict = 'Acceptable';
          references = ['AHA Guidelines on Statin Therapy'];
        }
      } else if (isLisinopril) {
        verdict = 'Acceptable';
        references = ['AHA/ACC Hypertension Guidelines'];
      }

      return {
        ...m,
        class: drugClass,
        verdict,
        pgx: {
          gene: pgxGene,
          phenotype: pgxPheno,
          significance: pgxSig,
          considerations: pgxConsiderations
        },
        compatibility: {
          age: compAge,
          renal: compRenal,
          hepatic: compHepatic,
          allergies: compAllergies,
          diagnoses: `Indication verified: ${m.indication}. Appropriate for patient cardiac profile.`
        },
        safety: {
          bleeding: bleedRisk,
          toxicity: toxRisk,
          failure: failRisk,
          contraindications: 'No absolute contraindications identified in current active diagnostics.',
          monitoring: monitorReq
        },
        outcome: {
          effectiveness: outcomeEff,
          time: outcomeTime,
          complications: outcomeComplication,
          followUp: outcomeFollowUp
        },
        reasoning: {
          mechanism,
          factors: [
            patient.age > 60 ? 'Advanced patient age (64 years)' : '',
            isPoorCyp2c19 && isClopidogrel ? 'Loss-of-function CYP2C19 *2 allele state' : '',
            isLowSlco1b1 && isStatin ? 'Reduced hepatic clearance via SLCO1B1 *5 variant' : '',
            hasWarfarin && isClopidogrel ? 'Concurrent double antithrombotic therapy' : ''
          ].filter(Boolean),
          interpretation
        },
        alternatives: alternativeSuggestions,
        references
      };
    });

    return {
      overallRec,
      clinicalPriority,
      evidenceStrength,
      medsAssessedCount: proposedMeds.length,
      interactionsCount: interactions.length,
      monitoringCount: recCount,
      interactions,
      breakdowns
    };
  }, [proposedMeds, patient]);

  // Handle finalize action
  const handleFinalizeAction = () => {
    setAssessmentStatus('Finalized');
    const timeStr = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });
    setAuditLog(prev => [
      ...prev, 
      { date: '18 Jul 2026', time: timeStr, event: 'Prescription Finalized', detail: 'Authorized and sent to pharmacy system by Dr. Sarah Ade' }
    ]);
    
    // Trigger parent callback on completion
    setTimeout(() => {
      onComplete();
    }, 1500);
  };

  // Handle pharmacist review request
  const submitPharmacistReview = (e: React.FormEvent) => {
    e.preventDefault();
    setAssessmentStatus('Pharmacist Review');
    const timeStr = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });
    setAuditLog(prev => [
      ...prev, 
      { 
        date: '18 Jul 2026',
        time: timeStr, 
        event: 'Requested Pharmacist Review', 
        detail: `Sent as [${pharmPriority}] priority to ${assignedPharmacist}. Note: "${pharmacistMessage || 'Anticoagulation / antiplatelet genomic query.'}"` 
      }
    ]);
    setShowPharmacistModal(false);

    // Simulate pharmacist approval after 3 seconds
    setTimeout(() => {
      setAssessmentStatus('Approved');
      const approveTimeStr = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });
      setAuditLog(prev => [
        ...prev,
        {
          date: '18 Jul 2026',
          time: approveTimeStr,
          event: 'Pharmacist Recommendation Received',
          detail: `Approved by ${assignedPharmacist}. "Anticoagulation strategy verified against CPIC guidelines. Suggesting alternative P2Y12 inhibitor for clopidogrel if Poor Metabolizer confirmed."`
        },
        {
          date: '18 Jul 2026',
          time: approveTimeStr,
          event: 'Final Review Completed',
          detail: 'Ready for doctor finalization.'
        }
      ]);
      setChecklist(prev => ({
        ...prev,
        interactions: true,
        genomics: true,
        evidence: true,
        reasoning: true
      }));
    }, 3000);
  };


  // Add clinical note
  const handleAddClinicalNoteSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!physicianNoteText.trim()) return;
    const timeStr = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });
    setAuditLog(prev => [
      ...prev,
      {
        date: '18 Jul 2026',
        time: timeStr,
        event: 'Physician Note Added',
        detail: physicianNoteText
      }
    ]);
    setPhysicianNoteText('');
    setShowNoteModal(false);
  };

  // CSS Color Helper Functions based on clinical status and results
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'High':
      case 'Major':
      case 'High Risk':
        return 'text-red-700 bg-red-50 border-red-200';
      case 'Moderate':
      case 'Caution':
      case 'Requires Caution':
        return 'text-amber-700 bg-amber-50 border-amber-200';
      case 'Low':
      case 'Minor':
      case 'Acceptable':
        return 'text-emerald-700 bg-emerald-50 border-emerald-200';
      default:
        return 'text-slate-600 bg-slate-50 border-slate-200';
    }
  };

  return (
    <div className="min-h-screen bg-hospital-bg text-hospital-text font-sans flex flex-col antialiased">
      
      {/* Premium Hospital Top Navigation Bar (Matching App style, Light, Sterile) */}
      <header className="bg-white border-b border-hospital-border px-4 lg:px-6 py-3.5 flex flex-wrap items-center justify-between shrink-0 shadow-xs gap-4">
        <div className="flex items-center gap-3">
          <div className="bg-hospital-blue p-2 rounded-lg text-white">
            <ShieldAlert size={18} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] font-bold text-hospital-blue uppercase tracking-wider">Clinical Decision Support</span>
              <span className="bg-slate-100 px-1.5 py-0.5 rounded text-[9px] text-hospital-muted border border-hospital-border font-mono">GENOMIX-CDS</span>
            </div>
            <h1 className="text-base font-bold text-slate-900 tracking-tight">Medication Assessment Workspace</h1>
          </div>
        </div>

        {/* Hospital Environment Info */}
        <div className="hidden lg:flex items-center gap-5 px-3.5 py-1.5 bg-hospital-bg rounded-lg border border-hospital-border">
          <div className="text-[11px] font-medium text-slate-600">
            Institution: <span className="text-slate-900 font-bold">Lagos Heart Institute</span>
          </div>
          <div className="h-3 w-[1px] bg-slate-300"></div>
          <div className="text-[11px] font-medium text-slate-600">
            Ordering MD: <span className="text-slate-900 font-bold">Dr. Sarah Ade</span>
          </div>
          <div className="h-3 w-[1px] bg-slate-300"></div>
          <div className="text-[11px] font-medium text-slate-600">
            Department: <span className="text-hospital-blue font-bold font-mono uppercase">Cardiology</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Status Indicator */}
          <div className="flex items-center gap-1.5 mr-2">
            <span className="text-[11px] text-hospital-muted">CDS Feed:</span>
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-[11px] font-bold text-emerald-700">Real-Time Connected</span>
          </div>

          <button 
            onClick={onBack}
            className="flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 hover:text-slate-950 px-3.5 py-1.5 rounded-lg text-xs font-semibold border border-hospital-border transition-colors cursor-pointer"
            id="close-assessment-workspace-btn"
          >
            <X size={14} />
            <span>Exit Workspace</span>
          </button>
        </div>
      </header>

      {/* Main Responsive Grid Layout (Responsive Three-Panel) */}
      <div className="flex-1 w-full max-w-7xl mx-auto p-4 lg:p-6 grid grid-cols-1 lg:grid-cols-4 gap-6 overflow-y-auto">
        
        {/* ==================== LEFT PANEL (25%): Proposed Medication Order ==================== */}
        <aside className="lg:col-span-1 space-y-6 flex flex-col" id="left-panel-medications">
          
          {/* Active vs Proposed list Section Card */}
          <div className="bg-white border border-hospital-border rounded-xl shadow-xs p-4 flex-1 flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-hospital-border mb-4">
              <div className="flex items-center gap-1.5">
                <ClipboardList size={16} className="text-hospital-blue" />
                <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Proposed Medication Order</h2>
              </div>
              <button 
                onClick={addMedication}
                className="flex items-center gap-1 bg-hospital-blue hover:bg-blue-800 text-white px-2 py-1 rounded text-xs font-bold transition-colors cursor-pointer shadow-xs"
                id="add-medication-btn"
              >
                <Plus size={12} />
                <span>Add Drug</span>
              </button>
            </div>

            {/* Proposed Medications Form Fields */}
            <div className="space-y-4 flex-1 overflow-y-auto max-h-[500px] lg:max-h-none pr-1">
              {proposedMeds.map((pm, index) => {
                const isSearching = activeSearchIndex === index;
                return (
                  <div key={pm.id} className="p-3 bg-slate-50 border border-hospital-border rounded-lg hover:border-slate-300 transition-all relative">
                    <div className="flex justify-between items-center mb-2.5">
                      <span className="bg-blue-50 text-hospital-blue text-[9px] font-mono px-2 py-0.5 rounded font-bold border border-blue-100 uppercase">
                        New Order #{index + 1}
                      </span>
                      <div className="flex items-center gap-1.5">
                        <button 
                          title="Duplicate Medication"
                          onClick={() => duplicateMedication(index)}
                          className="p-1 text-slate-500 hover:text-slate-800 hover:bg-slate-200 rounded transition-colors"
                          id={`duplicate-med-btn-${index}`}
                        >
                          <Copy size={11} />
                        </button>
                        {proposedMeds.length > 1 && (
                          <button 
                            title="Remove Medication"
                            onClick={() => removeMedication(pm.id, pm.name)}
                            className="p-1 text-hospital-red hover:text-red-700 hover:bg-red-50 rounded transition-colors"
                            id={`remove-med-btn-${index}`}
                          >
                            <Trash2 size={11} />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Compact inputs */}
                    <div className="space-y-2 text-[12px]">
                      {/* Searchable Drug Selector */}
                      <div className="relative">
                        <label className="text-[9px] font-bold text-hospital-muted uppercase block mb-0.5">Drug Name</label>
                        <div className="relative">
                          <input 
                            type="text" 
                            className="w-full bg-white border border-hospital-border rounded px-2 py-1 text-slate-900 focus:outline-none focus:border-hospital-blue font-semibold text-[12px]"
                            value={pm.name}
                            onChange={(e) => {
                              updateMedicationField(pm.id, 'name', e.target.value);
                              setActiveSearchIndex(index);
                              setSearchQuery(e.target.value);
                            }}
                            onFocus={() => {
                              setActiveSearchIndex(index);
                              setSearchQuery(pm.name);
                            }}
                            id={`drug-name-input-${index}`}
                          />
                          <Search size={11} className="absolute right-2 top-1.5 text-hospital-muted" />
                        </div>
                        
                        {/* Searchable dropdown options */}
                        {isSearching && (
                          <div className="absolute left-0 right-0 mt-1 bg-white border border-hospital-border rounded-md shadow-lg z-50 max-h-40 overflow-y-auto">
                            {CLINICAL_DRUGS.filter(cd => cd.name.toLowerCase().includes(searchQuery.toLowerCase())).map(cd => (
                              <button
                                key={cd.name}
                                className="w-full text-left px-2.5 py-1.5 hover:bg-slate-50 text-slate-800 border-b border-slate-100 last:border-0 text-[11px] font-medium"
                                onClick={() => {
                                  updateMedicationField(pm.id, 'name', cd.name);
                                  setActiveSearchIndex(null);
                                }}
                                type="button"
                              >
                                <div className="font-bold">{cd.name}</div>
                                <div className="text-[9px] text-hospital-muted">{cd.class}</div>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Strength & Dose */}
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="text-[9px] font-bold text-hospital-muted uppercase block mb-0.5">Strength</label>
                          <input 
                            type="text" 
                            className="w-full bg-white border border-hospital-border rounded px-2 py-1 text-slate-800 focus:outline-none focus:border-hospital-blue text-[11px]"
                            value={pm.strength}
                            onChange={(e) => updateMedicationField(pm.id, 'strength', e.target.value)}
                          />
                        </div>
                        <div>
                          <label className="text-[9px] font-bold text-hospital-muted uppercase block mb-0.5">Dose</label>
                          <input 
                            type="text" 
                            className="w-full bg-white border border-hospital-border rounded px-2 py-1 text-slate-800 focus:outline-none focus:border-hospital-blue text-[11px]"
                            value={pm.dose}
                            onChange={(e) => updateMedicationField(pm.id, 'dose', e.target.value)}
                          />
                        </div>
                      </div>

                      {/* Route & Frequency */}
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="text-[9px] font-bold text-hospital-muted uppercase block mb-0.5">Route</label>
                          <select 
                            className="w-full bg-white border border-hospital-border rounded px-2 py-1 text-slate-800 focus:outline-none focus:border-hospital-blue text-[11px]"
                            value={pm.route}
                            onChange={(e) => updateMedicationField(pm.id, 'route', e.target.value)}
                          >
                            <option value="Oral">Oral</option>
                            <option value="IV">IV (Intravenous)</option>
                            <option value="IM">IM (Intramuscular)</option>
                            <option value="Subcutaneous">Subcutaneous</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-[9px] font-bold text-hospital-muted uppercase block mb-0.5">Frequency</label>
                          <input 
                            type="text" 
                            className="w-full bg-white border border-hospital-border rounded px-2 py-1 text-slate-800 focus:outline-none focus:border-hospital-blue text-[11px]"
                            value={pm.frequency}
                            onChange={(e) => updateMedicationField(pm.id, 'frequency', e.target.value)}
                          />
                        </div>
                      </div>

                      {/* Duration & Start Date */}
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="text-[9px] font-bold text-hospital-muted uppercase block mb-0.5">Duration</label>
                          <input 
                            type="text" 
                            className="w-full bg-white border border-hospital-border rounded px-2 py-1 text-slate-800 focus:outline-none focus:border-hospital-blue text-[11px]"
                            value={pm.duration}
                            onChange={(e) => updateMedicationField(pm.id, 'duration', e.target.value)}
                          />
                        </div>
                        <div>
                          <label className="text-[9px] font-bold text-hospital-muted uppercase block mb-0.5">Start Date</label>
                          <input 
                            type="date" 
                            className="w-full bg-white border border-hospital-border rounded px-2 py-1 text-slate-800 focus:outline-none focus:border-hospital-blue text-[11px] font-mono"
                            value={pm.startDate}
                            onChange={(e) => updateMedicationField(pm.id, 'startDate', e.target.value)}
                          />
                        </div>
                      </div>

                      {/* Indication */}
                      <div>
                        <label className="text-[9px] font-bold text-hospital-muted uppercase block mb-0.5">Indication</label>
                        <input 
                          type="text" 
                          className="w-full bg-white border border-hospital-border rounded px-2 py-1 text-slate-800 focus:outline-none focus:border-hospital-blue text-[11px]"
                          value={pm.indication}
                          onChange={(e) => updateMedicationField(pm.id, 'indication', e.target.value)}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Separated Active Medications (EHR Standard) */}
          <div className="bg-white border border-hospital-border rounded-xl shadow-xs p-4">
            <div className="flex items-center gap-1.5 pb-2.5 border-b border-hospital-border mb-3">
              <Pill size={14} className="text-hospital-green" />
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Active Patient Therapy</h3>
            </div>
            <div className="space-y-2">
              {patient.medications.map(am => (
                <div key={am.id} className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
                  <div>
                    <div className="text-xs font-bold text-slate-800">{am.name}</div>
                    <div className="text-[10px] text-hospital-muted">{am.dose} • {am.frequency} • {am.route}</div>
                  </div>
                  <span className="px-2 py-0.5 bg-emerald-50 text-hospital-green text-[9px] font-bold rounded uppercase border border-emerald-100">
                    Active
                  </span>
                </div>
              ))}
            </div>
          </div>
        </aside>

        {/* ==================== CENTER PANEL (50%): Primary Assessment Workspace ==================== */}
        <main className="lg:col-span-2 space-y-6 flex flex-col" id="center-panel-workspace">
          
          {/* Patient Context Clinical Header */}
          <section className="bg-white border border-hospital-border rounded-xl p-4 shadow-xs" id="patient-context-header">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center text-hospital-blue border border-hospital-border">
                  <User size={20} />
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-sm font-bold text-slate-900">{patient.name}</h2>
                    <span className="px-2 py-0.5 bg-slate-100 text-slate-700 font-mono text-[10px] rounded border border-hospital-border font-bold">
                      MRN: {patient.mrn}
                    </span>
                  </div>
                  <div className="text-[11px] text-hospital-muted mt-0.5">
                    Age: <span className="font-semibold text-slate-800">{patient.age}</span> | Sex: <span className="font-semibold text-slate-800">{patient.sex}</span> | Cardiac diagnoses:{' '}
                    <span className="text-slate-800 font-semibold">{patient.conditions.join(', ')}</span>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-[10px] text-hospital-muted">Department</div>
                <div className="text-xs font-bold text-hospital-blue font-mono">CARDIOLOGY</div>
              </div>
            </div>
          </section>

          {/* Medication Assessment Summary Card */}
          <section className="bg-white border-l-4 border-l-hospital-blue border border-hospital-border rounded-r-xl p-5 shadow-xs" id="assessment-summary-card">
            <div className="flex items-center gap-2 mb-3">
              <ShieldAlert size={16} className="text-hospital-blue" />
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Medication Assessment Summary</h3>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="p-3 bg-slate-50 rounded-lg border border-hospital-border">
                <div className="text-[9px] text-hospital-muted font-bold uppercase tracking-wider">Overall Recommendation</div>
                <div className={`text-xs font-bold mt-1 ${simulation.overallRec.includes('High') ? 'text-hospital-red' : 'text-amber-600'}`}>
                  {simulation.overallRec}
                </div>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg border border-hospital-border">
                <div className="text-[9px] text-hospital-muted font-bold uppercase tracking-wider">Clinical Priority</div>
                <div className="flex items-center gap-1.5 mt-1">
                  <span className={`w-2 h-2 rounded-full ${simulation.clinicalPriority === 'High' ? 'bg-hospital-red' : 'bg-hospital-yellow'}`}></span>
                  <span className="text-xs font-bold text-slate-800">{simulation.clinicalPriority}</span>
                </div>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg border border-hospital-border">
                <div className="text-[9px] text-hospital-muted font-bold uppercase tracking-wider">Evidence Strength</div>
                <div className="text-xs font-bold text-hospital-blue mt-1">{simulation.evidenceStrength}</div>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg border border-hospital-border">
                <div className="text-[9px] text-hospital-muted font-bold uppercase tracking-wider">Assessed Scope</div>
                <div className="text-xs font-bold text-slate-800 mt-1">
                  {simulation.medsAssessedCount} {simulation.medsAssessedCount === 1 ? 'drug' : 'drugs'} evaluated
                </div>
              </div>
            </div>
          </section>

          {/* Assessment Breakdowns Collapsible Section */}
          <section className="space-y-4" id="assessment-breakdown-section">
            <div className="flex items-center justify-between pb-1 border-b border-hospital-border">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Therapeutic Breakdown</h3>
              <span className="text-xs font-semibold text-hospital-muted font-mono">{proposedMeds.length} Meds under evaluation</span>
            </div>

            <div className="space-y-4">
              {simulation.breakdowns.map((br) => {
                const isOpen = expandedCards[br.id] ?? false;
                const statusTheme = getSeverityColor(br.verdict);
                return (
                  <div key={br.id} className="bg-white border border-hospital-border rounded-xl shadow-xs overflow-hidden">
                    
                    {/* Expandable Header */}
                    <div 
                      onClick={() => toggleCard(br.id)}
                      className="p-4 bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer flex items-center justify-between gap-4"
                      id={`breakdown-header-${br.id}`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg border ${
                          br.verdict === 'High Risk' ? 'bg-red-50 text-hospital-red border-red-100' : 
                          br.verdict === 'Caution' ? 'bg-amber-50 text-amber-600 border-amber-100' : 
                          'bg-emerald-50 text-hospital-green border-emerald-100'
                        }`}>
                          <Pill size={16} />
                        </div>
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <h4 className="text-sm font-bold text-slate-900">{br.name}</h4>
                            <span className="text-[11px] font-semibold text-hospital-muted font-mono">({br.strength} • {br.frequency})</span>
                          </div>
                          <p className="text-[11px] text-hospital-muted mt-0.5">{br.class}</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <span className={`px-2.5 py-0.5 text-[9px] font-bold rounded uppercase border ${statusTheme}`}>
                          {br.verdict}
                        </span>
                        {isOpen ? <ChevronUp size={14} className="text-slate-400" /> : <ChevronDown size={14} className="text-slate-400" />}
                      </div>
                    </div>

                    {/* Collapsible Content */}
                    <AnimatePresence initial={false}>
                      {isOpen && (
                        <motion.div 
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="border-t border-hospital-border"
                        >
                          <div className="p-4 space-y-6">
                            
                            {/* 1. Medication Overview */}
                            <div className="bg-slate-50/50 p-3.5 border border-hospital-border rounded-lg">
                              <div className="text-[10px] font-bold text-slate-800 uppercase tracking-wider mb-2.5 flex items-center gap-1">
                                <Info size={11} className="text-hospital-blue" />
                                <span>Medication Overview</span>
                              </div>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                                <div>
                                  <span className="text-[9px] text-hospital-muted block font-bold uppercase">Drug Class</span>
                                  <span className="font-semibold text-slate-800">{br.class}</span>
                                </div>
                                <div>
                                  <span className="text-[9px] text-hospital-muted block font-bold uppercase">Intended Indication</span>
                                  <span className="font-semibold text-slate-800">{br.indication}</span>
                                </div>
                                <div>
                                  <span className="text-[9px] text-hospital-muted block font-bold uppercase">Dose / Route</span>
                                  <span className="font-semibold text-slate-800">{br.strength} • {br.route}</span>
                                </div>
                                <div>
                                  <span className="text-[9px] text-hospital-muted block font-bold uppercase">Frequency</span>
                                  <span className="font-semibold text-slate-800">{br.frequency}</span>
                                </div>
                              </div>
                            </div>

                            {/* 2. Pharmacogenomic Assessment */}
                            <div>
                              <div className="text-[10px] font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center gap-1">
                                <Zap size={11} className="text-hospital-blue" />
                                <span>Pharmacogenomic Assessment</span>
                              </div>
                              <div className="p-3.5 border border-hospital-border bg-slate-50/50 rounded-lg">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3 pb-3 border-b border-hospital-border/60">
                                  <div>
                                    <span className="text-[9px] text-hospital-muted block font-bold uppercase">Relevant Biomarkers</span>
                                    <div className="flex items-center gap-2 mt-1">
                                      <span className="font-mono text-xs font-bold text-hospital-blue px-2 py-0.5 bg-blue-50 border border-blue-100 rounded">
                                        {br.pgx.gene}
                                      </span>
                                      <span className="text-xs font-bold text-slate-800">
                                        {br.pgx.phenotype}
                                      </span>
                                    </div>
                                  </div>
                                  <div>
                                    <span className="text-[9px] text-hospital-muted block font-bold uppercase">Clinical Significance</span>
                                    <span className="text-xs font-medium text-slate-700">{br.pgx.significance}</span>
                                  </div>
                                </div>
                                <div>
                                  <span className="text-[9px] text-hospital-muted block font-bold uppercase mb-1">Medication-Specific Genomic Considerations</span>
                                  <p className="text-xs text-slate-700 leading-relaxed font-medium bg-white p-2.5 border border-hospital-border rounded">
                                    {br.pgx.considerations}
                                  </p>
                                </div>
                              </div>
                            </div>

                            {/* 3. Clinical Compatibility */}
                            <div>
                              <div className="text-[10px] font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center gap-1">
                                <Activity size={11} className="text-hospital-blue" />
                                <span>Clinical Compatibility</span>
                              </div>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 text-xs bg-slate-50/30 p-3.5 border border-hospital-border rounded-lg">
                                <div className="space-y-2">
                                  <div>
                                    <span className="text-[9px] text-hospital-muted block font-bold uppercase">Patient Diagnoses</span>
                                    <span className="font-semibold text-slate-800">{br.compatibility.diagnoses}</span>
                                  </div>
                                  <div>
                                    <span className="text-[9px] text-hospital-muted block font-bold uppercase">Age Review</span>
                                    <span className="font-semibold text-slate-800">{br.compatibility.age}</span>
                                  </div>
                                  <div>
                                    <span className="text-[9px] text-hospital-muted block font-bold uppercase">Drug Allergies</span>
                                    <span className="font-semibold text-slate-800">{br.compatibility.allergies}</span>
                                  </div>
                                </div>
                                <div className="space-y-2">
                                  <div>
                                    <span className="text-[9px] text-hospital-muted block font-bold uppercase">Renal Function</span>
                                    <span className="font-semibold text-slate-800">{br.compatibility.renal}</span>
                                  </div>
                                  <div>
                                    <span className="text-[9px] text-hospital-muted block font-bold uppercase">Hepatic Function</span>
                                    <span className="font-semibold text-slate-800">{br.compatibility.hepatic}</span>
                                  </div>
                                  <div>
                                    <span className="text-[9px] text-hospital-muted block font-bold uppercase">Other Active Therapy</span>
                                    <span className="font-semibold text-slate-800">No drug-class overlaps with active list.</span>
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* 4. Drug Interaction Analysis */}
                            {simulation.interactions.length > 0 && (
                              <div>
                                <div className="text-[10px] font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center gap-1 text-hospital-red">
                                  <AlertTriangle size={11} />
                                  <span>Drug-Drug Interaction Analysis</span>
                                </div>
                                <div className="space-y-2">
                                  {simulation.interactions.map((inter, i) => (
                                    <div key={i} className="p-3 bg-red-50/50 border border-red-200 rounded-lg text-xs">
                                      <div className="flex justify-between items-center mb-1.5">
                                        <span className="font-bold text-slate-900">{inter.meds}</span>
                                        <span className={`px-2 py-0.2 text-[8px] font-bold uppercase rounded border ${
                                          inter.severity === 'Major' ? 'bg-red-100 text-hospital-red border-red-200' : 'bg-amber-100 text-amber-700 border-amber-200'
                                        }`}>
                                          {inter.severity} Interaction
                                        </span>
                                      </div>
                                      <div className="text-slate-700 mb-2 leading-relaxed font-medium"><span className="text-hospital-muted">Mechanism:</span> {inter.mechanism}</div>
                                      <div className="bg-white p-2 border border-red-100 rounded text-red-800 font-semibold"><span className="text-hospital-muted text-[10px] block uppercase font-bold tracking-wider mb-0.5">Clinical Recommendation</span>{inter.recommendation}</div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* 5. Safety Assessment */}
                            <div>
                              <div className="text-[10px] font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center gap-1">
                                <ShieldAlert size={11} className="text-hospital-blue" />
                                <span>Safety Assessment Categories</span>
                              </div>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-slate-50/30 p-3 border border-hospital-border rounded-lg text-xs">
                                <div className="p-2 bg-white border border-hospital-border rounded">
                                  <span className="text-[9px] text-hospital-muted block font-bold uppercase">Bleeding Risk</span>
                                  <div className="flex items-center gap-1.5 mt-1">
                                    <span className={`w-2 h-2 rounded-full ${br.safety.bleeding === 'High' ? 'bg-hospital-red' : br.safety.bleeding === 'Moderate' ? 'bg-hospital-yellow' : 'bg-hospital-green'}`}></span>
                                    <span className="font-bold text-slate-800">{br.safety.bleeding} Risk</span>
                                  </div>
                                </div>
                                <div className="p-2 bg-white border border-hospital-border rounded">
                                  <span className="text-[9px] text-hospital-muted block font-bold uppercase">Toxicity Risk</span>
                                  <div className="flex items-center gap-1.5 mt-1">
                                    <span className={`w-2 h-2 rounded-full ${br.safety.toxicity === 'High' ? 'bg-hospital-red' : br.safety.toxicity === 'Moderate' ? 'bg-hospital-yellow' : 'bg-hospital-green'}`}></span>
                                    <span className="font-bold text-slate-800">{br.safety.toxicity} Risk</span>
                                  </div>
                                </div>
                                <div className="p-2 bg-white border border-hospital-border rounded">
                                  <span className="text-[9px] text-hospital-muted block font-bold uppercase">Therapeutic Failure</span>
                                  <div className="flex items-center gap-1.5 mt-1">
                                    <span className={`w-2 h-2 rounded-full ${br.safety.failure === 'High' ? 'bg-hospital-red' : br.safety.failure === 'Moderate' ? 'bg-hospital-yellow' : 'bg-hospital-green'}`}></span>
                                    <span className="font-bold text-slate-800">{br.safety.failure} Risk</span>
                                  </div>
                                </div>
                                <div className="p-2 bg-white border border-hospital-border rounded">
                                  <span className="text-[9px] text-hospital-muted block font-bold uppercase">Contraindications</span>
                                  <span className="text-xs font-bold text-hospital-muted block mt-1">None reported</span>
                                </div>
                              </div>
                              <div className="mt-2.5 p-3 bg-blue-50/40 border border-blue-100 rounded-lg text-xs">
                                <span className="text-[9px] text-hospital-blue font-bold uppercase tracking-wider block mb-0.5">Monitoring Requirements</span>
                                <span className="font-semibold text-slate-700">{br.safety.monitoring}</span>
                              </div>
                            </div>

                            {/* 6. Expected Clinical Outcome */}
                            <div className="p-3.5 border border-hospital-border bg-slate-50/50 rounded-lg text-xs">
                              <div className="text-[10px] font-bold text-slate-800 uppercase tracking-wider mb-2.5">Expected Clinical Outcome</div>
                              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div>
                                  <span className="text-[9px] text-hospital-muted block font-bold uppercase">Expected Effectiveness</span>
                                  <span className="font-bold text-slate-800">{br.outcome.effectiveness}</span>
                                </div>
                                <div>
                                  <span className="text-[9px] text-hospital-muted block font-bold uppercase">Time to Therapeutic Effect</span>
                                  <span className="font-bold text-slate-800">{br.outcome.time}</span>
                                </div>
                                <div>
                                  <span className="text-[9px] text-hospital-muted block font-bold uppercase">Potential Complications</span>
                                  <span className="font-semibold text-slate-700">{br.outcome.complications}</span>
                                </div>
                              </div>
                            </div>

                            {/* 7. Clinical Reasoning (Structured) */}
                            <div>
                              <div className="text-[10px] font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center gap-1">
                                <ClipboardList size={11} className="text-hospital-blue" />
                                <span>Clinical Reasoning Matrix</span>
                              </div>
                              <div className="p-3.5 border border-hospital-border rounded-lg space-y-3.5">
                                <div>
                                  <span className="text-[9px] text-hospital-muted block font-bold uppercase mb-0.5">Pharmacological Mechanism</span>
                                  <p className="text-xs text-slate-700 leading-relaxed font-medium">{br.reasoning.mechanism}</p>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2.5 border-t border-hospital-border/60">
                                  <div>
                                    <span className="text-[9px] text-hospital-muted block font-bold uppercase mb-1">Patient-Specific Influencing Factors</span>
                                    <ul className="list-disc pl-4 space-y-1 text-xs font-semibold text-slate-700">
                                      {br.reasoning.factors.map((f: string, idx: number) => <li key={idx}>{f}</li>)}
                                      {br.reasoning.factors.length === 0 && <li>Age (64) and active standard physiological profile.</li>}
                                    </ul>
                                  </div>
                                  <div>
                                    <span className="text-[9px] text-hospital-muted block font-bold uppercase mb-1">Clinical Interpretation Summary</span>
                                    <div className="bg-slate-50 p-2.5 border border-hospital-border rounded text-xs font-semibold text-slate-800 leading-relaxed italic">
                                      "{br.reasoning.interpretation}"
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* 8. Alternative Therapy (Comparison) */}
                            {br.alternatives.length > 0 && (
                              <div>
                                <div className="text-[10px] font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center gap-1 text-hospital-blue">
                                  <ArrowLeftRight size={11} />
                                  <span>GenomixAI Recommended Alternative Therapy</span>
                                </div>
                                <div className="space-y-4">
                                  {br.alternatives.map((alt: any, altIdx: number) => {
                                    const isAltOpen = expandedAlternatives[`${br.id}-${altIdx}`] ?? true;
                                    return (
                                      <div key={altIdx} className="border border-hospital-border rounded-lg overflow-hidden bg-slate-50/40">
                                        
                                        {/* Alternative Card header */}
                                        <div 
                                          onClick={() => setExpandedAlternatives(prev => ({...prev, [`${br.id}-${altIdx}`]: !isAltOpen}))}
                                          className="p-3 bg-blue-50/40 hover:bg-blue-50/75 cursor-pointer transition-colors flex justify-between items-center"
                                        >
                                          <div className="flex items-center gap-2">
                                            <span className="bg-hospital-blue text-white text-[9px] font-mono px-1.5 py-0.2 rounded font-bold uppercase">
                                              Alternative Recommendation
                                            </span>
                                            <span className="text-xs font-bold text-slate-900">{alt.drugName} ({alt.recommendedDose})</span>
                                          </div>
                                          <div className="flex items-center gap-2">
                                            <span className="text-[10px] text-hospital-blue font-bold font-mono">{alt.evidenceLevel}</span>
                                            {isAltOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                                          </div>
                                        </div>

                                        {isAltOpen && (
                                          <div className="p-3.5 space-y-3.5 bg-white border-t border-hospital-border text-xs">
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                              <div>
                                                <span className="text-[9px] text-hospital-muted block font-bold uppercase">Drug Class & Frequency</span>
                                                <span className="font-semibold text-slate-800">{alt.class} • {alt.frequency}</span>
                                              </div>
                                              <div>
                                                <span className="text-[9px] text-hospital-muted block font-bold uppercase">Clinical Context for Recommendation</span>
                                                <span className="font-semibold text-slate-800">{alt.reasonRecommended}</span>
                                              </div>
                                            </div>

                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 bg-slate-50 p-2.5 border border-hospital-border rounded">
                                              <div className="p-2 bg-white rounded border border-hospital-border">
                                                <span className="text-[9px] text-emerald-700 block font-bold uppercase">Clinical Advantages</span>
                                                <span className="font-semibold text-slate-700">{alt.advantages}</span>
                                              </div>
                                              <div className="p-2 bg-white rounded border border-hospital-border">
                                                <span className="text-[9px] text-hospital-red block font-bold uppercase">Potential Disadvantages</span>
                                                <span className="font-semibold text-slate-700">{alt.disadvantages}</span>
                                              </div>
                                            </div>

                                            {/* Comparison Table */}
                                            <div>
                                              <span className="text-[9px] text-hospital-muted block font-bold uppercase mb-1.5">Therapeutic Comparison Matrix</span>
                                              <div className="overflow-x-auto border border-hospital-border rounded">
                                                <table className="w-full text-[11px] border-collapse">
                                                  <thead>
                                                    <tr className="bg-slate-50 border-b border-hospital-border font-mono text-[9px] font-bold text-slate-500 uppercase">
                                                      <th className="py-1.5 px-3.5 text-left font-bold">Metric</th>
                                                      <th className="py-1.5 px-3.5 text-left font-bold">Current ({br.name})</th>
                                                      <th className="py-1.5 px-3.5 text-left font-bold text-hospital-blue bg-blue-50/20">Alternative ({alt.drugName})</th>
                                                    </tr>
                                                  </thead>
                                                  <tbody className="divide-y divide-hospital-border font-semibold text-slate-700">
                                                    <tr>
                                                      <td className="py-1.5 px-3.5 bg-slate-50/50">Primary Purpose</td>
                                                      <td className="py-1.5 px-3.5">Cardiac Thrombosis Prevention</td>
                                                      <td className="py-1.5 px-3.5 text-hospital-blue">{alt.drugName === 'Apixaban' ? 'Stroke Prevention in AFib' : 'Antiplatelet Inhibition'}</td>
                                                    </tr>
                                                    <tr>
                                                      <td className="py-1.5 px-3.5 bg-slate-50/50">Bleeding Risk</td>
                                                      <td className="py-1.5 px-3.5">{br.safety.bleeding === 'High' ? 'High Risk' : 'Moderate'}</td>
                                                      <td className="py-1.5 px-3.5 text-hospital-blue">{alt.comparison.bleeding}</td>
                                                    </tr>
                                                    <tr>
                                                      <td className="py-1.5 px-3.5 bg-slate-50/50">Monitoring Requirement</td>
                                                      <td className="py-1.5 px-3.5">Intense clinical tracking</td>
                                                      <td className="py-1.5 px-3.5 text-hospital-blue">{alt.comparison.monitoring}</td>
                                                    </tr>
                                                    <tr>
                                                      <td className="py-1.5 px-3.5 bg-slate-50/50">Drug Interactions</td>
                                                      <td className="py-1.5 px-3.5">Major clinical risks</td>
                                                      <td className="py-1.5 px-3.5 text-hospital-blue">{alt.comparison.interactions}</td>
                                                    </tr>
                                                    <tr>
                                                      <td className="py-1.5 px-3.5 bg-slate-50/50">Genomic Suitability</td>
                                                      <td className="py-1.5 px-3.5 text-hospital-red">{br.verdict === 'High Risk' ? 'Impaired metabolizer state' : 'Standard sensitivity'}</td>
                                                      <td className="py-1.5 px-3.5 text-emerald-700 bg-emerald-50/10 font-bold">{alt.comparison.genomics}</td>
                                                    </tr>
                                                  </tbody>
                                                </table>
                                              </div>
                                            </div>

                                          </div>
                                        )}
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                            )}

                            {/* 9. Supporting Evidence Accordion */}
                            <div>
                              <div className="text-[10px] font-bold text-slate-800 uppercase tracking-wider mb-2">Supporting Evidence (Expandable Guidelines)</div>
                              <div className="space-y-1.5">
                                {[
                                  { key: 'guidelines', title: 'Clinical Guidelines', content: `ACC/AHA/HRS clinical taskforce for management of cardiovascular disorders. Recommends direct oral anticoagulants over VKAs for eligible patients (Class I recommendation) based on comprehensive hazard ratios.` },
                                  { key: 'fda', title: 'FDA Approved Labeling & Warning', content: `Official FDA labeling outlines mandatory warning alerts regarding reduced pharmacological benefit of Clopidogrel in CYP2C19 Poor Metabolizers. Clinicians should evaluate alternative antiplatelet strategies.` },
                                  { key: 'cpic', title: 'CPIC Pharmacogenomic Guidelines', content: `CPIC (Clinical Pharmacogenetics Implementation Consortium) level-A evidence. Strongly advises using prasugrel or ticagrelor instead of clopidogrel in acute coronary syndrome patients with CYP2C19 loss-of-function variants.` },
                                  { key: 'trials', title: 'Relevant Clinical Trials (ARISTOTLE & PLATO)', content: `PLATO trial details superior absolute risk reduction in secondary MI events with Ticagrelor compared to Clopidogrel without a major overall increase in hemorrhage risk.` },
                                  { key: 'monograph', title: 'Drug Monograph and Kinetic Reference', content: `Molecular bio-activation profile: Warfarin exerts effect within 72 hours; clopidogrel reaches platelet steady-state in 3-5 days. Kinetic variations heavily amplified by genetic variants.` }
                                ].map((item) => {
                                  const isEvOpen = expandedEvidence[`${br.id}-${item.key}`] ?? false;
                                  return (
                                    <div key={item.key} className="border border-hospital-border rounded bg-slate-50/50 overflow-hidden text-xs">
                                      <div 
                                        onClick={() => setExpandedEvidence(prev => ({...prev, [`${br.id}-${item.key}`]: !isEvOpen}))}
                                        className="p-2.5 flex justify-between items-center cursor-pointer hover:bg-slate-100 transition-colors"
                                      >
                                        <span className="font-bold text-slate-800">{item.title}</span>
                                        {isEvOpen ? <ChevronUp size={12} className="text-hospital-blue" /> : <ChevronDown size={12} className="text-hospital-muted" />}
                                      </div>
                                      {isEvOpen && (
                                        <div className="p-3 bg-white border-t border-hospital-border text-slate-700 leading-relaxed font-medium">
                                          {item.content}
                                        </div>
                                      )}
                                    </div>
                                  );
                                })}
                              </div>
                            </div>

                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>

                  </div>
                );
              })}
            </div>
          </section>

          {/* Assessment Chronological Timeline Card */}
          <section className="bg-white border border-hospital-border rounded-xl p-5 shadow-xs" id="assessment-timeline-card">
            <div className="flex items-center gap-1.5 pb-2.5 border-b border-hospital-border mb-4">
              <Clock size={14} className="text-hospital-blue" />
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Clinical Assessment Lifecycle</h3>
            </div>
            
            <div className="relative pl-6 space-y-4">
              {/* Timeline central vertical line */}
              <div className="absolute left-2.5 top-2 bottom-2 w-[1.5px] bg-slate-200"></div>

              {[
                { status: 'Draft', label: 'Medication Assessment Created', date: '18 Jul 2026', time: '09:42', done: true },
                { status: 'Draft', label: 'Proposed Medication Order Formed', date: '18 Jul 2026', time: '09:45', done: proposedMeds.length > 0 },
                { status: 'Pharmacist Review', label: 'Request Sent for Pharmacist Review', date: '18 Jul 2026', time: '09:51', done: assessmentStatus === 'Pharmacist Review' || assessmentStatus === 'Approved' || assessmentStatus === 'Finalized' },
                { status: 'Approved', label: 'Pharmacist Recommendation Approved', date: '18 Jul 2026', time: '10:15', done: assessmentStatus === 'Approved' || assessmentStatus === 'Finalized' },
                { status: 'Finalized', label: 'Prescription Finalized', date: '18 Jul 2026', time: '10:22', done: assessmentStatus === 'Finalized' }
              ].map((step, idx) => (
                <div key={idx} className="flex items-start gap-4 text-xs relative">
                  {/* Circle Indicator */}
                  <div className={`absolute -left-[19.5px] w-3 h-3 rounded-full border-2 ${
                    step.done ? 'bg-hospital-blue border-hospital-blue' : 'bg-white border-slate-300'
                  } z-10`}></div>
                  
                  <div className="flex-1 flex flex-col sm:flex-row sm:justify-between gap-1">
                    <div>
                      <span className={`font-bold ${step.done ? 'text-slate-900' : 'text-slate-400'}`}>
                        {step.label}
                      </span>
                      {step.done && idx === 2 && assessmentStatus === 'Pharmacist Review' && (
                        <span className="ml-2 px-1.5 py-0.2 bg-purple-50 text-purple-700 text-[8px] font-mono rounded font-bold uppercase animate-pulse border border-purple-200">
                          Review Queue STAT
                        </span>
                      )}
                    </div>
                    <div className="text-[10px] text-hospital-muted font-mono font-semibold flex items-center gap-1.5 shrink-0">
                      <span>{step.date}</span>
                      <span>•</span>
                      <span>{step.time}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Pharmacist Live Simulation Panel (Requested: "if approved on pharma side it should approve on doctor side too and all") */}
          {assessmentStatus === 'Pharmacist Review' && (
            <section className="bg-purple-50/60 border border-purple-200 rounded-xl p-5 shadow-xs animate-pulse">
              <div className="flex items-center gap-2 mb-3">
                <Settings size={16} className="text-purple-700 animate-spin" />
                <h3 className="text-xs font-bold text-purple-900 uppercase tracking-wider">🔬 Pharmacist Portal Simulation (Action Needed)</h3>
              </div>
              <p className="text-xs text-purple-900 font-medium mb-3 leading-relaxed">
                You have sent this case to the clinical pharmacist. Under the hood, the pharmacist reviews the attached genomic variant profile, active medications, and the cardiac labs.
              </p>
              <div className="bg-white p-3 border border-purple-100 rounded-lg text-xs mb-3 font-semibold text-slate-800">
                <span className="text-[9px] text-purple-600 font-bold uppercase tracking-wider block mb-1">Pharmacist assigned</span>
                {assignedPharmacist} (Lagos Cardiology Ward Clinic)
                {pharmacistMessage && (
                  <div className="mt-2 text-slate-600 italic border-l-2 border-purple-300 pl-2">
                    Message: "{pharmacistMessage}"
                  </div>
                )}
              </div>

            </section>
          )}

        </main>

        {/* ==================== RIGHT PANEL (25%): Clinical Decision Panel ==================== */}
        <aside className="lg:col-span-1 space-y-6 flex flex-col" id="right-panel-decisions">
          
          {/* Assessment Status Badge Panel */}
          <div className="bg-white border border-hospital-border rounded-xl p-4 shadow-xs">
            <span className="text-[10px] text-hospital-muted font-bold uppercase tracking-wider block mb-1.5">Assessment Status</span>
            <div className="flex items-center justify-between">
              <span className={`px-3 py-1 text-xs font-bold rounded-lg ${
                assessmentStatus === 'Finalized' ? 'bg-emerald-100 text-hospital-green border border-emerald-200' :
                assessmentStatus === 'Approved' ? 'bg-blue-100 text-hospital-blue border border-blue-200' :
                assessmentStatus === 'Pharmacist Review' ? 'bg-purple-100 text-purple-800 border border-purple-200 animate-pulse' :
                'bg-slate-100 text-slate-700 border border-slate-200'
              }`}>
                {assessmentStatus === 'Draft' ? 'Draft' : assessmentStatus}
              </span>
              <span className="text-[10px] text-hospital-muted font-mono font-medium">Real-time synced</span>
            </div>
          </div>

          {/* Interactive EHR Review Checklist */}
          <div className="bg-white border border-hospital-border rounded-xl p-4 shadow-xs">
            <div className="flex items-center gap-1.5 pb-2 border-b border-hospital-border mb-3">
              <CheckCircle2 size={14} className="text-hospital-blue" />
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">EHR Review Checklist</h3>
            </div>
            <p className="text-[11px] text-hospital-muted mb-3 leading-relaxed">
              Verify safety items before authorizing finalized outpatient pharmacy orders.
            </p>
            <div className="space-y-2">
              {[
                { key: 'entered', label: 'Proposed medications entered' },
                { key: 'interactions', label: 'EHR drug interaction review completed' },
                { key: 'genomics', label: 'Pharmacogenomic variants reviewed' },
                { key: 'evidence', label: 'CPIC clinical evidence validated' },
                { key: 'reasoning', label: 'Structured clinical rationale noted' }
              ].map((item) => (
                <label 
                  key={item.key} 
                  className="flex items-center gap-2.5 text-xs text-slate-700 font-semibold cursor-pointer select-none p-1.5 rounded hover:bg-slate-50 transition-colors"
                >
                  <input 
                    type="checkbox" 
                    className="rounded text-hospital-blue focus:ring-hospital-blue w-3.5 h-3.5 border-slate-300"
                    checked={checklist[item.key] ?? false}
                    onChange={(e) => setChecklist({ ...checklist, [item.key]: e.target.checked })}
                  />
                  <span>{item.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Physician Actions Box */}
          <div className="bg-white border border-hospital-border rounded-xl p-4 shadow-xs space-y-3">
            <div className="flex items-center gap-1.5 pb-2 border-b border-hospital-border">
              <Settings size={14} className="text-hospital-blue" />
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Physician Action Center</h3>
            </div>

            {/* Finalize Prescription Button */}
            <button 
              onClick={handleFinalizeAction}
              disabled={assessmentStatus === 'Pharmacist Review'}
              className={`w-full py-2.5 rounded-lg text-xs font-bold text-white transition-all shadow-xs flex items-center justify-center gap-2 cursor-pointer ${
                assessmentStatus === 'Pharmacist Review' 
                  ? 'bg-slate-300 cursor-not-allowed opacity-60' 
                  : 'bg-hospital-blue hover:bg-blue-800'
              }`}
              id="finalize-prescription-btn"
            >
              <Check size={14} />
              <span>Finalize Prescription</span>
            </button>

            {/* Secondary Actions */}
            <div className="grid grid-cols-2 gap-2">
              <button 
                onClick={() => {
                  setAssessmentStatus('Draft');
                  const timeStr = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });
                  setAuditLog(prev => [...prev, { date: '18 Jul 2026', time: timeStr, event: 'Status Updated', detail: 'Returned medication assessment back to Draft state' }]);
                }}
                className="py-2 px-1 bg-slate-100 hover:bg-slate-200 border border-hospital-border rounded text-[11px] font-bold text-slate-700 text-center transition-colors cursor-pointer"
              >
                Modify Medication
              </button>
              <button 
                onClick={() => setShowPharmacistModal(true)}
                className="py-2 px-1 bg-purple-50 hover:bg-purple-100 border border-purple-200 rounded text-[11px] font-bold text-purple-700 text-center transition-colors cursor-pointer"
                id="request-pharmacist-review-btn"
              >
                Request Pharmacist
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button 
                onClick={() => {
                  setAssessmentStatus('Draft');
                  const timeStr = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });
                  setAuditLog(prev => [...prev, { date: '18 Jul 2026', time: timeStr, event: 'Draft Saved', detail: 'Temporary EHR draft persisted' }]);
                }}
                className="py-1.5 px-1 bg-slate-50 hover:bg-slate-100 border border-hospital-border rounded text-[11px] font-bold text-slate-700 transition-colors cursor-pointer"
              >
                Save Draft
              </button>
              <button 
                onClick={() => setShowNoteModal(true)}
                className="py-1.5 px-1 bg-slate-50 hover:bg-slate-100 border border-hospital-border rounded text-[11px] font-bold text-slate-700 transition-colors cursor-pointer"
              >
                Add Clinical Note
              </button>
            </div>

            <button 
              onClick={() => {
                const timeStr = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });
                setAuditLog(prev => [...prev, { date: '18 Jul 2026', time: timeStr, event: 'Report Exported', detail: 'Exported official clinical PDF report to patient chart file' }]);
                alert('EHR system simulated exporting PDF report successfully!');
              }}
              className="w-full py-1.5 bg-slate-50 hover:bg-slate-100 border border-hospital-border rounded text-[11px] font-bold text-slate-700 flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
            >
              <FileDown size={12} />
              <span>Generate PDF Report</span>
            </button>
          </div>

          {/* Audit History Timeline Log */}
          <div className="bg-white border border-hospital-border rounded-xl p-4 shadow-xs flex-1 flex flex-col max-h-[300px]">
            <div className="flex items-center gap-1.5 pb-2 border-b border-hospital-border mb-3">
              <History size={14} className="text-hospital-muted" />
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">EHR Audit History Trail</h3>
            </div>
            
            <div className="space-y-3 flex-1 overflow-y-auto pr-1">
              {auditLog.slice().reverse().map((log, logIdx) => (
                <div key={logIdx} className="text-[11px] pb-2.5 border-b border-slate-100 last:border-0">
                  <div className="flex justify-between font-mono text-[9px] font-bold text-slate-500 mb-0.5">
                    <span>{log.date} • {log.time}</span>
                    <span className="text-hospital-blue">logged</span>
                  </div>
                  <div className="font-bold text-slate-800">{log.event}</div>
                  <div className="text-hospital-muted leading-relaxed mt-0.5 font-medium">{log.detail}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Disclaimer (EHR Requirement) */}
          <div className="p-3 bg-blue-50/50 border border-blue-100 rounded-lg text-[10px] text-hospital-blue font-medium leading-relaxed">
            <span className="font-bold uppercase block mb-0.5">Clinical Disclaimer</span>
            GenomixAI is a clinician decision support tool. All prescription decisions remain the sole professional responsibility of the attending licensed physician.
          </div>

        </aside>

      </div>

      {/* ==================== PHARMACIST COLLABORATION MODAL ==================== */}
      <AnimatePresence>
        {showPharmacistModal && (
          <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-[200] flex items-center justify-center p-4">
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white w-full max-w-lg rounded-xl shadow-xl border border-hospital-border overflow-hidden"
            >
              <div className="p-4 border-b border-hospital-border flex justify-between items-center bg-slate-50">
                <div className="flex items-center gap-2">
                  <Pill size={16} className="text-hospital-blue" />
                  <h3 className="font-bold text-slate-900">Request Pharmacist Consultation</h3>
                </div>
                <button 
                  onClick={() => setShowPharmacistModal(false)} 
                  className="text-hospital-muted hover:text-slate-800 cursor-pointer"
                >
                  <X size={18} />
                </button>
              </div>

              <form onSubmit={submitPharmacistReview} className="p-5 space-y-4">
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-[10px] font-bold text-hospital-muted uppercase mb-1.5 block tracking-wider">Review Priority</label>
                    <select 
                      value={pharmPriority}
                      onChange={(e) => setPharmPriority(e.target.value as any)}
                      className="w-full bg-white border border-hospital-border rounded-lg px-3 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-hospital-blue/10 focus:border-hospital-blue text-slate-800"
                    >
                      <option value="Routine">Routine</option>
                      <option value="Urgent">Urgent</option>
                      <option value="STAT">STAT (Emergent)</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-[10px] font-bold text-hospital-muted uppercase mb-1.5 block tracking-wider">Assigned Pharmacist</label>
                    <select 
                      value={assignedPharmacist}
                      onChange={(e) => setAssignedPharmacist(e.target.value)}
                      className="w-full bg-white border border-hospital-border rounded-lg px-3 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-hospital-blue/10 focus:border-hospital-blue text-slate-800"
                    >
                      <option value="Dr. Clara Uzor, PharmD">Dr. Clara Uzor, PharmD (Lagos Hospital)</option>
                      <option value="Dr. Emeka Johnson, PharmD">Dr. Emeka Johnson, PharmD (Cardiology Clinical Pharmacist)</option>
                      <option value="Dr. Sarah Jenkins, PharmD">Dr. Sarah Jenkins, PharmD (On-call Pharmacist)</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-[10px] font-bold text-hospital-muted uppercase mb-1.5 block tracking-wider">Optional Consult Message</label>
                  <textarea 
                    placeholder="e.g., Please review the anticoagulation strategy due to elevated risk of bleeding and CYP2C19 Poor Metabolizer genotype..."
                    className="w-full bg-white border border-hospital-border rounded-lg px-3 py-2 text-xs h-24 focus:outline-none focus:ring-2 focus:ring-hospital-blue/10 focus:border-hospital-blue text-slate-800"
                    value={pharmacistMessage}
                    onChange={(e) => setPharmacistMessage(e.target.value)}
                  />
                </div>

                {/* EHR Auto Attachments metadata display */}
                <div className="p-3 bg-slate-50 border border-hospital-border rounded-lg space-y-1.5">
                  <span className="text-[9px] text-hospital-blue font-bold uppercase tracking-wider block">EHR System Auto-Attachments</span>
                  <div className="grid grid-cols-2 gap-2 text-[10px] text-hospital-muted font-semibold">
                    <div className="flex items-center gap-1">✅ Proposed medication templates</div>
                    <div className="flex items-center gap-1">✅ GenomixAI genomic variants</div>
                    <div className="flex items-center gap-1">✅ INR and hepatic lab summaries</div>
                    <div className="flex items-center gap-1">✅ Attending doctor clinical rationale</div>
                  </div>
                </div>

                <div className="flex justify-end gap-2.5 pt-2">
                  <button 
                    type="button" 
                    onClick={() => setShowPharmacistModal(false)}
                    className="px-4 py-2 border border-hospital-border rounded-lg text-xs font-bold text-slate-700 hover:bg-slate-50 cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit"
                    className="px-5 py-2 bg-purple-700 hover:bg-purple-800 text-white rounded-lg text-xs font-bold transition-colors cursor-pointer"
                    id="submit-pharmacist-review-btn"
                  >
                    Send to Pharmacist Queue
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ==================== PHYSICIAN CLINICAL NOTE MODAL ==================== */}
      <AnimatePresence>
        {showNoteModal && (
          <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-[200] flex items-center justify-center p-4">
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white w-full max-w-md rounded-xl shadow-xl border border-hospital-border overflow-hidden"
            >
              <div className="p-4 border-b border-hospital-border flex justify-between items-center bg-slate-50">
                <div className="flex items-center gap-2">
                  <ClipboardList size={16} className="text-hospital-blue" />
                  <h3 className="font-bold text-slate-900">Add Clinical Progress Note</h3>
                </div>
                <button 
                  onClick={() => setShowNoteModal(false)} 
                  className="text-hospital-muted hover:text-slate-800 cursor-pointer"
                >
                  <X size={18} />
                </button>
              </div>

              <form onSubmit={handleAddClinicalNoteSubmit} className="p-5 space-y-4">
                <div>
                  <label className="text-[10px] font-bold text-hospital-muted uppercase mb-1.5 block tracking-wider">Progress Note Content</label>
                  <textarea 
                    required
                    placeholder="Enter details of your clinical reasoning or adjustments..."
                    className="w-full bg-white border border-hospital-border rounded-lg px-3 py-2 text-xs h-28 focus:outline-none focus:ring-2 focus:ring-hospital-blue/10 focus:border-hospital-blue text-slate-800 font-medium"
                    value={physicianNoteText}
                    onChange={(e) => setPhysicianNoteText(e.target.value)}
                  />
                </div>

                <div className="flex justify-end gap-2.5 pt-2">
                  <button 
                    type="button" 
                    onClick={() => setShowNoteModal(false)}
                    className="px-4 py-2 border border-hospital-border rounded-lg text-xs font-bold text-slate-700 hover:bg-slate-50 cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit"
                    className="px-5 py-2 bg-hospital-blue hover:bg-blue-800 text-white rounded-lg text-xs font-bold transition-colors cursor-pointer"
                  >
                    Save to Audit Trail
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </div>
  );
};

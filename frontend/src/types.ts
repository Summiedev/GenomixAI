export interface Patient {
  id: string;
  name: string;
  age: number;
  sex: 'M' | 'F';
  mrn: string;
  lastVisit: string;
  status: 'Active' | 'Inactive';
  conditions: string[];
  medications: Medication[];
  allergies: string[];
  labs: LabResult[];
  genomicProfile?: GenomicProfile;
  clinicalNotes?: string;
}

export interface Medication {
  id: string;
  name: string;
  dose: string;
  frequency: string;
  route: string;
  startDate: string;
  status: 'Active' | 'Discontinued';
}

export interface LabResult {
  name: string;
  value: string;
  unit: string;
  date: string;
  status: 'Normal' | 'High' | 'Low';
}

export interface GenomicProfile {
  variants: {
    gene: string;
    variant: string;
    phenotype: string;
  }[];
}

export interface DrugInfo {
  id: string;
  name: string;
  class: string;
  standardDose: string;
  indications: string[];
}

export interface SimulationResult {
  metabolicActivation: string;
  clearanceRate: string;
  expectedEffectiveness: string;
  riskLevel: 'Safe' | 'Moderate' | 'High';
  suitabilityVerdict: 'Acceptable' | 'Caution' | 'High Risk';
  evaluationSummary: {
    suitability: 'Low' | 'Moderate' | 'High';
    effectiveness: 'Reduced' | 'Adequate';
    safety: 'Elevated Risk' | 'Acceptable';
  };
  clinicalInterpretation: {
    mechanism: string;
    patientFactors: string;
    expectedImpact: string;
  };
  dosageEvaluation: string[];
  patientHistory: {
    response: string;
    insight: string;
  };
  riskInterpretation: {
    failure: 'Low' | 'Moderate' | 'High';
    adverse: 'Low' | 'Moderate' | 'High';
  };
  clinicalConsiderations: string[];
  riskBreakdown: {
    effectiveness: number;
    toxicity: number;
    interaction: number;
  };
  interpretation: string; // Keep for backward compatibility or simple views
  supportingEvidence?: {
    pharmacology: string;
    clinicalHistory: string;
    causalLink: string;
    references: string[];
  };
  alternativeSuggestions?: {
    drugName: string;
    class: string;
    recommendedDose: string;
    frequency: string;
    reasoning: string;
    benefitAnalysis: string;
  }[];
}

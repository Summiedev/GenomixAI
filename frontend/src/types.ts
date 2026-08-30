export interface Patient {
  id: string;
  organizationId?: string;
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
  variants: { gene: string; variant: string; phenotype: string }[];
}

export interface DrugInfo {
  id: string;
  name: string;
  class: string;
  standardDose: string;
  indications: string[];
}

export const MOCK_PATIENTS = [
  {
    id: '1',
    name: 'Sarah Jenkins',
    age: 64,
    sex: 'F',
    mrn: 'MRN-882910',
    lastVisit: '2026-03-12',
    status: 'Active',
    conditions: ['Hypertension', 'Post-MI', 'Hyperlipidemia'],
    medications: [
      { id: 'm1', name: 'Aspirin', dose: '75mg', frequency: 'Daily', route: 'Oral', startDate: '2025-11-20', status: 'Active' },
      { id: 'm2', name: 'Atorvastatin', dose: '40mg', frequency: 'Daily', route: 'Oral', startDate: '2025-11-20', status: 'Active' }
    ],
    allergies: ['Penicillin'],
    labs: [
      { name: 'INR', value: '1.1', unit: '', date: '2026-04-01', status: 'Normal' },
      { name: 'LDL', value: '110', unit: 'mg/dL', date: '2026-04-01', status: 'High' },
      { name: 'ALT', value: '24', unit: 'U/L', date: '2026-04-01', status: 'Normal' }
    ],
    genomicProfile: {
      variants: [
        { gene: 'CYP2C19', variant: '*2/*2', phenotype: 'Poor Metabolizer' },
        { gene: 'SLCO1B1', variant: '*5/*5', phenotype: 'Low Transporter Activity' }
      ]
    },
    clinicalNotes: "Patient presents with recurring chest pain. History of MI in 2025. Currently on standard dual antiplatelet therapy. Genetic testing ordered to evaluate clopidogrel responsiveness due to suspected suboptimal platelet inhibition."
  },
  {
    id: '2',
    name: 'Robert Chen',
    age: 52,
    sex: 'M',
    mrn: 'MRN-441209',
    lastVisit: '2026-02-28',
    status: 'Active',
    conditions: ['Type 2 Diabetes', 'Chronic Kidney Disease'],
    medications: [
      { id: 'm3', name: 'Metformin', dose: '1000mg', frequency: 'BID', route: 'Oral', startDate: '2024-05-15', status: 'Active' }
    ],
    allergies: [],
    labs: [
      { name: 'HbA1c', value: '7.4', unit: '%', date: '2026-03-15', status: 'High' },
      { name: 'eGFR', value: '45', unit: 'mL/min', date: '2026-03-15', status: 'Low' }
    ],
    clinicalNotes: "Monitoring renal function closely. HbA1c remains above target. Discussed lifestyle modifications and potential insulin therapy if targets not met in next 3 months."
  }
];

export const RECENT_PATIENTS = [
  MOCK_PATIENTS[0],
  MOCK_PATIENTS[1]
];

export const MOCK_DRUGS = [
  {
    id: 'd1',
    name: 'Clopidogrel',
    class: 'Antiplatelet',
    standardDose: '75mg',
    indications: ['Post-MI', 'Stroke Prevention', 'ACS']
  },
  {
    id: 'd2',
    name: 'Warfarin',
    class: 'Anticoagulant',
    standardDose: '5mg',
    indications: ['AFib', 'DVT', 'PE']
  },
  {
    id: 'd3',
    name: 'Lisinopril',
    class: 'ACE Inhibitor',
    standardDose: '10mg',
    indications: ['Hypertension', 'Heart Failure']
  }
];


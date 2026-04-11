import json
import os
from random import randint, choice, uniform
from datetime import datetime, timedelta
from models import Patient, Medication, LabResult, GenomicProfile, GenomicVariant

N = 100
DATA_PATH = os.path.join(os.path.dirname(__file__), 'static', 'patients.json')

NAMES = [
    'Sarah Jenkins', 'Robert Chen', 'Maria Lopez', 'James Smith', 'Aisha Patel', 'David Kim', 'Linda Brown', 'Mohammed Ali', 'Emily Clark', 'John Lee',
    # ... add more names for realism
]
SEXES = ['M', 'F']
ETHNICITIES = ['Caucasian', 'African American', 'Asian', 'Hispanic', 'Other']
BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
CONDITIONS = ['Hypertension', 'Type 2 Diabetes', 'Myocardial Infarction', 'Asthma', 'COPD', 'Heart Failure', 'Stroke', 'Hyperlipidemia', 'CKD']
MEDS = ['Aspirin', 'Atorvastatin', 'Metformin', 'Clopidogrel', 'Warfarin', 'Ticagrelor', 'Prasugrel']

CLINICAL_NOTES = [
    "Patient shows reduced response to standard antiplatelet therapy.",
    "Dose adjustment required due to bleeding risk.",
    "Possible metabolic variability suspected.",
    "Stable on current regimen.",
    "History of adverse reaction to statins.",
    "Consider alternative anticoagulant due to INR variability."
]

def random_date(start_year=2010, end_year=2026):
    year = randint(start_year, end_year)
    month = randint(1, 12)
    day = randint(1, 28)
    return f"{year}-{month:02d}-{day:02d}"

def generate_and_save_patients():
    patients = []
    for i in range(N):
        name = choice(NAMES)
        sex = choice(SEXES)
        age = randint(18, 90)
        mrn = f"MRN-{randint(100000,999999)}"
        last_visit = random_date(2025, 2026)
        status = choice(['Active', 'Inactive'])
        conditions = [choice(CONDITIONS) for _ in range(randint(1, 3))]
        meds = [Medication(
            id=f"m{i}{j}",
            name=choice(MEDS),
            dose=f"{randint(10,100)}mg",
            frequency=choice(["Daily", "BID", "TID"]),
            route="Oral",
            startDate=random_date(2015, 2026),
            status=choice(["Active", "Discontinued"])
        ).dict() for j in range(randint(1, 3))]
        allergies = [choice(["Penicillin", "None", "Sulfa", "Aspirin"])]
        labs = [LabResult(
            name=choice(["INR", "LDL", "ALT", "eGFR", "HbA1c"]),
            value=str(round(uniform(0.8, 8.0), 2)),
            unit=choice(["mg/dL", "%", "U/L", "mL/min", ""]),
            date=random_date(2024, 2026),
            status=choice(["Normal", "High", "Low"])
        ).dict() for _ in range(randint(2, 5))]
        genomic = GenomicProfile(variants=[GenomicVariant(
            gene=choice(["CYP2C19", "SLCO1B1", "CYP2C9"]),
            variant=choice(["*1/*1", "*2/*2", "*5/*5"]),
            phenotype=choice(["Normal Metabolizer", "Poor Metabolizer", "Low Transporter Activity"])
        )]).dict() if randint(0, 1) else None
        notes = choice(CLINICAL_NOTES)
        patients.append(Patient(
            id=str(i+1),
            name=name,
            age=age,
            sex=sex,
            mrn=mrn,
            lastVisit=last_visit,
            status=status,
            conditions=conditions,
            medications=meds,
            allergies=allergies,
            labs=labs,
            genomicProfile=genomic,
            clinicalNotes=notes
        ).dict())
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(patients, f, indent=2)

if __name__ == "__main__":
    generate_and_save_patients()

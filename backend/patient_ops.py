from fastapi import HTTPException
from models import Patient, Medication
from data import load_patients
import json, os

DATA_PATH = os.path.join(os.path.dirname(__file__), 'static', 'patients.json')

def save_patients(patients):
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump([p.dict() for p in patients], f, indent=2)

def add_patient(patient: Patient):
    patients = load_patients()
    if any(p.id == patient.id for p in patients):
        raise HTTPException(status_code=400, detail='Patient already exists')
    patients.append(patient)
    save_patients(patients)
    return patient

def update_patient(patient_id: str, update: dict):
    patients = load_patients()
    for i, p in enumerate(patients):
        if p.id == patient_id:
            for k, v in update.items():
                setattr(p, k, v)
            save_patients(patients)
            return p
    raise HTTPException(status_code=404, detail='Patient not found')

def add_medication(patient_id: str, med: Medication):
    patients = load_patients()
    for p in patients:
        if p.id == patient_id:
            p.medications.append(med)
            save_patients(patients)
            return p
    raise HTTPException(status_code=404, detail='Patient not found')

def discontinue_medication(patient_id: str, med_id: str):
    patients = load_patients()
    for p in patients:
        if p.id == patient_id:
            for m in p.medications:
                if m.id == med_id:
                    m.status = 'Discontinued'
                    save_patients(patients)
                    return p
    raise HTTPException(status_code=404, detail='Medication or patient not found')



from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import Patient, DrugInfo, SimulationResult, Medication
from data import load_patients, load_drugs
from simulation import simulate_drug_response
from patient_ops import add_patient, update_patient, add_medication, discontinue_medication
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/patients", response_model=List[Patient])
def get_patients():
    return load_patients()

@app.get("/api/patient/{patient_id}", response_model=Patient)
def get_patient(patient_id: str):
    patients = load_patients()
    for p in patients:
        if p.id == patient_id:
            return p
    raise HTTPException(status_code=404, detail="Patient not found")

@app.get("/api/drugs", response_model=List[DrugInfo])
def get_drugs():
    return load_drugs()

@app.post("/api/simulate", response_model=SimulationResult)
def simulate(payload: dict):
    # Expecting: {"patient_id": str, "drug_id": str, "dose": float, "frequency": str}
    patients = load_patients()
    drugs = load_drugs()
    patient = next((p for p in patients if p.id == payload.get("patient_id")), None)
    drug = next((d for d in drugs if d.id == payload.get("drug_id")), None)
    if not patient or not drug:
        raise HTTPException(status_code=400, detail="Invalid patient or drug")
    dose = float(payload.get("dose", 0))
    frequency = payload.get("frequency", "Once Daily")
    return simulate_drug_response(patient, drug, dose, frequency)


# --- Patient/Medication Management ---
@app.post("/api/patient", response_model=Patient)
def create_patient(patient: Patient):
    return add_patient(patient)

@app.patch("/api/patient/{patient_id}", response_model=Patient)
def patch_patient(patient_id: str, update: dict):
    return update_patient(patient_id, update)

@app.post("/api/patient/{patient_id}/medication", response_model=Patient)
def add_patient_medication(patient_id: str, med: Medication):
    return add_medication(patient_id, med)

@app.patch("/api/patient/{patient_id}/medication/{med_id}", response_model=Patient)
def discontinue_patient_medication(patient_id: str, med_id: str):
    return discontinue_medication(patient_id, med_id)

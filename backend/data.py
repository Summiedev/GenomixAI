import os
import json
from typing import List
from models import Patient, DrugInfo

DATA_PATH = os.path.join(os.path.dirname(__file__), 'static', 'patients.json')
DRUGS_PATH = os.path.join(os.path.dirname(__file__), 'static', 'drugs.json')

def load_patients() -> List[Patient]:
    if not os.path.exists(DATA_PATH):
        from .generate_patients import generate_and_save_patients
        generate_and_save_patients()
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [Patient(**p) for p in data]

def load_drugs() -> List[DrugInfo]:
    with open(DRUGS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [DrugInfo(**d) for d in data]

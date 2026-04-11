from pydantic import BaseModel
from typing import List, Optional, Literal, Dict

class LabResult(BaseModel):
    name: str
    value: str
    unit: str
    date: str
    status: Literal['Normal', 'High', 'Low']

class Medication(BaseModel):
    id: str
    name: str
    dose: str
    frequency: str
    route: str
    startDate: str
    status: Literal['Active', 'Discontinued']

class GenomicVariant(BaseModel):
    gene: str
    variant: str
    phenotype: str

class GenomicProfile(BaseModel):
    variants: List[GenomicVariant]

class Patient(BaseModel):
    id: str
    name: str
    age: int
    sex: Literal['M', 'F']
    mrn: str
    lastVisit: str
    status: Literal['Active', 'Inactive']
    conditions: List[str]
    medications: List[Medication]
    allergies: List[str]
    labs: List[LabResult]
    genomicProfile: Optional[GenomicProfile] = None
    clinicalNotes: Optional[str] = None

class DrugInfo(BaseModel):
    id: str
    name: str
    class_: str
    standardDose: str
    indications: List[str]

class SimulationResult(BaseModel):
    evaluationSummary: Dict[str, str]
    clinicalInterpretation: Dict[str, str]
    dosageEvaluation: List[str]
    riskInterpretation: Dict[str, str]
    clinicalConsiderations: List[str]

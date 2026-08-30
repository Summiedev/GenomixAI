const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '');
const TOKEN_KEY = 'genomixai_access_token';

export type ApiUser = { id: string; email: string; full_name: string; status: string };
export type ApiMembership = {
  id: string;
  organization: { id: string; name: string; slug: string; status: string };
  department: { id: string; name: string; slug: string; status: string } | null;
  role: string;
  status: string;
};
export type MeResponse = { user: ApiUser; membership: ApiMembership | null; memberships: ApiMembership[] };
export type PatientPage = { items: Array<Record<string, any>>; total: number; page: number; page_size: number };
export type Medication = { id: string; generic_name: string; brand_name?: string | null; strength?: string | null; dosage_form?: string | null };

export function getToken() { return localStorage.getItem(TOKEN_KEY); }
export function clearToken() { localStorage.removeItem(TOKEN_KEY); }

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set('Content-Type', 'application/json');
  const token = getToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (response.status === 401) {
    clearToken();
    window.dispatchEvent(new Event('genomixai:unauthorized'));
  }
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { const body = await response.json(); message = body.detail || message; } catch { /* non-JSON response */ }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function login(email: string, password: string) {
  const result = await request<{ access_token: string }>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
  localStorage.setItem(TOKEN_KEY, result.access_token);
  return result;
}
export const getMe = () => request<MeResponse>('/auth/me');
export async function logout() { try { await request<void>('/auth/logout', { method: 'POST' }); } finally { clearToken(); } }

export const listPatients = (organizationId: string, search = '') =>
  request<PatientPage>(`/patients?organization_id=${organizationId}&page=1&page_size=25${search ? `&search=${encodeURIComponent(search)}` : ''}`);
export const getPatient = (id: string, organizationId: string) => request<Record<string, any>>(`/patients/${id}?organization_id=${organizationId}`);
export const listMedications = (search = '') => request<Medication[]>(`/medications${search ? `?search=${encodeURIComponent(search)}` : ''}`);
export const listPatientMedications = (id: string, organizationId: string) => request<PatientPage>(`/patients/${id}/medications?organization_id=${organizationId}&page_size=100`);
export const listPatientTimeline = (id: string, organizationId: string) => request<PatientPage>(`/patients/${id}/timeline?organization_id=${organizationId}&page_size=100`);
export const getPatientGenomics = (id: string, organizationId: string) => request<PatientPage>(`/patients/${id}/genomics?organization_id=${organizationId}&page_size=100`);
export const listClinical = (id: string, organizationId: string, domain: string) => request<PatientPage>(`/patients/${id}/${domain}?organization_id=${organizationId}&page_size=100`);
export async function getPatientBundle(id: string, organizationId: string) {
  const [patient, encounters, conditions, notes, vitals, labs, allergies, adverseReactions, medications, timeline, genomics] = await Promise.all([
    getPatient(id, organizationId), listClinical(id, organizationId, 'encounters'), listClinical(id, organizationId, 'conditions'), listClinical(id, organizationId, 'notes'),
    listClinical(id, organizationId, 'vitals'), listClinical(id, organizationId, 'labs'), listClinical(id, organizationId, 'allergies'),
    listClinical(id, organizationId, 'adverse-reactions'), listPatientMedications(id, organizationId), listPatientTimeline(id, organizationId), getPatientGenomics(id, organizationId),
  ]);
  return { patient, encounters: encounters.items, conditions: conditions.items, notes: notes.items, vitals: vitals.items, labs: labs.items, allergies: allergies.items, adverseReactions: adverseReactions.items, medications: medications.items, timeline: timeline.items, genomics: genomics.items };
}

export const createAssessment = (patientId: string, organizationId: string, medications: any[]) =>
  request<any>(`/patients/${patientId}/medication-assessments?organization_id=${organizationId}`, { method: 'POST', body: JSON.stringify({ medications }) });
export const analyzeAssessment = (id: string, organizationId: string) => request<any>(`/assessments/${id}/analyze?organization_id=${organizationId}`, { method: 'POST' });
export const getAssessment = (id: string, organizationId: string) => request<any>(`/assessments/${id}?organization_id=${organizationId}`);
export const requestReview = (id: string, organizationId: string, physician_message: string) => request<any>(`/assessments/${id}/request-pharmacist-review?organization_id=${organizationId}`, { method: 'POST', body: JSON.stringify({ priority: 'HIGH', physician_message }) });
export const listReviews = (organizationId: string) => request<any[]>(`/pharmacist/reviews?organization_id=${organizationId}`);
export const startReview = (id: string, organizationId: string) => request<any>(`/pharmacist/reviews/${id}/start?organization_id=${organizationId}`, { method: 'POST' });
export const submitReview = (id: string, organizationId: string, body: any) => request<any>(`/pharmacist/reviews/${id}/submit?organization_id=${organizationId}`, { method: 'POST', body: JSON.stringify(body) });
export const recordDecision = (id: string, organizationId: string, body: any) => request<any>(`/assessments/${id}/final-decision?organization_id=${organizationId}`, { method: 'POST', body: JSON.stringify(body) });
export const createReport = (id: string, organizationId: string) => request<any>(`/assessments/${id}/reports?organization_id=${organizationId}`, { method: 'POST' });
export const listNotifications = (organizationId: string) => request<any[]>(`/notifications?organization_id=${organizationId}&page_size=25`);
export const readNotification = (id: string, organizationId: string) => request<any>(`/notifications/${id}/read?organization_id=${organizationId}`, { method: 'POST' });

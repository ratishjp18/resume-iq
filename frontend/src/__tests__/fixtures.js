export const analysisFixture = {
  id: 7, resume_id: 3, job_id: 4, resume_filename: 'sample_resume.pdf', job_title: 'Backend Engineer',
  company_name: 'Acme Corp', coverage_score: 50, semantic_similarity: 0.42, requirements_total: 4, requirements_matched: 2,
  matched_skills: [
    { skill_name: 'Python', status: 'matched', category: 'Programming Languages', requirement_type: 'skill', resume_evidence: 'Built REST APIs in Python for billing.', similarity_score: 0.61, evidence_strength: 'demonstrated', note: null },
    { skill_name: 'Docker', status: 'matched', category: 'DevOps', requirement_type: 'skill', resume_evidence: 'Skills: Docker, Git, SQL', similarity_score: 0.4, evidence_strength: 'listed', note: 'Mentioned only in a skills list' },
  ],
  uncertain_skills: [
    { skill_name: 'MySQL', status: 'uncertain', category: 'Databases', requirement_type: 'skill', resume_evidence: 'Designed PostgreSQL schemas.', similarity_score: 0.5, evidence_strength: null, note: 'Related databases experience found.' },
  ],
  not_evidenced_skills: [
    { skill_name: 'Kubernetes', status: 'not_evidenced', category: 'DevOps', requirement_type: 'skill', resume_evidence: null, similarity_score: 0.1, evidence_strength: null, note: null },
  ],
  recommendations: [
    { category: 'skill_gap', message: 'Kubernetes is not evidenced in your resume. Consider learning Kubernetes basics.' },
    { category: 'evidence', message: 'Docker appears only in a skills list.' },
  ],
  model_version: 'sentence-transformers/all-MiniLM-L6-v2 | matcher-v1', created_at: '2026-11-01T10:00:00Z',
}

export const historyFixture = {
  total: 2,
  items: [
    { id: 7, resume_id: 3, job_id: 4, resume_filename: 'sample_resume.pdf', job_title: 'Backend Engineer', company_name: 'Acme Corp', coverage_score: 50, semantic_similarity: 0.42, created_at: '2026-11-01T10:00:00Z' },
    { id: 8, resume_id: 3, job_id: 5, resume_filename: 'sample_resume.pdf', job_title: 'Data Engineer', company_name: null, coverage_score: 75, semantic_similarity: 0.55, created_at: '2026-11-02T10:00:00Z' },
  ],
}

# Phase 2: Medical Scenarios & Content

## Tasks

### 2.1 Scenario Data Structure
Each scenario JSON should contain:
```json
{
  "id": "cbc_blood_test",
  "title": "Complete Blood Count Results",
  "description": "Patient receives CBC with some out-of-range values",
  "patient_context": "Routine checkup, first time seeing lab results",
  "lab_data": { ... },
  "clinical_explanation_prompt": "...",
  "analogy_explanation_prompt": "...",
  "quiz_questions": [ ... ],
  "answer_key": [ ... ],
  "reference_sources": ["MedlinePlus URL", ...]
}
```

### 2.2 Scenario 1: CBC Blood Test
- Include realistic lab values (WBC, RBC, hemoglobin, hematocrit, platelets)
- 1-2 values out of range (e.g., low hemoglobin, high WBC)
- Quiz: Can the patient identify which values are abnormal? Do they understand what that means?
- Reference: MedlinePlus CBC page

### 2.3 Scenario 2: Pre-Diabetes Diagnosis
- HbA1c result in pre-diabetic range (5.7-6.4%)
- Fasting glucose also borderline
- Quiz: What does HbA1c measure? What lifestyle changes are recommended? When to follow up?
- Reference: ADA pre-diabetes guidelines

### 2.4 Scenario 3: Medication Instructions
- New prescription with:
  - Starting dose
  - Dose increase after 2 weeks if symptoms persist
  - Food/timing requirements
  - Side effects requiring doctor contact
- Quiz: What's the starting dose? When to increase? What side effects = call doctor?
- Reference: MedlinePlus drug info

### 2.5 Explanation Prompts (4 per scenario)
For each scenario, write system prompts for the Explainer that produce:
1. **Clinical-Static**: One-shot clinical explanation
2. **Clinical-Dialog**: Clinical language, but responsive to questions
3. **Analogy-Static**: One-shot analogy-enriched explanation
4. **Analogy-Dialog**: Analogy language, responsive to questions

### 2.6 Answer Keys
- Write detailed answer keys for the judge
- Include: correct answer, common misconceptions, partial credit criteria
- Each quiz: 5-6 questions mixing factual recall and applied reasoning

### 2.7 Validation
- Cross-check all medical content against MedlinePlus / clinical guidelines
- Have team members review for accuracy

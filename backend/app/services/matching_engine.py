from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from backend.app.models.resume import Resume, ResumeSkill
from backend.app.models.job import Job
from backend.app.models.match import JobMatch
from backend.app.models.profile import JobPreference
from backend.app.services.embedding_service import embedding_service


class MatchingEngineService:
    @classmethod
    def evaluate_fit(
        cls,
        resume: Resume,
        job: Job,
        preferences: JobPreference = None
    ) -> Dict[str, Any]:
        """Calculates multi-factor explainable match score between a Resume and a Job."""
        # 1. Extract CV skills & text
        cv_text = resume.raw_text or ""
        parsed = resume.parsed_json or {}
        cv_skills = {s.skill_name.lower().strip() for s in resume.skills}
        for s in parsed.get("skills", []):
            if isinstance(s, dict) and "skill_name" in s:
                cv_skills.add(s["skill_name"].lower().strip())
            elif isinstance(s, str):
                cv_skills.add(s.lower().strip())

        # 2. Extract Job required skills & requirements
        job_skills = [s.strip() for s in (job.required_skills or []) if s.strip()]
        job_skills_lower = [s.lower() for s in job_skills]

        # 3. Calculate skill overlap
        matched_skills = []
        missing_skills = []

        for original_skill, skill_lower in zip(job_skills, job_skills_lower):
            if skill_lower in cv_skills or any(skill_lower in s for s in cv_skills):
                matched_skills.append(original_skill)
            else:
                missing_skills.append(original_skill)

        if job_skills:
            skill_coverage = len(matched_skills) / len(job_skills)
        else:
            skill_coverage = 0.8  # If no explicit skills tagged, baseline neutral

        skill_coverage_score = round(skill_coverage * 100.0, 1)

        # 4. Semantic similarity via vector embeddings
        job_text = f"{job.title}\n{job.description}\n{' '.join(job.requirements or [])}"
        cv_vector = embedding_service.get_embedding(cv_text)
        job_vector = embedding_service.get_embedding(job_text)
        sim = embedding_service.cosine_similarity(cv_vector, job_vector)
        # Scaled to realistic 40%-95% range
        semantic_score = round((sim * 50.0) + 45.0, 1)

        # 5. Preference & Location modifier
        experience_fit_score = 90.0
        if preferences:
            # Check employment type fit
            if preferences.employment_type != "both" and job.employment_type:
                if preferences.employment_type.lower() != job.employment_type.lower():
                    experience_fit_score -= 15.0
            
            # Check remote fit
            if preferences.remote_preference == "remote" and not job.is_remote:
                experience_fit_score -= 10.0

        # 6. Overall Weighted Score: 40% skills, 40% semantic, 20% experience/pref fit
        overall_score = round(
            (skill_coverage_score * 0.45) +
            (semantic_score * 0.35) +
            (experience_fit_score * 0.20),
            1
        )
        overall_score = max(10.0, min(99.0, overall_score))

        # 7. Generate Explainability narrative
        reasons_for_fit = []
        if matched_skills:
            reasons_for_fit.append(f"Strong overlap on core required technologies: {', '.join(matched_skills[:4])}.")
        if job.is_remote:
            reasons_for_fit.append("Offers remote flexibility aligning with modern distributed roles.")
        if semantic_score > 70.0:
            reasons_for_fit.append("CV project and work history strongly match the engineering domain.")

        development_areas = []
        if missing_skills:
            development_areas.append(f"Missing mentions of: {', '.join(missing_skills[:3])}.")

        summary = (
            f"Overall match of {overall_score}%. "
            f"Candidate covers {len(matched_skills)} of {len(job_skills)} required competencies."
        )

        return {
            "overall_score": overall_score,
            "semantic_score": semantic_score,
            "skill_coverage_score": skill_coverage_score,
            "experience_fit_score": experience_fit_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "explanation": {
                "summary": summary,
                "reasons_for_fit": reasons_for_fit,
                "development_areas": development_areas,
                "skill_overlap_ratio": f"{len(matched_skills)}/{len(job_skills)}" if job_skills else "N/A"
            }
        }


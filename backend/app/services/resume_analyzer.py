import re
from typing import List, Set, Tuple

from app.data.skill_lexicon import ALL_CANONICAL_SKILLS, expand_skill_variants
from app.schemas.analysis import ResumeProfile, ResumeSkillEvidence
from app.services.text_utils import find_skill_mentions, normalize_text, split_sentences

EXPERIENCE_HEADERS = ("experience", "work history", "employment", "professional experience")
SKILLS_HEADERS = ("skills", "technical skills", "core competencies", "technologies")
EDUCATION_HEADERS = ("education", "academic")
CERT_HEADERS = ("certifications", "certificates", "licenses")
PROJECT_HEADERS = ("projects", "selected projects")


def _section_lines(text: str, headers: Tuple[str, ...]) -> List[str]:
    lines = [line.strip() for line in text.splitlines()]
    capture = False
    collected: List[str] = []
    for line in lines:
        lower = line.lower().strip(": ")
        if any(header in lower for header in headers) and len(line) < 60:
            capture = True
            continue
        if capture and line and any(
            other in lower
            for other in EXPERIENCE_HEADERS + SKILLS_HEADERS + EDUCATION_HEADERS + CERT_HEADERS + PROJECT_HEADERS
        ):
            if not any(header in lower for header in headers):
                break
        if capture and line:
            collected.append(line)
    return collected


def _bullet_items(lines: List[str]) -> List[str]:
    items: List[str] = []
    for line in lines:
        cleaned = re.sub(r"^[\-\*•\u2022]\s*", "", line).strip()
        if cleaned:
            items.append(cleaned)
    return items


def analyze_resume(resume_text: str) -> ResumeProfile:
    text = resume_text.strip()
    lower = text.lower()

    explicit_skills: Set[str] = set()
    demonstrated_skills: Set[str] = set()
    evidence: List[ResumeSkillEvidence] = []

    skills_section = _section_lines(text, SKILLS_HEADERS)
    skills_blob = " ".join(skills_section) if skills_section else ""
    for skill in ALL_CANONICAL_SKILLS:
        variants = list(expand_skill_variants(skill))
        mentions = find_skill_mentions(text, variants)
        if not mentions:
            continue
        in_skills_section = any(find_skill_mentions(skills_blob, variants)) if skills_blob else False
        mention_type = "explicit" if in_skills_section else "demonstrated"
        target = explicit_skills if mention_type == "explicit" else demonstrated_skills
        target.add(skill)
        for _, snippet in mentions[:2]:
            evidence.append(
                ResumeSkillEvidence(skill=skill, mention_type=mention_type, evidence=snippet),
            )

    experience_lines = _bullet_items(_section_lines(text, EXPERIENCE_HEADERS))
    project_lines = _bullet_items(_section_lines(text, PROJECT_HEADERS))
    responsibilities = experience_lines[:12]
    achievements = [line for line in experience_lines if re.search(r"\d|%|\$", line)][:8]

    education = _bullet_items(_section_lines(text, EDUCATION_HEADERS))
    if not education and ("bachelor" in lower or "master" in lower):
        education = [sentence for sentence in split_sentences(text) if "degree" in sentence.lower()][:3]

    certifications = _bullet_items(_section_lines(text, CERT_HEADERS))
    cert_pattern = re.compile(r"\b(AWS|Azure|GCP|PMP|CKA|CKAD|CISSP|CompTIA)[^\n,.;]{0,40}", re.I)
    if not certifications:
        certifications = [match.group(0).strip() for match in cert_pattern.finditer(text)][:5]

    return ResumeProfile(
        explicit_skills=sorted(explicit_skills),
        demonstrated_skills=sorted(demonstrated_skills - explicit_skills),
        achievements=achievements,
        responsibilities=responsibilities,
        education=education,
        certifications=certifications,
        skill_evidence=evidence,
    )

import re
import uuid
from typing import Dict, List, Optional, Set, Tuple

from app.data.skill_lexicon import ALL_CANONICAL_SKILLS, canonicalize_skill, expand_skill_variants
from app.schemas.analysis import (
    ExtractedRequirement,
    RequirementCategory,
    RequirementImportance,
    StructuredRequirements,
)
from app.services.text_utils import normalize_text, split_sentences

SECTION_HINTS: Dict[RequirementCategory, Tuple[str, ...]] = {
    RequirementCategory.REQUIRED_TECHNICAL: (
        "requirements",
        "required qualifications",
        "must have",
        "minimum qualifications",
        "what you'll need",
    ),
    RequirementCategory.PREFERRED: (
        "preferred",
        "nice to have",
        "bonus",
        "pluses",
    ),
    RequirementCategory.TOOLS_FRAMEWORKS: (
        "tech stack",
        "tools",
        "technologies",
        "frameworks",
    ),
    RequirementCategory.EXPERIENCE: (
        "responsibilities",
        "what you'll do",
        "you will",
        "experience",
        "role",
    ),
    RequirementCategory.EDUCATION: (
        "education",
        "degree",
        "certification",
        "certifications",
    ),
    RequirementCategory.DOMAIN_SOFT: (
        "about you",
        "soft skills",
        "domain",
        "who you are",
    ),
}

IMPORTANCE_BY_SECTION: Dict[RequirementCategory, RequirementImportance] = {
    RequirementCategory.REQUIRED_TECHNICAL: RequirementImportance.REQUIRED,
    RequirementCategory.PREFERRED: RequirementImportance.PREFERRED,
    RequirementCategory.TOOLS_FRAMEWORKS: RequirementImportance.REQUIRED,
    RequirementCategory.EXPERIENCE: RequirementImportance.REQUIRED,
    RequirementCategory.EDUCATION: RequirementImportance.PREFERRED,
    RequirementCategory.DOMAIN_SOFT: RequirementImportance.PREFERRED,
}

REQUIRED_MARKERS = ("must", "required", "minimum", "need to have")
PREFERRED_MARKERS = ("preferred", "nice to have", "bonus", "plus")


def _detect_section(line: str) -> Optional[RequirementCategory]:
    lower = line.lower().strip(": ")
    for category, hints in SECTION_HINTS.items():
        if any(hint in lower for hint in hints):
            return category
    return None


def _importance_from_text(text: str, default: RequirementImportance) -> RequirementImportance:
    lower = text.lower()
    if any(marker in lower for marker in REQUIRED_MARKERS):
        return RequirementImportance.REQUIRED
    if any(marker in lower for marker in PREFERRED_MARKERS):
        return RequirementImportance.PREFERRED
    return default


def _skills_in_text(text: str) -> List[str]:
    lower = text.lower()
    found: List[str] = []
    for skill in sorted(ALL_CANONICAL_SKILLS, key=len, reverse=True):
        variants = expand_skill_variants(skill)
        for variant in variants:
            pattern = re.compile(rf"(?<![a-z0-9]){re.escape(variant)}(?![a-z0-9])")
            if pattern.search(lower):
                canonical = canonicalize_skill(skill)
                if canonical not in found:
                    found.append(canonical)
                break
    return found


def _category_for_skill(skill: str, section: RequirementCategory) -> RequirementCategory:
    soft = {"communication", "leadership", "problem solving", "agile"}
    if skill in soft:
        return RequirementCategory.DOMAIN_SOFT
    tools = {
        "docker",
        "kubernetes",
        "git",
        "terraform",
        "jenkins",
        "jira",
        "figma",
        "nginx",
        "helm",
        "prometheus",
        "grafana",
    }
    if skill in tools or section == RequirementCategory.TOOLS_FRAMEWORKS:
        return RequirementCategory.TOOLS_FRAMEWORKS
    if section == RequirementCategory.PREFERRED:
        return RequirementCategory.PREFERRED
    return RequirementCategory.REQUIRED_TECHNICAL


def _make_requirement(
    label: str,
    category: RequirementCategory,
    importance: RequirementImportance,
    source_text: str,
) -> ExtractedRequirement:
    return ExtractedRequirement(
        id=str(uuid.uuid4()),
        label=label,
        category=category,
        importance=importance,
        source_text=source_text,
    )


def extract_requirements(job_description: str) -> StructuredRequirements:
    lines = [line.strip() for line in job_description.splitlines() if line.strip()]
    current_section = RequirementCategory.EXPERIENCE
    items: List[ExtractedRequirement] = []
    seen_labels: Set[str] = set()

    def add_item(label: str, category: RequirementCategory, importance: RequirementImportance, source: str) -> None:
        normalized_label = normalize_text(label)
        key = normalized_label.lower()
        if not normalized_label or key in seen_labels:
            return
        seen_labels.add(key)
        items.append(_make_requirement(normalized_label, category, importance, source))

    for line in lines:
        section = _detect_section(line)
        if section is not None and len(line) < 80:
            current_section = section
            continue

        source = line
        bullet = re.sub(r"^[\-\*•\u2022]\s*", "", line).strip()
        text = bullet if bullet else line
        importance = _importance_from_text(text, IMPORTANCE_BY_SECTION[current_section])

        skills = _skills_in_text(text)
        if skills:
            for skill in skills:
                category = _category_for_skill(skill, current_section)
                add_item(skill, category, importance, source)
            continue

        if current_section == RequirementCategory.EDUCATION and any(
            token in text.lower() for token in ("bachelor", "master", "degree", "certified", "certification")
        ):
            add_item(text, RequirementCategory.EDUCATION, importance, source)
            continue

        if current_section in {RequirementCategory.EXPERIENCE, RequirementCategory.DOMAIN_SOFT}:
            if len(text) >= 20:
                add_item(text, current_section, importance, source)

    # Global pass for skills mentioned anywhere if not captured yet.
    for sentence in split_sentences(job_description):
        for skill in _skills_in_text(sentence):
            add_item(
                skill,
                _category_for_skill(skill, RequirementCategory.REQUIRED_TECHNICAL),
                _importance_from_text(sentence, RequirementImportance.REQUIRED),
                sentence,
            )

    if not items:
        add_item(
            "General role alignment with posted responsibilities",
            RequirementCategory.EXPERIENCE,
            RequirementImportance.REQUIRED,
            normalize_text(job_description[:240]),
        )

    return StructuredRequirements(items=items)

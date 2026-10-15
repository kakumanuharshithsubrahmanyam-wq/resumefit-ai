from typing import Dict, FrozenSet, List, Set

# Canonical skill -> known aliases (lowercase). Aliases must not cross unrelated technologies.
SKILL_ALIASES: Dict[str, List[str]] = {
    "python": ["python3", "py"],
    "javascript": ["js", "ecmascript"],
    "typescript": ["ts"],
    "react": ["react.js", "reactjs"],
    "node.js": ["node", "nodejs", "node js"],
    "fastapi": ["fast api"],
    "django": [],
    "flask": [],
    "sql": ["structured query language"],
    "postgresql": ["postgres", "psql"],
    "mysql": [],
    "mongodb": ["mongo"],
    "redis": [],
    "docker": ["containerization", "containers"],
    "kubernetes": ["k8s"],
    "aws": ["amazon web services"],
    "azure": ["microsoft azure"],
    "gcp": ["google cloud", "google cloud platform"],
    "git": [],
    "ci/cd": ["cicd", "continuous integration", "continuous delivery"],
    "rest": ["restful", "rest api", "rest apis"],
    "graphql": [],
    "pytest": [],
    "machine learning": ["ml"],
    "deep learning": ["dl"],
    "scikit-learn": ["sklearn", "scikit learn"],
    "pandas": [],
    "numpy": [],
    "tensorflow": [],
    "pytorch": [],
    "java": [],
    "c++": ["cpp", "c plus plus"],
    "c#": ["csharp", "c sharp"],
    "go": ["golang"],
    "rust": [],
    "html": [],
    "css": [],
    "tailwind css": ["tailwind"],
    "linux": [],
    "agile": ["scrum", "kanban"],
    "communication": ["written communication", "verbal communication"],
    "leadership": ["team leadership"],
    "problem solving": ["problem-solving"],
    "microservices": ["micro services"],
    "sqlalchemy": [],
    "vite": [],
    "terraform": [],
    "kafka": ["apache kafka"],
    "spark": ["apache spark"],
    "snowflake": [],
    "dbt": [],
    "tableau": [],
    "power bi": ["powerbi"],
    "selenium": [],
    "playwright": [],
    "figma": [],
    "jira": [],
    "openapi": ["swagger"],
    "oauth": ["oauth2", "oauth 2.0"],
    "jwt": [],
    "elasticsearch": ["elastic search"],
    "nginx": [],
    "helm": [],
    "prometheus": [],
    "grafana": [],
    "llm": ["large language models", "large language model"],
    "rag": ["retrieval augmented generation"],
}

ALL_CANONICAL_SKILLS: FrozenSet[str] = frozenset(SKILL_ALIASES.keys())

_ALIAS_TO_CANONICAL: Dict[str, str] = {}
for canonical, aliases in SKILL_ALIASES.items():
    _ALIAS_TO_CANONICAL[canonical] = canonical
    for alias in aliases:
        _ALIAS_TO_CANONICAL[alias.lower()] = canonical


def canonicalize_skill(token: str) -> str:
    normalized = token.strip().lower()
    return _ALIAS_TO_CANONICAL.get(normalized, normalized)


def expand_skill_variants(skill: str) -> Set[str]:
    canonical = canonicalize_skill(skill)
    variants: Set[str] = {canonical}
    for alias in SKILL_ALIASES.get(canonical, []):
        variants.add(alias.lower())
    if canonical in SKILL_ALIASES:
        variants.add(canonical)
    return variants

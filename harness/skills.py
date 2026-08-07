from config import SKILLS_DIR, TEXT_ENCODING
from utils import parse_frontmatter, log


SKILL_REGISTRY = {}


def _scan_skills():
    if not SKILLS_DIR.exists():
        return
    for dir in sorted(SKILLS_DIR.iterdir()):
        if not dir.is_dir():
            continue
        manifest = dir / "SKILL.md"
        if not manifest.exists():
            continue
        raw = manifest.read_text(encoding=TEXT_ENCODING, errors="replace")
        meta, _body = parse_frontmatter(raw)
        name = meta.get("name", dir.name)
        _title = raw.split("\n")[0].lstrip("#").strip()
        when_to_use = meta.get("when_to_use", "")
        description = meta.get("description", _title) + when_to_use
        SKILL_REGISTRY[name] = {
            "name": name,
            "description": description,
            "content": raw,
        }


_scan_skills()


def run_load_skill(name: str):
    skill = SKILL_REGISTRY.get(name)
    if not skill:
        return f"Skill not found: {name}"
    log.info(f"[🪄 SKILL] loaded {name}")
    return skill["content"]

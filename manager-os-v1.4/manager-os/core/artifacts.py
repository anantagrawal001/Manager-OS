"""Create inspectable project files from a model response; never execute generated code."""
import json
from pathlib import Path, PurePosixPath
import re
import uuid
import zipfile


def save_project(raw, root='outputs'):
    cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw.strip())
    data = json.loads(cleaned)
    files = data.get('files')
    if not isinstance(files, list) or not 1 <= len(files) <= 30:
        raise ValueError('Project must contain 1–30 files')
    validated = []
    names = set()
    for item in files:
        name = item.get('path', '').replace('\\', '/')
        content = item.get('content')
        path = PurePosixPath(name)
        if not name or path.is_absolute() or '..' in path.parts or ':' in name or name.casefold() in names:
            raise ValueError('Invalid or duplicate artifact path')
        if not isinstance(content, str) or len(content) > 200000:
            raise ValueError('Invalid file content')
        if any(part.rstrip(' .') != part or part.upper().split('.')[0] in {'CON','NUL','AUX','PRN','COM1','LPT1'} for part in path.parts):
            raise ValueError('Unsupported filename')
        names.add(name.casefold())
        validated.append((name, content))
    target = Path(root).resolve()/f'project-{uuid.uuid4().hex[:10]}'
    target.mkdir(parents=True)
    for name, content in validated:
        path = target/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    archive = target.with_suffix('.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as zip_file:
        for name, _ in validated:
            zip_file.write(target/name, name)
    return target, archive

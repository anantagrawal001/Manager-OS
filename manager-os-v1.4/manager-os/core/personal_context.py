"""Bounded local evidence discovery. Documents are data, never instructions."""
from pathlib import Path
import os
import re
import sqlite3
import time
import zipfile
from xml.etree import ElementTree as ET

SKIP = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', 'backups',
        'logs', 'security', 'releases', 'outputs', 'appdata'}
PATTERN = re.compile(r'resume|résumé|curriculum|(?:^|[ _-])cv(?:[ _.-]|$)|portfolio|biodata', re.I)


def read_document(path):
    path = Path(path)
    if path.stat().st_size > 8_000_000:
        raise ValueError('Document exceeds 8 MB limit')
    suffix = path.suffix.lower()
    if suffix == '.docx':
        with zipfile.ZipFile(path) as archive:
            member = archive.getinfo('word/document.xml')
            if member.file_size > 12_000_000:
                raise ValueError('Expanded document is too large')
            root = ET.fromstring(archive.read(member))
        ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        # Read leaf text runs once: outer text boxes otherwise duplicate entire resumes.
        lines = []
        for paragraph in root.iter(ns + 'p'):
            texts = [t.text or '' for t in paragraph.iter(ns + 't')]
            if any(child.tag == ns + 'p' for child in list(paragraph.iter())[1:]):
                continue
            line = ''.join(texts).strip()
            if line and line not in lines:
                lines.append(line)
        return '\n'.join(lines)[:30000]
    if suffix == '.pdf':
        from pypdf import PdfReader
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise ValueError('Encrypted PDF')
        return '\n'.join(page.extract_text() or '' for page in reader.pages[:12])[:30000]
    if suffix in {'.txt', '.md'}:
        return path.read_text(encoding='utf-8', errors='replace')[:30000]
    raise ValueError('Unsupported document type')


def discover(config):
    opts = config.get('personal_context', {})
    roots = [Path(p).expanduser().resolve() for p in opts.get('roots', [])]
    owner = config.get('manager', {}).get('owner', '').strip()
    matches, ignored, errors = [], [], []
    candidates = []
    visited = set()
    count = 0
    deadline = time.monotonic() + 12
    for root in roots:
        if not root.is_dir():
            continue
        for base, dirs, files in os.walk(root, followlinks=False):
            if time.monotonic() > deadline or count > 30000:
                break
            directory = Path(base)
            dirs[:] = [d for d in dirs if d.lower() not in SKIP and not d.startswith('.')
                       and not (directory / d).is_symlink()
                       and (directory / d).resolve().is_relative_to(root)]
            if len(directory.relative_to(root).parts) >= 5:
                dirs[:] = []
            for name in files:
                count += 1
                path = directory / name
                if not PATTERN.search(name) or path.suffix.lower() not in {'.pdf', '.docx', '.txt', '.md'}:
                    continue
                try:
                    resolved = path.resolve()
                    if path.is_symlink() or not resolved.is_relative_to(root) or resolved in visited:
                        continue
                    visited.add(resolved)
                    candidates.append((path.stat().st_mtime, path))
                except OSError:
                    continue
    for modified, path in sorted(candidates, reverse=True)[:30]:
        try:
            text = read_document(path)
            # Only accept the owner's name near the document's contact/name header.
            if not owner or not re.search(r'\b' + re.escape(owner) + r'\b', text[:1200], re.I):
                ignored.append(path.name)
                continue
            if len(text.strip()) < 80:
                raise ValueError('No readable text; scanned PDF may need OCR')
            matches.append({'path': str(path), 'modified': modified, 'text': text})
        except Exception as exc:
            errors.append({'file': path.name, 'reason': type(exc).__name__})
    # Prefer the newest matching source, keeping others as provenance/conflict evidence.
    return {'documents': matches[:6], 'other_people_or_unmatched': ignored,
            'unreadable': errors, 'roots': [str(p) for p in roots],
            'bounded_scan': count > 30000 or time.monotonic() > deadline}


def user_history(config, recent):
    """Only user statements count as facts; never recycle AI-generated achievements."""
    messages = [m['content'] for m in recent if m.get('role') == 'user']
    path = Path(config.get('conversation', {}).get('store_path', './logs/conversations.db')).resolve()
    if path.exists():
        try:
            connection = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
            try:
                rows = connection.execute("SELECT content FROM conversations WHERE role='user' ORDER BY id DESC LIMIT 500").fetchall()
                messages.extend(row[0] for row in rows)
            finally:
                connection.close()
        except sqlite3.Error:
            pass
    relevant = []
    for text in messages:
        if re.search(r'\b(my|i|worked|experience|graduat|degree|wipro|skill|resume|cv|education|project)\b', text, re.I):
            if text not in relevant:
                relevant.append(text[:2000])
    return relevant[:30]

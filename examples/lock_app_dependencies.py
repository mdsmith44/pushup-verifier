"""Snapshot the installed app dependency closure for this OS/Python version."""
from importlib.metadata import distribution
from pathlib import Path
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

roots=['mediapipe','opencv-python','fastapi','uvicorn','matplotlib','imageio-ffmpeg','httpx']
seen={}
todo=roots[:]
while todo:
    name=canonicalize_name(todo.pop())
    if name in seen:
        continue
    package=distribution(name)
    seen[name]=package.version
    for text in package.requires or []:
        requirement=Requirement(text)
        if requirement.marker is None or requirement.marker.evaluate({'extra':''}):
            todo.append(requirement.name)
path=Path(__file__).resolve().parents[1]/'requirements-app.lock.txt'
path.write_text('# Tested Linux / Python 3.12 dependency snapshot. Regenerate intentionally.\n'+'\n'.join(f'{name}=={seen[name]}' for name in sorted(seen))+'\n')
print(f'Locked {len(seen)} distributions')

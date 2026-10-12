"""Ajoute une vidéo dans la file : python tools/enqueue.py <video.mp4> <post.json>
Le dossier queue/<id>/ est créé avec video.mp4 + post.json (id = date + nom court)."""
import json, shutil, sys
from pathlib import Path
video, spec = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
pid = f"{spec['publish_at'][:10]}_{spec['slug']}"
d = Path(__file__).resolve().parent.parent / "queue" / pid
d.mkdir(parents=True, exist_ok=True)
shutil.copy(video, d / "video.mp4")
(d / "post.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
print("ajouté :", d.relative_to(d.parent.parent))

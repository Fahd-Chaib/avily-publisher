"""AVILY publisher — publishes queued videos to Instagram (Reels), YouTube (Shorts)
and sends them to TikTok (inbox draft) when their time has come.

Queue layout:
  queue/<post-id>/video.mp4
  queue/<post-id>/post.json   (see README for the format)

Each run:
  * YouTube: uploads any post not yet sent, as private + publishAt (YouTube publishes it itself).
  * Instagram: publishes posts whose publish_at is due (needs the video reachable on GitHub Pages).
  * TikTok: sends due posts to the TikTok inbox as drafts (unaudited API), if TikTok secrets exist.
  * Writes the result of every platform back into post.json; once everything is done,
    moves post.json to archive/ and deletes the video.

Secrets are read from environment variables only. Nothing secret is ever printed.
"""
import datetime as dt
import json
import math
import os
import shutil
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "queue"
ARCHIVE = ROOT / "archive"
PAGES_BASE = os.environ.get("PAGES_BASE", "").rstrip("/")  # e.g. https://fahd-chaib.github.io/avily-publisher
NOW = dt.datetime.now(dt.timezone.utc)
DRY = os.environ.get("DRY_RUN") == "1"
NEW_SECRETS = {}  # rotated tokens to save back as repo secrets


def log(*a):
    print(*a, flush=True)


def parse_time(s, tz="Africa/Casablanca"):
    """publish_at is local time in `tz` (default Morocco) unless it carries its own offset."""
    from zoneinfo import ZoneInfo
    t = dt.datetime.fromisoformat(s)
    if t.tzinfo is None:
        t = t.replace(tzinfo=ZoneInfo(tz))
    return t.astimezone(dt.timezone.utc)


# ---------------------------------------------------------------- YouTube
def yt_token():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"],
        "grant_type": "refresh_token"}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def youtube(post, video, when):
    y = post["youtube"]
    status = {"privacyStatus": "private", "selfDeclaredMadeForKids": False,
              "containsSyntheticMedia": True}  # AI-generated scenery: disclosed
    if when > NOW + dt.timedelta(minutes=20):
        status["publishAt"] = when.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        status["privacyStatus"] = "public"
    meta = {"snippet": {"title": y["title"][:100], "description": y["description"],
                        "tags": y.get("tags", []), "categoryId": y.get("category_id", "26"),
                        "defaultLanguage": "fr"},
            "status": status}
    if DRY:
        log("  [dry] youtube", json.dumps(meta, ensure_ascii=False)[:200]); return {"state": "dry"}
    tok = yt_token()
    init = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(video.stat().st_size)},
        data=json.dumps(meta), timeout=60)
    init.raise_for_status()
    up = requests.put(init.headers["Location"], data=video.read_bytes(),
                      headers={"Content-Type": "video/mp4"}, timeout=600)
    up.raise_for_status()
    vid = up.json()["id"]
    return {"state": "scheduled" if "publishAt" in status else "published",
            "id": vid, "url": f"https://youtube.com/shorts/{vid}"}


# ---------------------------------------------------------------- Instagram (Instagram Login API)
IG = "https://graph.instagram.com"


def ig_refresh():
    """Long-lived tokens last 60 days; refresh on every run (allowed once older than 24 h)."""
    tok = os.environ["IG_ACCESS_TOKEN"]
    r = requests.get(f"{IG}/refresh_access_token",
                     params={"grant_type": "ig_refresh_token", "access_token": tok}, timeout=30)
    if r.ok and r.json().get("access_token") and r.json()["access_token"] != tok:
        NEW_SECRETS["IG_ACCESS_TOKEN"] = r.json()["access_token"]
        return r.json()["access_token"]
    return tok


def instagram(post, pid):
    url = f"{PAGES_BASE}/queue/{pid}/video.mp4"
    cap = post["instagram"]["caption"]
    if DRY:
        log("  [dry] instagram", url); return {"state": "dry"}
    tok = ig_refresh()
    uid = os.environ["IG_USER_ID"]
    head = requests.head(url, timeout=30, allow_redirects=True)
    if head.status_code != 200:
        return {"state": "waiting", "note": f"video not yet on Pages ({head.status_code})"}
    c = requests.post(f"{IG}/{uid}/media", data={
        "media_type": "REELS", "video_url": url, "caption": cap, "share_to_feed": "true",
        "access_token": tok}, timeout=60)
    if not c.ok:
        return {"state": "error", "note": c.text[:300]}
    cid = c.json()["id"]
    for _ in range(40):  # up to ~10 min of processing
        s = requests.get(f"{IG}/{cid}", params={"fields": "status_code,status", "access_token": tok}, timeout=30).json()
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") == "ERROR":
            return {"state": "error", "note": str(s)[:300]}
        time.sleep(15)
    else:
        return {"state": "error", "note": "processing timeout"}
    p = requests.post(f"{IG}/{uid}/media_publish", data={"creation_id": cid, "access_token": tok}, timeout=60)
    if not p.ok:
        return {"state": "error", "note": p.text[:300]}
    return {"state": "published", "id": p.json()["id"]}


# ---------------------------------------------------------------- TikTok (inbox draft, unaudited)
TT = "https://open.tiktokapis.com/v2"


def tt_token():
    r = requests.post(f"{TT}/oauth/token/", data={
        "client_key": os.environ["TT_CLIENT_KEY"], "client_secret": os.environ["TT_CLIENT_SECRET"],
        "grant_type": "refresh_token", "refresh_token": os.environ["TT_REFRESH_TOKEN"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=30)
    r.raise_for_status()
    j = r.json()
    if j.get("refresh_token") and j["refresh_token"] != os.environ["TT_REFRESH_TOKEN"]:
        NEW_SECRETS["TT_REFRESH_TOKEN"] = j["refresh_token"]
    return j["access_token"]


def tiktok(post, video):
    if DRY:
        log("  [dry] tiktok draft"); return {"state": "dry"}
    tok = tt_token()
    size = video.stat().st_size
    chunk = size if size <= 64 * 1024 * 1024 else 10 * 1024 * 1024
    n = math.ceil(size / chunk)
    init = requests.post(f"{TT}/post/publish/inbox/video/init/",
                         headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"},
                         json={"source_info": {"source": "FILE_UPLOAD", "video_size": size,
                                               "chunk_size": chunk, "total_chunk_count": n}}, timeout=60)
    if not init.ok:
        return {"state": "error", "note": init.text[:300]}
    up_url = init.json()["data"]["upload_url"]
    data = video.read_bytes()
    for i in range(n):
        a, b = i * chunk, min(size, (i + 1) * chunk) - 1
        r = requests.put(up_url, data=data[a:b + 1], headers={
            "Content-Type": "video/mp4", "Content-Range": f"bytes {a}-{b}/{size}"}, timeout=600)
        if r.status_code not in (200, 201, 206):
            return {"state": "error", "note": f"chunk {i}: {r.status_code}"}
    return {"state": "draft_sent", "note": "ouvre TikTok > notifications/boîte de réception pour finaliser"}


# ---------------------------------------------------------------- main loop
def enabled(name):
    need = {"youtube": ["YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"],
            "instagram": ["IG_ACCESS_TOKEN", "IG_USER_ID"],
            "tiktok": ["TT_CLIENT_KEY", "TT_CLIENT_SECRET", "TT_REFRESH_TOKEN"]}[name]
    return DRY or all(os.environ.get(k) for k in need)


def main():
    changed = False
    for d in sorted(p for p in QUEUE.iterdir() if p.is_dir()) if QUEUE.exists() else []:
        pj, video = d / "post.json", d / "video.mp4"
        if not pj.exists() or not video.exists():
            continue
        post = json.loads(pj.read_text(encoding="utf-8"))
        when = parse_time(post["publish_at"], post.get("timezone", "Africa/Casablanca"))
        res = post.setdefault("results", {})
        log(f"- {d.name} (publish_at {when.isoformat()})")
        for plat in post.get("platforms", []):
            prev = res.get(plat, {}).get("state")
            if prev in ("published", "scheduled", "draft_sent", "dry"):
                continue
            if not enabled(plat):
                res[plat] = {"state": "skipped", "note": "secrets manquants"}; continue
            due = when <= NOW
            if when < NOW - dt.timedelta(hours=6) and plat != "tiktok":
                res[plat] = {"state": "skipped", "note": "trop en retard (> 6 h), non publié", "at": NOW.isoformat()}
                changed = True
                continue
            # YouTube schedules natively: send as soon as possible. Others: only when due.
            if plat != "youtube" and not due:
                continue
            if plat == "tiktok" and when < NOW - dt.timedelta(hours=6):
                pass  # late but still useful as a draft
            try:
                fn = {"youtube": lambda: youtube(post, video, when),
                      "instagram": lambda: instagram(post, d.name),
                      "tiktok": lambda: tiktok(post, video)}[plat]
                res[plat] = {**fn(), "at": NOW.isoformat()}
            except requests.HTTPError as e:
                res[plat] = {"state": "error", "note": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                             "at": NOW.isoformat()}
            except Exception as e:  # keep going with the other posts
                res[plat] = {"state": "error", "note": repr(e)[:200], "at": NOW.isoformat()}
            log(f"  {plat}: {res[plat]['state']} {res[plat].get('note', '')}")
            changed = True
        pj.write_text(json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8")
        done = all(res.get(p, {}).get("state") in ("published", "scheduled", "draft_sent", "skipped")
                   for p in post.get("platforms", []))
        if done and when <= NOW - dt.timedelta(hours=2) and not DRY:
            ARCHIVE.mkdir(exist_ok=True)
            shutil.move(str(pj), ARCHIVE / f"{d.name}.json")
            shutil.rmtree(d)
            log(f"  archived {d.name}")
            changed = True
    if NEW_SECRETS:
        Path(os.environ.get("NEW_SECRETS_FILE", "/tmp/new_secrets.json")).write_text(json.dumps(NEW_SECRETS))
    return changed


if __name__ == "__main__":
    main()
    errors = [p for p in QUEUE.glob("*/post.json")
              if any(v.get("state") == "error" for v in json.loads(p.read_text()).get("results", {}).values())]
    sys.exit(1 if errors else 0)

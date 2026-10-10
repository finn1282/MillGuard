"""All mutable state (live session, readings buffer, sensor issues, notify ids, subscribers, feedback, advice cache) lives here.

Backends, chosen by environment:
  Upstash Redis REST   KV_REST_API_URL + KV_REST_API_TOKEN (Vercel)
  Redis                REDIS_URL (redis-py)
  file                 MILLGUARD_STATE_FILE: a JSON file, so the API and the polling bot can share state locally (`make live`)
  memory               default (one process)
Values are JSON. Lists and sets are small and capped by callers.
"""
import json
import os
from pathlib import Path

import httpx

PREFIX = "mg:"


class Memory:
    def __init__(self, path=None):
        self.path, self.d = (Path(path) if path else None), {}

    def _load(self):
        if self.path is not None:
            try:
                self.d = json.loads(self.path.read_text())
            except (OSError, ValueError):
                self.d = {}

    def _save(self):
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.d))

    def get(self, key):
        self._load()
        return self.d.get(key)

    def set(self, key, value, ex=None):
        self._load(); self.d[key] = value; self._save()

    def delete(self, key):
        self._load(); self.d.pop(key, None); self._save()

    def push(self, key, item, keep=None):
        self._load()
        lst = self.d.setdefault(key, []); lst.append(item)
        if keep:
            del lst[:-keep]
        self._save()

    def items(self, key):
        self._load()
        return list(self.d.get(key, []))

    def add(self, key, member):
        """-> True if the member is new."""
        self._load()
        lst = self.d.setdefault(key, [])
        if member in lst:
            return False
        lst.append(member); self._save()
        return True

    def members(self, key):
        return self.items(key)


class Redis:
    """Upstash REST (httpx) or redis-py; values are JSON strings."""

    def __init__(self, url=None, token=None, redis_url=None):
        self.url, self.token = url, token
        self.r = None
        if redis_url:
            import redis
            self.r = redis.Redis.from_url(redis_url, decode_responses=True)

    def _cmd(self, *args):
        if self.r is not None:
            return self.r.execute_command(*args)
        resp = httpx.post(self.url, headers={"Authorization": f"Bearer {self.token}"}, json=[str(a) for a in args], timeout=10)
        resp.raise_for_status()
        return resp.json().get("result")

    def get(self, key):
        v = self._cmd("GET", PREFIX + key)
        return None if v is None else json.loads(v)

    def set(self, key, value, ex=None):
        self._cmd("SET", PREFIX + key, json.dumps(value), *(["EX", ex] if ex else []))

    def delete(self, key):
        self._cmd("DEL", PREFIX + key)

    def push(self, key, item, keep=None):
        self._cmd("RPUSH", PREFIX + key, json.dumps(item))
        if keep:
            self._cmd("LTRIM", PREFIX + key, -keep, -1)

    def items(self, key):
        return [json.loads(x) for x in self._cmd("LRANGE", PREFIX + key, 0, -1) or []]

    def add(self, key, member):
        return bool(self._cmd("SADD", PREFIX + key, json.dumps(member)))

    def members(self, key):
        return [json.loads(x) for x in self._cmd("SMEMBERS", PREFIX + key) or []]


_backend = None


def make_backend():
    env = os.environ
    if env.get("KV_REST_API_URL") and env.get("KV_REST_API_TOKEN"):
        return Redis(url=env["KV_REST_API_URL"], token=env["KV_REST_API_TOKEN"])
    if env.get("REDIS_URL"):
        return Redis(redis_url=env["REDIS_URL"])
    return Memory(env.get("MILLGUARD_STATE_FILE"))


def db():
    global _backend
    if _backend is None:
        _backend = make_backend()
    return _backend


def use(backend):
    """Swap the backend (tests)."""
    global _backend
    _backend = backend

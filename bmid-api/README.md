# BMID API v0.1
## Behavioral Manipulation Intelligence Database
### Hoffman Lenses Initiative -- hoffmanlenses.org

The fisherman's record. An open intelligence database documenting
who uses behavioral manipulation online, how they do it, where they
lead the people they catch, and what harm has resulted.

---

## Running locally

```bash
pip install flask flask-cors
python app.py
```

API available at http://localhost:5000

---

## Key endpoints

```
GET  /api/v1/health
GET  /api/v1/fisherman/{domain}
GET  /api/v1/fisherman/{domain}/bait
GET  /api/v1/explain?domain=&patterns=&headline=
GET  /api/v1/pattern/{pattern_type}
GET  /api/v1/search?domain=&pattern=&harm_type=
POST /api/v1/fisherman
POST /api/v1/session
```

---

## The analogy

FISHERMAN -- who is doing this (publisher identity)
BAIT      -- what they use (the manipulative content)
HOOK      -- the specific technique (hl-detect pattern instance)
NET       -- where they lead you (destination ecosystem)
CATCH     -- documented harm (evidence-based harm records)
MOTIVE    -- why they do it (documented business model)
EVIDENCE  -- proof (primary source citations)

---

## License

MIT -- Hoffman Lenses Initiative

"""
BMID API — Behavioral Manipulation Intelligence Database
Version: 0.2.0
Stack: Python / Flask / SQLite (via sqlite3)
"""

import os
import uuid
import sqlite3
import json
from flask import Flask, jsonify, request, g, render_template

app = Flask(__name__)

# Local dev: bmid.db next to app.py
# Production (Fly.io): /data/bmid.db on a persistent volume
DATABASE = os.environ.get('BMID_DATABASE', os.path.join(os.path.dirname(__file__), 'bmid.db'))
SCHEMA   = os.path.join(os.path.dirname(__file__), 'schema.sql')


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Create all tables from schema.sql (idempotent — CREATE TABLE IF NOT EXISTS)."""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA, 'r') as f:
        db.executescript(f.read())
    db.commit()
    db.close()


def row_to_dict(row):
    return dict(row) if row else None


def rows_to_list(rows):
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Application startup
# ---------------------------------------------------------------------------

with app.app_context():
    init_db()


# ===========================================================================
# CORE API ENDPOINTS  (v0.1 — existing)
# ===========================================================================

@app.route('/api/v1/health')
def health():
    return jsonify({"status": "ok", "version": "0.2.0"})


# ---------------------------------------------------------------------------
# GET /api/v1/fisherman/<domain>
# ---------------------------------------------------------------------------

@app.route('/api/v1/fisherman/<domain>')
def get_fisherman(domain):
    db = get_db()
    fisherman = row_to_dict(
        db.execute("SELECT * FROM fisherman WHERE domain = ?", (domain,)).fetchone()
    )
    if not fisherman:
        return jsonify({"error": "fisherman not found", "domain": domain}), 404

    fid = fisherman['fisherman_id']
    fisherman['motives']  = rows_to_list(db.execute(
        "SELECT * FROM motive WHERE fisherman_id = ?", (fid,)).fetchall())
    fisherman['catches']  = rows_to_list(db.execute(
        "SELECT * FROM catch WHERE fisherman_id = ?", (fid,)).fetchall())
    fisherman['evidence'] = rows_to_list(db.execute(
        "SELECT * FROM evidence WHERE entity_id = ? AND entity_type = 'fisherman'",
        (fid,)).fetchall())
    return jsonify(fisherman)


# ---------------------------------------------------------------------------
# GET /api/v1/explain?domain=<domain>
# Used by the Hoffman Browser for pre-analysis context injection.
# ---------------------------------------------------------------------------

@app.route('/api/v1/explain')
def explain():
    domain = request.args.get('domain', '').strip()
    if not domain:
        return jsonify({"error": "domain parameter required"}), 400

    db = get_db()
    fisherman = row_to_dict(
        db.execute("SELECT * FROM fisherman WHERE domain = ?", (domain,)).fetchone()
    )
    if not fisherman:
        return jsonify({"known": False, "domain": domain})

    fid = fisherman['fisherman_id']
    motives      = rows_to_list(db.execute(
        "SELECT * FROM motive WHERE fisherman_id = ?", (fid,)).fetchall())
    catch_count  = db.execute(
        "SELECT COUNT(*) AS n FROM catch WHERE fisherman_id = ?", (fid,)).fetchone()['n']
    first_motive = motives[0] if motives else None

    return jsonify({
        "known":          True,
        "domain":         domain,
        "display_name":   fisherman.get('display_name'),
        "owner":          fisherman.get('owner'),
        "business_model": fisherman.get('business_model'),
        "confidence":     fisherman.get('confidence_score'),
        "first_motive":   first_motive,
        "catch_count":    catch_count,
    })


# ---------------------------------------------------------------------------
# GET /api/v1/bait/<technique>
# ---------------------------------------------------------------------------

@app.route('/api/v1/bait/<technique>')
def get_bait(technique):
    db  = get_db()
    rows = rows_to_list(db.execute(
        "SELECT * FROM motive WHERE motive_type = ?", (technique,)).fetchall())
    return jsonify({"technique": technique, "count": len(rows), "motives": rows})


# ---------------------------------------------------------------------------
# GET /api/v1/pattern/<pattern>
# ---------------------------------------------------------------------------

@app.route('/api/v1/pattern/<pattern>')
def get_pattern(pattern):
    db   = get_db()
    like = f"%{pattern}%"
    rows = rows_to_list(db.execute(
        "SELECT * FROM catch WHERE harm_type LIKE ?", (like,)).fetchall())
    return jsonify({"pattern": pattern, "count": len(rows), "catches": rows})


# ---------------------------------------------------------------------------
# GET /api/v1/search?q=<query>
# ---------------------------------------------------------------------------

@app.route('/api/v1/search')
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({"error": "q parameter required"}), 400

    db   = get_db()
    like = f"%{q}%"
    fishermen = rows_to_list(db.execute(
        "SELECT * FROM fisherman WHERE domain LIKE ? OR display_name LIKE ? OR owner LIKE ?",
        (like, like, like)).fetchall())
    motives = rows_to_list(db.execute(
        "SELECT * FROM motive WHERE description LIKE ? OR motive_type LIKE ?",
        (like, like)).fetchall())
    catches = rows_to_list(db.execute(
        "SELECT * FROM catch WHERE harm_type LIKE ? OR documented_outcome LIKE ?",
        (like, like)).fetchall())

    return jsonify({
        "query":      q,
        "fishermen":  fishermen,
        "motives":    motives,
        "catches":    catches,
    })


# ---------------------------------------------------------------------------
# POST /api/v1/session
# ---------------------------------------------------------------------------

@app.route('/api/v1/session', methods=['POST'])
def post_session():
    data = request.get_json(silent=True) or {}
    return jsonify({"status": "received", "echo": data})


# ===========================================================================
# ADMIN GUI ROUTES
# ===========================================================================

@app.route('/admin')
def admin_dashboard():
    db = get_db()
    counts = {
        'fishermen': db.execute("SELECT COUNT(*) AS n FROM fisherman").fetchone()['n'],
        'motives':   db.execute("SELECT COUNT(*) AS n FROM motive").fetchone()['n'],
        'catches':   db.execute("SELECT COUNT(*) AS n FROM catch").fetchone()['n'],
        'evidence':  db.execute("SELECT COUNT(*) AS n FROM evidence").fetchone()['n'],
    }
    recent_catches = rows_to_list(db.execute(
        "SELECT c.*, f.domain FROM catch c JOIN fisherman f ON c.fisherman_id = f.fisherman_id "
        "ORDER BY c.created_at DESC LIMIT 5").fetchall())
    return render_template('admin/index.html',
                           counts=counts,
                           recent_catches=recent_catches,
                           active_page='dashboard')


@app.route('/admin/fishermen')
def admin_fishermen():
    db = get_db()
    fishermen = rows_to_list(db.execute("""
        SELECT f.*,
               COUNT(DISTINCT c.catch_id) AS catch_count,
               COUNT(DISTINCT m.motive_id) AS motive_count
        FROM fisherman f
        LEFT JOIN catch c ON c.fisherman_id = f.fisherman_id
        LEFT JOIN motive m ON m.fisherman_id = f.fisherman_id
        GROUP BY f.fisherman_id
        ORDER BY f.domain
    """).fetchall())
    return render_template('admin/fishermen.html', fishermen=fishermen, active_page='fishermen')


@app.route('/admin/fishermen/<fid>')
def admin_fisherman_detail(fid):
    db = get_db()
    row = db.execute("SELECT * FROM fisherman WHERE fisherman_id = ?", (fid,)).fetchone()
    if not row:
        return "Not found", 404
    fisherman = row_to_dict(row)

    motives = rows_to_list(db.execute(
        "SELECT * FROM motive WHERE fisherman_id = ?", (fid,)).fetchall())
    catches = rows_to_list(db.execute(
        "SELECT c.*, "
        "(SELECT COUNT(*) FROM evidence e WHERE e.entity_id = c.catch_id AND e.entity_type = 'catch') AS evidence_count "
        "FROM catch c WHERE c.fisherman_id = ?", (fid,)).fetchall())

    catch_count  = len(catches)
    motive_count = len(motives)
    top_patterns = list(set(c['harm_type'] for c in catches)) if catches else []

    api_response = {
        'known':          True,
        'domain':         fisherman['domain'],
        'display_name':   fisherman.get('display_name'),
        'owner':          fisherman.get('owner'),
        'business_model': fisherman.get('business_model'),
        'confidence':     fisherman.get('confidence_score'),
        'first_motive':   motives[0] if motives else None,
        'catch_count':    catch_count,
    }

    return render_template('admin/fisherman_detail.html',
                           fisherman=fisherman,
                           motives=motives,
                           catches=catches,
                           catch_count=catch_count,
                           motive_count=motive_count,
                           top_patterns=top_patterns,
                           api_response=api_response,
                           active_page='fishermen')


@app.route('/admin/catches')
def admin_catches():
    db = get_db()
    filter_fisherman = request.args.get('fisherman', '').strip()
    filter_harm      = request.args.get('harm', '').strip()

    query = (
        "SELECT c.*, f.display_name AS fisherman_name, f.domain, "
        "(SELECT COUNT(*) FROM evidence e WHERE e.entity_id = c.catch_id AND e.entity_type = 'catch') AS evidence_count "
        "FROM catch c JOIN fisherman f ON c.fisherman_id = f.fisherman_id WHERE 1=1"
    )
    params = []
    if filter_fisherman:
        query += " AND f.domain = ?"
        params.append(filter_fisherman)
    if filter_harm:
        query += " AND c.harm_type = ?"
        params.append(filter_harm)
    query += " ORDER BY c.severity_score DESC"

    catches   = rows_to_list(db.execute(query, params).fetchall())
    fishermen = rows_to_list(db.execute("SELECT domain FROM fisherman ORDER BY domain").fetchall())
    harm_types = [r['harm_type'] for r in rows_to_list(
        db.execute("SELECT DISTINCT harm_type FROM catch ORDER BY harm_type").fetchall())]

    return render_template('admin/catches.html',
                           catches=catches,
                           fishermen=fishermen,
                           harm_types=harm_types,
                           filter_fisherman=filter_fisherman,
                           filter_harm=filter_harm,
                           active_page='catches')


# ---------------------------------------------------------------------------
# Admin: submissions queue
# ---------------------------------------------------------------------------

@app.route('/admin/submissions')
def admin_submissions():
    db            = get_db()
    filter_status = request.args.get('status', 'pending').strip()

    submissions = rows_to_list(db.execute(
        "SELECT * FROM submission WHERE status = ? ORDER BY submitted_at DESC",
        (filter_status,)
    ).fetchall())

    # Parse flags JSON for template rendering
    for s in submissions:
        try:
            s['flags_parsed'] = json.loads(s['flags']) if s.get('flags') else []
        except (json.JSONDecodeError, TypeError):
            s['flags_parsed'] = []

    total_pending      = db.execute("SELECT COUNT(*) AS n FROM submission WHERE status = 'pending'").fetchone()['n']
    total_investigating = db.execute("SELECT COUNT(*) AS n FROM submission WHERE status = 'investigating'").fetchone()['n']
    total_accepted     = db.execute("SELECT COUNT(*) AS n FROM submission WHERE status = 'accepted'").fetchone()['n']
    total_rejected     = db.execute("SELECT COUNT(*) AS n FROM submission WHERE status = 'rejected'").fetchone()['n']

    return render_template('admin/submissions.html',
                           submissions=submissions,
                           filter_status=filter_status,
                           total_pending=total_pending,
                           total_investigating=total_investigating,
                           total_accepted=total_accepted,
                           total_rejected=total_rejected,
                           active_page='submissions')


@app.route('/admin/submissions/<submission_id>/status', methods=['POST'])
def admin_update_submission_status(submission_id):
    db         = get_db()
    new_status = request.form.get('status', '').strip()
    agent_notes = request.form.get('agent_notes', '').strip()

    valid_statuses = {'pending', 'investigating', 'accepted', 'rejected'}
    if new_status not in valid_statuses:
        return jsonify({"error": f"invalid status '{new_status}'"}), 400

    sub = db.execute(
        "SELECT id FROM submission WHERE submission_id = ?", (submission_id,)
    ).fetchone()
    if not sub:
        return "Not found", 404

    db.execute(
        "UPDATE submission SET status = ?, agent_notes = ? WHERE submission_id = ?",
        (new_status, agent_notes, submission_id)
    )
    db.commit()

    from flask import redirect, url_for
    return redirect(url_for('admin_submissions', status=new_status))


# ===========================================================================
# NETWORK AND ACTOR API ENDPOINTS  (v0.2)
# ===========================================================================

# ---------------------------------------------------------------------------
# GET /api/v1/network/map
# Full network graph as JSON (nodes + edges) suitable for visualisation.
# Registered BEFORE /api/v1/network/<domain> so Flask resolves the static
# path segment "map" before the parameterised segment.
# ---------------------------------------------------------------------------

@app.route('/api/v1/network/map')
def network_map():
    db = get_db()

    fishermen = rows_to_list(db.execute(
        "SELECT id, domain, display_name, owner, country, confidence_score "
        "FROM fisherman").fetchall())

    actors = rows_to_list(db.execute(
        "SELECT id, name, current_role, current_fisherman_id, "
        "documented_knowledge_of_harm, confidence "
        "FROM actor").fetchall())

    network_edges = rows_to_list(db.execute("""
        SELECT n.id, n.relationship_type, n.confidence, n.verified,
               fp.domain AS parent_domain, fc.domain AS child_domain
        FROM   network n
        JOIN   fisherman fp ON n.parent_fisherman_id = fp.id
        JOIN   fisherman fc ON n.child_fisherman_id  = fc.id
    """).fetchall())

    actor_role_edges = rows_to_list(db.execute("""
        SELECT ar.actor_id, ar.fisherman_id, ar.role,
               ar.date_start, ar.date_end
        FROM   actor_role ar
    """).fetchall())

    nodes = [{"type": "fisherman", **f} for f in fishermen] + \
            [{"type": "actor",     **a} for a in actors]

    edges = [{"edge_type": "network",    **e} for e in network_edges] + \
            [{"edge_type": "actor_role", **e} for e in actor_role_edges]

    return jsonify({
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
    })


# ---------------------------------------------------------------------------
# GET /api/v1/network/<domain>
# All documented relationships for a fisherman domain.
# ---------------------------------------------------------------------------

@app.route('/api/v1/network/<domain>')
def get_network(domain):
    db = get_db()

    fisherman = row_to_dict(
        db.execute("SELECT * FROM fisherman WHERE domain = ?", (domain,)).fetchone()
    )
    if not fisherman:
        return jsonify({"error": "fisherman not found", "domain": domain}), 404

    fid = fisherman['id']

    # Relationships where this fisherman is the parent (owns/funds children)
    as_parent = rows_to_list(db.execute("""
        SELECT n.*,
               f_child.domain       AS child_domain,
               f_child.display_name AS child_name
        FROM   network n
        JOIN   fisherman f_child ON n.child_fisherman_id = f_child.id
        WHERE  n.parent_fisherman_id = ?
        ORDER  BY n.confidence DESC
    """, (fid,)).fetchall())

    # Relationships where this fisherman is the child (owned/funded by parents)
    as_child = rows_to_list(db.execute("""
        SELECT n.*,
               f_parent.domain       AS parent_domain,
               f_parent.display_name AS parent_name
        FROM   network n
        JOIN   fisherman f_parent ON n.parent_fisherman_id = f_parent.id
        WHERE  n.child_fisherman_id = ?
        ORDER  BY n.confidence DESC
    """, (fid,)).fetchall())

    # Actors currently associated with this fisherman
    actors = rows_to_list(db.execute("""
        SELECT a.id, a.name, a.current_role,
               a.documented_knowledge_of_harm,
               a.knowledge_date, a.confidence
        FROM   actor a
        WHERE  a.current_fisherman_id = ?
        ORDER  BY a.documented_knowledge_of_harm DESC, a.confidence DESC
    """, (fid,)).fetchall())

    return jsonify({
        "domain":       domain,
        "fisherman_id": fid,
        "display_name": fisherman.get('display_name'),
        "as_parent":    as_parent,
        "as_child":     as_child,
        "actors":       actors,
    })


# ---------------------------------------------------------------------------
# GET /api/v1/actor/search?name=<name>
# Registered BEFORE /api/v1/actor/<actor_id> to prevent Flask treating
# "search" as an integer actor_id.
# ---------------------------------------------------------------------------

@app.route('/api/v1/actor/search')
def search_actors():
    name = request.args.get('name', '').strip()
    if not name:
        return jsonify({"error": "name parameter required"}), 400

    db   = get_db()
    like = f"%{name}%"
    actors = rows_to_list(db.execute(
        "SELECT * FROM actor WHERE name LIKE ? OR name_aliases LIKE ?",
        (like, like)).fetchall())

    for actor in actors:
        actor_id = actor['id']
        actor['roles'] = rows_to_list(db.execute("""
            SELECT ar.*, f.domain, f.display_name
            FROM   actor_role ar
            JOIN   fisherman f ON ar.fisherman_id = f.id
            WHERE  ar.actor_id = ?
            ORDER  BY ar.date_start DESC
        """, (actor_id,)).fetchall())

    return jsonify({"query": name, "count": len(actors), "actors": actors})


# ---------------------------------------------------------------------------
# GET /api/v1/actor/<actor_id>
# Full profile for a documented actor — roles, investments, political ties,
# and all documented knowledge-of-harm moments.
# ---------------------------------------------------------------------------

@app.route('/api/v1/actor/<int:actor_id>')
def get_actor(actor_id):
    db    = get_db()
    actor = row_to_dict(
        db.execute("SELECT * FROM actor WHERE id = ?", (actor_id,)).fetchone()
    )
    if not actor:
        return jsonify({"error": "actor not found", "actor_id": actor_id}), 404

    # Current fisherman (if any)
    if actor.get('current_fisherman_id'):
        current_fisherman = row_to_dict(db.execute(
            "SELECT domain, display_name FROM fisherman WHERE id = ?",
            (actor['current_fisherman_id'],)).fetchone())
        actor['current_fisherman'] = current_fisherman
    else:
        actor['current_fisherman'] = None

    # All roles across platforms over time
    actor['roles'] = rows_to_list(db.execute("""
        SELECT ar.*, f.domain, f.display_name
        FROM   actor_role ar
        JOIN   fisherman f ON ar.fisherman_id = f.id
        WHERE  ar.actor_id = ?
        ORDER  BY ar.date_start DESC
    """, (actor_id,)).fetchall())

    # Investment positions
    actor['investments'] = rows_to_list(db.execute("""
        SELECT ai.*, f.domain, f.display_name
        FROM   actor_investment ai
        JOIN   fisherman f ON ai.fisherman_id = f.id
        WHERE  ai.actor_id = ?
        ORDER  BY ai.date_start DESC
    """, (actor_id,)).fetchall())

    # Political relationships
    actor['political'] = rows_to_list(db.execute(
        "SELECT * FROM actor_political WHERE actor_id = ? ORDER BY date DESC",
        (actor_id,)).fetchall())

    # Documented knowledge-of-harm moments
    actor['knowledge'] = rows_to_list(db.execute("""
        SELECT ak.*, f.domain, f.display_name
        FROM   actor_knowledge ak
        LEFT   JOIN fisherman f ON ak.fisherman_id = f.id
        WHERE  ak.actor_id = ?
        ORDER  BY ak.date ASC
    """, (actor_id,)).fetchall())

    return jsonify(actor)


# ---------------------------------------------------------------------------
# GET /api/v1/accountability/<domain>
# Full accountability chain for a domain:
#   ownership chain → key actors → knowledge moments →
#   political relationships → documented harm → motives
# ---------------------------------------------------------------------------

@app.route('/api/v1/accountability/<domain>')
def get_accountability(domain):
    db = get_db()

    fisherman = row_to_dict(
        db.execute("SELECT * FROM fisherman WHERE domain = ?", (domain,)).fetchone()
    )
    if not fisherman:
        return jsonify({"error": "fisherman not found", "domain": domain}), 404

    fid      = fisherman['id']
    fid_text = fisherman['fisherman_id']

    # Ownership / funding chain (parents of this fisherman)
    ownership_chain = rows_to_list(db.execute("""
        SELECT n.relationship_type, n.description, n.evidence,
               n.source_url, n.date_established, n.confidence,
               fp.domain       AS parent_domain,
               fp.display_name AS parent_name,
               fp.owner        AS parent_owner
        FROM   network n
        JOIN   fisherman fp ON n.parent_fisherman_id = fp.id
        WHERE  n.child_fisherman_id = ?
          AND  n.relationship_type IN ('owns', 'funds', 'investment')
        ORDER  BY n.confidence DESC
    """, (fid,)).fetchall())

    # Key actors currently or historically linked to this fisherman
    key_actors = rows_to_list(db.execute("""
        SELECT DISTINCT
               a.id, a.name, a.current_role,
               a.documented_knowledge_of_harm,
               a.knowledge_date, a.knowledge_source, a.confidence
        FROM   actor a
        LEFT   JOIN actor_role ar ON ar.actor_id = a.id
        WHERE  a.current_fisherman_id = ?
           OR  ar.fisherman_id = ?
        ORDER  BY a.documented_knowledge_of_harm DESC, a.confidence DESC
    """, (fid, fid)).fetchall())

    # All documented knowledge-of-harm moments for this fisherman
    knowledge_moments = rows_to_list(db.execute("""
        SELECT ak.*, a.name AS actor_name
        FROM   actor_knowledge ak
        JOIN   actor a ON ak.actor_id = a.id
        WHERE  ak.fisherman_id = ?
        ORDER  BY ak.date ASC
    """, (fid,)).fetchall())

    # Political relationships for actors tied to this fisherman
    political_relationships = rows_to_list(db.execute("""
        SELECT ap.*, a.name AS actor_name
        FROM   actor_political ap
        JOIN   actor a ON ap.actor_id = a.id
        WHERE  a.current_fisherman_id = ?
           OR  a.id IN (
               SELECT actor_id FROM actor_role WHERE fisherman_id = ?
           )
        ORDER  BY ap.date DESC
    """, (fid, fid)).fetchall())

    # Documented harm / catches
    documented_harm = rows_to_list(db.execute(
        "SELECT * FROM catch WHERE fisherman_id = ? ORDER BY severity_score DESC",
        (fid_text,)).fetchall())

    # Motives
    motives = rows_to_list(db.execute(
        "SELECT * FROM motive WHERE fisherman_id = ?", (fid_text,)).fetchall())

    return jsonify({
        "domain":                   domain,
        "fisherman":                fisherman,
        "ownership_chain":          ownership_chain,
        "key_actors":               key_actors,
        "knowledge_moments":        knowledge_moments,
        "political_relationships":  political_relationships,
        "documented_harm":          documented_harm,
        "motives":                  motives,
    })


# ---------------------------------------------------------------------------
# GET /api/v1/conspiracy/<fisherman_id_1>/<fisherman_id_2>
# All documented connections between two fishermen:
# shared ownership, shared investors, shared board members,
# documented coordination, shared personnel.
# Uses integer primary key ids (fisherman.id), not fisherman_id text keys.
# ---------------------------------------------------------------------------

@app.route('/api/v1/conspiracy/<int:fisherman_id_1>/<int:fisherman_id_2>')
def get_conspiracy(fisherman_id_1, fisherman_id_2):
    db = get_db()

    f1 = row_to_dict(
        db.execute("SELECT * FROM fisherman WHERE id = ?", (fisherman_id_1,)).fetchone()
    )
    f2 = row_to_dict(
        db.execute("SELECT * FROM fisherman WHERE id = ?", (fisherman_id_2,)).fetchone()
    )
    if not f1:
        return jsonify({"error": "fisherman not found", "fisherman_id": fisherman_id_1}), 404
    if not f2:
        return jsonify({"error": "fisherman not found", "fisherman_id": fisherman_id_2}), 404

    # Direct network relationships between the two (either direction)
    direct_links = rows_to_list(db.execute("""
        SELECT n.*,
               fp.domain AS parent_domain, fc.domain AS child_domain
        FROM   network n
        JOIN   fisherman fp ON n.parent_fisherman_id = fp.id
        JOIN   fisherman fc ON n.child_fisherman_id  = fc.id
        WHERE  (n.parent_fisherman_id = ? AND n.child_fisherman_id = ?)
           OR  (n.parent_fisherman_id = ? AND n.child_fisherman_id = ?)
        ORDER  BY n.confidence DESC
    """, (fisherman_id_1, fisherman_id_2,
          fisherman_id_2, fisherman_id_1)).fetchall())

    # Shared parent fishermen (common owners / investors)
    shared_parents = rows_to_list(db.execute("""
        SELECT fp.domain AS shared_parent_domain,
               fp.display_name AS shared_parent_name,
               n1.relationship_type AS link_to_f1,
               n2.relationship_type AS link_to_f2,
               MIN(n1.confidence, n2.confidence) AS min_confidence
        FROM   network n1
        JOIN   network n2
               ON  n1.parent_fisherman_id = n2.parent_fisherman_id
        JOIN   fisherman fp ON fp.id = n1.parent_fisherman_id
        WHERE  n1.child_fisherman_id = ?
          AND  n2.child_fisherman_id = ?
        ORDER  BY min_confidence DESC
    """, (fisherman_id_1, fisherman_id_2)).fetchall())

    # Shared actors (people who have held roles at both fishermen)
    shared_actors = rows_to_list(db.execute("""
        SELECT DISTINCT
               a.id, a.name, a.current_role, a.confidence,
               ar1.role       AS role_at_f1,
               ar1.date_start AS start_at_f1,
               ar1.date_end   AS end_at_f1,
               ar2.role       AS role_at_f2,
               ar2.date_start AS start_at_f2,
               ar2.date_end   AS end_at_f2
        FROM   actor a
        JOIN   actor_role ar1 ON ar1.actor_id = a.id AND ar1.fisherman_id = ?
        JOIN   actor_role ar2 ON ar2.actor_id = a.id AND ar2.fisherman_id = ?
        ORDER  BY a.confidence DESC
    """, (fisherman_id_1, fisherman_id_2)).fetchall())

    # Shared investment actors (investors in both)
    shared_investors = rows_to_list(db.execute("""
        SELECT DISTINCT
               a.id, a.name, a.current_role, a.confidence,
               ai1.position_type AS position_at_f1,
               ai2.position_type AS position_at_f2
        FROM   actor a
        JOIN   actor_investment ai1 ON ai1.actor_id = a.id AND ai1.fisherman_id = ?
        JOIN   actor_investment ai2 ON ai2.actor_id = a.id AND ai2.fisherman_id = ?
        ORDER  BY a.confidence DESC
    """, (fisherman_id_1, fisherman_id_2)).fetchall())

    # Shared harm patterns (same harm_type documented at both fishermen)
    # NOTE: catch.fisherman_id is the TEXT fisherman_id key, not the integer id.
    shared_harm_types = rows_to_list(db.execute("""
        SELECT c1.harm_type,
               COUNT(DISTINCT c1.id) AS count_at_f1,
               COUNT(DISTINCT c2.id) AS count_at_f2
        FROM   catch c1
        JOIN   catch c2 ON c1.harm_type = c2.harm_type
        WHERE  c1.fisherman_id = ?
          AND  c2.fisherman_id = ?
        GROUP  BY c1.harm_type
        ORDER  BY (count_at_f1 + count_at_f2) DESC
    """, (f1['fisherman_id'], f2['fisherman_id'])).fetchall())

    connection_count = (
        len(direct_links) +
        len(shared_parents) +
        len(shared_actors) +
        len(shared_investors)
    )

    return jsonify({
        "fisherman_1":       {"id": fisherman_id_1, "domain": f1['domain'], "display_name": f1.get('display_name')},
        "fisherman_2":       {"id": fisherman_id_2, "domain": f2['domain'], "display_name": f2.get('display_name')},
        "connection_count":  connection_count,
        "direct_links":      direct_links,
        "shared_parents":    shared_parents,
        "shared_actors":     shared_actors,
        "shared_investors":  shared_investors,
        "shared_harm_types": shared_harm_types,
    })


# ===========================================================================
# SUBMISSIONS API  (v0.3)
# ===========================================================================

# ---------------------------------------------------------------------------
# POST /api/v1/submit
# Accepts a Hoffman Browser analysis result as a crowdsourced submission.
# contributor_token = SHA-256(provider:apikey) — anonymous identity for
# rate limiting. Raw API key is never transmitted.
# Rate limit: 50 submissions per token per 24 hours.
# ---------------------------------------------------------------------------

SUBMISSION_DAILY_LIMIT = 50

@app.route('/api/v1/submit', methods=['POST'])
def submit_analysis():
    data  = request.get_json(silent=True) or {}

    domain            = (data.get('domain') or '').strip()
    contributor_token = (data.get('contributor_token') or '').strip()
    flags             = data.get('flags') or []
    summary           = (data.get('summary') or '').strip()
    url               = (data.get('url') or '').strip()

    if not domain:
        return jsonify({"error": "domain is required"}), 400
    if not contributor_token or len(contributor_token) < 16:
        return jsonify({"error": "valid contributor_token is required"}), 400
    if not flags:
        return jsonify({"error": "no flags to submit — only analyses with findings are accepted"}), 400

    db = get_db()

    # Rate limit: count submissions from this token in the last 24 hours
    recent = db.execute(
        "SELECT COUNT(*) AS n FROM submission "
        "WHERE contributor_token = ? AND submitted_at > datetime('now', '-1 day')",
        (contributor_token,)
    ).fetchone()['n']

    if recent >= SUBMISSION_DAILY_LIMIT:
        return jsonify({
            "error":   "rate_limit_exceeded",
            "message": "Daily submission limit reached. Submissions reset every 24 hours."
        }), 429

    submission_id = 'sub-' + str(uuid.uuid4())[:12]

    db.execute(
        "INSERT INTO submission "
        "(submission_id, domain, url, contributor_token, flags, summary, technique_count) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (submission_id, domain, url, contributor_token,
         json.dumps(flags), summary, len(flags))
    )
    db.commit()

    return jsonify({"success": True, "submission_id": submission_id}), 201


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

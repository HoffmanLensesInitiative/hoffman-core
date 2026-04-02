"""
BMID API — Behavioral Manipulation Intelligence Database
Version: 0.2.0
Stack: Python / Flask / SQLite (via sqlite3)
"""

import os
import sqlite3
import json
from flask import Flask, jsonify, request, g, render_template

app = Flask(__name__)

DATABASE = os.path.join(os.path.dirname(__file__), 'bmid.db')
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

    fid = fisherman['id']
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

    fid = fisherman['id']
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
    fisherman_count = db.execute("SELECT COUNT(*) AS n FROM fisherman").fetchone()['n']
    motive_count    = db.execute("SELECT COUNT(*) AS n FROM motive").fetchone()['n']
    catch_count     = db.execute("SELECT COUNT(*) AS n FROM catch").fetchone()['n']
    evidence_count  = db.execute("SELECT COUNT(*) AS n FROM evidence").fetchone()['n']
    return render_template('admin/dashboard.html',
                           fisherman_count=fisherman_count,
                           motive_count=motive_count,
                           catch_count=catch_count,
                           evidence_count=evidence_count)


@app.route('/admin/fishermen')
def admin_fishermen():
    db        = get_db()
    fishermen = rows_to_list(db.execute("SELECT * FROM fisherman ORDER BY domain").fetchall())
    return render_template('admin/fishermen.html', fishermen=fishermen)


@app.route('/admin/fishermen/<int:fid>')
def admin_fisherman_detail(fid):
    db        = get_db()
    fisherman = row_to_dict(db.execute("SELECT * FROM fisherman WHERE id = ?", (fid,)).fetchone())
    if not fisherman:
        return "Not found", 404
    fisherman['motives']  = rows_to_list(db.execute(
        "SELECT * FROM motive WHERE fisherman_id = ?", (fid,)).fetchall())
    fisherman['catches']  = rows_to_list(db.execute(
        "SELECT * FROM catch WHERE fisherman_id = ?", (fid,)).fetchall())
    fisherman['evidence'] = rows_to_list(db.execute(
        "SELECT * FROM evidence WHERE entity_id = ? AND entity_type = 'fisherman'",
        (fid,)).fetchall())
    return render_template('admin/fisherman_detail.html', fisherman=fisherman)


@app.route('/admin/catches')
def admin_catches():
    db      = get_db()
    catches = rows_to_list(db.execute(
        "SELECT c.*, f.display_name AS fisherman_name, f.domain "
        "FROM catch c JOIN fisherman f ON c.fisherman_id = f.id "
        "ORDER BY c.severity_score DESC").fetchall())
    return render_template('admin/catches.html', catches=catches)


# ===========================================================================
# NETWORK AND ACTOR API ENDPOINTS  (v0.2 — new)
# ===========================================================================

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

    # Relationships where this fisherman is the parent
    as_parent = rows_to_list(db.execute("""
        SELECT n.*,
               f_child.domain  AS child_domain,
               f_child.display_name AS child_name
        FROM   network n
        JOIN   fisherman f_child ON n.child_fisherman_id = f_child.id
        WHERE  n.parent_fisherman_id = ?
    """, (fid,)).fetchall())

    # Relationships where this fisherman is the child
    as_child = rows_to_list(db.execute("""
        SELECT n.*,
               f_parent.domain  AS parent_domain,
               f_parent.display_name AS parent_name
        FROM   network n
        JOIN   fisherman f_parent ON n.parent_fisherman_id = f_parent.id
        WHERE  n.child_fisherman_id = ?
    """, (fid,)).fetchall())

    # Actors currently associated with this fisherman
    actors = rows_to_list(db.execute("""
        SELECT a.id, a.name, a.current_role, a.documented_knowledge_of_harm,
               a.knowledge_date, a.confidence
        FROM   actor a
        WHERE  a.current_fisherman_id = ?
    """, (fid,)).fetchall())

    return jsonify({
        "domain":      domain,
        "fisherman_id": fid,
        "display_name": fisherman.get('display_name'),
        "as_parent":   as_parent,
        "as_child":    as_child,
        "actors":      actors,
    })


# ---------------------------------------------------------------------------
# GET /api/v1/actor/search?name=<name>
# Must be registered BEFORE /api/v1/actor/<actor_id> to avoid route collision.
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
        actor['roles'] = rows_to_list(db.execute(
            "SELECT ar.*, f.domain, f.display_name "
            "FROM actor_role ar JOIN fisherman f ON ar.fisherman_id = f.id "
            "WHERE ar.actor_id = ? ORDER BY ar.date_start DESC",
            (actor_id,)).fetchall())

    return jsonify({"query": name, "count": len(actors), "actors": actors})


# ---------------------------------------------------------------------------
# GET /api/v1/actor/<actor_id>
# Full profile for a documented actor.
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

    # All roles across platforms
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

    # Documented knowledge moments
    actor['knowledge'] = rows_to_list(db.execute("""
        SELECT ak.*, f.domain, f.display_name
        FROM   actor_knowledge ak
        LEFT   JOIN fisherman f ON ak.fisherman_id = f.id
        WHERE  ak.actor_id = ?
        ORDER  BY ak.date DESC
    """, (actor_id,)).fetchall())

    return jsonify(actor)


# ---------------------------------------------------------------------------
# GET /api/v1/network/map
# Full network graph as JSON (nodes + edges) suitable for visualisation.
# Must be registered AFTER the specific /network/ routes to avoid ambiguity,
# but Flask resolves static path segments before parameterised ones so this
# ordering is safe.
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

    edges = [{"edge_type": "network",     **e} for e in network_edges] + \
            [{"edge_type": "actor_role",  **e} for e in actor_role_edges]

    return jsonify({"nodes": nodes, "edges": edges})


# ---------------------------------------------------------------------------
# GET /api/v1/accountability/<domain>
# Full accountability chain for a domain:
#   parent companies → key actors → knowledge moments → political relationships
#   → documented harm.
# ---------------------------------------------------------------------------

@app.route('/api/v1/accountability/<domain>')
def get_accountability(domain):
    db = get_db()

    fisherman = row_to_dict(
        db.execute("SELECT * FROM fisherman WHERE domain = ?", (domain,)).fetchone()
    )
    if not fisherman:
        return jsonify({"error": "fisherman not found", "domain": domain}), 404

    fid = fisherman['id']

    # Parent companies / ownership chain
    parent_relationships = rows_to_list(db.execute("""
        SELECT n.relationship_type, n.description, n.evidence,
               n.source_url, n.date_established, n.confidence,
               fp.domain AS parent_domain, fp.display_name AS parent_name,
               fp.owner  AS parent_owner
        FROM   network n
        JOIN   fisherman fp ON n.parent_fisherman_id = fp.id
        WHERE  n.child_fisherman_id = ?
          AND  n.relationship_type IN ('owns', 'funds', 'investment')
        ORDER  BY n.confidence DESC
    """, (fid,)).fetchall())

    # Key actors currently or historically linked to this fisherman
    actors = rows_to_list(db.execute("""
        SELECT DISTINCT a.id, a.name, a.current_role,
               a.documented_knowledge_of_harm,
               a.knowledge_date, a.knowledge_source, a.confidence
        FROM   actor a
        LEFT   JOIN actor_role ar ON ar.actor_id = a.id
        WHERE  a.current_fisherman_id = ?
           OR  ar.fisherman_id = ?
        ORDER  BY a.documented_knowledge_of_harm DESC, a.confidence DESC
    """, (fid, fid)).fetchall())

    # All documented knowledge moments for this fisherman
    knowledge_moments = rows_to_list(db.execute("""
        SELECT ak.*, a.name AS actor_name
        FROM   actor_knowledge ak
        JOIN   actor a ON ak.actor_id = a.id
        WHERE  ak.fisherman_id = ?
        ORDER  BY ak.date ASC
    """, (fid,)).fetchall())

    # Political relationships for actors tied to this fisherman
    political = rows_to_list(db.execute("""
        SELECT ap.*, a.name AS actor_name
        FROM   actor_political ap
        JOIN   actor a ON ap.actor_id = a.id
        WHERE  a.current_fisherman_id = ?
           OR  a.id IN (SELECT actor_id FROM actor_role WHERE fisherman_id = ?)
        ORDER  BY ap.date DESC
    """, (fid, fid)).fetchall())

    # Documented catches / harm
    catches = rows_to_list(db.execute(
        "SELECT * FROM catch WHERE fisherman_id = ? ORDER BY severity_score DESC",
        (fid,)).fetchall())

    # Motives
    motives = rows_to_list(db.execute(
        "SELECT * FROM motive WHERE fisherman_id = ?", (fid,)).fetchall())

    return jsonify({
        "domain":               domain,
        "fisherman":            fisherman,
        "ownership_chain":      parent_relationships,
        "key_actors":           actors,
        "knowledge_moments":    knowledge_moments,
        "political_relationships": political,
        "documented_harm":      catches,
        "motives":              motives,
    })


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == '__main__':
    app.run(debug=True, port=5000)

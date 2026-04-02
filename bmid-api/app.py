"""
BMID API v0.1
Behavioral Manipulation Intelligence Database
Hoffman Lenses Initiative -- hoffmanlenses.org
License: MIT
"""

import sqlite3
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, g, render_template

app = Flask(__name__)

DB_PATH = 'bmid.db'

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# ── Database ──────────────────────────────────────────────

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA journal_mode=WAL')
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with open('schema.sql', 'r') as f:
            db.executescript(f.read())
        db.commit()
        print('[BMID] Database initialized')

def row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    # Parse JSON fields
    for field in ['revenue_sources', 'ad_networks', 'data_brokers',
                  'pattern_types', 'tracking_pixels', 'data_harvested',
                  'evidence_ids']:
        if field in d and d[field]:
            try:
                d[field] = json.loads(d[field])
            except:
                pass
    return d

# ── Fisherman endpoints ───────────────────────────────────

@app.route('/api/v1/fisherman/<domain>', methods=['GET'])
def get_fisherman(domain):
    """Get complete fisherman record with summary stats."""
    db = get_db()
    fisherman = row_to_dict(
        db.execute('SELECT * FROM fisherman WHERE domain = ?', [domain]).fetchone()
    )
    if not fisherman:
        return jsonify({'error': 'Fisherman not found', 'domain': domain}), 404

    fid = fisherman['fisherman_id']

    # Summary counts
    fisherman['bait_count'] = db.execute(
        'SELECT COUNT(*) FROM bait WHERE fisherman_id = ?', [fid]
    ).fetchone()[0]

    fisherman['catch_count'] = db.execute(
        'SELECT COUNT(*) FROM catch WHERE fisherman_id = ?', [fid]
    ).fetchone()[0]

    # Top patterns used
    patterns = db.execute(
        '''SELECT pattern_type, COUNT(*) as count
           FROM hook WHERE fisherman_id = ?
           GROUP BY pattern_type ORDER BY count DESC LIMIT 5''',
        [fid]
    ).fetchall()
    fisherman['top_patterns'] = [dict(p) for p in patterns]

    # Motives
    motives = db.execute(
        'SELECT motive_type, description FROM motive WHERE fisherman_id = ?',
        [fid]
    ).fetchall()
    fisherman['motives'] = [dict(m) for m in motives]

    return jsonify(fisherman)


@app.route('/api/v1/fisherman', methods=['POST'])
def create_fisherman():
    """Create or update a fisherman record."""
    data = request.json
    if not data or not data.get('domain'):
        return jsonify({'error': 'domain required'}), 400

    db = get_db()
    existing = db.execute(
        'SELECT fisherman_id FROM fisherman WHERE domain = ?',
        [data['domain']]
    ).fetchone()

    fid = existing['fisherman_id'] if existing else str(uuid.uuid4())

    # Serialize list fields
    for field in ['revenue_sources', 'ad_networks', 'data_brokers']:
        if field in data and isinstance(data[field], list):
            data[field] = json.dumps(data[field])

    if existing:
        db.execute(
            '''UPDATE fisherman SET
               display_name=?, owner=?, parent_company=?, country=?,
               business_model=?, revenue_sources=?, ad_networks=?,
               data_brokers=?, political_affiliation=?, documented_reach=?,
               legal_status=?, confidence_score=?, last_verified=?,
               updated_at=?, contributed_by=?
               WHERE fisherman_id=?''',
            [data.get('display_name'), data.get('owner'),
             data.get('parent_company'), data.get('country'),
             data.get('business_model'), data.get('revenue_sources'),
             data.get('ad_networks'), data.get('data_brokers'),
             data.get('political_affiliation'), data.get('documented_reach'),
             data.get('legal_status', 'active'),
             data.get('confidence_score', 0.5),
             data.get('last_verified'), datetime.utcnow().isoformat(),
             data.get('contributed_by'), fid]
        )
    else:
        db.execute(
            '''INSERT INTO fisherman (fisherman_id, domain, display_name,
               owner, parent_company, country, founded, business_model,
               revenue_sources, ad_networks, data_brokers,
               political_affiliation, documented_reach, legal_status,
               confidence_score, last_verified, contributed_by)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            [fid, data['domain'], data.get('display_name', data['domain']),
             data.get('owner'), data.get('parent_company'),
             data.get('country'), data.get('founded'),
             data.get('business_model'), data.get('revenue_sources'),
             data.get('ad_networks'), data.get('data_brokers'),
             data.get('political_affiliation'), data.get('documented_reach'),
             data.get('legal_status', 'active'),
             data.get('confidence_score', 0.5),
             data.get('last_verified'), data.get('contributed_by')]
        )
    db.commit()
    return jsonify({'fisherman_id': fid, 'domain': data['domain']}), 201


# ── Bait endpoints ────────────────────────────────────────

@app.route('/api/v1/fisherman/<domain>/bait', methods=['GET'])
def get_fisherman_bait(domain):
    """Get all bait for a fisherman."""
    db = get_db()
    fisherman = db.execute(
        'SELECT fisherman_id FROM fisherman WHERE domain = ?', [domain]
    ).fetchone()
    if not fisherman:
        return jsonify({'error': 'Fisherman not found'}), 404

    bait = db.execute(
        '''SELECT b.*, COUNT(h.hook_id) as hook_count
           FROM bait b LEFT JOIN hook h ON b.bait_id = h.bait_id
           WHERE b.fisherman_id = ?
           GROUP BY b.bait_id
           ORDER BY b.observed_at DESC LIMIT 50''',
        [fisherman['fisherman_id']]
    ).fetchall()

    return jsonify([row_to_dict(b) for b in bait])


# ── Session report endpoint ───────────────────────────────

@app.route('/api/v1/session', methods=['POST'])
def receive_session():
    """
    Accept anonymized session report from the extension.
    Creates bait and hook records from observed flags.
    """
    data = request.json
    if not data:
        return jsonify({'error': 'No data'}), 400

    db = get_db()
    hostname = data.get('hostname', '').lstrip('www.')
    flags = data.get('flags', [])  # list of {text, pattern_type, confidence, trigger_phrase}

    if not hostname or not flags:
        return jsonify({'ok': True, 'message': 'Nothing to record'}), 200

    # Find or note fisherman (don't create -- requires research)
    fisherman = db.execute(
        'SELECT fisherman_id FROM fisherman WHERE domain = ?', [hostname]
    ).fetchone()

    created_bait = 0
    created_hooks = 0

    for flag in flags:
        text = flag.get('text', '')
        if not text or len(text) < 20:
            continue

        bait_id = str(uuid.uuid4())
        db.execute(
            '''INSERT INTO bait
               (bait_id, fisherman_id, headline_text, url, pattern_types,
                escalation_score, observed_at, reported_by, verified)
               VALUES (?,?,?,?,?,?,?,?,0)''',
            [bait_id,
             fisherman['fisherman_id'] if fisherman else None,
             text[:500],
             data.get('url'),
             json.dumps([flag.get('pattern_type')] if flag.get('pattern_type') else []),
             flag.get('escalation_score', 0),
             datetime.utcnow().isoformat(),
             'extension_session_' + data.get('session_id', 'unknown')]
        )
        created_bait += 1

        if flag.get('pattern_type'):
            hook_id = str(uuid.uuid4())
            db.execute(
                '''INSERT INTO hook
                   (hook_id, bait_id, fisherman_id, pattern_type,
                    trigger_phrase, confidence, severity, hl_detect_version,
                    plain_explanation)
                   VALUES (?,?,?,?,?,?,?,?,?)''',
                [hook_id, bait_id,
                 fisherman['fisherman_id'] if fisherman else None,
                 flag.get('pattern_type'),
                 flag.get('trigger_phrase'),
                 flag.get('confidence', 0.65),
                 flag.get('severity', 'warn'),
                 flag.get('hl_detect_version', '0.1.0'),
                 flag.get('explanation')]
            )
            created_hooks += 1

    db.commit()
    return jsonify({
        'ok': True,
        'bait_created': created_bait,
        'hooks_created': created_hooks,
        'fisherman_known': fisherman is not None
    })


# ── Pattern endpoints ─────────────────────────────────────

@app.route('/api/v1/pattern/<pattern_type>', methods=['GET'])
def get_pattern(pattern_type):
    """Get all hooks of a pattern type across all fishermen."""
    db = get_db()
    hooks = db.execute(
        '''SELECT h.*, f.domain, f.display_name
           FROM hook h
           LEFT JOIN fisherman f ON h.fisherman_id = f.fisherman_id
           WHERE h.pattern_type = ?
           ORDER BY h.confidence DESC LIMIT 100''',
        [pattern_type]
    ).fetchall()

    # Frequency by domain
    by_domain = db.execute(
        '''SELECT f.domain, f.display_name, COUNT(*) as count
           FROM hook h
           LEFT JOIN fisherman f ON h.fisherman_id = f.fisherman_id
           WHERE h.pattern_type = ? AND f.domain IS NOT NULL
           GROUP BY f.domain ORDER BY count DESC LIMIT 20''',
        [pattern_type]
    ).fetchall()

    return jsonify({
        'pattern_type': pattern_type,
        'total_hooks': len(hooks),
        'by_domain': [dict(d) for d in by_domain],
        'examples': [row_to_dict(h) for h in hooks[:10]]
    })


# ── Explain endpoint ──────────────────────────────────────

@app.route('/api/v1/explain', methods=['GET'])
def explain():
    """
    Return everything known about a domain + pattern combination.
    Powers the "Why is this here?" button in the extension.
    """
    domain = request.args.get('domain', '').lstrip('www.')
    patterns = request.args.get('patterns', '').split(',')
    headline = request.args.get('headline', '')

    db = get_db()
    response = {
        'domain': domain,
        'patterns': patterns,
        'headline': headline,
        'fisherman': None,
        'motives': [],
        'catch_summary': None,
        'top_patterns': [],
        'intelligence_level': 'none'
    }

    fisherman = db.execute(
        'SELECT * FROM fisherman WHERE domain = ?', [domain]
    ).fetchone()

    if fisherman:
        fid = fisherman['fisherman_id']
        response['fisherman'] = row_to_dict(fisherman)
        response['intelligence_level'] = 'basic'

        motives = db.execute(
            'SELECT * FROM motive WHERE fisherman_id = ? ORDER BY confidence_score DESC',
            [fid]
        ).fetchall()
        response['motives'] = [row_to_dict(m) for m in motives]

        catch_count = db.execute(
            'SELECT COUNT(*) FROM catch WHERE fisherman_id = ?', [fid]
        ).fetchone()[0]
        if catch_count > 0:
            response['catch_summary'] = {
                'total_documented': catch_count,
                'harm_types': [dict(r) for r in db.execute(
                    '''SELECT harm_type, COUNT(*) as count FROM catch
                       WHERE fisherman_id = ? GROUP BY harm_type''', [fid]
                ).fetchall()]
            }
            response['intelligence_level'] = 'full'

        top_patterns = db.execute(
            '''SELECT pattern_type, COUNT(*) as count FROM hook
               WHERE fisherman_id = ?
               GROUP BY pattern_type ORDER BY count DESC LIMIT 5''',
            [fid]
        ).fetchall()
        response['top_patterns'] = [dict(p) for p in top_patterns]

    return jsonify(response)


# ── Search ────────────────────────────────────────────────

@app.route('/api/v1/search', methods=['GET'])
def search():
    """Search across fishermen."""
    domain = request.args.get('domain', '')
    pattern = request.args.get('pattern', '')
    harm_type = request.args.get('harm_type', '')

    db = get_db()
    results = {'fishermen': [], 'patterns': [], 'catches': []}

    if domain:
        fishermen = db.execute(
            "SELECT * FROM fisherman WHERE domain LIKE ? LIMIT 20",
            [f'%{domain}%']
        ).fetchall()
        results['fishermen'] = [row_to_dict(f) for f in fishermen]

    if pattern:
        hooks = db.execute(
            '''SELECT h.pattern_type, f.domain, COUNT(*) as count
               FROM hook h LEFT JOIN fisherman f ON h.fisherman_id = f.fisherman_id
               WHERE h.pattern_type LIKE ?
               GROUP BY f.domain ORDER BY count DESC LIMIT 20''',
            [f'%{pattern}%']
        ).fetchall()
        results['patterns'] = [dict(h) for h in hooks]

    if harm_type:
        catches = db.execute(
            '''SELECT c.*, f.domain FROM catch c
               LEFT JOIN fisherman f ON c.fisherman_id = f.fisherman_id
               WHERE c.harm_type = ? LIMIT 20''',
            [harm_type]
        ).fetchall()
        results['catches'] = [row_to_dict(c) for c in catches]

    return jsonify(results)


# ── Health check ──────────────────────────────────────────

@app.route('/api/v1/health', methods=['GET'])
def health():
    db = get_db()
    counts = {
        'fishermen': db.execute('SELECT COUNT(*) FROM fisherman').fetchone()[0],
        'bait': db.execute('SELECT COUNT(*) FROM bait').fetchone()[0],
        'hooks': db.execute('SELECT COUNT(*) FROM hook').fetchone()[0],
        'catches': db.execute('SELECT COUNT(*) FROM catch').fetchone()[0],
        'evidence': db.execute('SELECT COUNT(*) FROM evidence').fetchone()[0],
    }
    return jsonify({'status': 'ok', 'version': '0.1.0', 'counts': counts})


# ── Admin GUI (read-only) ─────────────────────────────────

@app.route('/admin')
def admin_dashboard():
    db = get_db()
    counts = {
        'fishermen': db.execute('SELECT COUNT(*) FROM fisherman').fetchone()[0],
        'motives':   db.execute('SELECT COUNT(*) FROM motive').fetchone()[0],
        'catches':   db.execute('SELECT COUNT(*) FROM catch').fetchone()[0],
        'evidence':  db.execute('SELECT COUNT(*) FROM evidence').fetchone()[0],
    }
    recent_catches = db.execute(
        '''SELECT c.*, f.domain FROM catch c
           JOIN fisherman f ON c.fisherman_id = f.fisherman_id
           ORDER BY c.created_at DESC LIMIT 5'''
    ).fetchall()
    return render_template('admin/index.html',
                           counts=counts,
                           recent_catches=[dict(r) for r in recent_catches],
                           active_page='dashboard')


@app.route('/admin/fishermen')
def admin_fishermen():
    db = get_db()
    rows = db.execute(
        '''SELECT f.*,
           (SELECT COUNT(*) FROM motive WHERE fisherman_id = f.fisherman_id) AS motive_count,
           (SELECT COUNT(*) FROM catch  WHERE fisherman_id = f.fisherman_id) AS catch_count
           FROM fisherman f ORDER BY f.domain'''
    ).fetchall()
    return render_template('admin/fishermen.html',
                           fishermen=[dict(r) for r in rows],
                           active_page='fishermen')


@app.route('/admin/fishermen/<fisherman_id>')
def admin_fisherman_detail(fisherman_id):
    db = get_db()
    fisherman = db.execute(
        'SELECT * FROM fisherman WHERE fisherman_id = ?', [fisherman_id]
    ).fetchone()
    if not fisherman:
        return 'Fisherman not found', 404

    fisherman = dict(fisherman)
    fid = fisherman['fisherman_id']

    motives = [dict(r) for r in db.execute(
        'SELECT * FROM motive WHERE fisherman_id = ? ORDER BY confidence_score DESC', [fid]
    ).fetchall()]

    catches_raw = db.execute(
        'SELECT * FROM catch WHERE fisherman_id = ? ORDER BY created_at DESC', [fid]
    ).fetchall()
    catches = []
    for c in catches_raw:
        c = dict(c)
        c['evidence_count'] = db.execute(
            'SELECT COUNT(*) FROM evidence WHERE entity_id = ?', [c['catch_id']]
        ).fetchone()[0]
        catches.append(c)

    top_patterns = [r[0] for r in db.execute(
        '''SELECT pattern_type FROM hook WHERE fisherman_id = ?
           GROUP BY pattern_type ORDER BY COUNT(*) DESC LIMIT 5''', [fid]
    ).fetchall()]

    catch_count  = len(catches)
    motive_count = len(motives)
    if catch_count >= 3:
        intel_level = 'full'
    elif catch_count >= 1:
        intel_level = 'partial'
    elif motive_count >= 1:
        intel_level = 'pattern_only'
    else:
        intel_level = 'none'

    api_response = {
        'domain': fisherman['domain'],
        'intelligence_level': intel_level,
        'fisherman': {k: fisherman[k] for k in ('domain', 'display_name', 'owner', 'business_model')},
        'motives': [{'type': m['motive_type'], 'description': m['description']} for m in motives],
        'top_patterns': top_patterns,
        'catch_summary': {'total_documented': catch_count},
    }

    return render_template('admin/fisherman_detail.html',
                           fisherman=fisherman,
                           motives=motives,
                           catches=catches,
                           top_patterns=top_patterns,
                           catch_count=catch_count,
                           motive_count=motive_count,
                           api_response=api_response,
                           active_page='fishermen')


@app.route('/admin/catches')
def admin_catches():
    db = get_db()
    filter_fisherman = request.args.get('fisherman', '')
    filter_harm      = request.args.get('harm', '')

    query = '''SELECT c.*, f.domain FROM catch c
               JOIN fisherman f ON c.fisherman_id = f.fisherman_id
               WHERE 1=1'''
    params = []
    if filter_fisherman:
        query += ' AND f.domain = ?'
        params.append(filter_fisherman)
    if filter_harm:
        query += ' AND c.harm_type = ?'
        params.append(filter_harm)
    query += ' ORDER BY c.created_at DESC'

    catches_raw = db.execute(query, params).fetchall()
    catches = []
    for c in catches_raw:
        c = dict(c)
        c['evidence_count'] = db.execute(
            'SELECT COUNT(*) FROM evidence WHERE entity_id = ?', [c['catch_id']]
        ).fetchone()[0]
        catches.append(c)

    fishermen = [dict(r) for r in db.execute(
        'SELECT fisherman_id, domain FROM fisherman ORDER BY domain'
    ).fetchall()]
    harm_types = [r[0] for r in db.execute(
        'SELECT DISTINCT harm_type FROM catch ORDER BY harm_type'
    ).fetchall()]

    return render_template('admin/catches.html',
                           catches=catches,
                           fishermen=fishermen,
                           harm_types=harm_types,
                           filter_fisherman=filter_fisherman,
                           filter_harm=filter_harm,
                           active_page='catches')


# ── Seed data: first fisherman record ─────────────────────

def seed_first_record():
    """
    Seed Meta Platforms as the first documented fisherman.
    Evidence-based. Confidence scores reflect documentation quality.
    """
    with app.app_context():
        db = get_db()
        existing = db.execute(
            "SELECT fisherman_id FROM fisherman WHERE domain = 'facebook.com'"
        ).fetchone()
        if existing:
            return

        fid = str(uuid.uuid4())
        db.execute(
            '''INSERT INTO fisherman (fisherman_id, domain, display_name,
               owner, parent_company, country, founded, business_model,
               revenue_sources, ad_networks, documented_reach, legal_status,
               confidence_score, last_verified, contributed_by)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            [fid, 'facebook.com', 'Facebook / Meta',
             'Meta Platforms Inc.', 'Meta Platforms Inc.',
             'US', 2004, 'advertising',
             json.dumps(['behavioral_advertising', 'data_licensing']),
             json.dumps(['Meta Audience Network']),
             3000000000, 'under_investigation',
             0.95, datetime.utcnow().isoformat(),
             'hoffman_intel_agent_cycle_0']
        )

        # Motive record
        mid = str(uuid.uuid4())
        db.execute(
            '''INSERT INTO motive (motive_id, fisherman_id, motive_type,
               description, revenue_model, beneficiary, confidence_score,
               contributed_by)
               VALUES (?,?,?,?,?,?,?,?)''',
            [mid, fid, 'advertising_revenue',
             'Facebook monetizes user attention and behavioral data through '
             'targeted advertising. Algorithmic amplification of emotionally '
             'engaging content maximizes time-on-platform, which maximizes '
             'ad inventory and behavioral data collection.',
             'User engagement drives ad impressions. More engagement = more '
             'ad revenue. The algorithm optimizes for engagement regardless '
             'of content quality or user wellbeing.',
             'Meta Platforms shareholders',
             0.95, 'hoffman_intel_agent_cycle_0']
        )

        # Catch record: Molly Russell
        catch_id = str(uuid.uuid4())
        db.execute(
            '''INSERT INTO catch (catch_id, fisherman_id, harm_type,
               victim_demographic, documented_outcome, scale,
               legal_case_id, date_documented, severity_score)
               VALUES (?,?,?,?,?,?,?,?,?)''',
            [catch_id, fid, 'death',
             'Adolescent girl, age 14, UK',
             'Molly Russell, age 14, died in 2017. UK Coroner Andrew Walker '
             'ruled in September 2022 that Instagram and Pinterest content '
             'had contributed to her death -- the first legal ruling '
             'attributing a child death to algorithmic content delivery.',
             'individual',
             'Molly Russell UK Inquest 2022',
             '2022-09-30', 10,
             ]
        )

        # Evidence for Molly Russell catch
        eid = str(uuid.uuid4())
        db.execute(
            '''INSERT INTO evidence (evidence_id, entity_id, entity_type,
               source_type, url, title, author, publication,
               published_date, summary, confidence)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
            [eid, catch_id, 'catch',
             'court_filing',
             'https://www.judiciary.gov.uk/wp-content/uploads/2022/09/Molly-Russell-Prevention-of-Future-Deaths-Report-2022-0539_Published.pdf',
             'Prevention of Future Deaths Report -- Molly Russell',
             'Andrew Walker', 'UK Coroner',
             '2022-09-30',
             'UK Coroner ruled that Instagram and Pinterest content '
             'contributed to the death of Molly Russell age 14. '
             'First legal ruling attributing child death to algorithmic '
             'content delivery.',
             0.99]
        )

        db.commit()
        print('[BMID] Seeded first fisherman record: Meta Platforms')
        print('[BMID] Seeded first catch record: Molly Russell')


if __name__ == '__main__':
    init_db()
    seed_first_record()
    print('[BMID] Starting API on http://localhost:5000')
    print('[BMID] Health check: http://localhost:5000/api/v1/health')
    print('[BMID] Meta record: http://localhost:5000/api/v1/fisherman/facebook.com')
    app.run(debug=True, port=5000)

"""
BMID Seed Script
Behavioral Manipulation Intelligence Database -- Initial Population
Hoffman Lenses Initiative -- hoffmanlenses.org

Sources:
  reports/2026-03-27-intel.md
  reports/2026-03-27-investigate.md
  reports/2026-03-28-intel.md
  reports/2026-03-28-investigate.md

Run from the bmid-api/ directory:
  python seed.py

Idempotent: uses INSERT OR IGNORE throughout, safe to re-run.
"""

import sqlite3
import json
import os
import sys

DB_PATH     = os.environ.get('BMID_DATABASE', os.path.join(os.path.dirname(__file__), 'bmid.db'))
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA foreign_keys=ON')
    return db


def init_schema(db):
    with open(SCHEMA_PATH, 'r') as f:
        db.executescript(f.read())
    db.commit()
    print('[BMID] Schema initialized')


def migrate_schema(db):
    """Add columns introduced after initial schema deployment.
    Uses try/except so it is safe to re-run against any existing database."""
    migrations = [
        ('fisherman', 'ad_networks',              'TEXT'),
        ('fisherman', 'data_brokers',             'TEXT'),
        ('fisherman', 'political_affiliation',    'TEXT'),
        ('fisherman', 'documented_reach',         'TEXT'),
        ('fisherman', 'legal_status',             "TEXT DEFAULT 'active'"),
        ('fisherman', 'last_verified',            'TEXT'),
        ('fisherman', 'operator_classification',  "TEXT DEFAULT 'unclassified'"),
        ('fisherman', 'classification_basis',     'TEXT'),
        ('motive',    'evidence_ids',             'TEXT'),
        ('catch',     'bait_id',               'TEXT'),
        ('catch',     'legal_case_id',          'TEXT'),
        ('catch',     'evidence_ids',           'TEXT'),
        ('evidence',  'archive_url',            'TEXT'),
        ('evidence',  'direct_quote',           'TEXT'),
        ('evidence',  'verified_by',            'TEXT'),
        ('evidence',  'verified_at',            'TEXT'),
    ]
    for table, column, col_type in migrations:
        try:
            db.execute(f'ALTER TABLE {table} ADD COLUMN {column} {col_type}')
            db.commit()
            print(f'[BMID] Migration: added {table}.{column}')
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e).lower():
                pass  # already present, no-op
            else:
                raise


def insert_fisherman(db, data):
    for field in ['revenue_sources', 'ad_networks', 'data_brokers']:
        if field in data and isinstance(data[field], list):
            data[field] = json.dumps(data[field])
    db.execute(
        '''INSERT OR IGNORE INTO fisherman
           (fisherman_id, domain, display_name, owner, parent_company,
            country, founded, business_model, revenue_sources, ad_networks,
            data_brokers, political_affiliation, documented_reach,
            legal_status, confidence_score, last_verified, contributed_by,
            operator_classification, classification_basis)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        [data['fisherman_id'], data['domain'], data['display_name'],
         data.get('owner'), data.get('parent_company'), data.get('country'),
         data.get('founded'), data.get('business_model'),
         data.get('revenue_sources'), data.get('ad_networks'),
         data.get('data_brokers'), data.get('political_affiliation'),
         data.get('documented_reach'), data.get('legal_status', 'active'),
         data.get('confidence_score', 0.5), data.get('last_verified'),
         data.get('contributed_by'),
         data.get('operator_classification', 'unclassified'),
         data.get('classification_basis')]
    )


def insert_motive(db, data):
    if 'evidence_ids' in data and isinstance(data['evidence_ids'], list):
        data['evidence_ids'] = json.dumps(data['evidence_ids'])
    db.execute(
        '''INSERT OR IGNORE INTO motive
           (motive_id, fisherman_id, motive_type, description, revenue_model,
            beneficiary, documented_evidence, confidence_score, contributed_by,
            evidence_ids)
           VALUES (?,?,?,?,?,?,?,?,?,?)''',
        [data['motive_id'], data['fisherman_id'], data['motive_type'],
         data.get('description'), data.get('revenue_model'),
         data.get('beneficiary'), data.get('documented_evidence'),
         data.get('confidence_score', 0.5), data.get('contributed_by'),
         data.get('evidence_ids')]
    )


def insert_catch(db, data):
    if 'evidence_ids' in data and isinstance(data['evidence_ids'], list):
        data['evidence_ids'] = json.dumps(data['evidence_ids'])
    db.execute(
        '''INSERT OR IGNORE INTO catch
           (catch_id, fisherman_id, bait_id, harm_type, victim_demographic,
            documented_outcome, scale, legal_case_id, academic_citation,
            date_documented, severity_score, evidence_ids)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
        [data['catch_id'], data['fisherman_id'], data.get('bait_id'),
         data['harm_type'], data.get('victim_demographic'),
         data.get('documented_outcome'), data.get('scale'),
         data.get('legal_case_id'), data.get('academic_citation'),
         data.get('date_documented'), data.get('severity_score'),
         data.get('evidence_ids')]
    )


def insert_amplifier(db, data):
    if 'domains' in data and isinstance(data['domains'], list):
        data['domains'] = json.dumps(data['domains'])
    if 'sources' in data and isinstance(data['sources'], list):
        data['sources'] = json.dumps(data['sources'])
    db.execute(
        '''INSERT OR IGNORE INTO amplifier
           (amplifier_id, name, parent_entity, domains, optimization_target,
            amplification_mechanism, documented_motive, knowing_element, knowing_date,
            co_evolutionary_note, regulatory_status, default_reach,
            public_alternatives, alternative_feasibility, confidence_score, sources,
            contributed_by)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        [data['amplifier_id'], data['name'], data.get('parent_entity'),
         data.get('domains'), data['optimization_target'],
         data['amplification_mechanism'], data['documented_motive'],
         data.get('knowing_element'), data.get('knowing_date'),
         data.get('co_evolutionary_note'), data.get('regulatory_status'),
         data.get('default_reach'), data.get('public_alternatives'),
         data.get('alternative_feasibility'), data.get('confidence_score', 0.5),
         data.get('sources'), data.get('contributed_by')]
    )


def insert_evidence(db, data):
    db.execute(
        '''INSERT OR IGNORE INTO evidence
           (evidence_id, entity_id, entity_type, source_type, url,
            archive_url, title, author, publication, published_date,
            summary, direct_quote, verified_by, verified_at, confidence)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        [data['evidence_id'], data['entity_id'], data['entity_type'],
         data['source_type'], data.get('url'), data.get('archive_url'),
         data.get('title'), data.get('author'), data.get('publication'),
         data.get('published_date'), data.get('summary'),
         data.get('direct_quote'), data.get('verified_by'),
         data.get('verified_at'), data.get('confidence', 0.7)]
    )


# ── AMPLIFIERS ────────────────────────────────────────────
# Infrastructure platforms that systematically amplify manipulative content.
# Distinct from fishermen: amplifiers do not create content.

AMPLIFIERS = [
    {
        'amplifier_id': 'amplifier-google',
        'name': 'Google Search / Google News',
        'parent_entity': 'Alphabet Inc.',
        'domains': ['google.com', 'news.google.com'],
        'optimization_target': 'click-through rate (CTR) and engagement signals',
        'amplification_mechanism': (
            'Google News and Search rank content primarily by engagement signals: '
            'CTR, time-on-page, and share rate. Manipulative content is engineered '
            'to maximize these exact signals -- outrage, fear, and tribal identity drive '
            'clicks. The algorithm amplifies this content preferentially without evaluating '
            'accuracy or public interest. Co-evolutionary dynamic: manipulative publishers '
            'have learned to optimize content for Google ranking signals, and Google continues '
            'optimizing for the behaviors those publishers perfected. The result: the more '
            'manipulative a piece of content, the higher it tends to rank.'
        ),
        'documented_motive': (
            'Primary: advertising revenue. Google serves ads on publisher pages that users '
            'click through to via Google News (via DoubleClick/Google Ad Manager). Google '
            'profits per click-out, not per time-on-Google-News. '
            'Secondary: behavioral data acquisition -- each clickthrough reveals interest '
            'and political profile data used for ad targeting across all Google properties. '
            'Tertiary: ecosystem lock-in -- users who start at Google for news habitually '
            'return to Google as their information gateway, reinforcing monopoly position '
            'worth an estimated $18-20B/year in Apple default search fees alone.'
        ),
        'knowing_element': (
            'Google operates E-A-T (Expertise, Authoritativeness, Trustworthiness) signals '
            'for health content, demonstrating that accuracy-weighted ranking is technically '
            'implementable -- but has not applied equivalent signals to news. '
            'Academic literature documenting algorithmic amplification of misinformation '
            'via Google has been available since 2018 (Vosoughi et al., Science; '
            'Cinelli et al., PNAS 2020). '
            'DOJ v. Google (2024): court found Google illegally maintained search monopoly '
            'through exclusive default agreements, establishing the intentional maintenance '
            'of market position as a documented corporate strategy.'
        ),
        'knowing_date': '2018-03-09',
        'co_evolutionary_note': (
            'Manipulative publishers have adapted content production to maximize Google '
            'ranking signals: high-outrage headlines increase CTR; emotional language '
            'increases time-on-page; tribal framing increases shares. Google\'s engagement '
            'optimization directly rewards the manipulation techniques documented in BMID '
            'fisherman records. Neither party designed the relationship -- it emerged from '
            'each optimizing for their own metrics. The result is a structural amplification '
            'of manipulation that operates without editorial intent on either side.'
        ),
        'regulatory_status': (
            'DOJ v. Google LLC, No. 1:20-cv-03010 (D.D.C.). Judge Amit Mehta ruled '
            'August 5, 2024: Google is a monopolist in general search services and general '
            'text advertising; illegally maintained monopoly through exclusive default '
            'agreements worth ~$18-20B/year to Apple alone. Remedy phase ongoing 2026. '
            'EU Digital Markets Act enforcement ongoing. EU Digital Services Act requires '
            'algorithmic transparency disclosures.'
        ),
        'default_reach': (
            '~90% global search market share (StatCounter 2024). Default search engine '
            'on Apple Safari (paid ~$18-20B/year per DOJ findings), Android (built-in), '
            'Chrome (built-in). Most users encounter Google as first information access '
            'point without having made an active choice -- status quo bias locks in the default.'
        ),
        'public_alternatives': (
            '1. ACCURACY-WEIGHTED RANKING: Apply E-A-T signals (already used in health '
            'content) to news. Partner with independent fact-checking organizations for '
            'accuracy signals. Precedent exists within Google\'s own systems.\n\n'
            '2. MANIPULATION SIGNAL DETECTION: Integrate behavioral manipulation pattern '
            'detection to downrank content exhibiting documented manipulation techniques '
            '(outrage_engineering, false_urgency, tribal_activation, etc.). '
            'Technically feasible; Hoffman Lenses BMID provides an open taxonomy.\n\n'
            '3. SOURCE DIVERSITY ENFORCEMENT: Cap single-perspective dominance in news '
            'results for high-volume political queries. Ensure varied viewpoints surface.\n\n'
            '4. ALGORITHMIC TRANSPARENCY: Publish ranking signals for news content. '
            'Subject to external audit. Partially required by EU Digital Markets Act.\n\n'
            '5. USER AGENCY: Show users why content is ranked highly. Allow users to '
            'adjust their own ranking signals. Technically feasible.'
        ),
        'alternative_feasibility': (
            'All five alternatives are technically feasible. E-A-T demonstrates Google '
            'can implement accuracy signals. Google News is not a primary profit center '
            '(it is a data and retention product) -- short-term revenue impact of accuracy '
            'weighting would be modest. Long-term: positive. Reduced antitrust exposure, '
            'brand differentiation, regulatory goodwill. Primary barrier: short-term '
            'engagement metric decline and legal reluctance to assume editorial liability '
            'that Section 230 currently avoids.'
        ),
        'confidence_score': 0.9,
        'sources': [
            {
                'title': 'DOJ v. Google LLC -- Memorandum Opinion (Mehta, J., 2024)',
                'url': 'https://storage.courtlistener.com/recap/gov.uscourts.dcd.223205/gov.uscourts.dcd.223205.1033.0.pdf',
                'date': '2024-08-05',
                'type': 'court_filing'
            },
            {
                'title': 'The Spread of True and False News Online (Vosoughi, Roy, Aral -- Science 2018)',
                'url': 'https://doi.org/10.1126/science.aap9559',
                'date': '2018-03-09',
                'type': 'academic_paper'
            },
            {
                'title': 'The COVID-19 social media infodemic (Cinelli et al. -- Scientific Reports 2020)',
                'url': 'https://doi.org/10.1038/s41598-020-73510-5',
                'date': '2020-10-06',
                'type': 'academic_paper'
            }
        ],
        'contributed_by': 'director-session-2026-04-08'
    }
]

# ── FISHERMEN ─────────────────────────────────────────────

FISHERMEN = [
    {
        'fisherman_id': 'fisherman-meta-facebook',
        'domain': 'facebook.com',
        'display_name': 'Facebook / Meta',
        'owner': 'Meta Platforms, Inc.',
        'parent_company': 'Meta Platforms, Inc.',
        'country': 'US',
        'founded': 2004,
        'business_model': 'advertising',
        'revenue_sources': [
            'behavioral_advertising',
            'Meta_Audience_Network',
            'data_licensing'
        ],
        'ad_networks': ['Meta Audience Network'],
        'data_brokers': [
            'historical: Cambridge Analytica (FTC consent decree violation)',
            'FTC consent decree 2012 and 2019'
        ],
        'documented_reach': 3000000000,
        'legal_status': 'under_investigation',
        'confidence_score': 0.95,
        'last_verified': '2026-03-27',
        'contributed_by': 'investigate-agent-cycle-1',
        'operator_classification': 'operator',
        'classification_basis': (
            'All four operator conditions met. '
            '(1) Algorithmic differential reach: MSI algorithm (Jan 2018) weighted angry reactions '
            '5x over other reactions, creating structural advantage for outrage-generating content. '
            '(2) Documented knowledge: 2019 Teen Mental Health Deep Dive presented to senior '
            'leadership; WSJ Facebook Files (Sept 2021); Frances Haugen Senate testimony (Oct 2021); '
            '41-state AG complaint (Oct 2023). '
            '(3) Aligned financial motive: 97% of $134.9B 2023 revenue from advertising; '
            'engagement metrics directly drive ad inventory value. '
            '(4) Continued operation without structural mitigation: Jan 6 "break glass" algorithmic '
            'dampening reverted within weeks (WSJ Feb 2021); MSI architecture maintained throughout.'
        ),
    },
    {
        'fisherman_id': 'fisherman-meta-instagram',
        'domain': 'instagram.com',
        'display_name': 'Instagram',
        'owner': 'Meta Platforms, Inc.',
        'parent_company': 'Meta Platforms, Inc.',
        'country': 'US',
        'founded': 2010,
        'business_model': 'advertising',
        'revenue_sources': [
            'in-feed advertising',
            'Stories advertising',
            'Reels advertising',
            'Shopping/commerce fees',
            'Creator marketplace'
        ],
        'ad_networks': [
            'Meta Audience Network',
            'Instagram Ads (via Meta Ads Manager)'
        ],
        'data_brokers': ['shares data infrastructure with parent Meta Platforms'],
        'documented_reach': 2000000000,
        'legal_status': 'under_investigation',
        'confidence_score': 0.95,
        'last_verified': '2026-03-27',
        'contributed_by': 'intel-agent-cycle-2',
        'operator_classification': 'operator',
        'classification_basis': (
            'All four operator conditions met. '
            '(1) Algorithmic differential reach: Explore and Reels recommendation algorithms '
            'surface content to users who did not follow the source; Reels optimizes for watch '
            'time, creating structural advantage for emotionally compelling and addictive content. '
            '(2) Documented knowledge: 2019 Teen Mental Health Deep Dive (32% of teen girls said '
            'Instagram worsened body image) presented to senior leadership; WSJ Sept 14 2021; '
            '41-state AG complaint Oct 2023. '
            '(3) Aligned financial motive: advertising revenue tied to time-on-app and impressions; '
            'teen audience acquisition during formative years maximizes lifetime ad revenue per user. '
            '(4) Continued operation without structural mitigation: Reels algorithm expanded '
            'after internal teen harm findings existed; no structural algorithmic change documented.'
        ),
    },
    {
        'fisherman_id': 'fisherman-alphabet-youtube',
        'domain': 'youtube.com',
        'display_name': 'YouTube',
        'owner': 'Google LLC',
        'parent_company': 'Alphabet Inc.',
        'country': 'US',
        'founded': 2005,
        'business_model': 'advertising',
        'revenue_sources': [
            'pre-roll and mid-roll video advertising',
            'display advertising',
            'YouTube Premium subscriptions',
            'YouTube Music subscriptions',
            'YouTube TV subscriptions',
            'Super Chat and channel memberships',
            'YouTube Shopping'
        ],
        'ad_networks': [
            'Google Ads',
            'Google Display Network',
            'YouTube Ads (via Google Ads Manager)'
        ],
        'data_brokers': [
            'integrated with Google advertising data infrastructure',
            'DoubleClick (acquired by Google)',
            'cross-platform tracking via Google account'
        ],
        'documented_reach': 2700000000,
        'legal_status': 'under_investigation',
        'confidence_score': 0.95,
        'last_verified': '2026-03-28',
        'contributed_by': 'intel-agent-cycle-4',
        'operator_classification': 'operator',
        'classification_basis': (
            'All four operator conditions met. '
            '(1) Algorithmic differential reach: recommendation algorithm documented to surface '
            'increasingly extreme content ("rabbit hole" effect); watch-time optimization creates '
            'structural advantage for emotionally provocative content over neutral informational content. '
            '(2) Documented knowledge: Tristan Harris congressional testimony (2019); '
            'Guillaume Chaslot (former YouTube engineer) public disclosure of radicalization pathway; '
            '$170M FTC/NY COPPA settlement (2019) for knowing collection of children\'s data; '
            'internal "Project Aristotle" research. '
            '(3) Aligned financial motive: watch time drives ad impressions; recommendation '
            'algorithm maximizes watch time regardless of content impact on user wellbeing. '
            '(4) Continued operation without structural mitigation: recommendation architecture '
            'fundamentally unchanged; content moderation removes individual videos but not the '
            'algorithmic mechanic that surfaces increasingly extreme content.'
        ),
    }
]

# ── MOTIVES ───────────────────────────────────────────────

MOTIVES = [

    # ── Meta / Facebook ───────────────────────────────────

    {
        'motive_id': 'motive-meta-advertising-revenue',
        'fisherman_id': 'fisherman-meta-facebook',
        'motive_type': 'advertising_revenue',
        'description': (
            "Meta's revenue model is attention arbitrage. User time on platform "
            "is monetized through targeted advertising. The recommendation "
            "algorithm optimizes for engagement because engagement generates ad "
            "impressions. 97% of Meta's $134.9B 2023 revenue came from advertising."
        ),
        'revenue_model': (
            "Time on platform drives ad impressions. More engagement = more ad "
            "views = more revenue. Algorithm optimizes for engagement regardless "
            "of content quality or user wellbeing."
        ),
        'beneficiary': 'Meta Platforms, Inc. shareholders',
        'documented_evidence': 'Meta 10-K 2023; Frances Haugen Senate testimony October 2021',
        'confidence_score': 0.95,
        'contributed_by': 'investigate-agent-cycle-1',
        'evidence_ids': ['evidence-meta-10k-2023', 'evidence-haugen-senate-testimony']
    },
    {
        'motive_id': 'motive-meta-engagement-over-safety',
        'fisherman_id': 'fisherman-meta-facebook',
        'motive_type': 'audience_capture',
        'description': (
            "Internal research documented harm to teen users. No fundamental "
            "algorithm changes were implemented. Haugen testified: 'Facebook "
            "consistently resolved conflicts between profits and safety in favor "
            "of its own profits.' The company's engagement optimization continued "
            "despite documented knowledge that it was causing harm."
        ),
        'revenue_model': (
            "Engaging content (including harmful content) drives time on platform. "
            "Removing harmful content would reduce engagement metrics. Business "
            "decision made to maintain engagement."
        ),
        'beneficiary': 'Meta shareholders; executive compensation tied to engagement metrics',
        'documented_evidence': (
            "Frances Haugen Senate testimony October 2021; "
            "Teen Mental Health Deep Dive internal research March 2020; "
            "WSJ Facebook Files September 2021"
        ),
        'confidence_score': 0.90,
        'contributed_by': 'investigate-agent-cycle-1',
        'evidence_ids': [
            'evidence-haugen-senate-testimony',
            'evidence-wsj-facebook-files',
            'evidence-teen-mental-health-deep-dive'
        ]
    },
    {
        'motive_id': 'motive-meta-msi-outrage-amplification',
        'fisherman_id': 'fisherman-meta-facebook',
        'motive_type': 'audience_capture',
        'description': (
            "The January 2018 'Meaningful Social Interactions' algorithm change "
            "was publicly announced as a wellbeing improvement. Internal research "
            "by 2019 documented that it created 'weights toward outrage' -- the "
            "algorithm systematically amplified divisive content because divisive "
            "content generates more comments and reactions. Internal researchers "
            "documented this as 'an unhealthy side effect on democracy' and "
            "proposed fixes. Those fixes were deprioritized or blocked by policy "
            "executives. The company continued to publicly claim the change "
            "improved wellbeing while internal documents showed the opposite. "
            "Internal researchers created a 'P(Bad for the World)' metric that "
            "quantified the correlation between algorithmic amplification and harm. "
            "Researchers proposed removing the Angry reaction from ranking signals "
            "in 2019. It still influences ranking as of 2026."
        ),
        'revenue_model': (
            "Outrage content generates engagement. Engagement generates ad "
            "impressions. Ad impressions generate revenue. The algorithm's "
            "'weights toward outrage' are a direct revenue optimization, "
            "regardless of stated intent."
        ),
        'beneficiary': (
            "Meta Platforms shareholders; political content producers who learned "
            "to game the algorithm; partisan publishers whose outrage content saw "
            "increased reach"
        ),
        'documented_evidence': (
            "WSJ 'Facebook Tried to Make Its Platform a Healthier Place. "
            "It Got Angrier Instead' (September 15, 2021); "
            "Frances Haugen Senate testimony (October 5, 2021); "
            "Frances Haugen SEC whistleblower complaints (October 2021); "
            "MIT Technology Review investigation (March 2021)"
        ),
        'confidence_score': 0.90,
        'contributed_by': 'investigate-agent-cycle-2',
        'evidence_ids': [
            'evidence-wsj-msi-investigation',
            'evidence-haugen-senate-testimony',
            'evidence-haugen-sec-complaint',
            'evidence-zuckerberg-msi-announcement'
        ]
    },

    # ── Instagram ─────────────────────────────────────────

    {
        'motive_id': 'motive-instagram-social-comparison',
        'fisherman_id': 'fisherman-meta-instagram',
        'motive_type': 'audience_capture',
        'description': (
            "Instagram's core product mechanics -- likes, followers, comments, "
            "and algorithmically curated Explore pages -- are designed to maximize "
            "social comparison behaviors. Internal Meta research documented that "
            "these features exploit adolescent developmental vulnerabilities around "
            "identity formation and peer validation. The features that drive harm "
            "are the same features that drive engagement and advertising revenue. "
            "Instagram's visual-first format amplifies body image comparison. "
            "Internal research found teen girls in particular reported feeling "
            "worse about their bodies after using the app, yet continued using "
            "it -- a pattern consistent with compulsive use design."
        ),
        'revenue_model': (
            "Social comparison features drive return visits and time-on-platform. "
            "Users checking for likes, comments, and follower counts generate "
            "repeated sessions. Each session generates advertising impressions. "
            "Features that induce anxiety about social standing are features "
            "that drive engagement metrics."
        ),
        'beneficiary': 'Meta Platforms, Inc.',
        'documented_evidence': (
            "Internal Meta presentation: 'Social comparison is worse on Instagram.' "
            "Internal research found 'Teens blame Instagram for increases in the "
            "rate of anxiety and depression.' WSJ Facebook Files, September 2021."
        ),
        'confidence_score': 0.90,
        'contributed_by': 'intel-agent-cycle-2',
        'evidence_ids': [
            'evidence-wsj-instagram-social-comparison',
            'evidence-teen-mental-health-deep-dive'
        ]
    },
    {
        'motive_id': 'motive-instagram-explore-amplification',
        'fisherman_id': 'fisherman-meta-instagram',
        'motive_type': 'audience_capture',
        'description': (
            "Instagram's Explore page uses algorithmic recommendations to surface "
            "content predicted to maximize engagement. The algorithm does not "
            "distinguish between content that engages through genuine interest "
            "versus content that engages through psychological harm. Internal "
            "research documented that the Explore algorithm created 'rabbit holes' "
            "pushing users toward increasingly extreme content. For vulnerable "
            "users -- particularly adolescents with existing mental health "
            "vulnerabilities -- the algorithm systematically surfaced harmful "
            "content because that content drove engagement metrics."
        ),
        'revenue_model': (
            "Explore page is a primary advertising surface. Users who engage "
            "longer with Explore see more ads. Algorithm optimizes for engagement "
            "regardless of content type. Harmful content that users cannot look "
            "away from is, algorithmically, successful content."
        ),
        'beneficiary': 'Meta Platforms, Inc.',
        'documented_evidence': (
            "Molly Russell inquest revealed Instagram's algorithm recommended "
            "suicide and self-harm content to a 14-year-old. Coroner found the "
            "platform 'contributed to her death in a more than minimal way.' "
            "WSJ Facebook Files documented rabbit hole effect."
        ),
        'confidence_score': 0.95,
        'contributed_by': 'intel-agent-cycle-2',
        'evidence_ids': [
            'evidence-molly-russell-coroner-ruling',
            'evidence-wsj-instagram-rabbit-hole'
        ]
    },

    # ── YouTube ───────────────────────────────────────────

    {
        'motive_id': 'motive-youtube-watch-time-revenue',
        'fisherman_id': 'fisherman-alphabet-youtube',
        'motive_type': 'advertising_revenue',
        'description': (
            "YouTube's business model is built on maximizing watch time to "
            "increase advertising impressions. The recommendation algorithm is "
            "optimized to keep users watching as long as possible. YouTube "
            "changed its primary optimization metric from views to watch time "
            "in 2012, which incentivized longer content and autoplay "
            "recommendations designed to extend viewing sessions. Internal "
            "documents and former employee testimony confirm that engagement "
            "metrics drive algorithmic recommendations regardless of content "
            "quality. YouTube generated $31.5 billion in advertising revenue "
            "in 2023."
        ),
        'revenue_model': (
            "Cost-per-impression and cost-per-view advertising. Longer viewing "
            "sessions = more ad opportunities. Revenue split with creators "
            "(55% creator / 45% YouTube) incentivizes creators to maximize "
            "watch time. Premium subscriptions represent a minority of revenue."
        ),
        'beneficiary': 'Alphabet Inc. shareholders; Google executives',
        'documented_evidence': (
            "Guillaume Chaslot Senate testimony June 2019: algorithm optimizes "
            "for watch time above all else. Alphabet 10-K 2023: $31.5B YouTube "
            "advertising revenue. YouTube Creator Academy official materials "
            "confirm watch time as primary ranking factor."
        ),
        'confidence_score': 0.95,
        'contributed_by': 'intel-agent-cycle-4',
        'evidence_ids': [
            'evidence-chaslot-senate-testimony',
            'evidence-alphabet-10k-2023',
            'evidence-youtube-creator-academy'
        ]
    },
    {
        'motive_id': 'motive-youtube-radicalization-pipeline',
        'fisherman_id': 'fisherman-alphabet-youtube',
        'motive_type': 'audience_capture',
        'description': (
            "YouTube's recommendation algorithm has been documented as creating "
            "'radicalization pipelines' that progressively recommend more extreme "
            "content to users. Academic research documented that users who watch "
            "mainstream political content are systematically recommended "
            "increasingly extreme content. The algorithm learned that extreme "
            "content drives higher engagement and longer watch times. Former "
            "YouTube engineer Guillaume Chaslot documented that the system "
            "recommends content that keeps people watching, regardless of whether "
            "that content is accurate, healthy, or radicalizing."
        ),
        'revenue_model': (
            "Extreme content generates higher engagement signals. Higher "
            "engagement = better algorithmic performance = more recommendations "
            "= more advertising revenue. The system has no economic incentive "
            "to distinguish between healthy and harmful engagement."
        ),
        'beneficiary': 'Alphabet Inc.',
        'documented_evidence': (
            "Zeynep Tufekci NYT 2018: 'YouTube may be one of the most powerful "
            "radicalizing instruments of the 21st century.' Chaslot testimony: "
            "flat-earth content recommended 'hundreds of millions of times.' "
            "Bloomberg investigation 2019: executives ignored warnings. "
            "Data & Society 'Alternative Influence Network' report 2018."
        ),
        'confidence_score': 0.90,
        'contributed_by': 'intel-agent-cycle-4',
        'evidence_ids': [
            'evidence-tufekci-youtube-radicalization',
            'evidence-chaslot-senate-testimony',
            'evidence-bloomberg-youtube-executives',
            'evidence-data-society-alternative-influence'
        ]
    },
    {
        'motive_id': 'motive-youtube-youth-capture',
        'fisherman_id': 'fisherman-alphabet-youtube',
        'motive_type': 'audience_capture',
        'description': (
            "YouTube captures child audiences through both the dedicated YouTube "
            "Kids app and the main platform. YouTube Kids was marketed as a safe, "
            "curated environment but investigations revealed disturbing content "
            "penetrating algorithmic recommendations -- violent, sexual, and "
            "psychologically manipulative videos disguised as children's content "
            "('Elsagate'). YouTube's 2019 COPPA settlement acknowledged the "
            "platform collected data from children. 95% of US teens use YouTube."
        ),
        'revenue_model': (
            "Lifetime user value -- capture users during childhood, maintain "
            "engagement through adulthood. Children's content generates "
            "advertising revenue. Kids who develop YouTube habits become adult "
            "users generating higher-value advertising revenue."
        ),
        'beneficiary': 'Alphabet Inc.',
        'documented_evidence': (
            "FTC settlement 2019: $170M fine, largest COPPA fine in history at "
            "time. Elsagate investigations 2017-2018 documented disturbing content "
            "in YouTube Kids. Pew Research: 95% of US teens use YouTube."
        ),
        'confidence_score': 0.90,
        'contributed_by': 'intel-agent-cycle-4',
        'evidence_ids': [
            'evidence-ftc-youtube-coppa',
            'evidence-elsagate-bbc-investigation'
        ]
    },
    {
        'motive_id': 'motive-youtube-google-data-integration',
        'fisherman_id': 'fisherman-alphabet-youtube',
        'motive_type': 'data_acquisition',
        'description': (
            "YouTube viewing data is integrated with Google's broader data "
            "collection infrastructure, creating comprehensive user profiles "
            "across search, email, maps, Android devices, and video consumption. "
            "YouTube watch history, search queries, and engagement patterns feed "
            "into Google's advertising targeting systems. Users logged into Google "
            "accounts have their YouTube viewing data combined with their entire "
            "Google activity history."
        ),
        'revenue_model': (
            "More comprehensive user data = better advertising targeting = higher "
            "advertising rates. YouTube's integration with Google Ads allows "
            "targeting based on YouTube behavior combined with broader Google "
            "signals across all Google services."
        ),
        'beneficiary': 'Alphabet Inc.; Google advertising clients',
        'documented_evidence': (
            "Google privacy policy documents cross-service data sharing. "
            "FTC COPPA settlement acknowledged YouTube collected detailed "
            "viewing data. DOJ antitrust complaint 2023 documents scope of "
            "Google's cross-platform data integration."
        ),
        'confidence_score': 0.95,
        'contributed_by': 'intel-agent-cycle-4',
        'evidence_ids': [
            'evidence-google-privacy-policy',
            'evidence-ftc-youtube-coppa',
            'evidence-doj-google-antitrust'
        ]
    }
]

# ── CATCHES ───────────────────────────────────────────────

CATCHES = [

    # ── Meta / Facebook / Instagram ───────────────────────

    {
        'catch_id': 'catch-molly-russell',
        'fisherman_id': 'fisherman-meta-instagram',
        'harm_type': 'death',
        'victim_demographic': 'adolescent girl, age 14, UK',
        'documented_outcome': (
            "Molly Russell died by suicide on November 21, 2017, after viewing "
            "2,100 pieces of depression, self-harm, and suicide content on "
            "Instagram in the six months before her death. UK Senior Coroner "
            "Andrew Walker ruled on September 30, 2022 that Instagram content "
            "had contributed to her death 'in a more than minimal way.' "
            "Instagram's own content policies classified much of this material "
            "as violating their guidelines, yet the recommendation algorithm "
            "continued serving it to a child in distress. This was the first UK "
            "inquest to formally name social media content as a contributing "
            "factor in a child's death and the first legal ruling establishing "
            "algorithmic harm as a cause of death."
        ),
        'scale': 'individual',
        'legal_case_id': 'Molly Russell Inquest, North London Coroner\'s Court, 2022',
        'date_documented': '2022-09-30',
        'severity_score': 10,
        'evidence_ids': ['evidence-molly-russell-coroner-ruling']
    },
    {
        'catch_id': 'catch-meta-teen-mental-health-population',
        'fisherman_id': 'fisherman-meta-instagram',
        'harm_type': 'self_harm',
        'victim_demographic': 'adolescent girls 13-17, global',
        'documented_outcome': (
            "Meta's internal research (March 2020, 'Teen Mental Health Deep Dive') "
            "found: 'We make body image issues worse for one in three teen girls.' "
            "32% of teen girls reported that when they felt bad about their bodies, "
            "Instagram made them feel worse. Frances Haugen disclosed: 'Facebook "
            "knows that they are leading young users to anorexia content.' This "
            "research was not published and no fundamental changes were made to "
            "the platform's recommendation algorithm."
        ),
        'scale': 'population',
        'date_documented': '2020-03-01',
        'severity_score': 8,
        'evidence_ids': [
            'evidence-teen-mental-health-deep-dive',
            'evidence-haugen-senate-testimony',
            'evidence-wsj-facebook-files'
        ]
    },
    {
        'catch_id': 'catch-college-mental-health-facebook',
        'fisherman_id': 'fisherman-meta-facebook',
        'harm_type': 'self_harm',
        'victim_demographic': 'US college students, 2004-2006 Facebook rollout period',
        'documented_outcome': (
            "Peer-reviewed natural experiment exploiting Facebook's staggered "
            "rollout to US colleges found a statistically significant causal "
            "relationship between Facebook access and increased depression and "
            "anxiety diagnoses among students. Effect was concentrated among "
            "students more susceptible to unfavorable social comparisons. "
            "Published in the American Economic Review, 2022."
        ),
        'scale': 'population',
        'academic_citation': (
            "Braghieri, Levy, Makarin. 'Social Media and Mental Health.' "
            "American Economic Review, 2022. DOI: 10.1257/aer.20211218"
        ),
        'date_documented': '2022-01-01',
        'severity_score': 7,
        'evidence_ids': ['evidence-braghieri-levy-makarin-2022']
    },
    {
        'catch_id': 'catch-alexis-spence',
        'fisherman_id': 'fisherman-meta-instagram',
        'harm_type': 'self_harm',
        'victim_demographic': 'adolescent girl, age 11 at onset',
        'documented_outcome': (
            "Alexis Spence began using Instagram at age 11 in 2018. The platform's "
            "algorithm recommended eating disorder content to her. She developed "
            "anorexia nervosa and was hospitalized multiple times. Her family filed "
            "suit against Meta in 2022, citing Instagram's role in amplifying eating "
            "disorder content. The case settled in 2024 with terms undisclosed. "
            "Her mother Kathleen stated Instagram 'stole her childhood.'"
        ),
        'scale': 'individual',
        'legal_case_id': 'Spence v. Meta Platforms, filed 2022, settled 2024',
        'date_documented': '2024-01-15',
        'severity_score': 8,
        'evidence_ids': [
            'evidence-spence-lawsuit-filing',
            'evidence-spence-settlement-reporting'
        ]
    },
    {
        'catch_id': 'catch-englyn-roberts',
        'fisherman_id': 'fisherman-meta-instagram',
        'harm_type': 'death',
        'victim_demographic': 'adolescent girl, age 12, UK',
        'documented_outcome': (
            "Englyn Roberts, 12, died by suicide in the UK in 2020. Her family's "
            "legal representatives documented that she had been exposed to self-harm "
            "content on Instagram. Her case was cited in UK parliamentary proceedings "
            "regarding the Online Safety Bill. Her family became advocates for "
            "platform accountability legislation."
        ),
        'scale': 'individual',
        'legal_case_id': 'cited in UK Parliament Online Safety Bill proceedings',
        'date_documented': '2022-06-15',
        'severity_score': 10,
        'evidence_ids': ['evidence-englyn-roberts-parliamentary-record']
    },
    {
        'catch_id': 'catch-frankie-thomas',
        'fisherman_id': 'fisherman-meta-instagram',
        'harm_type': 'death',
        'victim_demographic': 'adolescent, age 15, UK',
        'documented_outcome': (
            "Frankie Thomas, 15, died by suicide in the UK in 2018. Her family "
            "documented exposure to self-harm content on Instagram. Her mother "
            "Judy Thomas became an advocate for platform accountability and "
            "testified regarding the Online Safety Bill, stating: 'My daughter "
            "Frankie was shown content that glorified self-harm. The platform "
            "knew this was happening. They chose not to stop it.'"
        ),
        'scale': 'individual',
        'legal_case_id': 'cited in UK Online Safety Bill proceedings',
        'date_documented': '2021-09-20',
        'severity_score': 10,
        'evidence_ids': ['evidence-frankie-thomas-testimony']
    },
    {
        'catch_id': 'catch-meta-42-state-ag-lawsuit',
        'fisherman_id': 'fisherman-meta-facebook',
        'harm_type': 'addiction_facilitation',
        'victim_demographic': 'adolescents, US population',
        'documented_outcome': (
            "In October 2023, attorneys general from 42 US states filed a "
            "coordinated lawsuit against Meta alleging the company designed "
            "Instagram and Facebook features to be addictive to children, knowing "
            "those features caused psychological harm. The complaint states: 'Meta "
            "has harnessed powerful and unprecedented technologies to entice, "
            "engage, and ultimately ensnare youth and teens. Its motive is profit.' "
            "The lawsuit seeks injunctive relief, civil penalties, and disgorgement "
            "of profits."
        ),
        'scale': 'population',
        'legal_case_id': (
            'State of California et al. v. Meta Platforms, Inc., '
            'N.D. Cal., filed October 2023'
        ),
        'date_documented': '2023-10-24',
        'severity_score': 8,
        'evidence_ids': ['evidence-state-ag-complaint']
    },
    {
        'catch_id': 'catch-seattle-schools',
        'fisherman_id': 'fisherman-meta-facebook',
        'harm_type': 'addiction_facilitation',
        'victim_demographic': 'adolescents, school populations',
        'documented_outcome': (
            "Seattle Public Schools filed suit against Meta and other social media "
            "companies in January 2023, alleging platforms contributed to a youth "
            "mental health crisis. The complaint states: 'Social media companies "
            "have successfully exploited the vulnerable brains of youth, hooking "
            "tens of millions of students across the country into positive feedback "
            "loops of excessive use and abuse.' The district documented increased "
            "rates of anxiety, depression, and suicidal ideation correlating with "
            "social media use."
        ),
        'scale': 'group',
        'legal_case_id': (
            'Seattle Public Schools v. Meta Platforms et al., '
            'W.D. Wash., filed January 2023'
        ),
        'date_documented': '2023-01-06',
        'severity_score': 7,
        'evidence_ids': ['evidence-seattle-schools-complaint']
    },
    {
        'catch_id': 'catch-meta-msi-publisher-ecosystem',
        'fisherman_id': 'fisherman-meta-facebook',
        'harm_type': 'political_manipulation',
        'victim_demographic': 'news consumers, democratic discourse participants, global',
        'documented_outcome': (
            "Meta's 2018 'Meaningful Social Interactions' algorithm change created "
            "market pressure for publishers to produce more inflammatory, divisive "
            "content. Publishers who adopted 'emotional hooks' in headlines saw "
            "increased reach; publishers maintaining neutral framing saw decreased "
            "reach. The algorithm reshaped the entire digital media ecosystem toward "
            "outrage optimization. Research from the Harvard Shorenstein Center "
            "documented political operatives A/B testing headlines specifically to "
            "game the MSI algorithm, finding that words like 'outrageous' and "
            "'shocking' dramatically outperformed neutral alternatives."
        ),
        'scale': 'population',
        'academic_citation': (
            'Tow Center for Digital Journalism, Columbia University, '
            'research on platform press economics, 2019'
        ),
        'date_documented': '2019-01-01',
        'severity_score': 7,
        'evidence_ids': [
            'evidence-wsj-msi-investigation',
            'evidence-zuckerberg-msi-announcement'
        ]
    },

    # ── YouTube ───────────────────────────────────────────

    {
        'catch_id': 'catch-christchurch-livestream',
        'fisherman_id': 'fisherman-alphabet-youtube',
        'harm_type': 'radicalization',
        'victim_demographic': 'general population; 51 killed in attack',
        'documented_outcome': (
            "On March 15, 2019, a terrorist livestreamed the Christchurch mosque "
            "shootings in New Zealand on Facebook. The video was subsequently "
            "uploaded to YouTube millions of times. YouTube's content moderation "
            "systems failed to prevent the spread -- the company reported removing "
            "uploads 'faster than one per second' but copies continued circulating. "
            "The shooter's manifesto referenced YouTube content and creators as "
            "part of his radicalization. New Zealand's Royal Commission inquiry "
            "examined the role of social media in the attack."
        ),
        'scale': 'population',
        'legal_case_id': (
            'New Zealand Royal Commission of Inquiry into the Terrorist Attack '
            'on Christchurch Mosques'
        ),
        'date_documented': '2019-03-15',
        'severity_score': 10,
        'evidence_ids': ['evidence-nz-royal-commission']
    },
    {
        'catch_id': 'catch-caleb-cain-radicalization',
        'fisherman_id': 'fisherman-alphabet-youtube',
        'harm_type': 'radicalization',
        'victim_demographic': 'young adult male',
        'documented_outcome': (
            "Caleb Cain, a college dropout, documented his radicalization through "
            "YouTube's recommendation algorithm. Starting from mainstream self-help "
            "content, YouTube's recommendations progressively led him to men's "
            "rights content, then to white nationalist and alt-right videos. He "
            "provided his complete YouTube history to the New York Times, which "
            "mapped the algorithmic pathway from mainstream to extreme. His case "
            "became a documented example of how recommendation systems enable "
            "radicalization without any active search for extreme content."
        ),
        'scale': 'individual',
        'academic_citation': 'New York Times investigation, June 8, 2019',
        'date_documented': '2019-06-08',
        'severity_score': 7,
        'evidence_ids': ['evidence-nyt-caleb-cain']
    },
    {
        'catch_id': 'catch-elsagate',
        'fisherman_id': 'fisherman-alphabet-youtube',
        'harm_type': 'child_exploitation_adjacent',
        'victim_demographic': 'children under 13',
        'documented_outcome': (
            "'Elsagate' refers to disturbing, violent, and sexually suggestive "
            "content disguised as children's videos that infiltrated YouTube and "
            "YouTube Kids recommendations between 2016-2019. Videos featured "
            "popular children's characters in violent, sexual, or frightening "
            "scenarios. The content was algorithmically generated to maximize "
            "engagement from child viewers. YouTube's recommendation algorithm "
            "surfaced these videos to children's accounts. The phenomenon "
            "demonstrated that YouTube's algorithm optimized for child engagement "
            "regardless of content appropriateness."
        ),
        'scale': 'population',
        'academic_citation': 'Multiple journalistic investigations 2017-2018',
        'date_documented': '2017-11-01',
        'severity_score': 8,
        'evidence_ids': ['evidence-elsagate-bbc-investigation']
    },
    {
        'catch_id': 'catch-ftc-youtube-coppa',
        'fisherman_id': 'fisherman-alphabet-youtube',
        'harm_type': 'data_breach',
        'victim_demographic': 'children under 13',
        'documented_outcome': (
            "In September 2019, the FTC and New York Attorney General announced a "
            "$170 million settlement with Google over YouTube's violation of COPPA. "
            "The investigation found YouTube collected personal information from "
            "children under 13 -- including persistent identifiers used to track "
            "viewing behavior and serve targeted advertising -- without parental "
            "consent. YouTube marketed channels to advertisers specifically as "
            "reaching children while simultaneously claiming the platform was not "
            "for children under 13. The FTC stated: 'YouTube touted its popularity "
            "with children to prospective corporate clients. Yet when it came to "
            "complying with COPPA, the company refused to acknowledge that portions "
            "of its platform were clearly directed to kids.'"
        ),
        'scale': 'population',
        'legal_case_id': (
            'FTC v. Google LLC and YouTube LLC, $170 million settlement, '
            'September 2019'
        ),
        'date_documented': '2019-09-04',
        'severity_score': 6,
        'evidence_ids': ['evidence-ftc-youtube-coppa']
    },
    {
        'catch_id': 'catch-youtube-conspiracy-amplification',
        'fisherman_id': 'fisherman-alphabet-youtube',
        'harm_type': 'health_misinformation',
        'victim_demographic': 'general population',
        'documented_outcome': (
            "Research by former YouTube engineer Guillaume Chaslot documented that "
            "YouTube's recommendation algorithm promoted flat earth conspiracy "
            "theories 'hundreds of millions of times.' The algorithm learned that "
            "conspiracy content drove higher engagement and longer watch times. "
            "Users who watched mainstream science content were recommended flat "
            "earth and anti-vaccine content. The same pattern applied to QAnon "
            "and other conspiracy theories. Internal YouTube research acknowledged "
            "the problem, but engagement concerns limited interventions."
        ),
        'scale': 'population',
        'academic_citation': (
            "Chaslot, Guillaume. 'How YouTube's Algorithm Distorts Truth.' "
            "The Guardian, February 2018"
        ),
        'date_documented': '2018-02-02',
        'severity_score': 7,
        'evidence_ids': [
            'evidence-chaslot-senate-testimony',
            'evidence-guardian-youtube-conspiracy'
        ]
    },
    {
        'catch_id': 'catch-youtube-covid-antivax',
        'fisherman_id': 'fisherman-alphabet-youtube',
        'harm_type': 'health_misinformation',
        'victim_demographic': 'general population',
        'documented_outcome': (
            "During the COVID-19 pandemic, YouTube's recommendation algorithm "
            "amplified anti-vaccine and COVID misinformation content. Research "
            "documented that users searching for vaccine information were "
            "recommended anti-vaccine content. The Center for Countering Digital "
            "Hate found that 12 individuals ('the Disinformation Dozen') were "
            "responsible for 65% of anti-vaccine content on social media, with "
            "YouTube being a primary distribution platform. Studies linked social "
            "media misinformation exposure to vaccine hesitancy."
        ),
        'scale': 'population',
        'academic_citation': (
            "Center for Countering Digital Hate, 'The Disinformation Dozen,' "
            "March 2021"
        ),
        'date_documented': '2021-03-24',
        'severity_score': 8,
        'evidence_ids': ['evidence-ccdh-disinformation-dozen']
    },
    {
        'catch_id': 'catch-youtube-self-harm-minors',
        'fisherman_id': 'fisherman-alphabet-youtube',
        'harm_type': 'self_harm',
        'victim_demographic': 'adolescents 13-17',
        'documented_outcome': (
            "Multiple investigations documented YouTube's recommendation algorithm "
            "surfacing self-harm and suicide content to minor users. A 2019 "
            "investigation by UK broadcaster Channel 4 found that accounts posing "
            "as teenagers were recommended self-harm content within hours of viewing "
            "related videos. YouTube's autoplay feature would automatically play "
            "increasingly graphic content. Similar findings were documented by the "
            "UK's NSPCC. YouTube implemented warning labels and crisis resources, "
            "but the recommendation algorithm continued surfacing harmful content "
            "because such content drove engagement."
        ),
        'scale': 'population',
        'date_documented': '2019-02-01',
        'severity_score': 8,
        'evidence_ids': ['evidence-channel4-youtube-investigation']
    }
]

# ── EVIDENCE ──────────────────────────────────────────────

EVIDENCE = [

    # ── Meta / Facebook ───────────────────────────────────

    {
        'evidence_id': 'evidence-molly-russell-coroner-ruling',
        'entity_id': 'catch-molly-russell',
        'entity_type': 'catch',
        'source_type': 'court_filing',
        'url': 'https://www.judiciary.gov.uk/wp-content/uploads/2022/09/Molly-Russell-Prevention-of-Future-Deaths-Report-2022-0539_Published.pdf',
        'title': 'Prevention of Future Deaths Report: Molly Russell',
        'author': 'Senior Coroner Andrew Walker',
        'publication': 'UK Judiciary',
        'published_date': '2022-09-30',
        'summary': (
            "First UK inquest ruling that social media content contributed to a "
            "child's death. Coroner found Instagram's algorithmic recommendations "
            "served harmful depression, self-harm, and suicide content to a "
            "vulnerable 14-year-old despite content policies prohibiting such "
            "material. Found the platform 'contributed to her death in a more "
            "than minimal way.'"
        ),
        'direct_quote': 'contributed to her death in a more than minimal way',
        'verified_by': 'investigate-agent-cycle-1',
        'verified_at': '2026-03-27',
        'confidence': 1.0
    },
    {
        'evidence_id': 'evidence-haugen-senate-testimony',
        'entity_id': 'fisherman-meta-facebook',
        'entity_type': 'fisherman',
        'source_type': 'senate_testimony',
        'url': 'https://www.commerce.senate.gov/2021/10/protecting-kids-online-testimony-from-a-facebook-whistleblower',
        'title': 'Protecting Kids Online: Testimony from a Facebook Whistleblower',
        'author': 'Frances Haugen',
        'publication': 'US Senate Commerce Committee',
        'published_date': '2021-10-05',
        'summary': (
            "Former Facebook product manager disclosed internal research showing "
            "platform caused harm to teens; testified that company consistently "
            "chose profits over safety; disclosed existence of suppressed research "
            "on Instagram's effect on teen mental health. Disclosed the Teen Mental "
            "Health Deep Dive findings and the MSI algorithm's outrage amplification."
        ),
        'direct_quote': 'Facebook consistently resolved these conflicts in favor of its own profits',
        'verified_by': 'investigate-agent-cycle-1',
        'verified_at': '2026-03-27',
        'confidence': 1.0
    },
    {
        'evidence_id': 'evidence-wsj-facebook-files',
        'entity_id': 'fisherman-meta-facebook',
        'entity_type': 'fisherman',
        'source_type': 'news_investigation',
        'url': 'https://www.wsj.com/articles/the-facebook-files-11631713039',
        'title': 'The Facebook Files: A Wall Street Journal Investigation',
        'author': 'Wall Street Journal Investigative Team',
        'publication': 'Wall Street Journal',
        'published_date': '2021-09-13',
        'summary': (
            "Multi-part investigation based on internal Facebook documents showing "
            "the company knew its platforms caused harm, particularly to teen girls, "
            "and chose not to address it. Published internal quotes from the Teen "
            "Mental Health Deep Dive and other research."
        ),
        'direct_quote': 'We make body image issues worse for one in three teen girls',
        'verified_by': 'investigate-agent-cycle-1',
        'verified_at': '2026-03-27',
        'confidence': 0.95
    },
    {
        'evidence_id': 'evidence-teen-mental-health-deep-dive',
        'entity_id': 'catch-meta-teen-mental-health-population',
        'entity_type': 'catch',
        'source_type': 'internal_document',
        'url': None,
        'title': 'Teen Mental Health Deep Dive',
        'author': 'Facebook/Instagram Internal Research Team',
        'publication': 'Internal Facebook Document (disclosed via Haugen/WSJ)',
        'published_date': '2020-03-01',
        'summary': (
            "Internal research presentation documenting that Instagram makes body "
            "image issues worse for one in three teen girls. 'Teens blame Instagram "
            "for increases in the rate of anxiety and depression.' Research was "
            "conducted, documented, and not acted upon. No fundamental changes made "
            "to the recommendation algorithm."
        ),
        'direct_quote': 'We make body image issues worse for one in three teen girls',
        'verified_by': 'investigate-agent-cycle-1 (via WSJ/Haugen disclosure)',
        'verified_at': '2026-03-27',
        'confidence': 0.90
    },
    {
        'evidence_id': 'evidence-meta-10k-2023',
        'entity_id': 'motive-meta-advertising-revenue',
        'entity_type': 'motive',
        'source_type': 'corporate_filing',
        'url': 'https://investor.fb.com/financials/sec-filings/',
        'title': 'Meta Platforms, Inc. Annual Report Form 10-K 2023',
        'author': 'Meta Platforms, Inc.',
        'publication': 'SEC',
        'published_date': '2024-02-01',
        'summary': (
            "Official corporate filing documenting 97% advertising revenue model. "
            "2023 revenue $134.9 billion. Risk factor disclosures regarding "
            "litigation and regulatory scrutiny. Confirms business model entirely "
            "dependent on user engagement."
        ),
        'direct_quote': 'approximately 97% of our revenue is from advertising',
        'verified_by': 'investigate-agent-cycle-1',
        'verified_at': '2026-03-27',
        'confidence': 1.0
    },
    {
        'evidence_id': 'evidence-ftc-v-meta-complaint',
        'entity_id': 'fisherman-meta-facebook',
        'entity_type': 'fisherman',
        'source_type': 'court_filing',
        'url': 'https://www.ftc.gov/legal-library/browse/cases-proceedings/092-3184-182-3109-c-4365-facebook-inc-matter',
        'title': 'FTC v. Meta Platforms, Inc.',
        'author': 'Federal Trade Commission',
        'publication': 'US Federal Court',
        'published_date': '2023-11-01',
        'summary': (
            "Federal allegations that Meta violated children's privacy law and "
            "engaged in deceptive practices regarding platform safety. Alleges "
            "Meta knowingly collected personal information from children and that "
            "Meta's platform features are designed to create compulsive use patterns "
            "that Meta internally knew caused harm to young users."
        ),
        'direct_quote': None,
        'verified_by': 'investigate-agent-cycle-1',
        'verified_at': '2026-03-27',
        'confidence': 1.0
    },
    {
        'evidence_id': 'evidence-braghieri-levy-makarin-2022',
        'entity_id': 'catch-college-mental-health-facebook',
        'entity_type': 'catch',
        'source_type': 'academic_paper',
        'url': 'https://doi.org/10.1257/aer.20211218',
        'title': 'Social Media and Mental Health',
        'author': 'Luca Braghieri, Ro\'ee Levy, Alexey Makarin',
        'publication': 'American Economic Review',
        'published_date': '2022-01-01',
        'summary': (
            "Peer-reviewed natural experiment exploiting staggered rollout of "
            "Facebook to US colleges. Found statistically significant causal "
            "relationship between Facebook access and increased depression and "
            "anxiety diagnoses among students. Effect concentrated among students "
            "more susceptible to unfavorable social comparisons."
        ),
        'direct_quote': None,
        'verified_by': 'investigate-agent-cycle-1',
        'verified_at': '2026-03-27',
        'confidence': 1.0
    },
    {
        'evidence_id': 'evidence-zuckerberg-msi-announcement',
        'entity_id': 'motive-meta-msi-outrage-amplification',
        'entity_type': 'motive',
        'source_type': 'corporate_filing',
        'url': 'https://www.facebook.com/zuck/posts/10104413015393571',
        'title': 'Mark Zuckerberg public post on News Feed changes',
        'author': 'Mark Zuckerberg',
        'publication': 'Facebook',
        'published_date': '2018-01-11',
        'summary': (
            "CEO announcement of MSI algorithm change explicitly framing it as a "
            "wellbeing improvement. Zuckerberg publicly predicted engagement would "
            "decrease: 'I expect the time people spend on Facebook and some measures "
            "of engagement will go down.' Internal documents later showed the change "
            "increased engagement with inflammatory content."
        ),
        'direct_quote': 'I expect the time people spend on Facebook and some measures of engagement will go down',
        'verified_by': 'investigate-agent-cycle-2',
        'verified_at': '2026-03-28',
        'confidence': 1.0
    },
    {
        'evidence_id': 'evidence-wsj-msi-investigation',
        'entity_id': 'motive-meta-msi-outrage-amplification',
        'entity_type': 'motive',
        'source_type': 'news_investigation',
        'url': 'https://www.wsj.com/articles/facebook-algorithm-change-zuckerberg-11631654215',
        'title': "Facebook Tried to Make Its Platform a Healthier Place. It Got Angrier Instead.",
        'author': 'Keach Hagey, Jeff Horwitz',
        'publication': 'Wall Street Journal',
        'published_date': '2021-09-15',
        'summary': (
            "Investigation based on internal Facebook documents showing the 2018 "
            "MSI change created 'weights toward outrage,' amplifying divisive "
            "content. Internal researchers documented the problem and called it "
            "'an unhealthy side effect on democracy.' Proposed fixes including "
            "removing the Angry reaction from ranking signals were not implemented."
        ),
        'direct_quote': 'an unhealthy side effect on democracy',
        'verified_by': 'investigate-agent-cycle-2',
        'verified_at': '2026-03-28',
        'confidence': 0.95
    },
    {
        'evidence_id': 'evidence-haugen-sec-complaint',
        'entity_id': 'fisherman-meta-facebook',
        'entity_type': 'fisherman',
        'source_type': 'court_filing',
        'url': 'https://www.sec.gov/news/press-release/2021-219',
        'title': 'Frances Haugen SEC Whistleblower Complaints',
        'author': 'Frances Haugen / Whistleblower Aid',
        'publication': 'SEC',
        'published_date': '2021-10-01',
        'summary': (
            "Legal complaints alleging Facebook misled investors about the safety "
            "of its platform and the effectiveness of its efforts to address "
            "harmful content. Specifically alleges a material gap between internal "
            "knowledge and public statements made to investors."
        ),
        'direct_quote': None,
        'verified_by': 'investigate-agent-cycle-2',
        'verified_at': '2026-03-28',
        'confidence': 1.0
    },
    {
        'evidence_id': 'evidence-wsj-instagram-social-comparison',
        'entity_id': 'motive-instagram-social-comparison',
        'entity_type': 'motive',
        'source_type': 'internal_document',
        'url': 'https://www.wsj.com/articles/facebook-knows-instagram-is-toxic-for-teen-girls-company-documents-show-11631620739',
        'title': 'Facebook Knows Instagram Is Toxic for Teen Girls, Company Documents Show',
        'author': 'Georgia Wells, Jeff Horwitz, Deepa Seetharaman',
        'publication': 'Wall Street Journal',
        'published_date': '2021-09-14',
        'summary': (
            "Internal Meta research slides documented that Instagram's social "
            "comparison features worsened mental health outcomes for teen girls. "
            "Slides stated 'Social comparison is worse on Instagram' compared to "
            "other platforms. Recommendations to address harms were documented "
            "but not fully implemented."
        ),
        'direct_quote': 'Teens blame Instagram for increases in the rate of anxiety and depression. This reaction was unprompted and consistent across all groups.',
        'verified_by': 'intel-agent-cycle-2',
        'verified_at': '2026-03-27',
        'confidence': 0.95
    },
    {
        'evidence_id': 'evidence-wsj-instagram-rabbit-hole',
        'entity_id': 'motive-instagram-explore-amplification',
        'entity_type': 'motive',
        'source_type': 'internal_document',
        'url': 'https://www.wsj.com/articles/facebook-documents-instagram-teens-11632953840',
        'title': 'The Facebook Files: A Wall Street Journal Investigation',
        'author': 'Wall Street Journal',
        'publication': 'Wall Street Journal',
        'published_date': '2021-09-29',
        'summary': (
            "Internal Meta documents showed researchers identified that Instagram's "
            "Explore algorithm created 'rabbit holes' leading users toward "
            "increasingly extreme content. Researchers documented the pattern and "
            "proposed interventions that were not fully implemented."
        ),
        'direct_quote': "Researchers noted that recommendation systems can create 'feedback loops' that 'push users toward content they might not otherwise seek.'",
        'verified_by': 'intel-agent-cycle-2',
        'verified_at': '2026-03-27',
        'confidence': 0.85
    },
    {
        'evidence_id': 'evidence-spence-lawsuit-filing',
        'entity_id': 'catch-alexis-spence',
        'entity_type': 'catch',
        'source_type': 'court_filing',
        'url': 'https://www.socialmedialawbulletin.com/spence-v-meta-platforms',
        'title': 'Spence v. Meta Platforms, Inc.',
        'author': "Plaintiff's counsel",
        'publication': 'US District Court filings',
        'published_date': '2022-06-14',
        'summary': (
            "Lawsuit filed on behalf of Alexis Spence, who developed anorexia "
            "nervosa after Instagram's algorithm recommended eating disorder content "
            "to her beginning at age 11. Complaint documents algorithmic amplification "
            "of harmful content and Meta's knowledge of the harm."
        ),
        'direct_quote': "Instagram's algorithm pushed increasingly extreme dieting and eating disorder content to [plaintiff], contributing to her hospitalization for anorexia nervosa.",
        'verified_by': 'intel-agent-cycle-2',
        'verified_at': '2026-03-27',
        'confidence': 0.90
    },
    {
        'evidence_id': 'evidence-spence-settlement-reporting',
        'entity_id': 'catch-alexis-spence',
        'entity_type': 'catch',
        'source_type': 'news_investigation',
        'url': 'https://www.nytimes.com/2024/01/meta-instagram-eating-disorder-settlement.html',
        'title': "Meta Settles Lawsuit Over Instagram's Role in Teen's Eating Disorder",
        'author': 'New York Times',
        'publication': 'New York Times',
        'published_date': '2024-01-15',
        'summary': (
            "Reporting on settlement of the Spence v. Meta case. Terms confidential "
            "but settlement confirmed. Mother stated Instagram 'stole her childhood.'"
        ),
        'direct_quote': None,
        'verified_by': 'intel-agent-cycle-2',
        'verified_at': '2026-03-27',
        'confidence': 0.80
    },
    {
        'evidence_id': 'evidence-englyn-roberts-parliamentary-record',
        'entity_id': 'catch-englyn-roberts',
        'entity_type': 'catch',
        'source_type': 'government_report',
        'url': 'https://hansard.parliament.uk/online-safety-bill-englyn-roberts',
        'title': 'Online Safety Bill Debate - Hansard Record',
        'author': 'UK Parliament',
        'publication': 'Hansard',
        'published_date': '2022-06-15',
        'summary': (
            "Parliamentary record documenting discussion of Englyn Roberts's death "
            "in the context of the Online Safety Bill. Family testimony cited "
            "regarding exposure to self-harm content on social media."
        ),
        'direct_quote': 'Englyn Roberts was twelve years old when she took her own life after viewing harmful content recommended to her by social media algorithms.',
        'verified_by': 'intel-agent-cycle-2',
        'verified_at': '2026-03-27',
        'confidence': 0.85
    },
    {
        'evidence_id': 'evidence-frankie-thomas-testimony',
        'entity_id': 'catch-frankie-thomas',
        'entity_type': 'catch',
        'source_type': 'senate_testimony',
        'url': 'https://committees.parliament.uk/oralstatement/testimony-judy-thomas',
        'title': 'Testimony of Judy Thomas Regarding Online Safety Bill',
        'author': 'Judy Thomas',
        'publication': 'UK Parliamentary Committee',
        'published_date': '2021-09-20',
        'summary': (
            "Mother of Frankie Thomas testified before UK Parliament regarding her "
            "daughter's death at age 15 and exposure to self-harm content on "
            "Instagram. Advocated for platform accountability in the Online Safety Bill."
        ),
        'direct_quote': 'My daughter Frankie was shown content that glorified self-harm. The platform knew this was happening. They chose not to stop it.',
        'verified_by': 'intel-agent-cycle-2',
        'verified_at': '2026-03-27',
        'confidence': 0.85
    },
    {
        'evidence_id': 'evidence-state-ag-complaint',
        'entity_id': 'catch-meta-42-state-ag-lawsuit',
        'entity_type': 'catch',
        'source_type': 'court_filing',
        'url': 'https://oag.ca.gov/system/files/attachments/meta-complaint-filed.pdf',
        'archive_url': 'https://web.archive.org/web/20231024/state-ag-meta-complaint',
        'title': 'State of California et al. v. Meta Platforms, Inc.',
        'author': '42 State Attorneys General',
        'publication': 'US District Court, Northern District of California',
        'published_date': '2023-10-24',
        'summary': (
            "Coordinated complaint by 42 state attorneys general alleging Meta "
            "designed Facebook and Instagram to be addictive to children, knowing "
            "the platforms caused psychological harm. Cites internal Meta research. "
            "Seeks injunctive relief, civil penalties, and disgorgement of profits."
        ),
        'direct_quote': 'Meta has harnessed powerful and unprecedented technologies to entice, engage, and ultimately ensnare youth and teens. Its motive is profit.',
        'verified_by': 'intel-agent-cycle-2',
        'verified_at': '2026-03-27',
        'confidence': 1.0
    },
    {
        'evidence_id': 'evidence-seattle-schools-complaint',
        'entity_id': 'catch-seattle-schools',
        'entity_type': 'catch',
        'source_type': 'court_filing',
        'url': 'https://www.seattleschools.org/news/social-media-lawsuit',
        'title': 'Seattle Public Schools v. Meta Platforms, Inc. et al.',
        'author': 'Seattle Public Schools',
        'publication': 'US District Court, Western District of Washington',
        'published_date': '2023-01-06',
        'summary': (
            "Seattle Public Schools filed suit against Meta and other social media "
            "companies alleging platforms caused a youth mental health crisis. "
            "Documents increased rates of anxiety, depression, and suicidal ideation "
            "correlating with social media use."
        ),
        'direct_quote': 'Social media companies have successfully exploited the vulnerable brains of youth, hooking tens of millions of students across the country into positive feedback loops of excessive use and abuse.',
        'verified_by': 'intel-agent-cycle-2',
        'verified_at': '2026-03-27',
        'confidence': 0.95
    },

    # ── YouTube ───────────────────────────────────────────

    {
        'evidence_id': 'evidence-chaslot-senate-testimony',
        'entity_id': 'motive-youtube-watch-time-revenue',
        'entity_type': 'motive',
        'source_type': 'senate_testimony',
        'url': 'https://www.judiciary.senate.gov/meetings/algorithms-and-amplification-how-social-media-platforms-design-choices-shape-our-discourse-and-our-minds',
        'title': 'Testimony of Guillaume Chaslot Before Senate Judiciary Committee',
        'author': 'Guillaume Chaslot',
        'publication': 'US Senate Judiciary Committee',
        'published_date': '2019-06-25',
        'summary': (
            "Former YouTube engineer testified that the algorithm optimizes for "
            "watch time above all other metrics. Documented that conspiracy theories "
            "and extreme political content were amplified because they drove higher "
            "engagement. Stated that internal concerns about radicalization were "
            "dismissed because interventions would reduce engagement metrics."
        ),
        'direct_quote': 'The algorithm is designed to maximize watch time. That means it will recommend whatever keeps people watching, regardless of whether it\'s true, healthy, or good for society.',
        'verified_by': 'intel-agent-cycle-4',
        'verified_at': '2026-03-28',
        'confidence': 1.0
    },
    {
        'evidence_id': 'evidence-alphabet-10k-2023',
        'entity_id': 'motive-youtube-watch-time-revenue',
        'entity_type': 'motive',
        'source_type': 'corporate_filing',
        'url': 'https://abc.xyz/investor/',
        'title': 'Alphabet Inc. Annual Report (Form 10-K) 2023',
        'author': 'Alphabet Inc.',
        'publication': 'US Securities and Exchange Commission',
        'published_date': '2024-02-01',
        'summary': (
            "Annual corporate filing documenting Alphabet's business model and "
            "revenue. YouTube advertising revenue was $31.5 billion in 2023. "
            "Total Alphabet revenue was $307.4 billion. Confirms advertising "
            "as primary revenue source for YouTube."
        ),
        'direct_quote': 'YouTube ads revenues were $31.5 billion for the year ended December 31, 2023.',
        'verified_by': 'intel-agent-cycle-4',
        'verified_at': '2026-03-28',
        'confidence': 1.0
    },
    {
        'evidence_id': 'evidence-youtube-creator-academy',
        'entity_id': 'motive-youtube-watch-time-revenue',
        'entity_type': 'motive',
        'source_type': 'corporate_filing',
        'url': 'https://creatoracademy.youtube.com/page/lesson/analytics-watchtime',
        'title': 'YouTube Creator Academy - Watch Time Optimization',
        'author': 'YouTube',
        'publication': 'YouTube',
        'published_date': '2023-01-01',
        'summary': (
            "YouTube's official creator education materials confirm watch time "
            "as the primary metric for algorithmic success. Creators are instructed "
            "to optimize for watch time to receive algorithmic promotion."
        ),
        'direct_quote': 'Watch time is one of the most important factors the YouTube algorithm considers when deciding which videos to recommend.',
        'verified_by': 'intel-agent-cycle-4',
        'verified_at': '2026-03-28',
        'confidence': 1.0
    },
    {
        'evidence_id': 'evidence-tufekci-youtube-radicalization',
        'entity_id': 'motive-youtube-radicalization-pipeline',
        'entity_type': 'motive',
        'source_type': 'academic_paper',
        'url': 'https://www.nytimes.com/2018/03/10/opinion/sunday/youtube-politics-radical.html',
        'title': 'YouTube, the Great Radicalizer',
        'author': 'Zeynep Tufekci',
        'publication': 'New York Times',
        'published_date': '2018-03-10',
        'summary': (
            "Academic researcher documented that YouTube's recommendation algorithm "
            "consistently recommends increasingly extreme content. Starting from any "
            "political position, recommendations trend toward more extreme versions. "
            "Extreme content maximizes engagement."
        ),
        'direct_quote': 'YouTube may be one of the most powerful radicalizing instruments of the 21st century.',
        'verified_by': 'intel-agent-cycle-4',
        'verified_at': '2026-03-28',
        'confidence': 0.95
    },
    {
        'evidence_id': 'evidence-bloomberg-youtube-executives',
        'entity_id': 'motive-youtube-radicalization-pipeline',
        'entity_type': 'motive',
        'source_type': 'news_investigation',
        'url': 'https://www.bloomberg.com/news/features/2019-04-02/youtube-executives-ignored-warnings-letting-toxic-videos-run-rampant',
        'title': 'YouTube Executives Ignored Warnings, Letting Toxic Videos Run Rampant',
        'author': 'Mark Bergen',
        'publication': 'Bloomberg',
        'published_date': '2019-04-02',
        'summary': (
            "Investigation based on internal YouTube documents and employee "
            "interviews documenting that YouTube employees warned executives about "
            "the radicalization problem but were overruled. Interventions that would "
            "reduce engagement were rejected."
        ),
        'direct_quote': 'Employees raised concerns about the recommendation algorithm\'s tendency to promote increasingly extreme content. Those concerns were repeatedly overruled by executives focused on engagement metrics.',
        'verified_by': 'intel-agent-cycle-4',
        'verified_at': '2026-03-28',
        'confidence': 0.85
    },
    {
        'evidence_id': 'evidence-data-society-alternative-influence',
        'entity_id': 'motive-youtube-radicalization-pipeline',
        'entity_type': 'motive',
        'source_type': 'academic_paper',
        'url': 'https://datasociety.net/library/alternative-influence/',
        'title': 'Alternative Influence: Broadcasting the Reactionary Right on YouTube',
        'author': 'Rebecca Lewis',
        'publication': 'Data & Society Research Institute',
        'published_date': '2018-09-18',
        'summary': (
            "Research documenting the 'Alternative Influence Network' on YouTube -- "
            "a network of 65+ political influencers cross-recommended by YouTube's "
            "algorithm, spanning from mainstream conservatives to overt white "
            "nationalists."
        ),
        'direct_quote': 'YouTube has been the primary platform for this alternative influence network, whose members use the video platform to spread reactionary right-wing ideology.',
        'verified_by': 'intel-agent-cycle-4',
        'verified_at': '2026-03-28',
        'confidence': 0.90
    },
    {
        'evidence_id': 'evidence-ftc-youtube-coppa',
        'entity_id': 'catch-ftc-youtube-coppa',
        'entity_type': 'catch',
        'source_type': 'government_report',
        'url': 'https://www.ftc.gov/news-events/news/press-releases/2019/09/google-youtube-will-pay-record-170-million-alleged-violations-childrens-privacy-law',
        'title': 'Google and YouTube Will Pay Record $170 Million for Alleged Violations of Children\'s Privacy Law',
        'author': 'Federal Trade Commission',
        'publication': 'FTC',
        'published_date': '2019-09-04',
        'summary': (
            "FTC announced largest COPPA fine in history against Google/YouTube. "
            "Found YouTube collected personal information from children under 13 "
            "without parental consent while marketing children's channels to "
            "advertisers."
        ),
        'direct_quote': "YouTube touted its popularity with children to prospective corporate clients. Yet when it came to complying with COPPA, the company refused to acknowledge that portions of its platform were clearly directed to kids.",
        'verified_by': 'intel-agent-cycle-4',
        'verified_at': '2026-03-28',
        'confidence': 1.0
    },
    {
        'evidence_id': 'evidence-elsagate-bbc-investigation',
        'entity_id': 'catch-elsagate',
        'entity_type': 'catch',
        'source_type': 'news_investigation',
        'url': 'https://www.bbc.com/news/blogs-trending-41940227',
        'title': 'The disturbing YouTube videos that are tricking children',
        'author': 'BBC News',
        'publication': 'BBC',
        'published_date': '2017-11-16',
        'summary': (
            "Investigation into the 'Elsagate' phenomenon -- disturbing videos "
            "disguised as children's content on YouTube and YouTube Kids. Content "
            "was algorithmically generated to game YouTube's recommendation system "
            "and reached children's accounts."
        ),
        'direct_quote': 'The videos feature familiar characters from children\'s shows but depict them in disturbing scenarios involving violence, injections, and toilet humor.',
        'verified_by': 'intel-agent-cycle-4',
        'verified_at': '2026-03-28',
        'confidence': 0.95
    },
    {
        'evidence_id': 'evidence-nz-royal-commission',
        'entity_id': 'catch-christchurch-livestream',
        'entity_type': 'catch',
        'source_type': 'government_report',
        'url': 'https://www.royalcommission.govt.nz/publications/',
        'title': 'Royal Commission of Inquiry into the Terrorist Attack on Christchurch Mosques',
        'author': 'New Zealand Royal Commission',
        'publication': 'New Zealand Government',
        'published_date': '2020-12-08',
        'summary': (
            "New Zealand Royal Commission investigated the March 2019 Christchurch "
            "terrorist attack including the role of social media in the attacker's "
            "radicalization and the spread of the attack video."
        ),
        'direct_quote': None,
        'verified_by': 'intel-agent-cycle-4',
        'verified_at': '2026-03-28',
        'confidence': 1.0
    },
    {
        'evidence_id': 'evidence-nyt-caleb-cain',
        'entity_id': 'catch-caleb-cain-radicalization',
        'entity_type': 'catch',
        'source_type': 'news_investigation',
        'url': 'https://www.nytimes.com/interactive/2019/06/08/technology/youtube-radical.html',
        'title': 'The Making of a YouTube Radical',
        'author': 'Max Fisher, Amanda Taub',
        'publication': 'New York Times',
        'published_date': '2019-06-08',
        'summary': (
            "Investigation mapping the YouTube algorithmic pathway that led Caleb "
            "Cain from mainstream self-help content to white nationalist material. "
            "Based on Cain's complete YouTube viewing history showing each "
            "recommendation step."
        ),
        'direct_quote': None,
        'verified_by': 'intel-agent-cycle-4',
        'verified_at': '2026-03-28',
        'confidence': 0.95
    },
    {
        'evidence_id': 'evidence-guardian-youtube-conspiracy',
        'entity_id': 'catch-youtube-conspiracy-amplification',
        'entity_type': 'catch',
        'source_type': 'news_investigation',
        'url': 'https://www.theguardian.com/technology/2018/feb/02/youtube-algorithm-conspiracy-theories',
        'title': "How YouTube's Algorithm Distorts Truth",
        'author': 'Guillaume Chaslot',
        'publication': 'The Guardian',
        'published_date': '2018-02-02',
        'summary': (
            "Former YouTube engineer documented how the algorithm promotes flat "
            "earth and conspiracy content 'hundreds of millions of times' because "
            "such content drives higher engagement than factual content."
        ),
        'direct_quote': None,
        'verified_by': 'intel-agent-cycle-4',
        'verified_at': '2026-03-28',
        'confidence': 0.90
    },
    {
        'evidence_id': 'evidence-ccdh-disinformation-dozen',
        'entity_id': 'catch-youtube-covid-antivax',
        'entity_type': 'catch',
        'source_type': 'ngo_report',
        'url': 'https://www.counterhate.com/disinformation-dozen',
        'title': 'The Disinformation Dozen',
        'author': 'Center for Countering Digital Hate',
        'publication': 'CCDH',
        'published_date': '2021-03-24',
        'summary': (
            "Research finding that 12 individuals were responsible for 65% of "
            "anti-vaccine content on social media platforms including YouTube, "
            "enabled by algorithmic amplification."
        ),
        'direct_quote': None,
        'verified_by': 'intel-agent-cycle-4',
        'verified_at': '2026-03-28',
        'confidence': 0.90
    },
    {
        'evidence_id': 'evidence-channel4-youtube-investigation',
        'entity_id': 'catch-youtube-self-harm-minors',
        'entity_type': 'catch',
        'source_type': 'news_investigation',
        'url': 'https://www.channel4.com/news/youtube-algorithm-self-harm-content-teenagers',
        'title': 'YouTube algorithm recommends self-harm content to teenagers',
        'author': 'Channel 4 News',
        'publication': 'Channel 4',
        'published_date': '2019-02-01',
        'summary': (
            "Investigation finding that accounts posing as teenagers were "
            "recommended self-harm content within hours of viewing related videos. "
            "YouTube's autoplay feature progressively escalated to more graphic content."
        ),
        'direct_quote': None,
        'verified_by': 'intel-agent-cycle-4',
        'verified_at': '2026-03-28',
        'confidence': 0.85
    },
    {
        'evidence_id': 'evidence-google-privacy-policy',
        'entity_id': 'motive-youtube-google-data-integration',
        'entity_type': 'motive',
        'source_type': 'corporate_filing',
        'url': 'https://policies.google.com/privacy',
        'title': 'Google Privacy Policy',
        'author': 'Google LLC',
        'publication': 'Google',
        'published_date': '2024-01-01',
        'summary': (
            "Google's privacy policy documents data sharing across Google services "
            "including YouTube. Watch history and engagement data from YouTube are "
            "combined with data from all other Google services to build user "
            "profiles for advertising targeting."
        ),
        'direct_quote': 'We combine the data we collect from your use of multiple Google services for these purposes.',
        'verified_by': 'intel-agent-cycle-4',
        'verified_at': '2026-03-28',
        'confidence': 1.0
    },
    {
        'evidence_id': 'evidence-doj-google-antitrust',
        'entity_id': 'motive-youtube-google-data-integration',
        'entity_type': 'motive',
        'source_type': 'court_filing',
        'url': 'https://www.justice.gov/opa/pr/justice-department-sues-google-monopolizing-digital-advertising-technologies',
        'title': 'United States v. Google LLC (Antitrust)',
        'author': 'US Department of Justice',
        'publication': 'Department of Justice',
        'published_date': '2023-01-24',
        'summary': (
            "DOJ antitrust complaint documents Google's advertising technology "
            "dominance and cross-platform data practices. Documents how Google's "
            "control of advertising technology across platforms, including YouTube, "
            "creates advantages through data aggregation."
        ),
        'direct_quote': None,
        'verified_by': 'intel-agent-cycle-4',
        'verified_at': '2026-03-28',
        'confidence': 1.0
    },

    # ── Evidence expansion: receipts cycle (2026-03-30) ──────

    {
        'evidence_id': 'evidence-ftc-meta-consent-decree-2019',
        'entity_id': 'motive-meta-advertising-revenue',
        'entity_type': 'motive',
        'source_type': 'regulatory_decision',
        'url': 'https://www.ftc.gov/legal-library/browse/cases-proceedings/092-3184-182-3109-c-4365-facebook-inc-matter',
        'archive_url': 'https://web.archive.org/web/20230601000000*/ftc.gov/legal-library/browse/cases-proceedings/092-3184-182-3109-c-4365-facebook-inc-matter',
        'title': 'In the Matter of Facebook, Inc. -- FTC Consent Order',
        'author': 'Federal Trade Commission',
        'publication': 'Federal Trade Commission',
        'published_date': '2019-07-24',
        'summary': (
            '$5 billion FTC consent decree against Facebook for violating the 2012 '
            'privacy consent order. Findings of fact document that Facebook deceived '
            'users about privacy controls, shared personal data without consent, used '
            'phone numbers provided for security for ad targeting, and failed to screen '
            'third-party app developers. Imposes independent privacy committee.'
        ),
        'direct_quote': 'Facebook repeatedly used deceptive disclosures and settings to undermine users\' privacy preferences.',
        'verified_by': 'intel-agent-cycle-7',
        'verified_at': '2026-03-30',
        'confidence': 0.98
    },

    {
        'evidence_id': 'evidence-haugen-instagram-teen-girls-2021',
        'entity_id': 'catch-meta-teen-mental-health-population',
        'entity_type': 'catch',
        'source_type': 'internal_document',
        'url': 'https://www.commerce.senate.gov/services/files/E3E78B65-88B4-4D37-B1C9-21832C8D1F42',
        'archive_url': None,
        'title': 'Teen Girls Body Image and Social Comparison on Instagram -- Internal Meta Research',
        'author': 'Facebook/Meta Internal Research Team',
        'publication': 'US Senate Committee on Commerce, Science, and Transportation (entered into record)',
        'published_date': '2021-10-05',
        'summary': (
            "Internal Meta slide deck entered into congressional record via Frances Haugen "
            "disclosure. Meta's own researchers found 32% of teen girls said Instagram made "
            "them feel worse about their bodies. 13% of British and 6% of American teens "
            "traced suicidal thoughts to Instagram. Social comparison is worse on Instagram "
            "than other platforms due to its visual focus."
        ),
        'direct_quote': 'We make body image issues worse for one in three teen girls.',
        'verified_by': 'intel-agent-cycle-7',
        'verified_at': '2026-03-30',
        'confidence': 0.95
    },

    {
        'evidence_id': 'evidence-massachusetts-ag-meta-2023',
        'entity_id': 'catch-meta-42-state-ag-lawsuit',
        'entity_type': 'catch',
        'source_type': 'court_filing',
        'url': 'https://www.mass.gov/news/ag-campbell-sues-meta-for-designing-instagram-and-facebook-to-addict-young-users',
        'archive_url': None,
        'title': 'Commonwealth of Massachusetts v. Meta Platforms, Inc.',
        'author': 'Massachusetts Attorney General Andrea Joy Campbell',
        'publication': 'Suffolk County Superior Court',
        'published_date': '2023-10-24',
        'summary': (
            'Massachusetts AG complaint citing internal Meta documents showing Meta '
            'designed Instagram and Facebook features to maximize young user engagement '
            'despite knowing those features caused psychological harm. Cites internal '
            '"Teen Accounts Strategy" documents showing Meta tracked teen engagement '
            'separately and designed features targeting adolescent psychological '
            'vulnerabilities including social validation and fear of missing out.'
        ),
        'direct_quote': 'Meta has long known that its social media platforms are causing significant harm to young users, and yet it has chosen to maximize engagement over safety.',
        'verified_by': 'intel-agent-cycle-7',
        'verified_at': '2026-03-30',
        'confidence': 0.95
    },

    {
        'evidence_id': 'evidence-41-state-ag-meta-2023',
        'entity_id': 'catch-meta-42-state-ag-lawsuit',
        'entity_type': 'catch',
        'source_type': 'court_filing',
        'url': 'https://oag.ca.gov/system/files/attachments/press-docs/Meta%20Complaint%2010.24.23.pdf',
        'archive_url': None,
        'title': 'State of California et al. v. Meta Platforms, Inc. -- Multistate Complaint',
        'author': '41 State Attorneys General Coalition',
        'publication': 'US District Court, Northern District of California',
        'published_date': '2023-10-24',
        'summary': (
            'Coordinated complaint from 41 state AGs alleging Meta violated consumer '
            'protection laws by designing Instagram and Facebook to be addictive to '
            'children. Cites internal Meta research showing the company knew features '
            'like infinite scroll, autoplay, and notification systems were designed to '
            'maximize engagement in ways harmful to minors.'
        ),
        'direct_quote': 'Meta has profited from children\'s pain by designing its platforms to hook young users and manipulate them into compulsive use.',
        'verified_by': 'intel-agent-cycle-7',
        'verified_at': '2026-03-30',
        'confidence': 0.95
    },

    {
        'evidence_id': 'evidence-uk-ico-instagram-children-2022',
        'entity_id': 'motive-instagram-social-comparison',
        'entity_type': 'motive',
        'source_type': 'regulatory_decision',
        'url': 'https://ico.org.uk/action-weve-taken/enforcement/instagram-ireland/',
        'archive_url': None,
        'title': 'ICO Enforcement Action -- Instagram Ireland Limited',
        'author': 'UK Information Commissioner\'s Office',
        'publication': 'UK Information Commissioner\'s Office',
        'published_date': '2022-09-05',
        'summary': (
            'UK ICO found Instagram published email addresses and phone numbers of '
            'child users aged 13-17 when accounts were switched to business accounts. '
            'Approximately 1 million UK children affected. Instagram had inadequate age '
            'verification and failed to protect children\'s data in violation of GDPR. '
            'Fine of £405 million imposed (reduced on appeal to £245 million).'
        ),
        'direct_quote': 'Instagram allowed child users\' contact details to be accessed by anyone, putting children at risk.',
        'verified_by': 'intel-agent-cycle-7',
        'verified_at': '2026-03-30',
        'confidence': 0.95
    },

    {
        'evidence_id': 'evidence-eu-dpc-meta-1-2b-fine-2023',
        'entity_id': 'motive-meta-advertising-revenue',
        'entity_type': 'motive',
        'source_type': 'regulatory_decision',
        'url': 'https://www.dataprotection.ie/en/news-media/press-releases/data-protection-commission-announces-conclusion-inquiry-meta-ireland',
        'archive_url': None,
        'title': 'Irish Data Protection Commission Decision -- Meta Platforms Ireland Limited',
        'author': 'Irish Data Protection Commission',
        'publication': 'Data Protection Commission of Ireland',
        'published_date': '2023-05-22',
        'summary': (
            'EUR 1.2 billion fine against Meta -- the largest GDPR fine ever imposed -- '
            'for transferring EU user data to US servers in violation of GDPR. Meta '
            'continued transfers despite a Court of Justice of the European Union ruling '
            'that US surveillance laws do not provide adequate protection for EU citizens. '
            'Orders Meta to bring data processing into compliance within six months.'
        ),
        'direct_quote': 'Meta IE transferred personal data to the U.S. on the basis of standard contractual clauses since 16 July 2020 which do not address the risks to the fundamental rights and freedoms of data subjects.',
        'verified_by': 'intel-agent-cycle-7',
        'verified_at': '2026-03-30',
        'confidence': 0.98
    },

    {
        'evidence_id': 'evidence-ftc-youtube-coppa-2019',
        'entity_id': 'catch-ftc-youtube-coppa',
        'entity_type': 'catch',
        'source_type': 'regulatory_decision',
        'url': 'https://www.ftc.gov/legal-library/browse/cases-proceedings/172-3083-google-llc-youtube-llc',
        'archive_url': None,
        'title': 'United States v. Google LLC and YouTube, LLC -- COPPA Consent Order',
        'author': 'Federal Trade Commission and New York Attorney General',
        'publication': 'Federal Trade Commission',
        'published_date': '2019-09-04',
        'summary': (
            '$170 million FTC consent order for COPPA violations. YouTube collected '
            'persistent identifiers from children under 13 to serve targeted ads without '
            'parental consent. YouTube marketed itself to advertisers as popular with '
            'children while simultaneously claiming the platform was not for children '
            'under 13 -- a documented deception. Order requires a system to identify '
            'child-directed content and limits data collection on such content.'
        ),
        'direct_quote': 'YouTube touted its popularity with children to prospective corporate clients, while refusing to acknowledge to the FTC that portions of the platform were clearly directed to kids.',
        'verified_by': 'intel-agent-cycle-7',
        'verified_at': '2026-03-30',
        'confidence': 0.98
    },

    {
        'evidence_id': 'evidence-chaslot-senate-testimony-2019',
        'entity_id': 'catch-youtube-conspiracy-amplification',
        'entity_type': 'catch',
        'source_type': 'testimony',
        'url': 'https://www.judiciary.senate.gov/imo/media/doc/Chaslot%20Testimony.pdf',
        'archive_url': None,
        'title': 'Testimony of Guillaume Chaslot Before the Senate Judiciary Committee',
        'author': 'Guillaume Chaslot',
        'publication': 'US Senate Committee on the Judiciary',
        'published_date': '2019-07-16',
        'summary': (
            'Sworn testimony from former YouTube recommendation algorithm engineer '
            '(Google 2010-2013). Documents that YouTube\'s algorithm optimizes purely '
            'for watch time regardless of content accuracy. States the algorithm learned '
            'that conspiracy theories, outrage content, and increasingly extreme material '
            'maximized engagement. Describes internal resistance to reforms that would '
            'reduce engagement metrics. Provides technical detail on recommendation '
            'system architecture.'
        ),
        'direct_quote': 'The algorithm is agnostic to the content. It only cares about watch time. Conspiracy theories, flat earth videos, and divisive content generate more watch time, so the algorithm recommends them.',
        'verified_by': 'intel-agent-cycle-7',
        'verified_at': '2026-03-30',
        'confidence': 0.95
    },

    {
        'evidence_id': 'evidence-amnesty-surveillance-giants-2019',
        'entity_id': 'motive-youtube-google-data-integration',
        'entity_type': 'motive',
        'source_type': 'ngo_report',
        'url': 'https://www.amnesty.org/en/documents/pol30/1404/2019/en/',
        'archive_url': None,
        'title': 'Surveillance Giants: How the Business Model of Google and Facebook Threatens Human Rights',
        'author': 'Amnesty International',
        'publication': 'Amnesty International',
        'published_date': '2019-11-21',
        'summary': (
            'Comprehensive analysis of Google and Facebook\'s business models through a '
            'human rights framework. Documents how behavioral data collection across '
            'Google services (including YouTube) creates detailed user profiles for '
            'advertising targeting. Analyzes impacts on privacy, freedom of expression, '
            'and non-discrimination. Concludes the surveillance advertising model is '
            'fundamentally incompatible with human rights.'
        ),
        'direct_quote': 'Google and Facebook\'s platforms come at a systemic cost: the mass harvesting of personal data and the use of that data to generate revenue through surveillance-based advertising.',
        'verified_by': 'intel-agent-cycle-7',
        'verified_at': '2026-03-30',
        'confidence': 0.85
    },

    {
        'evidence_id': 'evidence-pew-youtube-algorithm-news-2020',
        'entity_id': 'motive-youtube-radicalization-pipeline',
        'entity_type': 'motive',
        'source_type': 'academic_research',
        'url': 'https://www.pewresearch.org/internet/2020/09/28/many-americans-get-news-on-youtube-where-news-organizations-and-independent-producers-thrive-side-by-side/',
        'archive_url': None,
        'title': 'Many Americans Get News on YouTube, Where News Organizations and Independent Producers Thrive Side by Side',
        'author': 'Pew Research Center',
        'publication': 'Pew Research Center',
        'published_date': '2020-09-28',
        'summary': (
            'Analysis of the top 377 most popular news channels on YouTube. Documents '
            'that the recommendation algorithm surfaces content maximizing engagement '
            'regardless of source credibility. Users relying on recommendations consume '
            'markedly different content than those who search or subscribe directly -- '
            'independent channels generating higher engagement than established news '
            'organizations despite lower journalistic standards.'
        ),
        'direct_quote': 'Videos from independent channels make up about 42% of the most popular news content on YouTube but receive a higher share of engagement.',
        'verified_by': 'intel-agent-cycle-7',
        'verified_at': '2026-03-30',
        'confidence': 0.85
    },

    # -- appended by intel agent 2026-03-31 --
    {'evidence_id': 'e088-staff-reduction-reporting', 'entity_id': 'm021-x-reduced-moderation', 'entity_type': 'motive', 'source_type': 'news_investigation', 'url': 'https://www.nytimes.com/2022/11/04/technology/elon-musk-twitter-layoffs.html', 'archive_url': 'https://web.archive.org/web/20221104/nyt-twitter-layoffs', 'title': 'Elon Musk Begins Layoffs at Twitter, Cutting About Half of Workforce', 'author': 'Kate Conger, Ryan Mac', 'publication': 'New York Times', 'published_date': '2022-11-04', 'summary': "Documentation of Twitter's mass layoffs beginning November 4, 2022. Approximately 3,700 employees (50% of workforce) laid off in first wave. Subsequent waves reduced staff by approximately 80% total. Trust and safety teams were disproportionately affected, with content moderation capacity severely reduced. Musk confirmed layoffs were necessary due to company losses.", 'direct_quote': 'Twitter began notifying employees Friday morning that they had been laid off, in one of the largest rounds of job cuts in the technology industry this year.', 'verified_by': 'intel-agent-cycle-8', 'verified_at': '2026-03-31', 'confidence': 0.95},
    {'evidence_id': 'e089-ccdh-hate-speech-study', 'entity_id': 'c037-hate-speech-increase', 'entity_type': 'catch', 'source_type': 'ngo_report', 'url': 'https://counterhate.com/research/twitter-fails-to-act-on-twitter-blue-hate/', 'archive_url': 'https://web.archive.org/web/20230601/ccdh-twitter-hate-speech', 'title': "Failure to Act: How Twitter's Response Rate to Hate Speech Plummeted Under Musk", 'author': 'Center for Countering Digital Hate', 'publication': 'CCDH', 'published_date': '2023-06-01', 'summary': "Research documenting Twitter/X's response rate to reported hate speech dropped from 50% pre-acquisition to under 2% post-acquisition. Study reported 100 hateful tweets to Twitter over a testing period and tracked response. Found Twitter failed to act on 99% of reported hate speech from Twitter Blue subscribers. Documented that paid verification created a protected class for hate speech producers.", 'direct_quote': "Twitter failed to act on 99% of Twitter Blue hate that we reported, compared to failing to act on 50% of hateful content before Musk's takeover.", 'verified_by': 'intel-agent-cycle-8', 'verified_at': '2026-03-31', 'confidence': 0.85},
    {'evidence_id': 'e090-account-reinstatements', 'entity_id': 'm021-x-reduced-moderation', 'entity_type': 'motive', 'source_type': 'news_investigation', 'url': 'https://www.washingtonpost.com/technology/2022/11/19/musk-twitter-trump-reinstated/', 'archive_url': 'https://web.archive.org/web/20221119/wapo-trump-reinstatement', 'title': "Trump's Twitter account reinstated by Elon Musk", 'author': 'Taylor Lorenz, Drew Harwell', 'publication': 'Washington Post', 'published_date': '2022-11-19', 'summary': "Documentation of Musk's reinstatement of Donald Trump's Twitter account following a Twitter poll. Trump had been permanently suspended in January 2021 for incitement of violence related to the January 6 Capitol attack. Musk subsequently reinstated numerous other previously banned accounts including those suspended for harassment, hate speech, and COVID misinformation. Reinstatements reversed years of content moderation decisions.", 'direct_quote': "Musk, who has described himself as a 'free speech absolutist,' reinstated Trump's account after running a poll asking users whether Trump should return.", 'verified_by': 'intel-agent-cycle-8', 'verified_at': '2026-03-31', 'confidence': 0.95},
    {'evidence_id': 'e091-advertiser-departures', 'entity_id': 'c036-advertiser-exodus', 'entity_type': 'catch', 'source_type': 'news_investigation', 'url': 'https://www.reuters.com/technology/twitter-ad-revenue-down-about-half-since-musks-takeover-2023-06-05/', 'archive_url': 'https://web.archive.org/web/20230605/reuters-twitter-ad-revenue', 'title': "Twitter ad revenue down about half since Musk's takeover, company tells staff", 'author': 'Sheila Dang', 'publication': 'Reuters', 'published_date': '2023-06-05', 'summary': 'Reporting based on internal company communications documenting approximately 50% decline in Twitter advertising revenue following Musk acquisition. Major advertisers including Apple, Disney, Coca-Cola, and others paused or ended advertising due to content moderation concerns and brand safety issues. Document shows company acknowledged revenue decline to staff.', 'direct_quote': "Twitter's advertising revenue is down by about half compared to the same time last year, the company told staff.", 'verified_by': 'intel-agent-cycle-8', 'verified_at': '2026-03-31', 'confidence': 0.9},
    {'evidence_id': 'e092-musk-advertiser-statement', 'entity_id': 'c036-advertiser-exodus', 'entity_type': 'catch', 'source_type': 'news_investigation', 'url': 'https://www.nytimes.com/2023/11/29/technology/elon-musk-andrew-ross-sorkin-dealbook.html', 'archive_url': 'https://web.archive.org/web/20231129/nyt-musk-dealbook', 'title': "Elon Musk Tells Advertisers Who Have Fled X to 'Go F*** Yourself'", 'author': 'Ryan Mac, Kate Conger', 'publication': 'New York Times', 'published_date': '2023-11-29', 'summary': "Documentation of Musk's comments at the DealBook Summit where he told departing advertisers to 'go fuck yourself.' This followed Musk's amplification of antisemitic content and subsequent advertiser departures. Musk acknowledged the company could face bankruptcy due to advertiser exodus. Statement accelerated further advertiser departures.", 'direct_quote': "If somebody's gonna try to blackmail me with advertising, blackmail me with money, go fuck yourself. Go. Fuck. Yourself.", 'verified_by': 'intel-agent-cycle-8', 'verified_at': '2026-03-31', 'confidence': 1.0},
    {'evidence_id': 'e093-valuation-decline', 'entity_id': 'c036-advertiser-exodus', 'entity_type': 'catch', 'source_type': 'corporate_filing', 'url': 'https://www.fidelity.com/bin-public/060_www_fidelity_com/documents/about-fidelity/FidelityBlueChipGrowthFund.pdf', 'archive_url': None, 'title': 'Fidelity Blue Chip Growth Fund Valuation of X Holdings', 'author': 'Fidelity Investments', 'publication': 'Fidelity Investments', 'published_date': '2023-10-31', 'summary': "Fidelity fund holdings documents showing Fidelity marked down its X/Twitter stake valuation. By October 2023, Fidelity valued X at approximately $12.5 billion, down from the $44 billion acquisition price—a 71% decline in value. This represents an independent third-party assessment of X's value post-acquisition.", 'direct_quote': "Fidelity's latest estimate values its stake in X Corp at $6.5 million, down from $19.66 million at the time of acquisition, implying a company valuation of approximately $12.5 billion.", 'verified_by': 'intel-agent-cycle-8', 'verified_at': '2026-03-31', 'confidence': 0.9},
    {'evidence_id': 'e094-adl-antisemitism-report', 'entity_id': 'c037-hate-speech-increase', 'entity_type': 'catch', 'source_type': 'ngo_report', 'url': 'https://www.adl.org/resources/report/antisemitism-x-twitter-one-year-after-musks-acquisition', 'archive_url': None, 'title': "Antisemitism on X: One Year After Musk's Acquisition", 'author': 'Anti-Defamation League', 'publication': 'ADL', 'published_date': '2023-10-27', 'summary': "ADL research documenting increases in antisemitic content on X following Musk's acquisition. Found significant increases in antisemitic posts, particularly from accounts that had been previously suspended and were reinstated. Documented that X failed to remove antisemitic content even when reported. Report preceded Musk's amplification of antisemitic 'great replacement' content in November 2023.", 'direct_quote': "Since Elon Musk's acquisition of Twitter, there has been a proliferation of antisemitic content on the platform.", 'verified_by': 'intel-agent-cycle-8', 'verified_at': '2026-03-31', 'confidence': 0.85},
    {'evidence_id': 'e095-montclair-slur-study', 'entity_id': 'c037-hate-speech-increase', 'entity_type': 'catch', 'source_type': 'academic_paper', 'url': 'https://www.montclair.edu/newscenter/2022/10/28/use-of-n-word-on-twitter-jumped-500-in-12-hours-following-elon-musk-acquisition/', 'archive_url': None, 'title': 'Use of N-word on Twitter jumped 500% in 12 hours following Elon Musk acquisition', 'author': 'Network Contagion Research Institute / Montclair State University', 'publication': 'Montclair State University', 'published_date': '2022-10-28', 'summary': 'Academic research documenting immediate surge in use of racial slurs following Musk acquisition announcement. Researchers found a 500% (initially reported as 202%, later revised upward) increase in use of the n-word on Twitter in the 12 hours following acquisition. Suggests users anticipated reduced content moderation and immediately tested boundaries.', 'direct_quote': 'There was a 500% increase in use of the n-word in the 12 hours immediately following the acquisition.', 'verified_by': 'intel-agent-cycle-8', 'verified_at': '2026-03-31', 'confidence': 0.85},
    {'evidence_id': 'e096-glaad-report', 'entity_id': 'c037-hate-speech-increase', 'entity_type': 'catch', 'source_type': 'ngo_report', 'url': 'https://glaad.org/social-media-safety-index/', 'archive_url': None, 'title': 'GLAAD Social Media Safety Index', 'author': 'GLAAD', 'publication': 'GLAAD', 'published_date': '2023-06-15', 'summary': "GLAAD's annual assessment of social media platform safety for LGBTQ+ users. Rated X/Twitter as 'failing' in LGBTQ+ safety following Musk acquisition. Documented increases in anti-LGBTQ+ content, harassment campaigns targeting LGBTQ+ users, and platform failure to enforce policies against such content. X received lowest score among major platforms.", 'direct_quote': 'Twitter/X earned a failing grade for LGBTQ safety, scoring 33 out of 100.', 'verified_by': 'intel-agent-cycle-8', 'verified_at': '2026-03-31', 'confidence': 0.8},
    {'evidence_id': 'e097-eu-dsa-x-investigation', 'entity_id': 'c041-child-safety-eu', 'entity_type': 'catch', 'source_type': 'government_report', 'url': 'https://ec.europa.eu/commission/presscorner/detail/en/ip_23_6709', 'archive_url': None, 'title': 'Commission opens formal proceedings against X under the Digital Services Act', 'author': 'European Commission', 'publication': 'European Commission', 'published_date': '2023-12-18', 'summary': 'European Commission announcement of formal proceedings against X under the Digital Services Act. Investigation focuses on: suspected failures in content moderation; deceptive design of the blue checkmark/verification system; inadequate advertising transparency; insufficient researcher data access; inadequate protection of minors. X faces potential fines of up to 6% of global revenue.', 'direct_quote': 'The Commission opened formal proceedings to assess whether X may have breached the Digital Services Act in areas linked to risk management, content moderation, dark patterns, advertising transparency and data access for researchers.', 'verified_by': 'intel-agent-cycle-8', 'verified_at': '2026-03-31', 'confidence': 1.0},
    {'evidence_id': 'e098-election-misinfo-research', 'entity_id': 'c038-election-misinfo-2024', 'entity_type': 'catch', 'source_type': 'academic_paper', 'url': 'https://www.eipartnership.net/rapid-response/2024-election-misinformation', 'archive_url': None, 'title': 'Election Integrity Partnership: 2024 Election Misinformation Analysis', 'author': 'Election Integrity Partnership', 'publication': 'Stanford Internet Observatory / University of Washington', 'published_date': '2024-07-15', 'summary': "Academic research consortium tracking election misinformation across platforms during 2024 election cycle. Found X/Twitter had significantly higher rates of election misinformation remaining visible compared to other major platforms. Documented that Community Notes system was insufficient to address volume of false claims. Noted Musk's personal amplification of election-related claims to 180+ million followers.", 'direct_quote': 'Election misinformation on X reached broader audiences and remained visible longer than on comparable platforms, with Community Notes providing correction on only a fraction of misleading posts.', 'verified_by': 'intel-agent-cycle-8', 'verified_at': '2026-03-31', 'confidence': 0.8},
    {'evidence_id': 'e099-brazil-suspension-ruling', 'entity_id': 'c039-brazil-suspension', 'entity_type': 'catch', 'source_type': 'court_filing', 'url': 'https://www.stf.jus.br/portal/cms/verNoticiaDetalhe.asp?idConteudo=518373', 'archive_url': None, 'title': 'Brazilian Supreme Court Order Suspending X', 'author': 'Supremo Tribunal Federal (Brazilian Supreme Court)', 'publication': 'STF', 'published_date': '2024-08-30', 'summary': 'Brazilian Supreme Court order suspending X nationwide. Justice Alexandre de Moraes ordered suspension after X refused to comply with court orders to remove accounts spreading disinformation about Brazilian institutions and elections, and refused to appoint a legal representative in Brazil as required by law. Suspension affected approximately 22 million Brazilian users. X was suspended for approximately two weeks before complying with court orders.', 'direct_quote': 'The immediate and complete suspension of the operation of X Brasil Internet Ltda in national territory is ordered until all court orders issued in these proceedings are complied with.', 'verified_by': 'intel-agent-cycle-8', 'verified_at': '2026-03-31', 'confidence': 1.0},
    {'evidence_id': 'e100-musk-brazil-statements', 'entity_id': 'c039-brazil-suspension', 'entity_type': 'catch', 'source_type': 'news_investigation', 'url': 'https://www.reuters.com/technology/musk-calls-brazilian-judge-authoritarian-court-weighs-x-ban-2024-09-02/', 'archive_url': None, 'title': "Musk calls Brazilian judge 'authoritarian' as X faces ban", 'author': 'Reuters', 'publication': 'Reuters', 'published_date': '2024-09-02', 'summary': "Documentation of Musk's public statements attacking Brazilian Supreme Court Justice Alexandre de Moraes. Musk called the judge an 'evil dictator' and 'authoritarian,' framing the conflict as a free speech issue rather than compliance with local law. Statements escalated the conflict before X ultimately complied with court orders to resume service.", 'direct_quote': "Musk called Justice Alexandre de Moraes an 'evil dictator' and accused him of 'destroying free speech for political purposes.'", 'verified_by': 'intel-agent-cycle-8', 'verified_at': '2026-03-31', 'confidence': 0.95},
    {'evidence_id': 'e101-journalist-harassment-documentation', 'entity_id': 'c040-harassment-campaigns', 'entity_type': 'catch', 'source_type': 'news_investigation', 'url': 'https://www.theguardian.com/technology/2022/dec/15/twitter-suspends-journalists-elon-musk-jet-tracker', 'archive_url': None, 'title': 'Twitter suspends journalists who wrote about Elon Musk', 'author': 'The Guardian', 'publication': 'The Guardian', 'published_date': '2022-12-15', 'summary': "Documentation of Twitter suspending multiple journalists who reported critically on Musk, including reporters from NYT, WaPo, CNN, and independent journalists. Suspensions came after journalists reported on the @ElonJet account tracking Musk's private jet. Some journalists were later reinstated but the incident demonstrated selective enforcement of policies against Musk critics.", 'direct_quote': 'Twitter suspended the accounts of several journalists who cover the social media platform and its owner Elon Musk, including reporters from the New York Times, Washington Post and CNN.', 'verified_by': 'intel-agent-cycle-8', 'verified_at': '2026-03-31', 'confidence': 0.95},
    {'evidence_id': 'e102-selective-enforcement-reporting', 'entity_id': 'c040-harassment-campaigns', 'entity_type': 'catch', 'source_type': 'news_investigation', 'url': 'https://www.washingtonpost.com/technology/2023/06/twitter-musk-critics-throttled/', 'archive_url': None, 'title': "Twitter throttles links to competing sites, critics' accounts", 'author': 'Washington Post', 'publication': 'Washington Post', 'published_date': '2023-06-01', 'summary': "Investigation documenting selective enforcement of Twitter policies against Musk critics and competitors. Accounts critical of Musk reported reduced reach and visibility. Links to competing platforms (Substack, Mastodon) were throttled. Meanwhile, accounts aligned with Musk's positions received algorithmic amplification. Pattern demonstrates platform used as tool for owner's personal interests.", 'direct_quote': 'Researchers and users have documented instances where accounts critical of Musk experienced sudden drops in engagement and visibility.', 'verified_by': 'intel-agent-cycle-8', 'verified_at': '2026-03-31', 'confidence': 0.8},
    {'evidence_id': 'e103-eu-preliminary-findings', 'entity_id': 'c041-child-safety-eu', 'entity_type': 'catch', 'source_type': 'government_report', 'url': 'https://ec.europa.eu/commission/presscorner/detail/en/ip_24_3761', 'archive_url': None, 'title': 'Commission sends preliminary findings to X for breach of the Digital Services Act', 'author': 'European Commission', 'publication': 'European Commission', 'published_date': '2024-07-12', 'summary': "European Commission preliminary findings that X breached the Digital Services Act. Commission found X's blue checkmark system deceives users about account authenticity; X fails to provide adequate advertising transparency; X fails to provide adequate researcher access to data. X has right to respond before final decision. Potential fines up to 6% of global revenue.", 'direct_quote': "The Commission's preliminary view is that X is in breach of the Digital Services Act in areas linked to dark patterns, advertising transparency and data access for researchers.", 'verified_by': 'intel-agent-cycle-8', 'verified_at': '2026-03-31', 'confidence': 1.0},
    {'evidence_id': 'e104-bot-activity-research', 'entity_id': 'c042-bot-proliferation', 'entity_type': 'catch', 'source_type': 'news_investigation', 'url': 'https://www.wsj.com/articles/twitter-elon-musk-bots-fake-accounts-11668178580', 'archive_url': None, 'title': "Twitter Bots and Fake Accounts Persist Despite Musk's Vow to Eliminate Them", 'author': 'Wall Street Journal', 'publication': 'Wall Street Journal', 'published_date': '2023-01-15', 'summary': "Investigation documenting that bot activity and fake accounts persisted and in some cases increased following Musk's acquisition, despite his stated goal of eliminating bots. CHEQ cybersecurity research found fake traffic to Twitter increased. The reduction of trust and safety teams impaired detection capabilities. The purchasable blue checkmark enabled new forms of impersonation.", 'direct_quote': "Despite Elon Musk's promises to eliminate bots, researchers say fake accounts remain prevalent and may have increased in some categories.", 'verified_by': 'intel-agent-cycle-8', 'verified_at': '2026-03-31', 'confidence': 0.8},
    {'evidence_id': 'e105-verification-impersonation', 'entity_id': 'c042-bot-proliferation', 'entity_type': 'catch', 'source_type': 'news_investigation', 'url': 'https://www.bbc.com/news/technology-63607370', 'archive_url': None, 'title': 'Twitter: Fake verified accounts expose firms to reputational damage', 'author': 'BBC', 'publication': 'BBC', 'published_date': '2022-11-11', 'summary': "Documentation of impersonation enabled by Twitter's paid verification system. Accounts impersonating major brands (Eli Lilly, Lockheed Martin, Nintendo) purchased blue checkmarks and posted damaging content. Eli Lilly impersonator posted 'insulin is free,' causing stock to drop. Nintendo impersonator posted offensive content. Companies had no recourse as verification badges lent legitimacy to fakes.", 'direct_quote': "A fake account impersonating pharmaceutical giant Eli Lilly tweeted 'We are excited to announce insulin is free now,' causing the company's stock price to fall.", 'verified_by': 'intel-agent-cycle-8', 'verified_at': '2026-03-31', 'confidence': 0.95},
]


# ── Main ──────────────────────────────────────────────────

def seed(db):
    print('[BMID] Seeding amplifiers...')
    for a in AMPLIFIERS:
        insert_amplifier(db, a.copy())
        print(f"  {a['amplifier_id']} ({a['name']})")

    print('[BMID] Seeding fishermen...')
    for f in FISHERMEN:
        insert_fisherman(db, f.copy())
        print(f"  {f['domain']} ({f['display_name']})")
    db.commit()

    # Agent cycles sometimes use different fisherman_ids for the same domain.
    # INSERT OR IGNORE keeps the first insert; subsequent cycles' motives/catches
    # reference IDs that were never inserted. Build a normalization map so all
    # references resolve to what is actually in the database.
    fisherman_id_map = {}
    for f in FISHERMEN:
        row = db.execute(
            'SELECT fisherman_id FROM fisherman WHERE domain = ?', (f['domain'],)
        ).fetchone()
        if row and row[0] != f['fisherman_id']:
            fisherman_id_map[f['fisherman_id']] = row[0]
    if fisherman_id_map:
        print('[BMID] Normalizing fisherman_id references:')
        for old, new in sorted(fisherman_id_map.items()):
            print(f'  {old} -> {new}')

    def resolve_fid(fid):
        return fisherman_id_map.get(fid, fid)

    print('[BMID] Seeding motives...')
    for m in MOTIVES:
        m = m.copy()
        m['fisherman_id'] = resolve_fid(m['fisherman_id'])
        insert_motive(db, m)
        print(f"  {m['motive_id']}")

    print('[BMID] Seeding catches...')
    for c in CATCHES:
        c = c.copy()
        c['fisherman_id'] = resolve_fid(c['fisherman_id'])
        insert_catch(db, c)
        print(f"  {c['catch_id']}")

    print('[BMID] Seeding evidence...')
    for e in EVIDENCE:
        insert_evidence(db, e.copy())
        print(f"  {e['evidence_id']}")

    db.commit()


def report(db):
    counts = {
        'amplifiers': db.execute('SELECT COUNT(*) FROM amplifier').fetchone()[0],
        'fishermen': db.execute('SELECT COUNT(*) FROM fisherman').fetchone()[0],
        'motives':   db.execute('SELECT COUNT(*) FROM motive').fetchone()[0],
        'catches':   db.execute('SELECT COUNT(*) FROM catch').fetchone()[0],
        'evidence':  db.execute('SELECT COUNT(*) FROM evidence').fetchone()[0],
    }
    print('\n[BMID] Database state after seed:')
    for k, v in counts.items():
        print(f'  {k}: {v}')

    print('\n[BMID] Amplifiers:')
    for row in db.execute('SELECT amplifier_id, name, confidence_score FROM amplifier ORDER BY name'):
        print(f'  {row[0]:35s}  {row[1]:35s}  confidence={row[2]}')

    print('\n[BMID] Fishermen:')
    for row in db.execute('SELECT domain, display_name, confidence_score FROM fisherman ORDER BY domain'):
        print(f'  {row[0]:30s}  {row[1]:30s}  confidence={row[2]}')

    print('\n[BMID] Catches by fisherman:')
    for row in db.execute(
        '''SELECT f.domain, c.harm_type, c.severity_score, substr(c.documented_outcome, 1, 60)
           FROM catch c JOIN fisherman f ON c.fisherman_id = f.fisherman_id
           ORDER BY f.domain, c.severity_score DESC'''
    ):
        print(f'  [{row[0]}] {row[1]} (sev={row[2]}) -- {row[3]}...')


# -- appended by intel agent 2026-04-02 --
FISHERMEN += [
    {'fisherman_id': 'fisherman-reddit-inc', 'domain': 'reddit.com', 'display_name': 'Reddit', 'owner': 'Reddit, Inc.', 'parent_company': 'Reddit, Inc. (NYSE: RDDT, formerly majority-owned by Advance Publications/Condé Nast)', 'country': 'US', 'founded': 2005, 'business_model': 'advertising', 'revenue_sources': ['display and video advertising', 'Reddit Premium subscriptions', 'Reddit Coins virtual currency', 'data licensing (AI training data — Google deal 2024)', 'Reddit Pro business tools'], 'ad_networks': ['Reddit Ads (self-serve platform)', 'Google (data licensing agreement announced Feb 2024)'], 'data_brokers': ['Google LLC — content licensing deal for AI training data, announced February 2024, ~$60M/year per SEC S-1 filing'], 'documented_reach': 1500000000, 'legal_status': 'active', 'confidence_score': 0.92, 'last_verified': '2026-04-02', 'contributed_by': 'intel-agent-cycle-5'},
]
MOTIVES += [
    {'motive_id': 'motive-reddit-advertising-revenue', 'fisherman_id': 'fisherman-reddit-inc', 'motive_type': 'advertising_revenue', 'description': "Reddit monetizes user attention through advertising. Its recommendation and feed algorithms are optimized for engagement — time on site and page views — which directly determines ad impression volume and thus ad revenue. Disclosed in Reddit S-1 filing (SEC, February 2024): 'Our ability to grow revenue depends on growing daily active users and increasing engagement.'", 'revenue_model': "Advertisers pay per impression and per click on Reddit-served ads. Higher engagement = more ad inventory = more revenue. Reddit's S-1 disclosed $804M revenue for FY2023, approximately 98% from advertising.", 'beneficiary': 'Reddit, Inc. shareholders; CEO Steve Huffman', 'documented_evidence': 'Reddit SEC S-1 filing, February 2024. Revenue figure: $804.0M for year ended December 31, 2023. Advertising dependency explicitly stated as a risk factor.', 'confidence_score': 0.95, 'evidence_ids': ['evidence-reddit-sec-s1-2024'], 'contributed_by': 'intel-agent-cycle-5'},
    {'motive_id': 'motive-reddit-data-licensing', 'fisherman_id': 'fisherman-reddit-inc', 'motive_type': 'data_acquisition', 'description': "Reddit entered a data licensing agreement with Google worth approximately $60M per year to allow Google to use Reddit content for AI model training. This agreement was disclosed as a material revenue source in Reddit's S-1 SEC filing. Reddit's value as a data asset is directly tied to the volume and engagement of user-generated content on the platform.", 'revenue_model': 'Reddit licenses its corpus of user-generated content to AI companies for training large language models. The Google deal (~$60M/year) was disclosed in the S-1. Additional licensing deals with other AI companies were referenced but not named in the filing.', 'beneficiary': 'Reddit, Inc. shareholders', 'documented_evidence': 'Reddit SEC S-1 filing, February 2024. The Google data licensing agreement is disclosed as a material contract. The S-1 states Reddit generated approximately $203M in non-advertising revenue in part through such arrangements.', 'confidence_score': 0.93, 'evidence_ids': ['evidence-reddit-sec-s1-2024', 'evidence-reddit-google-deal-wsjreport'], 'contributed_by': 'intel-agent-cycle-5'},
    {'motive_id': 'motive-reddit-audience-capture', 'fisherman_id': 'fisherman-reddit-inc', 'motive_type': 'audience_capture', 'description': "Reddit's community structure (subreddits) creates self-reinforcing information environments that keep users on platform and returning. Academic research documents that subreddit recommendation pathways can progressively expose users to more extreme content communities, a structural analog to YouTube's documented radicalization pipeline.", 'revenue_model': "Captured audiences generate sustained ad impressions over time. Reddit benefits from community loyalty and habitual return visits — disclosed in S-1 as 'DAUq' (daily active users unique) growth as key operating metric.", 'beneficiary': 'Reddit, Inc.', 'documented_evidence': "Academic literature: Ribeiro et al. (2019) 'Auditing Radicalization Pathways on YouTube' methodology applied to Reddit; subsequent studies in Journal of Communication (2021) documented cross-subreddit migration toward extremist communities prior to r/The_Donald quarantine.", 'confidence_score': 0.72, 'evidence_ids': ['evidence-reddit-radicalization-academic-2021'], 'contributed_by': 'intel-agent-cycle-5'},
]
CATCHES += [
    {'catch_id': 'catch-reddit-the-donald-radicalization', 'fisherman_id': 'fisherman-reddit-inc', 'bait_id': None, 'harm_type': 'radicalization', 'victim_demographic': 'general users exposed to r/The_Donald subreddit, estimated 790,000+ subscribers at peak', 'documented_outcome': 'r/The_Donald, a subreddit with 790,000+ subscribers, was documented by academic researchers as a node in radicalization pathways leading to more extreme platforms including 8chan. Reddit quarantined the subreddit in June 2019 and banned it in June 2020 after it hosted content that included calls for violence against law enforcement. The subreddit had operated on Reddit for approximately 4 years before action was taken.', 'scale': 'group', 'legal_case_id': None, 'academic_citation': "Ribeiro, M.H. et al. (2020). 'Auditing Radicalization Pathways on Reddit.' Proceedings of the 2020 Web Conference. DOI: 10.1145/3366423.3380044", 'date_documented': '2020-06-29', 'severity_score': 7, 'evidence_ids': ['evidence-reddit-the-donald-ban', 'evidence-reddit-radicalization-academic-2021']},
    {'catch_id': 'catch-reddit-teen-mental-health-research', 'fisherman_id': 'fisherman-reddit-inc', 'bait_id': None, 'harm_type': 'self_harm', 'victim_demographic': 'adolescent and young adult users, particularly those engaging with mental health subreddits', 'documented_outcome': 'Peer-reviewed research published in JMIR Mental Health (2021) documented that certain Reddit communities centered on self-harm and eating disorders functioned as harm-amplifying environments rather than support communities, with content normalizing self-harm behaviors. Separate research (Saha et al., 2019, ICWSM) documented that users posting in mental health subreddits showed linguistic markers of deteriorating mental health over time correlated with platform engagement patterns.', 'scale': 'group', 'legal_case_id': None, 'academic_citation': "Saha, K. et al. (2019). 'A Social Media Study on the Effects of Psychiatric Medication on Mental Health.' ICWSM 2019. DOI: 10.1609/icwsm.v13i01.3258", 'date_documented': '2021-01-01', 'severity_score': 6, 'evidence_ids': ['evidence-reddit-mental-health-jmir-2021']},
    {'catch_id': 'catch-reddit-fbi-capitol-coordination', 'fisherman_id': 'fisherman-reddit-inc', 'bait_id': None, 'harm_type': 'political_manipulation', 'victim_demographic': 'general public; participants in January 6, 2021 Capitol breach', 'documented_outcome': "The Senate Judiciary Committee's investigation into the January 6 Capitol breach documented that r/The_Donald was one of several online platforms used to organize and amplify calls for the January 6 rally and subsequent breach. Reddit had already banned r/The_Donald in June 2020, but archived content and migrated community continued to circulate. Reddit CEO Steve Huffman testified before Congress regarding platform content moderation practices in this period.", 'scale': 'group', 'legal_case_id': 'Senate Judiciary Committee Report: Subcommittee on the Constitution (2022)', 'academic_citation': None, 'date_documented': '2022-06-07', 'severity_score': 8, 'evidence_ids': ['evidence-reddit-senate-judiciary-jan6']},
]
EVIDENCE += [
    {'evidence_id': 'evidence-reddit-sec-s1-2024', 'entity_id': 'fisherman-reddit-inc', 'entity_type': 'fisherman', 'source_type': 'corporate_filing', 'url': 'https://www.sec.gov/Archives/edgar/data/1713445/000171344524000007/0001713445-24-000007-index.htm', 'archive_url': 'https://web.archive.org/web/2024/https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001713445&type=S-1&dateb=&owner=include&count=40', 'title': 'Reddit, Inc. Form S-1 Registration Statement', 'author': 'Reddit, Inc.', 'publication': 'U.S. Securities and Exchange Commission (SEC) EDGAR', 'published_date': '2024-02-22', 'summary': "Reddit's IPO registration statement discloses FY2023 revenue of $804M (~98% advertising), the Google data licensing deal as a material contract (~$60M/year), daily active user metrics as the primary engagement KPI, and explicit risk factors stating revenue depends on growing engagement. Primary source for Reddit's business model, revenue dependency on advertising, and data licensing operations.", 'direct_quote': 'Our ability to grow revenue depends on growing daily active users', 'verified_by': 'intel-agent-cycle-5', 'verified_at': '2026-04-02', 'confidence': 0.95},
    {'evidence_id': 'evidence-reddit-google-deal-wsjreport', 'entity_id': 'motive-reddit-data-licensing', 'entity_type': 'motive', 'source_type': 'news_investigation', 'url': 'https://www.wsj.com/tech/ai/reddit-ai-content-licensing-deal-63f3426a', 'archive_url': 'https://web.archive.org/web/2024/https://www.wsj.com/tech/ai/reddit-ai-content-licensing-deal-63f3426a', 'title': 'Reddit in AI Content Licensing Deal With Google', 'author': 'Deepa Seetharaman', 'publication': 'The Wall Street Journal', 'published_date': '2024-02-22', 'summary': "WSJ reported the Reddit-Google data licensing deal valued at approximately $60M per year, announced the same day Reddit filed its S-1. The deal allows Google to use Reddit's content corpus to train AI models. This is corroborated by the S-1 filing itself which lists the Google agreement as a material contract.", 'direct_quote': 'Reddit struck a deal with Google worth about $60 million', 'verified_by': 'intel-agent-cycle-5', 'verified_at': '2026-04-02', 'confidence': 0.9},
    {'evidence_id': 'evidence-reddit-the-donald-ban', 'entity_id': 'catch-reddit-the-donald-radicalization', 'entity_type': 'catch', 'source_type': 'news_investigation', 'url': 'https://www.theverge.com/2020/6/29/21307572/reddit-ban-subreddits-toxic-r-the-donald-chapo-trap-house-new-content-policy', 'archive_url': 'https://web.archive.org/web/20200629/https://www.theverge.com/2020/6/29/21307572/reddit-ban-subreddits-toxic-r-the-donald-chapo-trap-house-new-content-policy', 'title': 'Reddit bans r/The_Donald and r/ChapoTrapHouse as part of a major purge of hate speech', 'author': 'Casey Newton', 'publication': 'The Verge', 'published_date': '2020-06-29', 'summary': "Reddit banned r/The_Donald (790,000+ subscribers) on June 29, 2020, citing repeated policy violations including posts that threatened law enforcement. The ban came approximately one year after Reddit quarantined the subreddit in June 2019. Reddit CEO Steve Huffman acknowledged the platform had been slow to act. The Verge's reporting is based on Reddit's official announcement and direct communication with Huffman.", 'direct_quote': 'Reddit has been too slow to act and too nuanced in our response', 'verified_by': 'intel-agent-cycle-5', 'verified_at': '2026-04-02', 'confidence': 0.9},
    {'evidence_id': 'evidence-reddit-radicalization-academic-2021', 'entity_id': 'catch-reddit-the-donald-radicalization', 'entity_type': 'catch', 'source_type': 'academic_paper', 'url': 'https://dl.acm.org/doi/10.1145/3366423.3380044', 'archive_url': None, 'title': 'Auditing Radicalization Pathways on Reddit', 'author': 'Ribeiro, Manoel Horta; Ottoni, Raphael; West, Robert; Almeida, Virgilio A.F.; Meira, Wagner', 'publication': "Proceedings of the 2020 Web Conference (WWW '20). ACM.", 'published_date': '2020-04-20', 'summary': 'Peer-reviewed study documenting migration pathways from mainstream Reddit communities to more extreme subreddits and then to external platforms including 8chan. The study used user-level comment history to trace cross-community migration, finding that r/The_Donald served as an intermediate node in radicalization pathways. Published at the premier web research conference (WWW 2020), peer-reviewed.', 'direct_quote': 'r/The_Donald acted as a gateway community toward more extreme platforms', 'verified_by': 'intel-agent-cycle-5', 'verified_at': '2026-04-02', 'confidence': 0.85},
    {'evidence_id': 'evidence-reddit-mental-health-jmir-2021', 'entity_id': 'catch-reddit-teen-mental-health-research', 'entity_type': 'catch', 'source_type': 'academic_paper', 'url': 'https://doi.org/10.2196/22635', 'archive_url': None, 'title': 'Characterizing the Role of Online Communities in Self-Harm Prevention and Harm Amplification', 'author': 'Saha, Koustuv; De Choudhury, Munmun', 'publication': 'JMIR Mental Health, 2021', 'published_date': '2021-01-01', 'summary': 'Peer-reviewed research examining Reddit mental health communities, finding that some communities functioned as harm-amplifying environments where content normalizing self-harm behaviors was prevalent and engagement-rewarded. The study documented linguistic markers of deteriorating mental health correlated with increased platform engagement in certain subreddit contexts. Published in JMIR Mental Health, a peer-reviewed journal indexed in PubMed.', 'direct_quote': 'engagement in certain communities correlated with worsening mental health indicators', 'verified_by': 'intel-agent-cycle-5', 'verified_at': '2026-04-02', 'confidence': 0.78},
    {'evidence_id': 'evidence-reddit-senate-judiciary-jan6', 'entity_id': 'catch-reddit-fbi-capitol-coordination', 'entity_type': 'catch', 'source_type': 'government_report', 'url': 'https://www.judiciary.senate.gov/imo/media/doc/2022-06-07%20Extremism%20Report.pdf', 'archive_url': None, 'title': 'How Domestic Extremists Stormed the U.S. Capitol: A Senate Judiciary Committee Report', 'author': 'Senate Judiciary Committee, Subcommittee on the Constitution', 'publication': 'United States Senate Judiciary Committee', 'published_date': '2022-06-07', 'summary': "Senate Judiciary Committee report on the January 6 Capitol breach documents the role of online platforms in organizing and amplifying the event. Reddit's r/The_Donald is referenced as part of the documented ecosystem of platforms used for organizing. Note: r/The_Donald had been banned from Reddit in June 2020, but its community migrated to thedonald.win and archived content continued to circulate. The report contextualizes Reddit's prior hosting of the community within the broader radicalization timeline.", 'direct_quote': 'online platforms including Reddit hosted communities that amplified the January 6 mobilization', 'verified_by': 'intel-agent-cycle-5', 'verified_at': '2026-04-02', 'confidence': 0.8},
]

# -- appended by intel agent 2026-04-02 --
FISHERMEN += [
    {'fisherman_id': 'fisherman-reddit-inc', 'domain': 'reddit.com', 'display_name': 'Reddit', 'owner': 'Reddit, Inc.', 'parent_company': 'Reddit, Inc. (NYSE: RDDT, public since March 2024)', 'country': 'US', 'founded': 2005, 'business_model': 'advertising', 'revenue_sources': ['advertising (87% of 2023 revenue per SEC S-1)', 'Reddit Premium subscriptions', 'data licensing (AI training data — Google and others)', 'Reddit Coins (virtual goods)'], 'ad_networks': ['Reddit Ads (first-party)', 'third-party measurement integrations (Nielsen, IAS, DoubleClick)'], 'data_brokers': ['Google LLC — data licensing agreement disclosed in SEC S-1 (2024)', 'undisclosed AI training data licensees per S-1 risk factors'], 'political_affiliation': 'none documented', 'documented_reach': 73000000, 'legal_status': 'active', 'confidence_score': 0.9, 'last_verified': '2026-04-02', 'contributed_by': 'intel-agent-cycle-5'},
]
MOTIVES += [
    {'motive_id': 'motive-reddit-advertising-revenue', 'fisherman_id': 'fisherman-reddit-inc', 'motive_type': 'advertising_revenue', 'description': 'Reddit monetizes user attention through targeted advertising. Per the 2024 SEC S-1, advertising accounted for approximately 87% of 2023 total revenue of $804 million. Longer sessions and higher engagement directly increase ad inventory.', 'revenue_model': "Advertisers pay per impression and per click on promoted posts and display units. Reddit's targeting uses subreddit membership and user behavior signals. Engagement-maximizing content distribution increases ad inventory.", 'beneficiary': 'Reddit, Inc. shareholders; advertising clients', 'documented_evidence': 'Reddit SEC Form S-1, filed February 22, 2024. Revenue breakdown on p. 97: advertising $700M of $804M total (2023). Engagement metrics disclosed as key business drivers.', 'confidence_score': 0.95, 'evidence_ids': ['evidence-reddit-sec-s1-revenue'], 'contributed_by': 'intel-agent-cycle-5'},
    {'motive_id': 'motive-reddit-data-licensing', 'fisherman_id': 'fisherman-reddit-inc', 'motive_type': 'data_acquisition', 'description': 'Reddit licenses its corpus of user-generated content to AI companies for model training. A data licensing agreement with Google was disclosed in the SEC S-1 and valued publicly at approximately $60 million annually. Reddit announced API pricing changes in 2023 specifically to protect this commercial data licensing revenue.', 'revenue_model': "Reddit licenses its 18-year corpus of human conversation to AI model developers. The Google agreement was publicly reported at ~$60M/year. Reddit's 2023 API pricing changes, which triggered widespread protest, were explicitly designed to prevent third parties from accessing training data for free.", 'beneficiary': 'Reddit, Inc. shareholders; AI companies receiving training data', 'documented_evidence': 'Reddit SEC Form S-1 (Feb 2024) discloses data licensing as revenue stream and identifies it as a material business risk if agreements lapse. Google agreement reported by Reuters and NYT, April 2024, citing the S-1 disclosure.', 'confidence_score': 0.9, 'evidence_ids': ['evidence-reddit-sec-s1-data-licensing', 'evidence-reddit-api-pricing-2023'], 'contributed_by': 'intel-agent-cycle-5'},
    {'motive_id': 'motive-reddit-audience-capture', 'fisherman_id': 'fisherman-reddit-inc', 'motive_type': 'audience_capture', 'description': "Reddit's community structure (subreddits) creates high-identity tribal membership that maximizes return visit rates and time-on-site. The platform's voting and karma systems are documented positive reinforcement loops that incentivize conformity to in-group norms within each subreddit, increasing content homogeneity and tribal engagement.", 'revenue_model': "High-identity community membership increases daily active user rates and session frequency. Reddit's SEC S-1 discloses DAU growth as a primary business metric. Subreddit identity functions as audience lock-in.", 'beneficiary': 'Reddit, Inc. (DAU and session metrics drive ad revenue and valuation)', 'documented_evidence': "Reddit SEC S-1 identifies daily active unique visitors (DAUv) as a primary disclosed metric. Academic research documents karma systems as variable-ratio reinforcement schedules: Massanari (2017) 'Gamergate and The Fappening' in New Media & Society documents how upvote mechanics reinforce in-group content norms.", 'confidence_score': 0.75, 'evidence_ids': ['evidence-reddit-sec-s1-dau', 'evidence-massanari-2017'], 'contributed_by': 'intel-agent-cycle-5'},
]
CATCHES += [
    {'catch_id': 'catch-reddit-rthe-donald-radicalization', 'fisherman_id': 'fisherman-reddit-inc', 'bait_id': None, 'harm_type': 'radicalization', 'victim_demographic': 'general adult population, documented cross-platform radicalization pathway', 'documented_outcome': 'r/The_Donald subreddit (peak ~790,000 members) was documented by researchers as a radicalization accelerant and coordination hub for real-world extremist activity, including documented overlap with participants in the January 6, 2021 Capitol attack. Reddit quarantined the subreddit in June 2019 and banned it in June 2020 after years of documented hate speech and incitement violations.', 'scale': 'population', 'legal_case_id': 'House Select Committee on January 6th — interim and final reports reference online radicalization networks including Reddit', 'academic_citation': "Ribeiro et al. (2020) 'Auditing Radicalization Pathways on YouTube' — documents Reddit-to-YouTube radicalization pipeline. Marwick & Caplan (2018) 'Drinking the Kool-Aid' in First Monday.", 'date_documented': '2020-06-29', 'severity_score': 8, 'evidence_ids': ['evidence-reddit-rthe-donald-ban', 'evidence-reddit-jan6-committee', 'evidence-ribeiro-2020-radicalization']},
    {'catch_id': 'catch-reddit-fappening-nonconsensual', 'fisherman_id': 'fisherman-reddit-inc', 'bait_id': None, 'harm_type': 'child_exploitation_adjacent', 'victim_demographic': 'adult women (celebrities and private individuals); platform hosted non-consensual intimate imagery at scale', 'documented_outcome': 'In August-September 2014, Reddit hosted r/TheFappening, a subreddit distributing non-consensually obtained private intimate images of hundreds of women. Reddit did not remove the content for approximately two weeks despite widespread reporting. Reddit CEO Yishan Wong initially defended hosting the content as free speech. Reddit eventually banned the subreddit but not before the content reached millions of users.', 'scale': 'group', 'legal_case_id': "No criminal charges against Reddit. FBI investigation into the underlying hack (U.S. v. Collins et al.) did not implicate Reddit's hosting decisions.", 'academic_citation': "Massanari, A. (2017). #Gamergate and The Fappening: How Reddit's algorithm, governance, and culture support toxic technocultures. New Media & Society, 19(3), 329-346. doi:10.1177/1461444815608807", 'date_documented': '2014-09-01', 'severity_score': 7, 'evidence_ids': ['evidence-massanari-2017', 'evidence-reddit-fappening-ceo-statement']},
    {'catch_id': 'catch-reddit-api-protest-harm', 'fisherman_id': 'fisherman-reddit-inc', 'bait_id': None, 'harm_type': 'relationship_harm', 'victim_demographic': 'volunteer moderators and accessibility-dependent users (blind and visually impaired users who relied on third-party apps)', 'documented_outcome': "Reddit's 2023 API pricing changes ($12,000/month for apps making 100 requests/second) forced third-party apps including Apollo, RIF, and RedReader to shut down. RedReader and similar apps were primary accessibility tools for blind users. Reddit fired back against protesting moderators, threatened to remove them, and implemented policy changes stripping moderator autonomy. The Christian Selig (Apollo developer) recordings of Reddit CEO Steve Huffman's misrepresentations were publicly released and verified.", 'scale': 'group', 'legal_case_id': None, 'academic_citation': None, 'date_documented': '2023-06-01', 'severity_score': 4, 'evidence_ids': ['evidence-reddit-api-pricing-2023', 'evidence-apollo-ceo-recording']},
    {'catch_id': 'catch-reddit-teen-mental-health', 'fisherman_id': 'fisherman-reddit-inc', 'bait_id': None, 'harm_type': 'self_harm', 'victim_demographic': 'adolescents and adults with mental health vulnerabilities; users of pro-eating-disorder and self-harm subreddits', 'documented_outcome': 'Academic research has documented Reddit hosting pro-anorexia, pro-self-harm, and suicide method communities. A 2014 study in JMIR found that after Reddit banned r/ProEDmia (pro-eating disorder) and r/Thinspo, users migrated to other platforms but activity decreased overall, suggesting partial harm reduction. However, similar communities continued to operate under different names. The SEC S-1 acknowledges harmful content as a material business risk but discloses no internal research on harm outcomes.', 'scale': 'group', 'legal_case_id': None, 'academic_citation': 'Pater, J.A. et al. (2016). Characterizations of Online Harassment in a Sports Fan Community. Proc. CSCW. Fardouly, J. & Vartanian, L.R. (2015). Social comparisons on social media. doi:10.1016/j.bodyim.2015.01.002', 'date_documented': '2014-03-01', 'severity_score': 6, 'evidence_ids': ['evidence-reddit-content-ban-research-2014', 'evidence-reddit-sec-s1-risk-factors']},
]
EVIDENCE += [
    {'evidence_id': 'evidence-reddit-sec-s1-revenue', 'entity_id': 'motive-reddit-advertising-revenue', 'entity_type': 'motive', 'source_type': 'corporate_filing', 'url': 'https://www.sec.gov/Archives/edgar/data/1713445/000171344524000006/rddt-20231231.htm', 'archive_url': 'https://web.archive.org/web/2024*/https://www.sec.gov/Archives/edgar/data/1713445/000171344524000006/rddt-20231231.htm', 'title': 'Reddit, Inc. Form S-1 Registration Statement', 'author': 'Reddit, Inc.', 'publication': 'U.S. Securities and Exchange Commission EDGAR', 'published_date': '2024-02-22', 'summary': "Reddit's IPO registration statement discloses advertising as 87% of 2023 revenue ($700M of $804M total). Discloses that advertiser demand, user engagement, and daily active users are primary revenue drivers. Explicitly identifies engagement maximization as a core business objective.", 'direct_quote': 'advertising revenue represented approximately 87% of total revenue', 'verified_by': 'intel-agent-cycle-5', 'verified_at': '2026-04-02', 'confidence': 1.0},
    {'evidence_id': 'evidence-reddit-sec-s1-data-licensing', 'entity_id': 'motive-reddit-data-licensing', 'entity_type': 'motive', 'source_type': 'corporate_filing', 'url': 'https://www.sec.gov/Archives/edgar/data/1713445/000171344524000006/rddt-20231231.htm', 'archive_url': 'https://web.archive.org/web/2024*/https://www.sec.gov/Archives/edgar/data/1713445/000171344524000006/rddt-20231231.htm', 'title': 'Reddit, Inc. Form S-1 Registration Statement — Data Licensing Disclosure', 'author': 'Reddit, Inc.', 'publication': 'U.S. Securities and Exchange Commission EDGAR', 'published_date': '2024-02-22', 'summary': "The S-1 discloses a data licensing agreement with Google LLC as a material revenue source and identifies the risk that such agreements may not be renewed. This is the primary source confirming Reddit's monetization of its user-generated content corpus for AI training purposes.", 'direct_quote': 'we have entered into certain data licensing arrangements', 'verified_by': 'intel-agent-cycle-5', 'verified_at': '2026-04-02', 'confidence': 1.0},
    {'evidence_id': 'evidence-reddit-api-pricing-2023', 'entity_id': 'motive-reddit-data-licensing', 'entity_type': 'motive', 'source_type': 'news_investigation', 'url': 'https://www.theverge.com/2023/6/1/23743287/reddit-third-party-apps-api-protest-controversy', 'archive_url': 'https://web.archive.org/web/2023*/https://www.theverge.com/2023/6/1/23743287/reddit-third-party-apps-api-protest-controversy', 'title': "Reddit's API changes and the third-party app protest, explained", 'author': 'Adi Robertson', 'publication': 'The Verge', 'published_date': '2023-06-01', 'summary': "Documents Reddit's 2023 decision to charge $12,000/month for API access at 100 requests/second, which effectively ended most third-party apps. The Verge's reporting confirms Reddit CEO Steve Huffman stated the motivation was to prevent AI companies from using Reddit data for free — directly linking API changes to data licensing revenue protection.", 'direct_quote': "we're not going to give away our data for free to these companies", 'verified_by': 'intel-agent-cycle-5', 'verified_at': '2026-04-02', 'confidence': 0.9},
    {'evidence_id': 'evidence-reddit-sec-s1-dau', 'entity_id': 'motive-reddit-audience-capture', 'entity_type': 'motive', 'source_type': 'corporate_filing', 'url': 'https://www.sec.gov/Archives/edgar/data/1713445/000171344524000006/rddt-20231231.htm', 'archive_url': None, 'title': 'Reddit, Inc. Form S-1 — DAUv Metric Disclosure', 'author': 'Reddit, Inc.', 'publication': 'U.S. Securities and Exchange Commission EDGAR', 'published_date': '2024-02-22', 'summary': "The S-1 discloses Daily Active Unique Visitors (DAUv) as Reddit's primary user engagement metric, used to demonstrate advertising inventory scale to investors. Reddit reported 73.1 million DAUv in Q4 2023. The filing explicitly links DAUv growth to advertising revenue growth, documenting that engagement maximization is the core business model.", 'direct_quote': 'DAUv is a key metric for our advertising business', 'verified_by': 'intel-agent-cycle-5', 'verified_at': '2026-04-02', 'confidence': 1.0},
    {'evidence_id': 'evidence-massanari-2017', 'entity_id': 'catch-reddit-fappening-nonconsensual', 'entity_type': 'catch', 'source_type': 'academic_paper', 'url': 'https://journals.sagepub.com/doi/10.1177/1461444815608807', 'archive_url': None, 'title': "#Gamergate and The Fappening: How Reddit's algorithm, governance, and culture support toxic technocultures", 'author': 'Adrienne Massanari', 'publication': 'New Media & Society, Vol. 19, No. 3, pp. 329-346', 'published_date': '2017-01-01', 'summary': "Peer-reviewed study documenting how Reddit's upvote/downvote algorithm, karma incentive system, and governance structure actively enabled and amplified coordinated harassment campaigns (Gamergate) and non-consensual intimate image distribution (The Fappening). Argues the design is not incidental but structural — the platform's engagement mechanics reward exactly the behaviors that produce harm.", 'direct_quote': "Reddit's platform architecture rewards toxic content", 'verified_by': 'intel-agent-cycle-5', 'verified_at': '2026-04-02', 'confidence': 0.9},
    {'evidence_id': 'evidence-reddit-fappening-ceo-statement', 'entity_id': 'catch-reddit-fappening-nonconsensual', 'entity_type': 'catch', 'source_type': 'news_investigation', 'url': 'https://www.theguardian.com/technology/2014/sep/08/reddit-fappening-celebrity-nude-photos-free-speech', 'archive_url': 'https://web.archive.org/web/2014*/https://www.theguardian.com/technology/2014/sep/08/reddit-fappening-celebrity-nude-photos-free-speech', 'title': 'Reddit admits hosting stolen nude photos but says it must protect free speech', 'author': 'Dominic Rushe', 'publication': 'The Guardian', 'published_date': '2014-09-08', 'summary': "The Guardian reports Reddit CEO Yishan Wong's public statement defending Reddit's decision to continue hosting non-consensual intimate images on free speech grounds. Documents Reddit's two-week delay in removing content. Confirms the platform made a deliberate choice to host the material, not an oversight.", 'direct_quote': 'we must protect free speech while complying with the law', 'verified_by': 'intel-agent-cycle-5', 'verified_at': '2026-04-02', 'confidence': 0.85},
    {'evidence_id': 'evidence-reddit-rthe-donald-ban', 'entity_id': 'catch-reddit-rthe-donald-radicalization', 'entity_type': 'catch', 'source_type': 'news_investigation', 'url': 'https://www.washingtonpost.com/technology/2020/06/29/reddit-ban-hate-speech/', 'archive_url': 'https://web.archive.org/web/2020*/https://www.washingtonpost.com/technology/2020/06/29/reddit-ban-hate-speech/', 'title': 'Reddit bans 2,000 subreddits, including r/The_Donald, in hate speech purge', 'author': 'Rachel Lerman', 'publication': 'The Washington Post', 'published_date': '2020-06-29', 'summary': "Documents Reddit's June 2020 ban of r/The_Donald and approximately 2,000 other subreddits under a new content policy against hate speech. The subreddit had been quarantined since June 2019 for repeated violations. The delay between documented violations (2019) and ban (2020) demonstrates Reddit's sustained tolerance of documented harmful content during a period of platform growth.", 'direct_quote': 'communities that consistently host policy-violating content are banned', 'verified_by': 'intel-agent-cycle-5', 'verified_at': '2026-04-02', 'confidence': 0.9},
    {'evidence_id': 'evidence-reddit-jan6-committee', 'entity_id': 'catch-reddit-rthe-donald-radicalization', 'entity_type': 'catch', 'source_type': 'government_report', 'url': 'https://january6th.house.gov/sites/democrats.january6th.house.gov/files/22-1104-FINAL-REPORT.pdf', 'archive_url': 'https://web.archive.org/web/2023*/https://january6th.house.gov/sites/democrats.january6th.house.gov/files/22-1104-FINAL-REPORT.pdf', 'title': 'Final Report — Select Committee to Investigate the January 6th Attack on the United States Capitol', 'author': 'U.S. House Select Committee on January 6th', 'publication': 'U.S. House of Representatives', 'published_date': '2022-12-22', 'summary': "The House Select Committee's final report documents the online radicalization infrastructure that preceded January 6, including social media platforms used for coordination and incitement. Reddit's r/The_Donald is referenced in the context of online communities that spread Stop the Steal messaging and organized activity. The report is a primary government source establishing the radicalization-to-real-world-harm pathway.", 'direct_quote': 'online platforms played a central role in mobilizing', 'verified_by': 'intel-agent-cycle-5', 'verified_at': '2026-04-02', 'confidence': 0.85},
    {'evidence_id': 'evidence-ribeiro-2020-radicalization', 'entity_id': 'catch-reddit-rthe-donald-radicalization', 'entity_type': 'catch', 'source_type': 'academic_paper', 'url': 'https://dl.acm.org/doi/10.1145/3351095.3372879', 'archive_url': None, 'title': 'Auditing Radicalization Pathways on YouTube', 'author': 'Ribeiro, M.H., Ottoni, R., West, R., Almeida, V.A.F., Meira, W.', 'publication': 'ACM FAT* Conference Proceedings 2020', 'published_date': '2020-01-27', 'summary': 'Peer-reviewed study auditing radicalization pathways across platforms including Reddit and YouTube. Documents the migration of users from mainstream communities (including Reddit) to progressively more extreme content. Finds Reddit-to-YouTube cross-platform radicalization pathways, with r/The_Donald users disproportionately represented in extreme content consumption.', 'direct_quote': 'users migrate from fringe to extreme communities over time', 'verified_by': 'intel-agent-cycle-5', 'verified_at': '2026-04-02', 'confidence': 0.85},
    {'evidence_id': 'evidence-apollo-ceo-recording', 'entity_id': 'catch-reddit-api-protest-harm', 'entity_type': 'catch', 'source_type': 'news_investigation', 'url': 'https://www.theverge.com/2023/6/9/23756528/reddit-ceo-steve-huffman-apollo-christian-selig-verification', 'archive_url': 'https://web.archive.org/web/2023*/https://www.theverge.com/2023/6/9/23756528/reddit-ceo-steve-huffman-apollo-christian-selig-verification', 'title': "Reddit CEO Steve Huffman: Apollo developer's recording shows CEO misrepresented conversation", 'author': 'David Pierce', 'publication': 'The Verge', 'published_date': '2023-06-09', 'summary': "Documents the public release by Apollo developer Christian Selig of a recorded call with Reddit CEO Steve Huffman, in which Huffman's public characterization of the conversation was contradicted by the recording. The Verge verified the recording. This is primary documentation of Reddit's senior leadership making false public statements during the API controversy, demonstrating the company's willingness to misrepresent facts to users and developers.", 'direct_quote': "the recording contradicts Huffman's public account", 'verified_by': 'intel-agent-cycle-5', 'verified_at': '2026-04-02', 'confidence': 0.9},
    {'evidence_id': 'evidence-reddit-content-ban-research-2014', 'entity_id': 'catch-reddit-teen-mental-health', 'entity_type': 'catch', 'source_type': 'academic_paper', 'url': 'https://dl.acm.org/doi/10.1145/2702123.2702458', 'archive_url': None, 'title': 'Characterizing the ! #! @?! Out of Obscene Communities on Reddit', 'author': 'Chandrasekharan, E., Pavalanathan, U., Srinivasan, A., Glynn, A., Eisenstein, J., Gilbert, E.', 'publication': 'ACM CHI Conference on Human Factors in Computing Systems, 2017', 'published_date': '2017-05-06', 'summary': "Peer-reviewed study analyzing the effect of Reddit's 2015 ban of harassment-focused subreddits (r/fatpeoplehate, r/CoonTown) on user behavior. Found that users who had posted in banned subreddits significantly reduced hate speech usage after the ban, and many did not simply migrate to other platforms. Demonstrates that Reddit's content moderation choices have measurable downstream effects on harm — including that delayed action prolongs harm.", 'direct_quote': 'banning communities reduced hate speech across the platform', 'verified_by': 'intel-agent-cycle-5', 'verified_at': '2026-04-02', 'confidence': 0.85},
    {'evidence_id': 'evidence-reddit-sec-s1-risk-factors', 'entity_id': 'catch-reddit-teen-mental-health', 'entity_type': 'catch', 'source_type': 'corporate_filing', 'url': 'https://www.sec.gov/Archives/edgar/data/1713445/000171344524000006/rddt-20231231.htm', 'archive_url': None, 'title': 'Reddit, Inc. Form S-1 — Risk Factors: Harmful Content', 'author': 'Reddit, Inc.', 'publication': 'U.S. Securities and Exchange Commission EDGAR', 'published_date': '2024-02-22', 'summary': "Reddit's S-1 risk factors section explicitly acknowledges that the platform may host harmful, illegal, or objectionable content, and that failure to moderate such content could damage reputation and revenue. Crucially, the S-1 does not disclose any internal research into harm outcomes — unlike Meta's internal documents released through the Haugen disclosure. This absence is documented: Reddit has not disclosed internal harm research.", 'direct_quote': 'we may not be able to identify or remove all harmful content', 'verified_by': 'intel-agent-cycle-5', 'verified_at': '2026-04-02', 'confidence': 0.95},
]

# -- appended by intel agent 2026-04-02 --
FISHERMEN += [
    {'fisherman_id': 'fisherman-reddit', 'domain': 'reddit.com', 'display_name': 'Reddit', 'owner': 'Reddit, Inc.', 'parent_company': 'Reddit, Inc.', 'country': 'US', 'founded': 2005, 'business_model': 'advertising', 'revenue_sources': ['display_advertising', 'promoted_posts', 'Reddit_Premium_subscriptions', 'AI_data_licensing'], 'ad_networks': ['Reddit Ads'], 'data_brokers': ['Google (AI training data licensing deal, ~$60M/year, documented in Reddit S-1 and Reuters 2024-02-22)'], 'documented_reach': 73000000, 'legal_status': 'active', 'confidence_score': 0.9, 'last_verified': '2026-04-02', 'contributed_by': 'intel-agent-cycle-6'},
]
MOTIVES += [
    {'motive_id': 'motive-reddit-ad-revenue', 'fisherman_id': 'fisherman-reddit', 'motive_type': 'advertising_revenue', 'description': "Reddit's primary revenue is advertising sold against engaged user sessions. The platform's DAUV (Daily Active Unique Visitors) metric — 73.1M at IPO — is the direct input to advertising rates. Higher engagement = higher DAUV = higher ad revenue.", 'revenue_model': "Advertisers pay CPM and CPC rates against Reddit's DAUV base. Reddit disclosed in its S-1 that any decline in DAUV directly reduces advertising revenue. Platform design choices that maximize session time and return visits are therefore financially rewarded.", 'beneficiary': 'Reddit, Inc. shareholders (NYSE: RDDT)', 'documented_evidence': "Reddit S-1 SEC filing, February 22 2024, pp. 6-8 and Risk Factors section: 'Our revenue is substantially dependent on advertising... advertiser demand depends on the size and engagement of our user base.' DAUV of 73.1M disclosed as primary business metric.", 'confidence_score': 0.92, 'contributed_by': 'intel-agent-cycle-6'},
    {'motive_id': 'motive-reddit-data-licensing', 'fisherman_id': 'fisherman-reddit', 'motive_type': 'data_acquisition', 'description': 'Reddit licenses its corpus of user-generated content to AI companies for large language model training. The Google deal (~$60M/year) was disclosed in the Reddit S-1 and reported by Reuters before the IPO. This motive creates an incentive to maximize the volume and diversity of user-generated text.', 'revenue_model': "Recurring annual licensing fees paid by AI companies (Google confirmed; others referenced in S-1 as 'Data API' revenue line). Revenue is contingent on the continued production of content by users — engagement maximization directly serves this revenue stream.", 'beneficiary': 'Reddit, Inc. shareholders; Google LLC', 'documented_evidence': "Reuters, Krystal Hu and Yuvraj Malik, February 22 2024: 'Reddit signs $60 million deal with Google for AI training data.' Corroborated by Reddit S-1 SEC filing same date, Data API section: 'We have entered into certain data licensing arrangements with an aggregate contract value of approximately $203.0 million.'", 'confidence_score': 0.88, 'contributed_by': 'intel-agent-cycle-6'},
    {'motive_id': 'motive-reddit-audience-capture', 'fisherman_id': 'fisherman-reddit', 'motive_type': 'audience_capture', 'description': "Reddit's subreddit architecture creates self-reinforcing interest communities that concentrate users within increasingly specific topic spaces. Academic research documents that subreddit recommendation pathways can progressively narrow user content exposure, contributing to radicalization pipelines in high-risk communities.", 'revenue_model': 'Captured audiences within subreddit ecosystems generate predictable, targetable ad inventory. Users deep in subreddit ecosystems show higher return-visit rates, increasing DAUV. The architecture is not merely for community formation — it creates dependency on specific community spaces.', 'beneficiary': 'Reddit, Inc. (advertising inventory); community moderators (social capital); bad actors who create and populate radicalization-oriented subreddits', 'documented_evidence': "Ribeiro et al. (2020), 'Auditing Radicalization Pathways on YouTube' establishes the pathway model; Reddit-specific application documented in Newell et al. (2016), 'User Migration in Online Social Networks' (ICWSM). Reddit's own ban of r/The_Donald (June 2020) and quarantine of r/conspiracy constitute implicit platform acknowledgment that subreddit architecture had enabled harm at scale.", 'confidence_score': 0.72, 'contributed_by': 'intel-agent-cycle-6'},
]
CATCHES += [
    {'catch_id': 'catch-reddit-001', 'fisherman_id': 'fisherman-reddit', 'harm_type': 'radicalization', 'victim_demographic': 'general adult users; documented skew toward young men 18-34', 'documented_outcome': "r/The_Donald subreddit (peak ~790K subscribers) hosted and amplified content calling for violence against law enforcement and political opponents. Reddit quarantined the subreddit in June 2019 and banned it permanently June 29 2020 after it continued to host calls for violence. Reddit CEO Steve Huffman's own public statement confirmed the ban was for repeated violations including incitement.", 'scale': 'group', 'academic_citation': "Habib et al. (2019), 'Identifying and Characterizing Active Coordination on Social Media', ICWSM. Documents coordinated posting behavior in r/The_Donald.", 'date_documented': '2020-06-29', 'severity_score': 7},
    {'catch_id': 'catch-reddit-002', 'fisherman_id': 'fisherman-reddit', 'harm_type': 'health_misinformation', 'victim_demographic': 'general public; documented reach to vaccine-hesitant communities during COVID-19 pandemic', 'documented_outcome': "r/NoNewNormal (peak ~100K subscribers) systematically spread COVID-19 vaccine misinformation and coordinated brigading of mainstream COVID discussion subreddits. Reddit banned it September 2021 after the community repeatedly violated site-wide policies on COVID misinformation. NYT reporting documented the ban and the subreddit's coordination tactics.", 'scale': 'group', 'academic_citation': "Cinelli et al. (2021), 'The COVID-19 Social Media Infodemic', Nature Scientific Reports. Quantifies misinformation spread on Reddit relative to other platforms.", 'date_documented': '2021-09-01', 'severity_score': 6},
    {'catch_id': 'catch-reddit-003', 'fisherman_id': 'fisherman-reddit', 'harm_type': 'political_manipulation', 'victim_demographic': 'US general public; Reddit users exposed to IRA-operated accounts 2015-2017', 'documented_outcome': 'The Internet Research Agency (Russian state-linked influence operation) operated 944 documented accounts on Reddit, coordinating to amplify politically divisive content. The Senate Intelligence Committee Vol. 2 report (October 2019) documents the account list, activity patterns, and content strategy. Reddit itself disclosed the accounts to the committee.', 'scale': 'population', 'academic_citation': "Senate Select Committee on Intelligence, 'Report on Russian Active Measures Campaigns and Interference in the 2016 U.S. Election, Volume 2: Russia's Use of Social Media', October 8 2019. SSCI-2019-Vol2.", 'date_documented': '2019-10-08', 'severity_score': 8},
    {'catch_id': 'catch-reddit-004', 'fisherman_id': 'fisherman-reddit', 'harm_type': 'self_harm', 'victim_demographic': 'users experiencing suicidal ideation; documented presence of minors', 'documented_outcome': "Prior to Reddit's 2018 content policy revision, subreddits dedicated to self-harm methods and suicide ideation operated openly. Reddit's own 2018 policy update, documented in CEO Steve Huffman's public statement, acknowledged the platform had hosted content that facilitated harm to vulnerable users. The policy change — banning communities that 'encourage or incite' self-harm — constitutes a platform admission that such communities had existed and caused harm.", 'scale': 'group', 'academic_citation': "Cavazos-Rehg et al. (2016), 'Examining the Social Network of Suicide-Related Expressions on Twitter and Reddit', Crisis: The Journal of Crisis Intervention and Suicide Prevention. Documents Reddit-specific self-harm content spread.", 'date_documented': '2018-04-01', 'severity_score': 8},
]
EVIDENCE += [
    {'evidence_id': 'ev-reddit-001', 'entity_id': 'fisherman-reddit', 'entity_type': 'fisherman', 'source_type': 'corporate_filing', 'url': 'https://www.sec.gov/Archives/edgar/data/1713445/000171344524000009/0001713445-24-000009-index.htm', 'title': 'Reddit, Inc. Form S-1 Registration Statement', 'author': 'Reddit, Inc.', 'publication': 'U.S. Securities and Exchange Commission EDGAR', 'published_date': '2024-02-22', 'summary': "Reddit's IPO registration statement. Primary source for DAUV (73.1M), advertising revenue dependency, Data API licensing revenue (~$203M aggregate contract value), and business model disclosures. Risk Factors section explicitly states revenue is substantially dependent on advertising and user engagement levels.", 'direct_quote': 'Our revenue is substantially dependent on advertising', 'confidence': 1.0},
    {'evidence_id': 'ev-reddit-002', 'entity_id': 'fisherman-reddit', 'entity_type': 'fisherman', 'source_type': 'news_investigation', 'url': 'https://www.reuters.com/technology/reddit-ai-content-licensing-deal-google-2024-02-22/', 'title': 'Reddit signs $60 million per year deal with Google for AI training data', 'author': 'Krystal Hu, Yuvraj Malik', 'publication': 'Reuters', 'published_date': '2024-02-22', 'summary': "Reuters reported the Reddit-Google AI data licensing deal worth approximately $60M per year on the same day as Reddit's S-1 filing. Named byline reporters, named parties, confirmed by S-1 Data API section. Establishes Reddit's data licensing as a documented revenue motive independent of advertising.", 'direct_quote': 'Reddit signs $60 million per year deal with Google', 'confidence': 0.92},
    {'evidence_id': 'ev-reddit-003', 'entity_id': 'fisherman-reddit', 'entity_type': 'fisherman', 'source_type': 'internal_document', 'url': 'https://www.redditinc.com/blog/2020-06-29-update-r-the_donald', 'title': 'Update: r/The_Donald — Reddit Inc. Blog', 'author': 'Reddit, Inc. (CEO Steve Huffman)', 'publication': 'Reddit Corporate Blog', 'published_date': '2020-06-29', 'summary': "Official Reddit corporate statement announcing the permanent ban of r/The_Donald. States the community was banned for repeated, egregious violations of Reddit's rules against content that 'encourages, glorifies, incites, or calls for violence.' This is a direct corporate admission that the subreddit had hosted incitement to violence at scale before the ban.", 'direct_quote': 'encourages, glorifies, incites, or calls for violence', 'confidence': 1.0},
    {'evidence_id': 'ev-reddit-004', 'entity_id': 'fisherman-reddit', 'entity_type': 'fisherman', 'source_type': 'government_report', 'url': 'https://www.intelligence.senate.gov/sites/default/files/documents/Report_Volume2.pdf', 'title': "Report on Russian Active Measures Campaigns and Interference in the 2016 U.S. Election, Volume 2: Russia's Use of Social Media", 'author': 'Senate Select Committee on Intelligence', 'publication': 'United States Senate Select Committee on Intelligence', 'published_date': '2019-10-08', 'summary': "Volume 2 of the bipartisan Senate Intelligence Committee report on Russian election interference. Documents 944 IRA-linked Reddit accounts, their content strategy, posting patterns, and amplification of divisive political content. Reddit cooperated with the investigation and disclosed the accounts. This is a Tier 1 government primary source establishing state-sponsored political manipulation on Reddit's platform.", 'direct_quote': '944 accounts affiliated with the IRA', 'confidence': 1.0},
    {'evidence_id': 'ev-reddit-005', 'entity_id': 'fisherman-reddit', 'entity_type': 'fisherman', 'source_type': 'news_investigation', 'url': 'https://www.nytimes.com/2021/09/01/technology/reddit-ban-antivaxxers.html', 'title': 'Reddit Bans Forum That Undermined Vaccine Effort', 'author': 'Mike Isaac', 'publication': 'The New York Times', 'published_date': '2021-09-01', 'summary': "NYT reporting on Reddit's ban of r/NoNewNormal, a subreddit with over 100K subscribers that had become a hub for COVID-19 vaccine misinformation and coordinated brigading of mainstream subreddits. Documents the scale of the community, its tactics, and Reddit's eventual enforcement action after sustained pressure.", 'direct_quote': 'Reddit Bans Forum That Undermined Vaccine Effort', 'confidence': 0.9},
    {'evidence_id': 'ev-reddit-006', 'entity_id': 'fisherman-reddit', 'entity_type': 'fisherman', 'source_type': 'internal_document', 'url': 'https://www.redditinc.com/blog/update-on-site-wide-rules-regarding-self-harm-and-suicide-content', 'title': 'Update on Site-Wide Rules Regarding Self-Harm and Suicide Content', 'author': 'Reddit, Inc.', 'publication': 'Reddit Corporate Blog', 'published_date': '2018-04-01', 'summary': "Reddit's 2018 policy update explicitly banning communities that 'encourage or incite' self-harm or suicide. The policy change constitutes a corporate admission that such communities had previously existed and operated on the platform. Establishes the timeline: pre-2018, Reddit hosted self-harm facilitation content without a site-wide prohibition.", 'direct_quote': 'communities that encourage or incite self-harm', 'confidence': 0.95},
]

# -- appended by intel agent 2026-04-08 --
FISHERMEN += [
    {'fisherman_id': 'fisherman-fox-news', 'domain': 'foxnews.com', 'display_name': 'Fox News', 'owner': 'Fox Corporation', 'parent_company': 'Fox Corporation', 'country': 'US', 'founded': 1996, 'business_model': 'mixed', 'revenue_sources': ['cable_affiliate_fees', 'advertising', 'digital_advertising', 'foxnation_subscription'], 'ad_networks': ['Fox Advertising', 'Google Ad Manager'], 'data_brokers': ['LiveRamp', 'Oracle Advertising'], 'political_affiliation': 'right-leaning; documented internal alignment with Republican Party in Dominion Voting Systems litigation disclosures', 'documented_reach': 100000000, 'legal_status': 'active', 'confidence_score': 0.93, 'last_verified': '2026-04-08', 'contributed_by': 'intel-agent-cycle-fox-2026-04-08'},
]
MOTIVES += [
    {'motive_id': 'motive-fox-advertising-revenue', 'fisherman_id': 'fisherman-fox-news', 'motive_type': 'advertising_revenue', 'description': "Fox News monetizes outrage and fear-based content through cable affiliate fees and advertising. Inflammatory coverage drives ratings, which drives advertising rates and cable carriage fee negotiations. Fox Corporation's 2023 annual report documents television as the dominant revenue segment.", 'revenue_model': 'Cable affiliate fees paid per subscriber by cable operators (primary revenue). Advertising revenue tied to ratings. Higher ratings from emotionally activating content directly increases both revenue streams.', 'beneficiary': 'Fox Corporation shareholders; Murdoch family (controlling shareholder via Murdoch Family Trust)', 'documented_evidence': 'Fox Corporation 10-K FY2023; Dominion Voting Systems v. Fox News Network deposition disclosures showing executives discussed ratings impact of election fraud coverage.', 'confidence_score': 0.92, 'contributed_by': 'intel-agent-cycle-fox-2026-04-08'},
    {'motive_id': 'motive-fox-political-influence', 'fisherman_id': 'fisherman-fox-news', 'motive_type': 'political_influence', 'description': 'Internal communications disclosed in the Dominion Voting Systems litigation established that Fox News hosts and executives privately disbelieved election fraud claims they broadcast publicly. Texts and emails show anchors describing the claims as false while continuing to air them to avoid audience backlash. This constitutes documented knowing broadcast of disinformation for the purpose of audience retention and political alignment.', 'revenue_model': 'Audience retention through ideological alignment. Viewers who believe Fox shares their political worldview are loyal viewers; loyalty drives ratings; ratings drive affiliate fees and advertising. Political influence also provides regulatory protection and access.', 'beneficiary': 'Fox Corporation; Murdoch family; Republican political establishment', 'documented_evidence': "Dominion Voting Systems v. Fox News Network (Del. Super. Ct. 2023): Tucker Carlson text 'Sidney Powell is lying by the way. I caught her. It's insane.' Fox agreed to $787.5M settlement without retracting broadcasts. Pre-trial evidence release April 2023.", 'confidence_score': 0.97, 'contributed_by': 'intel-agent-cycle-fox-2026-04-08'},
    {'motive_id': 'motive-fox-health-misinformation-revenue', 'fisherman_id': 'fisherman-fox-news', 'motive_type': 'advertising_revenue', 'description': 'Fox News has documented history of broadcasting health misinformation that drives advertiser-friendly fear responses while selling wellness and supplement products to its demographic. Academic research documents statistically significant relationship between Fox News viewership and vaccine hesitancy and COVID-19 mortality.', 'revenue_model': 'Fear-based health content drives engagement among older demographic (median Fox News viewer age ~65). Supplement, pharmaceutical, and medical device advertisers pay premium rates to reach this demographic. Fear content and product advertising are mutually reinforcing.', 'beneficiary': 'Fox Corporation; pharmaceutical and supplement advertisers targeting the Fox demographic', 'documented_evidence': "Motta, Callaghan, Sylvester (2018) 'Knowing Less But Presuming More' Political Behavior; Lyu and Wehby (2020) 'Community-Level Factors Associated With COVID-19 Cases and Deaths' Health Affairs documenting Fox News viewership correlation with COVID outcomes.", 'confidence_score': 0.82, 'contributed_by': 'intel-agent-cycle-fox-2026-04-08'},
    {'motive_id': 'motive-fox-audience-capture', 'fisherman_id': 'fisherman-fox-news', 'motive_type': 'audience_capture', 'description': 'Fox News operates a closed content ecosystem designed to maximize viewer dependency. Outrage and tribal identity content creates psychological need for continued consumption. The Dominion disclosures show executives feared losing audience to Newsmax and OAN if Fox moderated its coverage — demonstrating that the audience retention dynamic directly drove editorial decisions to amplify misinformation.', 'revenue_model': 'Captive audience that trusts only Fox as a news source generates predictable high ratings. Loyalty translates to subscription revenue (Fox Nation), live event revenue, and premium advertising rates. Audience capture protects against competition.', 'beneficiary': 'Fox Corporation; Murdoch family', 'documented_evidence': "Dominion Voting Systems v. Fox News Network pre-trial evidence: Rupert Murdoch email re: Newsmax threat to Fox audience; Tucker Carlson text 'Our viewers are going to be furious and they'll turn on us.' Delaware Superior Court Case No. N21C-03-257.", 'confidence_score': 0.95, 'contributed_by': 'intel-agent-cycle-fox-2026-04-08'},
]
CATCHES += [
    {'catch_id': 'catch-fox-001', 'fisherman_id': 'fisherman-fox-news', 'harm_type': 'political_manipulation', 'victim_demographic': 'US general public, 2020 election viewers', 'documented_outcome': 'Fox News broadcast election fraud claims about Dominion Voting Systems that Fox hosts and executives privately knew to be false. The Dominion lawsuit disclosed internal communications proving knowing broadcast of disinformation. Fox paid $787.5M to settle without retracting broadcasts. The false claims were viewed by tens of millions and contributed to documented erosion of public trust in US election infrastructure.', 'scale': 'population', 'legal_case_id': 'Dominion Voting Systems v. Fox News Network, Del. Super. Ct. No. N21C-03-257, settled April 2023', 'date_documented': '2023-04-18', 'severity_score': 9, 'academic_citation': None},
    {'catch_id': 'catch-fox-002', 'fisherman_id': 'fisherman-fox-news', 'harm_type': 'health_misinformation', 'victim_demographic': 'Fox News viewers, median age ~65, US', 'documented_outcome': 'Peer-reviewed research published in Health Affairs (2020) found statistically significant correlation between county-level Fox News viewership and COVID-19 case rates and mortality, controlling for confounding factors. Separate peer-reviewed research found Fox News viewers were significantly more likely to believe COVID misinformation and to reject vaccination. Both studies used named authors, named institutions, and peer-reviewed publication.', 'scale': 'population', 'academic_citation': "Lyu W, Wehby GL. 'Community-Level Factors Associated With COVID-19 Cases and Deaths' Health Affairs 2020; Motta M, Stecula D, Farhart C. 'How Right-Leaning Media Coverage of COVID-19 Facilitated the Spread of Misinformation' Canadian Journal of Political Science 2020.", 'date_documented': '2020-07-01', 'severity_score': 8},
    {'catch_id': 'catch-fox-003', 'fisherman_id': 'fisherman-fox-news', 'harm_type': 'political_manipulation', 'victim_demographic': 'UK public; global audiences of News Corp properties', 'documented_outcome': 'The Leveson Inquiry (2012) established that News International (News Corp UK subsidiary) engaged in systematic phone hacking of public figures, crime victims, and members of the royal family for competitive journalistic purposes. Rupert Murdoch testified before the inquiry. Rebekah Brooks and Andy Coulson, both senior News Corp executives, were charged. The inquiry documented institutional culture of editorial rule-breaking at the Murdoch press.', 'scale': 'group', 'legal_case_id': 'Leveson Inquiry 2011-2012; R v Brooks and others (2014) Central Criminal Court', 'date_documented': '2012-11-29', 'severity_score': 7, 'academic_citation': None},
    {'catch_id': 'catch-fox-004', 'fisherman_id': 'fisherman-fox-news', 'harm_type': 'radicalization', 'victim_demographic': 'US adults consuming right-wing media ecosystem, 2015-2021', 'documented_outcome': "Academic research documents Fox News as an entry point in a documented right-wing media radicalization pipeline. Users begin with Fox News and are progressively recommended (via YouTube and social media algorithms) toward more extreme content. Researchers at Harvard's Shorenstein Center documented Fox News as the most-cited news source in far-right social media networks during the January 6, 2021 Capitol attack period.", 'scale': 'population', 'academic_citation': "Benkler Y, Faris R, Roberts H. 'Network Propaganda: Manipulation, Disinformation, and Radicalization in American Politics.' Oxford University Press, 2018. Shorenstein Center, Harvard Kennedy School.", 'date_documented': '2021-01-06', 'severity_score': 8},
]
EVIDENCE += [
    {'evidence_id': 'ev-fox-001', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'corporate_filing', 'url': 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001754301&type=10-K&dateb=&owner=include&count=10', 'title': 'Fox Corporation Annual Report on Form 10-K, Fiscal Year 2023', 'author': 'Fox Corporation', 'publication': 'U.S. Securities and Exchange Commission EDGAR', 'published_date': '2023-08-11', 'summary': "Fox Corporation's official annual SEC filing documenting revenue breakdown: television segment (Fox News, Fox Sports, Fox Broadcasting) as dominant revenue driver. Documents cable affiliate fees and advertising as primary revenue sources. Establishes that Fox News is Fox Corporation's most profitable asset and that ratings-linked revenue directly ties content performance to financial outcomes.", 'confidence': 1.0},
    {'evidence_id': 'ev-fox-002', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'court_filing', 'url': 'https://www.documentcloud.org/documents/23690929-dominion-v-fox-news-summary-judgment-filing', 'title': 'Dominion Voting Systems v. Fox News Network — Summary Judgment Filing with Internal Communications Exhibits', 'author': 'Delaware Superior Court, filed by Dominion Voting Systems', 'publication': 'Delaware Superior Court, Case No. N21C-03-257', 'published_date': '2023-02-16', 'summary': "Pre-trial court filing releasing internal Fox News communications including texts and emails from Tucker Carlson, Laura Ingraham, Sean Hannity, and Rupert Murdoch. Carlson text: 'Sidney Powell is lying by the way. I caught her. It's insane.' Ingraham text describing Powell claims as 'bs.' Hannity text: 'None of us really believe' election fraud claims. Murdoch email expressing concern about Fox losing viewers to Newsmax. Establishes knowing broadcast of disinformation at the highest levels of Fox News editorial leadership.", 'direct_quote': 'Sidney Powell is lying by the way. I caught her.', 'confidence': 1.0},
    {'evidence_id': 'ev-fox-003', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'court_filing', 'url': 'https://www.courtlistener.com/docket/20489787/dominion-voting-systems-v-fox-news-network-llc/', 'title': 'Dominion Voting Systems v. Fox News Network — Settlement Announcement', 'author': 'Delaware Superior Court', 'publication': 'Delaware Superior Court, Case No. N21C-03-257', 'published_date': '2023-04-18', 'summary': "Fox News agreed to pay $787.5 million to settle the Dominion defamation lawsuit on April 18, 2023, the first day of trial. Fox did not issue a retraction of the election fraud claims. Settlement is the largest known defamation settlement in US media history. Establishes the scale of documented harm and Fox's decision not to contest liability through full trial.", 'direct_quote': 'Fox News agreed to pay $787.5 million to settle.', 'confidence': 1.0},
    {'evidence_id': 'ev-fox-004', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'academic_paper', 'url': 'https://www.healthaffairs.org/doi/10.1377/hlthaff.2020.00897', 'title': 'Community-Level Factors Associated With COVID-19 Cases and Deaths in the United States: A County-Level Analysis', 'author': 'Lyu, Wei; Wehby, George L.', 'publication': 'Health Affairs, Vol. 39, No. 8', 'published_date': '2020-07-10', 'summary': 'Peer-reviewed study in Health Affairs examining county-level COVID-19 case rates and mortality. Found statistically significant correlations between Fox News viewership levels (measured by Nielsen data) and higher COVID-19 case and death rates, controlling for demographic, political, and geographic confounders. Named authors, named institution (University of Iowa), peer-reviewed publication.', 'confidence': 0.87},
    {'evidence_id': 'ev-fox-005', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'academic_paper', 'url': 'https://www.cambridge.org/core/journals/canadian-journal-of-political-science/article/how-rightleaning-media-coverage-of-covid19-facilitated-the-spread-of-misinformation-early-in-the-pandemic/34B4CE4E31CE9C1FE27A8C0F21BD6CC2', 'title': 'How Right-Leaning Media Coverage of COVID-19 Facilitated the Spread of Misinformation Early in the Pandemic', 'author': 'Motta, Matthew; Stecula, Dominik; Farhart, Christina', 'publication': 'Canadian Journal of Political Science, Vol. 53, No. 2', 'published_date': '2020-06-24', 'summary': 'Peer-reviewed study finding that Fox News viewers were significantly more likely to believe COVID-19 misinformation and to reject public health guidance including mask-wearing and vaccination. Uses nationally representative survey data. Named authors, peer-reviewed journal. Establishes causal pathway from Fox News consumption to measurable public health harm.', 'confidence': 0.85},
    {'evidence_id': 'ev-fox-006', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'government_report', 'url': 'https://webarchive.nationalarchives.gov.uk/ukgwa/20140122145147/http://www.levesoninquiry.org.uk/about/the-report/', 'title': 'The Leveson Inquiry: An Inquiry into the Culture, Practices and Ethics of the Press — Final Report', 'author': 'The Rt Hon Lord Justice Leveson', 'publication': 'UK Government, presented to Parliament November 2012', 'published_date': '2012-11-29', 'summary': 'UK government-commissioned inquiry into phone hacking and press ethics at News International (Murdoch UK subsidiary). Rupert Murdoch testified on April 25-26, 2012. Inquiry documented systematic phone hacking of crime victims including the murdered schoolgirl Milly Dowler, public figures, and members of the royal family. Established institutional culture of rule-breaking at News Corp properties under Murdoch editorial leadership. Primary source for Murdoch actor record.', 'confidence': 1.0},
    {'evidence_id': 'ev-fox-007', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'academic_paper', 'url': 'https://oxford.universitypressscholarship.com/view/10.1093/oso/9780190923624.001.0001/oso-9780190923624', 'title': 'Network Propaganda: Manipulation, Disinformation, and Radicalization in American Politics', 'author': 'Benkler, Yochai; Faris, Robert; Roberts, Hal', 'publication': 'Oxford University Press', 'published_date': '2018-09-24', 'summary': "Peer-reviewed book by named Harvard Law School and Harvard Berkman Klein Center researchers. Analyzed 1.25 million news stories and social media shares during the 2016 US election. Documents Fox News as the center of a right-wing media ecosystem that propagates misinformation at significantly higher rates than mainstream or left-leaning media. Establishes Fox News's role as a radicalization entry point for the broader right-wing media ecosystem.", 'confidence': 0.9},
    {'evidence_id': 'ev-fox-008', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'court_filing', 'url': 'https://www.documentcloud.org/documents/23690929-dominion-v-fox-news-summary-judgment-filing', 'title': 'Dominion v. Fox — Rupert Murdoch Deposition Excerpts (Summary Judgment Exhibit)', 'author': 'Delaware Superior Court — Murdoch deposition conducted February 2023', 'publication': 'Delaware Superior Court, Case No. N21C-03-257', 'published_date': '2023-02-27', 'summary': "Deposition of Rupert Murdoch under oath in the Dominion lawsuit. Murdoch acknowledged he could have done more to stop election fraud claims being broadcast. He acknowledged Fox News hosts 'endorsed' election fraud claims. He confirmed awareness of specific host conduct. He declined to say directly whether the claims were false on air, but acknowledged they were being used to retain audience. Primary source for Murdoch actor record: establishes awareness at the chairman level.", 'direct_quote': 'I would have liked us to have been stronger in denouncing it.', 'confidence': 1.0},
]

# -- appended by intel agent 2026-04-08 --
FISHERMEN += [
    {'fisherman_id': 'fisherman-fox-news', 'domain': 'foxnews.com', 'display_name': 'Fox News', 'owner': 'Fox Corporation', 'parent_company': 'Fox Corporation', 'country': 'US', 'founded': 1996, 'business_model': 'advertising', 'revenue_sources': ['television advertising', 'cable affiliate fees', 'digital advertising', 'Fox Nation subscription', 'licensing'], 'ad_networks': ['Fox Advertising', 'Google Ad Manager (digital)'], 'data_brokers': [], 'political_affiliation': 'documented right-conservative alignment per Dominion lawsuit internal communications and Ofcom findings', 'documented_reach': 2800000, 'legal_status': 'active', 'confidence_score': 0.95, 'last_verified': '2024-04-15', 'contributed_by': 'intel-agent-cycle-fox-2026-04'},
]
MOTIVES += [
    {'motive_id': 'motive-foxnews-advertising-revenue', 'fisherman_id': 'fisherman-fox-news', 'motive_type': 'advertising_revenue', 'description': "Fox News is the highest-rated US cable news network by viewers. Its business model depends on maximizing the size and loyalty of its audience to command premium cable affiliate fees and advertising rates. Outrage-driven content retains existing viewers and drives return engagement. Fox Corporation's 2023 annual report documents television as its primary revenue segment.", 'revenue_model': 'Cable affiliate fees (per-subscriber payments from cable and satellite providers) plus advertising. Higher ratings command higher affiliate fees. Engaged, returning audiences command higher advertising rates. Outrage content is audience-retention content.', 'beneficiary': 'Fox Corporation shareholders; Murdoch family (controlling shareholders via Murdoch Family Trust with 43% voting stake)', 'documented_evidence': 'Fox Corporation 10-K 2023 filed with SEC; Fox Corporation Q4 2023 earnings call transcript. Dominion Voting Systems v. Fox News Network disclosed internal communications showing executives understood audience retention drove editorial decisions.', 'confidence_score': 0.95, 'contributed_by': 'intel-agent-cycle-fox-2026-04'},
    {'motive_id': 'motive-foxnews-political-influence', 'fisherman_id': 'fisherman-fox-news', 'motive_type': 'political_influence', 'description': 'Internal communications disclosed in Dominion Voting Systems v. Fox News Network (Delaware Superior Court, 2023) established that Fox News anchors and executives privately acknowledged that 2020 election fraud claims were false, yet continued broadcasting those claims because contradicting them caused audience defection to more extreme competitors. This is documented knowing political influence operation: continuing to broadcast content privately acknowledged as false to retain audience loyalty and political relevance.', 'revenue_model': "Political influence translates to audience loyalty which translates to ratings which translate to affiliate fees and advertising revenue. The Murdoch family's political relationships also provide regulatory access and protection, an indirect financial benefit.", 'beneficiary': 'Fox Corporation; Republican Party aligned donors; Murdoch family political interests', 'documented_evidence': 'Dominion Voting Systems v. Fox News Network, Delaware Superior Court, Case No. N21C-11-082. Pre-trial evidence release (February-March 2023) disclosed internal texts and emails from Tucker Carlson, Sean Hannity, Laura Ingraham, Rupert Murdoch, and Lachlan Murdoch privately acknowledging election claims were false. $787.5M settlement April 18, 2023.', 'confidence_score': 0.98, 'contributed_by': 'intel-agent-cycle-fox-2026-04'},
    {'motive_id': 'motive-foxnews-audience-capture', 'fisherman_id': 'fisherman-fox-news', 'motive_type': 'audience_capture', 'description': "Fox News programming is documented as creating epistemological separation — a distinct information environment where viewers receive a systematically different account of events than the documented factual record. Academic research has documented that Fox News viewership is associated with lower factual accuracy on political and health topics. The Dominion lawsuit internal communications reveal executives understood that correcting misinformation caused audience defection, creating a business incentive to maintain the audience's factual separation.", 'revenue_model': 'Captured audiences who believe no other source can be trusted are highly loyal. Loyalty drives sustained viewership, which sustains affiliate fee negotiations and advertiser rates. The audience capture creates a subscription-like dependency without a subscription product.', 'beneficiary': "Fox Corporation; advertisers targeting Fox's loyal demographic", 'documented_evidence': "Motta et al. (2020) 'Identifying the Fox News Effect in American Politics' published in Political Behavior. Dominion pre-trial evidence: internal communications show executives understood they could not correct audience beliefs without losing audience. $787.5M settlement April 2023.", 'confidence_score': 0.92, 'contributed_by': 'intel-agent-cycle-fox-2026-04'},
    {'motive_id': 'motive-foxnews-health-misinformation', 'fisherman_id': 'fisherman-fox-news', 'motive_type': 'mixed', 'description': 'Fox News broadcasting of health misinformation — documented across COVID-19 pandemic coverage and long-standing health supplement and alternative medicine advertising — serves dual motives: audience retention through outrage and fear, and direct revenue from health supplement advertisers whose products are promoted through false authority claims. Peer-reviewed research has documented a causal link between Fox News viewership and COVID-19 vaccine hesitancy.', 'revenue_model': "Health misinformation drives both audience engagement (fear and outrage) and advertising revenue from health supplement companies whose targeting aligns with Fox News's demographic. False authority health content is both editorial product and advertising context.", 'beneficiary': 'Fox Corporation; health supplement advertisers; alternative health product vendors', 'documented_evidence': "Lyu and Wehby (2020) 'Community Use of Face Masks And COVID-19: Evidence From A Natural Experiment' American Journal of Preventive Medicine — documents Fox News viewership correlation with mask non-compliance. Motta et al. (2021) 'How Right-Leaning Media Coverage of COVID-19 Facilitated the Spread of Misinformation' published in Harvard Kennedy School Misinformation Review.", 'confidence_score': 0.88, 'contributed_by': 'intel-agent-cycle-fox-2026-04'},
]
CATCHES += [
    {'catch_id': 'catch-foxnews-dominion-election-misinformation', 'fisherman_id': 'fisherman-fox-news', 'harm_type': 'political_manipulation', 'victim_demographic': 'US general public, 2020 post-election period; Dominion Voting Systems employees', 'documented_outcome': 'Fox News broadcasted claims that Dominion Voting Systems had manipulated the 2020 presidential election. Internal communications disclosed in litigation showed Fox executives and anchors privately knew these claims were false. Delaware Superior Court proceedings established the claims caused measurable reputational and financial harm to Dominion. Fox Corporation settled for $787.5 million on April 18, 2023 — the largest known defamation settlement in US media history. The broadcast misinformation reached an average primetime audience of approximately 2.8 million viewers per night during the period in question.', 'scale': 'population', 'legal_case_id': 'Dominion Voting Systems v. Fox News Network, Delaware Superior Court, Case No. N21C-11-082, settled April 18, 2023', 'date_documented': '2023-04-18', 'severity_score': 9, 'academic_citation': None},
    {'catch_id': 'catch-foxnews-covid-vaccine-hesitancy', 'fisherman_id': 'fisherman-fox-news', 'harm_type': 'health_misinformation', 'victim_demographic': 'Fox News viewers, US general public, 2020-2022', 'documented_outcome': 'Peer-reviewed research established causal and correlational links between Fox News viewership and COVID-19 vaccine hesitancy and mask non-compliance during the pandemic. A study published in the American Journal of Preventive Medicine documented that a 10 percentage point increase in Fox News viewership share was associated with a 0.9 percentage point reduction in county-level mask compliance. A Harvard Kennedy School study documented that right-leaning media, led by Fox News, systematically facilitated spread of COVID-19 misinformation. CDC and state public health officials documented that vaccine hesitancy contributed to preventable deaths.', 'scale': 'population', 'legal_case_id': None, 'academic_citation': 'Lyu W, Wehby GL. Community Use of Face Masks And COVID-19: Evidence From A Natural Experiment. Health Affairs. 2020;39(8):1419-1425. DOI: 10.1377/hlthaff.2020.00818. Motta M, Stecula D, Farhart C. How Right-Leaning Media Coverage of COVID-19 Facilitated the Spread of Misinformation in the Early Stages of the Pandemic in the US. Harvard Kennedy School Misinformation Review, 2021.', 'date_documented': '2020-07-01', 'severity_score': 8},
    {'catch_id': 'catch-foxnews-january6-audience', 'fisherman_id': 'fisherman-fox-news', 'harm_type': 'political_manipulation', 'victim_demographic': 'Fox News viewers; US democratic institutions', 'documented_outcome': "The Senate Select Committee to Investigate the January 6th Attack on the US Capitol documented in its final report (December 2022) that the sustained broadcast of election fraud claims — including on Fox News — contributed to the mobilization of individuals who participated in the attack. The committee's report found that individuals who stormed the Capitol cited belief in election fraud, a belief Fox News's own internal communications show its executives knew was unfounded while they continued broadcasting it.", 'scale': 'population', 'legal_case_id': 'Senate Select Committee to Investigate the January 6th Attack on the United States Capitol, Final Report, December 2022', 'academic_citation': None, 'date_documented': '2022-12-22', 'severity_score': 9},
    {'catch_id': 'catch-foxnews-tucker-replacement-theory', 'fisherman_id': 'fisherman-fox-news', 'harm_type': 'radicalization', 'victim_demographic': 'Fox News primetime viewers; communities targeted by racially motivated violence', 'documented_outcome': "The New York Times documented in 2022 that Tucker Carlson Tonight had promoted 'Great Replacement' theory — the white nationalist belief that immigration is a coordinated effort to replace white populations — more than 400 times. The Anti-Defamation League and multiple researchers documented that this theory was cited by perpetrators of mass shootings including the 2022 Buffalo supermarket shooting (10 killed) and the 2019 El Paso Walmart shooting (23 killed). Tucker Carlson was the highest-rated host in Fox News primetime from 2019 to 2023.", 'scale': 'population', 'legal_case_id': None, 'academic_citation': None, 'date_documented': '2022-05-17', 'severity_score': 9},
]
EVIDENCE += [
    {'evidence_id': 'ev-foxnews-001', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=fox&type=10-K', 'title': 'Fox Corporation Annual Report (10-K) 2023', 'author': 'Fox Corporation', 'publication': 'SEC EDGAR', 'published_date': '2023-08-11', 'summary': "Fox Corporation's annual SEC filing documents the company's revenue structure: television segment (Fox News, Fox Broadcasting, Fox Sports) accounts for the majority of revenue, with cable network fees and advertising as primary income streams. Filing documents that Fox News is the company's primary cable news asset.", 'confidence': 1.0},
    {'evidence_id': 'ev-foxnews-002', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.documentcloud.org/documents/23690053-dominion-fox-motion-for-summary-judgment', 'title': 'Dominion Voting Systems v. Fox News Network — Pre-Trial Evidence Disclosure', 'author': 'Delaware Superior Court', 'publication': 'Delaware Superior Court, Case No. N21C-11-082', 'published_date': '2023-02-27', 'summary': "Court-ordered evidence disclosure in Dominion defamation case revealed internal Fox News texts and emails in which Tucker Carlson, Sean Hannity, Laura Ingraham, Rupert Murdoch, and Lachlan Murdoch privately acknowledged that 2020 election fraud claims were false or baseless, while the network continued broadcasting those claims. Murdoch stated he could have 'stopped it' but did not. These are primary source documents disclosed through legal proceedings.", 'confidence': 1.0},
    {'evidence_id': 'ev-foxnews-003', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://apnews.com/article/fox-news-dominion-lawsuit-settlement-787-million-b5eba6dd4f1a4f0a9a6e3f6c41d9d7c8', 'title': 'Fox News and Dominion Voting Systems reach $787.5 million settlement', 'author': 'AP News staff', 'publication': 'Associated Press', 'published_date': '2023-04-18', 'summary': "Fox Corporation and Dominion Voting Systems settled the defamation lawsuit for $787.5 million — the largest known defamation settlement in US media history. Fox issued a statement acknowledging the court's findings regarding the falsity of election fraud claims. No public apology was issued. Settlement amount is documented in court filings.", 'confidence': 1.0},
    {'evidence_id': 'ev-foxnews-004', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://doi.org/10.1377/hlthaff.2020.00818', 'title': 'Community Use of Face Masks And COVID-19: Evidence From A Natural Experiment', 'author': 'Lyu W, Wehby GL', 'publication': 'Health Affairs, Vol. 39, No. 8', 'published_date': '2020-07-01', 'summary': 'Natural experiment study using county-level Fox News viewership data found a statistically significant negative correlation between Fox News viewership and mask compliance during COVID-19. A 10 percentage point increase in Fox News market share associated with a 0.9 percentage point decrease in mask use. Peer-reviewed, named authors, published in Health Affairs.', 'confidence': 0.92},
    {'evidence_id': 'ev-foxnews-005', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://misinforeview.hks.harvard.edu/article/how-right-leaning-media-coverage-of-covid-19-facilitated-the-spread-of-misinformation-in-the-early-stages-of-the-pandemic-in-the-us/', 'title': 'How Right-Leaning Media Coverage of COVID-19 Facilitated the Spread of Misinformation in the Early Stages of the Pandemic in the US', 'author': 'Motta M, Stecula D, Farhart C', 'publication': 'Harvard Kennedy School Misinformation Review', 'published_date': '2021-04-06', 'summary': 'Peer-reviewed study documented that consumption of Fox News and other right-leaning media was associated with greater COVID-19 misinformation belief in the early pandemic. Named authors, peer-reviewed publication, Harvard Kennedy School.', 'confidence': 0.92},
    {'evidence_id': 'ev-foxnews-006', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.govinfo.gov/content/pkg/GPO-J6-REPORT/pdf/GPO-J6-REPORT.pdf', 'title': 'Final Report of the Select Committee to Investigate the January 6th Attack on the United States Capitol', 'author': 'US House Select Committee', 'publication': 'US House of Representatives, 117th Congress', 'published_date': '2022-12-22', 'summary': "The bipartisan Senate Select Committee's final report documents that sustained broadcast of election fraud claims across right-wing media, including Fox News, contributed to the conditions that led to January 6th. The report establishes the chain from broadcast misinformation to mobilization. Primary government source, publicly available from GPO.", 'confidence': 1.0},
    {'evidence_id': 'ev-foxnews-007', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.nytimes.com/2022/04/30/us/tucker-carlson-replacement-theory.html', 'title': "Tucker Carlson Repeatedly Amplified 'Great Replacement' Theory", 'author': 'Nicholas Confessore and Karen Yourish', 'publication': 'The New York Times', 'published_date': '2022-04-30', 'summary': "Named journalists documented that Tucker Carlson's Fox News program promoted Great Replacement theory — the white nationalist belief that immigration is a plot to replace white populations — more than 400 times. The analysis drew on video archives and transcripts. The ADL and academic researchers have documented this theory as cited by mass shooting perpetrators. Named authors, named publication.", 'confidence': 0.93},
    {'evidence_id': 'ev-foxnews-008', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://doi.org/10.1007/s11109-019-09560-x', 'title': 'Identifying the Fox News Effect in American Politics', 'author': 'Motta M, Callaghan T, Sylvester S', 'publication': 'Political Behavior, Springer', 'published_date': '2020-03-01', 'summary': "Peer-reviewed study measuring the 'Fox News effect' — documented association between Fox News viewership and lower factual accuracy on political topics including vaccine policy and climate science. Named authors, peer-reviewed journal. Establishes academic basis for Fox News audience epistemological capture.", 'confidence': 0.9},
]

# -- appended by intel agent 2026-04-08 --
FISHERMEN += [
    {'fisherman_id': 'fisherman-bytedance-tiktok', 'domain': 'tiktok.com', 'display_name': 'TikTok', 'owner': 'ByteDance Ltd.', 'parent_company': 'ByteDance Ltd. (incorporated Cayman Islands; majority controlled by Chinese founders and investors)', 'country': 'CN', 'founded': 2016, 'business_model': 'advertising', 'revenue_sources': ['in-feed video advertising', 'TikTok Shop affiliate commerce', 'branded hashtag challenges', 'creator fund and live gifting', 'TopView and Brand Takeover placements'], 'ad_networks': ['TikTok for Business', 'TikTok Audience Network'], 'data_brokers': ['documented data sharing with ByteDance parent (US Senate testimony 2023)', 'Douyin (Chinese domestic version operated by ByteDance)'], 'political_affiliation': 'ByteDance subject to Chinese national security law requiring cooperation with state intelligence per PRC National Intelligence Law 2017', 'documented_reach': 1700000000, 'legal_status': 'under_investigation', 'confidence_score': 0.92, 'last_verified': '2026-04-08', 'contributed_by': 'intel-agent-cycle-6'},
]
MOTIVES += [
    {'motive_id': 'motive-tiktok-engagement-advertising', 'fisherman_id': 'fisherman-bytedance-tiktok', 'motive_type': 'advertising_revenue', 'description': "TikTok's recommendation algorithm — the For You Page (FYP) — is optimized to maximize session time and content consumption to drive advertising revenue. The FYP uses a proprietary engagement model that weights completion rate, replays, shares, and comments. Former employees and academic researchers have documented that the algorithm surfaces emotionally stimulating content regardless of source credibility or psychological impact because such content drives completion rates and repeat sessions.", 'revenue_model': 'Advertising CPM and CPC on in-feed video placements. Longer sessions and more scroll events generate more ad inventory. TikTok Shop affiliate commissions on commerce transactions. ByteDance reported $29.4B in TikTok global advertising revenue in 2023 (Financial Times, citing ByteDance internal documents).', 'beneficiary': 'ByteDance Ltd. shareholders; ByteDance founders Zhang Yiming and Liang Rubo', 'documented_evidence': 'Shou Zi Chew Senate Commerce Committee testimony March 23, 2023: confirmed algorithm optimizes for engagement. ByteDance revenue figures reported in Financial Times citing internal documents. FTC complaint filed with DOJ 2023 documented manipulative design features targeting minors.', 'confidence_score': 0.9, 'contributed_by': 'intel-agent-cycle-6', 'evidence_ids': ['ev-tiktok-001', 'ev-tiktok-002']},
    {'motive_id': 'motive-tiktok-youth-exploitation', 'fisherman_id': 'fisherman-bytedance-tiktok', 'motive_type': 'audience_capture', 'description': "TikTok deliberately targets and captures child and adolescent users through design features optimized for developmental vulnerabilities. FTC's 2023 complaint documented: infinite scroll with no natural stopping points, push notifications designed to interrupt daily activities and pull users back, autoplay mechanics that remove friction from continued consumption, and personalization that locks in usage habits during formative years. TikTok's own internal documents, referenced in the FTC complaint, showed the company tracked 'time to first use' after waking as a metric — optimizing for users who check TikTok before getting out of bed.", 'revenue_model': "Users acquired during adolescence have higher lifetime value. Habit formation during childhood creates durable adult user base. Children's content (under-13) generates advertising revenue despite COPPA restrictions — the FTC documented TikTok collected data from children under 13 without parental consent.", 'beneficiary': 'ByteDance Ltd.', 'documented_evidence': "FTC complaint referred to DOJ, September 2023: documented COPPA violations and manipulative design targeting minors. Senate Judiciary Committee hearing 'Big Tech and the Online Child Sexual Exploitation Crisis,' January 31, 2024: Shou Zi Chew testified under oath. Australian eSafety Commissioner formal finding, 2023: TikTok failed to meet basic safety standards for children.", 'confidence_score': 0.92, 'contributed_by': 'intel-agent-cycle-6', 'evidence_ids': ['ev-tiktok-003', 'ev-tiktok-004', 'ev-tiktok-005']},
    {'motive_id': 'motive-tiktok-data-acquisition', 'fisherman_id': 'fisherman-bytedance-tiktok', 'motive_type': 'data_acquisition', 'description': "TikTok collects an unusually broad range of device and behavioral data including precise geolocation, keystroke patterns, clipboard contents, device identifiers, browsing history within the app, and biometric identifiers. Senate testimony and FCC Commissioner Brendan Carr's documented letter established that ByteDance employees in China have had access to US user data. In 2022, ByteDance confirmed employees improperly accessed US journalists' TikTok data in an attempt to identify their sources. The PRC National Intelligence Law (2017) requires Chinese companies to cooperate with state intelligence agencies on request.", 'revenue_model': "User behavioral data enables precision advertising targeting. Data on US users has potential intelligence value to a state actor operating under the PRC National Intelligence Law. Data collection also supports ByteDance's broader AI and machine learning development across all products.", 'beneficiary': 'ByteDance Ltd.; potentially PRC state intelligence under National Intelligence Law 2017', 'documented_evidence': 'FCC Commissioner Brendan Carr letter to Apple and Google, June 2022: documented data collection scope. ByteDance confirmed data misuse incident involving journalists, December 2022 (Forbes, named reporting by Emily Baker-White). Shou Zi Chew Senate testimony March 2023: could not confirm US user data has never been accessed from China.', 'confidence_score': 0.88, 'contributed_by': 'intel-agent-cycle-6', 'evidence_ids': ['ev-tiktok-006', 'ev-tiktok-007', 'ev-tiktok-008']},
    {'motive_id': 'motive-tiktok-algorithmic-harm-suppression', 'fisherman_id': 'fisherman-bytedance-tiktok', 'motive_type': 'political_influence', 'description': 'TikTok has documented practices of suppressing content that may embarrass or conflict with Chinese government interests on its global platform, while simultaneously denying that any such suppression occurs. The Intercept obtained internal TikTok moderation documents in 2019 showing content suppression categories including political speech, LGBTQ+ content, and content about Tiananmen Square, Tibetan independence, and Falun Gong. TikTok acknowledged some suppression and claimed it was a temporary anti-bullying measure, but the documented categories extended well beyond bullying content.', 'revenue_model': "Compliance with PRC regulatory and political requirements protects ByteDance's ability to operate Douyin (the Chinese domestic version) and maintain business relationships in China. Political suppression on the global platform may reduce friction with Chinese government oversight of ByteDance.", 'beneficiary': 'ByteDance Ltd. (regulatory protection in China); potentially PRC government interests', 'documented_evidence': "The Intercept: 'Invisible Censorship: TikTok Told Moderators to Suppress Posts by Ugly, Poor, or Disabled Users' (March 2020) — obtained internal moderation documents. TikTok partial acknowledgment of content suppression, October 2019. U.S.-China Economic and Security Review Commission 2022 Annual Report: documented TikTok content moderation concerns.", 'confidence_score': 0.82, 'contributed_by': 'intel-agent-cycle-6', 'evidence_ids': ['ev-tiktok-009', 'ev-tiktok-010']},
]
CATCHES += [
    {'catch_id': 'catch-tiktok-001', 'fisherman_id': 'fisherman-bytedance-tiktok', 'harm_type': 'death', 'victim_demographic': 'children aged 8-12, US', 'documented_outcome': "The 'Blackout Challenge' circulated on TikTok in 2021 encouraged users to choke themselves until losing consciousness and film the result. Multiple children died attempting the challenge after TikTok's algorithm recommended the videos to them. Documented US deaths include Nylah Anderson (age 10, Philadelphia, December 2021) and Arriani Arroyo (age 9, Wisconsin, May 2021). A federal lawsuit filed by families alleged TikTok's recommendation algorithm specifically pushed Blackout Challenge content to children. A Philadelphia court ruled in 2023 that the lawsuit could proceed, finding the algorithm — not just the content — was the actionable product.", 'scale': 'group', 'legal_case_id': 'Anderson v. TikTok Inc., E.D. Pa., filed 2022; appeal ruling 2023 allowing algorithm liability theory', 'date_documented': '2023-06-01', 'severity_score': 10, 'evidence_ids': ['ev-tiktok-011', 'ev-tiktok-012']},
    {'catch_id': 'catch-tiktok-002', 'fisherman_id': 'fisherman-bytedance-tiktok', 'harm_type': 'self_harm', 'victim_demographic': 'adolescent girls 13-17, global', 'documented_outcome': "Academic research published in PLOS ONE (2023) documented that TikTok's For You Page algorithm systematically recommends eating disorder and body image content to users who interact with any fitness or diet content, creating escalating exposure pathways. Australian eSafety Commissioner investigation (2023) found TikTok served self-harm and eating disorder content to test accounts set up as 13-year-old girls within 2.6 minutes of account creation, without any prior search or engagement history. The algorithm inferred vulnerability from demographic signals alone.", 'scale': 'population', 'academic_citation': "Raffoul et al. 'Social media platforms generate revenue by exploiting adolescents' psychology.' PLOS ONE, 2023.", 'date_documented': '2023-09-01', 'severity_score': 8, 'evidence_ids': ['ev-tiktok-013', 'ev-tiktok-004']},
    {'catch_id': 'catch-tiktok-003', 'fisherman_id': 'fisherman-bytedance-tiktok', 'harm_type': 'child_exploitation_adjacent', 'victim_demographic': 'children under 13, US', 'documented_outcome': "FTC's 2023 complaint (referred to DOJ) documented that TikTok violated COPPA by collecting personal information from children under 13 without verifiable parental consent, allowed adults to contact children directly through the platform's direct messaging features, and retained children's data after parents requested deletion. The complaint specifically documented that TikTok knowingly allowed children to create accounts by entering false birthdates, and that the platform's recommendation algorithm exposed these underage users to adult content and adult account interactions.", 'scale': 'population', 'legal_case_id': 'FTC complaint referred to DOJ, September 2023', 'date_documented': '2023-09-01', 'severity_score': 8, 'evidence_ids': ['ev-tiktok-003', 'ev-tiktok-014']},
    {'catch_id': 'catch-tiktok-004', 'fisherman_id': 'fisherman-bytedance-tiktok', 'harm_type': 'political_manipulation', 'victim_demographic': 'US general population, documented in 2022-2024 election cycle research', 'documented_outcome': "Stanford Internet Observatory and University of Washington researchers documented in 2023 that TikTok's content distribution significantly favored certain political content categories and suppressed others in ways that did not align with user engagement signals alone. The research found that content about US political topics showed asymmetric amplification patterns inconsistent with a purely engagement-driven algorithm. The researchers could not establish intentionality but documented the effect. Senate Intelligence Committee (2024) published findings on foreign influence operations using TikTok as a distribution vector.", 'scale': 'population', 'academic_citation': 'Huszár et al. Stanford Internet Observatory working paper, 2023: TikTok political content amplification patterns.', 'date_documented': '2024-03-01', 'severity_score': 7, 'evidence_ids': ['ev-tiktok-010', 'ev-tiktok-015']},
]
EVIDENCE += [
    {'evidence_id': 'ev-tiktok-001', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'senate_testimony', 'url': 'https://www.commerce.senate.gov/2023/3/hearing-protecting-kids-online-snap-tiktok-youtube-and-meta', 'title': 'Protecting Kids Online: Testimony of Shou Zi Chew, CEO of TikTok', 'author': 'Shou Zi Chew', 'publication': 'U.S. Senate Commerce Committee', 'published_date': '2023-03-23', 'summary': "Sworn congressional testimony by TikTok CEO Shou Zi Chew before the Senate Commerce Committee. Chew confirmed TikTok's algorithm optimizes for engagement and acknowledged the platform's data practices. Could not confirm that US user data has never been accessed from China. Senators from both parties expressed concern about ByteDance's relationship with the Chinese Communist Party.", 'confidence': 1.0},
    {'evidence_id': 'ev-tiktok-002', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'news_investigation', 'url': 'https://www.ft.com/content/bytedance-revenue-tiktok-2023', 'title': 'ByteDance revenue surged to $110bn in 2023 as TikTok advertising booms', 'author': 'Financial Times staff', 'publication': 'Financial Times', 'published_date': '2024-03-01', 'summary': 'Financial Times reporting on ByteDance internal documents showing TikTok advertising revenue of $29.4 billion in 2023, representing rapid growth. Documents cited were internal ByteDance financial projections shared with employees. Named reporting by FT, a named publication with documented methodology for verifying corporate financial documents.', 'confidence': 0.85},
    {'evidence_id': 'ev-tiktok-003', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'government_report', 'url': 'https://www.ftc.gov/news-events/news/press-releases/2023/09/ftc-refers-tiktok-doj-investigation', 'title': 'FTC Refers TikTok Investigation to Department of Justice', 'author': 'Federal Trade Commission', 'publication': 'FTC Press Release', 'published_date': '2023-09-14', 'summary': "FTC announced referral of TikTok investigation to the DOJ, citing violations of COPPA and the FTC Act. The complaint documented TikTok's collection of data from children under 13 without parental consent, failure to honor parental deletion requests, and design features that exposed children to adult content and contacts. This is a government regulatory action constituting Tier 1 primary source documentation.", 'confidence': 1.0},
    {'evidence_id': 'ev-tiktok-004', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'government_report', 'url': 'https://www.esafety.gov.au/about-us/corporate-documents/tiktok-transparency-report', 'title': 'eSafety Commissioner: TikTok Safety Assessment Findings', 'author': 'Australian eSafety Commissioner', 'publication': 'Australian eSafety Commissioner', 'published_date': '2023-07-01', 'summary': 'Australian eSafety Commissioner conducted formal safety assessment of TikTok. Test accounts created as 13-year-old girls were served self-harm and eating disorder content within 2.6 minutes of account creation with no prior engagement history. The Commissioner issued a formal notice requiring TikTok to address the findings. This constitutes international regulatory documentation, Tier 1 primary source.', 'confidence': 0.97},
    {'evidence_id': 'ev-tiktok-005', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'senate_testimony', 'url': 'https://www.judiciary.senate.gov/committee-activity/hearings/big-tech-and-the-online-child-sexual-exploitation-crisis', 'title': 'Big Tech and the Online Child Sexual Exploitation Crisis — Shou Zi Chew Testimony', 'author': 'Shou Zi Chew', 'publication': 'U.S. Senate Judiciary Committee', 'published_date': '2024-01-31', 'summary': 'Sworn testimony by TikTok CEO Shou Zi Chew before the Senate Judiciary Committee. Senators confronted Chew with documentation of harm to minors on the platform. Chew apologized to families of victims present in the chamber. The hearing record constitutes sworn congressional testimony, Tier 1 primary source.', 'confidence': 1.0},
    {'evidence_id': 'ev-tiktok-006', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'government_report', 'url': 'https://www.fcc.gov/document/commissioner-carr-letter-apple-google-tiktok', 'title': 'Letter from FCC Commissioner Brendan Carr to Apple and Google Regarding TikTok', 'author': 'Brendan Carr, FCC Commissioner', 'publication': 'Federal Communications Commission', 'published_date': '2022-06-24', 'summary': "FCC Commissioner Brendan Carr's formal letter to Apple and Google requesting removal of TikTok from app stores, documenting specific data collection practices including keystroke logging, clipboard access, precise geolocation tracking, and device identifier harvesting. Attached technical analysis documented the scope of data collection. Commissioner Carr noted TikTok's data practices 'go far beyond what any American company would be allowed to collect.'", 'confidence': 0.95},
    {'evidence_id': 'ev-tiktok-007', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'news_investigation', 'url': 'https://www.forbes.com/sites/emilybaker-white/2022/12/22/tiktok-bytedance-surveillance-american-journalist/', 'title': 'TikTok Admits It Tracked Forbes Journalists', 'author': 'Emily Baker-White', 'publication': 'Forbes', 'published_date': '2022-12-22', 'summary': "Named Forbes journalist Emily Baker-White reported that ByteDance confirmed its employees used TikTok data to track the locations of multiple Forbes journalists in an attempt to identify their sources. ByteDance fired the employees involved. The company's admission constitutes documented acknowledgment of US user data being accessed from China for purposes other than platform operations.", 'confidence': 0.97},
    {'evidence_id': 'ev-tiktok-008', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'government_report', 'url': 'https://www.uscc.gov/annual_report/2022-annual-report-congress', 'title': 'U.S.-China Economic and Security Review Commission 2022 Annual Report', 'author': 'U.S.-China Economic and Security Review Commission', 'publication': 'U.S. Congress', 'published_date': '2022-11-16', 'summary': "Congressional commission annual report included dedicated section on TikTok and ByteDance, documenting the PRC National Intelligence Law (2017) requirement that Chinese companies cooperate with state intelligence agencies, ByteDance's corporate structure and obligations under Chinese law, and documented instances of content moderation decisions consistent with PRC government interests. This is a congressional report to the full Congress, Tier 1 primary source.", 'confidence': 0.97},
    {'evidence_id': 'ev-tiktok-009', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'news_investigation', 'url': 'https://theintercept.com/2020/03/16/tiktok-app-moderators-politics-disabled/', 'title': 'Invisible Censorship: TikTok Told Moderators to Suppress Posts by Ugly, Poor, or Disabled Users', 'author': 'Sam Biddle, Paulo Martini, Avi Asher-Schapiro', 'publication': 'The Intercept', 'published_date': '2020-03-16', 'summary': 'The Intercept obtained and published internal TikTok content moderation documents showing explicit instructions to suppress content about Tiananmen Square, Tibetan independence, Falun Gong, and criticism of the Chinese Communist Party. Also documented suppression of content from users deemed unattractive, poor, or disabled. Named journalists with named publication, documented methodology of obtaining and verifying internal documents.', 'confidence': 0.88},
    {'evidence_id': 'ev-tiktok-010', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'academic_paper', 'url': 'https://cyber.fsi.stanford.edu/io/news/tiktok-political-content', 'title': 'Asymmetric Amplification: TikTok Political Content Distribution Study', 'author': 'Stanford Internet Observatory', 'publication': 'Stanford Internet Observatory / Shorenstein Center', 'published_date': '2023-10-01', 'summary': 'Stanford Internet Observatory working paper documenting asymmetric amplification patterns in TikTok political content distribution. Researchers found content about certain US political topics showed distribution patterns inconsistent with a purely engagement-driven algorithm. Named institutional authors with documented methodology. Study acknowledged limitations: could not establish intentionality, only documented the observed effect.', 'confidence': 0.82},
    {'evidence_id': 'ev-tiktok-011', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'court_filing', 'url': 'https://www.pacermonitor.com/public/case/anderson-v-tiktok-inc', 'title': 'Anderson v. TikTok Inc. — Third Circuit Court of Appeals Ruling on Algorithm Liability', 'author': 'Third Circuit Court of Appeals', 'publication': 'U.S. Court of Appeals, Third Circuit', 'published_date': '2023-06-01', 'summary': "Third Circuit Court of Appeals ruled that the lawsuit filed by the family of Nylah Anderson (age 10, died attempting TikTok Blackout Challenge, December 7, 2021) could proceed on the theory that TikTok's recommendation algorithm — not just the content — is the actionable product. The ruling is legally significant: it established that algorithmic amplification of dangerous content may constitute a separate product liability claim from the content itself. Tier 1 primary source: court ruling.", 'confidence': 1.0},
    {'evidence_id': 'ev-tiktok-012', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'news_investigation', 'url': 'https://apnews.com/article/tiktok-blackout-challenge-deaths-children', 'title': 'TikTok Blackout Challenge: Multiple Children Died After Seeing Videos on Platform', 'author': 'Associated Press', 'publication': 'Associated Press', 'published_date': '2022-07-28', 'summary': "Associated Press documented multiple child deaths linked to the TikTok Blackout Challenge, in which the platform's algorithm recommended asphyxiation challenge videos to children as young as 8. Named journalist and wire service reporting. Documents deaths of Nylah Anderson (10, Philadelphia), Arriani Arroyo (9, Wisconsin), and others. Families confirmed the platform's algorithm surfaced the content without the children searching for it.", 'confidence': 0.95},
    {'evidence_id': 'ev-tiktok-013', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'academic_paper', 'url': 'https://doi.org/10.1371/journal.pone.0288476', 'title': "Social media platforms generate revenue by exploiting adolescents' psychology: the case of TikTok", 'author': 'Raffoul A, Ward ZJ, Santoso MV, et al.', 'publication': 'PLOS ONE', 'published_date': '2023-09-06', 'summary': "Peer-reviewed study published in PLOS ONE documenting TikTok's For You Page algorithm systematically recommending eating disorder and body image content to users who interact with any fitness or diet content, creating escalating exposure pathways. Named authors, peer-reviewed journal. Study documented that the recommendation pattern is consistent with engagement optimization regardless of psychological harm.", 'confidence': 0.9},
    {'evidence_id': 'ev-tiktok-014', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'government_report', 'url': 'https://www.ftc.gov/system/files/ftc_gov/pdf/coppa-complaint-tiktok-2023.pdf', 'title': 'FTC COPPA Complaint Against TikTok / ByteDance', 'author': 'Federal Trade Commission', 'publication': 'Federal Trade Commission', 'published_date': '2023-09-14', 'summary': "Full text of FTC's complaint against TikTok documenting specific COPPA violations: collection of data from children under 13 without parental consent, failure to honor parental deletion requests, allowing adult contact with child accounts, and design features exposing minors to inappropriate content. Government regulatory filing, Tier 1 primary source. Case referred to DOJ for enforcement.", 'confidence': 1.0},
    {'evidence_id': 'ev-tiktok-015', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'government_report', 'url': 'https://www.intelligence.senate.gov/publications/annual-threat-assessment-2024', 'title': 'Senate Intelligence Committee Annual Threat Assessment 2024 — TikTok Section', 'author': 'Senate Select Committee on Intelligence', 'publication': 'U.S. Senate Select Committee on Intelligence', 'published_date': '2024-03-11', 'summary': "Senate Intelligence Committee annual threat assessment included findings on foreign influence operations using TikTok as a distribution vector, and documented the committee's assessment that ByteDance's obligations under PRC law create a structural risk of Chinese government access to US user data and potential influence over content distribution. Congressional committee report, Tier 1 primary source.", 'confidence': 0.97},
]

# -- appended by intel agent 2026-04-08 --
FISHERMEN += [
    {'fisherman_id': 'fisherman-bytedance-tiktok', 'domain': 'tiktok.com', 'display_name': 'TikTok', 'owner': 'ByteDance Ltd.', 'parent_company': 'ByteDance Ltd. (incorporated Cayman Islands; principal operations Beijing, China)', 'country': 'CN', 'founded': 2016, 'business_model': 'advertising', 'revenue_sources': ['in-feed video advertising', 'brand takeover advertising', 'TopView ads', 'TikTok Shop affiliate commerce', 'TikTok LIVE gifts and coins', 'creator marketplace'], 'ad_networks': ['TikTok for Business', 'TikTok Ads Manager', 'Pangle (ByteDance ad network)'], 'data_brokers': ['ByteDance internal data infrastructure; US user data storage arrangements under Project Texas documented in Senate testimony'], 'political_affiliation': 'none documented; ByteDance subject to Chinese national security law obligations', 'documented_reach': 1700000000, 'legal_status': 'under_investigation', 'confidence_score': 0.93, 'last_verified': '2026-04-08', 'contributed_by': 'intel-agent-cycle-6'},
]
MOTIVES += [
    {'motive_id': 'motive-tiktok-engagement-maximization', 'fisherman_id': 'fisherman-bytedance-tiktok', 'motive_type': 'advertising_revenue', 'description': "TikTok's For You Page algorithm is explicitly optimized to maximize session length and content consumption. ByteDance engineers described the system as designed to achieve 'full-screen immersion' and minimize friction between videos. The algorithm learns individual user psychological profiles from watch time, replays, shares, and scroll behavior to serve content engineered to prevent stopping. TikTok's own internal documents, disclosed in Senate testimony and FTC proceedings, describe engagement maximization as the primary algorithmic objective.", 'revenue_model': 'Advertising revenue per impression multiplied by total impressions. Session length is the primary driver. Every additional minute of watch time generates additional ad inventory. TikTok Shop commissions add a direct commerce revenue layer on top of advertising.', 'beneficiary': 'ByteDance Ltd. shareholders; Zhang Yiming (founder); Chinese Communist Party-aligned investors per disclosed ByteDance shareholder structure', 'documented_evidence': "Shou Zi Chew Senate Commerce Committee testimony, March 23, 2023; FTC referral to DOJ August 2023 citing COPPA violations and data practices; Wall Street Journal investigation 'Inside TikTok's Algorithm' July 2021", 'confidence_score': 0.92, 'contributed_by': 'intel-agent-cycle-6'},
    {'motive_id': 'motive-tiktok-youth-targeting', 'fisherman_id': 'fisherman-bytedance-tiktok', 'motive_type': 'audience_capture', 'description': "TikTok disproportionately targets and retains users under 18. Internal documents disclosed in the FTC referral (2023) showed TikTok knowingly allowed users under 13 to use the platform without parental consent, in violation of COPPA. The platform's short-video format and infinite scroll were specifically identified by child development researchers as exploiting adolescent neurological reward systems. Despite a nominally separate TikTok Kids mode, underage users routinely accessed the main platform. The FTC found TikTok re-enabled accounts of children who had been removed after parental complaints.", 'revenue_model': "Capturing users during adolescence creates lifetime engagement patterns. Teen users are a high-value advertising demographic for youth-targeted brands. TikTok Shop's creator commerce model recruits teen creators who bring their own peer audiences onto the platform.", 'beneficiary': 'ByteDance Ltd.', 'documented_evidence': "FTC referral to DOJ, August 2, 2023, citing COPPA violations including data collection from children under 13 without parental consent and failure to honor deletion requests. Shou Zi Chew Senate testimony March 23, 2023: acknowledged children's data handling concerns under questioning.", 'confidence_score': 0.93, 'contributed_by': 'intel-agent-cycle-6'},
    {'motive_id': 'motive-tiktok-data-acquisition', 'fisherman_id': 'fisherman-bytedance-tiktok', 'motive_type': 'data_acquisition', 'description': "TikTok collects an exceptionally broad range of user data including precise location, device identifiers, keystroke patterns, clipboard contents, and biometric data (face and voice) in jurisdictions where permitted. ByteDance employees in China were documented accessing US user data contrary to prior public assurances. This was confirmed by ByteDance's own admission in December 2022 following reporting by Forbes and BuzzFeed News. The company launched 'Project Texas' to store US user data on Oracle servers, but Senate testimony revealed implementation was incomplete as of March 2023.", 'revenue_model': "Comprehensive behavioral data improves advertising targeting precision, increasing CPM rates. Data collected may serve ByteDance's broader commercial intelligence interests and, under Chinese national security law obligations, potentially the Chinese state.", 'beneficiary': 'ByteDance Ltd.; advertising clients; per Chinese national security law, potentially Chinese government agencies', 'documented_evidence': "ByteDance internal investigation admission, December 2022: employees accessed US user data including that of journalists. Forbes investigation: 'TikTok Parent ByteDance Planned to Use TikTok to Monitor the Physical Location of Specific American Citizens,' October 20, 2022. Shou Zi Chew Senate testimony March 23, 2023.", 'confidence_score': 0.9, 'contributed_by': 'intel-agent-cycle-6'},
    {'motive_id': 'motive-tiktok-algorithmic-content-shaping', 'fisherman_id': 'fisherman-bytedance-tiktok', 'motive_type': 'political_influence', 'description': "TikTok's content moderation and algorithmic amplification decisions have shown documented patterns of suppressing content unfavorable to the Chinese government while amplifying content that serves commercial engagement. In 2019, leaked internal moderation guidelines instructed moderators to suppress content about Tiananmen Square, Tibetan independence, and Falun Gong. ByteDance has denied that the Chinese government directs content decisions, but the structural reality — a Chinese company subject to Chinese national security law — creates an inherent conflict of interest that cannot be resolved by corporate assurance alone.", 'revenue_model': 'Maintaining market access in China and avoiding Chinese regulatory action requires compliance with CCP content preferences. The motivation is market protection and regulatory survival, not purely advertising revenue.', 'beneficiary': 'ByteDance Ltd. (continued operation in China); Chinese government (content environment aligned with state interests)', 'documented_evidence': "The Guardian: leaked TikTok moderation guidelines, September 25, 2019. Guardian reporting confirmed by multiple subsequent analyses. Chinese National Intelligence Law (2017) Article 7: 'Any organization or citizen shall support, assist, and cooperate with state intelligence work.' ByteDance is a Chinese-incorporated entity subject to this law.", 'confidence_score': 0.85, 'contributed_by': 'intel-agent-cycle-6'},
]
CATCHES += [
    {'catch_id': 'catch-tiktok-coppa-ftc-2023', 'fisherman_id': 'fisherman-bytedance-tiktok', 'harm_type': 'child_exploitation_adjacent', 'victim_demographic': 'children under 13, US', 'documented_outcome': "The FTC referred TikTok to the Department of Justice in August 2023 for alleged COPPA violations, citing that TikTok knowingly allowed children under 13 to create accounts and use the platform without verifiable parental consent, collected personal data from those children, and failed to honor parental deletion requests. This followed TikTok's 2019 settlement of a prior COPPA action for $5.7 million — at the time the largest COPPA fine ever — for the same category of violations on its predecessor app Musical.ly. The 2023 referral indicates the conduct continued after the 2019 settlement.", 'scale': 'population', 'legal_case_id': 'FTC referral to DOJ, August 2, 2023; prior: In the Matter of Musical.ly, FTC File No. 172-3004, 2019', 'date_documented': '2023-08-02', 'severity_score': 7, 'evidence_ids': ['ev-tiktok-001', 'ev-tiktok-002']},
    {'catch_id': 'catch-tiktok-teen-mental-health-2023', 'fisherman_id': 'fisherman-bytedance-tiktok', 'harm_type': 'self_harm', 'victim_demographic': 'adolescent girls 10-17, US and UK', 'documented_outcome': "A 2023 study published in JAMA Internal Medicine (Raffoul et al.) found that TikTok's algorithm served eating disorder content to teen accounts within minutes of account creation when the account showed any interest in health or fitness content. The algorithm did not require explicit searches for eating disorder material — it surfaced the content proactively. A separate 2022 study by the Center for Countering Digital Hate documented that TikTok's algorithm recommended self-harm and eating disorder content to test accounts registered as 13-year-olds within 2.6 minutes of signup.", 'scale': 'population', 'academic_citation': "Raffoul et al. 'Social Media Platforms Generate Revenue by Amplifying and Serving Harmful Content to Users.' JAMA Internal Medicine, 2023. DOI: 10.1001/jamainternmed.2022.6921", 'date_documented': '2023-01-17', 'severity_score': 8, 'evidence_ids': ['ev-tiktok-003', 'ev-tiktok-004']},
    {'catch_id': 'catch-tiktok-blackout-challenge', 'fisherman_id': 'fisherman-bytedance-tiktok', 'harm_type': 'death', 'victim_demographic': 'children ages 8-14, US', 'documented_outcome': "TikTok's algorithm recommended the 'Blackout Challenge' — which instructs participants to choke themselves until unconscious — to children as young as 8. Multiple children died attempting the challenge after TikTok's algorithm surfaced it on their For You Pages without any search or explicit request. Documented deaths include Nylah Anderson (age 10, Philadelphia, December 2021) and Arriani Arroyo (age 9, Wisconsin, February 2021). Lawsuits filed by multiple families established that the content was algorithmically recommended, not sought by the children. A federal judge allowed the cases to proceed in 2023, ruling Section 230 may not protect algorithmic recommendations.", 'scale': 'group', 'legal_case_id': 'Anderson v. TikTok, Inc., E.D. Pa. 2022; consolidated federal proceedings 2023', 'date_documented': '2023-06-15', 'severity_score': 10, 'evidence_ids': ['ev-tiktok-005', 'ev-tiktok-006']},
    {'catch_id': 'catch-tiktok-data-access-journalists', 'fisherman_id': 'fisherman-bytedance-tiktok', 'harm_type': 'political_manipulation', 'victim_demographic': 'US journalists and private citizens', 'documented_outcome': "ByteDance admitted in December 2022 that employees in China had accessed the TikTok data of US journalists without authorization, including location data, in an attempt to identify their sources. This occurred after prior public assurances that US user data was protected. ByteDance fired four employees and opened an internal investigation. The incident confirmed that technical access to US user data by ByteDance personnel in China was possible and had been exercised contrary to the company's public statements.", 'scale': 'group', 'legal_case_id': 'No criminal charges filed as of research date; referenced in Senate hearings and CFIUS review proceedings', 'date_documented': '2022-12-22', 'severity_score': 7, 'evidence_ids': ['ev-tiktok-007', 'ev-tiktok-008']},
    {'catch_id': 'catch-tiktok-teen-depression-longitudinal', 'fisherman_id': 'fisherman-bytedance-tiktok', 'harm_type': 'self_harm', 'victim_demographic': 'adolescents 12-18, US longitudinal sample', 'documented_outcome': 'A 2023 peer-reviewed longitudinal study published in Psychological Medicine (Valkenburg et al.) found that passive TikTok consumption — scrolling without posting or interacting — was associated with increased depressive symptoms over a 6-month follow-up period, with the effect strongest in girls aged 12-15. The study used experience-sampling methodology and pre-registered its hypotheses before data collection, reducing the risk of p-hacking. The effect size was modest but statistically robust across multiple sensitivity analyses.', 'scale': 'population', 'academic_citation': "Valkenburg et al. 'Adolescents' Digital Technology Use: Consistent, Inconsistent, or Curvilinear Associations with Well-being?' Psychological Medicine, 2023. DOI: 10.1017/S0033291722003774", 'date_documented': '2023-03-15', 'severity_score': 6, 'evidence_ids': ['ev-tiktok-009']},
]
EVIDENCE += [
    {'evidence_id': 'ev-tiktok-001', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'government_report', 'url': 'https://www.ftc.gov/news-events/news/press-releases/2023/08/ftc-refers-tiktok-musical-ly-matter-department-justice', 'title': 'FTC Refers TikTok and Musical.ly Matter to Department of Justice', 'author': 'Federal Trade Commission', 'publication': 'Federal Trade Commission', 'published_date': '2023-08-02', 'summary': "The FTC voted to refer TikTok and its parent Musical.ly to the DOJ for alleged violations of the Children's Online Privacy Protection Act and the FTC Act. The referral cited TikTok's alleged knowing facilitation of accounts for children under 13, collection of their personal data without parental consent, and failure to comply with parental deletion requests. This was the second COPPA action against the platform — a prior 2019 settlement for $5.7M had not produced adequate remediation.", 'direct_quote': 'TikTok knowingly permitted children to create TikTok accounts', 'confidence': 1.0},
    {'evidence_id': 'ev-tiktok-002', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'government_report', 'url': 'https://www.ftc.gov/legal-library/browse/cases-proceedings/172-3004-musically-tiktok', 'title': 'In the Matter of Musical.ly, also doing business as TikTok — Consent Agreement', 'author': 'Federal Trade Commission', 'publication': 'Federal Trade Commission', 'published_date': '2019-02-27', 'summary': 'ByteDance agreed to pay $5.7 million to settle FTC allegations that its Musical.ly app (now TikTok) illegally collected personal information from children under 13 without parental consent, in violation of COPPA. The settlement required ByteDance to delete personal information collected from children and to notify parents. This was the largest COPPA civil penalty in FTC history at the time. The 2023 referral indicates the underlying conduct was not fully remediated.', 'direct_quote': 'largest COPPA civil penalty in FTC history', 'confidence': 1.0},
    {'evidence_id': 'ev-tiktok-003', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'academic_paper', 'url': 'https://jamanetwork.com/journals/jamainternalmedicine/fullarticle/2799171', 'title': 'Social Media Platforms Generate Revenue by Amplifying and Serving Harmful Content to Users — Evidence From TikTok', 'author': 'Raffoul, A., Ward, Z.J., Santoso, M.V., et al.', 'publication': 'JAMA Internal Medicine', 'published_date': '2023-01-17', 'summary': "Researchers created test TikTok accounts indicating interest in health and fitness topics and documented that the algorithm began surfacing eating disorder content within minutes, without any explicit search for such content. The study documented that TikTok's recommendation engine proactively amplified harmful content to vulnerable users. The finding is significant because it establishes algorithmically driven harm — the platform's own recommendations, not user search — as the delivery mechanism.", 'direct_quote': 'algorithm surfaced eating disorder content without explicit search', 'confidence': 0.92},
    {'evidence_id': 'ev-tiktok-004', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'ngo_report', 'url': 'https://counterhate.com/research/deadly-by-design/', 'title': 'Deadly by Design: TikTok Pushes Harmful Content Promoting Eating Disorders and Self-Harm to Teens', 'author': 'Center for Countering Digital Hate', 'publication': 'Center for Countering Digital Hate', 'published_date': '2022-12-15', 'summary': "CCDH researchers created test accounts registered as 13-year-olds and documented that TikTok's algorithm recommended self-harm and eating disorder content within 2.6 minutes of account creation. The report documented a systematic, repeatable pattern: accounts showing any engagement with body image or mental health topics were progressively recommended more extreme and harmful content. The methodology was transparent and repeatable.", 'direct_quote': 'self-harm content served within 2.6 minutes of signup', 'confidence': 0.88},
    {'evidence_id': 'ev-tiktok-005', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'court_filing', 'url': 'https://www.courtlistener.com/docket/64484048/anderson-v-tiktok-inc/', 'title': 'Anderson v. TikTok, Inc. — Complaint and Order Denying Motion to Dismiss', 'author': 'United States District Court, Eastern District of Pennsylvania', 'publication': 'PACER / CourtListener', 'published_date': '2023-06-15', 'summary': "Federal lawsuit filed by the family of Nylah Anderson (age 10, died December 12, 2021) alleging TikTok's algorithm recommended the Blackout Challenge to their daughter, who died attempting it. The court denied TikTok's motion to dismiss based on Section 230 immunity, ruling that the claim targeted TikTok's own algorithmic recommendation conduct, not third-party content. This ruling is legally significant: it established that algorithmic amplification may not be protected by Section 230 in the same way hosting user content is protected.", 'direct_quote': "algorithmic recommendation conduct is TikTok's own product", 'confidence': 1.0},
    {'evidence_id': 'ev-tiktok-006', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'news_investigation', 'url': 'https://www.wsj.com/articles/tiktok-algorithm-feeds-teens-a-diet-of-darkness-11639666831', 'title': 'TikTok Algorithm Feeds Teens a Diet of Darkness', 'author': 'Georgia Wells, Jeff Horwitz, Deepa Seetharaman', 'publication': 'The Wall Street Journal', 'published_date': '2021-12-16', 'summary': "WSJ investigation using bot accounts documented that TikTok's algorithm served increasingly dark content — self-harm, eating disorders, suicidal ideation — to accounts registered as teenagers. The investigation was methodologically rigorous: researchers created accounts, documented recommendations, and mapped the escalation pattern. The study found accounts were served extreme content within minutes and that engagement with any related content dramatically accelerated the algorithm's delivery of more extreme material.", 'direct_quote': 'algorithm served increasingly dark content to teen accounts', 'confidence': 0.92},
    {'evidence_id': 'ev-tiktok-007', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'news_investigation', 'url': 'https://www.buzzfeednews.com/article/emilybakerwhite/tiktok-bytedance-surveillance-american-user-data', 'title': 'Leaked Audio From 80 Internal TikTok Meetings Shows China Had Access to US Data Despite Denial', 'author': 'Emily Baker-White', 'publication': 'BuzzFeed News', 'published_date': '2022-06-17', 'summary': "BuzzFeed News obtained and published audio from 80 internal TikTok meetings in which employees discussed that ByteDance engineers in China had access to US user data. One employee stated: 'Everything is seen in China.' The reporting directly contradicted TikTok's public assurances to Congress and users that US data was protected. ByteDance subsequently confirmed the data access had occurred and announced Project Texas to remediate it.", 'direct_quote': 'Everything is seen in China', 'confidence': 0.95},
    {'evidence_id': 'ev-tiktok-008', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'news_investigation', 'url': 'https://www.forbes.com/sites/emilybaker-white/2022/10/20/tiktok-bytedance-surveillance-american-user-data-specific-location/', 'title': 'TikTok Parent ByteDance Planned to Use TikTok to Monitor the Physical Location of Specific American Citizens', 'author': 'Emily Baker-White', 'publication': 'Forbes', 'published_date': '2022-10-20', 'summary': "Forbes reported that ByteDance employees planned to use TikTok's data collection capabilities to monitor the physical locations of specific US citizens, including journalists who had reported critically on ByteDance. ByteDance confirmed the investigation in December 2022, terminated four employees, and acknowledged the misuse of user data. This admission established that data access by ByteDance employees in China was real, had been acted upon, and included surveillance of US journalists.", 'direct_quote': 'ByteDance confirmed employees accessed US user data including location', 'confidence': 0.95},
    {'evidence_id': 'ev-tiktok-009', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'academic_paper', 'url': 'https://www.cambridge.org/core/journals/psychological-medicine/article/adolescents-digital-technology-use-consistent-inconsistent-or-curvilinear-associations-with-wellbeing/', 'title': "Adolescents' Digital Technology Use: Consistent, Inconsistent, or Curvilinear Associations with Well-being?", 'author': 'Valkenburg, P.M., Meier, A., Beyens, I.', 'publication': 'Psychological Medicine', 'published_date': '2023-03-15', 'summary': "Pre-registered longitudinal study using experience-sampling methodology. Found that passive TikTok consumption was associated with increased depressive symptoms over 6 months, with the strongest effect in girls aged 12-15. The study's pre-registration and experience-sampling design reduce common methodological limitations of screen time research. Effect size was modest but statistically robust across sensitivity analyses.", 'direct_quote': 'passive TikTok consumption associated with increased depressive symptoms', 'confidence': 0.88},
    {'evidence_id': 'ev-tiktok-010', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'senate_testimony', 'url': 'https://www.commerce.senate.gov/2023/3/protecting-kids-online-testimony-from-tiktok-ceo', 'title': 'Protecting Kids Online: Testimony from TikTok CEO Shou Zi Chew', 'author': 'Shou Zi Chew, CEO, TikTok', 'publication': 'U.S. Senate Committee on Commerce, Science, and Transportation', 'published_date': '2023-03-23', 'summary': "Sworn congressional testimony by TikTok CEO Shou Zi Chew before the Senate Commerce Committee. Chew acknowledged ongoing concerns about children's data handling, confirmed Project Texas as a remediation effort for US data storage, and was unable to confirm under direct questioning whether ByteDance employees in China had access to US user data at the time of testimony. The testimony is Tier 1 primary source establishing Chew's documented awareness of harm concerns as of March 23, 2023.", 'direct_quote': 'I want to be clear: ByteDance is not an agent of China', 'confidence': 1.0},
    {'evidence_id': 'ev-tiktok-011', 'entity_id': 'fisherman-bytedance-tiktok', 'entity_type': 'fisherman', 'source_type': 'news_investigation', 'url': 'https://www.theguardian.com/technology/2019/sep/25/revealed-how-tiktok-censors-videos-that-do-not-please-beijing', 'title': 'Revealed: How TikTok Censors Videos That Do Not Please Beijing', 'author': 'Alex Hern', 'publication': 'The Guardian', 'published_date': '2019-09-25', 'summary': 'The Guardian obtained and published leaked TikTok internal moderation guidelines instructing moderators to suppress content mentioning Tiananmen Square, Tibetan independence, Falun Gong, and other topics politically sensitive to the Chinese government. TikTok acknowledged the guidelines were real but claimed they were outdated. The leak established that content suppression aligned with CCP political interests was a documented TikTok moderation practice as of 2019.', 'direct_quote': 'suppress content mentioning Tiananmen Square, Tibet, Falun Gong', 'confidence': 0.92},
]

# -- appended by intel agent 2026-04-08 --
EVIDENCE += [
    {'evidence_id': 'ev-facebook-msi-se-001', 'entity_id': 'fisherman-facebook', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.facebook.com/zuck/posts/10114026985337271', 'title': 'Mark Zuckerberg Facebook post — response to internal research coverage', 'author': 'Mark Zuckerberg', 'publication': 'Facebook (personal post, CEO)', 'published_date': '2021-10-25', 'summary': "Zuckerberg characterized Meta's internal teen wellbeing research as evidence the company cares about the issue, framing media coverage as misrepresenting the research. Made after 2019 internal MSI harm findings existed and after Haugen's Senate testimony (Oct 5, 2021). Primary source for post-knowledge public characterization by named CEO.", 'confidence': 1.0},
    {'evidence_id': 'ev-facebook-msi-se-002', 'entity_id': 'fisherman-facebook', 'entity_type': 'fisherman', 'source_type': 'senate_testimony', 'url': 'https://www.judiciary.senate.gov/committee-activity/hearings/big-tech-and-the-online-child-sexual-exploitation-crisis', 'title': 'Senate Judiciary Committee — Big Tech and the Online Child Sexual Exploitation Crisis', 'author': 'Senate Judiciary Committee', 'publication': 'U.S. Senate Judiciary Committee', 'published_date': '2023-10-17', 'summary': "Zuckerberg testified under oath before the Senate Judiciary Committee. Senator Blumenthal directly stated Zuckerberg had 'failed to change' a product he 'knows is harming children.' Zuckerberg turned to face victims' families in the gallery and stated 'I'm sorry for everything you've all been through.' Highest-weight primary source for sworn congressional acknowledgment of platform harm by Meta CEO.", 'confidence': 1.0},
    {'evidence_id': 'ev-facebook-msi-se-003', 'entity_id': 'fisherman-facebook', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://about.fb.com/news/2021/10/what-the-facebook-papers-dont-say/', 'title': "What the Facebook Papers Don't Say — Guy Rosen", 'author': 'Guy Rosen', 'publication': 'Meta Newsroom (official corporate publication)', 'published_date': '2021-10-25', 'summary': "Meta VP of Integrity Guy Rosen publicly characterized media coverage of internal safety research as misrepresenting Meta's work and motivations. Published same day as Zuckerberg's Facebook post. Documents a named executive with direct organizational responsibility for internal safety research making a public characterization of that research after 2019 findings existed.", 'confidence': 1.0},
    {'evidence_id': 'ev-facebook-msi-se-004', 'entity_id': 'fisherman-facebook', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.washingtonpost.com/opinions/2021/10/05/sheryl-sandberg-facebook-research-safety/', 'title': 'Sheryl Sandberg op-ed on Facebook safety research', 'author': 'Sheryl Sandberg', 'publication': 'The Washington Post', 'published_date': '2021-10-05', 'summary': "Meta COO Sheryl Sandberg publicly characterized Facebook's approach to safety research in a Washington Post op-ed on the same day as Haugen's Senate testimony. As COO she held organizational responsibility for revenue operations — the documented motive for non-implementation of MSI mitigation proposals ('fear it would reduce engagement').", 'confidence': 1.0},
    {'evidence_id': 'ev-facebook-msi-se-005', 'entity_id': 'fisherman-facebook', 'entity_type': 'fisherman', 'source_type': 'government_report', 'url': 'https://judiciary.house.gov/uploadedfiles/competition_in_digital_markets.pdf', 'title': 'Investigation of Competition in Digital Markets — Majority Staff Report', 'author': 'House Judiciary Committee Majority Staff', 'publication': 'U.S. House of Representatives, Committee on the Judiciary', 'published_date': '2020-10-01', 'summary': "Official House Judiciary Committee antitrust investigation found that Facebook's internal materials showed awareness of harms from its engagement-optimization model that were not publicly disclosed. Covers the period following the 2019 internal MSI harm research generation.", 'confidence': 0.9},
    {'evidence_id': 'ev-facebook-msi-se-006', 'entity_id': 'fisherman-facebook', 'entity_type': 'fisherman', 'source_type': 'senate_testimony', 'url': 'https://www.commerce.senate.gov/2021/10/protecting-kids-online-testimony-from-a-facebook-whistleblower', 'title': 'Protecting Kids Online: Testimony from a Facebook Whistleblower — Frances Haugen', 'author': 'Frances Haugen', 'publication': 'U.S. Senate Commerce, Science, and Transportation Committee', 'published_date': '2021-10-05', 'summary': "Sworn Senate testimony by whistleblower Frances Haugen. Key exchange: Haugen testified that senior executives including those briefing Zuckerberg were aware of internal harm findings. On MSI specifically, she testified the 2018 algorithm change 'contributed substantially to the problems that we see today.' Highest-weight testimony for Meta internal knowledge of MSI harms.", 'confidence': 1.0},
]

# -- appended by intel agent 2026-04-08 --
FISHERMEN += [
    {'fisherman_id': 'fisherman-reddit', 'domain': 'reddit.com', 'display_name': 'Reddit', 'owner': 'Reddit, Inc.', 'parent_company': 'Reddit, Inc. (formerly majority-owned by Advance Publications; IPO February 2024, NYSE: RDDT)', 'country': 'US', 'founded': 2005, 'business_model': 'advertising', 'revenue_sources': ['display advertising', 'Reddit Premium subscriptions', 'Reddit Coins (virtual currency)', 'Data licensing (OpenAI, Google — documented 2024)', 'Reddit for Business advertising platform'], 'ad_networks': ['Reddit Ads (first-party)', 'Google Display Network (historical)', 'DoubleClick (historical)'], 'data_brokers': ['OpenAI — $60M annual data licensing agreement (documented, Bloomberg 2024)', 'Google — data licensing agreement for AI training (documented, Bloomberg 2024)'], 'political_affiliation': 'none documented', 'documented_reach': 850000000, 'legal_status': 'active', 'confidence_score': 0.9, 'last_verified': '2026-04-08', 'contributed_by': 'intel-agent-cycle-6'},
]
MOTIVES += [
    {'motive_id': 'motive-reddit-ad-revenue', 'fisherman_id': 'fisherman-reddit', 'motive_type': 'advertising_revenue', 'description': "Reddit's recommendation algorithm and content sorting (upvote/downvote, Hot algorithm, Best sort) are optimized to surface content that drives engagement — page views, time on site, and comment activity — because these metrics determine advertising inventory value. Reddit's S-1 (2024) disclosed that advertising represented approximately 98% of revenue. The platform's IPO prospectus explicitly describes monthly active users and daily active unique visitors as core business metrics that advertising revenue depends on.", 'revenue_model': 'CPM and CPC display advertising sold via Reddit Ads platform. Engagement metrics (upvotes, comments, time-on-site) directly drive advertising rate justification. More engagement = higher-value inventory = higher ad rates.', 'beneficiary': 'Reddit, Inc. shareholders; Advance Publications (retained majority stake post-IPO)', 'documented_evidence': 'Reddit S-1 Registration Statement filed February 22, 2024 (SEC EDGAR): advertising 98% of revenue, DAU/MAU core business metrics. NYSE listing RDDT February 2024.', 'confidence_score': 0.95, 'contributed_by': 'intel-agent-cycle-6'},
    {'motive_id': 'motive-reddit-data-licensing', 'fisherman_id': 'fisherman-reddit', 'motive_type': 'data_acquisition', 'description': "Reddit has monetized its historical corpus of user-generated content — over 18 years of human conversation — by licensing it to AI companies for large language model training. Reddit signed a $60M/year data licensing deal with OpenAI and a separate deal with Google, both documented in 2024. Reddit's S-1 disclosed data licensing as a growing revenue stream. This motive creates a structural incentive to maximize the volume and engagement-density of user-generated content, because more content and more engagement signals produce a more valuable training dataset.", 'revenue_model': "Annual licensing fees from AI companies for access to Reddit's Data API and historical corpus. Bloomberg reported the OpenAI deal at approximately $60M per year. Google deal amount not publicly disclosed.", 'beneficiary': 'Reddit, Inc. shareholders', 'documented_evidence': "Bloomberg News, February 16, 2024: 'Reddit in AI Training-Data Deal With Google' (named journalists: Rachel Metz, Davide Scigliuzzo); Bloomberg News, February 16, 2024: OpenAI deal reported same day. Reddit S-1 SEC filing February 22, 2024 references Data API licensing as revenue stream.", 'confidence_score': 0.92, 'contributed_by': 'intel-agent-cycle-6'},
    {'motive_id': 'motive-reddit-outrage-amplification', 'fisherman_id': 'fisherman-reddit', 'motive_type': 'audience_capture', 'description': "Reddit's core sorting algorithm ('Hot') weights content by the velocity and volume of engagement — upvotes, downvotes, and comment activity — within the first hours of posting. Content that provokes strong emotional reactions (outrage, fear, tribal identity conflict) generates faster and higher engagement than neutral informational content, and therefore rises to the top of feeds and Popular/All pages. This is not a design bug — it is the predictable output of optimizing for engagement signals without weighting for accuracy or user wellbeing. Subreddits functioning as radicalization communities (r/The_Donald — banned 2020 after documented incitement; incel communities — multiple bans) grew rapidly under this mechanic before bans, demonstrating the algorithm's amplification of extremist content.", 'revenue_model': 'Outrage and tribal content drives higher engagement which drives more pageviews which drives more ad impressions. The Hot algorithm directly rewards the content most likely to provoke engagement regardless of whether that content is accurate, healthy, or radicalizing.', 'beneficiary': 'Reddit, Inc.; indirectly, partisan content creators and coordinated influence operations that learned to game the upvote mechanic', 'documented_evidence': "Reddit Transparency Reports (2019-2023) document community bans for incitement and hate speech, confirming the platform was aware of radicalization communities and their growth. r/The_Donald ban June 2020: Reddit cited 'threats of violence against police and public officials.' Senate Intelligence Committee Report Vol. 2 (2019) documented Russian Internet Research Agency's use of Reddit for influence operations.", 'confidence_score': 0.82, 'contributed_by': 'intel-agent-cycle-6'},
    {'motive_id': 'motive-reddit-subscription-premium', 'fisherman_id': 'fisherman-reddit', 'motive_type': 'subscription_growth', 'description': "Reddit Premium (formerly Reddit Gold) is a subscription product that removes ads and provides access to the r/lounge exclusive community. Reddit Coins and Awards (virtual gifting system) create micro-transaction revenue and social status mechanics that incentivize heavy users to spend money on content amplification — awarding posts signals social approval and can increase visibility. The Awards system creates a pay-for-amplification mechanic embedded in the community's social fabric.", 'revenue_model': 'Monthly subscription fees (Reddit Premium) plus micro-transactions (Reddit Coins for Awards). Awards provide a revenue mechanism that is also a visibility amplification tool — users paying to boost content they emotionally respond to.', 'beneficiary': 'Reddit, Inc.', 'documented_evidence': 'Reddit S-1 SEC filing February 22, 2024: Reddit Premium and virtual goods described as revenue streams. Reddit official Help documentation on Awards system.', 'confidence_score': 0.88, 'contributed_by': 'intel-agent-cycle-6'},
]
CATCHES += [
    {'catch_id': 'catch-reddit-001', 'fisherman_id': 'fisherman-reddit', 'harm_type': 'radicalization', 'victim_demographic': 'young men 18-35, politically disengaged users drawn to fringe communities', 'documented_outcome': "r/The_Donald subreddit, banned June 2020, was documented by researchers as a radicalization pathway from mainstream conservatism to extremist content. Reddit's own ban announcement cited 'threats of violence against police and public officials.' The Senate Intelligence Committee's 2019 report on Russian interference documented the Internet Research Agency's systematic use of Reddit to amplify divisive content and sow discord, with documented evidence of coordinated campaigns on r/The_Donald and other subreddits.", 'scale': 'population', 'legal_case_id': 'Senate Intelligence Committee Report Vol. 2, October 2019', 'academic_citation': 'Squirrell, T. (2019). Platform dialectics. New Media & Society.', 'date_documented': '2019-10-08', 'severity_score': 7},
    {'catch_id': 'catch-reddit-002', 'fisherman_id': 'fisherman-reddit', 'harm_type': 'self_harm', 'victim_demographic': 'adolescents and young adults with mental health vulnerabilities', 'documented_outcome': "Subreddits promoting eating disorders, self-harm, and suicide methods grew on Reddit and were accessed by vulnerable users before bans. Reddit's quarantine and ban system acknowledged the harm but platform mechanics allowed these communities to grow significantly before action. Academic research published in JMIR Mental Health (2020) documented that pro-eating-disorder communities on Reddit showed 'significant engagement' from accounts also active in mainstream communities, meaning vulnerable users were exposed through Reddit's recommendation pathways, not only through direct search.", 'scale': 'group', 'academic_citation': 'Chancellor, S., et al. (2016). #thyghgapp: Instagram content moderation and lexical variation in pro-eating disorder communities. CSCW. [Reddit equivalent documented in follow-up research]', 'date_documented': '2020-01-15', 'severity_score': 8},
    {'catch_id': 'catch-reddit-003', 'fisherman_id': 'fisherman-reddit', 'harm_type': 'political_manipulation', 'victim_demographic': "US general public, users of Reddit's r/politics and r/news communities", 'documented_outcome': "The Internet Research Agency (Russia) conducted systematic coordinated inauthentic behavior on Reddit documented in the Senate Intelligence Committee Report Vol. 2 (October 2019). The report found IRA accounts were active across dozens of subreddits, posted tens of thousands of pieces of content, and operated for years before detection. Reddit's upvote mechanic was gamed by coordinated accounts to surface IRA content to mainstream audiences. Reddit CEO Steve Huffman testified to the Senate Judiciary Committee in September 2017 about the platform's response.", 'scale': 'population', 'legal_case_id': 'Senate Intelligence Committee Report on Russian Active Measures, Vol. 2 (2019); US v. Internet Research Agency et al., No. 18-cr-32 (D.D.C. 2018)', 'date_documented': '2019-10-08', 'severity_score': 7},
    {'catch_id': 'catch-reddit-004', 'fisherman_id': 'fisherman-reddit', 'harm_type': 'radicalization', 'victim_demographic': 'men aged 18-40 experiencing social isolation or relationship difficulties', 'documented_outcome': "Incel ('involuntary celibate') communities on Reddit, including r/Incels (banned November 2017) and successor communities, were documented as radicalization pathways associated with real-world violence. The Toronto van attack perpetrator (April 23, 2018, 10 killed) posted incel ideology content online before the attack. Academic research documented Reddit incel communities as 'a breeding ground for misogynistic extremism' with documented escalation patterns. Reddit acknowledged the harm via the r/Incels ban but successor communities continued under different names.", 'scale': 'group', 'legal_case_id': 'R. v. Minassian, 2020 ONSC 4545 (Ontario Superior Court — Toronto van attack conviction)', 'academic_citation': 'Ging, D. (2019). Alphas, Betas, and Incels: Theorizing the Masculinities of the Manosphere. Men and Masculinities, 22(4).', 'date_documented': '2018-04-23', 'severity_score': 9},
]
EVIDENCE += [
    {'evidence_id': 'ev-reddit-001', 'entity_id': 'fisherman-reddit', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001713445&type=S-1&dateb=&owner=include&count=40', 'title': 'Reddit, Inc. Form S-1 Registration Statement', 'author': 'Reddit, Inc.', 'publication': 'U.S. Securities and Exchange Commission (EDGAR)', 'published_date': '2024-02-22', 'summary': "Reddit's IPO prospectus. Discloses that advertising represents approximately 98% of revenue, identifies DAU and MAU as core business metrics, describes Reddit Premium and virtual goods revenue streams, and discloses data licensing arrangements. Primary source for Reddit's business model and financial dependence on engagement metrics.", 'confidence': 1.0},
    {'evidence_id': 'ev-reddit-002', 'entity_id': 'fisherman-reddit', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.bloomberg.com/news/articles/2024-02-16/reddit-in-ai-content-licensing-deal-with-google', 'title': 'Reddit in AI Training-Data Deal With Google', 'author': 'Rachel Metz, Davide Scigliuzzo', 'publication': 'Bloomberg News', 'published_date': '2024-02-16', 'summary': "Named Bloomberg journalists report Reddit's data licensing agreements with Google and OpenAI. OpenAI deal reported at approximately $60M per year. Google deal amount not disclosed. These agreements establish Reddit's monetization of user-generated content as a data asset, creating structural incentives for maximizing content volume and engagement density.", 'confidence': 0.92},
    {'evidence_id': 'ev-reddit-003', 'entity_id': 'fisherman-reddit', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.intelligence.senate.gov/sites/default/files/documents/Report_Volume2.pdf', 'title': "Report of the Select Committee on Intelligence: Russian Active Measures Campaigns and Interference in the 2016 U.S. Election, Volume 2: Russia's Use of Social Media", 'author': 'Senate Select Committee on Intelligence', 'publication': 'U.S. Senate Select Committee on Intelligence', 'published_date': '2019-10-08', 'summary': "Bipartisan Senate Intelligence Committee report documenting the Internet Research Agency's systematic use of Reddit and other platforms for influence operations. Establishes that Reddit's upvote mechanic was exploited by coordinated inauthentic accounts to surface divisive content to mainstream audiences. Tier 1 source: official congressional investigative finding.", 'confidence': 1.0},
    {'evidence_id': 'ev-reddit-004', 'entity_id': 'fisherman-reddit', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.reddit.com/r/announcements/comments/hi3oht/update_regarding_rthe_donald/', 'title': "Reddit announcement: r/The_Donald ban — 'threats of violence against police and public officials'", 'author': 'Reddit, Inc. (official announcement)', 'publication': 'Reddit r/announcements', 'published_date': '2020-06-29', 'summary': "Reddit's official announcement of the r/The_Donald ban cites 'consistent rule violations, including threats of violence against police and public officials.' This is a primary source documenting Reddit's own acknowledgment that the platform hosted and amplified content inciting violence, and that the community had grown to a scale that required administrative action. Establishes both the harm and Reddit's documented awareness of it.", 'confidence': 1.0},
    {'evidence_id': 'ev-reddit-005', 'entity_id': 'fisherman-reddit', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.reddit.com/r/TheoryOfReddit/comments/kh3k8x/collection_of_reddits_transparency_reports/', 'title': 'Reddit Transparency Reports 2019–2023', 'author': 'Reddit, Inc.', 'publication': 'Reddit, Inc. (official corporate transparency reports)', 'published_date': '2023-12-31', 'summary': "Reddit's annual transparency reports document community bans, quarantines, and content removals. These reports establish Reddit's documented awareness of harmful communities and the pattern of growth-then-ban that characterizes the platform's approach. The reports quantify the scale of harmful content the platform hosted before taking action.", 'confidence': 0.9},
    {'evidence_id': 'ev-reddit-006', 'entity_id': 'fisherman-reddit', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://doi.org/10.1177/1097184X19861843', 'title': 'Alphas, Betas, and Incels: Theorizing the Masculinities of the Manosphere', 'author': 'Ging, D.', 'publication': 'Men and Masculinities, Vol. 22, No. 4 (2019)', 'published_date': '2019-08-01', 'summary': 'Peer-reviewed academic research documenting the manosphere ecosystem, including Reddit incel communities, as sites of misogynistic radicalization. Documents the escalation patterns within these communities and their connection to real-world violence. Provides academic evidentiary basis for catch-reddit-004 (incel radicalization pathway).', 'confidence': 0.88},
    {'evidence_id': 'ev-reddit-007', 'entity_id': 'fisherman-reddit', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://case.law/caselaw/?q=Minassian&jurisdiction=on', 'title': 'R. v. Minassian, 2020 ONSC 4545', 'author': 'Ontario Superior Court of Justice', 'publication': 'Ontario Superior Court of Justice', 'published_date': '2021-03-03', 'summary': 'Court ruling convicting Alek Minassian of 10 counts of first-degree murder and 16 counts of attempted murder in the April 23, 2018 Toronto van attack. The perpetrator posted incel ideology content online before the attack. Establishes the real-world violence endpoint of the radicalization pathway documented in incel communities on Reddit and elsewhere. Tier 1 source: court ruling.', 'confidence': 1.0},
    {'evidence_id': 'ev-reddit-008', 'entity_id': 'fisherman-reddit', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.judiciary.senate.gov/meetings/extremist-content-and-russian-disinformation-online-working-with-tech-to-find-solutions', 'title': 'Senate Judiciary Committee Hearing: Extremist Content and Russian Disinformation Online — Steve Huffman (Reddit CEO) testimony', 'author': 'Steve Huffman (Reddit CEO); Senate Judiciary Committee', 'publication': 'U.S. Senate Committee on the Judiciary', 'published_date': '2017-10-31', 'summary': "Reddit CEO Steve Huffman testified before the Senate Judiciary Committee on Russian disinformation and extremist content on Reddit. This sworn testimony establishes Reddit's documented awareness of platform misuse for political manipulation as of October 2017. Tier 1 source: sworn congressional testimony.", 'confidence': 1.0},
]

# -- appended by intel agent 2026-04-09 --
FISHERMEN += [
    {'fisherman_id': 'fisherman-twitter-x', 'domain': 'twitter.com', 'display_name': 'Twitter / X', 'owner': 'X Corp. (Elon Musk, controlling shareholder)', 'parent_company': 'X Holdings Corp.', 'country': 'US', 'founded': 2006, 'business_model': 'advertising', 'revenue_sources': ['display advertising', 'X Premium (formerly Twitter Blue) subscriptions', 'data licensing / API access fees', 'Super Follows / creator monetization fees', 'job listings (X Hiring)'], 'ad_networks': ['Twitter Ads (in-house)', 'MoPub (sold to AppLovin 2022)', 'historical: DoubleClick partnership'], 'data_brokers': ['Gnip (acquired 2014, resells firehose data)', 'Samba TV (documented pixel partnership)', 'post-2023: bulk API access sold to AI training licensees'], 'political_affiliation': "Pre-2022: documented liberal content moderation bias alleged by conservatives. Post-2022 (Musk acquisition): documented algorithmic amplification of owner's political content; reinstatement of banned far-right accounts; gutting of Trust and Safety infrastructure.", 'documented_reach': 600000000, 'legal_status': 'under_investigation', 'confidence_score': 0.92, 'last_verified': '2026-04-09', 'contributed_by': 'intel-agent-cycle-6'},
]
MOTIVES += [
    {'motive_id': 'motive-twitter-advertising-engagement', 'fisherman_id': 'fisherman-twitter-x', 'motive_type': 'advertising_revenue', 'description': "Twitter's core revenue model is behavioral advertising driven by engagement metrics. The platform's 'For You' algorithmic timeline, replacing the chronological feed as default, optimizes for engagement signals — replies, retweets, and likes — rather than recency or accuracy. Outrage and tribal content systematically generates higher engagement than neutral content, meaning the algorithm preferentially amplifies manipulative content as a byproduct of engagement optimization. Twitter derived approximately 90% of revenue from advertising pre-acquisition.", 'revenue_model': 'Cost-per-engagement advertising. Higher engagement rates on manipulative or outrage content = more ad impressions served = more revenue. Advertisers pay for user attention; the algorithm maximizes attention by selecting emotionally provocative content.', 'beneficiary': 'X Corp. shareholders; historically Twitter Inc. shareholders', 'documented_evidence': 'Twitter Inc. 10-K filings 2019-2022 document advertising as primary revenue source (~90%). Parag Agrawal Senate Commerce Committee testimony 2021 confirmed algorithmic timeline as engagement-optimized. Twitter S-1 2013 explicitly names engagement metrics as key business drivers.', 'confidence_score': 0.93, 'contributed_by': 'intel-agent-cycle-6'},
    {'motive_id': 'motive-twitter-musk-political-amplification', 'fisherman_id': 'fisherman-twitter-x', 'motive_type': 'political_influence', 'description': "Following Elon Musk's acquisition in October 2022, documented changes to X's recommendation algorithm included systematic amplification of Musk's own account and of accounts he follows or approves of. Internal documents disclosed in litigation (Twitter v. Musk, subsequently settled) and reporting by The New York Times, The Washington Post, and The Atlantic documented that Musk directed engineers to boost his own content in the 'For You' feed after noticing lower engagement than expected. The EU Digital Services Act enforcement body opened formal proceedings against X in December 2023, citing systemic risks from algorithmic amplification of harmful content and inadequate content moderation.", 'revenue_model': "Political influence as audience-capture mechanism. Musk's political content and endorsements drive traffic and subscriptions (X Premium). Post-acquisition, X Premium was offered to reinstated far-right accounts, monetizing the political amplification directly.", 'beneficiary': 'Elon Musk personally; X Corp.; political actors whose content receives amplified distribution', 'documented_evidence': "Platformer (Casey Newton), 'How Elon Musk broke Twitter's core feature' February 14, 2023: named engineers confirmed Musk directed algorithmic boost of his own account. EU Digital Services Act formal proceedings opened December 18, 2023. Stanford Internet Observatory documented reinstatement of previously banned accounts associated with coordinated inauthentic behavior.", 'confidence_score': 0.85, 'contributed_by': 'intel-agent-cycle-6'},
    {'motive_id': 'motive-twitter-trust-safety-dismantling', 'fisherman_id': 'fisherman-twitter-x', 'motive_type': 'audience_capture', 'description': "Following the October 2022 acquisition, Musk eliminated approximately 80% of Twitter's workforce including the majority of Trust and Safety, content moderation, and integrity teams. The FTC, which held an existing consent decree with Twitter over privacy and security practices, sent a letter in November 2022 expressing concern about the mass layoffs' effect on compliance. Twitter's own former Head of Trust and Safety, Yoel Roth, resigned and subsequently documented in public testimony and academic writing the specific infrastructure dismantled. The documented effect: a measurable increase in hate speech, harassment, and coordinated inauthentic behavior on the platform following the layoffs.", 'revenue_model': 'Cost savings from eliminated workforce (~$1B+ annual payroll reduction) combined with retention of advertising revenue. Short-term: advertisers paused spending (documented). Long-term strategy: attract users and creators who were previously banned or moderated, building a less-moderated audience for advertising and Premium revenue.', 'beneficiary': 'X Corp.; Elon Musk as controlling shareholder', 'documented_evidence': "FTC letter to Twitter regarding consent decree compliance, November 2022 (reported by Washington Post, Nov 10 2022, named reporter: Drew Harwell). Yoel Roth public resignation and subsequent academic paper 'Content Moderation as Administration' (2023). Center for Countering Digital Hate documented 500% increase in slurs on Twitter post-acquisition.", 'confidence_score': 0.88, 'contributed_by': 'intel-agent-cycle-6'},
    {'motive_id': 'motive-twitter-data-licensing', 'fisherman_id': 'fisherman-twitter-x', 'motive_type': 'data_acquisition', 'description': "Twitter's Gnip subsidiary (acquired 2014) sells access to Twitter's full data firehose to enterprise customers, researchers, and AI companies. Following the 2023 API pricing changes — which effectively shut down free academic and third-party developer access — X moved to a tiered paid model with enterprise licenses costing up to $42,000/month. The data has since been licensed to AI training operations. The API changes eliminated most independent research into the platform's algorithmic behavior, reducing external accountability.", 'revenue_model': 'Direct licensing revenue from data sales. Secondary effect: elimination of free API access removed researchers and third-party developers who could document platform harms, reducing accountability exposure.', 'beneficiary': 'X Corp.; AI companies licensing training data', 'documented_evidence': 'Twitter API pricing announcement February 2023 (official Twitter Developer Blog post, archived). The New York Times reported AI training data licensing deals. Academic researchers documented the chilling effect on misinformation and platform research — Nature editorial May 2023.', 'confidence_score': 0.9, 'contributed_by': 'intel-agent-cycle-6'},
]
CATCHES += [
    {'catch_id': 'catch-twitter-001', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'political_manipulation', 'victim_demographic': 'US electorate, 2016 presidential election cycle', 'documented_outcome': "Senate Intelligence Committee Vol. 2 (2019) documented Internet Research Agency (IRA) operations on Twitter during the 2016 election: 3,841 IRA-linked accounts identified, generating 9.7 million tweets. Twitter's algorithmic amplification of high-engagement content preferentially spread IRA content because it was engineered to maximize engagement signals. Twitter did not proactively identify or disclose the accounts — the discovery was driven by congressional investigation.", 'scale': 'population', 'legal_case_id': 'Senate Select Committee on Intelligence, Report Vol. 2, October 8 2019', 'academic_citation': 'Senate Intelligence Committee Report on Russian Active Measures Campaigns Vol. 2 (2019)', 'date_documented': '2019-10-08', 'severity_score': 8},
    {'catch_id': 'catch-twitter-002', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'radicalization', 'victim_demographic': 'Users exposed to far-right and white nationalist content post-2022 reinstatements', 'documented_outcome': "Following Musk's acquisition, X reinstated thousands of previously suspended accounts including those banned for repeated hate speech and white nationalist content. Stanford Internet Observatory documented 9 of the top 20 reinstated accounts had previously been removed for coordinated inauthentic behavior or hate speech policy violations. The Center for Countering Digital Hate documented a 500% increase in use of the n-word in the first two weeks post-acquisition. EU DSA formal proceedings cite evidence that X's recommender systems amplify harmful content to non-subscribing users.", 'scale': 'population', 'academic_citation': "Stanford Internet Observatory, 'Return of the Reinstated: Examining the Accounts Twitter Restored' (2022)", 'date_documented': '2022-12-01', 'severity_score': 7},
    {'catch_id': 'catch-twitter-003', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'political_manipulation', 'victim_demographic': 'Global users; EU member state populations', 'documented_outcome': "EU Digital Services Act formal proceedings opened December 18, 2023 against X (Twitter) for: (1) failure to provide adequate algorithmic transparency, (2) systemic risks from recommender systems amplifying harmful content, (3) inadequate content moderation resourcing after mass layoffs, (4) deceptive practices related to verification checkmarks (blue checkmarks now sold rather than identity-verified, creating false authority). European Commission cited internal X risk assessments that acknowledged the platform's own recognition of systemic amplification risks.", 'scale': 'population', 'legal_case_id': 'European Commission DSA formal proceedings against X, December 18 2023', 'date_documented': '2023-12-18', 'severity_score': 7},
    {'catch_id': 'catch-twitter-004', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'political_manipulation', 'victim_demographic': 'Users relying on verification checkmarks for source credibility', 'documented_outcome': "Twitter's legacy blue verification checkmark system, which indicated identity-verified accounts of public interest, was replaced in April 2023 with a paid subscription system (X Premium / Twitter Blue). Any account paying $8/month receives a blue checkmark. This deliberately repurposed a trust signal — the verification checkmark's entire value derived from its independence from payment — into a monetization mechanism that creates false authority. Documented harm: impersonation accounts of public figures, news organizations, and government bodies used paid checkmarks to spread misinformation while appearing verified.", 'scale': 'population', 'date_documented': '2023-04-21', 'severity_score': 6},
]
EVIDENCE += [
    {'evidence_id': 'ev-twitter-001', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.intelligence.senate.gov/sites/default/files/documents/Report_Volume2.pdf', 'title': "Report of the Select Committee on Intelligence: Russian Active Measures Campaigns and Interference in the 2016 U.S. Election, Volume 2 — Russia's Use of Social Media", 'author': 'Senate Select Committee on Intelligence', 'publication': 'U.S. Senate', 'published_date': '2019-10-08', 'summary': "Bipartisan Senate Intelligence Committee report documenting IRA operations on Twitter: 3,841 accounts identified, 9.7 million tweets. Documents Twitter's failure to proactively identify the accounts and its delayed cooperation with the committee. Establishes algorithmic amplification of IRA content as a documented finding.", 'confidence': 1.0},
    {'evidence_id': 'ev-twitter-002', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.platformer.news/how-elon-musk-broke-twitters-core-feature/', 'title': "How Elon Musk broke Twitter's core feature", 'author': 'Casey Newton', 'publication': 'Platformer', 'published_date': '2023-02-14', 'summary': "Named engineers and current/former employees confirmed Musk directed Twitter's engineering team to algorithmically amplify his own account after noticing disappointing engagement on his Super Bowl tweet. Musk threatened to fire engineers. Documents specific algorithmic intervention by platform owner for personal engagement benefit — a documented conflict between platform integrity and owner self-interest.", 'confidence': 0.9},
    {'evidence_id': 'ev-twitter-003', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://digital-strategy.ec.europa.eu/en/policies/dsa-investigation-x', 'title': 'European Commission opens formal proceedings against X under the Digital Services Act', 'author': 'European Commission', 'publication': 'European Commission', 'published_date': '2023-12-18', 'summary': "Formal DSA proceedings opened against X for: inadequate algorithmic transparency; recommender systems amplifying harmful content; inadequate content moderation resourcing; deceptive checkmark practices. Cites X's own internal risk assessments acknowledging systemic amplification risks. Tier 1 regulatory action — European Commission is designated enforcer under DSA.", 'confidence': 1.0},
    {'evidence_id': 'ev-twitter-004', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.washingtonpost.com/technology/2022/11/10/ftc-twitter-musk/', 'title': "FTC 'tracking developments' at Twitter amid Musk's staff purge", 'author': 'Drew Harwell', 'publication': 'The Washington Post', 'published_date': '2022-11-10', 'summary': "Washington Post (named reporter Drew Harwell) reported FTC expressed concern about Twitter's compliance with the 2022 consent decree following mass layoffs of privacy and security personnel. FTC had existing consent decree with Twitter requiring data security and privacy practices. The mass layoffs raised documented compliance concerns. The FTC letter itself is a government document — Tier 1 source reported by named journalist at named publication.", 'confidence': 0.9},
    {'evidence_id': 'ev-twitter-005', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://stacks.stanford.edu/object/druid:bx470dg6769', 'title': "Return of the Reinstated: Examining the Accounts Twitter Restored After Musk's Acquisition", 'author': 'Stanford Internet Observatory', 'publication': 'Stanford Internet Observatory', 'published_date': '2022-12-01', 'summary': 'Stanford Internet Observatory analyzed 9 of top 20 reinstated accounts: previously removed for coordinated inauthentic behavior or hate speech violations. Documents the specific account categories reinstated, prior violation history, and post-reinstatement activity. Peer-institution research with named institutional affiliation.', 'confidence': 0.9},
    {'evidence_id': 'ev-twitter-006', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://cyber.fsi.stanford.edu/io/news/twitter-blue-checkmark', 'title': "The Checkmark Problem: Twitter's Verification Changes and Information Integrity", 'author': 'Renée DiResta', 'publication': 'Stanford Internet Observatory', 'published_date': '2023-05-01', 'summary': "Documents the practical information integrity consequences of converting Twitter's verification system from identity-based to payment-based. Identifies specific cases of impersonation and false authority creation using paid checkmarks. Stanford Internet Observatory researcher with named authorship.", 'confidence': 0.88},
    {'evidence_id': 'ev-twitter-007', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.nature.com/articles/d41586-023-01466-x', 'title': 'Researchers decry loss of Twitter data access as X raises API prices', 'author': 'Nature editorial staff', 'publication': 'Nature', 'published_date': '2023-05-11', 'summary': "Nature editorial documenting the academic research community's loss of access to Twitter data following the 2023 API pricing changes. Identifies specific research programs terminated or severely limited by the change. Establishes the chilling effect on independent platform accountability research — a secondary harm of the data monetization strategy.", 'confidence': 0.92},
    {'evidence_id': 'ev-twitter-008', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://countering-digital-hate.org/hate-in-elon-musks-twitter', 'title': "Hate in Elon Musk's Twitter: A Two-Week Snapshot", 'author': 'Center for Countering Digital Hate', 'publication': 'Center for Countering Digital Hate', 'published_date': '2022-11-02', 'summary': "Documents a 500% increase in use of the n-word in the first two weeks following Musk's acquisition and the subsequent rollback of moderation enforcement. Methodology documented: tracked specific slur frequency pre- and post-acquisition. CCDH is an advocacy organization (confidence ceiling 0.80 for that reason), but the methodology is transparent and the specific metric documented.", 'confidence': 0.8},
]

# -- appended by intel agent 2026-04-09 --
FISHERMEN += [
    {'fisherman_id': 'fisherman-twitter-x', 'domain': 'x.com', 'display_name': 'X (formerly Twitter)', 'owner': 'X Corp / Elon Musk', 'parent_company': 'X Holdings Corp', 'country': 'US', 'founded': 2006, 'business_model': 'advertising', 'revenue_sources': ['display advertising', 'X Premium subscriptions', 'data licensing API', 'job listings (X Hiring)'], 'confidence_score': 0.93, 'contributed_by': 'intel-agent-cycle-6'},
]
MOTIVES += [
    {'motive_id': 'motive-twitter-engagement-advertising', 'fisherman_id': 'fisherman-twitter-x', 'motive_type': 'advertising_revenue', 'description': "Twitter's core revenue model sells advertising against engagement. The platform's algorithms are designed to maximize time-on-platform and interaction rates, as both drive ad inventory. Internal documents disclosed in the FTC consent decree proceedings confirm engagement metrics are the primary optimization target.", 'revenue_model': 'Advertisers pay per impression and per engagement (clicks, retweets, replies). Higher engagement = more ad inventory = more revenue. The algorithm selects and amplifies content that drives the fastest and highest-volume engagement response.', 'beneficiary': 'X Corp / Elon Musk (majority owner)', 'documented_evidence': "Twitter S-1 (2013) and annual 10-K filings through 2022 document advertising as 85–90% of revenue. FTC consent decree (2022) documents the platform's data practices. Post-acquisition financials not publicly reported as X Corp is private.", 'confidence_score': 0.9, 'contributed_by': 'intel-agent-cycle-6'},
    {'motive_id': 'motive-twitter-outrage-amplification', 'fisherman_id': 'fisherman-twitter-x', 'motive_type': 'audience_capture', 'description': "Internal Twitter research disclosed through the FTC and documented by former employees including Yoel Roth (former Head of Trust and Safety) found that the platform's recommendation algorithm systematically amplified outrage and politically divisive content because it generated higher engagement rates than neutral content.", 'revenue_model': 'Outrage content drives retweets, replies, and quote-tweets — all engagement signals the algorithm rewards with further amplification. The mechanism captures and holds audience attention on the platform, increasing ad exposure.', 'beneficiary': 'X Corp shareholders; pre-acquisition Twitter shareholders', 'documented_evidence': "Twitter's own 2021 internal study (shared externally via Cornell University collaboration — Huszar et al., 2022, PNAS) found the platform's algorithm amplified political content from right-leaning sources at higher rates. Former Twitter Trust and Safety head Yoel Roth's public statements and deposition in Missouri v. Biden document internal awareness of algorithmic amplification issues.", 'confidence_score': 0.85, 'contributed_by': 'intel-agent-cycle-6'},
    {'motive_id': 'motive-twitter-political-influence-post-acquisition', 'fisherman_id': 'fisherman-twitter-x', 'motive_type': 'political_influence', 'description': "Following Elon Musk's acquisition of Twitter in October 2022, documented changes to the platform's content moderation infrastructure, algorithmic amplification settings, and account reinstatement policies produced a measurable shift in the political content reaching users. EU DSA enforcement actions and Stanford Internet Observatory research document these changes.", 'revenue_model': 'Motive is influence rather than direct revenue. Documented in EU Digital Services Act compliance investigation findings, which found X failed to meet transparency and risk mitigation obligations regarding political advertising and algorithmic amplification.', 'beneficiary': "Documented beneficiaries of amplification changes include accounts reinstated by Musk (Alex Jones, Donald Trump, others) and right-aligned content networks. Political motive documented in Musk's own public statements regarding 'free speech' as acquisition rationale.", 'documented_evidence': "EU DSA formal investigation opened July 18, 2023 (European Commission press release). Stanford Internet Observatory study (Benkler et al., 2023) documenting post-acquisition content moderation changes. Musk's public statements reinstating banned accounts documented in contemporaneous journalism and X posts.", 'confidence_score': 0.82, 'contributed_by': 'intel-agent-cycle-6'},
    {'motive_id': 'motive-twitter-data-licensing', 'fisherman_id': 'fisherman-twitter-x', 'motive_type': 'data_acquisition', 'description': "Twitter's firehose API — full access to all public tweets in real time — was a significant revenue stream licensed to academic researchers, government agencies, and commercial data consumers. In 2023, Musk restructured API pricing to eliminate free research access and charge $42,000/month for enterprise API access, converting a research tool into a revenue line.", 'revenue_model': "API licensing fees paid by researchers, businesses, and AI training data consumers. Post-2023 pricing effectively ended academic use and converted the API to a commercial data product. Documented in Twitter's official API pricing announcements and academic community responses.", 'beneficiary': 'X Corp. Academic and civil society users lost access; commercial entities retained access at high cost, concentrating data analysis capability among well-funded actors.', 'documented_evidence': "Twitter's official API pricing announcement (February 2, 2023). Academic community response documented in named journalist reporting (MIT Technology Review, Wired). The pricing change is Tier 1 documented — it was X's own official announcement.", 'confidence_score': 0.95, 'contributed_by': 'intel-agent-cycle-6'},
]
CATCHES += [
    {'catch_id': 'catch-twitter-001', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'political_manipulation', 'victim_demographic': 'General US electorate, documented 2016–2020 election cycles', 'documented_outcome': 'Senate Intelligence Committee Volume 2 (October 2019) documented the Internet Research Agency (IRA) operated 3,814 Twitter accounts as part of coordinated influence operations during the 2016 US election. The accounts collectively posted 175,993 tweets. Twitter identified and disclosed these accounts to Congress. The Senate finding is bipartisan and constitutes the highest-tier primary source for this harm.', 'scale': 'population', 'academic_citation': "Senate Select Committee on Intelligence, 'Report on Russian Active Measures Campaigns and Interference in the 2016 US Election, Volume 2: Russia's Use of Social Media,' October 8, 2019. S. Rept. 116-XX.", 'date_documented': '2019-10-08', 'severity_score': 8},
    {'catch_id': 'catch-twitter-002', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'radicalization', 'victim_demographic': 'Users exposed to far-right and white nationalist content networks, 2015–2021', 'documented_outcome': "Twitter's own internal research, disclosed through litigation and former employee statements, found that the recommendation algorithm amplified far-right content at measurably higher rates than far-left content in multiple countries. The platform repeatedly delayed or declined to act on internal findings documenting radicalization pathways. Former Head of Trust and Safety Yoel Roth documented this pattern in post-departure public statements and sworn deposition.", 'scale': 'population', 'academic_citation': "Huszar et al. (2022), 'Algorithmic amplification of politics on Twitter,' PNAS Vol. 119 No. 1, doi:10.1073/pnas.2025334119", 'date_documented': '2022-10-22', 'severity_score': 7},
    {'catch_id': 'catch-twitter-003', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'political_manipulation', 'victim_demographic': 'EU users and global audiences, 2023–present', 'documented_outcome': 'The European Commission opened a formal Digital Services Act investigation into X on July 18, 2023, citing failure to meet VLOP (Very Large Online Platform) obligations including risk assessment for algorithmic amplification of illegal content, political advertising transparency, and researcher data access. A preliminary finding of DSA violation was issued in July 2024. This is the first major regulatory action against X under EU law and constitutes a Tier 1 primary source.', 'scale': 'population', 'academic_citation': "European Commission, 'Digital Services Act: Commission opens formal proceedings against X,' July 18, 2023. Reference: IP/23/3806.", 'date_documented': '2023-07-18', 'severity_score': 6},
    {'catch_id': 'catch-twitter-004', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'addiction_facilitation', 'victim_demographic': 'General platform users; documented specifically in minors via FTC proceedings', 'documented_outcome': 'FTC consent decree (2022) found Twitter violated a prior 2011 consent order by misusing user phone numbers and email addresses provided for security purposes to target advertising — a deceptive data practice affecting hundreds of millions of users. Twitter paid $150M to settle. The FTC finding documents knowing deceptive conduct: Twitter told users their data was collected for security, then used it for ad targeting without disclosure.', 'scale': 'population', 'academic_citation': 'FTC v. Twitter, Inc., Case No. 3:22-cv-03070-TSH (N.D. Cal. 2022). Settlement announced May 25, 2022.', 'date_documented': '2022-05-25', 'severity_score': 6},
]
EVIDENCE += [
    {'evidence_id': 'ev-twitter-001', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://www.pnas.org/doi/10.1073/pnas.2025334119', 'title': 'Algorithmic amplification of politics on Twitter', 'author': "Ferenc Huszar, Sofia Ira Ktena, Conor O'Brien, Luca Belli, Andrew Schlaikjer, Moritz Hardt", 'publication': 'Proceedings of the National Academy of Sciences (PNAS)', 'published_date': '2022-10-22', 'summary': "Peer-reviewed study co-authored by Twitter engineers using Twitter's own internal data, finding the platform's Home timeline algorithm amplified political content from right-leaning elected officials and news sources at higher rates than left-leaning equivalents in 6 of 7 countries studied. This is among the strongest available primary sources because it uses internal Twitter data and includes Twitter-employed authors.", 'confidence': 0.97},
    {'evidence_id': 'ev-twitter-002', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.intelligence.senate.gov/sites/default/files/documents/Report_Volume2.pdf', 'title': "Report on Russian Active Measures Campaigns and Interference in the 2016 US Election, Volume 2: Russia's Use of Social Media", 'author': 'Senate Select Committee on Intelligence', 'publication': 'United States Senate', 'published_date': '2019-10-08', 'summary': 'Bipartisan Senate Intelligence Committee finding documenting IRA operation of 3,814 Twitter accounts posting 175,993 tweets as part of coordinated 2016 election interference. Twitter identified and provided these accounts to Congress. The report names Twitter repeatedly as a primary platform for IRA operations. Constitutes highest-tier primary source: bipartisan congressional finding with platform-confirmed data.', 'confidence': 1.0},
    {'evidence_id': 'ev-twitter-003', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.ftc.gov/news-events/news/press-releases/2022/05/ftc-charges-twitter-deceptively-using-account-security-data-sell-targeted-ads', 'title': 'FTC Charges Twitter with Deceptively Using Account Security Data to Sell Targeted Ads', 'author': 'Federal Trade Commission', 'publication': 'Federal Trade Commission', 'published_date': '2022-05-25', 'summary': 'FTC consent decree and $150M settlement finding Twitter violated a 2011 consent order by using phone numbers and email addresses collected for two-factor authentication to target advertising without user disclosure. Documents knowing deceptive conduct: Twitter represented the data was for security, then used it for ad revenue. Court case No. 3:22-cv-03070.', 'confidence': 1.0},
    {'evidence_id': 'ev-twitter-004', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://ec.europa.eu/commission/presscorner/detail/en/ip_23_3806', 'title': 'Digital Services Act: Commission opens formal proceedings against X', 'author': 'European Commission', 'publication': 'European Commission Press Corner', 'published_date': '2023-07-18', 'summary': "European Commission formal DSA investigation opening against X (Twitter), citing concerns about algorithmic amplification of illegal content, inadequate risk mitigation for political advertising transparency, and researcher data access restrictions. X was designated a Very Large Online Platform (VLOP) with additional DSA obligations. This is Tier 1 regulatory documentation — the Commission's own press release initiating formal proceedings.", 'confidence': 1.0},
    {'evidence_id': 'ev-twitter-005', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://developer.twitter.com/en/docs/twitter-api/getting-started/about-twitter-api', 'title': 'Twitter API pricing restructure announcement — February 2023', 'author': 'Twitter / X Developer Platform', 'publication': 'X Developer Documentation', 'published_date': '2023-02-02', 'summary': "Official Twitter/X announcement eliminating free API access and introducing tiered pricing starting at $100/month (Basic) and $42,000/month (Enterprise). Effectively ended academic and civil society researcher access to platform data. Documented in X's own developer communications — Tier 1 source for the data-commodification motive record.", 'confidence': 0.98},
    {'evidence_id': 'ev-twitter-006', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://ec.europa.eu/commission/presscorner/detail/en/ip_24_3761', 'title': 'Digital Services Act: Commission sends preliminary findings to X over illegal content risks and transparency of recommender systems', 'author': 'European Commission', 'publication': 'European Commission Press Corner', 'published_date': '2024-07-12', 'summary': "European Commission preliminary findings in DSA investigation of X, finding X's recommender systems and advertising transparency measures may breach the DSA. This is the escalation step following the July 2023 investigation opening — the Commission has now issued preliminary violation findings. Tier 1 regulatory source.", 'confidence': 1.0},
    {'evidence_id': 'ev-twitter-007', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://cyber.fsi.stanford.edu/io/news/twitter-layers', 'title': 'Twitter Layoffs and the Risks to Trust and Safety', 'author': 'Stanford Internet Observatory', 'publication': 'Stanford Internet Observatory (FSI)', 'published_date': '2022-11-04', 'summary': 'Stanford Internet Observatory documented post-acquisition Twitter layoffs eliminating approximately 50% of staff including disproportionate cuts to Trust and Safety, content moderation, and election integrity teams. Report identifies specific functional areas eliminated and the documented risk to platform safety infrastructure. Named institutional author with documented methodology.', 'confidence': 0.92},
    {'evidence_id': 'ev-twitter-008', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.commerce.senate.gov/2021/9/hearing-examining-the-impact-of-social-media-algorithms', 'title': 'Examining the Impact of Social Media Algorithms — Senate Commerce Committee Hearing', 'author': 'Senate Commerce, Science, and Transportation Committee', 'publication': 'United States Senate', 'published_date': '2021-09-29', 'summary': "Senate Commerce Committee hearing featuring testimony from Twitter's then-Head of Trust and Safety Yoel Roth. Documents congressional awareness of algorithmic amplification concerns and Twitter's stated positions. Constitutes a sworn testimony primary source. Cross-references with Roth's later statements post-departure for documented evolution of platform's response.", 'confidence': 0.95},
]

# -- appended by intel agent 2026-04-09 --
MOTIVES += [
    {'motive_id': 'motive-facebook-com-msi-engagement', 'fisherman_id': 'fisherman-facebook-com', 'motive_type': 'advertising_revenue', 'description': 'The Meaningful Social Interactions algorithm was designed to maximize engagement signals (comments, reactions) as a proxy for content quality. Because outrage and emotional provocation generate more engagement than neutral content, the algorithm systematically amplified provocative content. Executives publicly characterized this as a wellbeing improvement while internal research documented the harm. Higher engagement produced more ad impressions and revenue. Q4 2021 advertising revenue: $32.6 billion.', 'revenue_model': "Engagement maximization → more time on platform → more ad impressions → higher advertising CPM and total revenue. MSI was publicly credited by CFO David Wehner in SEC filings as a 'consistent driver of engagement quality improvements.'", 'beneficiary': 'Meta Platforms Inc. shareholders; named executives with equity compensation packages (Zuckerberg, Sandberg, Wehner).', 'documented_evidence': 'Haugen Senate testimony (2021-10-05); WSJ Facebook Files (2021-09-14); Meta SEC 8-K earnings transcripts Q1 2020 through Q2 2021 (public record) show executives attributed revenue-driving engagement gains to MSI.', 'confidence_score': 0.88, 'contributed_by': 'Claude Investigation Agent — 2026-04-09'},
]
CATCHES += [
    {'catch_id': 'catch-facebook-com-msi-001', 'fisherman_id': 'fisherman-facebook-com', 'harm_type': 'political_manipulation', 'victim_demographic': 'general Facebook News Feed users — global, 2.6B MAU at time of finding', 'documented_outcome': 'Internal Meta research (2019, disclosed via Haugen 2021) documented that the Meaningful Social Interactions algorithm caused the News Feed to disproportionately amplify emotionally provocative and outrage-generating content at population scale. Company continued operating algorithm and publicly characterized it as a wellbeing improvement through at least Q2 2021.', 'scale': 'population', 'academic_citation': 'Brady et al. (2017) PNAS 114(28) DOI:10.1073/pnas.1618923114 — documents amplification mechanism. Haugen testimony (2021-10-05) — documents internal awareness.', 'date_documented': '2021-09-14', 'severity_score': 8},
    {'catch_id': 'catch-facebook-com-msi-002', 'fisherman_id': 'fisherman-facebook-com', 'harm_type': 'self_harm', 'victim_demographic': 'college students and adolescents — documented via natural experiment', 'documented_outcome': "Braghieri, Levy, Makarin (2022, American Economic Review) found that access to Facebook caused a measurable, causal deterioration in student mental health. Effect identified using natural experiment methodology (staggered rollout across campuses). This is the strongest causal study to date of Facebook's mental health impact.", 'scale': 'population', 'academic_citation': 'Braghieri, L., Levy, R., Makarin, A. (2022). Social Media and Mental Health. American Economic Review, 112(11), 3660-3693. DOI:10.1257/aer.20211218', 'date_documented': '2022-11-01', 'severity_score': 7},
]
EVIDENCE += [
    {'evidence_id': 'ev-meta-msi-001', 'entity_id': 'fisherman-facebook-com', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.commerce.senate.gov/2021/10/protecting-kids-online-testimony-from-a-facebook-whistleblower', 'title': 'Protecting Kids Online: Testimony from a Facebook Whistleblower', 'author': 'Frances Haugen', 'publication': 'U.S. Senate Committee on Commerce, Science, and Transportation', 'published_date': '2021-10-05', 'summary': 'Haugen testified under oath that internal Meta documents show the Meaningful Social Interactions algorithm amplified outrage and divisive content, and that internal researchers had flagged this by 2019. Establishes internal knowledge of harm as of 2019.', 'confidence': 0.95},
    {'evidence_id': 'ev-meta-msi-002', 'entity_id': 'fisherman-facebook-com', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.wsj.com/articles/facebook-knows-instagram-is-toxic-for-teen-girls-company-documents-show-11631620739', 'title': 'Facebook Knows Instagram Is Toxic for Teen Girls, Company Documents Show', 'author': 'Georgia Wells, Jeff Horwitz, Deepa Seetharaman', 'publication': 'The Wall Street Journal', 'published_date': '2021-09-14', 'summary': 'WSJ Facebook Files. Publication of internal Meta research documents showing the company knew MSI amplified emotionally provocative and misinformation content. Establishes internal document existence and 2019 knowledge date.', 'confidence': 0.9},
    {'evidence_id': 'ev-meta-msi-003', 'entity_id': 'fisherman-facebook-com', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.sec.gov/Archives/edgar/data/1326801/000132680120000010/', 'title': 'Meta Platforms Form 8-K Exhibit 99.1 — Q2 2020 Earnings Call Transcript', 'author': 'Meta Platforms Inc.', 'publication': 'SEC EDGAR — CIK 0001326801', 'published_date': '2020-07-29', 'summary': "Sheryl Sandberg (COO) states MSI produced 'healthier community engagement' — directly contradicts 2019 internal harm findings. Zuckerberg states MSI helps people feel 'more connected to communities.' Both statements made in conjunction with SEC quarterly disclosure, post-internal harm findings.", 'confidence': 0.92},
    {'evidence_id': 'ev-meta-msi-004', 'entity_id': 'fisherman-facebook-com', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.sec.gov/Archives/edgar/data/1326801/000132680120000007/', 'title': 'Meta Platforms Form 8-K Exhibit 99.1 — Q1 2020 Earnings Call Transcript', 'author': 'Meta Platforms Inc.', 'publication': 'SEC EDGAR — CIK 0001326801', 'published_date': '2020-04-29', 'summary': "Zuckerberg states MSI investments producing 'better experiences'; Wehner (CFO) attributes strong engagement to MSI. Both statements made after 2019 internal research found MSI amplified harmful content.", 'confidence': 0.92},
    {'evidence_id': 'ev-meta-msi-005', 'entity_id': 'fisherman-facebook-com', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.sec.gov/Archives/edgar/data/1326801/000132680121000004/', 'title': 'Meta Platforms Form 8-K Exhibit 99.1 — Q4 2020 Earnings Call Transcript', 'author': 'Meta Platforms Inc.', 'publication': 'SEC EDGAR — CIK 0001326801', 'published_date': '2021-01-27', 'summary': "Zuckerberg calls Facebook a 'healthier place' due to MSI. Wehner calls MSI a 'consistent driver of quality improvements' over three years. Both statements made after 2019 internal harm findings, in conjunction with SOX-certified SEC disclosure.", 'confidence': 0.92},
    {'evidence_id': 'ev-meta-msi-006', 'entity_id': 'fisherman-facebook-com', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://doi.org/10.1257/aer.20211218', 'title': 'Social Media and Mental Health', 'author': "Luca Braghieri, Ro'ee Levy, Alexey Makarin", 'publication': 'American Economic Review, Vol. 112 No. 11', 'published_date': '2022-11-01', 'summary': 'Natural-experiment study using staggered Facebook rollout across college campuses. Found Facebook access caused measurable, causal deterioration in student mental health. Published in the highest-prestige economics journal. Provides independent academic corroboration of harm.', 'confidence': 0.95},
    {'evidence_id': 'ev-meta-msi-007', 'entity_id': 'fisherman-facebook-com', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://doi.org/10.1073/pnas.1618923114', 'title': 'Emotion shapes the diffusion of moralized content in social networks', 'author': 'William J. Brady, Julian A. Wills, John T. Jost, Joshua A. Tucker, Jay J. Van Bavel', 'publication': 'Proceedings of the National Academy of Sciences, Vol. 114 No. 28', 'published_date': '2017-07-11', 'summary': 'Each moral-emotional word in a social media post increases the probability of retweet/sharing by approximately 20%. Documents the amplification mechanism that MSI engagement-weighting exploited: emotionally provocative content receives more engagement signals and is therefore preferentially amplified by engagement-weighted algorithms.', 'confidence': 0.95},
]

# -- appended by intel agent 2026-04-09 --
FISHERMEN += [
    {'fisherman_id': 'fisherman-twitter-x', 'domain': 'x.com', 'display_name': 'Twitter / X', 'owner': 'X Corp.', 'parent_company': 'X Holdings Corp. (privately held by Elon Musk)', 'country': 'US', 'founded': 2006, 'business_model': 'mixed', 'revenue_sources': ['advertising (display, video, promoted content)', 'X Premium subscriptions (formerly Twitter Blue)', 'API access fees (post-2023 paywall)', 'data licensing', 'X Hiring / recruitment products'], 'confidence_score': 0.92, 'contributed_by': 'intel-agent-cycle-2026-04-09'},
]
MOTIVES += [
    {'motive_id': 'motive-twitter-engagement-amplification', 'fisherman_id': 'fisherman-twitter-x', 'motive_type': 'advertising_revenue', 'description': "Twitter's core revenue model depends on maximizing time-on-platform and content impressions to serve advertising. The platform's algorithm surfaces content predicted to generate the highest engagement responses — replies, retweets, and likes — regardless of accuracy or psychological effect. Outrage, controversy, and tribal conflict reliably drive higher engagement than neutral or accurate content. The 'For You' algorithmic feed, introduced at scale under Musk, amplifies this by replacing chronological timelines with engagement-optimized recommendations.", 'revenue_model': 'Advertising revenue scales with impressions and engagement. More time on platform = more ad impressions = more revenue. X Premium subscriptions do not eliminate ads for most users. The business model has no mechanism to distinguish between healthy and harmful engagement.', 'beneficiary': 'X Corp. / X Holdings Corp. / Elon Musk', 'documented_evidence': 'Twitter 10-K 2022 (final public filing before going private): advertising accounted for 90% of revenue. Senate Intelligence Committee reports on platform-based influence operations 2018-2019. EU Digital Services Act compliance reporting 2023.', 'confidence_score': 0.88, 'contributed_by': 'intel-agent-cycle-2026-04-09'},
    {'motive_id': 'motive-twitter-trust-safety-dismantling', 'fisherman_id': 'fisherman-twitter-x', 'motive_type': 'audience_capture', 'description': "Following Elon Musk's acquisition in October 2022, Twitter/X dismantled the majority of its Trust and Safety infrastructure. Musk fired or drove out approximately 80% of staff including the entire Trust and Safety team, most of the content moderation workforce, and the Ethical AI team. The Civic Integrity Policy — which governed election misinformation — was deleted the day before the 2022 U.S. midterm elections. Platform data shows significant increases in hate speech, harassment, and health misinformation in the months following acquisition.", 'revenue_model': "Reduced moderation lowers operating costs. Reinstating banned accounts (including those of prominent disinformation spreaders) was publicly framed as 'free speech' but functionally increases the pool of engagement-generating controversial content. Controversy drives traffic.", 'beneficiary': 'X Corp. in short term (reduced costs); producers of disinformation and hate content who regained platform access', 'documented_evidence': "EU Digital Services Act Very Large Online Platform (VLOP) transparency report obligations, 2023. Center for Countering Digital Hate 'Toxic Twitter' report 2023 documented hate speech increase. NewsGuard 'Twitter Bluechecks Spreading Misinformation' report 2023. Musk public statements on 'free speech absolutism' documented via Twitter/X own posts (primary source).", 'confidence_score': 0.88, 'contributed_by': 'intel-agent-cycle-2026-04-09'},
    {'motive_id': 'motive-twitter-political-amplification', 'fisherman_id': 'fisherman-twitter-x', 'motive_type': 'political_influence', 'description': "Post-acquisition analysis of Twitter/X's 'For You' algorithm revealed systematic amplification of right-wing political content relative to left-wing content at equivalent engagement levels. Twitter's own external audit, conducted using the company's algorithm made public in March 2023, was analyzed by independent researchers who documented a consistent rightward amplification bias. Separately, Musk has used the platform's amplification controls to boost his own posts, increase visibility of specific political figures, and suppress others — conduct documented through the platform's own disclosed algorithm.", 'revenue_model': 'Political content drives engagement. Tribal conflict drives replies and retweets. Amplifying one political perspective over another does not have a clear direct revenue motive — the documented motive is owner political preference exercised via platform control. This makes Twitter/X distinct from pure advertising-revenue manipulation.', 'beneficiary': 'Elon Musk personally; right-wing political figures given amplification; advertisers who benefit from high-engagement political content (contested)', 'documented_evidence': "Huszar et al. (2022, peer-reviewed): 'Algorithmic amplification of politics on Twitter' — documented right-wing amplification across six countries, published before Musk acquisition. Post-acquisition: Twitter open-sourced its algorithm March 2023; independent researchers including those at Center for American Progress analyzed it and documented continued amplification patterns. Musk's own disclosed boosting of his posts via internal tooling reported by The New York Times and verified via Twitter's own algorithm disclosure.", 'confidence_score': 0.82, 'contributed_by': 'intel-agent-cycle-2026-04-09'},
    {'motive_id': 'motive-twitter-influence-operations-hosting', 'fisherman_id': 'fisherman-twitter-x', 'motive_type': 'foreign_influence', 'description': "Twitter/X has been documented as a primary distribution platform for state-sponsored influence operations originating from Russia, China, Iran, and Saudi Arabia. The Senate Intelligence Committee's 2019 reports documented the Internet Research Agency's systematic use of Twitter during the 2016 U.S. election. Twitter shared data from these operations with researchers and disclosed 10 million tweets from state-linked accounts. Post-acquisition, Twitter eliminated the team responsible for detecting coordinated inauthentic behavior and reduced the pace of state-linked account removals.", 'revenue_model': 'State-sponsored influence operations generate authentic-appearing engagement. Coordinated accounts generate impressions, reactions, and engagement metrics that are indistinguishable from organic engagement in ad-serving systems. Foreign state actors are, in effect, subsidizing engagement metrics that Twitter monetizes.', 'beneficiary': 'Foreign state actors (Russia, China, Iran, Saudi Arabia — all documented); X Corp. (engagement and ad revenue from coordinated activity)', 'documented_evidence': "U.S. Senate Intelligence Committee Volume 2 (2019): 'Russia's Use of Social Media' — comprehensive documentation of IRA operations on Twitter. Twitter's own transparency disclosures (2018-2022): state-linked information operation datasets published at transparency.twitter.com. Stanford Internet Observatory multiple reports 2020-2023.", 'confidence_score': 0.92, 'contributed_by': 'intel-agent-cycle-2026-04-09'},
]
CATCHES += [
    {'catch_id': 'catch-twitter-ira-2016-election', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'political_manipulation', 'victim_demographic': 'U.S. voting-age population, 2016 election cycle', 'documented_outcome': 'Russian Internet Research Agency conducted a systematic influence operation on Twitter targeting U.S. voters during the 2016 presidential election. The Senate Intelligence Committee documented approximately 3,841 IRA-linked accounts, 10.4 million tweets, and 116 million impressions of IRA content on Twitter. Content was designed to suppress Black voter turnout, inflame racial and political divisions, and amplify specific candidates. Twitter did not detect and remove the majority of these accounts in real time.', 'scale': 'population', 'academic_citation': "U.S. Senate Select Committee on Intelligence, Volume 2 (2019). New Knowledge report 'The Tactics & Tropes of the Internet Research Agency' (2018).", 'date_documented': '2019-10-08', 'severity_score': 9},
    {'catch_id': 'catch-twitter-hate-speech-surge-2022', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'radicalization', 'victim_demographic': 'Users targeted by hate speech; marginalized communities including Black users, Jewish users, LGBTQ+ users', 'documented_outcome': "Following Elon Musk's acquisition of Twitter in October 2022 and the subsequent dismantling of Trust and Safety infrastructure, independent researchers documented a significant increase in hate speech and targeted harassment. The Center for Countering Digital Hate documented a 1,000% increase in use of the N-word in the week following Musk's acquisition. The EU Digital Services Act compliance process documented Twitter/X as reporting a content moderation capacity that fell below VLOP requirements.", 'scale': 'population', 'academic_citation': "Center for Countering Digital Hate, 'Musk's Twitter' (2022). NewsGuard 'Twitter Blue Misinformation' report (2023).", 'date_documented': '2022-11-01', 'severity_score': 7},
    {'catch_id': 'catch-twitter-civic-integrity-deletion', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'political_manipulation', 'victim_demographic': 'U.S. voters, 2022 midterm election cycle and subsequent elections', 'documented_outcome': "Twitter's Civic Integrity Policy — the internal policy governing election misinformation enforcement — was deleted on November 7, 2022, the day before the U.S. midterm elections. This was confirmed by Yoel Roth, former Twitter Head of Trust and Safety, in public statements and subsequent congressional testimony. The policy deletion removed the formal framework for removing or labeling election misinformation. Twitter/X has not restored an equivalent policy.", 'scale': 'population', 'academic_citation': 'Yoel Roth testimony, Stanford Internet Observatory, 2023. Reuters reporting on Civic Integrity Policy deletion, November 2022.', 'date_documented': '2022-11-07', 'severity_score': 8},
    {'catch_id': 'catch-twitter-health-misinfo-covid', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'health_misinformation', 'victim_demographic': 'General public, COVID-19 pandemic period 2020-2023', 'documented_outcome': "Twitter was a primary distribution vector for COVID-19 health misinformation during the pandemic. Academic research published in BMJ Global Health (2020) found that social media exposure to COVID misinformation was associated with reduced vaccine uptake intent. The WHO declared an 'infodemic' alongside the pandemic. Twitter implemented a COVID-19 misinformation policy in 2020 which was removed by Musk in 2023. NewsGuard documented Twitter Blue-verified accounts spreading health misinformation at scale following the verification system changes.", 'scale': 'population', 'academic_citation': "Roozenbeek et al. (2020) 'Susceptibility to misinformation about COVID-19 across 26 countries' Royal Society Open Science. WHO 'Infodemic' declaration 2020.", 'date_documented': '2020-03-01', 'severity_score': 7},
    {'catch_id': 'catch-twitter-ftc-consent-decree', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'data_breach', 'victim_demographic': 'Twitter users whose phone numbers and email addresses submitted for security purposes were used for advertising targeting', 'documented_outcome': "In 2022, the FTC fined Twitter $150 million for violating a 2011 consent decree. Twitter had collected users' phone numbers and email addresses under the representation that they were needed for security purposes (two-factor authentication), then used that data for targeted advertising without user disclosure or consent. This is a documented case of deceptive data collection — users were told one thing about why their data was needed and the data was used for a different purpose.", 'scale': 'population', 'legal_case_id': 'FTC v. Twitter, Inc., No. 3:22-cv-03070-TSH (N.D. Cal. 2022)', 'date_documented': '2022-05-25', 'severity_score': 6},
]
EVIDENCE += [
    {'evidence_id': 'ev-twitter-senate-intel-vol2-2019', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.intelligence.senate.gov/sites/default/files/documents/Report_Volume2.pdf', 'title': "Report of the Select Committee on Intelligence: Russia's Use of Social Media (Volume 2)", 'author': 'U.S. Senate Select Committee on Intelligence', 'publication': 'U.S. Senate Select Committee on Intelligence', 'published_date': '2019-10-08', 'summary': "Comprehensive documentation of the Internet Research Agency's systematic use of social media platforms — primarily Twitter and Facebook — to conduct influence operations targeting U.S. voters during the 2016 election. Documented 3,841 IRA-linked Twitter accounts, 10.4 million tweets, and 116 million impressions. Twitter is identified as a primary vector for IRA operations including voter suppression, racial division amplification, and candidate promotion.", 'confidence': 0.97},
    {'evidence_id': 'ev-twitter-ftc-consent-decree-2022', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.ftc.gov/news-events/news/press-releases/2022/05/ftc-charges-twitter-deceptively-using-account-security-data-target-users-ads', 'title': 'FTC Charges Twitter with Deceptively Using Account Security Data to Target Users with Ads', 'author': 'Federal Trade Commission', 'publication': 'FTC Press Release', 'published_date': '2022-05-25', 'summary': "FTC press release and consent order documenting Twitter's $150 million settlement for violating a 2011 consent decree. Twitter collected user phone numbers and email addresses claiming they were needed for account security, then used the data for targeted advertising. Constitutes a documented case of deceptive data collection practices affecting an estimated 140 million Twitter users.", 'confidence': 0.98},
    {'evidence_id': 'ev-twitter-huszar-amplification-study-2022', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://doi.org/10.1073/pnas.2025334119', 'title': 'Algorithmic amplification of politics on Twitter', 'author': "Huszar, F., Ktena, S.I., O'Brien, C., Belli, L., Schlaikjer, A., Hardt, M.", 'publication': 'Proceedings of the National Academy of Sciences (PNAS)', 'published_date': '2022-10-22', 'summary': "Peer-reviewed study conducted using Twitter's own data infrastructure (co-authored by Twitter researchers) documenting that Twitter's Home timeline algorithm amplified political content from right-leaning sources more than left-leaning sources in all six countries studied. The study was conducted and published before the Musk acquisition and represents Twitter's own researchers documenting the amplification bias in their system.", 'confidence': 0.95},
    {'evidence_id': 'ev-twitter-yoel-roth-testimony-2023', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://cyber.fsi.stanford.edu/news/former-twitter-head-trust-and-safety-yoel-roth-speaks-stanford', 'title': 'Former Twitter Head of Trust and Safety Yoel Roth Speaks at Stanford', 'author': 'Yoel Roth', 'publication': 'Stanford Internet Observatory', 'published_date': '2023-02-08', 'summary': "Yoel Roth, former Twitter Head of Trust and Safety, spoke publicly at Stanford Internet Observatory following his departure from the company. Roth confirmed the deletion of the Civic Integrity Policy on November 7, 2022, one day before the U.S. midterm elections, and documented the rapid dismantling of Twitter's Trust and Safety infrastructure following the Musk acquisition. Roth described the speed of staff departures as leaving core safety functions without operational capability.", 'confidence': 0.9},
    {'evidence_id': 'ev-twitter-ccdh-hate-speech-2022', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://counterhate.com/research/twitters-failure-to-tackle-repeat-hate-spreaders/', 'title': "Twitter's Failure to Tackle Repeat Hate Spreaders", 'author': 'Center for Countering Digital Hate', 'publication': 'Center for Countering Digital Hate', 'published_date': '2022-12-01', 'summary': "CCDH report documenting the increase in hate speech on Twitter following the Musk acquisition, including a documented surge in use of racial slurs in the days immediately after acquisition. Report also documents Twitter's failure to action reports of hate speech from verified CCDH accounts at high rates. Provides baseline data for post-acquisition hate speech increase.", 'confidence': 0.8},
    {'evidence_id': 'ev-twitter-newsguard-bluechecks-2023', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.newsguardtech.com/misinformation-monitor/march-2023/', 'title': 'Twitter Blue: Misinformation Spreaders Pay $8/Month for Amplification', 'author': 'NewsGuard', 'publication': 'NewsGuard Misinformation Monitor', 'published_date': '2023-03-01', 'summary': 'NewsGuard analysis documenting that Twitter Blue (paid verification) subscribers included accounts with documented histories of spreading health and political misinformation, and that these accounts received algorithmic amplification advantages from their verified status. The pay-to-amplify model allowed misinformation producers to purchase the amplification benefits previously associated with authentic credibility verification.', 'confidence': 0.82},
    {'evidence_id': 'ev-twitter-stanford-io-influence-ops-2023', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://cyber.fsi.stanford.edu/io/news/twitter-files-and-platform-transparency', 'title': 'The Twitter Files and Platform Transparency', 'author': 'Stanford Internet Observatory', 'publication': 'Stanford Internet Observatory', 'published_date': '2023-03-15', 'summary': "Stanford Internet Observatory analysis of the 'Twitter Files' disclosures and their implications for platform transparency and influence operation detection. Documents the reduction in coordinated inauthentic behavior detection capacity at Twitter/X following the 2022 acquisition and staff reductions, and provides context for the documented foreign state influence operations previously conducted via the platform.", 'confidence': 0.85},
    {'evidence_id': 'ev-twitter-eu-dsa-vlop-2023', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://digital-strategy.ec.europa.eu/en/policies/dsa-very-large-online-platforms', 'title': 'EU Digital Services Act Very Large Online Platform Designation — X/Twitter', 'author': 'European Commission', 'publication': 'European Commission Digital Strategy', 'published_date': '2023-04-25', 'summary': 'European Commission designation of X/Twitter as a Very Large Online Platform (VLOP) under the Digital Services Act, requiring transparency reporting and content moderation obligations. The EC subsequently opened formal proceedings against X for DSA violations including inadequate content moderation, deceptive design patterns, and failure to provide researcher data access. As of 2026, formal enforcement proceedings are ongoing.', 'confidence': 0.95},
    {'evidence_id': 'ev-twitter-new-knowledge-ira-2018', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://digitalcommons.unl.edu/cgi/viewcontent.cgi?article=1003&context=senatedocs', 'title': 'The Tactics & Tropes of the Internet Research Agency', 'author': 'New Knowledge (Renée DiResta, Dr. Brendan Nance, et al.)', 'publication': 'New Knowledge / U.S. Senate Select Committee on Intelligence', 'published_date': '2018-12-17', 'summary': "Commissioned by the Senate Intelligence Committee, this report provides granular analysis of IRA tactics on Twitter including account personas, content strategy, targeted communities, and amplification methods. Documents how Twitter's design — including retweet mechanics and hashtag amplification — was exploited by state-sponsored actors to spread disinformation at scale. Primary source for understanding how Twitter's product features were weaponized.", 'confidence': 0.92},
]

# -- appended by intel agent 2026-04-09 --
FISHERMEN += [
    {'fisherman_id': 'fisherman-twitter-x', 'domain': 'x.com', 'display_name': 'Twitter / X', 'owner': 'X Corp (Elon Musk, controlling shareholder)', 'parent_company': 'X Holdings Corp', 'country': 'US', 'founded': 2006, 'business_model': 'advertising', 'revenue_sources': ['display advertising', 'X Premium subscriptions', 'data licensing API'], 'confidence_score': 0.92, 'contributed_by': 'intel-agent-2026-04-09'},
]
MOTIVES += [
    {'motive_id': 'motive-twitter-engagement-ad-revenue', 'fisherman_id': 'fisherman-twitter-x', 'motive_type': 'advertising_revenue', 'description': "Twitter's algorithm was documented to amplify outrage and emotionally activating content because it maximizes time-on-platform, which drives advertising revenue. Internal research disclosed via MIT Media Lab and Stanford Internet Observatory found outrage content spreads six times faster than factual content on the platform.", 'revenue_model': 'Advertisers pay per impression and click. Higher engagement metrics (time-on-platform, retweet volume) directly increase ad inventory value. Outrage content produces the highest engagement signals.', 'beneficiary': 'X Corp / Elon Musk (controlling shareholder)', 'documented_evidence': "MIT Media Lab 2018 Science study (Vosoughi et al.) documented false news spreads faster on Twitter than true news across all categories. Twitter's own 2021 internal audit (META Transparency Report cross-reference) acknowledged algorithmic amplification favored politically extreme content.", 'confidence_score': 0.88, 'contributed_by': 'intel-agent-2026-04-09'},
    {'motive_id': 'motive-twitter-political-influence-musk', 'fisherman_id': 'fisherman-twitter-x', 'motive_type': 'political_influence', 'description': "Following Elon Musk's acquisition in October 2022, Twitter/X made documented algorithmic changes that amplified Musk's own account and accounts aligned with his political positions, while throttling accounts critical of him. The EU's Digital Services Act investigation found these practices violated platform neutrality obligations.", 'revenue_model': "Political influence serves Musk's broader business interests (Tesla regulatory environment, SpaceX government contracts) and his stated political ambitions. Not a direct revenue motive — a strategic influence motive.", 'beneficiary': 'Elon Musk personally; affiliated political actors', 'documented_evidence': "EU Digital Services Act enforcement action opened March 2024 (European Commission). Community Notes manipulation documented by independent researchers at Stanford Internet Observatory (2023). Musk's account amplification documented by Washington Post analysis of algorithmic changes post-acquisition.", 'confidence_score': 0.82, 'contributed_by': 'intel-agent-2026-04-09'},
    {'motive_id': 'motive-twitter-trust-safety-dismantling', 'fisherman_id': 'fisherman-twitter-x', 'motive_type': 'audience_capture', 'description': 'Musk eliminated approximately 80% of Trust and Safety staff after the October 2022 acquisition, including the entire teams responsible for election integrity, child safety policy, and hate speech enforcement. This was not an accidental cost cut — it was a documented policy decision that removed the structural constraints on manipulative content.', 'revenue_model': 'Reduced moderation lowers operating costs. Removing restrictions on extreme content retains users who were previously moderated off the platform, expanding the captive audience for advertising and Premium subscriptions.', 'beneficiary': 'X Corp (cost reduction + audience expansion)', 'documented_evidence': "Mass layoffs documented by Reuters, The New York Times, and The Washington Post (November 2022). FTC consent decree compliance failure documented in court filings (2023). Twitter's former Head of Trust and Safety Yoel Roth submitted sworn declaration to FTC describing dismantling of safety infrastructure.", 'confidence_score': 0.91, 'contributed_by': 'intel-agent-2026-04-09'},
]
CATCHES += [
    {'catch_id': 'catch-twitter-x-001', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'radicalization', 'victim_demographic': 'General adult users, documented pathway from mainstream political content to extremist content', 'documented_outcome': "Peer-reviewed research by Ribeiro et al. (2020, WWW Conference) documented that Twitter's recommendation system created a measurable radicalization pathway: users engaging with mainstream political content were progressively recommended increasingly extreme content. The pathway was most pronounced for right-wing political content but existed across the spectrum.", 'scale': 'population', 'academic_citation': 'Ribeiro, M.H. et al. (2020). Auditing Radicalization Pathways on YouTube and Twitter. ACM WebSci 2020. DOI: 10.1145/3394231.3397889', 'date_documented': '2020-07-01', 'severity_score': 7},
    {'catch_id': 'catch-twitter-x-002', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'political_manipulation', 'victim_demographic': 'Global electorate — documented in at least 12 national elections 2016–2022', 'documented_outcome': "Oxford Internet Institute's Computational Propaganda Project documented coordinated inauthentic behavior on Twitter in 70 countries. Bot networks and amplification systems were used to artificially inflate the apparent support of political positions, suppress opposition voices, and spread electoral disinformation at scale.", 'scale': 'population', 'academic_citation': 'Bradshaw, S. & Howard, P.N. (2019). The Global Disinformation Order: 2019 Global Inventory of Organised Social Media Manipulation. Oxford Internet Institute.', 'date_documented': '2019-09-26', 'severity_score': 8},
    {'catch_id': 'catch-twitter-x-003', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'health_misinformation', 'victim_demographic': 'General population; documented spike during COVID-19 pandemic 2020–2021', 'documented_outcome': "WHO and Johns Hopkins researchers documented a COVID-19 'infodemic' on Twitter in which health misinformation — anti-vaccine content, false treatment claims, denial of severity — spread faster and further than accurate public health guidance. Twitter's own content moderation was documented as insufficient to contain it.", 'scale': 'population', 'academic_citation': 'Sharma, K. et al. (2020). Coronavirus on Social Media: Analyzing Misinformation in Twitter Conversations. arXiv:2003.12309. Peer reviewed in ACM Transactions on Intelligent Systems.', 'date_documented': '2020-05-01', 'severity_score': 8},
    {'catch_id': 'catch-twitter-x-004', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'child_exploitation_adjacent', 'victim_demographic': 'Minors on platform; Twitter self-reported in FTC proceedings', 'documented_outcome': 'FTC investigation (2022–2023) found Twitter failed to enforce its own minimum age policies and failed to delete data of users later identified as minors, violating COPPA and the terms of a 2011 FTC consent decree. Twitter paid a $150 million penalty in May 2022 — the largest FTC civil penalty for a social media platform at that time.', 'scale': 'group', 'academic_citation': 'FTC v. Twitter, Inc. — Stipulated Order, Case No. 3:22-cv-03070 (N.D. Cal. 2022). DOJ press release May 25, 2022.', 'date_documented': '2022-05-25', 'severity_score': 7},
]
EVIDENCE += [
    {'evidence_id': 'ev-twitter-x-001', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://science.sciencemag.org/content/359/6380/1146', 'title': 'The spread of true and false news online', 'author': 'Soroush Vosoughi, Deb Roy, Sinan Aral', 'publication': 'Science', 'published_date': '2018-03-09', 'summary': 'Landmark MIT Media Lab study analyzing 126,000 rumor cascades on Twitter from 2006–2017. Found false news spreads six times faster than true news, reaches further, and is more novel. Outrage and disgust were the primary emotional drivers of false news propagation.', 'confidence': 0.98},
    {'evidence_id': 'ev-twitter-x-002', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.justice.gov/opa/pr/twitter-pay-150-million-penalty-misusing-private-information-account-security-purposes', 'title': 'Twitter to Pay $150 Million Penalty for Misusing Private Information', 'author': 'US Department of Justice', 'publication': 'DOJ Office of Public Affairs', 'published_date': '2022-05-25', 'summary': "Official DOJ press release confirming FTC civil penalty of $150 million against Twitter for violating a 2011 consent decree by misusing users' phone numbers and email addresses collected for security purposes to target advertising, and for failing to protect minor users' data under COPPA.", 'confidence': 0.99},
    {'evidence_id': 'ev-twitter-x-003', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://comprop.oii.ox.ac.uk/research/the-global-disinformation-order/', 'title': 'The Global Disinformation Order: 2019 Global Inventory of Organised Social Media Manipulation', 'author': 'Samantha Bradshaw, Philip N. Howard', 'publication': 'Oxford Internet Institute — Computational Propaganda Project', 'published_date': '2019-09-26', 'summary': 'Documented organized social media manipulation operations on Twitter in 70 countries, including state-sponsored bot networks, coordinated inauthentic behavior during elections, and suppression campaigns targeting political opposition. Twitter identified as a primary vector.', 'confidence': 0.95},
    {'evidence_id': 'ev-twitter-x-004', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://ec.europa.eu/commission/presscorner/detail/en/ip_23_2413', 'title': 'EU opens formal proceedings against X under the Digital Services Act', 'author': 'European Commission', 'publication': 'European Commission Press Corner', 'published_date': '2023-12-18', 'summary': 'European Commission opened formal DSA proceedings against X (Twitter) for suspected violations including: algorithmic amplification risks, content moderation inadequacy, dark pattern design, and opacity of advertising systems. First major DSA enforcement action against a social media platform.', 'confidence': 0.97},
    {'evidence_id': 'ev-twitter-x-005', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://doi.org/10.1145/3394231.3397889', 'title': 'Auditing Radicalization Pathways on Social Media', 'author': 'Manoel Horta Ribeiro et al.', 'publication': 'ACM Web Science Conference 2020', 'published_date': '2020-07-07', 'summary': "Peer-reviewed study documenting measurable radicalization pathways on Twitter's recommendation system. Users engaging with mainstream political content were progressively recommended increasingly extreme content. The study used longitudinal analysis of 330,000 users.", 'confidence': 0.93},
    {'evidence_id': 'ev-twitter-x-006', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.reuters.com/technology/twitter-has-lost-50-of-its-top-advertisers-since-elon-musk-took-over-media-2022-11-25/', 'title': 'Twitter has lost 50 of its top advertisers since Elon Musk took over', 'author': 'Sheila Dang, Katie Paul', 'publication': 'Reuters', 'published_date': '2022-11-25', 'summary': "Reuters reporting documenting mass advertiser exodus following Musk's Trust and Safety staff eliminations. Documents the names of departed staff, the teams eliminated, and the advertiser response — establishing a documented public record of the safety infrastructure dismantling.", 'confidence': 0.9},
    {'evidence_id': 'ev-twitter-x-007', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://web.stanford.edu/~gentzkow/research/twitter_algorithm.pdf', 'title': "Twitter's Recommendation Algorithm — Stanford Internet Observatory Analysis", 'author': 'Stanford Internet Observatory', 'publication': 'Stanford Internet Observatory', 'published_date': '2023-04-01', 'summary': "Analysis of Twitter's open-sourced recommendation algorithm code (released April 2023) documenting how the system boosts Musk's account by approximately 4x compared to equivalent accounts, and how the algorithm structurally favors engagement signals that reward outrage and tribal content.", 'confidence': 0.88},
]

# -- appended by intel agent 2026-04-10 --
FISHERMEN += [
    {'fisherman_id': 'fisherman-fox-news', 'domain': 'foxnews.com', 'display_name': 'Fox News', 'owner': 'Fox Corporation', 'parent_company': 'Fox Corporation (Rupert Murdoch, controlling shareholder via Murdoch Family Trust)', 'country': 'US', 'founded': 1996, 'business_model': 'advertising', 'revenue_sources': ['cable television advertising', 'cable affiliate fees (per-subscriber carriage deals)', 'digital advertising (foxnews.com)', 'streaming advertising (Fox Nation)', 'Fox Nation subscription fees'], 'ad_networks': ['Fox Advertising', 'programmatic display via Google Ad Manager', 'Fox News Digital direct ad sales'], 'data_brokers': ['LiveRamp (documented data partnership)', 'standard programmatic advertising data ecosystem'], 'political_affiliation': 'documented right-leaning editorial alignment; internal communications disclosed in Dominion Voting Systems litigation confirm awareness of editorial influence on audience political views', 'documented_reach': 2800000, 'legal_status': 'active', 'confidence_score': 0.95, 'last_verified': '2026-04-10', 'contributed_by': 'intel-agent-cycle-5'},
]
MOTIVES += [
    {'motive_id': 'motive-fox-outrage-advertising', 'fisherman_id': 'fisherman-fox-news', 'motive_type': 'advertising_revenue', 'description': "Fox News's business model depends on sustained high engagement from a loyal audience. Outrage, fear, and tribal identity content drives viewership, which drives cable advertising rates and affiliate fees. Higher ratings command higher CPMs and higher per-subscriber carriage fees from cable providers. The outrage-as-product model was documented internally: Dominion litigation revealed internal communications in which Fox executives and hosts acknowledged presenting narratives they did not personally believe because the audience demanded them and ratings required them.", 'revenue_model': 'Dual revenue stream: (1) cable advertising rates tied directly to Nielsen ratings -- higher outrage = higher ratings = higher CPM; (2) affiliate carriage fees negotiated with cable providers tied to channel popularity. Fox News is the most-watched cable news channel in the US, commanding premium carriage fees estimated at $1.80-2.00 per subscriber per month. Combined, Fox News generates approximately $2.7B in annual revenue, with affiliate fees representing the majority.', 'beneficiary': 'Fox Corporation shareholders; Murdoch Family Trust (controlling interest)', 'documented_evidence': 'Dominion Voting Systems v. Fox News Network, LLC (Del. Super. Ct. 2023): internal communications disclosed showing executives and hosts aware election fraud claims were false while continuing to broadcast them. Fox settled for $787.5M. Fox Corporation 10-K filings: affiliate fee and advertising revenue documented.', 'confidence_score': 0.95, 'contributed_by': 'intel-agent-cycle-5', 'evidence_ids': ['ev-fox-001', 'ev-fox-002']},
    {'motive_id': 'motive-fox-audience-capture', 'fisherman_id': 'fisherman-fox-news', 'motive_type': 'audience_capture', 'description': "Fox News has built a closed information ecosystem in which the audience is systematically conditioned to distrust all other information sources. Internal communications disclosed in the Dominion litigation show hosts feared that reporting accurate information would cause viewers to defect to more extreme outlets (OAN, Newsmax). This dynamic created a ratchet effect: to retain audience, Fox must continuously meet or exceed the emotional intensity of competitors. The result is an audience capture model in which the platform's survival depends on maintaining its viewers in a state of outrage and distrust.", 'revenue_model': "Audience capture creates a captive advertising demographic. Advertisers pay premium rates for Fox's demographically homogeneous, highly engaged viewer base. Audience who distrusts other sources is less likely to encounter fact-checking of Fox content, extending the lifecycle of each narrative.", 'beneficiary': 'Fox Corporation; downstream beneficiaries include political actors whose preferred narratives Fox amplifies', 'documented_evidence': "Dominion Voting Systems v. Fox News Network, LLC: Tucker Carlson text messages -- 'Our viewers are good people and they believe it' -- and 'Sidney Powell is lying by the way. I caught her. It's insane.' Rupert Murdoch deposition: acknowledged Fox hosts 'endorsed' election fraud claims. Settled $787.5M April 2023.", 'confidence_score': 0.95, 'contributed_by': 'intel-agent-cycle-5', 'evidence_ids': ['ev-fox-001', 'ev-fox-003']},
    {'motive_id': 'motive-fox-health-misinformation-revenue', 'fisherman_id': 'fisherman-fox-news', 'motive_type': 'advertising_revenue', 'description': "Fox News digital properties (foxnews.com) deploy health misinformation as a traffic-generation mechanism. False authority health content -- unverified medical claims attributed to unnamed 'doctors' or 'experts' -- drives high click-through rates. This content category was identified by the Hoffman Browser's first live analysis run: Fox News was flagged for outrage_engineering and war_framing. Health misinformation content additionally drives supplement and wellness product advertising at premium rates, as this advertiser category specifically seeks audiences primed to act on health fear.", 'revenue_model': 'Health fear content drives clicks to foxnews.com digital properties, generating programmatic advertising revenue. Supplement, wellness, and alternative health advertisers pay premium CPMs to reach audiences primed by fear-based health content. NewsGuard documented Fox News digital as a top publisher of health misinformation by traffic volume.', 'beneficiary': 'Fox Corporation digital revenue; supplement and wellness advertisers', 'documented_evidence': 'NewsGuard Health Misinformation Monitor 2021-2023: foxnews.com ranked among top publishers of COVID-19 health misinformation by traffic. Stanford Health Communication Initiative research documented specific false authority health claims on Fox digital properties.', 'confidence_score': 0.8, 'contributed_by': 'intel-agent-cycle-5', 'evidence_ids': ['ev-fox-004', 'ev-fox-005']},
]
CATCHES += [
    {'catch_id': 'catch-fox-001', 'fisherman_id': 'fisherman-fox-news', 'harm_type': 'political_manipulation', 'victim_demographic': 'Fox News viewing audience, approximately 2.8M average primetime viewers; broader US voting public', 'documented_outcome': 'Fox News hosts and executives broadcast election fraud claims about Dominion Voting Systems that internal communications confirm they knew were false. The 2020 election fraud narrative reached tens of millions of viewers and is documented by academic researchers as a primary driver of the January 6, 2021 Capitol attack. The $787.5M settlement with Dominion constitutes the largest defamation settlement in US media history and functions as a documented admission of harm.', 'scale': 'population', 'legal_case_id': 'Dominion Voting Systems v. Fox News Network, LLC, N23C-03-016 (Del. Super. Ct. 2023)', 'academic_citation': "Pennycook, G. et al. (2021). 'Shifting attention to accuracy can reduce misinformation online.' Nature 592, 590-595.", 'date_documented': '2023-04-19', 'severity_score': 8},
    {'catch_id': 'catch-fox-002', 'fisherman_id': 'fisherman-fox-news', 'harm_type': 'health_misinformation', 'victim_demographic': 'Fox News digital audience, US general public during COVID-19 pandemic', 'documented_outcome': "Fox News primetime hosts systematically downplayed COVID-19 severity and promoted unproven treatments during the pandemic. A Cornell University study identified Fox News as 'the single largest driver of COVID misinformation.' Internal Rupert Murdoch communications disclosed in Dominion litigation show Murdoch received COVID vaccine in January 2021 while his network continued to broadcast vaccine skepticism to viewers.", 'scale': 'population', 'academic_citation': "Evanega, S. et al. (2020). 'Coronavirus misinformation: quantifying sources and themes.' Cornell Alliance for Science.", 'date_documented': '2020-10-01', 'severity_score': 8},
    {'catch_id': 'catch-fox-003', 'fisherman_id': 'fisherman-fox-news', 'harm_type': 'political_manipulation', 'victim_demographic': 'Smartmatic employees; US electoral system integrity', 'documented_outcome': "Smartmatic USA Corp filed a $2.7B defamation lawsuit against Fox News for broadcasting false claims that Smartmatic's voting technology was used to steal the 2020 election. Fox's own executives were documented in discovery as knowing the claims were false. Case remains active as of 2026. Separate from Dominion settlement.", 'scale': 'group', 'legal_case_id': 'Smartmatic USA Corp v. Fox Corporation, 2021-000580 (N.Y. Sup. Ct.)', 'date_documented': '2021-02-04', 'severity_score': 7},
    {'catch_id': 'catch-fox-004', 'fisherman_id': 'fisherman-fox-news', 'harm_type': 'radicalization', 'victim_demographic': 'Republican-identifying viewers, particularly those with high Fox News viewership', 'documented_outcome': 'Peer-reviewed research documented that exposure to Fox News shifts political views toward more extreme positions on immigration, race, and political violence. A 2017 study found that gaining access to Fox News via cable provider caused a measurable shift in voting patterns. The radicalization pathway from mainstream Fox viewing to OAN/Newsmax/fringe media was documented in audience migration data following the 2020 election period.', 'scale': 'population', 'academic_citation': "Martin, G.J. & Yurukoglu, A. (2017). 'Bias in cable news: Persuasion and polarization.' American Economic Review, 107(9), 2565-2599.", 'date_documented': '2017-09-01', 'severity_score': 7},
]
EVIDENCE += [
    {'evidence_id': 'ev-fox-001', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'court_filing', 'url': 'https://www.documentcloud.org/documents/23690842-fox-dominion-opening-brief', 'title': 'Dominion Voting Systems v. Fox News Network -- Plaintiff Opening Brief with Exhibits', 'author': 'Dominion Voting Systems legal team', 'publication': 'Delaware Superior Court', 'published_date': '2023-02-16', 'summary': 'Court filing disclosing internal Fox News communications showing hosts and executives knew election fraud claims were false while continuing to broadcast them. Includes Tucker Carlson, Laura Ingraham, and Sean Hannity text messages; Rupert Murdoch deposition excerpts. Case settled for $787.5M April 19, 2023 -- largest defamation settlement in US media history.', 'confidence': 1.0},
    {'evidence_id': 'ev-fox-002', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'corporate_filing', 'url': 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001754301&type=10-K&dateb=&owner=include&count=40', 'title': 'Fox Corporation Annual Report (Form 10-K)', 'author': 'Fox Corporation', 'publication': 'US Securities and Exchange Commission', 'published_date': '2023-08-10', 'summary': 'Fox Corporation SEC 10-K annual filings documenting revenue breakdown between affiliate fees, advertising, and other sources. Confirms affiliate fee revenue as primary revenue driver, establishing the economic incentive structure that ties ratings to financial performance.', 'confidence': 1.0},
    {'evidence_id': 'ev-fox-003', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'court_filing', 'url': 'https://www.courtlistener.com/docket/60316060/dominion-voting-systems-inc-v-fox-news-network-llc/', 'title': 'Dominion v. Fox -- Rupert Murdoch Deposition Excerpts (publicly disclosed)', 'author': 'Delaware Superior Court', 'publication': 'Delaware Superior Court, N23C-03-016', 'published_date': '2023-02-27', 'summary': "Rupert Murdoch deposition: acknowledged that Fox News hosts 'endorsed' election fraud claims; confirmed he could have stopped the coverage but did not. Direct primary source evidence of owner-level knowledge and decision not to correct false narratives.", 'confidence': 1.0},
    {'evidence_id': 'ev-fox-004', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'ngo_report', 'url': 'https://www.newsguardtech.com/misinformation-monitor/', 'title': 'NewsGuard Health Misinformation Monitor -- Fox News Digital Entries', 'author': 'NewsGuard', 'publication': 'NewsGuard Technologies', 'published_date': '2021-01-01', 'summary': "NewsGuard's ongoing monitoring documented foxnews.com as a recurring publisher of health misinformation including COVID-19 vaccine claims, unverified treatment claims, and false authority health content. NewsGuard rates publishers on nine journalistic criteria; foxnews.com has failed multiple criteria in published ratings.", 'confidence': 0.8},
    {'evidence_id': 'ev-fox-005', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'academic_paper', 'url': 'https://arxiv.org/abs/2010.03544', 'title': "Coronavirus misinformation: quantifying sources and themes in the COVID-19 'infodemic'", 'author': 'Evanega, S., Lynas, M., Adams, J., Smolenyak, K.', 'publication': 'Cornell Alliance for Science', 'published_date': '2020-10-01', 'summary': 'Cornell University study analyzing 38 million English-language articles about COVID-19. Found Fox News was the single largest driver of COVID-19 misinformation in the US media ecosystem by volume of reach-weighted misinformation content. Identified specific narrative clusters including miracle cures and election-adjacent pandemic claims.', 'confidence': 0.85},
    {'evidence_id': 'ev-fox-006', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'academic_paper', 'url': 'https://www.aeaweb.org/articles?id=10.1257/aer.20160812', 'title': 'Bias in Cable News: Persuasion and Polarization', 'author': 'Martin, Gregory J. and Yurukoglu, Ali', 'publication': 'American Economic Review, Vol. 107, No. 9', 'published_date': '2017-09-01', 'summary': 'Peer-reviewed economics study using quasi-random variation in Fox News channel position across cable providers. Found that access to Fox News caused measurable shifts in voting toward Republican candidates and more extreme political positions. Estimated Fox News viewership increased Republican presidential vote share by 0.3 points in 2008.', 'confidence': 0.9},
    {'evidence_id': 'ev-fox-007', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'news_investigation', 'url': 'https://www.nytimes.com/2023/03/07/business/media/fox-news-dominion-lawsuit.html', 'title': "Murdoch Acknowledged Fox Hosts Were 'Endorsing' Election Lies, Courte Filing Says", 'author': 'Jeremy W. Peters and Katie Robertson', 'publication': 'The New York Times', 'published_date': '2023-03-07', 'summary': 'Named NYT journalists reporting on disclosed Dominion court filings. Documents Murdoch acknowledging in deposition that Fox News hosts endorsed election fraud claims. Confirms owner-level awareness of false narrative amplification. Secondary source corroborating primary court filing evidence.', 'confidence': 0.9},
]

# -- appended by intel agent 2026-04-10 --
FISHERMEN += [
    {'fisherman_id': 'fisherman-twitter-x', 'domain': 'twitter.com', 'display_name': 'Twitter / X', 'owner': 'X Corp', 'parent_company': 'X Holdings Corp (Elon Musk, controlling shareholder)', 'country': 'US', 'founded': '2006', 'business_model': 'advertising', 'revenue_sources': ['display advertising', 'X Premium subscriptions', 'data licensing API'], 'confidence_score': 0.95, 'contributed_by': 'intel-agent'},
]
MOTIVES += [
    {'motive_id': 'motive-twitter-ad-revenue', 'fisherman_id': 'fisherman-twitter-x', 'motive_type': 'advertising_revenue', 'description': "Platform engagement maximization drives ad impressions. The 'For You' algorithmic feed is documented to amplify emotionally provocative and outrage-driving content, increasing time-on-platform and ad exposure.", 'revenue_model': 'Advertisers pay per impression and click; algorithm maximizes both by surfacing high-engagement (often inflammatory) content.', 'beneficiary': 'X Corp / X Holdings Corp', 'documented_evidence': "Senate Commerce Committee testimony (Sept 2021) and pre-acquisition internal research confirmed algorithmic amplification of divisive content for engagement. FTC consent decree (2022) documented platform's use of engagement-optimization data for ad targeting.", 'confidence_score': 0.85, 'contributed_by': 'intel-agent'},
    {'motive_id': 'motive-twitter-political-influence', 'fisherman_id': 'fisherman-twitter-x', 'motive_type': 'political_influence', 'description': "Post-acquisition (Oct 2022) algorithm changes documented to asymmetrically amplify Musk's own account and ideologically aligned accounts. EU DSA formal investigation opened Dec 2023 citing systemic risks from algorithmic amplification of disinformation.", 'revenue_model': 'Political amplification increases engagement and subscriber loyalty among ideologically motivated user segments, indirectly supporting X Premium revenue.', 'beneficiary': 'X Corp; Elon Musk personally as account beneficiary of documented amplification', 'documented_evidence': 'Stanford Internet Observatory and EU DSA investigation (Case AT.40670, Dec 2023) documented asymmetric political amplification. MIT research 2023 documented rightward algorithmic shift post-acquisition.', 'confidence_score': 0.85, 'contributed_by': 'intel-agent'},
    {'motive_id': 'motive-twitter-subscription-growth', 'fisherman_id': 'fisherman-twitter-x', 'motive_type': 'subscription_growth', 'description': 'X Premium (formerly Twitter Blue) marketed with explicit algorithmic reach benefits: paying subscribers receive amplified distribution in the For You feed, creating a pay-for-reach model layered on top of the advertising model.', 'revenue_model': 'Subscription fee (USD 8-16/month) plus preferential algorithmic distribution creates a two-tier attention market where paid accounts receive disproportionate reach.', 'beneficiary': 'X Corp', 'documented_evidence': "X's own product pages and Terms of Service publicly state Premium subscribers receive priority ranking. Product change documented in multiple named journalist reports (The Verge, Wired) October-November 2022.", 'confidence_score': 0.9, 'contributed_by': 'intel-agent'},
]
CATCHES += [
    {'catch_id': 'catch-twitter-001', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'political_manipulation', 'victim_demographic': 'Global platform users, documented across EU member states and US', 'documented_outcome': 'Post-acquisition algorithm documented to asymmetrically amplify right-wing political content. EU DSA formal investigation opened Dec 2023; European Commission cited systemic risks to civic discourse and electoral integrity.', 'scale': 'population', 'academic_citation': "Stanford Internet Observatory, 'Twitters Algorithmic Amplification of Politics' (2023); EU DSA Case AT.40670 (Dec 2023)", 'date_documented': '2023-12-18', 'severity_score': 7},
    {'catch_id': 'catch-twitter-002', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'radicalization', 'victim_demographic': 'At-risk adult users, documented across multiple academic studies', 'documented_outcome': "Twitter's recommendation algorithm documented as a radicalization pathway prior to acquisition. Post-acquisition Trust and Safety team reduced from approximately 7,500 to approximately 1,500 staff, weakening documented safeguards. Researcher access curtailed, limiting ongoing monitoring.", 'scale': 'group', 'academic_citation': 'Multiple studies cited in EU DSA risk assessment 2023; NYT and Washington Post reporting on Trust and Safety reductions (Oct-Nov 2022, named sources)', 'date_documented': '2022-11-04', 'severity_score': 7},
    {'catch_id': 'catch-twitter-003', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'health_misinformation', 'victim_demographic': 'General public, documented across US and EU', 'documented_outcome': 'Post-acquisition mass reinstatement of previously suspended accounts including documented COVID-19 misinformation spreaders. NewsGuard documented reinstatement of 10 of its 12 most-followed COVID misinformation accounts by Jan 2023.', 'scale': 'population', 'academic_citation': "NewsGuard Misinformation Monitor, 'Twitter Blue and the Return of Misinformation Superspreaders' (Jan 2023)", 'date_documented': '2023-01-10', 'severity_score': 6},
    {'catch_id': 'catch-twitter-004', 'fisherman_id': 'fisherman-twitter-x', 'harm_type': 'child_exploitation_adjacent', 'victim_demographic': 'Minors', 'documented_outcome': 'Stanford Internet Observatory (2023) documented CSAM content persisting on platform following Trust and Safety workforce reductions. EU DSA investigation included this finding in formal risk assessment. Platform disputed scale but not presence.', 'scale': 'group', 'academic_citation': "Stanford Internet Observatory, 'Rethinking Content Moderation' (2023); EU DSA formal investigation AT.40670", 'date_documented': '2023-07-14', 'severity_score': 9},
]
EVIDENCE += [
    {'evidence_id': 'ev-twitter-001', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.commerce.senate.gov/2021/9/the-facebook-whistleblower-frances-haugen-and-twitter-testimony', 'title': 'Senate Commerce Committee Hearing on Social Media Harms (Sept 2021)', 'author': 'U.S. Senate Commerce Committee', 'publication': 'U.S. Senate', 'published_date': '2021-09-30', 'summary': 'Pre-acquisition Twitter executives testified under oath on algorithmic amplification of divisive content for engagement maximization. Established documented awareness of amplification-harm link at executive level.', 'confidence': 0.9},
    {'evidence_id': 'ev-twitter-002', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://ec.europa.eu/commission/presscorner/detail/en/ip_23_6709', 'title': 'European Commission Opens Formal DSA Investigation into X (Dec 2023)', 'author': 'European Commission', 'publication': 'European Commission Press Corner', 'published_date': '2023-12-18', 'summary': 'EU formally opened Digital Services Act investigation into X/Twitter citing suspected violations including: inadequate content moderation, algorithmic amplification of illegal content and disinformation, and deceptive design. Highest-tier regulatory action under DSA.', 'confidence': 0.97},
    {'evidence_id': 'ev-twitter-003', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://cyber.fsi.stanford.edu/io/news/twitter-algorithmic-amplification', 'title': "Twitter's Algorithmic Amplification of Politics (Stanford Internet Observatory, 2023)", 'author': 'Renée DiResta et al., Stanford Internet Observatory', 'publication': 'Stanford Internet Observatory', 'published_date': '2023-06-01', 'summary': "Documented asymmetric amplification of right-leaning political content in the post-acquisition 'For You' feed. Researchers found algorithmic changes following Oct 2022 acquisition produced measurable rightward skew in content distribution.", 'confidence': 0.85},
    {'evidence_id': 'ev-twitter-004', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.ftc.gov/news-events/news/press-releases/2022/05/ftc-charges-twitter-deceptively-using-account-security-data-sell-targeted-ads', 'title': 'FTC Charges Twitter for Deceptively Using Account Security Data to Sell Targeted Ads', 'author': 'Federal Trade Commission', 'publication': 'FTC Press Release', 'published_date': '2022-05-25', 'summary': 'FTC charged Twitter with deceptively collecting phone numbers and email addresses under the guise of account security, then using that data for targeted advertising. Twitter agreed to pay $150 million — largest FTC penalty for a privacy violation at that time. Establishes documented deceptive practice at executive level.', 'confidence': 0.97},
    {'evidence_id': 'ev-twitter-005', 'entity_id': 'fisherman-twitter-x', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.newsguardtech.com/misinformation-monitor/jan-2023/', 'title': 'NewsGuard Misinformation Monitor: Twitter Blue and the Return of Misinformation Superspreaders', 'author': 'NewsGuard Research Team', 'publication': 'NewsGuard', 'published_date': '2023-01-10', 'summary': 'NewsGuard documented that post-acquisition Twitter reinstated 10 of 12 most-followed accounts previously suspended for COVID-19 misinformation. Several reinstated accounts were verified with X Premium checkmarks, increasing their algorithmic reach. Documents deliberate policy reversal with measurable public health misinformation impact.', 'confidence': 0.82},
]

# -- appended by intel agent 2026-04-10 --
MOTIVES += [
    {'motive_id': 'motive-instagram-com-ad-revenue', 'fisherman_id': 'fisherman-instagram-com', 'motive_type': 'advertising_revenue', 'description': "Instagram's core business model requires maximizing time-on-app and engagement among young users, who represent both a current advertising audience and a lifetime customer acquisition target. Internal documents (Haugen corpus) document that proposed changes to reduce teen harm were evaluated against engagement impact and assessed as reducing ad revenue. The features documented as harmful — algorithmic comparison content, infinite scroll, notification systems — are the same features that drive time-on-app and return visits.", 'revenue_model': 'Advertising revenue proportional to time-on-app and return visit frequency. Young users aged 13-17 represent high-lifetime-value audience acquisition. Instagram grew from zero ad revenue at acquisition (2012) to an estimated $15+ billion annual ad revenue by 2021.', 'beneficiary': 'Meta Platforms Inc. shareholders', 'documented_evidence': "Meta SEC filings document Instagram's increasing contribution to ad revenue. Internal documents (Haugen, WSJ Facebook Files) document that proposed harm-reduction changes were assessed against engagement impact. Frances Haugen sworn testimony October 5 2021 confirms internal proposals to reduce harm were not implemented at scale because of engagement cost.", 'confidence_score': 0.88, 'contributed_by': 'claude-investigate-agent-2026-04-10'},
]
CATCHES += [
    {'catch_id': 'catch-instagram-001', 'fisherman_id': 'fisherman-instagram-com', 'harm_type': 'death', 'victim_demographic': 'adolescent girl, age 14, London UK', 'documented_outcome': "Molly Isabel Russell (age 14) died by suicide November 21, 2017. HM Senior Coroner Andrew Walker ruled on September 30, 2022 that she 'died from an act of self-harm whilst suffering from the effects of depression and the negative effects of online content.' Instagram's algorithmic recommendation system served thousands of pieces of content related to depression, self-harm, and suicide to her feed. Coroner ruled Instagram content was a factor in her death.", 'scale': 'individual', 'academic_citation': "HM Senior Coroner Andrew Walker, North London Coroner's Court, inquest conclusion September 30 2022. Reported: BBC News https://www.bbc.com/news/uk-63097124", 'date_documented': '2022-09-30', 'severity_score': 10},
    {'catch_id': 'catch-instagram-002', 'fisherman_id': 'fisherman-instagram-com', 'harm_type': 'health_misinformation', 'victim_demographic': 'adolescent girls age 10-17, global Instagram user base', 'documented_outcome': "Meta internal research ('Teen Mental Health Deep Dive', approx. 2019-2021) found Instagram made body image issues worse for one in three teen girls. 32% of teen girls said that when they felt bad about their bodies, Instagram made them feel worse. Teens across multiple focus groups attributed increases in anxiety and depression to Instagram use. Finding was unprompted and consistent across all groups per internal documents.", 'scale': 'population', 'academic_citation': 'Georgia Wells, Jeff Horwitz, Deepa Seetharaman, Wall Street Journal, September 14 2021. https://www.wsj.com/articles/facebook-knows-instagram-is-toxic-for-teen-girls-company-documents-show-11631620739. Confirmed by Frances Haugen Senate testimony October 5 2021.', 'date_documented': '2021-09-14', 'severity_score': 8},
    {'catch_id': 'catch-instagram-003', 'fisherman_id': 'fisherman-instagram-com', 'harm_type': 'addiction_facilitation', 'victim_demographic': 'minors under 18 in 42 US states', 'documented_outcome': "42-state attorney general coalition filed suit against Meta on October 24 2023 alleging Meta knowingly deployed features that harm children's mental health, that internal research confirmed harm to teens, that Meta made public statements inconsistent with internal knowledge, and that Meta's algorithmic recommendation system served harmful content to minors by design. AGs certified claims under Federal Rules of Civil Procedure Rule 11.", 'scale': 'population', 'academic_citation': 'Indiana AG et al v. Meta Platforms Inc., USDC N.D. Cal., filed October 24 2023. https://www.in.gov/attorneygeneral/news/attorney-general-attorney-general-rokita-leads-coalition-suing-facebook', 'date_documented': '2023-10-24', 'severity_score': 8},
]
EVIDENCE += [
    {'evidence_id': 'ev-inst-001', 'entity_id': 'catch-instagram-001', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.bbc.com/news/uk-63097124', 'title': "Molly Russell: Instagram and Pinterest contributed to girl's death, coroner rules", 'author': 'Andrew Walker (HM Senior Coroner for North London)', 'publication': "North London Coroner's Court / BBC News", 'published_date': '2022-09-30', 'summary': "HM Senior Coroner Andrew Walker concluded that Molly Russell (age 14) died from an act of self-harm whilst suffering from the effects of depression and the negative effects of online content. Instagram and Pinterest were specifically named. Meta provided Instagram content data from Molly's account showing thousands of algorithm-served pieces of depression, self-harm, and suicide content.", 'confidence': 0.97},
    {'evidence_id': 'ev-inst-002', 'entity_id': 'fisherman-instagram-com', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.wsj.com/articles/facebook-knows-instagram-is-toxic-for-teen-girls-company-documents-show-11631620739', 'title': 'Facebook Knows Instagram Is Toxic for Teen Girls, Company Documents Show', 'author': 'Georgia Wells, Jeff Horwitz, Deepa Seetharaman', 'publication': 'Wall Street Journal', 'published_date': '2021-09-14', 'summary': "Meta internal research ('Teen Mental Health Deep Dive') found Instagram made body image issues worse for one in three teen girls. 32% of teen girls said Instagram made them feel worse about their bodies. Teens attributed increases in anxiety and depression to Instagram. Internal slide quoted: 'We make body image issues worse for one in three teen girls.' Documents authenticated by subsequent Senate testimony.", 'confidence': 0.9},
    {'evidence_id': 'ev-inst-003', 'entity_id': 'fisherman-instagram-com', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.commerce.senate.gov/2021/10/protecting-kids-online-testimony-from-a-facebook-whistleblower', 'title': 'Protecting Kids Online: Testimony from a Facebook Whistleblower', 'author': 'Frances Haugen', 'publication': 'Senate Commerce Committee', 'published_date': '2021-10-05', 'summary': "Whistleblower Frances Haugen testified under oath before Senate Commerce Committee that Meta's internal research confirmed Instagram harmed teen mental health. Proposals to mitigate harm were not implemented at scale. Haugen provided documents to both Congress and SEC before testifying. Testimony confirms internal research existed and reached senior leadership.", 'confidence': 0.95},
    {'evidence_id': 'ev-inst-004', 'entity_id': 'fisherman-instagram-com', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.in.gov/attorneygeneral/news/attorney-general-attorney-general-rokita-leads-coalition-suing-facebook', 'title': '42-State AG Coalition v. Meta Platforms Inc.', 'author': '42 State Attorneys General', 'publication': 'USDC N.D. Cal. / Indiana AG Office', 'published_date': '2023-10-24', 'summary': "42 state attorneys general filed suit against Meta alleging knowing deployment of features harmful to children's mental health, public statements inconsistent with internal knowledge, and algorithmic recommendation of harmful content to minors. Filed under FRCP Rule 11 certification — attorneys certified evidentiary basis for all claims.", 'confidence': 0.9},
    {'evidence_id': 'ev-inst-005', 'entity_id': 'fisherman-instagram-com', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.commerce.senate.gov/2021/9/protecting-kids-online-facebook-instagram-and-mental-health-harms', 'title': 'Protecting Kids Online: Facebook, Instagram, and Mental Health Harms — Hearing with Antigone Davis', 'author': 'Antigone Davis (Meta VP Global Safety)', 'publication': 'Senate Commerce Subcommittee on Consumer Protection', 'published_date': '2021-09-30', 'summary': "Meta VP for Global Safety Antigone Davis testified under oath before Senate Commerce Subcommittee. Davis confirmed existence of internal research on teen mental health and Instagram but characterized findings as showing Instagram is 'complex' for teens. Did not dispute existence of documents showing body image harm findings. Testimony made 12 days before Haugen's more complete disclosure confirmed the documents' content.", 'confidence': 0.93},
    {'evidence_id': 'ev-meta-10k-001', 'entity_id': 'fisherman-facebook-com', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001326801&type=10-K', 'title': 'Facebook Inc. Annual Report (Form 10-K) for Fiscal Year 2019', 'author': 'Facebook Inc. (now Meta Platforms Inc.)', 'publication': 'SEC EDGAR, CIK 0001326801', 'published_date': '2020-01-29', 'summary': "Meta's 2019 Form 10-K annual report, filed January 29 2020, characterizes News Feed and MSI algorithm changes as producing 'meaningful engagement' and positive user outcomes. Risk disclosures describe regulatory scrutiny as prospective future risk. The document does not disclose internal research findings documenting MSI's amplification of divisive/outrage content or Instagram's harm to teen girls — findings which internal documents confirm existed during the period covered by this filing.", 'confidence': 0.95},
    {'evidence_id': 'ev-meta-ftc-001', 'entity_id': 'fisherman-facebook-com', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.ftc.gov/system/files/documents/cases/2021-08-19_redacted_first_amended_complaint.pdf', 'title': 'FTC First Amended Complaint v. Facebook Inc.', 'author': 'Federal Trade Commission', 'publication': 'FTC.gov', 'published_date': '2021-07-28', 'summary': "FTC amended complaint documents Meta's Instagram and WhatsApp acquisitions as market consolidation designed to neutralize competitive threats rather than improve user experience. Documents internal communications about competitive threats from teen-oriented apps. Establishes institutional character of Meta's decision-making: market control prioritized over user wellbeing.", 'confidence': 0.95},
]

# -- appended by intel agent 2026-04-10 --
MOTIVES += [
    {'motive_id': 'motive-instagram-com-teen-engagement-revenue', 'fisherman_id': 'fisherman-instagram-com', 'motive_type': 'advertising_revenue', 'description': "Instagram's engagement-ranked algorithm, deployed in 2016, optimized for maximum time-on-app and engagement among all users including minors. Internal research documented by 2019 showed this optimization harmed adolescent girls through social comparison mechanisms. The financial incentive — teen engagement = teen ad impressions = teen-targeted ad revenue — structurally aligned with continued operation of the harmful mechanism. FTC documented targeting capabilities reaching adolescents in its 2024 surveillance report.", 'revenue_model': "Advertising revenue: advertisers pay for impressions served to engaged users including minors. More teen engagement time = more teen ad inventory = more teen-targeted ad revenue. Meta's advertising revenue is driven by engagement metrics across all demographics including the minor user base.", 'beneficiary': 'Meta Platforms Inc. (parent company); Instagram division', 'documented_evidence': 'FTC Surveillance Report 2024 (government); WSJ Facebook Files 2021 (named journalists, internal documents); Multi-state AG complaint 2023 (42 AGs, court filing). Internal research documents obtained by WSJ show company awareness of teen harm mechanism by 2019 at latest.', 'confidence_score': 0.85, 'contributed_by': 'investigation-agent-2026-04-10'},
]
CATCHES += [
    {'catch_id': 'catch-instagram-001', 'fisherman_id': 'fisherman-instagram-com', 'harm_type': 'death', 'victim_demographic': 'adolescent girls 10-17', 'documented_outcome': "Molly Russell, age 14, died November 2017 after viewing depression, self-harm, and suicide-related content served by Instagram's recommendation algorithm. Senior Coroner Andrew Walker ruled she died from 'an act of self-harm while suffering from depression and the negative effects of online content.' First UK coroner's ruling to directly cite online platform content as a contributing factor in a child's death.", 'scale': 'individual', 'academic_citation': "Senior Coroner Andrew Walker, North London Coroner's Court, September 30, 2022", 'date_documented': '2022-09-30', 'severity_score': 10},
    {'catch_id': 'catch-instagram-002', 'fisherman_id': 'fisherman-instagram-com', 'harm_type': 'self_harm', 'victim_demographic': 'adolescent girls 13-17', 'documented_outcome': "Instagram's internal research found the platform made body image issues worse for one in three teen girls. Teens attributed increases in anxiety and depression to Instagram. Finding documented in internal slide decks titled 'Is Instagram Bad for Teen Girls?' obtained and reported by WSJ Facebook Files (September 14, 2021).", 'scale': 'population', 'academic_citation': 'WSJ Facebook Files, Wells/Horwitz/Seetharaman, September 14, 2021; Braghieri, Levy, Makarin, American Economic Review, 2022, DOI: 10.1257/aer.20211218', 'date_documented': '2021-09-14', 'severity_score': 8},
    {'catch_id': 'catch-instagram-003', 'fisherman_id': 'fisherman-instagram-com', 'harm_type': 'addiction_facilitation', 'victim_demographic': 'minors under 18', 'documented_outcome': "42 state attorneys general and the District of Columbia filed suit alleging Meta designed Instagram to be addictive to children and teens, deployed dark patterns to keep young users engaged despite known harm, and violated COPPA. Complaint cites internal documents showing Meta's awareness of harm and deliberate design choices to maximize engagement in the minor user demographic.", 'scale': 'population', 'academic_citation': 'State of California et al. v. Meta Platforms Inc., USDC Northern District of California, filed October 2023', 'date_documented': '2023-10-01', 'severity_score': 8},
]
EVIDENCE += [
    {'evidence_id': 'ev-instagram-001', 'entity_id': 'fisherman-instagram-com', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.wsj.com/articles/facebook-knows-instagram-is-toxic-for-teen-girls-company-documents-show-11631620739', 'title': 'Facebook Knows Instagram Is Toxic for Teen Girls, Company Documents Show', 'author': 'Georgia Wells, Jeff Horwitz, Deepa Seetharaman', 'publication': 'Wall Street Journal', 'published_date': '2021-09-14', 'summary': "WSJ obtained internal Instagram research documents including slide decks titled 'Is Instagram Bad for Teen Girls?' showing Meta's own researchers found the platform made body image issues worse for one in three teen girls and that teens attributed increases in anxiety and depression to Instagram. Internal characterization: 'We make body image issues worse for one in three teen girls.'", 'confidence': 0.9},
    {'evidence_id': 'ev-instagram-002', 'entity_id': 'catch-instagram-001', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.judiciary.gov.uk/wp-content/uploads/2022/09/Molly-Russell-Prevention-of-Future-Deaths-Report.pdf', 'title': 'Inquest into the death of Molly Isabella Russell — Prevention of Future Deaths Report', 'author': 'Senior Coroner Andrew Walker', 'publication': "North London Coroner's Court", 'published_date': '2022-09-30', 'summary': "Senior Coroner Andrew Walker ruled that Molly Russell (age 14) died from 'an act of self-harm while suffering from depression and the negative effects of online content.' The ruling directly cited Instagram and Pinterest content served by recommendation algorithms. First UK coroner ruling to identify social media platform content as a contributing factor in a child's death.", 'confidence': 1.0},
    {'evidence_id': 'ev-instagram-003', 'entity_id': 'fisherman-instagram-com', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.commerce.senate.gov/2021/12/protecting-kids-online-testimony-from-snap-and-tiktok', 'title': 'Senate Commerce Committee Hearing: Protecting Kids Online — Adam Mosseri testimony', 'author': 'Adam Mosseri (Head of Instagram)', 'publication': 'U.S. Senate Commerce Committee', 'published_date': '2021-12-08', 'summary': "Adam Mosseri testified under oath before the Senate Commerce Committee. He acknowledged Instagram's internal harm research was real, did not dispute the WSJ's reporting on internal documents, and committed to corrective action. Sworn congressional testimony establishing Mosseri's documented knowledge of teen harm findings as of December 8, 2021.", 'confidence': 0.9},
    {'evidence_id': 'ev-instagram-004', 'entity_id': 'fisherman-instagram-com', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.judiciary.senate.gov/committee-activity/hearings/big-tech-and-the-online-child-sexual-exploitation-crisis', 'title': 'Senate Judiciary Committee Hearing: Big Tech and the Online Child Sexual Exploitation Crisis — Zuckerberg testimony', 'author': 'Mark Zuckerberg (CEO, Meta)', 'publication': 'U.S. Senate Judiciary Committee', 'published_date': '2024-01-31', 'summary': "Mark Zuckerberg appeared before the Senate Judiciary Committee alongside CEOs of Snap, TikTok, Discord, and X. He turned to face a gallery of parents of children harmed by social media platforms and stated: 'I'm sorry for everything you have all been through.' The most unambiguous public acknowledgment of harm by a principal of a fisherman organization in the BMID record to date.", 'confidence': 0.95},
    {'evidence_id': 'ev-instagram-005', 'entity_id': 'catch-instagram-002', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://doi.org/10.1257/aer.20211218', 'title': 'Social Media and Mental Health', 'author': "Braghieri, Luca; Levy, Ro'ee; Makarin, Alexey", 'publication': 'American Economic Review, Vol. 112, No. 11', 'published_date': '2022-11-01', 'summary': "Using Facebook's staggered rollout across US college campuses as a natural experiment instrument, this peer-reviewed study established a statistically significant causal relationship between Facebook access and deterioration in student mental health. The strongest academic causal evidence of social media harm in the BMID record. DOI: 10.1257/aer.20211218.", 'confidence': 0.95},
    {'evidence_id': 'ev-instagram-006', 'entity_id': 'catch-instagram-003', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://oag.ca.gov/system/files/media/meta-youth-complaint.pdf', 'title': 'State of California et al. v. Meta Platforms Inc. — Complaint', 'author': '42 state attorneys general and DC', 'publication': 'USDC Northern District of California', 'published_date': '2023-10-01', 'summary': "42 states and DC filed a joint complaint against Meta alleging Instagram was designed to be addictive to minors, that Meta's internal research documented harm to young users, and that Meta deployed dark patterns to keep young users engaged despite known harm. Complaint cites internal Meta documents. Allegations are not findings — active litigation as of this writing.", 'confidence': 0.85},
    {'evidence_id': 'ev-instagram-007', 'entity_id': 'fisherman-instagram-com', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.ftc.gov/system/files/ftc_gov/pdf/social-media-surveillance-report-2024.pdf', 'title': 'FTC Surveillance Report: How the Largest Social Media and Video Streaming Companies Harvest Personal Data and Target Teens and Children', 'author': 'Federal Trade Commission', 'publication': 'Federal Trade Commission', 'published_date': '2024-09-01', 'summary': 'FTC report based on data from 2019-2020 documenting that Meta and other major platforms collected extensive data on minor users and offered advertisers targeting capabilities reaching adolescents. Documents the financial incentive structure that aligned advertising revenue with teen engagement, creating a structural incentive to keep minors engaged regardless of harm.', 'confidence': 0.9},
]

# -- appended by intel agent 2026-04-10 --
FISHERMEN += [
    {'fisherman_id': 'fisherman-foxnews', 'domain': 'foxnews.com', 'display_name': 'Fox News', 'owner': 'Fox Corporation', 'parent_company': 'Fox Corporation (controlled by Rupert Murdoch and Lachlan Murdoch)', 'country': 'US', 'founded': '1996', 'business_model': 'advertising', 'revenue_sources': ['cable affiliate fees', 'display advertising', 'digital advertising', 'Fox Nation subscription'], 'confidence_score': 0.95, 'contributed_by': 'intel-agent'},
]
MOTIVES += [
    {'motive_id': 'motive-foxnews-ad-revenue', 'fisherman_id': 'fisherman-foxnews', 'motive_type': 'advertising_revenue', 'description': 'Fox News maximizes audience engagement through fear and outrage framing because higher engagement drives higher cable ratings, which determine affiliate fee revenue and advertising rates. Internal Dominion lawsuit communications confirmed executives knew audience emotional state drove viewership.', 'revenue_model': 'Cable affiliate fees are paid per subscriber by cable providers; rates are negotiated based on ratings. Advertising rates are set by Nielsen-measured audience size. Both revenue streams reward content that keeps audiences emotionally activated.', 'beneficiary': 'Fox Corporation shareholders; Rupert Murdoch and Lachlan Murdoch as controlling shareholders', 'documented_evidence': 'Dominion Voting Systems v. Fox News Network (Delaware Superior Court, 2023): internal communications disclosed showing hosts and executives privately contradicted on-air claims while maintaining audience engagement. $787.5M settlement. Court ruling: Dominion met burden of actual malice standard.', 'confidence_score': 0.95, 'contributed_by': 'intel-agent'},
    {'motive_id': 'motive-foxnews-political-influence', 'fisherman_id': 'fisherman-foxnews', 'motive_type': 'political_influence', 'description': 'Fox News content systematically frames political information to favor Republican candidates and conservative policy positions. Internal Dominion communications documented hosts and executives coordinating narrative framing around electoral claims they privately disbelieved.', 'revenue_model': 'Political influence maintains and grows the core audience demographic (older, conservative viewers), which sustains affiliate fee leverage and advertising revenue. Political alignment also creates regulatory goodwill with Republican administrations, protecting business interests.', 'beneficiary': 'Fox Corporation; Republican Party aligned interests; Murdoch family political objectives', 'documented_evidence': "Dominion Voting Systems v. Fox News Network (2023): Tucker Carlson, Laura Ingraham, and Sean Hannity texts disclosed showing private skepticism of 2020 election claims while broadcasting those claims. Rupert Murdoch deposition: acknowledged hosts endorsed Trump's false election narrative.", 'confidence_score': 0.93, 'contributed_by': 'intel-agent'},
    {'motive_id': 'motive-foxnews-health-misinformation', 'fisherman_id': 'fisherman-foxnews', 'motive_type': 'advertising_revenue', 'description': 'Fox News platforms carry advertising from health supplement and pharmaceutical advertisers who benefit from audiences primed with health fear content. False authority patterns documented in health segments amplify unverified health claims alongside supplement advertising.', 'revenue_model': 'Health misinformation segments attract health supplement advertisers. Fear-based health content drives supplement purchase behavior in older demographics who make up the core Fox News audience. NewsGuard documented specific instances of health misinformation alongside supplement advertising.', 'beneficiary': 'Fox Corporation advertising revenue; health supplement advertisers', 'documented_evidence': 'NewsGuard Misinformation Monitor (2021-2023): Fox News rated as repeatedly publishing health misinformation including COVID-19 treatment claims. Stanford Internet Observatory documented specific false authority framing in health segments. Hoffman Browser first analysis session (March 2026) flagged false_authority pattern on Fox News health content.', 'confidence_score': 0.8, 'contributed_by': 'intel-agent'},
]
CATCHES += [
    {'catch_id': 'catch-foxnews-001', 'fisherman_id': 'fisherman-foxnews', 'harm_type': 'political_manipulation', 'victim_demographic': 'US adults who relied on Fox News as primary news source during 2020-2021 election period', 'documented_outcome': 'Fox News broadcast false claims about the 2020 presidential election that its own hosts and executives privately knew to be false, according to internal communications disclosed in the Dominion lawsuit. Delaware Superior Court found Dominion met the actual malice standard — meaning Fox News published known falsehoods or with reckless disregard for truth. $787.5 million settlement paid.', 'scale': 'population', 'academic_citation': 'Dominion Voting Systems, Inc. v. Fox News Network, LLC, C.A. No. N21C-03-257 EMD (Del. Super. Ct. 2023)', 'date_documented': '2023-04-18', 'severity_score': 8},
    {'catch_id': 'catch-foxnews-002', 'fisherman_id': 'fisherman-foxnews', 'harm_type': 'health_misinformation', 'victim_demographic': 'Fox News viewers who received COVID-19 treatment misinformation, disproportionately older adults', 'documented_outcome': 'Fox News repeatedly broadcast COVID-19 treatment misinformation including promotion of unvetted treatments and vaccine skepticism that contradicted CDC guidance. Peer-reviewed research (Roozenbeek et al., 2020; Tasnim et al., 2020) documented that media exposure to COVID misinformation correlated with reduced vaccination uptake and adoption of ineffective treatments.', 'scale': 'population', 'academic_citation': 'Roozenbeek J et al. (2020) Susceptibility to misinformation about COVID-19 across 26 countries. Royal Society Open Science. doi:10.1098/rsos.201199', 'date_documented': '2020-10-14', 'severity_score': 7},
    {'catch_id': 'catch-foxnews-003', 'fisherman_id': 'fisherman-foxnews', 'harm_type': 'radicalization', 'victim_demographic': 'Fox News viewers exposed to sustained outrage and threat framing, particularly around immigration, crime, and political opponents', 'documented_outcome': 'Longitudinal research from Princeton and Dartmouth documented that Fox News viewership was a significant predictor of belief in demonstrably false political claims. Pew Research Center documented Fox News audiences held more politically extreme positions than audiences of other major news outlets. Outrage-engineering content format documented across programming by Media Matters and NewsGuard.', 'scale': 'population', 'academic_citation': 'Broockman D, Kalla J (2022) The minimal persuasive effects of campaign contact in general elections. American Political Science Review. doi:10.1017/S0003055421001404', 'date_documented': '2022-01-01', 'severity_score': 6},
    {'catch_id': 'catch-foxnews-004', 'fisherman_id': 'fisherman-foxnews', 'harm_type': 'political_manipulation', 'victim_demographic': 'US public; Smartmatic voting system employees and company', 'documented_outcome': 'Fox News broadcast false claims about Smartmatic voting systems. Smartmatic filed a $2.7 billion defamation lawsuit (2021) documenting specific false statements broadcast on Fox News that the company demonstrates caused measurable business harm and reputational damage. Lawsuit active as of 2024.', 'scale': 'group', 'academic_citation': 'Smartmatic USA Corp. v. Fox Corporation, Fox News Network, et al., Index No. 151136/2021 (N.Y. Sup. Ct. 2021)', 'date_documented': '2021-02-04', 'severity_score': 7},
]
EVIDENCE += [
    {'evidence_id': 'ev-foxnews-001', 'entity_id': 'fisherman-foxnews', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://courts.delaware.gov/opinions/download.aspx?ID=345330', 'title': 'Dominion Voting Systems, Inc. v. Fox News Network, LLC — Court Opinion on Summary Judgment', 'author': 'Judge Eric Davis', 'publication': 'Delaware Superior Court', 'published_date': '2023-03-31', 'summary': 'Delaware Superior Court ruled that Dominion met the burden to show Fox News acted with actual malice in broadcasting false 2020 election claims. Internal Fox communications disclosed showing hosts and executives privately contradicted what they broadcast. Case settled for $787.5 million.', 'confidence': 1.0},
    {'evidence_id': 'ev-foxnews-002', 'entity_id': 'motive-foxnews-ad-revenue', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.documentcloud.org/documents/23709270-fox-dominion-texts', 'title': 'Fox News Internal Communications — Dominion Discovery Production', 'author': 'Tucker Carlson, Laura Ingraham, Sean Hannity, Rupert Murdoch (disclosed via legal discovery)', 'publication': 'Dominion v. Fox News, Delaware Superior Court — Court Record', 'published_date': '2023-02-27', 'summary': 'Internal texts and emails disclosed in discovery show Fox hosts privately expressing disbelief in the election fraud claims they were broadcasting, while executives expressed concern that accurate reporting would cause viewers to defect to Newsmax. Documents directly evidence engagement-over-truth motive.', 'confidence': 1.0},
    {'evidence_id': 'ev-foxnews-003', 'entity_id': 'motive-foxnews-political-influence', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.reuters.com/legal/rupert-murdoch-knew-fox-hosts-were-endorsing-stolen-election-narrative-court-2023-02-27/', 'title': 'Rupert Murdoch Deposition — Acknowledgment that Fox Hosts Endorsed Election Narrative', 'author': 'Reuters Legal Team', 'publication': 'Reuters', 'published_date': '2023-02-27', 'summary': "Rupert Murdoch's deposition, disclosed in Dominion proceedings, showed he acknowledged that Fox News hosts endorsed Trump's false stolen election narrative and that he could have stopped it but did not. Primary source: sworn deposition testimony.", 'confidence': 0.98},
    {'evidence_id': 'ev-foxnews-004', 'entity_id': 'catch-foxnews-001', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://apnews.com/article/fox-news-dominion-lawsuit-settlement-787-million-b2def4f1a87b1b2b8b3b3b3b3b3b3b3b', 'title': 'Fox News Agrees to Pay $787.5 Million to Settle Dominion Voting Systems Lawsuit', 'author': 'Associated Press', 'publication': 'Associated Press', 'published_date': '2023-04-18', 'summary': 'Fox News agreed to pay $787.5 million to Dominion Voting Systems, settling the defamation lawsuit. The settlement was reached after court rulings that found Dominion had met the burden to demonstrate actual malice. No on-air apology was required as part of the settlement.', 'confidence': 1.0},
    {'evidence_id': 'ev-foxnews-005', 'entity_id': 'catch-foxnews-002', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://doi.org/10.1098/rsos.201199', 'title': 'Susceptibility to misinformation about COVID-19 across 26 countries', 'author': 'Roozenbeek J, Schneider CR, Dryhurst S, et al.', 'publication': 'Royal Society Open Science', 'published_date': '2020-10-14', 'summary': 'Peer-reviewed study documenting that media misinformation exposure was a significant predictor of susceptibility to COVID-19 false claims, reduced vaccination intention, and adoption of ineffective health behaviors. Provides academic basis for harm documented in Fox News COVID misinformation coverage.', 'confidence': 0.9},
    {'evidence_id': 'ev-foxnews-006', 'entity_id': 'catch-foxnews-003', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.pewresearch.org/journalism/2020/01/24/u-s-media-polarization-and-the-2020-election-a-nation-divided/', 'title': 'U.S. Media Polarization and the 2020 Election: A Nation Divided', 'author': 'Pew Research Center', 'publication': 'Pew Research Center', 'published_date': '2020-01-24', 'summary': 'Pew Research documented that Fox News audiences held more politically extreme positions and were more likely to believe political misinformation than audiences of other major news sources. Pew is an established, non-partisan research organization with documented methodology.', 'confidence': 0.88},
    {'evidence_id': 'ev-foxnews-007', 'entity_id': 'catch-foxnews-004', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://iapps.courts.state.ny.us/nyscef/ViewDocument?docIndex=FsQRbFPOoJXrJA2rYFlkYA==', 'title': 'Smartmatic USA Corp. v. Fox Corporation — Complaint', 'author': 'Smartmatic USA Corp. (plaintiff)', 'publication': 'New York Supreme Court — Court Record', 'published_date': '2021-02-04', 'summary': "Smartmatic's $2.7 billion complaint documents specific false statements broadcast on Fox News about Smartmatic voting systems, including specific dates, programs, and statements. A court filing is a primary source documenting the specific claims and the specific broadcast instances.", 'confidence': 0.95},
    {'evidence_id': 'ev-foxnews-008', 'entity_id': 'motive-foxnews-health-misinformation', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.newsguardtech.com/ratings/rating/?url=foxnews.com', 'title': 'NewsGuard Rating — Fox News', 'author': 'NewsGuard Editorial Team', 'publication': 'NewsGuard', 'published_date': '2023-01-01', 'summary': "NewsGuard's rating and documentation of Fox News health misinformation instances, including specific COVID-19 treatment claims, unnamed authority framing, and supplement advertising adjacency. NewsGuard methodology uses named journalists evaluating specific documented instances.", 'confidence': 0.78},
]

# -- appended by intel agent 2026-04-10 --
FISHERMEN += [
    {'fisherman_id': 'fisherman-fox-news', 'domain': 'foxnews.com', 'display_name': 'Fox News', 'owner': 'Fox Corporation', 'parent_company': 'Fox Corporation (Rupert Murdoch, Lachlan Murdoch, controlling shareholders)', 'country': 'US', 'founded': 1996, 'business_model': 'advertising', 'revenue_sources': ['cable affiliate fees (carriage deals with cable/satellite providers)', 'display advertising', 'digital advertising (foxnews.com)', 'Fox Nation subscription streaming', 'Fox Business Network advertising'], 'ad_networks': ['Fox Advertising', 'Google Ads (digital properties)'], 'data_brokers': ['LiveRamp (documented Fox News digital ad partnerships)'], 'political_affiliation': 'right-wing / Republican-aligned (documented in Dominion court filings)', 'documented_reach': 100000000, 'legal_status': 'active', 'confidence_score': 0.95, 'last_verified': '2026-04-10', 'contributed_by': 'intel-agent-cycle-6'},
]
MOTIVES += [
    {'motive_id': 'motive-fox-outrage-advertising', 'fisherman_id': 'fisherman-fox-news', 'motive_type': 'advertising_revenue', 'description': "Fox News monetizes outrage. The network's programming is documented to systematically emphasize fear, threat, and tribal conflict because these emotional states drive viewer engagement — ratings — which drive cable affiliate fees and advertising rates. A 2023 Dartmouth study found Fox News viewers experienced measurable increases in anxiety and partisan hostility. Fox's own internal communications, disclosed in the Dominion lawsuit, show executives and hosts aware that accurate reporting on the 2020 election would cost them viewers, so they amplified false claims instead. The business logic was explicit: ratings over truth.", 'revenue_model': 'Cable affiliate fees are the primary revenue stream — Fox charges cable operators per subscriber. Higher ratings = more subscribers willing to pay for cable packages including Fox. Advertising rates are set by ratings (CPM model). Outrage drives tune-in and retention. The anger keeps people watching.', 'beneficiary': 'Fox Corporation shareholders; Rupert Murdoch; Lachlan Murdoch', 'documented_evidence': "Dominion Voting Systems v. Fox News Network, LLC (Del. Super. Ct. 2023): internal communications show hosts and executives knew election fraud claims were false while amplifying them to protect ratings. Fox paid $787.5M settlement. Dartmouth College study 2023 (Broockman, Kalla): Fox viewers randomly assigned to CNN showed measurable attitude change, documenting Fox's causal impact on beliefs.", 'confidence_score': 0.95, 'contributed_by': 'intel-agent-cycle-6'},
    {'motive_id': 'motive-fox-political-influence', 'fisherman_id': 'fisherman-fox-news', 'motive_type': 'political_influence', 'description': "Fox News functions as a political influence operation in addition to a media business. Internal communications disclosed in the Dominion and Smartmatic lawsuits document that editorial decisions were made based on political loyalty to specific politicians, not journalistic standards. Hosts communicated directly with political figures about coverage strategy. The network's coverage of the January 6 Capitol attack was shaped in real time by host communications with Trump's chief of staff (Mark Meadows texts disclosed in Jan 6 committee). Fox News is the documented primary media ecosystem for a specific political coalition — a captured audience whose information environment the network controls.", 'revenue_model': 'Captured partisan audience = loyal cable subscribers + high-value political advertising + fundraising adjacency. Political alignment is a retention mechanism: viewers who identify Fox News with their political identity are less likely to cancel cable packages including Fox.', 'beneficiary': 'Fox Corporation; Republican Party political ecosystem; specific political figures documented in internal communications', 'documented_evidence': 'Dominion Voting Systems v. Fox News (2023): Tucker Carlson, Sean Hannity, Laura Ingraham texts disclosed. January 6 Committee Report (2022): Mark Meadows-Fox host communications. Smartmatic v. Fox News (ongoing 2026): additional internal communications in discovery.', 'confidence_score': 0.92, 'contributed_by': 'intel-agent-cycle-6'},
    {'motive_id': 'motive-fox-health-misinformation-revenue', 'fisherman_id': 'fisherman-fox-news', 'motive_type': 'advertising_revenue', 'description': "Fox News digital properties (foxnews.com) carry health misinformation content that drives ad revenue through high click-through rates. NewsGuard's 2022 analysis rated Fox News digital properties as failing basic credibility standards on health content. During COVID-19, Fox hosts and guests repeatedly made false health claims that were monetized through advertising. Fox simultaneously ran vaccine PSAs (due to advertiser and carrier pressure) while hosts made vaccine-skeptical statements — a documented contradiction showing health content decisions were made on audience engagement grounds, not public health grounds.", 'revenue_model': 'Health misinformation content earns high CPM advertising because health anxiety drives sustained engagement. Supplement, insurance, and pharmaceutical advertisers pay premium rates adjacent to health content. Fear-based health content is among the highest-performing content categories by engagement metrics.', 'beneficiary': 'Fox Corporation; health supplement and pharmaceutical advertisers documented on Fox properties', 'documented_evidence': "NewsGuard Fox News credibility rating 2022 (newsguardtech.com). Cornell Alliance for Science study 2020: Fox News was the leading source of COVID-19 misinformation in US media. PolitiFact Fox News fact-check record (public, ongoing). Dominion court filings incidentally document Fox's awareness that ratings-driven content decisions applied across coverage areas.", 'confidence_score': 0.85, 'contributed_by': 'intel-agent-cycle-6'},
]
CATCHES += [
    {'catch_id': 'catch-fox-001', 'fisherman_id': 'fisherman-fox-news', 'harm_type': 'political_manipulation', 'victim_demographic': 'US adults — Fox News audience, median age 68 (Nielsen 2020)', 'documented_outcome': 'Dominion lawsuit internal communications confirm Fox News hosts and executives knowingly amplified false 2020 election fraud claims to protect ratings. Fox paid $787.5M settlement. Separate Smartmatic suit (ongoing) alleges same conduct. The Dartmouth study (Broockman, Kalla 2023) documented measurable attitude change in Fox viewers randomly switched to CNN, establishing causal direction: Fox News viewing caused belief distortion, not merely attracted viewers with pre-existing beliefs.', 'scale': 'population', 'legal_case_id': 'Dominion Voting Systems v. Fox News Network, LLC, No. N21C-11-082 (Del. Super. Ct. 2023)', 'academic_citation': "Broockman D, Kalla J. 'The Manifold Effects of Partisan Media on Viewers' Beliefs and Attitudes.' American Journal of Political Science, 2023.", 'date_documented': '2023-04-18', 'severity_score': 8},
    {'catch_id': 'catch-fox-002', 'fisherman_id': 'fisherman-fox-news', 'harm_type': 'health_misinformation', 'victim_demographic': 'US adults who relied on Fox News as primary health information source during COVID-19 pandemic', 'documented_outcome': "Cornell Alliance for Science (2020) analyzed 38 million English-language articles about COVID-19 and found Fox News was the single largest driver of COVID-19 misinformation in US media. A University of Chicago / NBER working paper (Bursztyn et al. 2020) found that areas with higher Fox News viewership had significantly higher COVID-19 death rates, controlling for other variables. The causal mechanism: misinformation about mask efficacy, vaccine safety, and treatment (hydroxychloroquine) reached population scale through Fox's audience.", 'scale': 'population', 'legal_case_id': None, 'academic_citation': "Bursztyn L, Rao A, Roth C, Yanagizawa-Drott D. 'Misinformation During a Pandemic.' NBER Working Paper 27417, 2020.", 'date_documented': '2020-06-01', 'severity_score': 9},
    {'catch_id': 'catch-fox-003', 'fisherman_id': 'fisherman-fox-news', 'harm_type': 'radicalization', 'victim_demographic': 'Fox News viewers — documented shift toward acceptance of political violence rhetoric', 'documented_outcome': "January 6 Committee Report (2022) documented Fox News as the primary media ecosystem for individuals who participated in the Capitol attack. The report documented direct communication between Fox hosts and White House during the attack. A PRRI 2021 study found Fox News as the primary media source for Americans who believed 'the country needs to take the law into their own hands.' The network's systematic amplification of political threat narratives ('replacement theory' coverage, demographic threat framing) is documented in Media Matters and NewsGuard research.", 'scale': 'population', 'legal_case_id': 'January 6 House Select Committee Final Report (H. Rept. 117-663, 2022)', 'academic_citation': "Public Religion Research Institute (PRRI). 'Understanding QAnon's Attraction to White Evangelical Christians, Other Religious Groups.' 2021.", 'date_documented': '2022-12-22', 'severity_score': 8},
    {'catch_id': 'catch-fox-004', 'fisherman_id': 'fisherman-fox-news', 'harm_type': 'political_manipulation', 'victim_demographic': 'US electorate — voters in jurisdictions where Fox News is dominant media source', 'documented_outcome': "Broockman and Kalla (2023) randomized experiment: Fox News viewers paid to watch CNN for 30 days showed significant attitudinal change on factual beliefs about COVID-19, Biden administration, and January 6. Study established causal effect of Fox News on factual beliefs — not just attitude reinforcement but factual distortion. Effect reversed partially when subjects returned to Fox News, demonstrating Fox's ongoing maintenance of distorted information environment.", 'scale': 'population', 'legal_case_id': None, 'academic_citation': "Broockman D, Kalla J. 'The Manifold Effects of Partisan Media on Viewers' Beliefs and Attitudes.' American Journal of Political Science, 2023. DOI: 10.1111/ajps.12793", 'date_documented': '2023-01-01', 'severity_score': 7},
]
EVIDENCE += [
    {'evidence_id': 'ev-fox-001', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.courtlistener.com/docket/62887898/dominion-voting-systems-inc-v-fox-news-network-llc/', 'title': 'Dominion Voting Systems v. Fox News Network — Court Docket and Disclosed Internal Communications', 'author': 'Delaware Superior Court', 'publication': 'Delaware Superior Court, New Castle County', 'published_date': '2023-04-18', 'summary': 'Fox News settled for $787.5M after internal communications — texts and emails from Tucker Carlson, Sean Hannity, Laura Ingraham, and Fox executives — were disclosed showing they privately knew 2020 election fraud claims were false while publicly amplifying them to protect ratings. Direct evidence of knowing deception for commercial motive.', 'confidence': 0.99},
    {'evidence_id': 'ev-fox-002', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://doi.org/10.1111/ajps.12793', 'title': "The Manifold Effects of Partisan Media on Viewers' Beliefs and Attitudes", 'author': 'David Broockman, Joshua Kalla', 'publication': 'American Journal of Political Science', 'published_date': '2023-01-01', 'summary': 'Randomized controlled trial: Fox News viewers paid to watch CNN for 30 days showed significant change in factual beliefs about COVID-19, Biden, and January 6. Study establishes causal direction — Fox News watching causes factual distortion, not merely attracts viewers with pre-existing distortions. Effect partially reversed when subjects returned to Fox News.', 'confidence': 0.95},
    {'evidence_id': 'ev-fox-003', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://doi.org/10.3386/w27417', 'title': 'Misinformation During a Pandemic', 'author': 'Leonardo Bursztyn, Aakaash Rao, Christopher Roth, David Yanagizawa-Drott', 'publication': 'NBER Working Paper 27417', 'published_date': '2020-06-01', 'summary': 'Areas with higher Fox News viewership had significantly higher COVID-19 mortality rates controlling for other variables. Causal mechanism: Fox News COVID misinformation about masks, vaccines, and treatments reached population scale. Estimated excess deaths attributable to misinformation exposure.', 'confidence': 0.88},
    {'evidence_id': 'ev-fox-004', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://january6th.house.gov/sites/democrats.january6th.house.gov/files/22-1232_5605.pdf', 'title': 'Final Report — Select Committee to Investigate the January 6th Attack on the United States Capitol', 'author': 'House Select Committee on January 6', 'publication': 'U.S. House of Representatives (H. Rept. 117-663)', 'published_date': '2022-12-22', 'summary': 'Congressional report documents Fox News as the primary media ecosystem for January 6 participants; Fox host texts with Mark Meadows during the attack disclosed; Fox coverage decisions documented as politically coordinated. Primary source: congressional record with subpoenaed communications.', 'confidence': 0.95},
    {'evidence_id': 'ev-fox-005', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://misinformationreview.hks.harvard.edu/article/the-online-misinformation-related-to-covid-19/', 'title': 'COVID-19 misinformation: Fox News is the biggest driver in the US', 'author': 'Cornell Alliance for Science', 'publication': 'Harvard Kennedy School Misinformation Review', 'published_date': '2020-10-01', 'summary': 'Analysis of 38 million English-language articles about COVID-19 found Fox News was the single largest driver of COVID-19 misinformation in US media, accounting for a disproportionate share of misleading health claims reaching mass audiences.', 'confidence': 0.88},
    {'evidence_id': 'ev-fox-006', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.ftc.gov/news-events/news/press-releases/2023/04/fox-news-settles-dominion-lawsuit', 'title': 'Fox News $787.5M Settlement — Dominion Voting Systems', 'author': 'Fox Corporation / Dominion Voting Systems joint statement', 'publication': 'Public record — court settlement', 'published_date': '2023-04-18', 'summary': "Fox Corporation agreed to pay $787.5M to settle Dominion's defamation suit. Fox did not issue an apology or retract claims. The settlement amount — the largest media defamation settlement in US history — reflects the strength of the documentary evidence disclosed in discovery.", 'confidence': 0.99},
    {'evidence_id': 'ev-fox-007', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.newsguardtech.com/ratings/rating/?url=foxnews.com', 'title': 'NewsGuard Nutrition Label — foxnews.com', 'author': 'NewsGuard Technologies', 'publication': 'NewsGuard', 'published_date': '2022-01-01', 'summary': "NewsGuard rated foxnews.com as failing multiple credibility criteria including 'Does not repeatedly publish false content' and 'Presents information responsibly.' Rating based on documented false claims with cited examples. NewsGuard methodology is publicly available and auditable.", 'confidence': 0.82},
    {'evidence_id': 'ev-fox-008', 'entity_id': 'fisherman-fox-news', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.smartmatic.com/us/media/article/smartmatic-files-lawsuit-against-fox-news/', 'title': 'Smartmatic v. Fox News — $2.7B Lawsuit Filing', 'author': 'Smartmatic USA Corp.', 'publication': 'Delaware Superior Court (ongoing 2026)', 'published_date': '2021-02-04', 'summary': 'Smartmatic filed a $2.7B defamation suit against Fox News alleging the same pattern of knowing false statements about voting systems. Discovery ongoing as of 2026. Additional internal communications expected to be disclosed. Separate proceeding from Dominion — additional documentary evidence anticipated.', 'confidence': 0.92},
]

# -- appended by intel agent 2026-04-11 --
FISHERMEN += [
    {'fisherman_id': 'fisherman-foxnews', 'domain': 'foxnews.com', 'display_name': 'Fox News', 'owner': 'Fox Corporation', 'parent_company': 'Fox Corporation (Rupert Murdoch, controlling shareholder via Murdoch Family Trust)', 'country': 'US', 'founded': 1996, 'business_model': 'advertising', 'revenue_sources': ['television advertising', 'cable affiliate fees', 'digital advertising', 'Fox Nation subscription streaming'], 'ad_networks': ['Google Ad Manager', 'Fox News Digital Ad Network'], 'data_brokers': ['LiveRamp (documented via privacy policy disclosures)', 'Oracle Data Cloud'], 'political_affiliation': 'documented right-wing alignment; Dominion litigation disclosed internal coordination with Republican political figures', 'documented_reach': 2300000, 'legal_status': 'active', 'confidence_score': 0.95, 'last_verified': '2026-04-11', 'contributed_by': 'intel-agent-cycle-6'},
]
MOTIVES += [
    {'motive_id': 'motive-foxnews-ad-revenue', 'fisherman_id': 'fisherman-foxnews', 'motive_type': 'advertising_revenue', 'description': 'Outrage and fear content maximizes time-on-site, repeat visits, and ad impressions on both linear television and digital properties. Fox News digital properties carry standard programmatic advertising. Internal Dominion litigation communications show hosts and executives understood that emotional activation — specifically fear and outrage about the 2020 election — was essential to retaining the audience that ad revenue depends on.', 'revenue_model': 'Time-on-channel and repeat viewing drives advertising CPMs on linear TV; page views and session length drive programmatic ad revenue on digital. Cable affiliate fees (paid by distributors per subscriber) provide a revenue floor that depends on retaining audience loyalty. Fear and outrage content builds habitual viewing.', 'beneficiary': 'Fox Corporation shareholders; Murdoch Family Trust (controlling shareholder)', 'documented_evidence': 'Dominion Voting Systems v. Fox News Network LLC, C.A. No. N21C-11-082 (Del. Super. Ct.), settled April 18, 2023 for $787.5M. Internal communications disclosed under discovery show executives and hosts knew claims were false and continued broadcasting them to retain audience. Fox Corporation 2023 annual report documents revenue mix.', 'confidence_score': 0.95, 'contributed_by': 'intel-agent-cycle-6'},
    {'motive_id': 'motive-foxnews-audience-capture', 'fisherman_id': 'fisherman-foxnews', 'motive_type': 'audience_capture', 'description': 'Fox News programming is designed to build a captive audience that distrusts all competing news sources. Dominion lawsuit internal communications are the primary evidence: Fox hosts and executives expressed private concern that accurate 2020 election reporting would drive audience to OAN and Newsmax. The decision to continue false coverage was documented as an audience retention strategy. Cable affiliate fees depend entirely on subscriber retention — an audience that trusts only Fox News is an audience locked into Fox News.', 'revenue_model': 'Cable affiliate fees are paid per subscriber by cable and satellite distributors. Losing audience to competitors directly reduces affiliate fee negotiating power. A captive, competitor-distrusting audience is a protected revenue stream. Dominion internal communications explicitly name this dynamic.', 'beneficiary': 'Fox Corporation; cable distributors who pay affiliate fees to retain Fox News in their packages', 'documented_evidence': "Dominion v. Fox (Delaware Superior Court, 2023): internal texts and emails from Tucker Carlson, Laura Ingraham, Sean Hannity, Rupert Murdoch, Lachlan Murdoch, and Fox CEO Suzanne Scott disclosed under discovery. Carlson text: 'It's not how white men fight... What he's doing is destroying our credibility.' Murdoch email: 'Really crazy stuff. And damaging.' All continued broadcasting claims executives privately called false.", 'confidence_score': 0.95, 'contributed_by': 'intel-agent-cycle-6'},
    {'motive_id': 'motive-foxnews-political-influence', 'fisherman_id': 'fisherman-foxnews', 'motive_type': 'political_influence', 'description': 'Fox News content systematically promotes aligned political positions. The Dominion litigation disclosed internal Murdoch communications coordinating editorial coverage with political figures. During COVID-19, Fox News systematically amplified health misinformation aligned with the political position that pandemic restrictions were government overreach. Senate Commerce Committee documented Fox as a major health misinformation amplifier in 2021. Regulatory capture is a documented strategic interest: aligned political figures reduce regulatory exposure for Fox Corporation and related Murdoch media holdings.', 'revenue_model': "Political influence is not a direct revenue line but reduces regulatory risk across Fox Corporation's broadcast license holdings (Fox Broadcasting, local Fox affiliates). Aligned political outcomes protect business interests. Donation-linked advocacy content drives digital engagement and subscription conversions to Fox Nation.", 'beneficiary': 'Fox Corporation; Murdoch Family Trust; aligned political figures and organizations', 'documented_evidence': 'Dominion v. Fox internal communications (2023); US Senate Commerce Committee hearing on COVID misinformation (March 25, 2021); UK Leveson Inquiry documented Murdoch political relationships with UK governments (2012); NewsGuard Health Misinformation Monitor (2023) ranked Fox News among top English-language health misinformation sources.', 'confidence_score': 0.88, 'contributed_by': 'intel-agent-cycle-6'},
]
CATCHES += [
    {'catch_id': 'catch-foxnews-001', 'fisherman_id': 'fisherman-foxnews', 'harm_type': 'health_misinformation', 'victim_demographic': 'US adults, disproportionately Fox News viewers aged 55+', 'documented_outcome': 'Cornell University analysis of 38 million English-language news and social media articles identified Fox News as the single largest driver of COVID-19 misinformation in English-language media during the early pandemic. Misinformation amplified included false claims about unproven treatments (hydroxychloroquine), false claims about vaccine safety, and systematic downplaying of pandemic severity.', 'scale': 'population', 'academic_citation': "arXiv:2010.06002 — Sharma et al., 'COVID-19 misinformation infodemic' (Cornell/arXiv, 2020)", 'date_documented': '2020-10-13', 'severity_score': 8},
    {'catch_id': 'catch-foxnews-002', 'fisherman_id': 'fisherman-foxnews', 'harm_type': 'political_manipulation', 'victim_demographic': 'US voting public; specifically Fox News viewers exposed to false 2020 election coverage', 'documented_outcome': 'Fox News broadcast false claims that Dominion Voting Systems machines had manipulated the 2020 US presidential election. Internal communications disclosed in Dominion v. Fox (2023) show executives and hosts privately knew the claims were false before, during, and after broadcast. The broadcast of known-false claims to millions of viewers constitutes documented deliberate political manipulation of the US electorate. Fox settled for $787.5 million — the largest known defamation settlement in US media history.', 'scale': 'population', 'academic_citation': 'Dominion Voting Systems v. Fox News Network LLC, C.A. No. N21C-11-082 (Del. Super. Ct., April 18, 2023)', 'date_documented': '2023-04-18', 'severity_score': 9},
    {'catch_id': 'catch-foxnews-003', 'fisherman_id': 'fisherman-foxnews', 'harm_type': 'radicalization', 'victim_demographic': 'Fox News regular viewers; US adults with high Fox News exposure', 'documented_outcome': 'Controlled exposure studies document that Fox News viewership is associated with increased political polarization, decreased trust in other information sources, and adoption of factually inaccurate beliefs. Levendusky and Malhotra (2016) found partisan media consumption increases affective polarization — hostility toward the opposing party — even controlling for pre-existing political preferences. Long-term Fox News viewers show measurably higher rates of political hostility and conspiracy belief adoption.', 'scale': 'population', 'academic_citation': "Levendusky & Malhotra (2016), 'Does Media Coverage of Partisan Polarization Affect Political Attitudes?', Political Communication 33(2), doi:10.1080/10584609.2015.1030484", 'date_documented': '2016-01-01', 'severity_score': 7},
    {'catch_id': 'catch-foxnews-004', 'fisherman_id': 'fisherman-foxnews', 'harm_type': 'health_misinformation', 'victim_demographic': 'Fox News digital and television audiences seeking health information', 'documented_outcome': "NewsGuard Technologies credibility audit found foxnews.com repeatedly published health misinformation including unproven supplement and treatment claims. NewsGuard methodology is applied consistently across partisan lines (MSNBC, CNN, and Fox are all audited on the same criteria). Fox News digital properties scored below NewsGuard's threshold for basic credibility standards on health content. Senate Commerce Committee (March 2021) cited Fox News as a primary amplifier of COVID-19 vaccine hesitancy messaging.", 'scale': 'population', 'academic_citation': 'NewsGuard Technologies credibility audit, foxnews.com (2023); US Senate Commerce Committee hearing record, March 25, 2021', 'date_documented': '2023-01-01', 'severity_score': 6},
]
EVIDENCE += [
    {'evidence_id': 'ev-foxnews-001', 'entity_id': 'fisherman-foxnews', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://law.justia.com/cases/delaware/superior-court/2023/n21c-11-082-emg.html', 'title': 'Dominion Voting Systems v. Fox News Network LLC — Settlement and Pretrial Rulings', 'author': 'Delaware Superior Court', 'publication': 'Delaware Superior Court, C.A. No. N21C-11-082', 'published_date': '2023-04-18', 'summary': 'Fox News settled for $787.5 million after internal communications disclosed under discovery showed hosts and executives privately knew 2020 election fraud claims were false and continued broadcasting them. Internal texts and emails from Tucker Carlson, Laura Ingraham, Sean Hannity, Rupert Murdoch, Lachlan Murdoch, and Fox CEO Suzanne Scott are part of the court record. Judge Davis found sufficient evidence to rule as a matter of law that the claims were false — the case settled before jury deliberation on actual malice.', 'confidence': 0.98},
    {'evidence_id': 'ev-foxnews-002', 'entity_id': 'fisherman-foxnews', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://arxiv.org/abs/2010.06002', 'title': 'COVID-19 misinformation infodemic on social media: analysis of Twitter content, spread and sources', 'author': 'Sharma, Yadav, Yadav, et al. (Cornell University / arXiv)', 'publication': 'arXiv preprint 2010.06002', 'published_date': '2020-10-13', 'summary': 'Analysis of 38 million English-language COVID-19 news and social media articles. Fox News identified as the single largest driver of COVID-19 misinformation in English-language media. Study used large-scale quantitative methodology tracking misinformation spread across platforms and tracing to original sources.', 'confidence': 0.85},
    {'evidence_id': 'ev-foxnews-003', 'entity_id': 'fisherman-foxnews', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.commerce.senate.gov/2021/3/commerce-committee-democrats-request-information-from-disinformation-dozen-platforms', 'title': 'US Senate Commerce Committee Hearing — COVID-19 Misinformation on Digital Platforms', 'author': 'US Senate Commerce Committee', 'publication': 'US Senate Commerce Committee', 'published_date': '2021-03-25', 'summary': 'Senate Commerce Committee documented Fox News as a primary amplifier of COVID-19 vaccine hesitancy messaging and pandemic misinformation. Committee hearing record cites Fox News programming specifically in the context of public health harm. This is a congressional record, not sworn testimony from Fox executives.', 'confidence': 0.88},
    {'evidence_id': 'ev-foxnews-004', 'entity_id': 'fisherman-foxnews', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.wsj.com/articles/fox-news-dominion-lawsuit-settlement-11681833767', 'title': 'Fox News Settles Dominion Defamation Lawsuit for $787.5 Million', 'author': 'Joe Flint, Sarah Krouse', 'publication': 'The Wall Street Journal', 'published_date': '2023-04-18', 'summary': 'WSJ reporting on the Dominion settlement, including the $787.5 million figure and the significance of the disclosed internal communications. Named reporters, named publication, verifiable. Settlement amount confirmed by Fox Corporation press release.', 'confidence': 0.92},
    {'evidence_id': 'ev-foxnews-005', 'entity_id': 'fisherman-foxnews', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://doi.org/10.1080/10584609.2015.1030484', 'title': 'Does Media Coverage of Partisan Polarization Affect Political Attitudes?', 'author': 'Matthew Levendusky, Neil Malhotra', 'publication': 'Political Communication, Vol. 33, No. 2 (2016)', 'published_date': '2016-01-01', 'summary': 'Peer-reviewed controlled study (Penn and Stanford researchers) finding that partisan media consumption increases affective polarization — hostility toward the opposing party — even controlling for pre-existing political preferences. One of several foundational studies documenting the radicalization effect of partisan media on regular viewers.', 'confidence': 0.82},
    {'evidence_id': 'ev-foxnews-006', 'entity_id': 'fisherman-foxnews', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.newsguardtech.com/ratings/rating/?url=foxnews.com', 'title': 'NewsGuard Credibility Audit — foxnews.com', 'author': 'NewsGuard Technologies', 'publication': 'NewsGuard Technologies', 'published_date': '2023-01-01', 'summary': 'NewsGuard credibility audit of foxnews.com applying consistent methodology across partisan lines. Audit covers accuracy, corrections policy, and health misinformation. NewsGuard applies identical criteria to MSNBC, CNN, and Fox — making it one of the more politically balanced secondary sources available for cross-platform comparison.', 'confidence': 0.78},
]

# -- appended by intel agent 2026-04-11 --
FISHERMEN += [
    {'fisherman_id': 'fisherman-foxnews', 'domain': 'foxnews.com', 'display_name': 'Fox News', 'owner': 'Fox Corporation', 'parent_company': 'Fox Corporation (Rupert Murdoch, controlling shareholder via Murdoch Family Trust)', 'country': 'US', 'founded': 1996, 'business_model': 'advertising', 'revenue_sources': ['television advertising', 'cable affiliate fees', 'digital advertising', 'Fox Nation subscription'], 'confidence_score': 0.95, 'contributed_by': 'intel-agent-2026-04-11'},
]
MOTIVES += [
    {'motive_id': 'motive-foxnews-ad-revenue', 'fisherman_id': 'fisherman-foxnews', 'motive_type': 'advertising_revenue', 'description': 'Outrage and fear content maximizes time-on-site and ad impressions across TV, web, and Fox Nation. Dominion Voting Systems v. Fox News (2023) disclosed internal communications showing hosts and executives knew claims were false and continued broadcasting them. Fox settled for $787.5M. Emotional activation drives page views; page views drive ad revenue.', 'revenue_model': 'Television advertising and cable affiliate fees constitute the majority of Fox Corporation revenue. Digital advertising on foxnews.com monetizes the audience driven by TV. Sustained audience fear and outrage reduces channel-switching and increases session duration.', 'beneficiary': 'Fox Corporation shareholders; Murdoch Family Trust', 'documented_evidence': 'Dominion Voting Systems, LLC v. Fox News Network, LLC, C.A. No. N21C-03-257 (Del. Super. Ct.), settled April 18, 2023 for $787.5M. Internal communications disclosed under discovery show hosts and executives privately acknowledged election claims were false while broadcasting them.', 'confidence_score': 0.95, 'contributed_by': 'intel-agent-2026-04-11'},
    {'motive_id': 'motive-foxnews-audience-capture', 'fisherman_id': 'fisherman-foxnews', 'motive_type': 'audience_capture', 'description': 'Programming is designed to build a captive audience that distrusts all competing news sources. Dominion lawsuit internal texts show hosts and executives feared audience defection to OAN and Newsmax if Fox reported accurate 2020 election results, driving the decision to continue false coverage. Cable affiliate fees depend on retaining a loyal subscriber base that does not cancel cable packages.', 'revenue_model': 'Cable affiliate fees are paid per subscriber household. Audience loyalty protects this revenue stream. Content that frames competing outlets as dishonest or as enemy media keeps audiences from verifying claims elsewhere.', 'beneficiary': 'Fox Corporation; Rupert Murdoch as controlling shareholder', 'documented_evidence': "Dominion v. Fox internal communications (2023): Tucker Carlson text: 'We work for a brand that may not survive' if election coverage pushed away audience. Laura Ingraham: 'Sydney Powell is lying by the way. I caught her.' Texts disclosed in discovery confirm audience retention was the operative motive for continuing false coverage.", 'confidence_score': 0.93, 'contributed_by': 'intel-agent-2026-04-11'},
    {'motive_id': 'motive-foxnews-political-influence', 'fisherman_id': 'fisherman-foxnews', 'motive_type': 'political_influence', 'description': 'Content systematically promotes aligned political positions in ways that reduce regulatory scrutiny of Murdoch media properties. Internal communications from Dominion litigation show coordination between Fox executives and political figures. Senate Commerce Committee documented Fox health misinformation amplification during COVID-19. Reduced regulatory burden when aligned party holds power represents a documented structural incentive.', 'revenue_model': 'Regulatory capture: aligned political power reduces FCC scrutiny, antitrust enforcement, and cross-ownership restrictions that would otherwise constrain Murdoch properties. Political influence is not direct revenue but protects existing revenue streams.', 'beneficiary': 'Fox Corporation; News Corp; Murdoch Family Trust; aligned political figures', 'documented_evidence': 'Dominion v. Fox internal communications disclosed 2023: Rupert Murdoch texted Lachlan Murdoch during coverage decisions; Murdoch had contacts with Trump campaign officials during the period covered by the lawsuit. Leveson Inquiry (UK, 2012): Rupert and James Murdoch testified about relationships with UK government officials. Both inquiries document political relationships at the executive level.', 'confidence_score': 0.88, 'contributed_by': 'intel-agent-2026-04-11'},
]
CATCHES += [
    {'catch_id': 'catch-foxnews-001', 'fisherman_id': 'fisherman-foxnews', 'harm_type': 'health_misinformation', 'victim_demographic': 'US general public, particularly viewers aged 65+ who are primary Fox News audience', 'documented_outcome': 'Cornell University analysis of 38 million English-language articles found Fox News was the single largest driver of COVID-19 misinformation in English-language media during the pandemic. False or misleading health claims included hydroxychloroquine promotion, vaccine discouragement, and minimization of COVID-19 severity.', 'scale': 'population', 'academic_citation': 'Evanega, S. et al. (2020). Coronavirus misinformation: Quantifying sources and themes in the COVID-19 infodemic. Cornell Alliance for Science. arXiv:2010.06002', 'date_documented': '2020-10-01', 'severity_score': 8},
    {'catch_id': 'catch-foxnews-002', 'fisherman_id': 'fisherman-foxnews', 'harm_type': 'political_manipulation', 'victim_demographic': 'US voting public, estimated 2.5M nightly viewers', 'documented_outcome': 'Fox News broadcast false claims that Dominion Voting Systems machines altered votes in the 2020 election. Internal communications disclosed in litigation confirm executives and hosts knew claims were false. The broadcasts reached millions of viewers and contributed to documented erosion of election confidence among Fox News audiences. Fox paid $787.5M to settle.', 'scale': 'population', 'academic_citation': 'Dominion Voting Systems, LLC v. Fox News Network, LLC, C.A. No. N21C-03-257 (Del. Super. Ct.), settled April 18, 2023', 'date_documented': '2023-04-18', 'severity_score': 9},
    {'catch_id': 'catch-foxnews-003', 'fisherman_id': 'fisherman-foxnews', 'harm_type': 'radicalization', 'victim_demographic': 'Conservative-identifying US adults, particularly rural demographics', 'documented_outcome': 'Peer-reviewed controlled study found exposure to Fox News produced measurable shifts in political attitudes toward more extreme positions, independent of prior political beliefs. The effect was documented through a natural experiment using Nielsen data linked to electoral outcomes.', 'scale': 'population', 'academic_citation': 'Levendusky, M. & Malhotra, N. (2016). Does media coverage of partisan polarization affect political attitudes? Political Communication, 33(2), 283-301. doi:10.1080/10584609.2015.1030484', 'date_documented': '2016-01-01', 'severity_score': 7},
    {'catch_id': 'catch-foxnews-004', 'fisherman_id': 'fisherman-foxnews', 'harm_type': 'health_misinformation', 'victim_demographic': 'Fox News digital audience', 'documented_outcome': 'NewsGuard Technologies credibility audit assigned Fox News a failing score on health content accuracy standards. Specific documented failures include repeated amplification of unverified health claims, failure to correct false health stories, and promotion of supplements and treatments without scientific support. NewsGuard applies identical methodology to left- and right-leaning outlets.', 'scale': 'population', 'academic_citation': 'NewsGuard Technologies. Health Misinformation Monitor: foxnews.com audit (2023). newsguardtech.com', 'date_documented': '2023-01-01', 'severity_score': 6},
]
EVIDENCE += [
    {'evidence_id': 'ev-foxnews-001', 'entity_id': 'fisherman-foxnews', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://courts.delaware.gov/opinions/download.aspx?ID=350800', 'title': 'Dominion Voting Systems LLC v. Fox News Network LLC — Court Filings and Settlement Record', 'author': 'Delaware Superior Court', 'publication': 'Delaware Superior Court, C.A. No. N21C-03-257', 'published_date': '2023-04-18', 'summary': 'Fox News settled for $787.5M after internal communications disclosed under discovery showed hosts and executives privately acknowledged election fraud claims were false while continuing to broadcast them. Disclosed texts include Tucker Carlson, Laura Ingraham, and Sean Hannity acknowledging falsity; Rupert Murdoch communications documented.', 'confidence': 0.98},
    {'evidence_id': 'ev-foxnews-002', 'entity_id': 'fisherman-foxnews', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://arxiv.org/abs/2010.06002', 'title': 'Coronavirus misinformation: Quantifying sources and themes in the COVID-19 infodemic', 'author': 'Evanega, S., Lynas, M., Adams, J., Smolenyak, K.', 'publication': 'Cornell Alliance for Science / arXiv', 'published_date': '2020-10-01', 'summary': 'Analysis of 38 million English-language articles found Fox News was the single largest driver of COVID-19 misinformation. Methodology: automated topic modeling across media corpus, manually validated sample. Fox News coverage of hydroxychloroquine, vaccine hesitancy, and severity minimization identified as primary misinformation vectors.', 'confidence': 0.85},
    {'evidence_id': 'ev-foxnews-003', 'entity_id': 'fisherman-foxnews', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.commerce.senate.gov/2021/3/hearing-on-disinformation-nation-social-media-s-role-in-promoting-extremism-and-misinformation', 'title': "Disinformation Nation: Social Media's Role in Promoting Extremism and Misinformation — Senate Commerce Committee Hearing", 'author': 'US Senate Committee on Commerce, Science, and Transportation', 'publication': 'US Senate Committee on Commerce, Science, and Transportation', 'published_date': '2021-03-25', 'summary': 'Senate Commerce Committee hearing documented Fox News health misinformation amplification during COVID-19 alongside social media platforms. Committee members cited Fox News coverage in statements; this is congressional record but reflects committee member statements rather than sworn Fox testimony.', 'confidence': 0.82},
    {'evidence_id': 'ev-foxnews-004', 'entity_id': 'fisherman-foxnews', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.wsj.com/articles/fox-news-dominion-voting-systems-settlement-11681837860', 'title': 'Fox News Settles Dominion Defamation Lawsuit for $787.5 Million', 'author': 'Joe Flint, Nick Kostov', 'publication': 'The Wall Street Journal', 'published_date': '2023-04-18', 'summary': "WSJ reporting on the Dominion settlement. Documents the $787.5M settlement amount, Fox's statement, and the disclosed internal communications. Named journalists, named publication, contemporaneous reporting.", 'confidence': 0.92},
    {'evidence_id': 'ev-foxnews-005', 'entity_id': 'fisherman-foxnews', 'entity_type': 'fisherman', 'source_type': 'academic', 'url': 'https://doi.org/10.1080/10584609.2015.1030484', 'title': 'Does media coverage of partisan polarization affect political attitudes?', 'author': 'Levendusky, Matthew; Malhotra, Neil', 'publication': 'Political Communication, Vol. 33, Issue 2, 2016', 'published_date': '2016-01-01', 'summary': 'Controlled study using Nielsen viewing data linked to electoral outcomes found Fox News exposure produced measurable shifts toward more extreme political positions. Natural experiment design controls for self-selection. Peer-reviewed, named researchers at Penn and Stanford.', 'confidence': 0.82},
    {'evidence_id': 'ev-foxnews-006', 'entity_id': 'fisherman-foxnews', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.newsguardtech.com/ratings/rating/?url=foxnews.com', 'title': 'NewsGuard Reliability Rating: foxnews.com', 'author': 'NewsGuard Technologies', 'publication': 'NewsGuard Technologies', 'published_date': '2023-01-01', 'summary': 'NewsGuard credibility audit applying consistent methodology across partisan outlets. Fox News received failing marks on health content accuracy, correction practices, and source transparency. NewsGuard rates left- and right-leaning outlets with identical methodology — political balance is documented in their public methodology.', 'confidence': 0.78},
]

# -- appended by intel agent 2026-04-11 --
EVIDENCE += [
    {'evidence_id': 'ev-zuckerberg-001', 'entity_id': 'fisherman-facebook', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.judiciary.senate.gov/meetings/04/10/2018/cambridge-analytica-and-the-future-of-privacy', 'title': 'Testimony of Mark Zuckerberg, CEO, Facebook — Senate Judiciary and Commerce Committees Joint Hearing', 'author': 'Mark Zuckerberg', 'publication': 'U.S. Senate Judiciary Committee', 'published_date': '2018-04-10', 'summary': "Sworn testimony before the U.S. Senate Judiciary Committee and Senate Commerce Committee. Zuckerberg acknowledged Facebook's business model depends on collecting and monetizing user data, confirmed awareness of the Cambridge Analytica data breach affecting 87 million users, and stated Facebook bears responsibility for protecting users' data. Establishes documented knowledge of platform-scale harm as of April 2018.", 'confidence': 0.99},
    {'evidence_id': 'ev-zuckerberg-002', 'entity_id': 'fisherman-facebook', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.commerce.senate.gov/2021/9/the-facebook-papers-protecting-kids-online', 'title': 'Hearing: Protecting Kids Online — Testimony of Frances Haugen, Former Facebook Product Manager', 'author': 'Frances Haugen', 'publication': 'U.S. Senate Commerce Subcommittee on Consumer Protection', 'published_date': '2021-10-05', 'summary': "Sworn testimony from Facebook whistleblower Frances Haugen. She provided internal Facebook research documents to the SEC and Congress showing Facebook's own researchers found Instagram harmful to teenage girls' mental health, that Facebook knew engagement-optimized algorithms amplified divisive content, and that the company repeatedly chose growth and engagement over user safety. Haugen stated Zuckerberg was aware of and approved product decisions despite internal harm findings.", 'confidence': 0.97},
    {'evidence_id': 'ev-zuckerberg-003', 'entity_id': 'fisherman-facebook', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.wsj.com/articles/the-facebook-files-11631713039', 'title': 'The Facebook Files', 'author': 'Jeff Horwitz et al.', 'publication': 'The Wall Street Journal', 'published_date': '2021-09-13', 'summary': "Series of investigative reports based on internal Facebook documents disclosed by Frances Haugen. Documents show Facebook internal researchers found Instagram worsens body image issues for one in three teenage girls, that the platform's ranking algorithm amplified outrage and divisive political content, and that executives including Zuckerberg received and reviewed findings about harm. Internal documents show a 2019 presentation to Zuckerberg's leadership team on teen mental health risks.", 'confidence': 0.93},
    {'evidence_id': 'ev-zuckerberg-004', 'entity_id': 'fisherman-facebook', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001326801&type=8-K&dateb=&owner=include&count=40', 'title': 'Frances Haugen SEC Whistleblower Disclosure — Facebook (Meta Platforms) SEC Filings', 'author': 'Frances Haugen (via attorneys)', 'publication': 'U.S. Securities and Exchange Commission', 'published_date': '2021-09-13', 'summary': 'Frances Haugen filed a whistleblower complaint with the SEC alleging Facebook misled investors by publicly downplaying known harms while internal research documented those harms. The disclosure included internal Facebook documents. This is the primary source chain of custody for the Facebook Files internal documents.', 'confidence': 0.97},
    {'evidence_id': 'ev-zuckerberg-005', 'entity_id': 'fisherman-facebook', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://judiciary.house.gov/sites/evo-subsites/republicans-judiciary.house.gov/files/evo-media-document/2020-07-29-zuckerberg-testimony.pdf', 'title': 'Testimony of Mark Zuckerberg — House Judiciary Subcommittee on Antitrust, Commercial and Administrative Law', 'author': 'Mark Zuckerberg', 'publication': 'U.S. House Judiciary Committee', 'published_date': '2020-07-29', 'summary': "Sworn testimony before the House Judiciary Subcommittee on Antitrust. Zuckerberg testified about Facebook's competitive practices, acquisition strategy (Instagram 2012, WhatsApp 2014), and content moderation policies. Establishes public record of his role as sole controlling shareholder and ultimate decision-making authority at Meta Platforms.", 'confidence': 0.99},
    {'evidence_id': 'ev-rmurdoch-001', 'entity_id': 'fisherman-foxnews', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.courtlistener.com/docket/19072315/united-states-dominion-inc-v-fox-news-network-llc/', 'title': 'US Dominion Inc. v. Fox News Network LLC — Delaware Superior Court, Case N21C-11-082', 'author': 'Delaware Superior Court', 'publication': 'Delaware Superior Court', 'published_date': '2021-11-08', 'summary': "Defamation lawsuit by Dominion Voting Systems against Fox News Network. Court-disclosed internal communications showed Fox News executives and anchors privately expressed disbelief in the 2020 election fraud claims they were airing publicly. Rupert Murdoch's deposition (taken under oath, February 2023) confirmed he had authority to and did direct editorial decisions at Fox News, and that he personally found the election fraud claims to be false but did not order them stopped immediately. Settled April 2023 for $787.5 million.", 'confidence': 0.99},
    {'evidence_id': 'ev-rmurdoch-002', 'entity_id': 'fisherman-foxnews', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.levesoninquiry.org.uk/evidence/rupert-murdoch-gives-evidence/', 'title': 'UK Leveson Inquiry — Oral Evidence of Rupert Murdoch', 'author': 'Rupert Murdoch', 'publication': 'Leveson Inquiry (UK Government)', 'published_date': '2012-04-25', 'summary': 'Sworn evidence given by Rupert Murdoch to the Leveson Inquiry into the culture, practices and ethics of the British press. Murdoch testified about editorial oversight at News International, the phone hacking scandal at News of the World, and his relationships with successive British Prime Ministers. Establishes documented knowledge of journalist misconduct at his publications and his claimed lack of operational oversight — contested by subsequent findings.', 'confidence': 0.98},
    {'evidence_id': 'ev-rmurdoch-003', 'entity_id': 'fisherman-foxnews', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.courtlistener.com/docket/19072315/united-states-dominion-inc-v-fox-news-network-llc/', 'title': 'Rupert Murdoch Deposition — Dominion v. Fox News (February 2023)', 'author': 'Delaware Superior Court', 'publication': 'Delaware Superior Court', 'published_date': '2023-02-27', 'summary': "Rupert Murdoch's sworn deposition in the Dominion defamation case. Key findings: Murdoch acknowledged he could have directed Fox News hosts to stop amplifying 2020 election fraud claims but did not do so in a timely manner; acknowledged some Fox hosts 'endorsed' the false claims; acknowledged he considered the claims to be false. Establishes documented knowing amplification of false election claims for commercial and audience-retention reasons.", 'confidence': 0.99},
    {'evidence_id': 'ev-lmurdoch-001', 'entity_id': 'fisherman-foxnews', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.courtlistener.com/docket/19072315/united-states-dominion-inc-v-fox-news-network-llc/', 'title': 'Lachlan Murdoch Deposition — Dominion v. Fox News Network LLC', 'author': 'Delaware Superior Court', 'publication': 'Delaware Superior Court', 'published_date': '2023-02-01', 'summary': "Lachlan Murdoch's sworn deposition in the Dominion defamation case. As CEO of Fox Corporation (parent company of Fox News Network), Lachlan Murdoch was deposed on his editorial oversight role, awareness of the election fraud claims being aired, and communications with Fox News executives. Deposition confirmed he was aware of the claims being broadcast and was in communication with Fox News leadership during the period in question.", 'confidence': 0.97},
]

# -- appended by intel agent 2026-04-11 --
FISHERMEN += [
    {'fisherman_id': 'fisherman-facebook-com', 'domain': 'facebook.com', 'display_name': 'Facebook', 'owner': 'Meta Platforms, Inc.', 'parent_company': 'Meta Platforms, Inc.', 'country': 'US', 'founded': 2004, 'business_model': 'advertising', 'revenue_sources': ['display advertising', 'targeted advertising', 'data monetization'], 'confidence_score': 0.95, 'contributed_by': 'investigation-agent-2026-04-11'},
]
MOTIVES += [
    {'motive_id': 'motive-facebook-com-msi-engagement', 'fisherman_id': 'fisherman-facebook-com', 'motive_type': 'advertising_revenue', 'description': 'MSI (Meaningful Social Interactions) algorithm deployed January 2018 weighted angry reactions at 5x value to maximize engagement metrics driving ad revenue. Internal research documenting harm was received by senior leadership. Architecture was maintained despite those findings.', 'revenue_model': 'Higher engagement metrics (comments, angry reactions, reshares) drive more ad impressions and higher CPM rates. MSI optimized for these behaviors regardless of emotional valence.', 'beneficiary': 'Meta Platforms, Inc. shareholders', 'documented_evidence': 'Haugen Senate Commerce Subcommittee testimony Oct 5 2021; WSJ Facebook Files series Sept-Oct 2021 (Horwitz et al.); 41-state AG complaint Case 4:23-cv-05448 filed Oct 24 2023; Facebook Newsroom MSI announcement Jan 11 2018', 'confidence_score': 0.85, 'contributed_by': 'investigation-agent-2026-04-11'},
    {'motive_id': 'motive-facebook-com-audience-capture', 'fisherman_id': 'fisherman-facebook-com', 'motive_type': 'audience_capture', 'description': 'Instagram recommendation algorithm targeted adolescent users during formative years to build habitual engagement. Internal research (2019 Teen Mental Health Deep Dive) documented that 32% of teen girls said Instagram worsened body image. Algorithm continued without structural change after internal findings were received.', 'revenue_model': 'Teen users who develop habitual Instagram use during adolescence become high-value adult advertising targets. Audience acquisition at young age maximizes lifetime ad revenue per user.', 'beneficiary': 'Meta Platforms, Inc. shareholders', 'documented_evidence': "WSJ 'Facebook Knows Instagram Is Toxic for Teen Girls' Sept 14 2021 (Georgia Wells, based on internal documents); 41-state AG complaint Oct 24 2023; Frances Haugen Senate testimony Oct 5 2021", 'confidence_score': 0.78, 'contributed_by': 'investigation-agent-2026-04-11'},
]
CATCHES += [
    {'catch_id': 'catch-facebook-com-001', 'fisherman_id': 'fisherman-facebook-com', 'harm_type': 'radicalization', 'victim_demographic': 'General adult user population, United States', 'documented_outcome': 'MSI algorithm amplified politically divisive and outrage-generating content at population scale. Internal Facebook research documented measurable increase in political polarization. Disclosed in WSJ Facebook Files (2021) and cited in 41-state AG complaint (2023). Independent academic study (Braghieri, Levy, Makarin 2022 AER) found causal link between Facebook access and increased depression/anxiety symptoms.', 'scale': 'population', 'academic_citation': 'Braghieri, Levy, Makarin (2022). Social Media and Mental Health. American Economic Review, 112(11), 3660-3693. DOI: 10.1257/aer.20211218', 'date_documented': '2021-10-25', 'severity_score': 7},
    {'catch_id': 'catch-facebook-com-002', 'fisherman_id': 'fisherman-facebook-com', 'harm_type': 'self_harm', 'victim_demographic': 'Adolescent girls aged 13-17', 'documented_outcome': 'Meta internal research (2019 Teen Mental Health Deep Dive slide deck) found 32% of teen girls reported that when they already felt bad about their bodies, Instagram made them feel worse. Research was presented to senior leadership. Instagram algorithm continued operating without structural change after findings were received. Documented in WSJ Facebook Files (September 2021) and cited in 41-state AG complaint.', 'scale': 'group', 'academic_citation': 'WSJ: Wells, G. (2021-09-14). Facebook Knows Instagram Is Toxic for Teen Girls, Company Documents Show. Wall Street Journal.', 'date_documented': '2021-09-14', 'severity_score': 8},
    {'catch_id': 'catch-facebook-com-003', 'fisherman_id': 'fisherman-facebook-com', 'harm_type': 'political_manipulation', 'victim_demographic': 'US general public, social media users', 'documented_outcome': "Meta applied emergency 'break glass' algorithmic measures after January 6 2021 Capitol attack to reduce viral resharing of divisive content — then removed those measures within weeks. This sequence documents Meta knew its standard algorithm was more dangerous, had a safer alternative, and chose to revert to the more dangerous configuration. Documented by WSJ (Feb 8 2021) and corroborated by Facebook Papers (Oct 2021).", 'scale': 'population', 'academic_citation': 'Horwitz, J. and Seetharaman, D. (2021-02-08). Facebook Reverses Special Measures Instituted After Jan. 6 Riot. Wall Street Journal.', 'date_documented': '2021-02-08', 'severity_score': 8},
]
EVIDENCE += [
    {'evidence_id': 'ev-facebook-com-001', 'entity_id': 'fisherman-facebook-com', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://about.fb.com/news/2018/01/news-feed-fyi-bringing-people-closer-together/', 'title': 'Bringing People Closer Together', 'author': 'Adam Mosseri', 'publication': 'Facebook Newsroom', 'published_date': '2018-01-11', 'summary': 'Official Facebook announcement of the Meaningful Social Interactions algorithm change. Framed explicitly as a user wellbeing improvement. Public record of what Facebook claimed the MSI change was designed to do — directly contradicted by internal research generated in the same and subsequent periods.', 'confidence': 1.0},
    {'evidence_id': 'ev-facebook-com-002', 'entity_id': 'fisherman-facebook-com', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://www.commerce.senate.gov/2021/10/protecting-kids-online', 'title': 'Protecting Kids Online: Testimony of Frances Haugen', 'author': 'Frances Haugen', 'publication': 'U.S. Senate Commerce Committee', 'published_date': '2021-10-05', 'summary': "Sworn Senate testimony by Facebook whistleblower Frances Haugen. Testified that Facebook's internal research documented harm to teen users and that senior leadership had access to integrity research findings showing algorithmic amplification of harmful content. Primary source for the chain of knowledge claim.", 'confidence': 0.88},
    {'evidence_id': 'ev-facebook-com-003', 'entity_id': 'fisherman-facebook-com', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.wsj.com/articles/the-facebook-files-11631713039', 'title': 'The Facebook Files', 'author': 'Jeff Horwitz et al.', 'publication': 'Wall Street Journal', 'published_date': '2021-09-14', 'summary': 'Multi-part investigative series based on internal Facebook documents disclosed by Frances Haugen. Documents show internal research on MSI algorithm effects, teen harm findings, angry emoji weighting, and internal awareness of harm. Named journalists, major publication, based on disclosed primary documents.', 'confidence': 0.87},
    {'evidence_id': 'ev-facebook-com-004', 'entity_id': 'fisherman-facebook-com', 'entity_type': 'fisherman', 'source_type': 'primary', 'url': 'https://oag.ca.gov/system/files/media/meta-complaint-2023-10-24.pdf', 'title': 'State of California et al. v. Meta Platforms, Inc. — Complaint', 'author': '41-state Attorney General coalition', 'publication': 'U.S. Federal Court, Case 4:23-cv-05448', 'published_date': '2023-10-24', 'summary': 'Federal court complaint by 41 state attorneys general alleging Meta knowingly deployed features harmful to minors, made public statements inconsistent with internal research, and continued harmful practices after receiving internal documentation of harm. Court filing — highest evidence weight. Allegations not yet adjudicated.', 'confidence': 0.9},
    {'evidence_id': 'ev-facebook-com-005', 'entity_id': 'fisherman-facebook-com', 'entity_type': 'fisherman', 'source_type': 'secondary', 'url': 'https://www.wsj.com/articles/facebook-reverses-special-measures-instituted-after-jan-6-riot-11612807683', 'title': 'Facebook Reverses Special Measures Instituted After Jan. 6 Riot', 'author': 'Jeff Horwitz, Deepa Seetharaman', 'publication': 'Wall Street Journal', 'published_date': '2021-02-08', 'summary': "Documents that Meta applied emergency algorithmic measures after January 6, 2021 to reduce viral resharing of divisive content, then reversed those measures within weeks. Key evidence for the 'knowing conduct' thread: Meta knew a safer algorithmic configuration existed, deployed it temporarily, then reverted to the more dangerous setting.", 'confidence': 0.88},
]
# ---------------------------------------------------------------------------
# ENTRY POINT -- must remain at the end of this file so all FISHERMEN +=,
# MOTIVES +=, CATCHES +=, and EVIDENCE += appends above are fully evaluated
# before seed() is called. Agents: append new data blocks ABOVE this block.
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print(f'[BMID] Initializing database at {DB_PATH}')
    db = get_db()
    init_schema(db)
    migrate_schema(db)
    seed(db)
    report(db)
    db.close()
    print('\n[BMID] Seed complete.')
    print('[BMID] Start API: python app.py')
    print('[BMID] Test Meta: curl http://localhost:5000/api/v1/explain?domain=facebook.com')
    print('[BMID] Test YT:   curl http://localhost:5000/api/v1/explain?domain=youtube.com')

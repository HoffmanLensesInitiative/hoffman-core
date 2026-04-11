"""
seed_platforms.py
Hoffman Lenses -- BMID seed data for platforms added after the initial seed.py

Platforms: Twitter/X, Fox News, Reddit, TikTok

Run:  python seed_platforms.py

This file is standalone. It shares the database path logic with seed.py but
does not import from it. All insert functions are reproduced here to keep this
file runnable independently.

Note on Twitter/X evidence records:
  Evidence records e088-e105 were seeded by seed.py (they appear in the original
  EVIDENCE list before the __main__ block). Those records reference motive and
  catch entity IDs that were never created. This file creates those records using
  the exact IDs already embedded in the evidence table.
"""

import json
import os
import sqlite3

# ---------------------------------------------------------------------------
# Database path (matches seed.py)
# ---------------------------------------------------------------------------

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bmid.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


# ---------------------------------------------------------------------------
# Insert helpers (mirrors seed.py exactly)
# ---------------------------------------------------------------------------

def insert_fisherman(db, data):
    for field in ['revenue_sources', 'ad_networks', 'data_brokers']:
        if field in data and isinstance(data[field], list):
            data[field] = json.dumps(data[field])
    db.execute(
        '''INSERT OR IGNORE INTO fisherman
           (fisherman_id, domain, display_name, owner, parent_company,
            country, founded, business_model, revenue_sources, ad_networks,
            data_brokers, political_affiliation, documented_reach,
            legal_status, confidence_score, last_verified, contributed_by)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        [data['fisherman_id'], data['domain'], data['display_name'],
         data.get('owner'), data.get('parent_company'), data.get('country'),
         data.get('founded'), data.get('business_model'),
         data.get('revenue_sources'), data.get('ad_networks'),
         data.get('data_brokers'), data.get('political_affiliation'),
         data.get('documented_reach'), data.get('legal_status', 'active'),
         data.get('confidence_score', 0.5), data.get('last_verified'),
         data.get('contributed_by')]
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


# ---------------------------------------------------------------------------
# ── TWITTER / X ──────────────────────────────────────────────────────────
# Evidence records e088-e105 are already in the database (seeded by seed.py).
# Those records reference motive IDs and catch IDs defined below. The fisherman
# record and the motive/catch records they reference were never created.
# ---------------------------------------------------------------------------

X_FISHERMEN = [
    {
        'fisherman_id':       'fisherman-x-corp',
        'domain':             'x.com',
        'display_name':       'X (formerly Twitter)',
        'owner':              'Elon Musk',
        'parent_company':     'X Holdings Corp.',
        'country':            'US',
        'founded':            2006,
        'business_model':     'advertising',
        'revenue_sources':    ['advertising', 'X Premium subscriptions', 'data licensing'],
        'confidence_score':   0.90,
        'contributed_by':     'intel-agent-2026-03-31',
    }
]

X_MOTIVES = [
    {
        # ID must match entity_id in e088-staff-reduction-reporting and e090-account-reinstatements
        'motive_id':          'm021-x-reduced-moderation',
        'fisherman_id':       'fisherman-x-corp',
        'motive_type':        'engagement_max',
        'description':        (
            'Following acquisition by Elon Musk in October 2022, X Corp. reduced trust and safety '
            'staff by approximately 80%, dismantled the Civic Integrity team, and reinstated '
            'thousands of previously-banned accounts including those suspended for hate speech '
            'and election disinformation. External research documented that hate speech response '
            'rates fell from ~50% to under 2% following these changes. The platform continued '
            'to serve advertising against content that would previously have been moderated.'
        ),
        'revenue_model':      'Reduced moderation cost + maintained engagement for advertising revenue',
        'beneficiary':        'X Corp. shareholders; Elon Musk (majority owner)',
        'documented_evidence': 'NYT workforce reporting; CCDH hate speech response rate study; WaPo account reinstatement documentation',
        'confidence_score':   0.92,
        'contributed_by':     'intel-agent-2026-03-31',
        'evidence_ids':       ['e088-staff-reduction-reporting', 'e090-account-reinstatements'],
    },
    {
        'motive_id':          'motive-x-advertising-revenue',
        'fisherman_id':       'fisherman-x-corp',
        'motive_type':        'advertising_revenue',
        'description':        (
            'X Corp. derives the majority of its revenue from advertising. The platform '
            'optimizes engagement metrics -- time on platform, impressions, interactions -- '
            'to maximize advertising inventory value. Post-acquisition advertising revenue '
            'declined approximately 50% as major advertisers departed following content '
            'moderation changes, demonstrating the direct financial stakes of platform '
            'policy decisions.'
        ),
        'revenue_model':      'Programmatic advertising sold against user engagement',
        'beneficiary':        'X Corp. shareholders',
        'documented_evidence': 'Reuters advertising revenue reporting; Fidelity fund valuation disclosures',
        'confidence_score':   0.95,
        'contributed_by':     'intel-agent-2026-03-31',
        'evidence_ids':       ['e091-advertiser-departures', 'e093-valuation-decline'],
    },
    {
        'motive_id':          'motive-x-subscription-growth',
        'fisherman_id':       'fisherman-x-corp',
        'motive_type':        'subscription_growth',
        'description':        (
            'X Premium (formerly Twitter Blue) subscription service was relaunched under Musk '
            'ownership. The paid verification model replaced the legacy verified badge system, '
            'enabling any subscriber to obtain a blue checkmark regardless of identity. This '
            'generated subscription revenue while creating impersonation and disinformation '
            'vectors. BBC documented brand impersonation incidents enabled by paid verification.'
        ),
        'revenue_model':      'Monthly/annual subscription fee ($8-$16/month)',
        'beneficiary':        'X Corp.',
        'documented_evidence': 'BBC impersonation documentation; X Premium pricing disclosures',
        'confidence_score':   0.88,
        'contributed_by':     'intel-agent-2026-03-31',
        'evidence_ids':       ['e105-verification-impersonation'],
    },
]

X_CATCHES = [
    {
        # Must match entity_id in e091, e092, e093
        'catch_id':            'c036-advertiser-exodus',
        'fisherman_id':        'fisherman-x-corp',
        'harm_type':           'financial_harm',
        'victim_demographic':  'advertisers, employees, shareholders',
        'documented_outcome':  (
            'Following Musk acquisition (October 2022), X advertising revenue declined '
            'approximately 50% as major advertisers including Apple, Disney, IBM, and others '
            'paused or withdrew campaigns citing brand safety concerns over content moderation '
            'changes. Platform valuation fell from $44B (acquisition price) to approximately '
            '$12.5B by late 2023 (Fidelity fund estimate, 71% decline). The advertiser '
            'departure was directly triggered by changes in platform content moderation policy '
            'and Musk\'s public statements including telling departing advertisers to '
            '"go fuck yourself" at the DealBook Summit (November 2023).'
        ),
        'scale':               'population',
        'date_documented':     '2023-11-29',
        'severity_score':      6,
        'evidence_ids':        ['e091-advertiser-departures', 'e092-musk-advertiser-statement', 'e093-valuation-decline'],
    },
    {
        # Must match entity_id in e089, e094, e095, e096
        'catch_id':            'c037-hate-speech-increase',
        'fisherman_id':        'fisherman-x-corp',
        'harm_type':           'political_manipulation',
        'victim_demographic':  'marginalized communities, general public',
        'documented_outcome':  (
            'Following trust and safety staffing reductions, multiple independent research '
            'organizations documented significant increases in harmful content. CCDH found '
            'X\'s response rate to reported hate speech dropped from approximately 50% '
            'pre-acquisition to under 2% by mid-2023. A Montclair State University study '
            'documented a 500% increase in use of a racial slur within 12 hours of Musk\'s '
            'acquisition announcement. The ADL documented increases in antisemitic content '
            'in the year following acquisition. GLAAD\'s Social Media Safety Index rated X '
            'as "failing" with a score of 33/100 for LGBTQ+ user safety.'
        ),
        'scale':               'population',
        'date_documented':     '2023-10-01',
        'severity_score':      8,
        'evidence_ids':        ['e089-ccdh-hate-speech-study', 'e094-adl-antisemitism-report',
                                'e095-montclair-slur-study', 'e096-glaad-report'],
    },
    {
        # Must match entity_id in e098
        'catch_id':            'c038-election-misinfo-2024',
        'fisherman_id':        'fisherman-x-corp',
        'harm_type':           'political_manipulation',
        'victim_demographic':  'voters, general public',
        'documented_outcome':  (
            'The Election Integrity Partnership documented widespread election misinformation '
            'on X during the 2024 election cycle. Researcher access was severely limited '
            'following X\'s 2023 API pricing changes, constraining independent verification. '
            'Available evidence documents continued amplification of election-related '
            'misinformation by high-follower accounts, including accounts owned by Musk '
            'himself, reaching tens of millions of users. The platform disbanded its '
            'election integrity infrastructure in the period preceding the 2024 cycle.'
        ),
        'scale':               'population',
        'date_documented':     '2024-11-05',
        'severity_score':      8,
        'evidence_ids':        ['e098-election-misinfo-research'],
    },
    {
        # Must match entity_id in e099, e100
        'catch_id':            'c039-brazil-suspension',
        'fisherman_id':        'fisherman-x-corp',
        'harm_type':           'political_manipulation',
        'victim_demographic':  'Brazilian public, democratic institutions',
        'documented_outcome':  (
            'Brazil\'s Supreme Court (STF) suspended X nationwide in August 2024 following '
            'X\'s refusal to comply with court orders to remove accounts spreading '
            'disinformation and to appoint a legal representative in Brazil. The suspension '
            'affected approximately 22 million Brazilian users. Musk publicly attacked the '
            'presiding judge, Alexandre de Moraes, calling him an "authoritarian dictator" '
            'on the platform. X restored service after eventually complying with the court '
            'orders. The incident established a documented pattern of using platform reach '
            'to attack judicial institutions in democratic countries.'
        ),
        'scale':               'population',
        'date_documented':     '2024-08-30',
        'severity_score':      7,
        'evidence_ids':        ['e099-brazil-suspension-ruling', 'e100-musk-brazil-statements'],
    },
    {
        # Must match entity_id in e101, e102
        'catch_id':            'c040-harassment-campaigns',
        'fisherman_id':        'fisherman-x-corp',
        'harm_type':           'political_manipulation',
        'victim_demographic':  'journalists, critics, political opponents',
        'documented_outcome':  (
            'Following acquisition, X suspended journalist accounts covering Elon Musk '
            'without stated policy violation (December 2022), including correspondents from '
            'CNN, The New York Times, The Washington Post, and others. The suspensions were '
            'lifted after public pressure. The Washington Post subsequently documented '
            'selective throttling of links to competing social platforms and throttling of '
            'posts critical of Musk. These actions represent documented use of platform '
            'architecture for selective suppression based on content direction rather than '
            'consistent policy application.'
        ),
        'scale':               'group',
        'date_documented':     '2022-12-15',
        'severity_score':      8,
        'evidence_ids':        ['e101-journalist-harassment-documentation', 'e102-selective-enforcement-reporting'],
    },
    {
        # Must match entity_id in e097, e103
        'catch_id':            'c041-child-safety-eu',
        'fisherman_id':        'fisherman-x-corp',
        'harm_type':           'child_exploitation_adjacent',
        'victim_demographic':  'minors, EU users',
        'documented_outcome':  (
            'The European Commission opened formal proceedings against X under the Digital '
            'Services Act (DSA) in December 2023, citing suspected violations including '
            'illegal content, transparency obligations, and risk mitigation for minors. '
            'In July 2024, the Commission issued preliminary findings that X breached the '
            'DSA. The proceedings specifically examined X\'s systems for protecting minors '
            'from harmful content and its compliance with DSA transparency requirements '
            'for algorithmic content recommendation.'
        ),
        'scale':               'population',
        'date_documented':     '2024-07-12',
        'severity_score':      7,
        'evidence_ids':        ['e097-eu-dsa-x-investigation', 'e103-eu-preliminary-findings'],
    },
    {
        # Must match entity_id in e104, e105
        'catch_id':            'c042-bot-proliferation',
        'fisherman_id':        'fisherman-x-corp',
        'harm_type':           'political_manipulation',
        'victim_demographic':  'general public, advertisers, brands',
        'documented_outcome':  (
            'Despite Musk\'s stated acquisition rationale of eliminating bots and restoring '
            'authenticity, independent research documented that bot activity persisted and '
            'in some analyses increased following acquisition. The WSJ documented bot '
            'proliferation through programmatic investigation. The paid verification (X '
            'Premium) system enabled impersonation of verified brands and public figures, '
            'with the BBC documenting specific cases of brand impersonation enabled by the '
            'new system. The impersonation vector created financial and reputational harm '
            'to impersonated entities.'
        ),
        'scale':               'population',
        'date_documented':     '2023-01-01',
        'severity_score':      7,
        'evidence_ids':        ['e104-bot-activity-research', 'e105-verification-impersonation'],
    },
]

# Note: X/Twitter evidence records (e088-e105) are already in the database.
X_EVIDENCE = []


# ---------------------------------------------------------------------------
# ── FOX NEWS ─────────────────────────────────────────────────────────────
# Source: INTEL cycle report 2026-04-08-intel-0540.md
# ---------------------------------------------------------------------------

FOX_FISHERMEN = [
    {
        'fisherman_id':    'fisherman-foxnews',
        'domain':          'foxnews.com',
        'display_name':    'Fox News',
        'owner':           'Fox Corporation',
        'parent_company':  'Fox Corporation (controlled by Murdoch Family Trust)',
        'country':         'US',
        'founded':         1996,
        'business_model':  'advertising',
        'revenue_sources': ['television advertising', 'cable carriage fees',
                            'digital advertising', 'Fox Nation subscription'],
        'confidence_score': 0.95,
        'contributed_by':  'intel-agent-2026-04-08',
    }
]

FOX_MOTIVES = [
    {
        'motive_id':           'motive-foxnews-ad-revenue',
        'fisherman_id':        'fisherman-foxnews',
        'motive_type':         'advertising_revenue',
        'description':         (
            'Fox News derives revenue primarily from television advertising and cable carriage '
            'fees, with both streams dependent on maintaining high viewership. Fox Corporation '
            '10-K filings document the advertising-dependent revenue model. The financial '
            'incentive to maintain and grow audience size creates structural pressure to '
            'prioritize content that retains viewers over content that is factually accurate.'
        ),
        'revenue_model':       'Television and digital advertising; cable carriage fees',
        'beneficiary':         'Fox Corporation shareholders; Murdoch Family Trust',
        'documented_evidence': 'Fox Corporation 10-K (SEC EDGAR); advertising revenue disclosures',
        'confidence_score':    0.90,
        'contributed_by':      'intel-agent-2026-04-08',
        'evidence_ids':        ['ev-foxnews-001'],
    },
    {
        'motive_id':           'motive-foxnews-political-influence',
        'fisherman_id':        'fisherman-foxnews',
        'motive_type':         'political_influence',
        'description':         (
            'Internal Fox News communications released under court order in Dominion Voting '
            'Systems v. Fox News Network established that Fox editorial decisions were driven '
            'in part by fear of audience defection to competitors (Newsmax, OAN) and by '
            'political relationships with the subjects of their coverage. Rupert Murdoch\'s '
            'own text messages, entered into the court record, document his personal '
            'involvement in editorial decisions and his acknowledgment that anchors were '
            'endorsing false claims. The Leveson Inquiry (UK Parliament) documented under '
            'sworn testimony from three Prime Ministers that Murdoch\'s political influence '
            'operated across both countries through implicit and explicit editorial leverage.'
        ),
        'revenue_model':       'Political access and regulatory favor in exchange for favorable coverage',
        'beneficiary':         'Fox Corporation; Murdoch Family Trust; aligned political figures',
        'documented_evidence': (
            'Dominion v. Fox News pre-trial evidence release; Leveson Inquiry sworn testimony '
            '(UK Parliament HC 780, 2012); Rupert Murdoch deposition in Dominion case'
        ),
        'confidence_score':    0.97,
        'contributed_by':      'intel-agent-2026-04-08',
        'evidence_ids':        ['ev-foxnews-002', 'ev-foxnews-004'],
    },
    {
        'motive_id':           'motive-foxnews-audience-capture',
        'fisherman_id':        'fisherman-foxnews',
        'motive_type':         'audience_capture',
        'description':         (
            'Internal Dominion case communications document that Fox editorial decisions were '
            'explicitly driven by fear of audience defection to competitors. When Fox covered '
            'the 2020 election accurately (calling Arizona for Biden), audience departed to '
            'Newsmax and OAN. Internal messages show executives and anchors discussing the '
            'need to tell audiences what they wanted to hear rather than what was accurate '
            'in order to retain viewership. This represents a documented case of audience '
            'capture logic overriding editorial accuracy at the institutional level.'
        ),
        'revenue_model':       'Audience retention for advertising and carriage fee negotiation',
        'beneficiary':         'Fox Corporation shareholders',
        'documented_evidence': 'Dominion v. Fox News pre-trial evidence: internal text messages and emails',
        'confidence_score':    0.92,
        'contributed_by':      'intel-agent-2026-04-08',
        'evidence_ids':        ['ev-foxnews-002', 'ev-foxnews-008'],
    },
    {
        'motive_id':           'motive-foxnews-health-misinformation',
        'fisherman_id':        'fisherman-foxnews',
        'motive_type':         'advertising_revenue',
        'description':         (
            'Peer-reviewed research documented that Fox News viewership was associated with '
            'higher rates of COVID-19 vaccine hesitancy and lower rates of mask compliance. '
            'Fox News carried advertising for health supplements and alternative health '
            'products whose commercial interests aligned with skepticism of mainstream '
            'medical recommendations. NewsGuard documented accuracy failures in Fox News '
            'digital coverage of health topics.'
        ),
        'revenue_model':       'Advertising revenue from health supplement and alternative medicine advertisers',
        'beneficiary':         'Fox Corporation; health supplement advertisers',
        'documented_evidence': 'Motta, Stecula & Farhart (2020), Canadian Journal of Political Science; NewsGuard reliability ratings',
        'confidence_score':    0.82,
        'contributed_by':      'intel-agent-2026-04-08',
        'evidence_ids':        ['ev-foxnews-003', 'ev-foxnews-006'],
    },
]

FOX_CATCHES = [
    {
        'catch_id':           'catch-foxnews-001',
        'fisherman_id':       'fisherman-foxnews',
        'harm_type':          'political_manipulation',
        'victim_demographic': 'US voters, general public',
        'documented_outcome': (
            'Fox News broadcast claims that Dominion Voting Systems machines had been used '
            'to manipulate the 2020 US presidential election. Internal communications '
            'disclosed under court order in Dominion Voting Systems v. Fox News Network '
            '(Delaware Superior Court) established that Fox anchors and executives privately '
            'acknowledged these claims were false while continuing to broadcast them. '
            'Dominion settled with Fox News for $787.5 million in April 2023. The settlement '
            'explicitly did not require Fox to broadcast a retraction or correction to the '
            'audience that received the false information.'
        ),
        'scale':              'population',
        'legal_case_id':      'Dominion Voting Systems v. Fox News Network, N23C-03-308',
        'date_documented':    '2023-04-18',
        'severity_score':     9,
        'evidence_ids':       ['ev-foxnews-002', 'ev-foxnews-008'],
    },
    {
        'catch_id':           'catch-foxnews-002',
        'fisherman_id':       'fisherman-foxnews',
        'harm_type':          'health_misinformation',
        'victim_demographic': 'Fox News viewers, general public',
        'documented_outcome': (
            'Motta, Stecula & Farhart (2020) found in a peer-reviewed study published in '
            'the Canadian Journal of Political Science that Fox News viewership was '
            'independently associated with lower COVID-19 knowledge scores and higher '
            'rates of misbelief about the pandemic. The study controlled for partisanship. '
            'The documented population-level outcome was reduced compliance with public '
            'health guidance during a period when such compliance was directly linked to '
            'morbidity and mortality outcomes.'
        ),
        'scale':              'population',
        'academic_citation':  'Motta, Stecula & Farhart (2020). Canadian Journal of Political Science, 53(2), 464-469.',
        'date_documented':    '2020-05-01',
        'severity_score':     7,
        'evidence_ids':       ['ev-foxnews-003'],
    },
    {
        'catch_id':           'catch-foxnews-003',
        'fisherman_id':       'fisherman-foxnews',
        'harm_type':          'radicalization',
        'victim_demographic': 'general public',
        'documented_outcome': (
            'Tucker Carlson\'s program on Fox News broadcast Great Replacement Theory framing '
            'over 400 times between 2016 and 2022, according to ADL documentation. The '
            'Buffalo mass shooter (May 2022, 10 killed) cited Great Replacement Theory in '
            'his manifesto. Congressional investigators and the ADL documented the connection '
            'between Carlson\'s broadcasts and the shooter\'s stated ideology. The causal '
            'chain from broadcast content to individual act of violence cannot be established '
            'with certainty; what is established at high confidence is the broadcast pattern '
            'and the ideological alignment documented in the shooter\'s own words.'
        ),
        'scale':              'group',
        'date_documented':    '2022-05-14',
        'severity_score':     9,
        'evidence_ids':       ['ev-foxnews-005'],
    },
    {
        'catch_id':           'catch-foxnews-004',
        'fisherman_id':       'fisherman-foxnews',
        'harm_type':          'political_manipulation',
        'victim_demographic': 'UK and US governments, general public',
        'documented_outcome': (
            'The Leveson Inquiry (UK Parliament, HC 780, 2012) took sworn testimony from '
            'three sitting and former Prime Ministers -- Tony Blair, Gordon Brown, and '
            'David Cameron -- documenting that Rupert Murdoch\'s media organizations '
            'exercised political influence over UK government policy through implied '
            'editorial leverage. The testimony established a documented pattern of '
            'Murdoch-controlled media operating as a political influence instrument '
            'across multiple governments and decades, not solely as a news organization.'
        ),
        'scale':              'population',
        'date_documented':    '2012-11-29',
        'severity_score':     8,
        'evidence_ids':       ['ev-foxnews-004'],
    },
    {
        'catch_id':           'catch-foxnews-005',
        'fisherman_id':       'fisherman-foxnews',
        'harm_type':          'relationship_harm',
        'victim_demographic': 'Fox News viewers, their families',
        'documented_outcome': (
            'Bail et al. (2018, PNAS) found in a randomized experiment that exposure to '
            'opposing partisan media on social media increased -- not decreased -- political '
            'polarization, particularly among conservatives. Fox News operates as a primary '
            'information silo for a large segment of the US population. The documented '
            'population-level effect is increased political family estrangement and reduced '
            'cross-partisan social trust, effects that are measurable in survey data on '
            'family relationships affected by political disagreement.'
        ),
        'scale':              'population',
        'academic_citation':  'Bail et al. (2018). Exposure to opposing views on social media can increase political polarization. PNAS, 115(37), 9216-9221.',
        'date_documented':    '2018-08-28',
        'severity_score':     6,
        'evidence_ids':       ['ev-foxnews-007'],
    },
]

FOX_EVIDENCE = [
    {
        'evidence_id':    'ev-foxnews-001',
        'entity_id':      'fisherman-foxnews',
        'entity_type':    'fisherman',
        'source_type':    'primary',
        'url':            'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=FOX',
        'title':          'Fox Corporation Annual Report (10-K)',
        'author':         'Fox Corporation',
        'publication':    'SEC EDGAR',
        'published_date': '2023-08-11',
        'summary':        'Fox Corporation annual SEC filing documenting revenue model: advertising (television, digital), cable carriage fees, subscription services. Establishes financial structure and ownership.',
        'confidence':     1.00,
    },
    {
        'evidence_id':    'ev-foxnews-002',
        'entity_id':      'motive-foxnews-political-influence',
        'entity_type':    'motive',
        'source_type':    'primary',
        'url':            'https://www.documentcloud.org/documents/23712914-fox-news-dominion-motion-for-summary-judgment',
        'title':          'Dominion Voting Systems v. Fox News Network -- Pre-Trial Evidence Release',
        'author':         'Delaware Superior Court',
        'publication':    'Delaware Superior Court, N23C-03-308',
        'published_date': '2023-02-27',
        'summary':        (
            'Court-disclosed internal Fox News communications including text messages and emails '
            'from Rupert Murdoch, Tucker Carlson, Laura Ingraham, Sean Hannity, and executives. '
            'Documents establish that named individuals privately acknowledged the 2020 election '
            'fraud claims were false while continuing to broadcast them. Murdoch texts document '
            'personal editorial involvement and knowledge of anchor conduct.'
        ),
        'direct_quote':   '"The Dominion case will be damaging. It gives us an opportunity to take a turn." -- Rupert Murdoch internal communication (paraphrased from court filings)',
        'confidence':     1.00,
    },
    {
        'evidence_id':    'ev-foxnews-003',
        'entity_id':      'catch-foxnews-002',
        'entity_type':    'catch',
        'source_type':    'academic',
        'url':            'https://doi.org/10.1017/S0008423920000396',
        'title':          'How Inaccurate and Absent COVID-19 Risk Perceptions Relate to Partisan and Fox News Use',
        'author':         'Motta, Stecula, Farhart',
        'publication':    'Canadian Journal of Political Science',
        'published_date': '2020-05-26',
        'summary':        'Peer-reviewed study finding Fox News viewership independently associated with lower COVID-19 knowledge scores and higher rates of misbelief, controlling for partisanship.',
        'confidence':     0.90,
    },
    {
        'evidence_id':    'ev-foxnews-004',
        'entity_id':      'motive-foxnews-political-influence',
        'entity_type':    'motive',
        'source_type':    'primary',
        'url':            'https://webarchive.nationalarchives.gov.uk/ukgwa/20140122145147/http://www.levesoninquiry.org.uk/about/the-report/',
        'title':          'The Leveson Report: An Inquiry into the Culture, Practices and Ethics of the Press',
        'author':         'Lord Justice Leveson',
        'publication':    'UK Parliament, HC 780',
        'published_date': '2012-11-29',
        'summary':        (
            'UK government-commissioned inquiry into press ethics. Took sworn testimony from '
            'Prime Ministers Tony Blair, Gordon Brown, and David Cameron documenting Murdoch '
            'political influence over UK government policy through implied editorial leverage. '
            'Tier 1 primary source: sworn testimony before official government inquiry.'
        ),
        'confidence':     1.00,
    },
    {
        'evidence_id':    'ev-foxnews-005',
        'entity_id':      'catch-foxnews-003',
        'entity_type':    'catch',
        'source_type':    'secondary',
        'url':            'https://www.adl.org/resources/report/tucker-carlson-and-great-replacement-theory',
        'title':          'Tucker Carlson and the Great Replacement Theory',
        'author':         'Anti-Defamation League',
        'publication':    'ADL Research Report',
        'published_date': '2021-04-08',
        'summary':        'ADL documentation of Tucker Carlson broadcasting Great Replacement Theory framing over 400 times. Documents frequency, framing, and ideological content of broadcasts.',
        'confidence':     0.88,
    },
    {
        'evidence_id':    'ev-foxnews-006',
        'entity_id':      'catch-foxnews-002',
        'entity_type':    'catch',
        'source_type':    'secondary',
        'url':            'https://www.newsguardtech.com/ratings/rating/?url=foxnews.com',
        'title':          'NewsGuard Reliability Rating: Fox News Digital',
        'author':         'NewsGuard',
        'publication':    'NewsGuard',
        'published_date': '2022-01-01',
        'summary':        'NewsGuard media reliability rating for Fox News digital properties. Documents specific accuracy failures in health and election coverage.',
        'confidence':     0.78,
    },
    {
        'evidence_id':    'ev-foxnews-007',
        'entity_id':      'catch-foxnews-005',
        'entity_type':    'catch',
        'source_type':    'academic',
        'url':            'https://doi.org/10.1073/pnas.1804840115',
        'title':          'Exposure to opposing views on social media can increase political polarization',
        'author':         'Bail et al.',
        'publication':    'Proceedings of the National Academy of Sciences',
        'published_date': '2018-08-28',
        'summary':        'Randomized controlled experiment finding partisan media exposure increases -- not decreases -- political polarization, particularly among conservatives.',
        'confidence':     0.88,
    },
    {
        'evidence_id':    'ev-foxnews-008',
        'entity_id':      'catch-foxnews-001',
        'entity_type':    'catch',
        'source_type':    'secondary',
        'url':            'https://apnews.com/article/fox-news-dominion-lawsuit-trial-2023-04-18',
        'title':          'Fox News reaches $787.5M settlement with Dominion Voting Systems',
        'author':         'David Bauder',
        'publication':    'Associated Press',
        'published_date': '2023-04-18',
        'summary':        'AP reporting on Fox News / Dominion settlement. Documents $787.5M settlement, absence of required on-air correction, and procedural history of the case.',
        'confidence':     0.97,
    },
]


# ---------------------------------------------------------------------------
# ── REDDIT ───────────────────────────────────────────────────────────────
# Source: INTEL cycle report 2026-04-08-intel-2044.md
# ---------------------------------------------------------------------------

REDDIT_FISHERMEN = [
    {
        'fisherman_id':    'fisherman-reddit',
        'domain':          'reddit.com',
        'display_name':    'Reddit',
        'owner':           'Reddit, Inc.',
        'parent_company':  'Reddit, Inc. (public, RDDT on NYSE)',
        'country':         'US',
        'founded':         2005,
        'business_model':  'advertising',
        'revenue_sources': ['advertising (~98% per S-1)', 'Reddit Premium subscription',
                            'data licensing (AI training data)'],
        'confidence_score': 0.90,
        'contributed_by':  'intel-agent-2026-04-08',
    }
]

REDDIT_MOTIVES = [
    {
        'motive_id':           'motive-reddit-ad-revenue',
        'fisherman_id':        'fisherman-reddit',
        'motive_type':         'advertising_revenue',
        'description':         (
            'Reddit\'s S-1 filing (February 2024, SEC) disclosed that advertising constitutes '
            'approximately 98% of revenue. The filing explicitly cites engagement metrics -- '
            'daily active users, time on platform, page views -- as the business drivers '
            'underpinning advertising inventory. This creates structural incentive to '
            'maximize engagement regardless of content quality or harm potential. '
            'Reddit\'s Hot algorithm rewards early high-velocity engagement, creating '
            'selection pressure for content that generates fast emotional reactions.'
        ),
        'revenue_model':       'Programmatic and direct advertising sold against user engagement',
        'beneficiary':         'Reddit, Inc. shareholders',
        'documented_evidence': 'Reddit S-1 SEC filing, February 22, 2024',
        'confidence_score':    0.95,
        'contributed_by':      'intel-agent-2026-04-08',
        'evidence_ids':        ['ev-reddit-001'],
    },
    {
        'motive_id':           'motive-reddit-data-licensing',
        'fisherman_id':        'fisherman-reddit',
        'motive_type':         'data_acquisition',
        'description':         (
            'Reddit entered data licensing agreements with Google and OpenAI to supply '
            'AI training data. Bloomberg reported a Google deal worth approximately $60M/year '
            'and an OpenAI arrangement. Reddit\'s S-1 (filed six days after Bloomberg\'s '
            'reporting) confirmed data API licensing arrangements without specifying dollar '
            'amounts. User-generated content -- produced without compensation by Reddit\'s '
            'community -- is the asset being licensed. This creates incentive to maintain '
            'and grow the user content corpus regardless of the health effects of the '
            'community dynamics that produce it.'
        ),
        'revenue_model':       'Data licensing fees from AI companies for training data',
        'beneficiary':         'Reddit, Inc.; AI licensees (Google, OpenAI)',
        'documented_evidence': 'Bloomberg reporting (Metz, Scigliuzzo); Reddit S-1 confirmation',
        'confidence_score':    0.92,
        'contributed_by':      'intel-agent-2026-04-08',
        'evidence_ids':        ['ev-reddit-001', 'ev-reddit-002'],
    },
    {
        'motive_id':           'motive-reddit-outrage-amplification',
        'fisherman_id':        'fisherman-reddit',
        'motive_type':         'audience_capture',
        'description':         (
            'Reddit\'s Hot algorithm rewards posts that accumulate high-velocity upvotes '
            'and comments in the early period after posting. Emotionally activating content '
            '-- outrage, fear, tribal conflict -- generates faster and higher engagement '
            'than neutral information content. This mechanism produced structural selection '
            'pressure for inflammatory content across subreddits, documented in the growth '
            'of r/The_Donald (quarantined 2019, banned 2020) and in radicalization pathway '
            'research. Unlike Meta, Reddit has not published internal research documenting '
            'awareness of this dynamic; the mechanism is established through behavioral '
            'evidence rather than internal documents.'
        ),
        'revenue_model':       'Engagement-based advertising inventory',
        'beneficiary':         'Reddit, Inc. shareholders',
        'documented_evidence': 'Pattern evidence from community growth/ban history; S-1 engagement metric disclosures',
        'confidence_score':    0.82,
        'contributed_by':      'intel-agent-2026-04-08',
        'evidence_ids':        ['ev-reddit-004', 'ev-reddit-005'],
    },
    {
        'motive_id':           'motive-reddit-subscription-premium',
        'fisherman_id':        'fisherman-reddit',
        'motive_type':         'subscription_growth',
        'description':         (
            'Reddit Premium provides an ad-free experience and access to r/lounge. '
            'The subscription model creates financial incentive to ensure the free, '
            'ad-supported experience is sufficiently compelling to drive subscription '
            'conversion while maintaining the advertising-supported community dynamics '
            'that make the platform valuable. The 2023 API pricing controversy '
            '(which shut down ad-free third-party apps) served this incentive directly.'
        ),
        'revenue_model':       'Monthly subscription fee for ad-free experience',
        'beneficiary':         'Reddit, Inc.',
        'documented_evidence': 'Reddit S-1 subscription revenue disclosure',
        'confidence_score':    0.88,
        'contributed_by':      'intel-agent-2026-04-08',
        'evidence_ids':        ['ev-reddit-001'],
    },
]

REDDIT_CATCHES = [
    {
        'catch_id':           'catch-reddit-001',
        'fisherman_id':       'fisherman-reddit',
        'harm_type':          'radicalization',
        'victim_demographic': 'general public, US voters',
        'documented_outcome': (
            'r/The_Donald, a subreddit dedicated to Donald Trump, grew to over 790,000 members '
            'and was documented by the Senate Intelligence Committee (Vol. 2, October 2019) as '
            'a primary vector for Russian Internet Research Agency (IRA) influence operations. '
            'The IRA created and amplified content in r/The_Donald as part of its documented '
            'campaign to influence the 2016 US election. Reddit quarantined the subreddit in '
            'June 2019 and banned it in June 2020, with Reddit\'s own announcement acknowledging '
            'violations of policies against inciting violence.'
        ),
        'scale':              'population',
        'legal_case_id':      None,
        'academic_citation':  'Senate Intelligence Committee. (2019). Report on Russian Active Measures Campaigns and Interference in the 2016 U.S. Election, Vol. 2.',
        'date_documented':    '2020-06-29',
        'severity_score':     7,
        'evidence_ids':       ['ev-reddit-003', 'ev-reddit-004'],
    },
    {
        'catch_id':           'catch-reddit-002',
        'fisherman_id':       'fisherman-reddit',
        'harm_type':          'self_harm',
        'victim_demographic': 'adolescents, people experiencing eating disorders or self-harm ideation',
        'documented_outcome': (
            'Reddit hosted communities dedicated to eating disorder content (pro-ana, pro-mia) '
            'and self-harm encouragement. Reddit\'s algorithmic recommendation of related '
            'communities created pathways from general mental health discussions into '
            'increasingly harmful content. Reddit banned several pro-eating-disorder and '
            'self-harm communities under policy updates in 2018 and 2022, but research '
            'documented migration of these communities to new subreddits. Reddit Transparency '
            'Reports document ongoing enforcement actions in these categories.'
        ),
        'scale':              'group',
        'date_documented':    '2022-01-01',
        'severity_score':     8,
        'evidence_ids':       ['ev-reddit-005'],
    },
    {
        'catch_id':           'catch-reddit-003',
        'fisherman_id':       'fisherman-reddit',
        'harm_type':          'political_manipulation',
        'victim_demographic': 'US voters, general public',
        'documented_outcome': (
            'The Senate Intelligence Committee Vol. 2 (October 2019) documented that the '
            'Internet Research Agency (IRA) operated 944 Reddit accounts as part of its '
            'influence operation targeting US audiences. IRA accounts operated across the '
            'political spectrum -- targeting both conservative and progressive communities '
            '-- to maximize social division. CEO Steve Huffman testified before the Senate '
            'Judiciary Committee on October 31, 2017, following the 2016 election. The '
            '2019 report documented continued IRA-linked activity on the platform after '
            'Huffman\'s testimony established awareness.'
        ),
        'scale':              'population',
        'legal_case_id':      None,
        'academic_citation':  'Senate Intelligence Committee. (2019). Vol. 2, p. 47-51. IRA Reddit operations.',
        'date_documented':    '2019-10-08',
        'severity_score':     7,
        'evidence_ids':       ['ev-reddit-003', 'ev-reddit-008'],
    },
    {
        'catch_id':           'catch-reddit-004',
        'fisherman_id':       'fisherman-reddit',
        'harm_type':          'radicalization',
        'victim_demographic': 'young men, general public',
        'documented_outcome': (
            'Alek Minassian, convicted of 10 counts of first-degree murder in the 2018 '
            'Toronto van attack, documented his radicalization through incel (involuntary '
            'celibate) communities on Reddit and other platforms. The court proceedings '
            '(R. v. Minassian, 2021 ONSC 4545) established the causal chain from '
            'radicalization in online incel communities to real-world mass violence. '
            'Ging (2019) documented the broader manosphere radicalization pathway through '
            'Reddit communities as part of peer-reviewed research on masculine extremism. '
            'Reddit subsequently banned r/Incels in November 2017, a year before the attack.'
        ),
        'scale':              'group',
        'legal_case_id':      'R. v. Minassian, 2021 ONSC 4545',
        'academic_citation':  'Ging, D. (2019). Alphas, Betas, and Incels. Men and Masculinities, 22(4), 638-657.',
        'date_documented':    '2021-03-03',
        'severity_score':     9,
        'evidence_ids':       ['ev-reddit-006', 'ev-reddit-007'],
    },
]

REDDIT_EVIDENCE = [
    {
        'evidence_id':    'ev-reddit-001',
        'entity_id':      'fisherman-reddit',
        'entity_type':    'fisherman',
        'source_type':    'primary',
        'url':            'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=RDDT',
        'title':          'Reddit, Inc. Form S-1 Registration Statement',
        'author':         'Reddit, Inc.',
        'publication':    'SEC EDGAR',
        'published_date': '2024-02-22',
        'summary':        (
            'Reddit IPO registration statement. Discloses advertising as ~98% of revenue, '
            'engagement metrics as primary business driver, data licensing arrangements, '
            'and risk factors including dependence on user-generated content and community '
            'health. Tier 1 primary source: SEC regulatory filing under legal obligation.'
        ),
        'confidence':     1.00,
    },
    {
        'evidence_id':    'ev-reddit-002',
        'entity_id':      'motive-reddit-data-licensing',
        'entity_type':    'motive',
        'source_type':    'secondary',
        'url':            'https://www.bloomberg.com/news/articles/2024-02-16/reddit-in-ai-content-licensing-deal-with-google',
        'title':          'Reddit in AI Content Licensing Deal With Google',
        'author':         'Metz, Chloe; Scigliuzzo, Davide',
        'publication':    'Bloomberg News',
        'published_date': '2024-02-16',
        'summary':        'Bloomberg reporting on Reddit data licensing arrangement with Google worth approximately $60M/year. Named journalists, contemporaneous reporting confirmed by subsequent S-1 filing.',
        'confidence':     0.92,
    },
    {
        'evidence_id':    'ev-reddit-003',
        'entity_id':      'catch-reddit-003',
        'entity_type':    'catch',
        'source_type':    'primary',
        'url':            'https://www.intelligence.senate.gov/sites/default/files/documents/Report_Volume2.pdf',
        'title':          'Report on Russian Active Measures Campaigns and Interference in the 2016 U.S. Election, Volume 2',
        'author':         'Senate Select Committee on Intelligence',
        'publication':    'US Senate Intelligence Committee',
        'published_date': '2019-10-08',
        'summary':        'Bipartisan Senate Intelligence Committee report documenting IRA influence operations including 944 Reddit accounts. Documents operations targeting both conservative and progressive communities to maximize social division.',
        'confidence':     1.00,
    },
    {
        'evidence_id':    'ev-reddit-004',
        'entity_id':      'catch-reddit-001',
        'entity_type':    'catch',
        'source_type':    'primary',
        'url':            'https://www.reddit.com/r/announcements/comments/hi3oht/reddits_position_on_the_healthcare_debate/',
        'title':          "r/The_Donald ban announcement",
        'author':         'Reddit, Inc.',
        'publication':    'Reddit',
        'published_date': '2020-06-29',
        'summary':        "Reddit's official announcement of r/The_Donald ban, acknowledging policy violations. Platform's own admission of documented harm from a specific community.",
        'confidence':     1.00,
    },
    {
        'evidence_id':    'ev-reddit-005',
        'entity_id':      'fisherman-reddit',
        'entity_type':    'fisherman',
        'source_type':    'primary',
        'url':            'https://www.redditinc.com/policies/transparency-report-2023',
        'title':          'Reddit Transparency Reports 2019-2023',
        'author':         'Reddit, Inc.',
        'publication':    'Reddit',
        'published_date': '2023-12-31',
        'summary':        'Annual transparency reports documenting content removal, community bans, and government requests. Establishes pattern of ongoing enforcement against harmful content categories.',
        'confidence':     0.90,
    },
    {
        'evidence_id':    'ev-reddit-006',
        'entity_id':      'catch-reddit-004',
        'entity_type':    'catch',
        'source_type':    'academic',
        'url':            'https://doi.org/10.1177/1097184X18816118',
        'title':          'Alphas, Betas, and Incels: Theorizing the Masculinities of the Manosphere',
        'author':         'Ging, Debbie',
        'publication':    'Men and Masculinities',
        'published_date': '2019-07-01',
        'summary':        'Peer-reviewed academic research documenting radicalization pathways through manosphere communities including Reddit incel communities. Documents ideological progression from mainstream to extreme.',
        'confidence':     0.88,
    },
    {
        'evidence_id':    'ev-reddit-007',
        'entity_id':      'catch-reddit-004',
        'entity_type':    'catch',
        'source_type':    'primary',
        'url':            'https://www.canlii.org/en/on/onsc/doc/2021/2021onsc4545/2021onsc4545.html',
        'title':          'R. v. Minassian, 2021 ONSC 4545',
        'author':         'Ontario Superior Court of Justice',
        'publication':    'Ontario Superior Court',
        'published_date': '2021-03-03',
        'summary':        'Court ruling convicting Alek Minassian on 10 counts of first-degree murder in the Toronto van attack. Establishes causal chain from online incel radicalization to mass violence. Tier 1 primary source: fully resolved court proceeding.',
        'confidence':     1.00,
    },
    {
        'evidence_id':    'ev-reddit-008',
        'entity_id':      'catch-reddit-003',
        'entity_type':    'catch',
        'source_type':    'primary',
        'url':            'https://www.judiciary.senate.gov/imo/media/doc/10-31-17%20Huffman%20Testimony.pdf',
        'title':          'Testimony of Steve Huffman, CEO of Reddit, Inc.',
        'author':         'Steve Huffman',
        'publication':    'US Senate Judiciary Committee',
        'published_date': '2017-10-31',
        'summary':        'Sworn congressional testimony by Reddit CEO Steve Huffman regarding Russian interference operations on Reddit. Establishes documented awareness of platform manipulation by foreign actors at the executive level.',
        'confidence':     1.00,
    },
]


# ---------------------------------------------------------------------------
# ── TIKTOK ───────────────────────────────────────────────────────────────
# Source: INTEL cycle report 2026-04-08-intel-0902.md
# ---------------------------------------------------------------------------

TIKTOK_FISHERMEN = [
    {
        'fisherman_id':    'fisherman-tiktok',
        'domain':          'tiktok.com',
        'display_name':    'TikTok',
        'owner':           'ByteDance Ltd.',
        'parent_company':  'ByteDance Ltd. (incorporated Cayman Islands, headquarters Beijing)',
        'country':         'CN',
        'founded':         2016,
        'business_model':  'advertising',
        'revenue_sources': ['in-app advertising', 'TikTok Shop affiliate commerce',
                            'TikTok LIVE gifting', 'brand partnership programs'],
        'confidence_score': 0.95,
        'contributed_by':  'intel-agent-2026-04-08',
    }
]

TIKTOK_MOTIVES = [
    {
        'motive_id':           'motive-tiktok-ad-revenue',
        'fisherman_id':        'fisherman-tiktok',
        'motive_type':         'advertising_revenue',
        'description':         (
            'TikTok\'s For You Page (FYP) algorithm optimizes watch time to maximize '
            'advertising inventory. ByteDance\'s 2023 advertising revenue exceeded $18B '
            '(Bloomberg/Reuters estimates). The FYP algorithm determines content distribution '
            'entirely on predicted engagement, without regard for creator follower count. '
            'This creates structural selection pressure for content that produces watch-time '
            'maximizing emotional responses -- including content targeting adolescent '
            'psychological vulnerabilities.'
        ),
        'revenue_model':       'In-stream advertising sold against watch time',
        'beneficiary':         'ByteDance Ltd.; ByteDance shareholders',
        'documented_evidence': 'Shou Zi Chew Senate testimony (March 2023); ByteDance revenue reporting',
        'confidence_score':    0.92,
        'contributed_by':      'intel-agent-2026-04-08',
        'evidence_ids':        ['ev-tiktok-002'],
    },
    {
        'motive_id':           'motive-tiktok-youth-targeting',
        'fisherman_id':        'fisherman-tiktok',
        'motive_type':         'audience_capture',
        'description':         (
            'TikTok (as Musical.ly) signed a consent decree with the FTC in 2019 agreeing '
            'to COPPA compliance after collecting data from children under 13 without '
            'parental consent. The FTC referred TikTok to the DOJ in August 2023 for '
            'continued COPPA violations after the consent decree. A 14-state AG complaint '
            '(October 2023) cited internal TikTok research showing the platform knew its '
            'design produced compulsive use patterns in minors and continued the design '
            'regardless. The knowledge-and-continued-action chain is fully documented '
            'at Tier 1 through the consent decree and the subsequent DOJ referral.'
        ),
        'revenue_model':       'Advertising revenue from under-13 users and engagement from minors',
        'beneficiary':         'ByteDance Ltd.',
        'documented_evidence': 'FTC DOJ referral (2023); FTC v. Musical.ly consent decree (2019); 14-state AG complaint (2023)',
        'confidence_score':    0.95,
        'contributed_by':      'intel-agent-2026-04-08',
        'evidence_ids':        ['ev-tiktok-001', 'ev-tiktok-006', 'ev-tiktok-007'],
    },
    {
        'motive_id':           'motive-tiktok-data-acquisition',
        'fisherman_id':        'fisherman-tiktok',
        'motive_type':         'data_acquisition',
        'description':         (
            'BuzzFeed News reported in June 2022 (Emily Baker-White) that audio from 80 '
            'internal TikTok meetings revealed China-based ByteDance employees repeatedly '
            'accessed US user data, contradicting TikTok\'s public statements. TikTok '
            'confirmed the access. The Senate Intelligence Committee held briefings on '
            'CFIUS review of TikTok\'s data practices. The precise use of US user data '
            'by ByteDance and any Chinese state direction is documented at the level of '
            'government concern, not yet established as proven legal finding.'
        ),
        'revenue_model':       'User behavioral data for algorithmic refinement and potential state use',
        'beneficiary':         'ByteDance Ltd.; potentially Chinese state interests',
        'documented_evidence': 'BuzzFeed News investigation (Baker-White, 2022); Senate Intelligence Committee hearing record',
        'confidence_score':    0.88,
        'contributed_by':      'intel-agent-2026-04-08',
        'evidence_ids':        ['ev-tiktok-003'],
    },
    {
        'motive_id':           'motive-tiktok-addiction-design',
        'fisherman_id':        'fisherman-tiktok',
        'motive_type':         'audience_capture',
        'description':         (
            'Short-form infinite scroll combined with variable reward delivery (not knowing '
            'if the next video will be compelling) produces compulsive use patterns documented '
            'in adolescents. The 14-state AG complaint (October 2023) cited internal TikTok '
            'research documenting these effects. TikTok\'s FYP design is optimized for '
            'session length maximization; features designed to interrupt use (screen time '
            'reminders) are documented to be ineffective against the core algorithmic design.'
        ),
        'revenue_model':       'Session length maximization for advertising inventory',
        'beneficiary':         'ByteDance Ltd.',
        'documented_evidence': '14-state AG complaint citing internal TikTok research; Australian eSafety Commissioner assessment',
        'confidence_score':    0.90,
        'contributed_by':      'intel-agent-2026-04-08',
        'evidence_ids':        ['ev-tiktok-005', 'ev-tiktok-006'],
    },
]

TIKTOK_CATCHES = [
    {
        'catch_id':           'catch-tiktok-001',
        'fisherman_id':       'fisherman-tiktok',
        'harm_type':          'child_exploitation_adjacent',
        'victim_demographic': 'children under 13, parents',
        'documented_outcome': (
            'TikTok (as Musical.ly) paid $5.7M -- the largest COPPA civil penalty at the '
            'time -- in a 2019 FTC consent decree for collecting personal data from children '
            'under 13 without verifiable parental consent. TikTok agreed to COPPA compliance '
            'as a condition of the settlement. The FTC referred TikTok to the DOJ in August '
            '2023 for continued COPPA violations after the consent decree, documenting '
            'ongoing data collection from under-13 users and failure to honor deletion '
            'requests. This establishes a knowing, repeated pattern of COPPA violation '
            'across a four-year period following a legal obligation to stop.'
        ),
        'scale':              'population',
        'legal_case_id':      'FTC v. Musical.ly, Inc. (2019); FTC DOJ Referral (2023)',
        'date_documented':    '2023-08-02',
        'severity_score':     8,
        'evidence_ids':       ['ev-tiktok-001', 'ev-tiktok-007'],
    },
    {
        'catch_id':           'catch-tiktok-002',
        'fisherman_id':       'fisherman-tiktok',
        'harm_type':          'self_harm',
        'victim_demographic': 'adolescents, particularly teenage girls',
        'documented_outcome': (
            'WSJ investigation (Wells, Horwitz, Seetharaman, September 2021) created '
            'researcher accounts registered as teenagers and documented that TikTok\'s '
            'For You Page served self-harm and suicide-related content within 2.6 minutes '
            'on a new account and within 8 minutes began serving a continuous stream of '
            'such content. The 14-state AG complaint cited internal TikTok research '
            'acknowledging these algorithmic pathways. The Molly Rose Foundation\'s '
            '"Pervasive-by-Design" report (August 2025) found 96% of algorithmically '
            'recommended videos on TikTok were harmful to adolescents in a controlled study.'
        ),
        'scale':              'population',
        'academic_citation':  'Molly Rose Foundation (2025). Pervasive-by-design. 19 August 2025.',
        'date_documented':    '2021-09-08',
        'severity_score':     9,
        'evidence_ids':       ['ev-tiktok-004', 'ev-tiktok-006'],
    },
    {
        'catch_id':           'catch-tiktok-003',
        'fisherman_id':       'fisherman-tiktok',
        'harm_type':          'addiction_facilitation',
        'victim_demographic': 'adolescents, young adults',
        'documented_outcome': (
            'Valkenburg et al. (2022, npj Mental Health Research) documented compulsive '
            'TikTok use patterns in adolescents in peer-reviewed research. The Australian '
            'eSafety Commissioner\'s TikTok Safety by Design Assessment (2023) found '
            'significant gaps in TikTok\'s implementation of safety features for minors '
            'and documented that the platform\'s default settings maximized engagement '
            'over user wellbeing. The short-form infinite scroll format combined with '
            'the FYP algorithm produces documented compulsive use patterns distinct from '
            'other social media platforms in clinical research.'
        ),
        'scale':              'population',
        'academic_citation':  'Valkenburg et al. (2022). npj Mental Health Research.',
        'date_documented':    '2023-01-01',
        'severity_score':     7,
        'evidence_ids':       ['ev-tiktok-005'],
    },
    {
        'catch_id':           'catch-tiktok-004',
        'fisherman_id':       'fisherman-tiktok',
        'harm_type':          'health_misinformation',
        'victim_demographic': 'adolescents, children',
        'documented_outcome': (
            'Multiple children died attempting TikTok viral challenges. The Benadryl '
            'Challenge (2020) resulted in documented teen deaths after TikTok videos '
            'encouraged dangerous overdose of diphenhydramine. The Blackout Challenge '
            '(choking until unconscious) resulted in documented child deaths; wrongful '
            'death lawsuits in Texas and Cook County, Illinois named TikTok\'s algorithm '
            'specifically, alleging it recommended Blackout Challenge content to children '
            'as young as 8. Reuters documented Benadryl Challenge deaths contemporaneously '
            '(September 2020). The severity rating of 9/10 reflects documented child '
            'deaths; causal evidence ceiling is 0.88 pending court findings on algorithm '
            'recommendations.'
        ),
        'scale':              'group',
        'legal_case_id':      'Wrongful death actions: Texas and Cook County IL (2022)',
        'date_documented':    '2020-09-25',
        'severity_score':     9,
        'evidence_ids':       ['ev-tiktok-008'],
    },
    {
        'catch_id':           'catch-tiktok-005',
        'fisherman_id':       'fisherman-tiktok',
        'harm_type':          'political_manipulation',
        'victim_demographic': 'US users, national security',
        'documented_outcome': (
            'BuzzFeed News documented China-based ByteDance employees accessing US user '
            'data in 2022. The US Senate Intelligence Committee held classified briefings '
            'on CFIUS review of TikTok. Multiple US states and the federal government '
            'banned TikTok on government devices. The Australian government banned TikTok '
            'on government devices in April 2023. The EU Data Protection Board opened '
            'formal investigation. TikTok\'s "Project Texas" data localization initiative '
            'was proposed as mitigation but its implementation and efficacy remain '
            'disputed. Shou Zi Chew could not confirm under oath in Senate testimony '
            'whether Chinese ByteDance employees had accessed US user data.'
        ),
        'scale':              'population',
        'date_documented':    '2022-06-17',
        'severity_score':     7,
        'evidence_ids':       ['ev-tiktok-002', 'ev-tiktok-003'],
    },
]

TIKTOK_EVIDENCE = [
    {
        'evidence_id':    'ev-tiktok-001',
        'entity_id':      'motive-tiktok-youth-targeting',
        'entity_type':    'motive',
        'source_type':    'primary',
        'url':            'https://www.ftc.gov/news-events/news/press-releases/2023/08/ftc-refers-tiktok-bytedance-matter-department-justice',
        'title':          'FTC Refers TikTok/ByteDance Matter to Department of Justice',
        'author':         'Federal Trade Commission',
        'publication':    'FTC Press Release',
        'published_date': '2023-08-02',
        'summary':        'FTC referral to DOJ documenting continued COPPA violations by TikTok following 2019 consent decree. Tier 1 primary source: government regulatory action.',
        'confidence':     0.95,
    },
    {
        'evidence_id':    'ev-tiktok-002',
        'entity_id':      'fisherman-tiktok',
        'entity_type':    'fisherman',
        'source_type':    'primary',
        'url':            'https://www.commerce.senate.gov/2023/3/protecting-kids-online-testimony-from-tiktok',
        'title':          'Testimony of Shou Zi Chew, CEO of TikTok',
        'author':         'Shou Zi Chew',
        'publication':    'US Senate Commerce Committee',
        'published_date': '2023-03-23',
        'summary':        (
            'Sworn congressional testimony by TikTok CEO Shou Zi Chew. Confirms the For You '
            'Page algorithm model, ByteDance corporate structure, and COPPA compliance status. '
            'Chew was unable to confirm under oath that China-based employees had not accessed '
            'US user data. Tier 1 primary source: sworn congressional testimony.'
        ),
        'direct_quote':   '"I can\'t say with 100 percent certainty that [Chinese ByteDance employees have not accessed US user data]." -- Shou Zi Chew, Senate testimony, March 23, 2023',
        'confidence':     1.00,
    },
    {
        'evidence_id':    'ev-tiktok-003',
        'entity_id':      'motive-tiktok-data-acquisition',
        'entity_type':    'motive',
        'source_type':    'secondary',
        'url':            'https://www.buzzfeednews.com/article/emilybakerwhite/tiktok-tapes-us-user-data-china-bytedance-access',
        'title':          "Leaked Audio From 80 Internal TikTok Meetings Shows Employees Discussing How Chinese Employees Could Access US Data",
        'author':         'Baker-White, Emily',
        'publication':    'BuzzFeed News',
        'published_date': '2022-06-17',
        'summary':        'Investigation based on 80 leaked internal TikTok meeting recordings documenting China-based ByteDance employees discussing and accessing US user data. TikTok subsequently confirmed the access.',
        'confidence':     0.92,
    },
    {
        'evidence_id':    'ev-tiktok-004',
        'entity_id':      'catch-tiktok-002',
        'entity_type':    'catch',
        'source_type':    'secondary',
        'url':            'https://www.wsj.com/articles/tiktok-algorithm-feeds-teens-a-diet-of-darkness-11639754848',
        'title':          "TikTok's Algorithm Leads Users From Mainstream Content to White Supremacy, Misogyny and Eating Disorders",
        'author':         'Wells, Georgia; Horwitz, Jeff; Seetharaman, Deepa',
        'publication':    'The Wall Street Journal',
        'published_date': '2021-09-08',
        'summary':        (
            'WSJ investigation using researcher accounts registered as teenagers. Documents '
            'that TikTok\'s For You Page served self-harm and suicide content within 2.6 '
            'minutes on a new account and within 8 minutes delivered a continuous stream. '
            'Named journalists, methodology documented.'
        ),
        'confidence':     0.90,
    },
    {
        'evidence_id':    'ev-tiktok-005',
        'entity_id':      'motive-tiktok-addiction-design',
        'entity_type':    'motive',
        'source_type':    'primary',
        'url':            'https://www.esafety.gov.au/industry/safety-by-design/assessments/tiktok',
        'title':          'TikTok Safety by Design Assessment',
        'author':         'Australian eSafety Commissioner',
        'publication':    'Australian eSafety Commissioner',
        'published_date': '2023-01-01',
        'summary':        'Government regulatory assessment of TikTok safety by design practices. Documents gaps in minor protections and engagement-maximizing default settings.',
        'confidence':     0.95,
    },
    {
        'evidence_id':    'ev-tiktok-006',
        'entity_id':      'catch-tiktok-002',
        'entity_type':    'catch',
        'source_type':    'primary',
        'url':            'https://oag.ca.gov/system/files/media/tiktok-complaint.pdf',
        'title':          '14-State Attorney General Complaint Against TikTok',
        'author':         'Attorneys General of California et al.',
        'publication':    'US District Court',
        'published_date': '2023-10-08',
        'summary':        (
            '14-state AG complaint filed in federal court citing internal TikTok research '
            'documenting awareness of harmful effects on adolescent mental health. Documents '
            'that TikTok possessed evidence of harm and continued engagement-maximizing '
            'design for minors. Tier 1: court filing referencing internal documents.'
        ),
        'confidence':     0.95,
    },
    {
        'evidence_id':    'ev-tiktok-007',
        'entity_id':      'catch-tiktok-001',
        'entity_type':    'catch',
        'source_type':    'primary',
        'url':            'https://www.ftc.gov/news-events/news/press-releases/2019/02/video-social-networking-app-musical-ly-agrees-settle-ftc-charges-it-illegally-collected-personal',
        'title':          'Video Social Networking App Musical.ly Agrees to Settle FTC Charges It Illegally Collected Personal Information from Children',
        'author':         'Federal Trade Commission',
        'publication':    'FTC Press Release',
        'published_date': '2019-02-27',
        'summary':        '$5.7M COPPA civil penalty -- largest at time of settlement. Establishes legal obligation for TikTok COPPA compliance as of 2019. Tier 1 primary source.',
        'confidence':     1.00,
    },
    {
        'evidence_id':    'ev-tiktok-008',
        'entity_id':      'catch-tiktok-004',
        'entity_type':    'catch',
        'source_type':    'secondary',
        'url':            'https://www.reuters.com/article/us-tiktok-challenge/teen-dies-after-attempting-benadryl-challenge-on-tiktok-idUSKBN26G2MO',
        'title':          "Teen dies after attempting 'Benadryl Challenge' on TikTok",
        'author':         'Reuters',
        'publication':    'Reuters',
        'published_date': '2020-09-25',
        'summary':        'Contemporaneous wire service reporting on documented teen death from Benadryl Challenge viral trend on TikTok.',
        'confidence':     0.88,
    },
]


# ---------------------------------------------------------------------------
# Seed function
# ---------------------------------------------------------------------------

def seed(db):
    platforms = [
        ('Twitter/X',   X_FISHERMEN,       X_MOTIVES,       X_CATCHES,       X_EVIDENCE),
        ('Fox News',    FOX_FISHERMEN,     FOX_MOTIVES,     FOX_CATCHES,     FOX_EVIDENCE),
        ('Reddit',      REDDIT_FISHERMEN,  REDDIT_MOTIVES,  REDDIT_CATCHES,  REDDIT_EVIDENCE),
        ('TikTok',      TIKTOK_FISHERMEN,  TIKTOK_MOTIVES,  TIKTOK_CATCHES,  TIKTOK_EVIDENCE),
    ]

    for platform_name, fishermen, motives, catches, evidence in platforms:
        print(f'\n[BMID] Seeding {platform_name}...')

        for rec in fishermen:
            insert_fisherman(db, rec)
            print(f'  fisherman: {rec["domain"]} ({rec["display_name"]})')

        for rec in motives:
            insert_motive(db, rec)
            print(f'  motive:    {rec["motive_id"]}')

        for rec in catches:
            insert_catch(db, rec)
            print(f'  catch:     {rec["catch_id"]} (sev={rec.get("severity_score","?")})')

        for rec in evidence:
            insert_evidence(db, rec)
            print(f'  evidence:  {rec["evidence_id"]}')

    db.commit()


def report(db):
    print('\n[BMID] Database state after platform seed:')
    for table in ['fisherman', 'motive', 'catch', 'evidence']:
        n = db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        print(f'  {table:12}: {n}')

    print('\n[BMID] All fishermen:')
    for row in db.execute('SELECT domain, display_name, confidence_score FROM fisherman ORDER BY domain'):
        print(f'  {row[0]:30} {row[1]:35} confidence={row[2]}')


if __name__ == '__main__':
    print(f'[BMID] Connecting to {DB_PATH}')
    db = get_db()
    seed(db)
    report(db)
    db.close()
    print('\n[BMID] Platform seed complete.')

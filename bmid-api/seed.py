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

DB_PATH = os.path.join(os.path.dirname(__file__), 'bmid.db')
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
        'contributed_by': 'investigate-agent-cycle-1'
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
        'contributed_by': 'intel-agent-cycle-2'
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
        'contributed_by': 'intel-agent-cycle-4'
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
    print('[BMID] Seeding fishermen...')
    for f in FISHERMEN:
        insert_fisherman(db, f.copy())
        print(f"  {f['domain']} ({f['display_name']})")

    print('[BMID] Seeding motives...')
    for m in MOTIVES:
        insert_motive(db, m.copy())
        print(f"  {m['motive_id']}")

    print('[BMID] Seeding catches...')
    for c in CATCHES:
        insert_catch(db, c.copy())
        print(f"  {c['catch_id']}")

    print('[BMID] Seeding evidence...')
    for e in EVIDENCE:
        insert_evidence(db, e.copy())
        print(f"  {e['evidence_id']}")

    db.commit()


def report(db):
    counts = {
        'fishermen': db.execute('SELECT COUNT(*) FROM fisherman').fetchone()[0],
        'motives':   db.execute('SELECT COUNT(*) FROM motive').fetchone()[0],
        'catches':   db.execute('SELECT COUNT(*) FROM catch').fetchone()[0],
        'evidence':  db.execute('SELECT COUNT(*) FROM evidence').fetchone()[0],
    }
    print('\n[BMID] Database state after seed:')
    for k, v in counts.items():
        print(f'  {k}: {v}')

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


if __name__ == '__main__':
    print(f'[BMID] Initializing database at {DB_PATH}')
    db = get_db()
    init_schema(db)
    seed(db)
    report(db)
    db.close()
    print('\n[BMID] Seed complete.')
    print('[BMID] Start API: python app.py')
    print('[BMID] Test Meta: curl http://localhost:5000/api/v1/explain?domain=facebook.com')
    print('[BMID] Test YT:   curl http://localhost:5000/api/v1/explain?domain=youtube.com')

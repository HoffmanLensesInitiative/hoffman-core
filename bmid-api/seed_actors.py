"""
seed_actors.py
BMID actor records for key platform executives.
Run: python seed_actors.py

Covers:
  - Rupert Murdoch (Fox Corp / Fox News)
  - Lachlan Murdoch (Fox Corp / Fox News)
  - Steve Huffman (Reddit)
  - Shou Zi Chew (TikTok / ByteDance)
  - Mark Zuckerberg (Meta) — foundational record
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "bmid.db")

# Fisherman rowids (verified against live DB 2026-04-09)
FISHERMAN = {
    "meta_facebook":   1,
    "meta_instagram":  2,
    "youtube":         3,
    "x_corp":          4,
    "foxnews":         5,
    "reddit":          6,
    "tiktok":          7,
}


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def insert_actor(conn, name, aliases, current_role, current_fisherman_id,
                 documented_knowledge, knowledge_source, knowledge_date,
                 notes, confidence=0.9):
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO actor
          (name, name_aliases, current_role, current_fisherman_id,
           documented_knowledge_of_harm, knowledge_source, knowledge_date,
           notes, confidence)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (name, aliases, current_role, current_fisherman_id,
          documented_knowledge, knowledge_source, knowledge_date,
          notes, confidence))
    conn.commit()
    cur.execute("SELECT rowid FROM actor WHERE name=?", (name,))
    row = cur.fetchone()
    return row[0] if row else None


def insert_actor_role(conn, actor_id, fisherman_id, role, date_start, date_end,
                      evidence, source_url=None, notes=None):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO actor_role
          (actor_id, fisherman_id, role, date_start, date_end,
           evidence, source_url, notes)
        VALUES (?,?,?,?,?,?,?,?)
    """, (actor_id, fisherman_id, role, date_start, date_end,
          evidence, source_url, notes))
    conn.commit()


def insert_actor_investment(conn, actor_id, fisherman_id, position_type,
                            stake_description, date_start, date_end,
                            evidence, source_url=None, notes=None):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO actor_investment
          (actor_id, fisherman_id, position_type, stake_description,
           date_start, date_end, evidence, source_url, notes)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (actor_id, fisherman_id, position_type, stake_description,
          date_start, date_end, evidence, source_url, notes))
    conn.commit()


def insert_actor_knowledge(conn, actor_id, fisherman_id, knowledge_type,
                           description, date, action_taken, evidence,
                           source_url=None, confidence=0.9, notes=None):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO actor_knowledge
          (actor_id, fisherman_id, knowledge_type, description, date,
           action_taken, evidence, source_url, confidence, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (actor_id, fisherman_id, knowledge_type, description, date,
          action_taken, evidence, source_url, confidence, notes))
    conn.commit()


def insert_actor_political(conn, actor_id, relationship_type, recipient,
                           amount, date, jurisdiction, evidence,
                           source_url=None, notes=None):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO actor_political
          (actor_id, relationship_type, recipient, amount, date,
           jurisdiction, evidence, source_url, notes)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (actor_id, relationship_type, recipient, amount, date,
          jurisdiction, evidence, source_url, notes))
    conn.commit()


def seed():
    conn = get_conn()

    # -------------------------------------------------------------------------
    # RUPERT MURDOCH
    # Chairman Emeritus, Fox Corporation / News Corp
    # -------------------------------------------------------------------------
    rupert_id = insert_actor(
        conn,
        name="Rupert Murdoch",
        aliases="Keith Rupert Murdoch",
        current_role="Chairman Emeritus, Fox Corporation; Chairman Emeritus, News Corp",
        current_fisherman_id=FISHERMAN["foxnews"],
        documented_knowledge=1,
        knowledge_source="Internal editorial direction; regulatory proceedings; "
                         "UK Leveson Inquiry testimony; Dominion Voting Systems "
                         "v. Fox News Network discovery documents (2023)",
        knowledge_date="2020-11-04",  # earliest documented knowledge re: 2020 election coverage
        notes="Founded News Corp (1980) and Fox News (1996) with Roger Ailes. "
              "Stepped down as Fox Corp chairman November 2023; retained chairman emeritus title. "
              "Dominion discovery revealed Murdoch was aware Fox hosts were promoting "
              "false 2020 election claims and did not intervene.",
        confidence=0.95,
    )

    # Roles
    insert_actor_role(
        conn, rupert_id, FISHERMAN["foxnews"],
        role="Founder and Executive Chairman, Fox Corporation",
        date_start="1996-10-07", date_end="2023-11-01",
        evidence="Fox Corporation SEC filings; public record",
        source_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=fox",
    )
    insert_actor_role(
        conn, rupert_id, FISHERMAN["foxnews"],
        role="Chairman Emeritus, Fox Corporation",
        date_start="2023-11-01", date_end=None,
        evidence="Fox Corporation press release, November 2023",
        source_url="https://www.foxcorporation.com",
    )

    # Investment
    insert_actor_investment(
        conn, rupert_id, FISHERMAN["foxnews"],
        position_type="major_shareholder",
        stake_description="Murdoch family trust holds majority voting control of Fox Corporation "
                          "through dual-class share structure (Class B supervoting shares)",
        date_start="2019-03-19", date_end=None,
        evidence="Fox Corporation prospectus and proxy statements, 2019–2026",
        source_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=fox",
    )

    # Knowledge records
    insert_actor_knowledge(
        conn, rupert_id, FISHERMAN["foxnews"],
        knowledge_type="internal_research",
        description="Dominion Voting Systems v. Fox News Network discovery documents revealed "
                    "that Rupert Murdoch was aware Fox News hosts including Tucker Carlson, "
                    "Laura Ingraham, and Sean Hannity were privately expressing doubt about "
                    "the stolen election narrative while promoting it on air. Murdoch described "
                    "the conduct as 'really crazy' in private messages but did not intervene "
                    "to stop the broadcasts.",
        date="2020-11-04",
        action_taken="No corrective action taken. Hosts continued to promote false claims.",
        evidence="Dominion Voting Systems, Inc. v. Fox News Network, LLC. Superior Court of "
                 "Delaware. Case No. N21C-11-082. Discovery documents filed February 2023.",
        source_url="https://www.courtlistener.com/docket/19828438/",
        confidence=0.97,
    )
    insert_actor_knowledge(
        conn, rupert_id, FISHERMAN["foxnews"],
        knowledge_type="regulatory_finding",
        description="UK Leveson Inquiry into press standards (2011-2012) examined Murdoch's "
                    "oversight of News International during the phone hacking scandal. "
                    "Rupert Murdoch testified he was not aware of widespread hacking at "
                    "News of the World; the inquiry found failures of corporate governance "
                    "at the highest levels.",
        date="2012-04-25",
        action_taken="News of the World closed July 2011. Rebekah Brooks and others prosecuted. "
                     "Murdoch not personally prosecuted.",
        evidence="The Leveson Inquiry: Culture, Practice and Ethics of the Press. "
                 "Volume IV. November 2012. HC 780-IV.",
        source_url="https://www.gov.uk/government/publications/leveson-inquiry-report-into-the-culture-practices-and-ethics-of-the-press",
        confidence=0.95,
    )

    # -------------------------------------------------------------------------
    # LACHLAN MURDOCH
    # CEO, Fox Corporation
    # -------------------------------------------------------------------------
    lachlan_id = insert_actor(
        conn,
        name="Lachlan Murdoch",
        aliases="Lachlan Keith Murdoch",
        current_role="Executive Chairman and CEO, Fox Corporation",
        current_fisherman_id=FISHERMAN["foxnews"],
        documented_knowledge=1,
        knowledge_source="Dominion Voting Systems v. Fox News Network discovery documents (2023); "
                         "Fox Corporation SEC filings",
        knowledge_date="2020-11-04",
        notes="Son of Rupert Murdoch. Named co-chairman of News Corp 2014; "
              "became sole chairman and CEO of Fox Corporation when Fox and News Corp split 2019. "
              "Named in Dominion discovery as aware of false election coverage.",
        confidence=0.95,
    )

    insert_actor_role(
        conn, lachlan_id, FISHERMAN["foxnews"],
        role="Executive Chairman and CEO, Fox Corporation",
        date_start="2019-03-19", date_end=None,
        evidence="Fox Corporation formation and SEC filings, 2019",
        source_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=fox",
    )

    insert_actor_investment(
        conn, lachlan_id, FISHERMAN["foxnews"],
        position_type="major_shareholder",
        stake_description="Beneficiary of Murdoch family trust; holds Class B supervoting shares "
                          "in Fox Corporation; personal holdings disclosed in annual proxy statements",
        date_start="2019-03-19", date_end=None,
        evidence="Fox Corporation proxy statements 2019–2026",
        source_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=fox",
    )

    insert_actor_knowledge(
        conn, lachlan_id, FISHERMAN["foxnews"],
        knowledge_type="court_proceeding",
        description="Dominion discovery documents show Lachlan Murdoch was copied on or "
                    "involved in communications about Fox News coverage of the 2020 election "
                    "during the period when hosts were privately disputing claims they were "
                    "publicly amplifying. Lachlan was named as a witness in the Dominion case.",
        date="2020-11-04",
        action_taken="No corrective editorial action documented. Settlement reached March 2023 "
                     "for $787.5 million; Fox did not issue correction or acknowledge wrongdoing.",
        evidence="Dominion Voting Systems, Inc. v. Fox News Network, LLC. Superior Court of "
                 "Delaware. Case No. N21C-11-082. Settlement announced March 2023.",
        source_url="https://www.courtlistener.com/docket/19828438/",
        confidence=0.95,
    )

    # -------------------------------------------------------------------------
    # STEVE HUFFMAN (SPEZ)
    # CEO, Reddit
    # -------------------------------------------------------------------------
    huffman_id = insert_actor(
        conn,
        name="Steve Huffman",
        aliases="spez",
        current_role="CEO and Co-Founder, Reddit Inc.",
        current_fisherman_id=FISHERMAN["reddit"],
        documented_knowledge=1,
        knowledge_source="Congressional testimony 2024; Reddit IPO S-1 filing 2024; "
                         "public statements on platform harm and content moderation",
        knowledge_date="2021-10-01",
        notes="Co-founded Reddit 2005 with Alexis Ohanian and Aaron Swartz. "
              "Stepped down 2009; returned as CEO 2015. Known username 'spez'. "
              "Controversial 2016 incident: admitted to secretly editing comments "
              "made by users criticizing him. Led Reddit through 2024 IPO.",
        confidence=0.9,
    )

    insert_actor_role(
        conn, huffman_id, FISHERMAN["reddit"],
        role="Co-Founder and CEO, Reddit",
        date_start="2015-07-10", date_end=None,
        evidence="Reddit corporate filings; public record",
        source_url="https://www.reddit.com/r/announcements/",
    )

    insert_actor_investment(
        conn, huffman_id, FISHERMAN["reddit"],
        position_type="major_shareholder",
        stake_description="Significant equity stake as co-founder; holdings disclosed in Reddit "
                          "IPO S-1 filing (March 2024). Reddit trades on NYSE as RDDT.",
        date_start="2005-06-23", date_end=None,
        evidence="Reddit Inc. Form S-1 Registration Statement. SEC filing, February 2024.",
        source_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=rddt",
    )

    insert_actor_knowledge(
        conn, huffman_id, FISHERMAN["reddit"],
        knowledge_type="media_coverage",
        description="Huffman testified before the Senate Judiciary Committee in January 2024 "
                    "alongside other platform CEOs regarding child safety online. "
                    "He acknowledged Reddit hosts harmful content and described content "
                    "moderation efforts, while defending the platform's community-moderation "
                    "model. Reddit's IPO S-1 filing discloses platform risks including "
                    "harmful content as a material business risk.",
        date="2024-01-31",
        action_taken="Announced expanded child safety tools and CSAM detection partnerships. "
                     "Reddit proceeded with IPO March 2024.",
        evidence="Senate Judiciary Committee hearing on child safety online, January 31, 2024. "
                 "Reddit Inc. Form S-1, February 2024.",
        source_url="https://www.judiciary.senate.gov/committee-activity/hearings/"
                   "protecting-our-children-online",
        confidence=0.9,
    )
    insert_actor_knowledge(
        conn, huffman_id, FISHERMAN["reddit"],
        knowledge_type="media_coverage",
        description="In November 2016, Huffman admitted to secretly modifying comments in "
                    "r/The_Donald that were directing personal insults at him, replacing "
                    "his username with the names of subreddit moderators. He acknowledged "
                    "the action was wrong and resigned as a moderator from r/The_Donald. "
                    "The incident demonstrated that platform administrators have technical "
                    "ability to modify user content — contradicting platform arguments about "
                    "inability to control content.",
        date="2016-11-23",
        action_taken="Public apology. Huffman retained CEO position.",
        evidence="Huffman, Steve ('spez'). Reddit post: 'Transparency and Edit Logs.' "
                 "r/announcements, November 23, 2016.",
        source_url="https://www.reddit.com/r/announcements/comments/5frg1n/",
        confidence=0.97,
    )

    # -------------------------------------------------------------------------
    # SHOU ZI CHEW
    # CEO, TikTok / Global Head, ByteDance
    # -------------------------------------------------------------------------
    chew_id = insert_actor(
        conn,
        name="Shou Zi Chew",
        aliases="Chew Shou Zi; 周受资",
        current_role="CEO, TikTok; Head of Global Business, ByteDance",
        current_fisherman_id=FISHERMAN["tiktok"],
        documented_knowledge=1,
        knowledge_source="Senate Judiciary Committee testimony, January 2024; "
                         "House Energy and Commerce Committee testimony, March 2023; "
                         "TikTok internal safety documents; court filings in Anderson v. TikTok",
        knowledge_date="2023-03-23",
        notes="Singaporean national. Appointed CEO of TikTok January 2021. "
              "Previously CFO of Xiaomi. Became public face of TikTok during "
              "US Congressional scrutiny and attempted forced divestiture. "
              "Testified before Congress twice in 2023-2024.",
        confidence=0.92,
    )

    insert_actor_role(
        conn, chew_id, FISHERMAN["tiktok"],
        role="CEO, TikTok",
        date_start="2021-01-01", date_end=None,
        evidence="TikTok press release January 2021; public record",
        source_url="https://newsroom.tiktok.com",
    )

    insert_actor_knowledge(
        conn, chew_id, FISHERMAN["tiktok"],
        knowledge_type="regulatory_finding",
        description="Chew testified before the House Energy and Commerce Committee on "
                    "March 23, 2023 — the first TikTok CEO to testify before Congress. "
                    "He was questioned extensively about the Blackout Challenge deaths, "
                    "including Nylah Anderson (age 10, 2021) and other children. "
                    "Chew acknowledged awareness of the challenge and described content "
                    "moderation measures, while denying the algorithm specifically "
                    "targeted vulnerable children. He was unable to answer questions "
                    "about specific internal safety research.",
        date="2023-03-23",
        action_taken="No algorithmic change announced. TikTok continued to contest "
                     "Anderson v. TikTok and related suits.",
        evidence="Protecting Americans from Foreign Adversary Controlled Applications Act "
                 "hearing. House Energy and Commerce Committee. March 23, 2023.",
        source_url="https://energycommerce.house.gov/events/hearing-tiktok-how-congress-can-"
                   "safeguard-american-data-privacy-and-protect-children-from-online-harms",
        confidence=0.95,
    )
    insert_actor_knowledge(
        conn, chew_id, FISHERMAN["tiktok"],
        knowledge_type="court_proceeding",
        description="Shou Zi Chew is named as a defendant or relevant party in multiple "
                    "state and federal suits alleging TikTok's algorithm served harmful "
                    "content to minors, including suits arising from Blackout Challenge deaths. "
                    "TikTok under his leadership chose to settle several major cases — "
                    "including a California class action settled days after JackLynn Blackwell's "
                    "death in February 2026 — rather than defend the algorithm in open court.",
        date="2026-02-10",
        action_taken="Settlement. Terms not disclosed. Algorithm not changed.",
        evidence="Multiple court filings 2022–2026; settlement reporting by Reuters and AP, "
                 "February 2026.",
        source_url=None,
        confidence=0.88,
        notes="Specific settlement documents under seal. Settlement fact reported by "
              "multiple outlets but terms not public.",
    )
    insert_actor_knowledge(
        conn, chew_id, FISHERMAN["tiktok"],
        knowledge_type="whistleblower_report",
        description="Internal TikTok documents and former employee accounts (reported by "
                    "Forbes and The Guardian, 2022-2023) described a 'heating' mechanism "
                    "allowing TikTok employees to manually boost videos into For You feeds, "
                    "contradicting public statements that the algorithm operated neutrally "
                    "based solely on user behavior signals.",
        date="2022-10-20",
        action_taken="TikTok acknowledged the 'heating' feature existed but described it "
                     "as limited in use. No independent audit conducted.",
        evidence="Forbes. 'TikTok's Secret 'Heating' Button Can Make Anyone Go Viral.' "
                 "October 20, 2022.",
        source_url="https://www.forbes.com/sites/emilybaker-white/2022/10/20/"
                   "tiktoks-secret-heating-button-can-make-anyone-go-viral/",
        confidence=0.9,
    )

    # -------------------------------------------------------------------------
    # MARK ZUCKERBERG (foundational record — Meta is primary fisherman)
    # -------------------------------------------------------------------------
    zuck_id = insert_actor(
        conn,
        name="Mark Zuckerberg",
        aliases="Mark Elliot Zuckerberg; Zuck",
        current_role="CEO and Chairman, Meta Platforms Inc.",
        current_fisherman_id=FISHERMAN["meta_facebook"],
        documented_knowledge=1,
        knowledge_source="Facebook Papers (Haugen disclosure 2021); "
                         "Senate Commerce Subcommittee testimony 2021; "
                         "Senate Judiciary Committee testimony 2024; "
                         "internal Meta research documents produced in litigation",
        knowledge_date="2021-09-13",
        notes="Co-founded Facebook 2004. Controls Meta through dual-class share structure "
              "giving him ~61% voting power as of 2024. Personally testified before Congress "
              "in 2018, 2021, and 2024. Apologized to bereaved families at January 2024 "
              "hearing while not committing to algorithmic changes.",
        confidence=0.98,
    )

    insert_actor_role(
        conn, zuck_id, FISHERMAN["meta_facebook"],
        role="Co-Founder, CEO, and Chairman, Meta Platforms Inc. (formerly Facebook Inc.)",
        date_start="2004-02-04", date_end=None,
        evidence="Public record; Meta SEC filings",
        source_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=meta",
    )
    insert_actor_role(
        conn, zuck_id, FISHERMAN["meta_instagram"],
        role="Controlling owner (Instagram acquired by Facebook April 2012)",
        date_start="2012-04-09", date_end=None,
        evidence="FTC filings; Meta annual reports",
        source_url=None,
    )

    insert_actor_investment(
        conn, zuck_id, FISHERMAN["meta_facebook"],
        position_type="major_shareholder",
        stake_description="Holds Class B supervoting shares granting ~61% voting control of Meta "
                          "as of 2024, despite owning approximately 13% of total shares. "
                          "Personal net worth estimated at $150B+ (Forbes 2024).",
        date_start="2012-05-18", date_end=None,
        evidence="Meta Platforms Inc. proxy statements 2022–2024; Forbes Billionaires list",
        source_url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=meta",
    )

    insert_actor_knowledge(
        conn, zuck_id, FISHERMAN["meta_facebook"],
        knowledge_type="internal_research",
        description="Facebook Papers (disclosed by Frances Haugen, September 2021): "
                    "Internal Meta research found Instagram worsened body image issues "
                    "for one in three teenage girls. A 2019 internal study titled "
                    "'Facebook's Well-Being Impact' found the platform had net negative "
                    "effects on user wellbeing. An internal 2020 document found 'we make "
                    "body image issues worse for one in three teen girls.' Recommendations "
                    "to change the algorithm to reduce harm were reviewed by leadership "
                    "and overruled because changes would reduce engagement metrics.",
        date="2021-09-13",
        action_taken="No algorithmic change. Zuckerberg testified before Congress October 2021 "
                     "and disputed Haugen's characterizations. Instagram announced superficial "
                     "changes to teen safety tools.",
        evidence="Facebook internal documents as published by Wall Street Journal "
                 "('The Facebook Files,' September 2021) and consortium of news organizations "
                 "('The Facebook Papers,' October 2021).",
        source_url="https://www.wsj.com/articles/the-facebook-files-11631713039",
        confidence=0.98,
    )
    insert_actor_knowledge(
        conn, zuck_id, FISHERMAN["meta_facebook"],
        knowledge_type="court_proceeding",
        description="Zuckerberg testified before the Senate Judiciary Committee on "
                    "January 31, 2024, alongside TikTok, Snap, Discord, and X CEOs. "
                    "Bereaved parents held photographs of their children in the gallery. "
                    "Zuckerberg said 'I'm sorry for everything you have all been through' "
                    "but did not apologize for the algorithm, did not commit to changing it, "
                    "and did not acknowledge internal research findings as accurate.",
        date="2024-01-31",
        action_taken="Meta announced incremental teen safety features. No algorithmic change. "
                     "Zuckerberg retained all positions and voting control.",
        evidence="Senate Judiciary Committee hearing transcript, January 31, 2024. "
                 "Video and transcript available via C-SPAN.",
        source_url="https://www.judiciary.senate.gov/committee-activity/hearings/"
                   "protecting-our-children-online",
        confidence=0.99,
    )

    conn.close()
    print("Actor records seeded successfully.")
    print(f"  Rupert Murdoch   → actor rowid {rupert_id}")
    print(f"  Lachlan Murdoch  → actor rowid {lachlan_id}")
    print(f"  Steve Huffman    → actor rowid {huffman_id}")
    print(f"  Shou Zi Chew     → actor rowid {chew_id}")
    print(f"  Mark Zuckerberg  → actor rowid {zuck_id}")


if __name__ == "__main__":
    seed()

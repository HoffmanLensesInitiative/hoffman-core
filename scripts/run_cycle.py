#!/usr/bin/env python3
"""
Hoffman Lenses -- Agent Cycle Runner
Reads a supervisor document, sends it to Claude,
writes results back to the document, commits to GitHub.

Usage:
  python run_cycle.py build
  python run_cycle.py intel
  python run_cycle.py investigate
  python run_cycle.py advocate
  python run_cycle.py all
"""

import os
import sys
import json
import anthropic
from datetime import datetime, timezone

# ── Configuration ─────────────────────────────────────────

SUPERVISOR_DOCS = {
    'build':       'HOFFMAN_BUILD.md',
    'intel':       'HOFFMAN_INTEL.md',
    'investigate': 'HOFFMAN_INVESTIGATE.md',
    'advocate':    'HOFFMAN_ADVOCATE.md'
}

# How many times per day each team runs
CYCLE_SCHEDULES = {
    'build':       1,   # Once daily -- build cycles are substantial work
    'intel':       2,   # Twice daily -- database population and verification
    'investigate': 1,   # Once daily -- deep research takes time
    'advocate':    1,   # Once daily -- outreach prep and monitoring
}

# What each agent is instructed to do in each cycle
AGENT_PROMPTS = {
    'build': """You are the Hoffman Lenses Build Agent.

Read the supervisor document above carefully.
It contains your mission, current state, build queue, and build log.

Your task for this cycle:
1. Identify the top item in the BUILD QUEUE
2. Build it -- write complete, working, tested code
3. Verify it works (trace through the logic, check for errors)
4. Record what you built, what you tested, and what you found

Return your response in this exact format:

## CYCLE RESULT -- BUILD -- {date}

### What I worked on
[describe the build queue item you addressed]

### What I built
[describe what was created or changed, with key code if relevant]

### Test results
[what was tested, what passed, what failed]

### Code to add to repository
[any new or changed files, with full content]

### Build queue update
[which items are done, which are next]

### Issues discovered
[anything that needs director attention]

### Next cycle recommendation
[what the next build cycle should focus on]
""",

    'intel': """You are the Hoffman Lenses Intelligence Agent.

Read the supervisor document above carefully.
It contains your mission, intelligence queue, and what's known so far.

Your task for this cycle:
1. Identify the top research target from the INTELLIGENCE QUEUE
2. Research it using your training knowledge -- document what is known
   about this publisher, their business model, documented harms,
   ownership structure, advertising relationships
3. Write structured BMID records matching the schema in BMID_SCHEMA.md
4. Assign honest confidence scores -- never inflate

Return your response in this exact format:

## CYCLE RESULT -- INTEL -- {date}

### Target researched
[which fisherman or pattern was researched]

### Fisherman record
[structured data matching BMID fisherman schema]

### Motive records
[structured data matching BMID motive schema, one per motive]

### Catch records
[structured data matching BMID catch schema, documented harms only]

### Evidence records
[primary sources for every factual claim]

### Confidence assessment
[honest assessment of what is well-documented vs uncertain]

### Gaps identified
[what needs primary source verification, what is missing]

### API calls to make
[formatted as: POST /api/v1/fisherman with body: {...}]

### Next cycle recommendation
[what the next intel cycle should focus on]
""",

    'investigate': """You are the Hoffman Lenses Investigation Agent.

Read the supervisor document above carefully.
It contains your mission, investigation queue, and rabbit hole findings.

Your task for this cycle:
1. Pick the top investigation from the INVESTIGATION QUEUE
2. Go deep -- follow threads, find primary sources, map connections
3. Document unexpected findings as RABBIT HOLE FINDINGS
4. Produce a structured intelligence file for the Intel team

Return your response in this exact format:

## CYCLE RESULT -- INVESTIGATE -- {date}

### Investigation target
[what was investigated]

### Key findings
[factual findings with primary source citations]

### Primary sources found
[URLs, titles, publication dates, what each proves]

### Rabbit hole findings
[unexpected connections discovered -- flag each clearly]

### Corporate/ownership connections
[documented ownership and financial relationships]

### Recommended BMID records
[structured data ready for Intel agent to enter]

### Unresolved threads
[what needs more investigation]

### Next cycle recommendation
[which thread to follow next]
""",

    'advocate': """You are the Hoffman Lenses Advocacy Agent.

Read the supervisor document above carefully.
It contains your mission, outreach queue, and contact information.

Your task for this cycle:
1. Review the ADVOCACY QUEUE for the highest priority item
2. Prepare any communications, drafts, or research needed
3. Monitor for new legal developments, academic papers, or news
   relevant to the mission
4. Draft any outreach materials for director review

IMPORTANT: All family communications and legal communications
must be flagged as REQUIRES DIRECTOR REVIEW before sending.
Never send these autonomously.

Return your response in this exact format:

## CYCLE RESULT -- ADVOCATE -- {date}

### Queue item addressed
[what advocacy task was worked on]

### Drafts prepared
[any communications drafted -- mark REQUIRES DIRECTOR REVIEW if sensitive]

### Intelligence gathered
[new legal cases, academic papers, news relevant to mission]

### White paper updates needed
[any new findings that should be added to the white paper]

### Requires director review
[anything that needs Norm's decision before proceeding]

### Next cycle recommendation
[what the next advocacy cycle should focus on]
"""
}

# ── Main cycle runner ─────────────────────────────────────

def run_cycle(team):
    if team not in SUPERVISOR_DOCS:
        print(f'Unknown team: {team}')
        print(f'Valid teams: {", ".join(SUPERVISOR_DOCS.keys())}')
        return False

    doc_path = SUPERVISOR_DOCS[team]
    if not os.path.exists(doc_path):
        print(f'Supervisor document not found: {doc_path}')
        print('Make sure you are running from the hoffman-core directory')
        return False

    print(f'[{team.upper()}] Reading supervisor document: {doc_path}')
    supervisor_doc = open(doc_path, encoding='utf-8').read()

    # Also read HOFFMAN.md for mission context
    mission_context = ''
    if os.path.exists('HOFFMAN.md'):
        mission_context = open('HOFFMAN.md', encoding='utf-8').read()

    # Also read BMID schema for intel/investigate agents
    bmid_context = ''
    if team in ('intel', 'investigate') and os.path.exists('BMID_SCHEMA.md'):
        bmid_context = open('BMID_SCHEMA.md', encoding='utf-8').read()

    date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    prompt = AGENT_PROMPTS[team].replace('{date}', date_str)

    # Build the full message
    full_context = []
    if mission_context:
        full_context.append(f'# DIRECTOR DOCUMENT (HOFFMAN.md)\n\n{mission_context}')
    if bmid_context:
        full_context.append(f'# BMID SCHEMA\n\n{bmid_context}')
    full_context.append(f'# SUPERVISOR DOCUMENT ({doc_path})\n\n{supervisor_doc}')
    full_context.append(f'# YOUR INSTRUCTIONS FOR THIS CYCLE\n\n{prompt}')

    message_content = '\n\n---\n\n'.join(full_context)

    print(f'[{team.upper()}] Sending to Claude (context: {len(message_content)} chars)')

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print('ERROR: ANTHROPIC_API_KEY environment variable not set')
        return False

    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model='claude-opus-4-5',
            max_tokens=8000,
            messages=[{
                'role': 'user',
                'content': message_content
            }]
        )
    except Exception as e:
        print(f'[{team.upper()}] Claude API error: {e}')
        return False

    result = response.content[0].text
    print(f'[{team.upper()}] Got response ({len(result)} chars)')

    # Append result to supervisor document
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    separator = f'\n\n---\n\n<!-- AUTO CYCLE {timestamp} -->\n\n'

    with open(doc_path, 'a', encoding='utf-8') as f:
        f.write(separator + result)

    print(f'[{team.upper()}] Results written to {doc_path}')

    # Save result to daily report file
    report_dir = 'reports'
    os.makedirs(report_dir, exist_ok=True)
    date_slug = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    report_path = f'{report_dir}/{date_slug}-{team}.md'

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f'# Hoffman Lenses -- {team.upper()} Cycle Report\n')
        f.write(f'**Date:** {timestamp}\n\n')
        f.write(result)

    print(f'[{team.upper()}] Report saved to {report_path}')
    return True


def run_all():
    results = {}
    for team in SUPERVISOR_DOCS:
        print(f'\n{"="*50}')
        print(f'RUNNING {team.upper()} CYCLE')
        print(f'{"="*50}')
        results[team] = run_cycle(team)

    print(f'\n{"="*50}')
    print('ALL CYCLES COMPLETE')
    for team, success in results.items():
        status = 'OK' if success else 'FAILED'
        print(f'  {team.upper()}: {status}')
    print(f'{"="*50}')
    return all(results.values())


def generate_daily_summary():
    """
    Reads all reports from today and generates a
    plain-language summary for the director.
    """
    import glob
    date_slug = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    reports = glob.glob(f'reports/{date_slug}-*.md')

    if not reports:
        print('No reports found for today')
        return

    combined = []
    for report_path in sorted(reports):
        team = report_path.split('-')[-1].replace('.md', '')
        content = open(report_path, encoding='utf-8').read()
        combined.append(f'## {team.upper()} TEAM\n\n{content}')

    summary_input = '\n\n---\n\n'.join(combined)

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=2000,
        messages=[{
            'role': 'user',
            'content': f"""You are summarizing the daily activity of the Hoffman Lenses
agent organization for the Director (Norm Robichaud).

Here are today's cycle reports from all teams:

{summary_input}

Write a concise director's briefing -- plain language, no jargon.
Format:

# Hoffman Lenses -- Director Briefing
## {date_slug}

### What got done today
[2-3 sentences per team, only what actually happened]

### Decisions needed from you
[anything flagged as REQUIRES DIRECTOR REVIEW]

### Things to know
[anything unexpected, concerning, or worth noting]

### What happens tomorrow
[what the agents will work on in the next cycles]
"""
        }]
    )

    summary = response.content[0].text
    summary_path = f'reports/{date_slug}-DIRECTOR-BRIEFING.md'

    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)

    print(f'\nDirector briefing saved to {summary_path}')
    print('\n' + '='*50)
    print(summary)
    print('='*50)


# ── Entry point ───────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python run_cycle.py [build|intel|investigate|advocate|all|summary]')
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'all':
        success = run_all()
        sys.exit(0 if success else 1)
    elif command == 'summary':
        generate_daily_summary()
    elif command in SUPERVISOR_DOCS:
        success = run_cycle(command)
        sys.exit(0 if success else 1)
    else:
        print(f'Unknown command: {command}')
        print('Valid: build, intel, investigate, advocate, all, summary')
        sys.exit(1)

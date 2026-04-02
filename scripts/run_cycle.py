#!/usr/bin/env python3
"""
Hoffman Lenses -- Agent Cycle Runner
Reads a supervisor document, sends it to Claude with file-writing tools,
executes any tool calls (creating/modifying real files), then commits.

Usage:
  python run_cycle.py build
  python run_cycle.py intel
  python run_cycle.py investigate
  python run_cycle.py advocate
  python run_cycle.py all
  python run_cycle.py summary
"""

import os
import re
import sys
import json
import time
import subprocess
import anthropic
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ─────────────────────────────────────────

SUPERVISOR_DOCS = {
    'browser':     'HOFFMAN_BUILD_BROWSER.md',
    'bmid':        'HOFFMAN_BUILD_BMID.md',
    'website':     'HOFFMAN_BUILD_WEBSITE.md',
    'intel':       'HOFFMAN_INTEL.md',
    'investigate': 'HOFFMAN_INVESTIGATE.md',
    'advocate':    'HOFFMAN_ADVOCATE.md',
    # legacy -- kept for reference, no longer scheduled
    'build':       'HOFFMAN_BUILD.md',
}

# ── Tools ─────────────────────────────────────────────────

# Available to all agents
TOOL_READ_FILE = {
    'name': 'read_file',
    'description': (
        'Read the current content of a file in the repository. '
        'Use this when you need to understand an existing file\'s structure before modifying it. '
        'Returns the file content (up to 8000 characters). '
        'If the file does not exist, returns an error. '
        'Read a file at most once per cycle -- do not re-read files you have already seen.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'path': {
                'type': 'string',
                'description': 'File path relative to the repo root (e.g. bmid-api/seed.py)'
            }
        },
        'required': ['path']
    }
}

# Available to all agents
TOOL_WRITE_FILE = {
    'name': 'write_file',
    'description': (
        'Write content to a file in the repository. '
        'Creates parent directories as needed. '
        'Overwrites the file if it already exists. '
        'Use this to create every new file or update every existing file you build. '
        'Do NOT just describe files in text -- call this tool to actually create them. '
        'WARNING: content must be complete and non-empty. Empty or near-empty writes are rejected.'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'path': {
                'type': 'string',
                'description': 'File path relative to the repo root (e.g. hoffman-browser/src/foo.js)'
            },
            'content': {
                'type': 'string',
                'description': 'Complete file content to write. Must not be empty.'
            }
        },
        'required': ['path', 'content']
    }
}

# Available to intel agent only: append structured records to seed.py
TOOL_APPEND_SEED = {
    'name': 'append_seed_records',
    'description': (
        'Append new BMID records to bmid-api/seed.py. '
        'Records are appended to the correct list and the seed script is run automatically. '
        'Use this instead of write_file for BMID database records.\n\n'
        'REQUIRED FIELDS PER RECORD TYPE -- use these exact field names:\n\n'
        'fishermen: fisherman_id (TEXT, e.g. "fisherman-reddit"), domain, display_name, '
        'owner, parent_company, country, founded, business_model, '
        'revenue_sources (list), confidence_score (0.0-1.0), contributed_by\n\n'
        'motives: motive_id (TEXT, e.g. "motive-reddit-ad-revenue"), fisherman_id, '
        'motive_type, description, revenue_model, beneficiary, '
        'documented_evidence, confidence_score, contributed_by\n\n'
        'catches: catch_id (TEXT, e.g. "catch-reddit-001"), fisherman_id, '
        'harm_type, victim_demographic, documented_outcome, scale, '
        'academic_citation, date_documented, severity_score (1-10)\n\n'
        'evidence: evidence_id (TEXT, e.g. "ev-reddit-001"), entity_id (the fisherman_id), '
        'entity_type ("fisherman"), source_type ("primary"|"secondary"|"academic"), '
        'url, title, author, publication, published_date, summary, confidence (0.0-1.0)'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'fishermen': {
                'type': 'array',
                'description': 'List of fisherman record dicts to add',
                'items': {'type': 'object'}
            },
            'motives': {
                'type': 'array',
                'description': 'List of motive record dicts to add',
                'items': {'type': 'object'}
            },
            'catches': {
                'type': 'array',
                'description': 'List of catch record dicts to add',
                'items': {'type': 'object'}
            },
            'evidence': {
                'type': 'array',
                'description': 'List of evidence record dicts to add',
                'items': {'type': 'object'}
            }
        },
        'required': []
    }
}

TOOLS_BY_TEAM = {
    'browser':     [TOOL_READ_FILE, TOOL_WRITE_FILE],
    'bmid':        [TOOL_READ_FILE, TOOL_WRITE_FILE, TOOL_APPEND_SEED],
    'website':     [TOOL_READ_FILE, TOOL_WRITE_FILE],
    'intel':       [TOOL_READ_FILE, TOOL_WRITE_FILE, TOOL_APPEND_SEED],
    'investigate': [TOOL_READ_FILE, TOOL_WRITE_FILE],
    'advocate':    [TOOL_READ_FILE, TOOL_WRITE_FILE],
    'build':       [TOOL_READ_FILE, TOOL_WRITE_FILE],
}

# ── Helpers ───────────────────────────────────────────────

def strip_code_blocks(text):
    """Remove fenced code blocks from agent response before appending to supervisor doc.
    Files are written to disk via write_file tool -- no need to also embed them in the doc."""
    cleaned = re.sub(r'```[^\n]*\n.*?```', '', text, flags=re.DOTALL)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()


def rotate_supervisor_doc(doc_path, keep_cycles=1):
    """Keep only the N most recent auto-cycle entries in the supervisor doc.
    Older cycles are pruned to prevent context bloat."""
    with open(doc_path, encoding='utf-8') as f:
        content = f.read()
    markers = [m.start() for m in re.finditer(r'\n---\n\n<!-- AUTO CYCLE', content)]
    if len(markers) <= keep_cycles:
        return  # nothing to prune
    static_end = markers[0]
    keep_from = markers[-keep_cycles]
    result = content[:static_end] + content[keep_from:]
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(result)
    pruned = len(markers) - keep_cycles
    print(f'  [rotate] pruned {pruned} old cycle(s) from {doc_path}')


# ── Tool execution ─────────────────────────────────────────

READ_FILE_LIMIT = 30000  # chars returned to the agent per read_file call

def tool_read_file(path):
    """Read a file from disk. Returns content string or error."""
    try:
        full_path = Path(path)
        if not full_path.exists():
            return f'ERROR: file not found: {path}'
        content = full_path.read_text(encoding='utf-8', errors='replace')
        if len(content) > READ_FILE_LIMIT:
            return content[:READ_FILE_LIMIT] + f'\n\n[TRUNCATED: file is {len(content)} chars; only first {READ_FILE_LIMIT} shown]'
        return content if content else f'(file exists but is empty: {path})'
    except Exception as e:
        return f'ERROR reading {path}: {e}'


def tool_write_file(path, content, files_written):
    """Write a file to disk. Returns status string. Rejects empty writes."""
    if not content or not content.strip():
        msg = f'REJECTED: content is empty. write_file requires non-empty content. File {path} was NOT written.'
        print(f'  [tool] {msg}')
        return msg

    # Guard against accidentally wiping a large existing file with trivially small content.
    full_path = Path(path)
    if full_path.exists():
        existing_size = full_path.stat().st_size
        if existing_size > 500 and len(content) < 50:
            msg = (
                f'REJECTED: refusing to overwrite {path} ({existing_size} bytes) '
                f'with only {len(content)} chars. Read the file first, then write the complete updated version.'
            )
            print(f'  [tool] {msg}')
            return msg

    try:
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')
        files_written.append(str(full_path))
        print(f'  [tool] wrote {path} ({len(content)} chars)')
        return f'OK: wrote {len(content)} chars to {path}'
    except Exception as e:
        print(f'  [tool] ERROR writing {path}: {e}')
        return f'ERROR: {e}'


def tool_append_seed(fishermen, motives, catches, evidence, files_written):
    """Append records to seed.py lists and run the seed.

    Uses += extension lines appended to the end of the file rather than
    bracket-finding insertion, which was unreliable when string values
    contained ] characters (e.g. URLs).
    """
    seed_path = Path('bmid-api/seed.py')
    if not seed_path.exists():
        return 'ERROR: bmid-api/seed.py not found'

    content = seed_path.read_text(encoding='utf-8')

    # Verify each list name exists in the file before appending extensions
    for list_name in ['FISHERMEN', 'MOTIVES', 'CATCHES', 'EVIDENCE']:
        if f'{list_name} = [' not in content:
            return f'ERROR: could not find {list_name} list in seed.py -- read the file first to check its structure'

    additions = []
    date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    extension_lines = [f'\n# -- appended by intel agent {date_str} --']

    for list_name, records in [
        ('FISHERMEN', fishermen or []),
        ('MOTIVES',   motives   or []),
        ('CATCHES',   catches   or []),
        ('EVIDENCE',  evidence  or []),
    ]:
        if not records:
            continue
        extension_lines.append(f'{list_name} += [')
        for rec in records:
            extension_lines.append('    ' + repr(rec) + ',')
        extension_lines.append(']')
        additions.append(f'{len(records)} {list_name.lower()}')

    if not additions:
        return 'OK: no records provided, nothing appended'

    new_content = content.rstrip() + '\n' + '\n'.join(extension_lines) + '\n'

    # Validate syntax before writing
    try:
        import ast as _ast
        _ast.parse(new_content)
    except SyntaxError as e:
        return f'ERROR: generated records have a Python syntax error and were NOT written: {e}'

    seed_path.write_text(new_content, encoding='utf-8')
    files_written.append(str(seed_path))
    print(f'  [tool] appended to seed.py: {", ".join(additions)}')

    # Run the seed
    try:
        result = subprocess.run(
            ['python', 'seed.py'],
            cwd='bmid-api',
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print('  [tool] seed.py ran successfully')
            return f'OK: appended {", ".join(additions)}. Seed ran successfully.\n' + result.stdout[-500:]
        else:
            print(f'  [tool] seed.py failed: {result.stderr}')
            return f'OK: appended records, but seed.py failed: {result.stderr[-300:]}'
    except Exception as e:
        return f'OK: appended records, but could not run seed.py: {e}'


def execute_tool(tool_name, tool_input, files_written):
    if tool_name == 'read_file':
        return tool_read_file(tool_input.get('path', ''))
    elif tool_name == 'write_file':
        return tool_write_file(
            tool_input.get('path', ''),
            tool_input.get('content', ''),
            files_written
        )
    elif tool_name == 'append_seed_records':
        return tool_append_seed(
            tool_input.get('fishermen', []),
            tool_input.get('motives', []),
            tool_input.get('catches', []),
            tool_input.get('evidence', []),
            files_written
        )
    else:
        return f'ERROR: unknown tool {tool_name}'


# ── Agent prompts ──────────────────────────────────────────

AGENT_PROMPTS = {
    'browser': """You are the Hoffman Browser Build Agent.

Read the supervisor document above carefully.
It contains your mission, current state, build queue, and build log.

## RULES FOR THIS CYCLE

**Stop immediately and report if blocked.** If a tool returns ERROR, write your cycle
result reporting the error. Do not retry the same operation. Do not loop.

**Read ALL files in Turn 1, write in Turn 2.** The conversation only keeps the most
recent exchange. If you read files across multiple turns you will lose earlier content.
Read every file you need in a single batch of parallel read_file calls on your first
turn, then write all modified files on your next turn. Do not read any file after Turn 1.

**Write files, not descriptions.** Call write_file for every file you create or change.
Text descriptions of code accomplish nothing. Do NOT include code blocks in your response.

## YOUR TASK FOR THIS CYCLE: BMID context injection

The top BUILD QUEUE item is BMID context injection in the analysis pipeline.

**Turn 1 -- read these three files simultaneously (all in one turn):**
- read_file('hoffman-browser/src/main.js')
- read_file('hoffman-browser/src/analyzer.js')
- read_file('hoffman-browser/panel/panel.html')

**Turn 2 -- write the modified files.** Based on what you read, modify the files needed
to inject BMID context before analysis. The BUILD BRIEF in the supervisor document
describes exactly what to do. Write every modified file via write_file.

Do not read any additional files. Do not read files you did not read in Turn 1.

## CYCLE RESULT FORMAT (fill this in after writing files)

## CYCLE RESULT -- BROWSER -- {date}

### What I built
[describe what was created or changed, no code]

### Files written
[list every file written via write_file -- if none, write NONE and explain why]

### Test results
[what was tested, what passed, what failed]

### Build queue update
[which items are done, which are next]

### Next cycle recommendation
[what the next browser cycle should focus on]
""",

    'bmid': """You are the Hoffman BMID Build Agent.

Read the supervisor document above carefully.
It contains your mission, current state, build queue, and build log.

## RULES FOR THIS CYCLE

**Stop immediately and report if blocked.** If a tool returns ERROR, write your cycle
result reporting the error. Do not retry the same operation. Do not loop.

**Read each file at most once.** Do not re-read a file you have already seen this cycle.
Do not read seed.py -- that is the intel agent's file, not yours.

**Write files, not descriptions.** Call write_file for every file you create or change.
Do NOT include code blocks in your response.

## YOUR TASK FOR THIS CYCLE: Add network/actor API endpoints to app.py

schema.sql was already updated last cycle with the 6 new tables. Your job this cycle
is to add the 5 new endpoints to app.py.

**Exact sequence -- follow this precisely:**
1. Call read_file('bmid-api/schema.sql') and read_file('bmid-api/app.py') in the SAME turn
2. Immediately call write_file('bmid-api/app.py') with the complete updated file
   (all existing routes preserved + 5 new endpoints appended at the end)
3. Do NOT call read_file again after step 1. You have everything you need.

**The 5 new endpoints to add:**
- GET /api/v1/network/<domain> -- all relationships for a fisherman
- GET /api/v1/actor/<actor_id> -- full actor profile
- GET /api/v1/actor/search?name=<name> -- search actors by name
- GET /api/v1/network/map -- full network graph as JSON
- GET /api/v1/accountability/<domain> -- full accountability chain for a domain

The schema for these tables (network, actor, actor_role, actor_investment,
actor_political, actor_knowledge) is in HOFFMAN.md Part 13 and in schema.sql.
Use the same Flask/SQLite patterns already in app.py.

## CYCLE RESULT FORMAT (fill this in after writing files)

## CYCLE RESULT -- BMID -- {date}

### What I built
[describe what was created or changed, no code]

### Files written
[list every file written via write_file -- if none, write NONE and explain why]

### Test results
[what was tested, what passed, what failed]

### Build queue update
[which items are done, which are next]

### Next cycle recommendation
[what the next BMID cycle should focus on]
""",

    'website': """You are the Hoffman Website Build Agent.

Read the supervisor document above carefully.
It contains your mission, current state, and build queue.

## RULES FOR THIS CYCLE

**Stop immediately and report if blocked.** If a tool returns ERROR, write your cycle
result reporting the error. Do not retry the same operation. Do not loop.

**Read ALL files in Turn 1, write in Turn 2.** The conversation only keeps the most
recent exchange. Read every file you need in a single batch on your first turn, then
write all output files on your next turn. Do not read any file after Turn 1.

**Write files, not descriptions.** Call write_file for every file you create or change.
Do NOT include code blocks or file contents in your text response.

IMPORTANT: /remembrance entries require director approval before going live.
Do not add contact functionality until email infrastructure is confirmed.

## YOUR TASK FOR THIS CYCLE: /remembrance page

**Turn 1 -- read these two files simultaneously (both in one turn):**
- read_file('hoffman-lenses-website/remembrance/index.html')
- read_file('hoffman-lenses-website/remembrance/remembrance.css')

**Turn 2 -- write the finished page.** Using the style and structure you see in those
files, write the complete updated index.html with the remembrance entries added.
Flag all individual entries as REQUIRES DIRECTOR REVIEW.

Do not read any other files. Do not read the same file twice.

## CYCLE RESULT FORMAT

## CYCLE RESULT -- WEBSITE -- {date}

### What I built
[describe what was created or changed]

### Files written
[list every file written via write_file -- if none, write NONE and explain why]

### Requires director review
[anything that needs approval before publishing]

### Next cycle recommendation
[what the next website cycle should focus on]
""",

    'build': """You are the Hoffman Lenses Build Agent.

Read the supervisor document above carefully.
It contains your mission, current state, build queue, and build log.

## RULES FOR THIS CYCLE

**Stop immediately and report if blocked.** If a tool returns ERROR, write your cycle
result reporting the error. Do not retry the same operation. Do not loop.

**Read before you modify.** If you need to update an existing file, call read_file
once to see its current content, then write the complete updated version with write_file.
Read each file at most once. Do not re-read files you have already seen.

**Write files, not descriptions.** Call write_file for every file you create or change.
Text descriptions of code accomplish nothing. Do NOT include code blocks in your response.

## YOUR TASK

1. Identify the top item in the BUILD QUEUE
2. If you need to see an existing file first, call read_file ONCE for that file
3. Build it -- write complete, working code via write_file
4. Write your cycle result

## CYCLE RESULT FORMAT

## CYCLE RESULT -- BUILD -- {date}

### What I built
[describe what was created or changed]

### Files written
[list every file written via the write_file tool -- if none, write NONE and explain why]

### Test results
[what was tested, what passed, what failed]

### Build queue update
[which items are done, which are next]

### Issues discovered
[anything that needs director attention]

### Next cycle recommendation
[what the next build cycle should focus on]
""",

    'intel': """You are the Hoffman Lenses Intelligence Agent.

Read the supervisor document above carefully.
It contains your mission, intelligence queue, and what is known so far.

## RULES FOR THIS CYCLE

**Stop immediately and report if blocked.** If append_seed_records returns ERROR,
write your cycle result reporting the exact error message. Do not retry. Do not loop.
If you need to check the seed file structure first, call read_file('bmid-api/seed.py')
ONCE before calling append_seed_records.

**Call the tool once with complete data.** Build all your records in one call to
append_seed_records. Do not make multiple partial calls.

## YOUR TASK

1. Identify the top target from the INTELLIGENCE QUEUE
2. If you are unsure of the seed file structure, call read_file('bmid-api/seed.py') once
3. Call append_seed_records ONCE with the fisherman, motives, catches, and evidence records
4. Write your cycle result

Every fisherman, motive, catch, and evidence record must be a Python dict passed to
append_seed_records. Assign honest confidence scores -- never inflate.

Keep record field values concise (one or two sentences max per field). You can always
add more detail in a future cycle. A complete but brief record is better than a
detailed but truncated one.

## CYCLE RESULT FORMAT (fill this in after calling append_seed_records)

## CYCLE RESULT -- INTEL -- {date}

### Target researched
[which fisherman or pattern was researched]

### Records added
[list every record added via append_seed_records -- if none, write NONE and state the error]

### Confidence assessment
[honest assessment of what is well-documented vs uncertain]

### Gaps identified
[what needs primary source verification, what is missing]

### Next cycle recommendation
[what the next intel cycle should focus on]
""",

    'investigate': """You are the Hoffman Lenses Investigation Agent.

Read the supervisor document above carefully.
It contains your mission, investigation queue, and rabbit hole findings.

## RULES FOR THIS CYCLE

**Stop immediately and report if blocked.** If write_file returns ERROR, write your
cycle result reporting the exact error. Do not retry the same operation. Do not loop.

**Write the file first, report second.** Call write_file to save your findings as
reports/investigate-{slug}.md. Then write your cycle result.

## YOUR TASK

1. Pick the top investigation from the INVESTIGATION QUEUE
2. Compile your findings -- primary sources, connections, key facts
3. Call write_file ONCE to save the intelligence file at reports/investigate-{slug}.md
4. Write your cycle result

Do not re-read existing files unless the investigation explicitly requires it.
Do not loop on planning. Write first, refine later.

## CYCLE RESULT FORMAT

## CYCLE RESULT -- INVESTIGATE -- {date}

### Investigation target
[what was investigated]

### Key findings
[factual findings with primary source citations]

### Rabbit hole findings
[unexpected connections discovered]

### Files written
[intelligence file saved via write_file -- if none, write NONE and explain why]

### Next cycle recommendation
[which thread to follow next]
""",

    'advocate': """You are the Hoffman Lenses Advocacy Agent.

Read the supervisor document above carefully.
It contains your mission, outreach queue, and contact information.

## RULES FOR THIS CYCLE

**Stop immediately and report if blocked.** If write_file returns ERROR, write your
cycle result reporting the exact error. Do not retry the same operation. Do not loop.

**Do not read existing drafts.** Previous drafts are summarized in the supervisor
document. Reading them file-by-file wastes your turns. Write new output directly.

**Write drafts directly.** Call write_file to save drafts at
reports/advocate-draft-{slug}.md. Do NOT include file contents in your response.

IMPORTANT: All family and legal communications must be flagged
as REQUIRES DIRECTOR REVIEW. Never send these autonomously.

## YOUR TASK FOR THIS CYCLE

The press kit outline and family letter template from prior cycles are done.
This cycle: write the Matthew Bergman / Social Media Victims Law Center outreach
letter and save it as reports/advocate-draft-bergman-letter.md.
Flag it REQUIRES DIRECTOR REVIEW.

Do not read any files. You have everything you need in the supervisor document.
Write the letter, call write_file once, then write your cycle result.

## CYCLE RESULT FORMAT

## CYCLE RESULT -- ADVOCATE -- {date}

### Queue item addressed
[what advocacy task was worked on]

### Drafts prepared
[any communications drafted -- mark REQUIRES DIRECTOR REVIEW if sensitive]

### Intelligence gathered
[new legal cases, academic papers, news relevant to mission]

### Requires director review
[anything that needs Norm's decision before proceeding]

### Next cycle recommendation
[what the next advocacy cycle should focus on]
"""
}

# ── Main cycle runner ──────────────────────────────────────

def run_cycle(team):
    if team not in SUPERVISOR_DOCS:
        print(f'Unknown team: {team}')
        return False

    doc_path = SUPERVISOR_DOCS[team]
    if not os.path.exists(doc_path):
        print(f'Supervisor document not found: {doc_path}')
        print('Make sure you are running from the hoffman-core directory')
        return False

    rotate_supervisor_doc(doc_path)
    print(f'[{team.upper()}] Reading supervisor document: {doc_path}')
    supervisor_doc = open(doc_path, encoding='utf-8').read()

    mission_context = ''
    if os.path.exists('HOFFMAN.md'):
        mission_context = open('HOFFMAN.md', encoding='utf-8').read()

    bmid_context = ''
    if team in ('intel', 'investigate') and os.path.exists('BMID_SCHEMA.md'):
        bmid_context = open('BMID_SCHEMA.md', encoding='utf-8').read()

    date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    prompt = AGENT_PROMPTS[team].replace('{date}', date_str)

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
        print('ERROR: ANTHROPIC_API_KEY not set')
        return False

    # timeout: 10s connect, 300s read (16K token responses can take 3-5 minutes to stream).
    client = anthropic.Anthropic(
        api_key=api_key,
        timeout=anthropic.Timeout(connect=10.0, read=300.0, write=10.0, pool=10.0)
    )
    tools = TOOLS_BY_TEAM.get(team, [])
    # Keep only the initial context message + the most recent exchange to limit
    # conversation growth. Tool results are appended per turn but older turns
    # are dropped -- the agent only needs the original brief and the latest state.
    initial_message = {'role': 'user', 'content': message_content}
    messages = [initial_message]
    files_written = []
    result_text = ''

    def call_api(msgs):
        """Call Claude with exponential backoff on rate limit and connection errors."""
        for attempt in range(5):
            try:
                return client.messages.create(
                    model='claude-sonnet-4-6',
                    max_tokens=16000,
                    tools=tools,
                    messages=msgs
                )
            except Exception as e:
                err = str(e).lower()
                if '429' in err or 'rate_limit' in err:
                    wait = 60 * (2 ** attempt)  # 60s, 120s, 240s, 480s, 960s
                    print(f'[{team.upper()}] Rate limited (attempt {attempt+1}/5). Waiting {wait}s...')
                    time.sleep(wait)
                elif 'connection' in err or 'timeout' in err:
                    wait = 30 * (attempt + 1)  # 30s, 60s, 90s, 120s, 150s
                    print(f'[{team.upper()}] Connection error (attempt {attempt+1}/5). Waiting {wait}s...')
                    time.sleep(wait)
                else:
                    print(f'[{team.upper()}] Unrecoverable API error: {e}')
                    return None
        print(f'[{team.upper()}] All retry attempts exhausted.')
        return None

    # Agentic loop -- keep going until no more tool calls
    # max_turns is intentionally low: legitimate multi-file work needs ~5 turns;
    # anything beyond 8 is almost certainly a planning/reading loop.
    max_turns = 8
    turn = 0
    tool_call_history = []  # list of (tool_name, key) for loop detection
    total_tool_calls = 0

    while turn < max_turns:
        turn += 1
        response = call_api(messages)
        if response is None:
            return False

        # Collect text and tool calls from this response
        tool_calls = []
        for block in response.content:
            if block.type == 'text':
                result_text += block.text
            elif block.type == 'tool_use':
                tool_calls.append(block)

        print(f'[{team.upper()}] Turn {turn}: stop_reason={response.stop_reason}, tool_calls={len(tool_calls)}')

        if response.stop_reason == 'end_turn' or not tool_calls:
            break

        # Execute tool calls, then reset messages to initial context + this exchange only.
        # This prevents the conversation from growing unboundedly across turns.
        tool_results = []
        for tc in tool_calls:
            total_tool_calls += 1
            print(f'  [tool] calling {tc.name}')

            # Loop detection: same tool + same primary argument more than twice = loop.
            # Exception: reading a file after successfully writing it is legitimate (verify step)
            # so we remove that file's read history entry when a write succeeds.
            path_arg = tc.input.get('path', '')
            loop_key = (tc.name, str(tc.input.get('path', tc.input.get('fishermen', '')[:80] if isinstance(tc.input.get('fishermen', ''), str) else '')))
            repeat_count = tool_call_history.count(loop_key)
            tool_call_history.append(loop_key)

            if repeat_count >= 2:
                result = (
                    f'LOOP DETECTED: you have called {tc.name} with these arguments {repeat_count + 1} times. '
                    'Stop retrying. Write your cycle result now and report what blocked you. '
                    'Do not call any more tools.'
                )
                print(f'  [tool] LOOP DETECTED for {tc.name}')
            else:
                result = execute_tool(tc.name, tc.input, files_written)
                # If a write succeeded, reset read history for that path so the agent
                # can read it back once to verify without triggering loop detection.
                if tc.name == 'write_file' and path_arg and result.startswith('OK:'):
                    read_key = ('read_file', path_arg)
                    while read_key in tool_call_history:
                        tool_call_history.remove(read_key)

            tool_results.append({
                'type': 'tool_result',
                'tool_use_id': tc.id,
                'content': result
            })
        messages = [
            initial_message,
            {'role': 'assistant', 'content': response.content},
            {'role': 'user', 'content': tool_results},
        ]

    cycle_status = 'OK' if files_written else ('NO_OUTPUT' if total_tool_calls == 0 else 'FAILED_NO_FILES_WRITTEN')
    print(f'[{team.upper()}] Cycle complete: status={cycle_status}, files_written={len(files_written)}, tool_calls={total_tool_calls}')

    # Append result to supervisor document -- strip code blocks to prevent bloat.
    # Files are written to disk via write_file; no need to embed them here too.
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    separator = f'\n\n---\n\n<!-- AUTO CYCLE {timestamp} -->\n\n'

    # If the cycle produced no file output despite calling tools, add a failure notice
    # so the director briefing picks it up. This makes failures visible immediately.
    failure_notice = ''
    if cycle_status == 'FAILED_NO_FILES_WRITTEN':
        failure_notice = (
            f'\n\n> **CYCLE FAILED [{timestamp}]**: Agent called {total_tool_calls} tool(s) '
            f'but wrote 0 files. The cycle produced no usable output. '
            f'See the report file for details.\n'
        )

    with open(doc_path, 'a', encoding='utf-8') as f:
        f.write(separator + strip_code_blocks(result_text) + failure_notice)

    # Save report (full response, including code, preserved here for reference)
    report_dir = 'reports'
    os.makedirs(report_dir, exist_ok=True)
    date_slug = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    time_slug = datetime.now(timezone.utc).strftime('%H%M')
    report_path = f'{report_dir}/{date_slug}-{team}-{time_slug}.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f'# Hoffman Lenses -- {team.upper()} Cycle Report\n')
        f.write(f'**Date:** {timestamp}\n')
        f.write(f'**Status:** {cycle_status}\n\n')
        f.write(result_text)

    print(f'[{team.upper()}] Report saved to {report_path}')

    # Commit everything: supervisor doc, report, and any files the agent wrote
    all_changed = [doc_path, report_path] + files_written
    if all_changed:
        try:
            subprocess.run(['git', 'add'] + all_changed, check=True)
            commit_msg = (
                f'{team}: auto cycle {date_slug}\n\n'
                f'Files written by agent: {len(files_written)}\n'
                + ('\n'.join(f'  {f}' for f in files_written) if files_written else '  (none)')
            )
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            subprocess.run(['git', 'pull', '--rebase'], check=True)
            subprocess.run(['git', 'push'], check=True)
            print(f'[{team.upper()}] Committed and pushed ({len(files_written)} files written)')
        except subprocess.CalledProcessError as e:
            print(f'[{team.upper()}] Git error: {e}')

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
    import glob
    date_slug = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    reports = glob.glob(f'reports/{date_slug}-*.md')
    reports = [r for r in reports if 'DIRECTOR' not in r]

    if not reports:
        print('No reports found for today')
        return

    combined = []
    for report_path in sorted(reports):
        content = open(report_path, encoding='utf-8').read()
        combined.append(content)

    summary_input = '\n\n---\n\n'.join(combined)

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=2000,
        messages=[{
            'role': 'user',
            'content': f"""You are summarizing the daily activity of the Hoffman Lenses
agent organization for the Director (Norm Robichaud).

Here are today's cycle reports:

{summary_input}

Write a concise director's briefing. Format:

# Hoffman Lenses -- Director Briefing
## {date_slug}

### What got done today
[2-3 sentences per team, only what actually happened -- distinguish clearly between
planning/intent (agent wrote about work) vs actual output (agent wrote files)]

### Files created or modified
[list any actual files the agents wrote; if a report says "NONE" or "FAILED", say so explicitly]

### Decisions needed from you
[anything flagged REQUIRES DIRECTOR REVIEW]

### Things to know
[any cycle marked FAILED or with status FAILED_NO_FILES_WRITTEN should be called out here]

### What happens tomorrow
[what the agents will work on next]
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


# ── Entry point ────────────────────────────────────────────

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

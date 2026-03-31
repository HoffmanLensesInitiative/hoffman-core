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
    'build':       'HOFFMAN_BUILD.md',
    'intel':       'HOFFMAN_INTEL.md',
    'investigate': 'HOFFMAN_INVESTIGATE.md',
    'advocate':    'HOFFMAN_ADVOCATE.md'
}

# ── Tools ─────────────────────────────────────────────────

# Available to all agents
TOOL_WRITE_FILE = {
    'name': 'write_file',
    'description': (
        'Write content to a file in the repository. '
        'Creates parent directories as needed. '
        'Overwrites the file if it already exists. '
        'Use this to create every new file or update every existing file you build. '
        'Do NOT just describe files in text -- call this tool to actually create them.'
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
                'description': 'Complete file content to write'
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
        'Provide a Python dict or list of dicts for each record type. '
        'These will be inserted into the correct list (FISHERMEN, MOTIVES, CATCHES, or EVIDENCE) '
        'and the seed will be run automatically. '
        'Use this instead of write_file for BMID database records.'
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
    'build':       [TOOL_WRITE_FILE],
    'intel':       [TOOL_WRITE_FILE, TOOL_APPEND_SEED],
    'investigate': [TOOL_WRITE_FILE],
    'advocate':    [TOOL_WRITE_FILE],
}

# ── Helpers ───────────────────────────────────────────────

def strip_code_blocks(text):
    """Remove fenced code blocks from agent response before appending to supervisor doc.
    Files are written to disk via write_file tool -- no need to also embed them in the doc."""
    cleaned = re.sub(r'```[^\n]*\n.*?```', '', text, flags=re.DOTALL)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()


def rotate_supervisor_doc(doc_path, keep_cycles=3):
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

def tool_write_file(path, content, files_written):
    """Write a file to disk. Returns status string."""
    try:
        full_path = Path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')
        files_written.append(str(full_path))
        print(f'  [tool] wrote {path} ({len(content)} chars)')
        return f'OK: wrote {len(content)} chars to {path}'
    except Exception as e:
        print(f'  [tool] ERROR writing {path}: {e}')
        return f'ERROR: {e}'


def tool_append_seed(fishermen, motives, catches, evidence, files_written):
    """Append records to seed.py lists and run the seed."""
    seed_path = Path('bmid-api/seed.py')
    if not seed_path.exists():
        return 'ERROR: bmid-api/seed.py not found'

    content = seed_path.read_text(encoding='utf-8')

    additions = []

    def make_block(label, records):
        if not records:
            return ''
        lines = [f'\n    # -- appended by intel agent {datetime.now(timezone.utc).strftime("%Y-%m-%d")} --']
        for rec in records:
            lines.append('    ' + repr(rec) + ',')
        return '\n'.join(lines)

    # Insert before closing ] of each list
    for list_name, records in [
        ('FISHERMEN', fishermen or []),
        ('MOTIVES',   motives   or []),
        ('CATCHES',   catches   or []),
        ('EVIDENCE',  evidence  or []),
    ]:
        if not records:
            continue
        block = make_block(list_name, records)
        # Find last ] that closes the list definition
        marker = f'{list_name} = ['
        start = content.find(marker)
        if start == -1:
            return f'ERROR: could not find {list_name} list in seed.py'
        # Find the matching closing bracket
        depth = 0
        i = start + len(marker)
        close_pos = -1
        while i < len(content):
            if content[i] == '[':
                depth += 1
            elif content[i] == ']':
                if depth == 0:
                    close_pos = i
                    break
                depth -= 1
            i += 1
        if close_pos == -1:
            return f'ERROR: could not find closing ] for {list_name}'
        content = content[:close_pos] + block + '\n' + content[close_pos:]
        additions.append(f'{len(records)} {list_name.lower()}')

    seed_path.write_text(content, encoding='utf-8')
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
    if tool_name == 'write_file':
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
    'build': """You are the Hoffman Lenses Build Agent.

Read the supervisor document above carefully.
It contains your mission, current state, build queue, and build log.

Your task for this cycle:
1. Identify the top item in the BUILD QUEUE
2. Build it -- write complete, working, tested code
3. Use the write_file tool to create EVERY file you build.
   Do not describe files in text -- call write_file for each one.
4. Verify your code (trace through the logic, check for errors)
5. Record what you built, what you tested, and what you found

CRITICAL: You must call write_file for every file you create or modify.
Writing code in your text response without calling write_file accomplishes nothing.
The file does not exist until write_file is called.

IMPORTANT: Do NOT include file contents or code blocks in your text response.
Your response text is appended to the supervisor document -- it must stay concise.
Describe what you built and tested in prose. All code goes through write_file only.

Return your response in this format AFTER calling all write_file tools:

## CYCLE RESULT -- BUILD -- {date}

### What I built
[describe what was created or changed]

### Files written
[list every file written via the write_file tool]

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

Your task for this cycle:
1. Identify the top research target from the INTELLIGENCE QUEUE
2. Research it -- document what is known about this publisher,
   their business model, documented harms, ownership structure
3. Use the append_seed_records tool to add records to the database.
   Do not just write records in your text response -- call append_seed_records.
   The records will not exist in the database until you call that tool.
4. Assign honest confidence scores -- never inflate

CRITICAL: You must call append_seed_records with the actual records.
Every fisherman, motive, catch, and evidence record must be passed
to append_seed_records as a Python dict. Text descriptions accomplish nothing.

After calling append_seed_records, return your response in this format:

## CYCLE RESULT -- INTEL -- {date}

### Target researched
[which fisherman or pattern was researched]

### Records added
[list every record added via append_seed_records]

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

Your task for this cycle:
1. Pick the top investigation from the INVESTIGATION QUEUE
2. Go deep -- follow threads, find primary sources, map connections
3. Use write_file to save your findings as a structured intelligence
   file at reports/investigate-{slug}.md
4. Document unexpected findings as RABBIT HOLE FINDINGS

CRITICAL: Use write_file to save your intelligence file.
Do not just write findings in your response -- call write_file.

Return your response in this format after calling write_file:

## CYCLE RESULT -- INVESTIGATE -- {date}

### Investigation target
[what was investigated]

### Key findings
[factual findings with primary source citations]

### Rabbit hole findings
[unexpected connections discovered]

### Files written
[intelligence file saved via write_file]

### Next cycle recommendation
[which thread to follow next]
""",

    'advocate': """You are the Hoffman Lenses Advocacy Agent.

Read the supervisor document above carefully.
It contains your mission, outreach queue, and contact information.

Your task for this cycle:
1. Review the ADVOCACY QUEUE for the highest priority item
2. Prepare communications, drafts, or research as needed
3. Use write_file to save any drafts at reports/advocate-draft-{slug}.md
4. Monitor for new legal developments, academic papers, or news

IMPORTANT: All family and legal communications must be flagged
as REQUIRES DIRECTOR REVIEW. Never send these autonomously.

Return your response in this format:

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

    client = anthropic.Anthropic(api_key=api_key)
    tools = TOOLS_BY_TEAM.get(team, [])
    messages = [{'role': 'user', 'content': message_content}]
    files_written = []
    result_text = ''

    # Agentic loop -- keep going until no more tool calls
    max_turns = 20
    turn = 0
    while turn < max_turns:
        turn += 1
        response = None
        for attempt in range(1, 4):  # up to 3 attempts per turn
            try:
                response = client.messages.create(
                    model='claude-sonnet-4-6',
                    max_tokens=8000,
                    tools=tools,
                    messages=messages
                )
                break
            except Exception as e:
                print(f'[{team.upper()}] Claude API error (attempt {attempt}/3): {e}')
                if attempt < 3:
                    wait = 15 * attempt
                    print(f'[{team.upper()}] Retrying in {wait}s...')
                    time.sleep(wait)
                else:
                    print(f'[{team.upper()}] All retries exhausted.')
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

        # Execute tool calls and feed results back
        messages.append({'role': 'assistant', 'content': response.content})
        tool_results = []
        for tc in tool_calls:
            print(f'  [tool] calling {tc.name}')
            result = execute_tool(tc.name, tc.input, files_written)
            tool_results.append({
                'type': 'tool_result',
                'tool_use_id': tc.id,
                'content': result
            })
        messages.append({'role': 'user', 'content': tool_results})

    print(f'[{team.upper()}] Got response ({len(result_text)} chars), files written: {len(files_written)}')

    # Append result to supervisor document -- strip code blocks to prevent bloat.
    # Files are written to disk via write_file; no need to embed them here too.
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    separator = f'\n\n---\n\n<!-- AUTO CYCLE {timestamp} -->\n\n'
    with open(doc_path, 'a', encoding='utf-8') as f:
        f.write(separator + strip_code_blocks(result_text))

    # Save report (full response, including code, preserved here for reference)
    report_dir = 'reports'
    os.makedirs(report_dir, exist_ok=True)
    date_slug = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    time_slug = datetime.now(timezone.utc).strftime('%H%M')
    report_path = f'{report_dir}/{date_slug}-{team}-{time_slug}.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f'# Hoffman Lenses -- {team.upper()} Cycle Report\n')
        f.write(f'**Date:** {timestamp}\n\n')
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
[2-3 sentences per team, only what actually happened]

### Files created or modified
[list any actual files the agents wrote]

### Decisions needed from you
[anything flagged REQUIRES DIRECTOR REVIEW]

### Things to know
[anything unexpected, concerning, or worth noting]

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

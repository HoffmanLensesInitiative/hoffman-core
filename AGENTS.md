# Hoffman Lenses -- Agent Automation

Autonomous agent cycles for the Hoffman Lenses Initiative.
Agents run on schedule, do their work, commit results, and
generate a daily director briefing.

---

## Daily schedule (UTC)

| Time  | Agent       | Frequency | What it does |
|-------|-------------|-----------|--------------|
| 08:00 | Intel       | Daily x2  | Research fishermen, populate BMID |
| 10:00 | Build       | Daily     | Extension, hl-detect, API development |
| 12:00 | Advocate    | Mondays   | Outreach prep, legal monitoring |
| 14:00 | Investigate | Daily     | Deep research, rabbit holes |
| 20:00 | Intel       | Daily x2  | Second intel cycle |
| 22:00 | Briefing    | Daily     | Director summary of all activity |

---

## What you do

Check `reports/YYYY-MM-DD-DIRECTOR-BRIEFING.md` each day.
That file tells you:
- What got done
- What decisions need your input
- What's coming tomorrow

Anything marked **REQUIRES DIRECTOR REVIEW** needs your
attention before the agents proceed.

---

## Setup

### 1. Add your Anthropic API key to GitHub

In your `hoffman-core` repository:
- Go to Settings -> Secrets and variables -> Actions
- Click "New repository secret"
- Name: `ANTHROPIC_API_KEY`
- Value: your Anthropic API key

### 2. Add the automation files

Copy these files into `hoffman-core`:
```
.github/workflows/build-cycle.yml
.github/workflows/intel-cycle.yml
.github/workflows/investigate-cycle.yml
.github/workflows/advocate-cycle.yml
.github/workflows/director-briefing.yml
scripts/run_cycle.py
scripts/requirements.txt
```

### 3. Enable GitHub Actions

Go to your repository -> Actions tab -> Enable workflows

### 4. Test manually

Click any workflow -> "Run workflow" button.
Check the Actions tab to see it running.
Check the `reports/` folder for output.

---

## Running manually

From the repository root:
```bash
export ANTHROPIC_API_KEY=your-key-here
pip install anthropic

python scripts/run_cycle.py build       # Run build agent
python scripts/run_cycle.py intel       # Run intel agent
python scripts/run_cycle.py investigate # Run investigation agent
python scripts/run_cycle.py advocate    # Run advocacy agent
python scripts/run_cycle.py all         # Run all agents
python scripts/run_cycle.py summary     # Generate director briefing
```

---

## How to redirect an agent

Edit the relevant supervisor document before the next scheduled run:
- `HOFFMAN_BUILD.md` -- redirect build priorities
- `HOFFMAN_INTEL.md` -- redirect intelligence targets
- `HOFFMAN_INVESTIGATE.md` -- redirect investigation focus
- `HOFFMAN_ADVOCATE.md` -- redirect advocacy activities

The agent reads the document at the start of every cycle.
Change the document, change the agent's behavior.

---

## Cost estimate

Each cycle calls Claude Opus once with ~10-20K context tokens
and receives ~2-4K output tokens.

Approximate cost per cycle: $0.15 - $0.30
Daily total (5 cycles): $0.75 - $1.50
Monthly: $22 - $45

Adjust frequency in the workflow files to manage costs.

---

*Hoffman Lenses Initiative -- hoffmanlenses.org*

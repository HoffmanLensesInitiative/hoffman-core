# hl-detect

Linguistic manipulation pattern detection library.
Part of the [Hoffman Lenses Initiative](https://hoffmanlenses.org).

Takes text as input. Returns structured analysis of manipulation patterns.
Platform-agnostic. DOM-agnostic. No dependencies.

## Usage

```javascript
const hlDetect = require('./src/hl-detect');

const result = hlDetect.detect("They don't want you to see this before it gets deleted");

if (result.flagged) {
  result.patterns.forEach(p => {
    console.log(p.label, '-', p.explanation);
  });
}
```

## Patterns Detected

| Pattern | Severity | Description |
|---------|----------|-------------|
| suppression_framing | danger | Claims content is being hidden or censored |
| false_urgency | warn | Artificial time pressure to prevent critical evaluation |
| incomplete_hook | warn | Withholds information to compel a click |
| outrage_engineering | danger | Language calibrated to produce outrage |
| false_authority | warn | Invokes unnamed, unverifiable authority |
| tribal_activation | warn | Signals group identity as prerequisite for agreement |
| engagement_directive | warn | Explicit instructions to share or amplify |

## Output

```javascript
{
  flagged: true,
  patternCount: 2,
  dominantPattern: 'suppression_framing',
  escalationScore: 57,
  patterns: [
    {
      type: 'suppression_framing',
      severity: 'danger',
      label: 'Suppression framing',
      confidence: 0.75,
      explanation: '...',
      evidence: ["don't want you to see this before it gets deleted"]
    }
  ],
  metadata: { processingTimeMs: 1, textLength: 54, version: '0.1.0' }
}
```

## Testing

```bash
node test/hl-detect.test.js
```

61 tests. All passing.

## License

MIT - Hoffman Lenses Initiative

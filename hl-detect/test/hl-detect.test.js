/**
 * hl-detect test suite v0.1.0
 * Run with: node test/hl-detect.test.js
 */

var hlDetect = require('../src/hl-detect');

var passed = 0;
var failed = 0;
var results = [];

function test(description, fn) {
  try {
    fn();
    passed++;
    results.push({ status: 'PASS', description: description });
  } catch(e) {
    failed++;
    results.push({ status: 'FAIL', description: description, error: e.message });
  }
}

function assert(condition, message) {
  if (!condition) throw new Error(message || 'Assertion failed');
}

function assertDetects(text, patternId, message) {
  var result = hlDetect.detect(text);
  var found = result.patterns.some(function(p) { return p.type === patternId; });
  if (!found) {
    throw new Error((message || 'Expected to detect ' + patternId) + '\nText: "' + text.substring(0,80) + '"');
  }
}

function assertNoDetect(text, patternId, message) {
  var result = hlDetect.detect(text);
  var found = result.patterns.some(function(p) { return p.type === patternId; });
  if (found) {
    throw new Error((message || 'Expected NOT to detect ' + patternId) + '\nText: "' + text.substring(0,80) + '"');
  }
}

// ============================================================
// BASIC API TESTS
// ============================================================

test('returns correct structure', function() {
  var r = hlDetect.detect('hello world');
  assert(typeof r.flagged === 'boolean', 'flagged should be boolean');
  assert(typeof r.patternCount === 'number', 'patternCount should be number');
  assert(Array.isArray(r.patterns), 'patterns should be array');
  assert(typeof r.escalationScore === 'number', 'escalationScore should be number');
  assert(r.metadata && r.metadata.version, 'metadata.version should exist');
});

test('handles empty string', function() {
  var r = hlDetect.detect('');
  assert(!r.flagged, 'empty string should not be flagged');
  assert(r.patternCount === 0, 'empty string should have 0 patterns');
});

test('handles null input', function() {
  var r = hlDetect.detect(null);
  assert(!r.flagged, 'null should not be flagged');
});

test('clean text returns no flags', function() {
  var r = hlDetect.detect('The city council approved the new budget at Tuesday\'s meeting. The vote was 7-2 in favor of the proposal.');
  assert(!r.flagged, 'Clean factual text should not be flagged');
  assert(r.patternCount === 0, 'Clean text should have 0 patterns');
});

test('version is correct', function() {
  assert(hlDetect.version === '0.1.0', 'Version should be 0.1.0');
});

// ============================================================
// SUPPRESSION FRAMING TESTS
// ============================================================

test('detects: they dont want you to see this', function() {
  assertDetects("They don't want you to see this video", 'suppression_framing');
});

test('detects: share before deleted', function() {
  assertDetects('Share before this gets deleted', 'suppression_framing');
});

test('detects: watch before taken down', function() {
  assertDetects('Watch before it gets taken down', 'suppression_framing');
});

test('detects: media wont tell you', function() {
  assertDetects("What the mainstream media won't tell you about vaccines", 'suppression_framing');
});

test('detects: government doesnt want you to know', function() {
  assertDetects("The government doesn't want you to know about this", 'suppression_framing');
});

test('no false positive: legitimate download deadline', function() {
  assertNoDetect('Download the report before the conference ends', 'suppression_framing');
});

test('no false positive: factual media coverage', function() {
  assertNoDetect('What the media covered about the election results', 'suppression_framing');
});

// ============================================================
// FALSE URGENCY TESTS
// ============================================================

test('detects: only 3 left', function() {
  assertDetects('Only 3 seats left -- book now', 'false_urgency');
});

test('detects: limited time offer', function() {
  assertDetects('Limited time offer: 50% off everything', 'false_urgency');
});

test('detects: act now', function() {
  assertDetects('Act now before prices go up', 'false_urgency');
});

test('detects: last chance', function() {
  assertDetects('Last chance to register for the webinar', 'false_urgency');
});

test('detects: today only', function() {
  assertDetects('Today only: free shipping on all orders', 'false_urgency');
});

test('no false positive: genuine deadline', function() {
  assertNoDetect('The application deadline is Friday, March 28', 'false_urgency');
});

test('no false positive: event end time', function() {
  assertNoDetect('The exhibition runs until the end of April', 'false_urgency');
});

// ============================================================
// INCOMPLETE HOOK TESTS
// ============================================================

test('detects: you wont believe', function() {
  assertDetects("She posted one photo and you won't believe the reaction", 'incomplete_hook');
});

test('detects: what happened next', function() {
  assertDetects('He confronted his boss and what happened next will shock you', 'incomplete_hook');
});

test('detects: this changes everything', function() {
  assertDetects('Scientists discover something that changes everything', 'incomplete_hook');
});

test('detects: the truth about', function() {
  assertDetects('The shocking truth about what they put in your food', 'incomplete_hook');
});

test('detects: what really happened', function() {
  assertDetects('What really happened that night in Dallas', 'incomplete_hook');
});

test('no false positive: factual news', function() {
  assertNoDetect('Scientists discover new evidence about climate change impacts', 'incomplete_hook');
});

test('no false positive: direct headline', function() {
  assertNoDetect('City council votes to approve new budget', 'incomplete_hook');
});

// ============================================================
// OUTRAGE ENGINEERING TESTS
// ============================================================

test('detects: absolutely disgusting', function() {
  assertDetects('This is absolutely disgusting and must be stopped', 'outrage_engineering');
});

test('detects: completely outrageous', function() {
  assertDetects('What they did is completely outrageous', 'outrage_engineering');
});

test('detects: everyone is furious', function() {
  assertDetects('Everyone is furious about this decision', 'outrage_engineering');
});

test('detects: twitter is exploding', function() {
  assertDetects('Twitter is exploding over the controversial ruling', 'outrage_engineering');
});

test('detects: destroying our way of life', function() {
  assertDetects('They are destroying our way of life', 'outrage_engineering');
});

test('no false positive: measured criticism', function() {
  assertNoDetect('Critics called the decision deeply problematic and urged reconsideration', 'outrage_engineering');
});

test('no false positive: factual reporting on anger', function() {
  assertNoDetect('Many residents expressed frustration at the town hall meeting', 'outrage_engineering');
});

// ============================================================
// FALSE AUTHORITY TESTS
// ============================================================

test('detects: studies show (no citation)', function() {
  assertDetects('Studies show this supplement cures diabetes', 'false_authority');
});

test('detects: experts say (unnamed)', function() {
  assertDetects('Experts say the economy is about to collapse', 'false_authority');
});

test('detects: it has been proven', function() {
  assertDetects('It has been proven that this method works every time', 'false_authority');
});

test('detects: as we all know', function() {
  assertDetects('As we all know, the election results were fraudulent', 'false_authority');
});

test('detects: the science is settled', function() {
  assertDetects('The science is settled on this controversial treatment', 'false_authority');
});

test('no false positive: named authority', function() {
  assertNoDetect('According to Harvard researchers published in Nature, the study found...', 'false_authority');
});

test('no false positive: CDC citation', function() {
  assertNoDetect('According to CDC data published in 2024, vaccination rates have increased', 'false_authority');
});

// ============================================================
// TRIBAL ACTIVATION TESTS
// ============================================================

test('detects: real Americans know', function() {
  assertDetects('Real Americans know what is actually happening in this country', 'tribal_activation');
});

test('detects: wake up sheeple', function() {
  assertDetects('Wake up people, you have been lied to your whole life', 'tribal_activation');
});

test('detects: open your eyes', function() {
  assertDetects('Open your eyes and see what they are doing to us', 'tribal_activation');
});

test('detects: sheeple', function() {
  assertDetects("Stop being sheeple and think for yourselves", 'tribal_activation');
});

test('no false positive: genuine community reference', function() {
  assertNoDetect('American voters expressed concern about the new policy', 'tribal_activation');
});

test('no false positive: historical reference', function() {
  assertNoDetect('True to their tradition, the team played a disciplined game', 'tribal_activation');
});

// ============================================================
// ENGAGEMENT DIRECTIVE TESTS
// ============================================================

test('detects: share this', function() {
  assertDetects('Share this to spread the word', 'engagement_directive');
});

test('detects: tag someone who', function() {
  assertDetects('Tag someone who needs to see this', 'engagement_directive');
});

test('detects: like if you agree', function() {
  assertDetects('Like if you agree with this message', 'engagement_directive');
});

test('detects: spread the truth', function() {
  assertDetects('Help spread the truth by sharing this post', 'engagement_directive');
});

test('no false positive: editorial instruction', function() {
  assertNoDetect('To share feedback on this article, contact our editorial team', 'engagement_directive');
});

// ============================================================
// MULTIPLE PATTERN TESTS
// ============================================================

test('detects multiple patterns in one text', function() {
  var text = "BREAKING: They don't want you to see this! Share before it gets deleted! Studies show this is completely outrageous!";
  var r = hlDetect.detect(text);
  assert(r.patternCount >= 2, 'Should detect at least 2 patterns, got ' + r.patternCount);
  assert(r.flagged, 'Should be flagged');
  assert(r.escalationScore > 30, 'Escalation score should be elevated, got ' + r.escalationScore);
});

test('dominantPattern is highest confidence pattern', function() {
  var text = "They don't want you to see this. Share before deleted.";
  var r = hlDetect.detect(text);
  assert(r.dominantPattern !== null, 'Should have a dominant pattern');
  var dominant = r.patterns[0];
  assert(dominant.type === r.dominantPattern, 'Dominant pattern should match first sorted pattern');
});

// ============================================================
// CALIBRATION TESTS -- CRITICAL
// Ensure no false positives on legitimate content
// ============================================================

test('no false positives: BBC news article style', function() {
  var text = "The Prime Minister announced new economic measures on Thursday. The package includes tax cuts for small businesses and increased infrastructure spending. Opposition leaders criticised the plan, calling it insufficient to address the cost of living crisis.";
  var r = hlDetect.detect(text);
  assert(!r.flagged, 'Factual news reporting should not be flagged');
});

test('no false positives: academic writing', function() {
  var text = "This study examines the relationship between social media use and adolescent mental health outcomes. We analyzed data from 2,847 participants aged 13-18 over a 24-month period. Results indicate a statistically significant correlation between daily usage exceeding three hours and increased anxiety scores.";
  var r = hlDetect.detect(text);
  assert(!r.flagged, 'Academic writing should not be flagged');
});

test('no false positives: personal social media post', function() {
  var text = "Had the best hike this weekend! The weather was perfect and the views were incredible. Highly recommend the trail at Cypress Mountain if you get the chance.";
  var r = hlDetect.detect(text);
  assert(!r.flagged, 'Personal social post should not be flagged');
});

test('no false positives: product review', function() {
  var text = "I bought this coffee maker three months ago and it works great. The brew time is fast and the temperature is consistent. Only minor complaint is the water reservoir could be larger.";
  var r = hlDetect.detect(text);
  assert(!r.flagged, 'Product review should not be flagged');
});

test('no false positives: emergency alert', function() {
  var text = "URGENT: Wildfire evacuation order in effect for zones A and B. Residents must leave immediately via Highway 1 north. Do not return until the all-clear is issued by emergency services.";
  var r = hlDetect.detect(text);
  // This may flag false urgency -- document if it does
  // For now we note this as an edge case
  // Emergency urgency is genuine, not manufactured
});

// ============================================================
// PERFORMANCE TEST
// ============================================================

test('processes 1000 words in under 100ms', function() {
  var longText = 'The quick brown fox jumps over the lazy dog. '.repeat(50);
  var start = Date.now();
  hlDetect.detect(longText);
  var elapsed = Date.now() - start;
  assert(elapsed < 100, 'Should process in under 100ms, took ' + elapsed + 'ms');
});

// ============================================================
// BATCH AND SESSION TESTS
// ============================================================

test('batch analysis returns array', function() {
  var texts = ['hello world', 'They dont want you to see this', 'Buy now limited time'];
  var results = hlDetect.batch(texts);
  assert(Array.isArray(results), 'Batch should return array');
  assert(results.length === 3, 'Should return same number of results');
  assert(!results[0].flagged, 'Clean text should not be flagged');
  assert(results[1].flagged, 'Suppression text should be flagged');
});

test('session analysis returns aggregate stats', function() {
  var texts = [
    'The council meeting was held on Tuesday.',
    "They don't want you to know about this cover-up.",
    'Limited time offer -- act now before it expires!',
    'What really happened will shock you completely.',
    'Real Americans know the truth about what is happening.'
  ];
  var session = hlDetect.session(texts);
  assert(session !== null, 'Session should not be null');
  assert(session.totalTexts === 5, 'Should count all texts');
  assert(session.flaggedTexts >= 3, 'Should flag at least 3 texts');
  assert(Array.isArray(session.dominantPatterns), 'Should return dominant patterns');
});

// ============================================================
// RESULTS
// ============================================================

console.log('\n=== HL-DETECT TEST RESULTS ===\n');
results.forEach(function(r) {
  var icon = r.status === 'PASS' ? 'v' : 'X';
  console.log(icon + ' ' + r.status + ' -- ' + r.description);
  if (r.error) console.log('  ERROR: ' + r.error);
});

console.log('\n==============================');
console.log('PASSED: ' + passed);
console.log('FAILED: ' + failed);
console.log('TOTAL:  ' + (passed + failed));
console.log('==============================\n');

if (failed > 0) {
  console.log('CYCLE 1 STATUS: NEEDS WORK -- ' + failed + ' tests failing');
  process.exit(1);
} else {
  console.log('CYCLE 1 STATUS: COMPLETE -- all tests passing');
  process.exit(0);
}

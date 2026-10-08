---
lab2_edge_cases:
  E1: {rule: R-08, count: 3}
  E2: {rule: R-06, count: 2}
  E3: {rule: R-09, count: 4}
  E4: {rule: R-10, count: 4}
  E5: {rule: R-12, count: 1}
  E6: {rule: R-13, count: 11}
---
<!-- ai-generated: 100% - drafted with an assistant and checked against the practice fixture and metric specification -->

# Edge cases in the practice event log

## E1 - clock skew produces a negative lead time

- What the log contains: Three shipped commits have timestamps later than the successful production deployment that carries them.
- What a default definition would have done: Dropping those pairs hides shipped work, while retaining negative durations makes the dashboard imply delivery happened before the commit.
- Why the rule is defensible: Clamping to zero preserves each observed delivery without pretending the clock-skewed interval has a meaningful negative length.

## E2 - a revert of a revert

- What the log contains: Two commits are reverts, and the second revert targets the first revert rather than the original change.
- What a default definition would have done: Counting each commit as a separate change would make one original piece of work look like three independent changes on the dashboard.
- Why the rule is defensible: Following the revert chain back to its root keeps the identity of the underlying change stable instead of inflating change counts.

## E3 - a hotfix that never touched `main`

- What the log contains: Four distinct commits on hotfix branches are carried by production deployments inside the observation window.
- What a default definition would have done: Filtering to `main` would omit real production work and make the measured lead-time sample look better or smaller than reality.
- Why the rule is defensible: Production exposure, not a repository branch name, determines whether a commit reached users and belongs in the delivery metric.

## E4 - a deployment with zero linked commits

- What the log contains: Four production deployments inside the window have an empty commits list.
- What a default definition would have done: Removing them would understate deployment frequency and silently change the denominators for instability rates.
- Why the rule is defensible: A production deployment is still an operational event even when its payload is not linked to commits, so it remains in deployment-level metrics.

## E5 - a deployment that failed and never recovered

- What the log contains: One failed production deployment has no covering incident with a resolution event.
- What a default definition would have done: Inventing a recovery at the window boundary fabricates a duration; dropping the failure hides instability from the failure rate.
- Why the rule is defensible: The recovery median should use only observed recoveries, while the open failure remains visible in the failure count and failure rate.

## E6 - overlapping incidents

- What the log contains: Eleven unordered pairs of distinct incident intervals overlap in time.
- What a default definition would have done: Merging incidents or summing their wall-clock durations would distort recovery and make the dashboard report time that no single failed deployment experienced.
- Why the rule is defensible: Recovery belongs to each failed deployment and its selected covering incident; overlap is separately counted rather than used to combine unrelated intervals.

## Gaming demonstration

The improved metric is `deployment_frequency_per_day`, using R-11. I added 18 production deployments with no linked commits and moved five successful base deployments to the instant at the end of the observation window. The added events increase the deployment count, although they deliver no changes, while the moved deployments make seven existing changes miss the window. A team rewarded only for deployment frequency could be encouraged to split out empty production pushes and defer real work; the team or manager whose score is based on that count would look more productive while users receive fewer changes.
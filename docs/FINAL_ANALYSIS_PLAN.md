# Phase 11 final analysis plan

Declared before reserved-seed final data collection. Final controller design
and training budget still require disposition of the development validation.
No original or development record is used as a final test replicate.

Use at least five independent, previously unused master training seeds and
all 25 configured loss/delay combinations. Pair traffic demand across all
methods for each seed. Hold out loss 0.3 and delay 1000 ms from robust training.
Use fresh training, frozen deterministic evaluation, matched budgets/rewards/
observations/exploration, nine policy variants and five communication rules.
The local policy is evaluated once per master seed; it does not receive a
pretend set of independent communication-condition replicates.

Report every cell, censoring, departed/expected/completed demand, waiting,
completed-trip travel, queue, stops, reward, packet attempts/deliveries/drops/
pending packets, payload bytes, message age/delay and action influence.
Packet reduction is relative to the same checkpoint under always-transmit.
Per-condition waiting degradation is `(impaired-ideal)/ideal * 100`; return
undefined when the reference is zero. Throughput degradation reverses the
numerator. Absolute metrics always accompany relative metrics.

The independent sampling unit is the master seed. Average repeated conditions
within seed before model comparisons. Report means, sample SD and descriptive
95% Student-t intervals across seed differences. These intervals are not
simultaneous and do not establish equivalence. A single traffic stream per
master seed limits within-policy traffic-uncertainty characterization.

The following **13 comparisons form one prespecified test family**:

1. Plain ideal-trained: 30% loss / zero delay minus ideal waiting.
2. Plain ideal-trained: zero loss / 1000 ms delay minus ideal waiting.
3. Plain ideal-trained: 30% loss / 1000 ms minus ideal waiting.
4. Plain ideal-trained: combined minus loss-only minus delay-only plus ideal
   waiting (interaction contrast).
5. Full robust minus plain robust waiting, averaged over all 25 cells.
6. Full robust minus full ideal waiting over the nine extreme held-out cells.
7. Action-sensitive minus periodic-pull waiting on the same full robust model.
8. The same comparison for packet attempts.
9. The same comparison for completion fraction.
10. No-age minus full robust waiting over all 25 cells.
11. No-availability minus full robust waiting over all 25 cells.
12. No-decay minus full robust waiting over all 25 cells.
13. No-stale minus full robust waiting over all 25 cells.

Use exact two-sided sign-flip tests on seed-level paired effects and Holm
familywise adjustment at 0.05. Sign flipping requires exchangeability/symmetry
under the null; report this assumption and do not overinterpret tiny samples.
With five seeds the minimum two-sided exact p is 0.0625, so this design cannot
produce a rejection even before correction. This limitation is explicit;
the purpose is estimation and honest small-sample reporting, not forcing
statistical significance. All other comparisons are descriptive.

An unchanged waiting mean is not proof of noninferiority or equivalence.
Communication savings with unfinished trips or weak controllers do not alone
support H5. A failure to reject a null does not confirm robustness or absence
of impairment effects. No favorable finding is required to retain a record.

Generate heatmaps, communication/traffic trade-off, component-ablation and
learning-curve figures from stored records. Check exact design coverage,
checkpoint/source hashes, frozen policies, demand pairing and raw metric
recomputation before interpretation. Preserve every attempt and archive the
configuration, source identity, dependencies, checkpoints and raw data.

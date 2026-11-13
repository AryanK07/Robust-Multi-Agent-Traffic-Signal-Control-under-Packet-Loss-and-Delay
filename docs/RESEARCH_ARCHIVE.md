# Research record preservation and reproduction

The original Phase 11 campaign, its separate audit, and all follow-up studies
are separate records. Keep unfavorable outcomes, censored episodes and every
attempt. A successful program run does not mean successful traffic control.
Phase 12 is not started by creating this archive.

## Archive contents and verification

`scripts/archive_research.py` includes only these repository-relative roots:

- `results/phase11/`: original checkpoints, training/evaluation and analysis.
- `results/phase11_audit_v1/`: independent audit, original hashes and separate
  corrected replays.
- `results/followup_v2/`: every development and reserved-seed campaign,
  including manifests, raw JSON, training logs, checkpoints, generated demand,
  tripinfo, derived statistics and figures.
- `source/repository.bundle`: all source history reachable from the archived
  HEAD, including the source commits recorded by the experiments.

The ZIP contains `archive_manifest.json`, with the exact byte length and
SHA-256 of every other entry. A separate `.sha256.json` file records the ZIP
digest, file count and source commit. Verification checks the complete entry
inventory and every content hash without extracting files. Archive creation
also verifies the Git bundle and rechecks source data after copying. It
refuses an existing output, a dirty source tree or an output inside its own
input roots. It never overwrites raw data or an existing archive.

Finish all campaigns and analysis, inspect the input inventory, and commit
the reviewed source before building. Independently run the campaign audits
before archiving; archive hash consistency alone does not establish scientific
validity. Archives belong outside the input roots and are ignored by Git:

```powershell
python scripts/archive_research.py results/research_archives/phase11-records-v1.zip
python scripts/archive_research.py results/research_archives/phase11-records-v1.zip --verify
```

Publish the ZIP and its digest together as a versioned repository release
asset, preserving previous versions. Check the uploaded size and SHA-256
against the local verified copy. An off-machine archive is a research backup,
not a claim that the findings are favorable or publication-ready.

## Restore and reproduce

1. Download the ZIP and its checksum record from the recorded release. Check
   the ZIP SHA-256, then run `archive_research.py --verify` on a trusted clone
   of the source. Keep the downloaded archive unchanged.
2. Extract the verified ZIP into a new directory. Restore source history with
   `git clone source/repository.bundle restored-project` from that directory.
   Copy the extracted `results` directory into that new clone, without
   replacing another experiment directory.
3. Use Python 3.14 and SUMO 1.27.1 for the measured environment. Create a clean
   virtual environment, install `requirements-research-lock.txt`, and install
   the project with `python -m pip install -e . --no-deps`. The optional
   in-process SUMO backend and its supporting packages are pinned in the lock.
4. Audit each complete follow-up with
   `python scripts/audit_followup.py results/followup_v2/<campaign>`.
   Regenerate the reserved-seed statistics/figures with
   `python scripts/analyze_final.py results/followup_v2/reserved_final_001`.
   These commands write derived outputs only; original raw records stay intact.
5. To repeat data collection, use a clean checkout of the source commit named
   in that campaign's `manifest.json`, its recorded configuration and a **new**
   output directory. For the reserved final campaign the source is `c9547d6`
   and configuration is `configs/phase11_reserved_final.yaml`. Do not resume
   an old directory under a different source or configuration identity.

The old Phase 11 records contain a documented source-provenance gap; archiving
does not repair their historical metadata. New campaigns record complete
source/configuration identities. Dependency locking records the measured
environment; it is not evidence that every OS or future package index will
reproduce floating-point trajectories identically.

The release location and verified digest will be recorded with the completed
Phase 11 readiness report after the final campaign is finished and audited.

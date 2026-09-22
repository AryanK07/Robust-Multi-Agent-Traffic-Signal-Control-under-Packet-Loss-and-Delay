# AGENTS.md

## Repository

**Project:**

Robust Multi-Agent Traffic Signal Control under Packet Loss and Delay

**GitHub repository:**

https://github.com/AryanK07/Robust-Multi-Agent-Traffic-Signal-Control-under-Packet-Loss-and-Delay

---

# 1. Purpose

You are the primary software-development agent for this research project.

Your responsibility is to incrementally build, test, document, evaluate, and maintain the project described in `PROJECT_SPEC.md`.

`PROJECT_SPEC.md` is the authoritative specification for:

- Research objective
- Research questions
- Hypotheses
- Architecture
- Methodology
- Experimental design
- Evaluation
- Project phases
- Research contribution

This file is the authoritative specification for:

- Agent behavior
- Coding workflow
- Testing workflow
- Git workflow
- Documentation workflow
- Safety and reproducibility
- Repository maintenance

If these instructions conflict with an existing implementation, preserve the research requirements in `PROJECT_SPEC.md` unless a human explicitly approves a change.

---

# 2. Core Principle

Build the project incrementally.

**DO NOT attempt to implement the entire project in a single operation.**

The correct workflow is:

```text
Inspect
   ↓
Plan
   ↓
Implement small unit
   ↓
Test
   ↓
Fix
   ↓
Document
   ↓
Commit
   ↓
Push
   ↓
Next unit
```

The project must always remain in a runnable state whenever reasonably possible.

---

# 3. First Action

When starting work in this repository:

1. Inspect the current directory.
2. Inspect Git status.
3. Inspect recent Git history.
4. Read `PROJECT_SPEC.md`.
5. Read this `AGENTS.md`.
6. Inspect the existing project structure.
7. Inspect existing tests.
8. Inspect dependency configuration.
9. Determine the current project phase from `PROJECT_STATUS.md`.
10. Continue from the current state rather than rebuilding existing work.

Do not delete or replace existing implementation merely because you would personally structure it differently.

---

# 4. Research Integrity

This is a research project.

All implementation and experimentation must maintain scientific integrity.

## Never:

- Fabricate results
- Fabricate experiment outputs
- Fabricate benchmark values
- Fabricate citations
- Fabricate statistical significance
- Fabricate successful training
- Claim an experiment was run when it was not
- Claim a hypothesis was confirmed without evidence
- Delete unfavorable results
- Cherry-pick favorable random seeds
- Modify raw results manually
- Backdate Git commits
- Create fake GitHub activity
- Create empty commits solely to make the contribution graph greener

## Always:

- Record actual results
- Preserve raw experiment outputs
- Record random seeds
- Record configurations
- Record relevant Git commit hashes
- Document failed experiments when important
- Distinguish measured results from assumptions
- Preserve reproducibility

---

# 5. GitHub Development Policy

GitHub is the project's actual development repository.

Meaningful development should be committed and pushed regularly.

The purpose is to maintain a genuine, transparent engineering and research history.

## After every meaningful implementation unit:

```text
1. Implement
2. Test
3. Review diff
4. Update documentation
5. Commit
6. Push
```

Do not wait until the entire phase is complete before committing all changes.

However, do not create meaningless micro-commits for every trivial edit.

A meaningful implementation unit is something such as:

```text
Add SUMO environment
Implement observation extraction
Implement signal controller
Add communication abstraction
Implement packet loss
Implement delay queue
Add stale-message handling
Add robustness mechanism
Add experiment runner
Add evaluation metrics
Add statistical analysis
```

---

# 6. Git Safety

Before committing:

```bash
git status
git diff
git diff --staged
```

Verify that:

- Only intended files are changed
- No secrets are present
- No virtual environment is included
- No unnecessary generated files are included
- No large temporary files are included
- No raw credentials are included

Before pushing:

```bash
git log --oneline -5
git status
```

The working tree should be understood before pushing.

---

# 7. Commit Message Convention

Use concise conventional-style commit messages.

Preferred prefixes:

```text
feat:
fix:
test:
refactor:
docs:
experiment:
analysis:
chore:
perf:
```

Examples:

```text
feat: initialize SUMO traffic environment

feat: implement intersection observation extraction

feat: add decentralized signal controller

test: add environment lifecycle tests

feat: add inter-agent communication layer

feat: implement configurable packet loss

feat: implement configurable communication delay

feat: add stale message tracking

feat: implement message reliability features

experiment: add packet loss benchmark

experiment: add delay benchmark

experiment: add combined impairment benchmark

analysis: add robustness degradation metrics

test: add reproducibility checks

docs: document communication model

fix: correct delayed message timestamp handling
```

Do not use vague messages such as:

```text
update
changes
stuff
final
final2
working
test
new version
```

---

# 8. Commit Granularity

Prefer:

```text
One logical change = One commit
```

For example:

```text
feat: add communication message model
```

followed by:

```text
test: add communication message tests
```

followed by:

```text
feat: add packet loss simulation
```

This produces a readable development history.

Do not combine unrelated changes into one large commit.

---

# 9. Push Policy

Push meaningful completed work to GitHub.

Preferred workflow:

```bash
git add <specific files>
git commit -m "<meaningful message>"
git push
```

Do not use broad destructive commands such as:

```bash
git reset --hard
git clean -fd
```

unless explicitly required and safe.

Never force-push unless explicitly authorized.

Do not rewrite published project history merely to make it look cleaner.

---

# 10. Branch Policy

For normal project development, use the repository's main development branch.

If the repository already uses:

```text
main
```

continue using it unless there is a strong reason to introduce another branch.

For major experimental features, branches may be used if helpful.

Do not create excessive branches for trivial changes.

Never delete meaningful branches or commits without authorization.

---

# 11. Phase-Based Development

The project follows the phases defined in `PROJECT_SPEC.md`.

Expected order:

```text
Phase 0
Development setup
      ↓
Phase 1
SUMO environment
      ↓
Phase 2
Single-agent RL
      ↓
Phase 3
Multi-agent RL
      ↓
Phase 4
Communication simulator
      ↓
Phase 5
Packet loss
      ↓
Phase 6
Communication delay
      ↓
Phase 7
Combined impairment
      ↓
Phase 8
Robustness mechanism
      ↓
Phase 9
Robust training
      ↓
Phase 10
Adaptive communication
      ↓
Phase 11
Final experiments
      ↓
Phase 12
Research documentation
```

Do not skip foundational phases merely to reach the advanced features faster.

---

# 12. Phase Completion Criteria

A phase is complete only when:

- Required implementation exists
- Relevant tests pass
- Documentation is updated
- Configuration is documented
- No known critical errors remain
- Reproducibility requirements are satisfied
- `PROJECT_STATUS.md` is updated
- `CHANGELOG.md` is updated
- The phase is committed
- The phase is pushed to GitHub

Then proceed to the next phase.

---

# 13. Human Approval Points

Request human confirmation before:

- Changing the research question
- Changing the project title
- Removing a major research component
- Replacing the main MARL approach
- Changing the primary evaluation metrics
- Removing a required experiment
- Changing research hypotheses
- Introducing a substantially different research contribution
- Making a final claim about novelty
- Making a claim of superiority
- Declaring the project publication-ready
- Changing the experimental protocol after substantial experiments have already been run

Routine implementation decisions do not require approval.

---

# 14. Coding Standards

Write maintainable Python.

Prefer:

- Clear function names
- Clear class names
- Type hints where useful
- Docstrings for important public functions/classes
- Small functions
- Modular components
- Configuration-driven behavior
- Explicit interfaces
- Meaningful variable names
- Minimal global state

Avoid:

- Giant files
- Giant functions
- Hidden global state
- Hard-coded experiment parameters
- Duplicate code
- Unnecessary abstraction
- Unused dependencies
- Dead code

---

# 15. Architecture Rules

Keep these components logically separated:

```text
SUMO Environment
      ↓
Traffic State Extraction
      ↓
Agent
      ↓
Communication Layer
      ↓
Communication Impairment
      ↓
Robustness Processing
      ↓
Policy
      ↓
Traffic Signal Action
```

Do not tightly couple:

- SUMO code with packet-loss logic
- Packet-loss logic with neural-network code
- Experiment logic with environment internals
- Plotting logic with training logic

Each component should be testable independently where practical.

---

# 16. Configuration Rules

Experiment parameters must not be unnecessarily hard-coded.

Prefer:

```text
configs/
```

with YAML configuration.

Parameters such as:

- Packet-loss probability
- Delay
- Simulation duration
- Learning rate
- Number of episodes
- Random seed
- Traffic demand
- Network configuration
- Reward weights

must be configurable.

The same code should support multiple experimental conditions without source-code modification.

---

# 17. Random Seeds

All stochastic components must support reproducible seeds.

Record seeds for:

- Python
- NumPy
- PyTorch
- Communication simulation
- Traffic generation where applicable
- Environment randomness

If SUMO has a relevant random seed configuration, configure it as well.

Every experiment must record its seed.

---

# 18. Testing Policy

Tests are mandatory.

Use `pytest` unless the repository has a justified alternative.

At minimum test:

### Environment

- Initialization
- Reset
- Step
- Action validation
- State extraction
- Reward calculation

### Communication

- Message creation
- Message delivery
- Packet loss
- Delay
- Message age
- Missing messages
- Message ordering

### Agents

- Observation shape
- Action shape
- Forward pass
- Training step

### Evaluation

- Metric calculations
- Aggregation
- Degradation calculation
- Result serialization

Every bug discovered during development should be considered for a regression test.

---

# 19. Test Before Commit

Before committing a logical change:

1. Run the smallest relevant tests.
2. Fix failures.
3. Run broader tests if appropriate.
4. Inspect the diff.
5. Commit.

Before phase completion:

```bash
pytest
```

or the project's equivalent full test command.

Do not commit known failing tests unless the failure is documented and the commit specifically represents work in progress.

---

# 20. SUMO Rules

The SUMO environment must be reproducible.

Do not rely on manually configured GUI state.

Prefer:

- Configuration files
- Scripted simulation startup
- Programmatic traffic generation
- Programmatic signal control
- Automated metric collection

The project must eventually be runnable by another researcher using the documented setup procedure.

---

# 21. Communication Simulation Rules

Packet loss and delay must be implemented in a dedicated communication abstraction.

Do not fake communication impairment by randomly modifying traffic metrics.

Packet loss must affect actual message delivery.

Delay must affect actual message timing.

Message age must be derived from timestamps.

Example:

```text
message_generation_time
current_simulation_time
        ↓
message_age
```

The simulation must preserve causal ordering.

---

# 22. Baseline Integrity

The baseline is a scientific reference.

Once the baseline has been validated:

- Preserve it
- Tag or clearly identify it
- Do not silently modify it
- Use it consistently in comparisons

If a baseline must be corrected because of a genuine implementation bug, document the correction and rerun affected experiments.

---

# 23. Proposed Method Integrity

The proposed robustness mechanism must be independently switchable.

The system should support configurations such as:

```yaml
model:
  robustness_enabled: false
```

and:

```yaml
model:
  robustness_enabled: true
```

This allows controlled comparisons.

Do not change the baseline and proposed model simultaneously in a way that prevents attribution of performance differences.

---

# 24. Ablation Requirements

If the proposed method contains multiple components, implement configuration switches so components can be disabled.

For example:

```text
Baseline
    ↓
+ message availability
    ↓
+ message age
    ↓
+ reliability information
    ↓
Full method
```

The architecture must allow these comparisons without rewriting the system.

---

# 25. Experiment Execution

Experiments should eventually be executable through scripts.

Example:

```bash
python experiments/run_packet_loss.py --config configs/packet_loss.yaml
```

or:

```bash
python scripts/run_experiment.py --config configs/packet_loss.yaml
```

Avoid requiring manual editing of source files between experiments.

---

# 26. Experiment Reproducibility

Each completed experiment should save:

```text
config.yaml
metrics.csv
summary.json
metadata.json
```

where appropriate.

Metadata should include:

```text
experiment name
timestamp
Git commit
random seed
environment configuration
communication configuration
training configuration
evaluation configuration
```

The exact schema may evolve.

---

# 27. Raw Results

Separate raw results from generated analysis.

Preferred:

```text
results/
    experiment_name/
        raw/
        processed/
        plots/
```

Do not manually alter raw result files.

Analysis scripts should consume raw data and generate processed results.

---

# 28. Statistical Analysis

When comparing models:

- Use the same traffic scenarios where appropriate
- Use the same evaluation seeds where appropriate
- Report sample size
- Report mean
- Report variability
- Use appropriate statistical tests when justified

Do not select statistical methods merely because they produce a desirable result.

If assumptions of a statistical test are not satisfied, document the limitation.

---

# 29. Documentation

Maintain these documents:

```text
README.md
PROJECT_SPEC.md
AGENTS.md
PROJECT_STATUS.md
CHANGELOG.md
EXPERIMENT_LOG.md
```

Additional documentation may be placed in:

```text
docs/
```

Important architecture changes must be documented.

---

# 30. README Requirements

The README should eventually include:

1. Project title
2. Research motivation
3. Problem statement
4. Architecture overview
5. Features
6. Installation
7. SUMO setup
8. Usage
9. Training
10. Evaluation
11. Experiments
12. Results
13. Reproducibility
14. Project structure
15. Limitations
16. Citation information when available

Do not add final performance claims until final experiments are complete.

---

# 31. PROJECT_STATUS.md

After every meaningful phase milestone, update:

```text
# Project Status

## Current Phase

## Completed

## In Progress

## Upcoming

## Tests

## Experiments

## Known Issues

## Latest Commit
```

Keep the document factual.

---

# 32. CHANGELOG.md

Record meaningful changes.

Example:

```text
## [Unreleased]

### Added
- Communication abstraction
- Configurable packet loss

### Changed
- Improved environment reset

### Fixed
- Corrected message timestamp handling
```

Do not list fabricated improvements.

---

# 33. EXPERIMENT_LOG.md

Every substantial experiment should have a record containing:

```text
Experiment ID
Date
Git commit
Configuration
Random seeds
Traffic scenario
Network
Packet loss
Delay
Training settings
Evaluation settings
Metrics
Observations
Limitations
```

Do not record numerical values until the experiment actually runs.

---

# 34. Literature and Citations

When implementing an algorithm based on published research:

- Identify the original paper
- Record the citation
- Document relevant methodological assumptions
- Do not claim to reproduce a paper unless the implementation is actually comparable

Do not fabricate bibliographic information.

If literature verification is required and web access is available, verify the source before making a research claim.

---

# 35. Research Novelty

The agent must not automatically describe the project as:

```text
first
novel
state-of-the-art
best
superior
unprecedented
```

unless such a claim is explicitly supported and approved.

Use precise language:

```text
implemented
evaluated
investigated
measured
compared
observed
```

Research novelty must be established through literature review and experimental differentiation.

---

# 36. Performance Claims

Do not write:

```text
Our method improves performance by 30%.
```

until the experiment has actually produced that result.

Instead, before experimentation use:

```text
The experiment will evaluate whether the proposed method improves performance.
```

After experimentation:

```text
The experiment measured a X% difference under condition Y.
```

Only make claims supported by actual data.

---

# 37. Handling Failed Experiments

If an experiment fails:

1. Save the error information.
2. Diagnose the cause.
3. Fix the implementation if appropriate.
4. Rerun the experiment.
5. Document important failures.

Do not hide failed experiments.

A failed experiment may reveal an important implementation or methodological issue.

---

# 38. Dependency Management

Before adding a dependency:

1. Check whether existing dependencies already provide the required functionality.
2. Prefer mature packages.
3. Avoid unnecessary dependencies.
4. Add the dependency to the correct project configuration.
5. Update documentation if installation changes.

Never install random packages solely to solve a problem without understanding their role.

---

# 39. Security

Never commit:

- API keys
- GitHub tokens
- SSH private keys
- Passwords
- Credentials
- `.env` files containing secrets
- Private configuration

Use environment variables for secrets when necessary.

Before every push, inspect staged files for accidental credentials.

---

# 40. Generated Files

Do not commit:

- Virtual environments
- Python cache files
- IDE-specific temporary files
- Large temporary logs
- Temporary SUMO outputs
- Model checkpoints unless intentionally selected
- Massive datasets
- OS-specific metadata

Use `.gitignore`.

If a generated artifact is scientifically necessary, document why it is committed.

---

# 41. Computational Resources

The project must remain practical for a student development environment.

Start with:

```text
small network
short simulations
small training runs
few seeds
```

for development.

Only increase:

```text
network size
simulation duration
episodes
number of seeds
```

after correctness is established.

Do not waste computation on experiments that have not passed basic validation.

---

# 42. Debugging Strategy

When something fails:

```text
Reproduce
   ↓
Read traceback
   ↓
Identify root cause
   ↓
Fix smallest responsible component
   ↓
Add regression test
   ↓
Run tests
   ↓
Continue
```

Do not make unrelated changes while debugging.

Avoid "fixes" that merely suppress the error.

---

# 43. Avoid Overengineering

The project is a research project, not a production-scale distributed system.

Prefer:

```text
simple
modular
testable
reproducible
interpretable
```

over:

```text
massive
complex
opaque
unnecessary
```

Do not introduce GNNs, Transformers, LLMs, federated learning, or other advanced architectures unless they directly support the research question and have a documented justification.

---

# 44. Adaptive Communication Rules

If Phase 10 is implemented:

The system must measure both:

```text
Traffic performance
+
Communication cost
```

Do not claim adaptive communication is successful solely because it sends fewer messages.

Evaluate the trade-off between:

```text
communication volume
vs.
traffic-control performance
```

---

# 45. Generalization Rules

When testing robustness to unseen communication conditions:

Clearly distinguish:

```text
Training conditions
```

from:

```text
Testing conditions
```

Do not accidentally train on the test conditions.

The experiment configuration must make this distinction explicit.

---

# 46. Final Experiment Lock

Before the final experimental campaign:

1. Freeze the baseline implementation.
2. Freeze the proposed methodology.
3. Define experiment configurations.
4. Define metrics.
5. Define random seeds.
6. Define evaluation scenarios.
7. Record the Git commit.
8. Run experiments.
9. Do not change methodology based on individual results unless the change is documented and the affected experiments are rerun.

---

# 47. Final Results Policy

Final figures and tables must be generated from stored experiment data.

Preferred workflow:

```text
Raw experiment data
        ↓
Analysis script
        ↓
Processed data
        ↓
Plot generation
        ↓
Publication figures
```

Never manually type experimental values into plots or tables.

---

# 48. Recruiter-Facing Repository Quality

The repository should eventually make it easy for a technical reviewer or recruiter to understand:

```text
What is the problem?
        ↓
Why does it matter?
        ↓
What did you build?
        ↓
How does it work?
        ↓
How was it evaluated?
        ↓
What did you learn?
        ↓
Can I reproduce it?
```

Maintain a professional README.

Use meaningful commits.

Keep the repository organized.

Keep documentation synchronized with implementation.

The Git history must represent genuine development.

---

# 49. Current-Phase Discipline

Always determine the current phase before implementing new work.

If:

```text
Phase 1 is incomplete
```

do not jump directly to:

```text
Phase 8
```

unless there is a specific reason.

If a future feature is prototyped early, clearly mark it as experimental and do not allow it to destabilize the main development path.

---

# 50. Completion Report

After completing a meaningful development unit, report:

```text
Implementation:
- What was added

Tests:
- Tests executed
- Result

Documentation:
- Files updated

Git:
- Commit message
- Commit hash
- Push status

Next:
- Next logical development unit

Approval required:
- Yes/No
```

Keep the report concise.

---

# 51. Phase Completion Report

At the end of a phase, report:

```text
Phase:
Status:

Implemented:
- ...

Tests:
- ...

Experiments:
- ...

Documentation:
- ...

Git commit:
- ...

GitHub push:
- ...

Known issues:
- ...

Next phase:
- ...
```

Do not claim phase completion if acceptance criteria are not satisfied.

---

# 52. Initial Execution Instruction

When this `AGENTS.md` and `PROJECT_SPEC.md` are first added to the repository:

**Start with Phase 0 only.**

Do not implement the MARL system immediately.

First:

```text
1. Inspect repository
2. Inspect Git state
3. Verify Python
4. Verify Git
5. Verify SUMO
6. Create project structure
7. Create dependency configuration
8. Create .gitignore
9. Configure tests
10. Create/update README
11. Create PROJECT_STATUS.md
12. Create CHANGELOG.md
13. Create EXPERIMENT_LOG.md
14. Verify basic environment
15. Run tests
16. Review changes
17. Commit
18. Push
```

After Phase 0 is verified, stop and report the status before proceeding to Phase 1 unless autonomous continuation has explicitly been requested.

---

# 53. Non-Negotiable Rules

The following rules always apply:

```text
1. Do not fabricate research results.
2. Do not fabricate GitHub activity.
3. Do not create empty commits to increase activity.
4. Do not backdate commits.
5. Do not hide failed experiments.
6. Do not commit secrets.
7. Do not silently change research methodology.
8. Do not remove tests to make the project pass.
9. Do not hard-code experiment results.
10. Do not claim novelty without evidence.
11. Do not claim superiority without experimental evidence.
12. Do not skip foundational validation.
13. Keep experiments reproducible.
14. Keep Git history truthful.
15. Push genuine meaningful progress regularly.
16. Preserve working functionality when adding new features.
17. Prefer simple, interpretable research mechanisms.
18. Document important decisions.
19. Treat PROJECT_SPEC.md as the research specification.
20. Treat this AGENTS.md as the development workflow specification.
```

---

# 54. Final Objective

The final repository should represent a genuine progression from:

```text
Basic SUMO environment
        ↓
Working RL controller
        ↓
Multi-agent controller
        ↓
Inter-agent communication
        ↓
Packet loss
        ↓
Communication delay
        ↓
Combined impairment
        ↓
Robustness mechanism
        ↓
Adaptive communication
        ↓
Systematic experiments
        ↓
Statistical analysis
        ↓
Research conclusions
```

Every stage must be supported by real implementation, testing, documentation, and Git history.

The goal is to produce a repository that is:

- Technically sound
- Scientifically reproducible
- Professionally organized
- Easy to inspect
- Easy to reproduce
- Suitable as the foundation for a research paper
- Demonstrative of genuine software-engineering and research work

**Begin with Phase 0.**
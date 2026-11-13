# Predeclared training validation, 2026-11-13

The user authorized completing the remaining Phase 11 prerequisites. Phase 12
remains unstarted. No previous campaign is changed or relabeled.

## Stage 1: additional training without a methodology change

Freeze `configs/training_validation_v1.yaml` before collection. Use the
unchanged v2 observations, reward, action constraints and linear IQL learner.
Five variants (local, plain ideal/robust, full ideal/robust), development seeds
31001/31002, 81 episodes, and checkpoints at 9/27/81 episodes give complete
cycles of the nine robust training conditions. The 20-vehicle, 120-second
scenario and all learner hyperparameters remain those of the development
pilot. No individual seed or checkpoint will be discarded.

At each checkpoint, evaluate separate frozen policy copies on ideal and
10%-loss/250-ms conditions using a separate validation seed domain (303,
versus training 101 and evaluation 202). Validation must not advance training
exploration RNG. Inspect completion, per-vehicle waiting, switching, reward
and TD-error curves. The final exploratory evaluation also includes the
30%-loss/1000-ms held-out cell. These remain development observations.

The feasibility criterion is at least 95% trip completion in every validation
cell at episode 81 for the five core variants and both development seeds.
Report all three checkpoints, including failures. This criterion establishes
basic controller usability, not convergence or superiority. If it fails,
diagnose observation/action/reward limitations before committing to a large
final campaign. Do not continue raising budgets until favorable outcomes
appear. Any justified representation correction requires a new version,
matched baselines, tests and a predeclared development comparison.

## Runtime equivalence

Use SUMO 1.27.1 with its official optional `libsumo` interface; one simulation
per worker process, two workers. The regression test runs a complete matched
120-second training trajectory through socket TraCI and libsumo, asserting
identical metrics and exact learned weights/biases. Both interfaces passed.
This is an execution optimization, not a different simulator model. The
original interface remains the default for existing configurations.

Install the pinned optional dependencies with `pip install -e ".[dev,research]".
The package installer initially resolved newer support packages; all four
SUMO packages were then pinned to 1.27.1 before tests and data collection.
Record package versions and source identity in each campaign manifest.
Official documentation: [Libsumo](https://sumo.dlr.de/docs/Libsumo.html).

After committing, execute:

```powershell
python scripts/run_followup.py --mode run --config configs/training_validation_v1.yaml --output results/followup_v2/training_validation_001
```

Later prerequisites are a reserved-seed final protocol, all 25 impairment
cells, required baselines and component ablations, paired seed analysis,
prespecified multiplicity handling, figures generated from raw records,
broader literature comparison, and a reproducibility archive. The final
configuration and budget will be frozen only after development diagnosis.
An unfavorable result remains a result; positive hypotheses are not an
acceptance requirement.

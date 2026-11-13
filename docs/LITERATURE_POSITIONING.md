# Literature comparison for Phase 11 readiness

Checked 2026-11-13. This is an engineering/research audit note, not a paper
draft or an exhaustive systematic review. Searches covered action-value
margins, request-based MARL communication, event triggering, message
certification, latency/value of information, and impaired traffic control.
Only primary papers support the comparisons below. No benchmark numbers
from different environments are used to rank this project.

| Primary source | Relevant established idea | Relationship to this project |
|---|---|---|
| Singh, Jain and Sukhbaatar, [IC3Net](https://arxiv.org/abs/1812.09755), ICLR 2019 | Learned gating controls communication | Selective communication is not new here; our gate is analytic and uses a linear policy. |
| Sai Qian Zhang, Qi Zhang and Jieyu Lin, [VBC](https://arxiv.org/html/1909.02682v2), NeurIPS 2019, sections 4.3 and 6.2 | Receivers request help when their top-two action-value gap is small; informative responses are selected using message variance | This is a close predecessor to action-sensitive pull communication. Our distinction is the joint feature-box minimum margin, plus explicit two-leg Bernoulli loss/fixed-delay simulation and packet-attempt accounting. We do not reproduce VBC's learned encoders, variance regularization or centralized mixing. |
| Hu et al., [ETCNet](https://arxiv.org/abs/2010.04978), 2020 preprint | Event-triggered communication under bandwidth constraints | Event triggering and communication/performance trade-offs are established; our study uses simpler fixed rules and an analytic gate. |
| Yuan et al., [CroMAC](https://arxiv.org/abs/2305.13936), 2023 preprint / Science China Information Sciences 2024 | Certified action-value reasoning under message perturbations using learned multi-view representations | Action certification with communication uncertainty is also established. Our exact linear box calculation is restricted and does not reproduce their certification/training framework. |
| Qian Zhang et al., [VIL2C](https://arxiv.org/abs/2511.19146), 2025 preprint | Value-of-information-aware latency/resource allocation and reception timing | Considering usefulness and delay is not unique. Our simulator uses fixed exogenous delay and does not optimize wireless resources. |
| Pang et al., [iLLM-TSC](https://arxiv.org/abs/2407.06025), 2024 preprint | Traffic control with imperfect observations, including degraded communication | Impaired communication in traffic control predates this project. Their LLM-based policy adjustment is outside this project's scope. |
| Yuli Zhang et al., [Dependency Dynamics](https://arxiv.org/abs/2502.16608), 2025 preprint | Relates intersection dependence and spillback to benefits of joint learning | A small lightly loaded network may not exhibit strong coordination benefits. This is relevant motivation for reporting limited communication influence, not proof that its theoretical assumptions hold here. |

The VBC protocol specifically compares the top-two local Q values to a
threshold and filters responses by encoded-message variance. The present
certificate instead minimizes the chosen-minus-alternative linear Q margin
over both neighbor blocks jointly while holding local features fixed. Its
statement is about the fitted model and declared box only. It gives no
optimality, physical-safety, long-horizon-return or generalization guarantee.

Defensible description: an interpretable, reproducible small-network study
of linear-IQL communication under packet loss and fixed delay, with exact
current-action invariance checks and explicit request/response accounting.
Whether that combination merits a research novelty claim remains unestablished.
Do not describe action gaps, request gating, certification, freshness or
traffic communication robustness individually as new contributions.

A search also identified a 2025 counterfactual-message-value paper, but its
publisher page required browser verification. Its full method was not
inspected, so it is not used to assert a detailed distinction. Broader search
coverage and a venue-specific assessment remain needed before any approved
final novelty or publication-readiness statement.

# How to use this project

This package lets you bring a clear research question to a project meeting, demonstrate a working software pipeline and explain its limitations. It contains no fabricated scientific results. The final empirical study still requires data access, selection of available API models, independent annotation of new data and real model runs.

## What is already prepared

- The four P6 starting papers and DiNaM have been analyzed, with distinctions between their tasks made explicit.
- Additional sources have been identified: SemEval Task 10, a retrieval baseline, HELM, EUDisinfoTest and TopicGPT.
- The proposal, protocol, annotation guidelines, work plan, report scaffold and defense materials are prepared.
- The CLI, HTTP adapter, two prompting strategies, baseline, data validation, metrics and reports are implemented.
- Fictional teaching data and a complete offline pipeline demonstration are included.
- An English presentation with English speaker notes is included.

## What remains to be established

| Question | Current information | How to resolve it |
|---|---|---|
| Existing data | PolyNarrative fits the proposed task | Obtain approved access and record the release |
| API access | The group can use API tokens | Verify provider, model IDs, quotas and returned usage fields |
| Budget | No amount has been specified | Set a monetary cap and provider alerts after the pilot |
| Team | A group exists, but membership is not specified here | Assign owners for data, code and analysis |
| New sample | The kickoff requires a new dataset | Confirm whether instructors provide one; this plan assumes independent collection |
| Credits and requirements | The slides list 6–10 credits for Berlin | Check your workload and whether the proposed task scope is acceptable |

PolyNarrative registration is described at https://nikon95.github.io/narrative-detection/. Access to a paper is not the same as access to its dataset. While access is pending, begin reading, developing the codebook and preparing your own pilot. Do not present synthetic teaching sentences as the course's new dataset.

## What to say at the next meeting

“We propose a resource-aware benchmark for narrative classification and extraction of supporting source evidence. We start with one language and domain, compare three API models and two prompting strategies with a CPU baseline, and measure F1, output usability, cost and latency on existing data. We then evaluate transfer to a separately and independently annotated new sample. The software pipeline already works in an offline demonstration. The next step is to fix the dataset release, codebook and available model configurations.”

This is a ready-to-use proposal statement. Use “propose” and “plan” for experiments that have not yet been performed.

## Personal preparation plan

**Session 1, 60–90 minutes.** Read the literature review and proposal. Explain the difference between a topic, a specific claim and a narrative on paper. Run the demo and find an example of an extra predicted category.

**Session 2, 60–90 minutes.** Study the protocol and metrics. Calculate precision, recall and F1 for five examples yourself. Explain why paragraphs from the same article must not be divided between training and test data.

**Session 3, 60–90 minutes.** Read the selected sections of PolyNarrative and the 2026 paper. Compare recovery, mining and discovery. Prepare one limitation of each study.

**Session 4, 60–90 minutes.** Read the annotation guide, label 10 teaching examples without consulting their supplied labels, and then compare. Rehearse answers to the questions in the study guide.

**Session 5, 45–60 minutes.** Rehearse an eight-minute presentation. Execute the CLI commands without prompts. Prepare a list of unresolved research decisions.

These durations are planning estimates, not a guarantee of readiness. You are ready when you can explain why the experiment is designed this way and identify which results are still missing.

## Dividing work within the group

For three participants, assign one to data and codebook, one to API execution and reproducibility, and one to evaluation and reporting. Everyone reads the core papers. For two participants, combine execution and reporting under one owner, but both independently annotate the new sample.

Double annotation requires independent initial judgments. One annotator should not show the other their categories first. A third person can adjudicate disagreements if available. In a two-person group, retain both original versions and a separate log of joint decisions.

## What constitutes a complete submission

1. A literature review with your own classification of approaches and citations.
2. A precise task, fixed data and annotation rules.
3. Reproducible code with configurations and tests.
4. Real results on existing data.
5. A quality–resource analysis with measurement limitations disclosed.
6. A new real sample, independent annotation, agreement assessment and frozen-system transfer evaluation.
7. A report, presentation, error discussion and contribution statement for each team member.

The kickoff assigns 25% to the literature review, 35% to implementation, 20% to the report and 20% to presentations. This package prepares all four components, but code alone does not replace empirical work or your own understanding. Requirements come from slides 7 and 9 of the supplied kickoff PDF.

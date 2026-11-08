# Actual status

As of 8 November 2026:

- Step 1: a specific initial method and narrowed scope have been selected as a proposal: PolyNarrative C.1, labels-only, English URW.
- Step 2 implementation: independent importer, prompt, taxonomy, API runner, deterministic parser, document aggregation, scoring, hashes, request ledger and run instructions prepared.
- Official baseline code: not located in the checked public sources. This is original implementation code, not a fork of author software.
- User-supplied articles and gold: opened and prepared locally. English ST2 has 41 articles; the filename-based English URW selection contains 17. Data and gold are not bundled or uploaded.
- Original paragraph annotations/boundaries: not obtained. The official ST2 scorer archive is now available locally. Do not claim paragraph evaluation or full paper scorer parity.
- API experiments: not executed. No keys were searched for or used.
- Published model results: none. Offline unit and HTTP-stub checks are software validation only.
- Validation: 23 offline tests passed, including repeated gold-label import, a localhost HTTP round trip, successful document scoring, truncation handling, immutable resumption, unresolved-attempt blocking, label parsing and gold exclusion from requests.
- Official scorer check: document sample-F1 matched in six local fine/coarse sanity cases using the prepared release. This confirms that calculation only; Macro-F1 and the full paper setup are not thereby verified.
- Remaining input: exact provider model and endpoint, local API credential. Selected release IDs and category strings have been checked. Review permitted hosted inference use before transmitting the data.

This folder is an executable preparation package. It does not certify that the experiment has already been reproduced successfully. The next real research artifact should be a dated pilot/full-run report with every implementation difference attached.

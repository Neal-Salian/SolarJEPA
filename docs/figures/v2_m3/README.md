# M3 frozen synthetic coverage figure

`coverage.png` is generated with Matplotlib3.11.2, 2520×1440 pixels, 180 dpi.
Each panel shows a different estimand. Points are true-target coverage over400
independent simulated datasets; bars are pointwise Wilson95 intervals. Blank
points mean unavailable inference. Do not interpret conditional coverage as joint
coverage or marginalize away unsupported assumptions.

Figure SHA-256: `aaea514b1990bf9b8e725a3b66e09be073edd99d771cb7ee07cf81d547e76355`.
Scientific payload SHA-256:
`4eae0b13e366d243718c0342552c5a51062851652261f52f2e47c9b6b8f69055`.
Serialized scientific-file SHA-256 (both executions):
`2ac1c72d4e008994d9496c6ff00f3b72e70ce3a34ce74a266382f9cccc12bda8`.
Payload hashing uses canonical JSON; file hashing includes serialization bytes.
Frozen executable commit: `f0806e37ff1993ab7735776adde12ac08df719cd`.
The publication exporter fixes only a negative machine-epsilon plotting length;
original Wilson endpoints remain intact in evidence.

Executed export, from repository root:

```sh
python scripts/summarize_m3_inference.py \
  --evaluation results/experiments/m3-evaluation-8cd4e9fbd509-6f812529e586 \
  --repeat results/experiments/m3-evaluation-8cd4e9fbd509-68d4f7c6605c \
  --development results/experiments/m3-development-c3ae3f038ed6-0d822845881f \
  --pilot results/experiments/m3-development-6fede9aa9f51-a179b4179d39
```

These unique bulk artifacts are intentionally ignored locally. To regenerate after
cloning, run the commands in `docs/V2_M3_INFERENCE_REMEDIATION_REPORT.md`, then supply
the newly emitted distinct IDs. The exporter verifies manifests, source/execution
identity agreement and matching final scientific results, rejects one execution
counted twice, and refuses to overwrite different evidence. This figure is a
derived presentation; the saved scientific JSON and its audited estimands carry
the statistical results. Cross-version pixel equality is not promised.

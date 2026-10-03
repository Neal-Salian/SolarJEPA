# Next authoritative evidence request: pipeline-1.1 timing and exposure

Prepared on 2026-10-03 (Asia/Kolkata). The user reports sending this request to
the official contact; **no reply is available yet**. The exact send time is
unrecorded and the agent has sent no external message. It requests one missing
resource: the applicable pipeline-1.1 timing/GTI/exposure specification or erratum.
Correction and response compatibility remain separate subsequent questions.
No scientific answer is inferred from sending the request.

The [official PRADAN contact page](https://pradan1.issdc.gov.in/al1/contacts.xhtml)
lists **Dr. Sankarasubramanian K, `sankark@ursc.gov.in`**, for SoLEXS payload
queries. The ignored page snapshot and SHA-256 are pinned in the
[D.1 evidence manifest](../data/manifests/solexs_phase_d1_evidence.json).
This published contact is DOCUMENTED; whether a particular response resolves
the scientific gate must be assessed from its contents and applicability.

**Subject:** SoLEXS July 2024 L1 data 1.1 / pipeline 1.1 timing, GTI and exposure specification

Dear Dr. Sankarasubramanian,

I am validating these original PRADAN SoLEXS products for reproducible research:

- `AL1_SLX_L1_20240701_v1.1.zip`, 6,036,792 bytes;
  SHA-256 `9d0cb2341c2eb6c4b25b6dd0b600042b750920ea433197e1d0def742c947b7e4`.
- `AL1_SLX_L1_20240703_v1.1.zip`, 6,216,112 bytes;
  SHA-256 `b82ce974cd6195621e85e3c2773dc94202811c12c7b31e71df0c0353fe3af4bf`.

Their creator metadata identifies processing software 1.1. I have the PRADAN
SoLEXS User Manual v1.0 (January 2025), Release Updates dated 2026-06-09 and
the original `solexs_tools-1.1.tar.gz`. The updates state that July–September
2024 was re-released as data 1.1 / processing 1.1 with timestamps aligned with UTC.

Please provide the applicable timing/GTI/exposure specification or erratum,
including the exact conversion or precedence rule for these products:

1. July 1 LC TIME and PI TSTART start at `1719792000`. LC DATE-OBS is
   `2024-07-01 05:30:00`, with MJDREFI `40587`, MJDREFF `0.22916666651`,
   TIMESYS `UTC`, TIMEREF `LOCAL` and TIMZERO `0`. Does TIME already represent
   absolute Unix UTC seconds? How should conflicting date/reference cards be
   interpreted? PI lacks epoch/date reference cards and GTI lacks encoded time units.
2. What physical instant does native LC TIME label: integration start, centre
   or end? Does the manual's PI integration-start definition apply to these
   processing-1.1 samples? How are GTI START/STOP tied to the same clock and bins?
3. Are GTI endpoints inclusive integration-start coordinates or continuous
   interval boundaries? On July 1, sum(STOP−START) is `86268`, while GTI EXPOSURE
   is `86272.0` and there are 86,272 finite one-second LC points within inclusive
   endpoints. PI TELAPSE and EXPOSURE are both 1 even in invalid/NaN rows.
   Which intervals/rows should contribute to valid continuous and effective exposure?
4. What Unix/leap-second convention, reference position and clock uncertainty
   apply? Are any clock/reference resources needed before absolute UTC use?

Please identify the supported data/processing versions and any recommended
validation example. I am preserving native values and have applied no timestamp
repair, GTI filter, correction or response/channel relabelling.

Thank you.

The [D.1 report](SOLEXS_PHASE_D1_REPORT.md) and portable metadata provide the
evidence without requiring raw scientific attachments. No additional science
download is requested by this draft. Preserve any reply or attached specification
unchanged in ignored documentation storage, with its source, date, scope and hash;
do not record an assumed answer in the scientific contract.

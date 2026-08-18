# Source archive — manifest

Local copies of the source materials used to build the South Tees Public System Map, preserved because these pages and documents change over time and old versions are not otherwise kept. Each map node also carries its source URL in the detail panel; this folder holds the captured copies.

**Method / limitations:** web pages and text-based PDFs are captured as markdown/text (searchable, faithful to content, not pixel-exact). Exact *binary* PDF copies can't be pulled with the current tooling — where that matters, drag-save the original from the URL into this folder. Items flagged **[binary — manual save]** below still need that.

| Source | URL | Type | Retrieved | Local copy |
|---|---|---|---|---|
| Middlesbrough Council organisation chart (June 2026) | https://www.middlesbrough.gov.uk/media/emzm1o33/organisation-chart-june26.pdf | PDF (image-only) | 2026-07-25 | **[binary — manual save]** — image-based, no text layer to extract |
| Middlesbrough Executive & councillors (moderngov) | https://middlesbrough.moderngov.co.uk/mgCommitteeDetails.aspx?ID=1146 (+ member pages) | Web | 2026-07-25 | `MBC-Executive-moderngov_2026-07-25.md` |
| Redcar & Cleveland Senior Management Structure (Feb 2026) | https://www.redcar-cleveland.gov.uk/sites/default/files/2026-02/Senior%20Management%20Structure.pdf | PDF (text) | 2026-07-25 | `RC-Senior-Management-Structure_2026-07-25.md` (text extract). Also drag-save the PDF here for a binary copy. |
| Redcar & Cleveland Cabinet page | https://www.redcar-cleveland.gov.uk/councillors-and-committees/the-cabinet-and-cabinet-papers | Web | 2026-07-25 | `RC-Cabinet-page_2026-07-25.md` |
| NHS NE&NC — Tees Valley PCNs | https://northeastnorthcumbria.nhs.uk/media/rl5ppbrf/tees-valley-pcns.pdf | PDF (non-extractable) | 2026-07-25 | **[binary — manual save]**. RCVDA's own "Tees Valley Primary Care Networks" Google Sheet is the maintained working copy of this data. |
| University Hospitals Tees (UHT) — group board | https://www.southtees.nhs.uk/about/university-hospitals-tees/meet-the-group-board/ | Web | 2026-07-25 | `UHT-Group-Board_2026-07-25.md`. UHT group manages South Tees Hospitals FT + North Tees and Hartlepool FT. |
| South Tees Hospitals FT — nominated governors | https://www.southtees.nhs.uk/about/governors/nominated/ | Web | 2026-07-25 | `STHFT-Nominated-Governors_2026-07-25.md`. Nominated governors link the trust to councils, universities, Healthwatch and Carers Together. |
| HDRC South Tees — team | https://hdrcsouthtees.co.uk/meet-the-team | Web | 2026-07-25 | `HDRC-South-Tees-Team_2026-07-25.md`. Delivery team modelled as nodes; co-applicants/associates captured as org links. |
| R&C Cabinet members — appointments (moderngov) | https://rcbc.moderngov.co.uk/mgUserInfo.aspx?UID=… (per member) | Web | 2026-07-25 | `RC-Cabinet-member-appointments_2026-07-25.md`. All 9 members captured (Cllr Ursula Earl retrieved via browser after web_fetch failed). |
| Community Safety Partnerships (Middlesbrough & R&C) + LCJB guidance | https://www.middlesbrough.gov.uk/crime-and-safety/middlesbrough-community-safety-partnership/ · https://www.redcar-cleveland.gov.uk/community-support/community-safety-partnership · https://assets.publishing.service.gov.uk/media/6419bed8d3bf7f7ff7d3b3c8/local-criminal-justice-boards-guidance.pdf | Web/PDF | 2026-07-25 | Each LA has its own CSP; both report to the Cleveland Local Criminal Justice Board (name to confirm). Not yet copied locally — save if wanted. |
| CURV Governance Group — initial meeting minute | Local file (already in Partnerships): `RCVDA Partnerships/Cleveland Wide/OPPC … Cleveland/CURV … /CURV Governance Group/2022-05-16 Meeting/2022-05-16 Cleveland Unit for the Reduction (as PDF).pdf` | PDF | 2022-05-16 | Source for CURV, its Governance Group representative membership, and the South Tees Changing Futures / Lived Experience Board thread. **Note: 2022 data — membership may have changed.** |

## Discrepancies caught while archiving

- **R&C Cabinet — Neighbourhoods portfolio:** **RESOLVED (2026-07-25).** Current holder is **Cllr Neil Bendelow**, as shown on the live Cabinet page. The confusion was mine: an automated `web_fetch` of the cabinet URL returned a **stale/cached copy** listing the predecessor Cllr Adam Brook, and I wrongly flagged the live page as out of date — it was current. Archive capture corrected. Cllr Adam Brook has moved on to be **Chief of Staff to Anna Turley MP (Redcar)** while remaining a councillor (MP + Chief-of-Staff nodes added). **Lesson: treat web_fetch output as possibly cached; check against the live page for anything time-sensitive.**

## Practice going forward

Every time a new source is used to add to the map, capture a copy here and add a row to this table with the retrieval date.

*Set up 2026-07-25.*

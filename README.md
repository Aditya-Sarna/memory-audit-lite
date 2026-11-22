# Memory audit (lite)

## What this project is

Claude can keep a memory of the person it talks to. This project is a ready-to-run kit for testing that memory in three ways, using **one invented person** (Ishaan Verma, 34, a product analyst in Pune) and **throwaway accounts only**. No real person's data is involved.

The three questions are:

1. **Does memory save what it should, and only that?** We send 1,000 made-up facts to four accounts and check which ones got saved. The four accounts differ in how the facts are delivered (casually, or with "Please remember this") and in whether the sensitive-topics switch is on. They are called T0 (casual, switch off), T1 (casual, on), T2 (explicit, off) and T3 (explicit, on).
2. **Does an assistant with a saved private fact use it where it should not?** An email assistant gets tasks that sit close to a saved private fact, such as a request for a standing desk when a migraine is saved. We check whether the email mentions the fact when nobody asked.
3. **Does that change after a delay?** We take the pairings in which Study 2 saw the assistant use a stored fact, and run them again (and a new task of the same theme) in memories that have been through different amounts of unrelated writes and chats. We also test whether a privacy rule saved once is still followed.

Deciding whether an email leaked is done by two people reading blind, then an AI judge that copies their rules, then people checking everything again.

Nothing has been run on real Claude yet. The numbers in the design marked *simulated* come from tests that run the scoring code on made-up results.

## How to use it

1. Read `DESIGN.md`. It explains the whole design from the beginning: the research question, how Claude's memory works, and each study in detail.
2. Run `python3 tests/test_all.py`. It takes about four minutes and must end with `0 failed`.
3. Before any real run, run `python3 tools/freeze.py write`. This records a fingerprint of the design, the data and the scoring code, so any later change is caught by `python3 tools/freeze.py verify`. Two more freezes follow later: `write-after-pilot` when the labelling pilot ends and `write-after-plan` once the Study 3 plan exists.
4. Run the work in this order: Study 1, then a small Study 2 pilot, then the labelling pilot, then Study 2 in full. Then run `python3 study3_delay/plan.py study2_email/checkbook.csv`, which builds the Study 3 plan from the pairings Study 2 flagged, and run Study 3 from that plan. If too few pairings fired, the plan says Study 3 is not run.

## The files

| Path | What it holds |
|---|---|
| `DESIGN.md` | The full design, written for someone meeting the project for the first time |
| `study1_storage/` | `facts.md` (the 1,000 facts), `feed.py` (prints what to send), `checkbook.csv` (the empty sheet where you record saved or not), `score.py` (turns the sheet into results) |
| `study2_email/` | `lures.md` (theme map, task map and the 976 email scenarios), `prompt_library.md` (every prompt used), `checkbook.csv` (2,669 empty run rows), `score.py` |
| `study3_delay/` | `plan.py` (builds the 27-store plan from the Study 2 results; writes `plan/`, which holds the plan and is generated, not shipped), `rules.md` (the two privacy rules of Study 3b), filler text, `seed.py` (prints what to save into a store), `score.py` |
| `adjudication/` | `PROTOCOL.md` (the labelling process), `rulebook.md` (the codebook), `kappa.py` (agreement), `plant.py` (plants known leaks), `rounds.csv` (log of AI-judge versions) |
| `tools/` | `stats.py` (the statistics), `mdtable.py` (reads the tables in the markdown files), `freeze.py` (the fingerprint tool) |
| `tests/test_all.py` | Checks every scorer on simulated data |

A checkbook is a spreadsheet with headings and one blank row for each thing to record. You fill it in as you run the study, then run the matching `score.py`.

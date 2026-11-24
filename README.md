# Memory audit (lite)

## What this project is

Claude can save notes about the person it talks to, known as its memory. This project is a ready-to-run kit for testing that memory, using **one made-up person** (Ishaan Verma, 34, a product analyst in Pune) and **throwaway accounts only**. No real person's information is involved.

The research question:

> Does Claude's memory keep to its own stated rules about what it saves? Do the private details it saves stay out of emails written for people who should not see them? And when they do leak and Claude is corrected, does it keep following that correction as sessions and unrelated memory saves pile up?

It is answered by three studies:

1. **Storage.** We send 960 made-up facts to four accounts and check which ones get saved. The accounts differ in how a fact is mentioned (casually, or with "Please remember this") and whether the sensitive-topics setting is on. The results are compared with Anthropic's published memory rules, checked word by word and linked in `DESIGN.md`.
2. **Leakage.** An email assistant with a private fact in memory writes emails to people who should not learn it. We check whether the fact slips in when nobody asked.
3. **Persistence.** For each confirmed leak, fresh accounts recreate it, Claude is told once not to share private details with others, and then new chats and unrelated saved notes are added on a 3 × 3 grid. We re-test the original email to see whether the advice holds, and compare with accounts that got no correction.

Every made-up fact carries an invented word that appears nowhere else. If that word shows up in Claude's memory or in an email, we know exactly which fact it came from. The words are built so they cannot be mistaken for English or for a name (for example Bzuvxajv), so Claude could not produce one by chance.

Nothing has been run on a live Claude account yet. Numbers marked *simulated* in the design come from tests that run the scoring code on made-up results.

## How to use it

1. Read `DESIGN.md`. It explains the whole design in plain words.
2. Run `python3 tests/test_all.py`. It must end with `0 failed`.
3. Before any real run, run `python3 tools/freeze.py write`. This records a fingerprint of the design, the data and the scoring code, so `python3 tools/freeze.py verify` catches any later change. Two more freezes follow: `write-after-pilot` when the labelling practice ends, and `write-before-study3` once the Study 3 case list is built.
4. Run in this order: the Study 1 trial (`python3 study1_storage/feed.py T0 --pilot`, and T1 to T3), Study 1, a small Study 2 trial with the labelling practice, Study 2 in full, then `python3 study3_correction/build.py cases` to pick the Study 3 cases from Study 2's results, then Study 3.

## The files

| Path | What it holds |
|---|---|
| `DESIGN.md` | The full design, for someone meeting the project for the first time |
| `study1_storage/` | `facts.md` (the 960 facts), `feed.py` (prints what to send, including the trial), `checkbook.csv` (where you record saved or not), `score.py` (turns the sheet into results) |
| `study2_email/` | `lures.md` (the 976 email test cases), `prompt_library.md` (every prompt used), `post_pilot_prompt.md` (the AI judge's instructions), `checkbook.csv` (2,669 empty run rows), `score.py` |
| `study3_correction/` | `correction.md` (the correction message and the run steps), `build.py` (picks the cases from Study 2 and prints each account's steps), `bland_saves.txt` and `neutral_prompts.txt` (the unrelated activity), `cases.csv` and `checkbook.csv` (empty until built), `score.py` |
| `adjudication/` | `PROTOCOL.md` (how replies are judged), `rulebook.md` (the codes), `kappa.py` (agreement between reviewers), `plant.py` (plants known leaks), `rounds.csv` (log of AI-judge versions) |
| `tools/` | `stats.py` (the statistics), `mdtable.py` (reads the tables in the markdown files), `freeze.py` (the fingerprint tool) |
| `tests/test_all.py` | Checks every scorer on simulated data |

A checkbook is a spreadsheet with headings and one blank row for each thing to record. You fill it in as you run the study, then run the matching `score.py`.

## Licence

MIT, see `LICENSE`. Every fact, person, ID and number in the data is invented.

# Voice — transcript, talk track, and board text

**Run the `factory-humanizer` skill (in the appropriate language) on `transcript.md`,
`talk-track.md`, and every text element on the board — every language, every time.** That skill
owns the general de-AI-slop pass (banned formatting/structure/transitions, word swaps, the
over-correction trap). What follows here is only the craft specific to *this* deliverable, on top
of that general pass.

## Recap-specific craft (any language)

- **Sections have headers and run as prose.** No bullet lists in the transcript.
- **Numbers carry their comparison in the same sentence.** Not "spending fell 3.3%" but "spending
  fell 3.3% against an expected rise of 0.9%".
- **Sources are named inline:** "Bloomberg reported", "the Japan Times said" — not "analysts say".
- **Contradictions are stated flatly and left standing**, without a reconciling bow on top.
- **The piece ends on the open question, not a summary of itself.**
- **Do not use Unicode arrows in prose.** Draw them on the board instead.

## Board voice, when the board ships in a second language

Whiteboard notes are naturally terse — this is someone scribbling, not writing a report. That's a
register choice on top of whatever `factory-humanizer` catches, not a replacement for it:

- **Plain/informal register throughout**, not a formal register — the board is notes, not prose.
  Fragments are correct here.
- **Do not align columns with padding spaces.** CJK (and most non-Latin) font fallbacks are
  proportional, so padded columns drift. Rewrite any such block as ordinary short lines instead.

### Worked example (Japanese, from the recap this method was built on)

| Japanese | Rough English |
|---|---|
| で、ツケは誰が払う? | so who's left holding the bill? |
| 数字は同じ。中身はまるで別物。 | same number, totally different thing underneath |
| もう一発なしで157を守れるか | can they hold 157 without another round? |
| 円をやりたいなら為替でやる。株じゃない。 | want the yen? do it in FX, not equities |
| 広い上げじゃない。原資を抜いた上げ。 | not a broad rally, one funded by selling something else |
| 誰も触りたくない数字 | the number nobody wants to touch |

Notes on why these work: casual words for formal concepts belong in speech (e.g. a colloquial
term for "another round" rather than a stiff bureaucratic one), and question marks / casual
sentence-final particles are correct here, not a lapse into informality to fix.

### Reuse your own published work's own wording

When the board references something you've previously published, use its actual title/phrasing
rather than inventing a new way to describe it — readers who know the reference recognize it, and
it's one less thing to get subtly wrong in translation.

# FitFindr

Cruz Chigonda

## What This Does

FitFindr takes a plain-language request for a secondhand piece, like
`'vintage graphic tee under $30'` or `'platform sneakers size 8'`, and pulls
the price ceiling, the size and the keywords out of it. It searches 40 thrift
listings from Depop, thredUp and Poshmark and picks the best match. It then
suggests one or two outfits built around that item from the user's saved
wardrobe, or general styling advice if the wardrobe is empty, and writes a
short caption to post about the find. If nothing matches, it stops after the
search and tells the user which part of the request to loosen.

---

## Tool Inventory

### `search_listings`

- **What it does:** Filters the 40 listings by price ceiling and size, then
  ranks what's left by keyword overlap with the description. Each query word
  scores 3 if it's in the title, 2 if it's in a style tag, and 1 if it's only
  in the description, category, colours or brand. Listings that score 0 are
  dropped. A size matches when it equals one whole part of the listing's size,
  split on spaces, slashes and brackets: `M` matches `M`, `S/M` and `M/L`, but
  not `XL` or `W30`, and `8` matches `US 8` but not `US 8.5`. "One Size"
  listings match any size.
- **Inputs:** `description` (str), `size` (str | None, where None skips the
  size filter), `max_price` (float | None, inclusive, where None skips the
  price filter)
- **Returns:** a `list[dict]` of at most `config.SEARCH_RESULT_LIMIT` (10)
  listings, highest score first, with ties kept in data order. Each dict is a
  whole listing: `id`, `title`, `description`, `category`, `style_tags` (list),
  `size`, `condition`, `price` (float), `colors` (list), `brand` (str or None)
  and `platform`.
- **When it has nothing:** `[]`. It never returns `None` and never raises.
  The loop branches on this.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfits built around the
  thrifted item. With a wardrobe, every outfit uses pieces the user already
  owns, named as they appear in the wardrobe. With an empty wardrobe, it asks
  for general styling advice: what kinds of pieces to pair the item with.
- **Inputs:** `new_item` (dict, one listing as returned by `search_listings`),
  `wardrobe` (dict with an `items` key holding a list of wardrobe item dicts,
  each with `name`, `category`, `colors`, `style_tags` and `notes`)
- **Returns:** a non-empty `str` of one or two outfit suggestions in plain
  text, a few lines long, naming the thrifted item's title and the pieces it
  goes with.
- **When it has nothing:** An empty `wardrobe["items"]` doesn't count as
  nothing. It returns general styling advice for the item instead. If the
  model sends back an empty string, it returns a fixed fallback line naming
  the item's category and style tags, so it never returns `""`.

### `create_fit_card`

- **What it does:** Asks the model for a short caption someone would post
  about the find. It reads like a real post rather than a product
  description, and mentions the item, its price and its platform once each.
- **Inputs:** `outfit` (str, the text `suggest_outfit` returned), `new_item`
  (dict, the same listing that went into `suggest_outfit`)
- **Returns:** a `str` caption of two to four sentences, containing the price
  written as `$24` and the platform name. The brand appears only when the
  listing has one.
- **When it has nothing:** If `outfit` is empty or only whitespace, it returns
  `"No outfit to caption for <title> yet. Run suggest_outfit first."` without
  calling the model and without raising.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:**

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** <!-- regex, string splitting, or asking the model — say which -->

**What moves through the session:** <!-- which fields, in what order -->

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask '...'

```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

```

```
$ python -c "from tools import suggest_outfit; ..."

```

```
$ python -c "from tools import create_fit_card; ..."

```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**

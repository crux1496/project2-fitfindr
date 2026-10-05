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

**Branch rule:** If `search_listings` returns an empty list, put a message in
`session["error"]` that repeats what was searched for and names what to
change (raise the price ceiling, drop the size, or use a broader word), then
stop without calling `suggest_outfit`. Otherwise put the first result in
`session["selected_item"]` and go to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

The loop is a `while` over a `next_step` value (`search_listings` →
`suggest_outfit` → `create_fit_card` → `done`). Each step picks the next one
from what it just got back, and `trace.check_iterations(count)` runs on every
pass as the stop condition. The empty search sets `next_step = "done"`
straight from `search_listings`, so that path goes round the loop once and
the happy path goes round three times.

**How the query is parsed:** Regex, in `agent.py::parse_query`, before the
loop starts. A price is taken from `under/below/less than/up to/max $N` or a
bare `$N`. A size is taken from `size X`, where X is a letter size (`M`,
`S/M`, `XXS`), a shoe size (`8`, `US 8.5`) or a waist size (`W30`,
`W30 L30`). Both are cut out of the query, along with lead-ins like "looking
for a". What's left is the description. The result goes into
`session["parsed"]` as `{"description", "size", "max_price"}`.

**What moves through the session:** `query` → `parsed` → `search_results`
(the whole ranked list) → `selected_item` (`search_results[0]`) →
`outfit_suggestion` (from `suggest_outfit(selected_item, wardrobe)`) →
`fit_card` (from `create_fit_card(outfit_suggestion, selected_item)`). Every
tool reads its inputs out of the session rather than from a local variable,
so the item that reaches `create_fit_card` is the same dict
`search_listings` returned. On the empty path, `error` is set and
`selected_item`, `outfit_suggestion` and `fit_card` stay `None`.

---

## Sample Run

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Graphic Tee — 2003 Tour Bootleg Style — $24.0 on depop

  Outfit:   Outfit 1: Pair the Graphic Tee — 2003 Tour Bootleg Style with Baggy straight-leg jeans, dark wash and Black combat boots, finished with the Black crossbody bag for an effortless grunge street look.

Outfit 2: Layer the Graphic Tee — 2003 Tour Bootleg Style over Wide-leg khaki trousers, add the Oversized grey crewneck sweatshirt draped over the shoulders, and lace up the Chunky white sneakers for a relaxed, vintage-inspired fit.

  Fit card: Scored this vintage 2003 tour bootleg tee on depop for just $24 and it's already my new favorite piece. I love styling it with baggy dark wash jeans and black combat boots for that ultimate grunge street look. It also looks so good layered over wide-leg khaki trousers with chunky white sneakers for a more relaxed, vintage vibe.
```

And the query that matches nothing, which stops after the search:

```
$ python app.py ask 'designer ballgown size XXS under $5'
  No listings matched 'designer ballgown' under $5 in size XXS. Try to raise the $5 price ceiling, or drop size XXS, or use broader words, like a category (tops, bottoms, outerwear, shoes, accessories) or a style (vintage, streetwear, y2k, grunge).

0 model calls this session
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; r = search_listings('graphic tee', max_price=30); print(len(r)); [print(x['id'], x['title'], x['size'], x['price']) for x in r]"
7
lst_006 Graphic Tee — 2003 Tour Bootleg Style L 24.0
lst_002 Y2K Baby Tee — Butterfly Print S/M 18.0
lst_033 Vintage Band Tee — Faded Grey L 19.0
lst_015 Vintage Graphic Hoodie — Faded Black L 26.0
lst_017 Mesh Long-Sleeve Top — Black S/M 15.0
lst_011 Low-Rise Cargo Pants — Khaki W29 27.0
lst_012 Oversized Crewneck Sweatshirt — Vintage Navy XL (fits oversized) 20.0

$ python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
[]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Outfit 1: Pair the Vintage Levi's 501 Jeans — Medium Wash with the White ribbed tank top, the Vintage black denim jacket, and the Chunky white sneakers.

Outfit 2: Pair the Vintage Levi's 501 Jeans — Medium Wash with the Oversized grey crewneck sweatshirt, the Brown leather belt, and the Black combat boots.

$ python -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_empty_wardrobe()))"
Pair your Vintage Levi's 501 Jeans with a tucked-in crisp white tee, a cropped black leather jacket, and well-worn canvas sneakers for an effortless everyday look.

For a dressed-up streetwear vibe, style the medium wash denim with an oversized charcoal grey hoodie, a structured trench coat, and chunky black loafers.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Score these vintage Levi's 501 jeans on depop for just $38 and they fit like an absolute glove. Threw them on with my favorite white sneakers for that classic nineties coffee run aesthetic. Honestly never taking these off now that the wash is broken in just right.

$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('   ', load_listings()[0]))"
No outfit to caption for Vintage Levi's 501 Jeans — Medium Wash yet. Run suggest_outfit first.
```

---

## How I Used AI

**Moment 1**

- *What I asked for:* I gave Claude my Tool Inventory spec for
  `search_listings` and asked it to implement it: price and size filters,
  then keyword scoring where a title or style-tag match counts 2 and any
  other match counts 1.
- *What came back:* Code that followed the spec exactly, including the
  whole-part size match, so `M` didn't pick up `XL` and `8` didn't pick up
  `US 8.5`. But `search_listings('graphic tee', max_price=30)` ranked the Y2K
  Baby Tee first. That listing has "graphic tee" as a style tag, so it tied
  with the listing actually titled "Graphic Tee" at 4 points, and the tie
  went to whichever came first in the data file.
- *What I changed:* I split the weights so a title match counts 3, a tag 2
  and everything else 1, and updated the Tool Inventory to match. "Graphic
  Tee — 2003 Tour Bootleg Style" now comes first. The spec had been followed
  correctly; the spec itself was what produced the wrong ranking.

**Moment 2**

- *What I asked for:* A regex parser for the query that pulls out the price
  ceiling and the size, strips a lead-in like "looking for", and keeps what's
  left as the description.
- *What came back:* It parsed all six example queries correctly. But
  `parse_query('looking for a vintage graphic tee under $30')` returned the
  description `'a vintage graphic tee'`. Search didn't care, because `a` is a
  stopword there, but the no-match message quotes the description back to
  the user, so it would have said "No listings matched 'a vintage graphic
  tee'".
- *What I changed:* I made the lead-in pattern also take an optional `a`,
  `an` or `some` after the verb, and re-ran the parser on the same query to
  confirm it now gives `'vintage graphic tee'`.

---

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

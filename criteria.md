# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
The search itself is deterministic, so the slack is for the two model calls
behind it. A run needs two `generate()` calls, and at about seven runs a minute
on the free tier a rate-limit stall or a transient service error on one of five
tries is realistic. A failure like that is a run that didn't complete, not a
bug in the loop. 5 of 5 would mean the target depends on the network.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
Nothing on this path touches the model. Parsing is regex, `search_listings` is
a pure filter over a fixed file, and the branch is an `if not results`. The
same query produces the same empty list every time, so a single miss would be
a bug in the branch, not variance.

---

## 3. The item the search picked is the item the outfit was built for

For a matching query, `session["selected_item"]["id"]` equals
`session["search_results"][0]["id"]`, and the outfit suggestion names
`session["selected_item"]["title"]` or its main noun (for example "graphic
tee" for "Graphic Tee — 2003 Tour Bootleg Style"). Target: 5 of 5 tries.

**Why this target:**
The first half is pure state: the loop copies one dict through the session,
so anything less than 5 of 5 means the session is being overwritten between
steps. The second half is the observable form of the same check. If a
different item reached `suggest_outfit`, its outfit would name a different
piece, and that looks like a bad model answer when it's really a state bug.
The prompt puts the title in front of the model, so it has no reason to drop
it.

---

## 4. The fit card is a caption, with the price and platform in it

The fit card is two to four sentences long and contains the selected item's
exact price (written `$24`, or `$24.00`) and its platform name (`depop`,
`thredUp` or `poshmark`, case-insensitive) — in at least 4 of 5 tries.

**Why this target:**
This is the one tool whose output I can't control word for word. At
`TEMPERATURE = 0.9` the model sometimes adds a hashtag line or a fifth
sentence, or writes "thirty bucks" instead of `$30`, even when the prompt asks
for the figure. One drift in five is what I expect from a sampled caption.
Two in five would mean the prompt isn't doing its job. Price and platform are
the two facts a buyer needs to act on the post, so a caption missing either
one doesn't do what it's for.

---

## 5. Filters are never violated

For every query that names a price ceiling or a size, no listing in
`session["search_results"]` costs more than the ceiling or has a size outside
the requested one. "Size M" never returns `XL`, `W30` or `US 8`, and "size 8"
never returns `US 8.5`. Target: 5 of 5 queries, checked on every result, not
only the first.

**Why this target:**
The sizes in this data are a mix of letters (`S/M`, `XL (oversized)`), waist
sizes (`W30 L30`) and shoe sizes (`US 8.5`), and a substring test gets them
wrong: `"l" in "xl"` and `"8" in "us 8.5"` are both True. A result outside the
ceiling or the size is a wrong answer that looks right, and the user is the
one who finds out. Both filters run in plain Python with no model involved, so
anything less than 5 of 5 is a filtering bug.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->

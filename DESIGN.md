# ATP Season Simulator: design note

How the simulator works. Where the data comes from, what shape it is stored in,
the formula at the centre of it, and exactly which numbers the computer is
allowed to change.

Scope: ATP singles, 1991 onward, three surfaces. Status: data audited, pipeline
not yet built.

---

## 1. The whole thing rests on one number

A tennis season looks impossibly complicated. Sixty-odd tournaments, hundreds of
players, thousands of matches, a ranking table that shuffles every Monday. All of
it is built from one repeated event.

> **How often does this player win a point when he is serving?**
> Everything else in this project is that number, repeated and stacked.

Four points in a row is a game. Six games is a set. Two or three sets is a match.
Seven matches is a title. A year of titles is a ranking. So if you can work out
one player's chance of winning one service point against one particular opponent
on one particular surface, you can build the rest by repetition.

Get the brick right and the tower follows. Get the brick wrong and nothing above
it is worth reading.

---

## 2. Where the data comes from

Every professional match has an official record: who played, who won, and a set
of counting statistics. First serves in, points won, aces, double faults, break
points faced and saved.

These were collected and published by Jeff Sackmann of Tennis Abstract, in the
public repository most tennis research is built on. That repository was taken
down at some point before August 2026 and now returns 404, along with his WTA
equivalent. We use an archival mirror carrying the same files under the same
licence (CC BY-NC-SA 4.0, non-commercial, attribution required, share-alike).

One consequence matters: **there is no live feed any more.** The mirror stops on
25 May 2026. So this project cannot forecast the season currently in progress. It
replays a completed season instead, week by week, scored against what actually
happened. That is a cleaner scientific setup anyway, because the answer is
already known and cannot be fudged.

### What the audit found

| Question | Answer | Figure |
|---|---|---|
| Matches in the archive | 1968 to 2026, tour level | 199,389 |
| When serve statistics start | Nothing usable before this year | 1991 |
| Coverage 1991 to 2015 | Stable plateau, gap is mostly lower-tier matches | ~88% |
| Coverage 2016 onward | Near complete | 94-99% |
| Usable matches, three live surfaces | Hard 52,302 / Clay 33,343 / Grass 10,403 | 96,048 |
| Training rows (two servers per match) | The dataset we actually fit on | 192,096 |
| Median matches per player per season | The tour is mostly one-off qualifiers | 4 |

Carpet appears in the archive but the surface was retired around 2009, so it is
dropped. That leaves hard, clay and grass.

That median of four is the uncomfortable number. A player with four matches
behind him has a very unreliable profile, which is why the model deliberately
drags thinly-observed players back towards the tour average rather than believing
their small sample.

---

## 3. Three files, and only three

| What | Format | Contents | Size |
|---|---|---|---|
| **The raw archive** (read-only, never edited) | `data/tennis_atp/atp_matches_YYYY.csv` | One line per match. Date, tournament, surface, both players, score, counting statistics for each side. | 113 MB |
| **The training table** (built by us, the real work) | `rows.parquet` | One row per *server per match*. Both form cards, surface, points served, points won. | ~192k rows |
| **The fitted model** (output of training) | `model.pt` | Every number the computer learned. | 243 numbers |

### Why every match becomes two rows

The model is about serving, and each match contains two servers. A single
Alcaraz against Sinner match on clay is stored as two observations:

| Server | Returner | Surface | Points served | Points won |
|---|---|---|---|---|
| Alcaraz | Sinner | Clay | 78 | 51 |
| Sinner | Alcaraz | Clay | 81 | 49 |

Note what is *not* stored: who won the match. The model never sees match results
during training. It only learns about service points. Match outcomes are held
back and used later as an independent check on whether the model is any good.

---

## 4. The form card

Before each match we write a short report on each player, describing him as he
was *that morning*. Eight numbers. Call it his form card, written `x`.

Each is computed from his previous matches, then standardised so **zero means
exactly tour average** and one means a standard deviation above it. That
convention matters: two average players produce a prediction of exactly the tour
baseline, with every other term cancelling to nothing.

| # | Attribute | Computed from | Window |
|---|---|---|---|
| 1 | Serve strength | `(1stWon + 2ndWon) / svpt` | 52 weeks |
| 2 | Ace rate | `ace / svpt` | 52 weeks |
| 3 | Double fault rate | `df / svpt` | 52 weeks |
| 4 | Return strength | points won receiving / points received | 52 weeks |
| 5 | Break points saved | `bpSaved / bpFaced` | 52 weeks |
| 6 | Break points converted | opponent `bpFaced - bpSaved` | 52 weeks |
| 7 | Form | last 10 matches minus the 52-week level | 10 matches |
| 8 | Age | from the player file's date of birth | on the day |

> **The one rule that cannot be broken.** A card for a match played on 5 June
> 2019 may only use matches from before 5 June 2019.
>
> Let one later match slip in and the model is reading tomorrow's newspaper. It
> will look brilliant and predict nothing. This failure is silent, which is why
> the first test written for this project is a leakage test rather than anything
> about accuracy.

Surface is deliberately *not* one of the eight. The model is fitted three
separate times, once per surface, so surface changes every weight rather than
adding a single offset.

---

## 5. What changes during training, and what does not

**Frozen, never adjusted:**

- The raw archive. Read-only, always.
- The form cards. Computed once from match history, then fixed. They are inputs,
  like the pixel values of a photograph.
- The point counts. What happened is what happened.

Training never edits any of this. If a card is wrong, it is wrong because the
pipeline that built it is wrong, and no amount of training will fix it.

**Learned, adjusted every step:**

- `mu`, the surface baseline
- `a`, how much each attribute is worth to a server
- `b`, how much each attribute is worth to a returner
- `W`, how the two players' attributes trade against each other

81 numbers per surface, three surfaces, 243 in total. That is the entire model.

Anyone coming to this from a language model will notice the difference. In a GPT
the word embeddings *are* parameters: the vector for a given word physically
changes as the model trains. Here the player cards are computed rather than
learned, so they stay put. That is a deliberate choice for version 1, and
reversing it is the last experiment on the list.

---

## 6. The formula

```
z = mu + a·x_i - b·x_j + x_iᵀ W x_j

p = 1 / (1 + e^(-z))

    i serves, j returns, one surface
```

Four layers, each answering a different question. The first line adds up reasons,
the second turns that total into a probability.

**`mu`, where everyone starts.** The tour-average chance of winning a service
point on this surface. Two exactly average players meet, every other term is
zero, and the answer comes back as this number.

**`+ a·x_i`, what the server brings.** Each of his eight attributes multiplied by
how much that attribute is worth to a server, then added up. This is where "he
has a huge serve" enters the calculation.

**`- b·x_j`, what the returner takes away.** The same idea for the man receiving,
subtracted, because his strength lowers the server's chances. It needs its own
set of weights because serving and returning are different jobs. A big serve
should count for a lot in `a` and almost nothing in `b`.

**`+ x_iᵀ W x_j`, how this particular pairing differs.** A grid of 64 small
corrections, one for every pair of attributes, covering style against style. This
is the only part of the formula that can express "he is a bad matchup for me even
though I am the better player". Without it, better always beats worse.

### Why the second line exists

Probabilities have to stay between 0 and 1, but adding things up does not respect
that. Start at 64%, add 20% for a strong server and 25% for a weak returner, and
you get 109%, which is nonsense.

So the arithmetic happens on a scale where adding is safe, called log-odds, which
runs from minus infinity to plus infinity. The second line squashes the result
back into a real probability at the very end. Same trick as working in decibels:
do the sums in a convenient space, convert once.

### Why this shape rather than something fancier

- **One number per player is not enough.** A single rating can rank players but
  cannot say *how* they win. Splitting serve from return is the minimum needed to
  tell a big server apart from a grinder.
- **The interaction term is the smallest step beyond adding up.** Constant, then
  linear, then the first cross term. Going further would fit noise, not tennis.
- **A neural network would predict marginally better and explain nothing.** With
  eight attributes and 192,000 rows there is not much more signal to extract, and
  the readable weights are the point: `a` tells you what matters on clay, `W`
  tells you which style troubles which.

---

## 7. Every symbol, in one table

| Symbol | Name | What it means | Values | Comes from | Status |
|---|---|---|---|---|---|
| `x_i` | Server's form card | Eight standardised attributes describing the man serving, as he was before this match | 8 | Computed from past matches | Frozen |
| `x_j` | Returner's form card | The same eight attributes for the man receiving | 8 | Computed from past matches | Frozen |
| `mu` | Baseline | Tour-average log-odds of winning a service point on this surface | 1 | Learned, started at the observed average | Learned |
| `a` | Serve weights | How much each attribute helps you when you are serving | 8 | Learned, started at zero | Learned |
| `b` | Return weights | How much each attribute of your opponent hurts you when he is receiving | 8 | Learned, started at zero | Learned |
| `W` | Interaction matrix | 8 by 8 grid. Entry (k, l) says what happens when I am strong on attribute k and he is strong on attribute l | 64 | Learned, started at zero | Learned |
| `z` | Total | The four layers added together, in log-odds | 1 | Calculated fresh each time | Derived |
| `p` | Prediction | Probability that this server wins this point. The output | 1 | Calculated fresh each time | Derived |

### W has the most numbers and the least influence

A natural first reading is that `W`, with 64 entries against 8 and 8, must
dominate. It is the opposite. Parameter count measures *flexibility*, not
*importance*. `W` needs 64 numbers because it has to cover every possible pair of
attributes, not because any of them is large. Its contribution is expected to be
a small fraction of the serve and return terms.

It is also, for exactly that reason, the part most likely to fit noise: the most
knobs, the least evidence behind any individual one. So it gets the heaviest
regularisation, a penalty pulling unused entries back towards zero.

Rather than trusting intuition, compute all three terms across the test season
and report how much each actually moves the prediction. That table belongs in the
README, and it is what decides whether the interaction term earned its place.

---

## 8. One prediction, worked through

Shrunk to two attributes instead of eight so the arithmetic is followable.
Alcaraz serving to Sinner, on clay.

```
form cards        x_server   = [1.2, 0.8]     Alcaraz, above average on both
                  x_returner = [0.9, 1.1]     Sinner, strong returner

current weights   mu = 0.49
                  a  = [0.30, 0.05]
                  b  = [0.02, 0.25]
                  W  = [[-0.04,  0.03],
                        [ 0.01, -0.02]]

the four layers   mu           =  0.490
                  a·x_server   =  0.400      what Alcaraz brings
                  b·x_returner =  0.293      what Sinner takes away
                  xᵀWx         = -0.014      the pairing correction

                  z = 0.490 + 0.400 - 0.293 - 0.014 = 0.583
                  p = 1 / (1 + e^-0.583)             = 0.642

prediction        Alcaraz wins 64.2% of his service points in this match
```

Look at the sizes. Serve term 0.400, return term 0.293, and the whole interaction
matrix just -0.014. That is what "most numbers, least influence" looks like.

---

## 9. How it learns

He actually served 78 points and won 51, which is 65.4%. We predicted 64.2%, so
we were slightly low. Converted into points rather than percentages:

```
predicted points won   78 x 0.642 = 50.06
actual points won                 = 51
error                             = -0.94    we were 0.94 points too low
```

That single error figure drives every adjustment. Each of the 243 numbers is
nudged by a tiny amount, and the size of its nudge follows one rule:

> **nudge = how wrong we were x how involved that number was**

Because we underpredicted, the serve weights tick up and the return weights tick
down. Each entry of `W` moves in proportion to the product of the two attributes
it connects, so a pairing where both players scored near zero barely moves at
all. Numbers only get blamed in proportion to their contribution.

### Why it settles down

Across 192,000 rows the random nudges cancel and the systematic ones accumulate.
If serve strength genuinely matters, its weight gets pushed up every time a
strong server beats the prediction, and pushed down only occasionally by chance.
It drifts upward until it reaches the value where it overpredicts as often as it
underpredicts. At that point the pushes balance, the number stops moving, and the
answer has been found. The same happens to all 243.

Nothing clever is going on. It is a very patient process of being slightly less
wrong each time.

---

## 10. From one point to a ranking

Once the 243 numbers are settled, the model can be asked about any two players who
have never met. Give it Alcaraz and Sinner on clay and it returns two service
percentages, one for each man. Everything above that is repetition.

```
  1. The model                two form cards + surface   ->  2 percentages
                                      |
  2. Points into a match      games, deuce, tiebreaks    ->  who wins
                                      |
  3. Matches into a tournament play the draw round by round -> who lifts it
                                      |
  4. Tournaments into a season award points, roll the 52-week ledger -> the table
                                      |
  5. Run the season 10,000 times                          ->  a distribution
```

The output is not a single prediction but a spread: *"Alcaraz finishes world
number one in 61% of simulated seasons, and in the top four in 94% of them."*
Substitute each real result as the season progresses and the spread narrows week
by week, which is what "predicting the rankings throughout the season" actually
means in practice.

### The surface baselines, which is where step 1 starts

| Surface | Tour-average service points won | Note |
|---|---|---|
| Grass | 65.9% | Fastest. Serving is worth most here |
| Hard | 64.2% | The bulk of the calendar |
| Clay | 61.9% | Slowest. Returners get more back |

Computed from the archive rather than quoted from memory. Four percentage points
separate clay from grass, which is a large gap at point level and an enormous one
by the time it compounds through a five-set match. It is the reason the model is
fitted three times rather than once.

---

## 11. The experiment, and what would count as a result

Built as a controlled comparison rather than a single model, with one thing
changed at each step.

| Rung | Model | What it tests | Status |
|---|---|---|---|
| 1 | Two numbers per player, added up. No interaction term | The baseline everything else must beat | Version 1 |
| 2 | Eight named attributes plus the learned interaction matrix | Do style matchups exist, and are they worth the complexity? | Version 1 |
| 3 | Player vectors learned from scratch instead of computed | Can the model find structure nobody specified? | Version 2 |

A null result is still a result. If the interaction matrix improves prediction by
a negligible amount, the honest conclusion is that professional tennis is more
transitive than fans assume, better players simply beat worse ones, and the added
complexity is not justified. Written up properly, that is a more interesting
finding than a model that merely works.

---

## 12. What this is not

- **Not a betting model.** It is a study of how far a transparent, readable model
  can get, not an attempt to beat a market.
- **Not a shot-level model.** The archive records serve and return counts only.
  Nothing in it measures footwork, forehands or court position, so the model
  cannot learn them and does not claim to.
- **Not able to predict injuries.** A retirement in week three wrecks an
  individual season forecast and there is no signal that would have warned of it.
- **Not live.** The source archive stopped in May 2026, so the simulator replays
  completed seasons rather than forecasting the current one.

Each belongs in the README as a stated limitation rather than being quietly
omitted. A model that says what it cannot do is easier to trust about what it can.

---

*Data originally compiled by Jeff Sackmann (Tennis Abstract), used under CC
BY-NC-SA 4.0 via an archival mirror after the original repository was withdrawn.
Point-to-match calculation follows the standard recursive construction used in
the tennis modelling literature; the interaction term follows the blade-chest
approach to intransitivity in matchup data (Chen and Joachims, 2016).*

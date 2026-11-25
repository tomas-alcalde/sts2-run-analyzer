# TODO

## New analyses

- [ ] CARDS: Dropdown all WR/WAR/ELO per Act too (both for Run WR and Act SR)
- [ ] CARDS: Track performance of upgraded vs. unupgraded cards, and value of upgrade per card. 
- [ ] CARDS: WAR (wins above replacement), the WR of the Runs that took a Card minus that of the Runs that passed it. 
- [ ] RELICS: Track WR/WAR. 
- [ ] FIGHTS: Per *named/individual* Fight: WR, HP loss, turns taken, potions used.
- [ ] EVENTS: Track WR when seen and WR per option taken. Eventually hardcode for specific events of interest.
- [ ] POTIONS: Track HP saved? 
- [ ] ACTS: Track WR, # Elites, # Hallways, # Rest Sites, # Smiths, # Rests, # Unknowns, # Cards Added, # Cards Removed, Deck size, # Cards per Rarity\*, # Cards per Type\*, # Relics, # Deaths to Fight-type.
- [ ] RUNS: As ACTS, and also Total Time.
- [ ] CHANGES IN PLAY: Test WR over time vs. other changes over time (e.g. taking more Elites, taking more Elites in Act 1, deck size, etc.). Do it automatically for all metrics, and flag significant ones.
- [ ] CHARACTERS: When applicable, compare conclusions across Characters (e.g. which one loses more HP overall,
      which one loses more HP at Bosses, which one dies in Act 2 the most, etc.). 

**Note:** Some of these are essentially done in .py and .sql files, just not fully implemented and added to Dashboard.


## Dashboard
- [ ] LANDING PAGE: Opens with the current WR and its trend over time, the longest streaks, and survival rate per Act.
- [ ] LANDING PAGE: Follows with a portrait of the typical Act and run, using the averages of the ACTS and RUNS metrics above.
- [ ] PAST RUN OVERVIEW: A logbook of every run, newest first. Each entry gives the run's details (all `Run` class variables: Character, Ascension, patch, seed, date, duration, result, etc.), traces its path through Acts, Bosses and Ancients (with the Ancient Relic taken), and closes with what killed it.
- [ ] INDIVIDUAL RUN OVERVIEW: One run in depth. Starts from the in-game run summary, then goes beyond it with a clearer view of the deck and the full set of RUNS metrics above.

## Simplified for now

Some tests and models require revisiting. These more technical points are listed as TODO in [methods.md](docs/methods.md).

-----

\* Not in .run files, would need manual database with each.
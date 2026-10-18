import json
from pathlib import Path
import pandas as pd

# NOTE: For adding things below, need to then edit schema.sql for
# the extra categories, and delete runs.db before ingesting.
# TODO: Add track of each event_choices.
#       (1) Remove those on floor of Ancients.
#       (2) For simple ones (e.g. "This or That") just matter of breaking up the
#       string in the key into the event and the decision.
#       (3) But overall custom made per event (Bridge has as many dicts as times out
#       clicked next card, Divination must be strange format, etc.)
# TODO: Add track of each shop decisions
# TODO: Add track of cards transformed/upgraded/enchanted.
#       Just to modify the final deck to add if upgraded/enchanted.

# TODO(!!): Adjust for Act 4 addition


class Run:
    """
    Single completed run of StS2, parsed from a run history file (JSON format)
    """

    def __init__(self, filepath, show=False):
        self.filepath = Path(filepath)
        self.show = show

        with open(self.filepath, encoding="utf-8") as f:
            raw = json.load(f)  # Translate JSON format into native Python dictionary.

        self._raw = raw

        # --- Core info ---
        self.id = self.filepath.name
        self.collection = str(self.filepath.parent)
        self.acts = raw.get("acts")
        self.ascension = raw.get("ascension")
        self.patch = raw.get("build_id")
        self.seed = raw.get("seed")
        self.time = raw.get("run_time")
        self.start = raw.get("start_time")
        self.win = int(raw.get("win"))
        self.killed_encounter = raw.get("killed_by_encounter")
        self.killed_event = raw.get("killed_by_event")

        self.player = raw.get("players")[0]
        self.player_num = len(raw.get("players"))
        self.character = self.player.get("character")
        self.max_pot = self.player.get("max_potion_slot_count")
        self.deck = [card.get("id") for card in self.player.get("deck")]
        self.deck_floors = [
            card.get("floor_added_to_deck") for card in self.player.get("deck")
        ]
        self.relics = [relic.get("id") for relic in self.player.get("relics")]
        self.relics_floors = [
            relic.get("floor_added_to_deck") for relic in self.player.get("relics")
        ]

        # --- Some easy variables to compute ---
        self.deck_size = len(self.deck)
        self.relic_size = len(self.relics)

        # --- History / Log info ---

        # NOTE: Excluded "ancient_choice", "card_choices", "potion_choices" and commented out keys
        #       to format differentely later.
        #       Namely, they return lists or dicts which cannot be injected into SQL directly.
        # NOTE: Shops are handled elsewhere, having: "card_choices", "bought_colorless", "bought_relics",
        #       "cards_gained", "cards_removed", "potion_choices", "relic_choices" (latter also shows in events)

        self.stats_keys = [
            "current_gold",
            "current_hp",
            "damage_taken",
            # "event_choices", # Gives one-element list of a *dict*.
            #                    Shows in ancients and actual events. Should just make a DF where each row
            #                    is an instance of an event choice, then deal with them in SQL.
            "gold_gained",
            "gold_lost",
            "gold_spent",
            "gold_stolen",
            "hp_healed",
            "max_hp",
            "max_hp_gained",
            "max_hp_lost",
            # "potion_used",
            # "rest_site_choices",
            #                        Handle as above.
            # "upgraded_cards", # Gives list of strings (one element per card upgraded)
            # "cards_enchanted", # Same
        ]

        # FLOOR-RANGE FIX (Golden Compass / variable act length):
        # An act's length isn't fixed (e.g. Golden Compass adds extra floors
        # *inside* an act, not always at the same spot), so floor numbers
        # can't be derived from a hardcoded per-act offset table without
        # desyncing from the real data
        # Instead, each act's floor range is the cumulative sum of the
        # *actual* lengths of the preceding acts' map_point_history entries.
        # Used by to_acts_df / to_bosses_df / to_card_choices_df to locate
        # the ancient, boss(es), and per-act tier by actual node type
        # instead of an assumed floor offset.
        act_sections = raw.get("map_point_history", [])
        self._act_ranges = []
        cum = 0
        for act_data in act_sections:
            self._act_ranges.append((cum, cum + len(act_data)))
            cum += len(act_data)
        while len(self._act_ranges) < len(self.acts or []):
            self._act_ranges.append(None)

        # Parse map_point_history into flat list of per-floor dicts, keyed by
        # absolute floor number using the ranges computed above.
        # Each dict contains every field froom rooms[0] and player_stats[0].
        # Mind [0] just because they are one-element lits.
        # Since a bit special structure, manually added "floor", "node" and "ancient_choice"
        self._floors = []

        for act_data, act_range in zip(act_sections, self._act_ranges):
            offset = act_range[0]
            for i, floor in enumerate(act_data):
                room = (floor.get("rooms") or [{}])[0]
                stats = (floor.get("player_stats") or [{}])[0]
                self._floors.append(
                    {
                        "floor": offset + i,
                        "node": floor.get("map_point_type"),
                        "seen": room.get("model_id"),
                        "turns_taken": room.get("turns_taken"),
                        "ancient_choice": stats.get("ancient_choice"),
                        **{k: v for k, v in stats.items() if k != "ancient_choice"},
                    }
                )

        # Fast floor-number lookup, used by "safe_seen"
        self._floor_map = {f["floor"]: f for f in self._floors}

        # NOTE: --- Build DataFrames ---
        self.run_summary_df = self.to_run_df()
        self.run_nodes_df = self.to_log_df()
        self.run_deck_df = self.to_deck_df()
        self.run_relics_df = self.to_relics_df()
        self.run_acts_df = self.to_acts_df()
        self.run_bosses_df = self.to_bosses_df()
        self.run_ancients_relics_df = self.to_ancients_relics_df()
        self.run_card_choices_df = self.to_card_choices_df()
        self.run_potions_choices_df = self.to_potions_choices_df()
        self.run_potions_used_df = self.to_potions_used_df()
        self.run_rest_choices_df = self.to_rest_choices_df()

        # --- Some options for showing/printing raw files ---
        if self.show:
            print("--- Keys in raw file ---")
            print(list(self._raw.keys()))

            print("--- Raw file as Python dict ---")
            print(self._raw)

            print("--- Raw file as JSON ---")
            print(json.dumps(run._raw, indent=2))

    # -----------
    # Helpers
    # -----------

    def safe_seen(self, floor):
        """Return the "seen" value for a given absolute floor number, or None"""
        return self._floor_map.get(floor, {}).get("seen")

    # -----------
    # DataFrame builders
    # -----------

    def to_run_df(self) -> pd.DataFrame:
        """One row summarising the whole run"""
        df = pd.DataFrame(
            {
                "id": [self.id],
                "collection": [self.collection],
                "charac": [self.character],
                "ascension": [self.ascension],
                "win": [self.win],
                "killed_encounter": [self.killed_encounter],
                "killed_event": [self.killed_event],  
                "deck_size": [self.deck_size],
                "relic_count": [self.relic_size],
                "max_pot": [self.max_pot],
                "time": [self.time],
                "patch": [self.patch],
                "seed": [self.seed],
                "start_time": [self.start],
            }
        )
        return df

    def to_deck_df(self) -> pd.DataFrame:
        """One row per card in the final deck"""
        df = pd.DataFrame(
            {
                "card": self.deck,
                "floor_added": self.deck_floors,
            }
        )
        return df

    def to_relics_df(self) -> pd.DataFrame:
        """One row per relic held at run end"""
        df = pd.DataFrame(
            {
                "relic": self.relics,
                "floor_added": self.relics_floors,
            }
        )
        return df

    def to_log_df(self) -> pd.DataFrame:
        """One row per floor, indexed by absolute floor number"""
        rows = []
        for f in self._floors:
            rows.append(
                {
                    "floor": f["floor"],
                    "node": f["node"],
                    "seen": f["seen"],
                    "turns_taken": f["turns_taken"],
                    **{k: f.get(k) for k in self.stats_keys},
                }
            )
        df = pd.DataFrame(rows)
        return df

    def _tier_of_floor(self, floor):
        """Act tier (1-indexed) a given absolute floor belongs to, or None.

        FLOOR-RANGE FIX: looks the floor up in `self._act_ranges` (built in
        __init__ from each act's *actual* length) instead of a hardcoded
        floor cutoff, since an act's real length can vary (Golden Compass).
        """
        for i, act_range in enumerate(self._act_ranges):
            if act_range and act_range[0] <= floor < act_range[1]:
                return i + 1
        return None

    def to_acts_df(self) -> pd.DataFrame:
        """One row per act: the ancient encountered and whether it was survived.

        FLOOR-RANGE FIX: the ancient is found by its real node type
        ("ancient") within the act's actual floor range (`self._act_ranges`),
        rather than an assumed fixed floor offset — see the comment in
        __init__ where `self._act_ranges` is built.
        """
        ancients = []
        survived = []
        for act_range in self._act_ranges:
            if act_range is None:
                # Act was never reached (run ended in an earlier act).
                ancients.append(None)
                survived.append(None)
                continue
            start, end = act_range
            act_floors = [f for f in self._floors if start <= f["floor"] < end]
            ancient_floor = next((f for f in act_floors if f["node"] == "ancient"), None)
            ancients.append(ancient_floor["seen"] if ancient_floor else None)
            died = any(f.get("current_hp") == 0 for f in act_floors)
            survived.append(0 if died else 1)

        df = pd.DataFrame(
            {
                "tier": list(range(1, len(self._act_ranges) + 1)),
                "act": self.acts,
                "ancient": ancients,
                "survived": survived,
            }
        )
        return df

    def to_bosses_df(self) -> pd.DataFrame:
        """One row per boss encountered, with the act it was fought in.

        FLOOR-RANGE FIX: bosses are found by their real node type ("boss")
        within each act's actual floor range (`self._act_ranges`), instead of
        a hardcoded floor offset per act. This also naturally handles
        Ascension 10's second boss on the last act (it just adds a second
        "boss"-typed floor there) without needing an ascension-specific case.
        """
        rows = []
        for tier, act_range in enumerate(self._act_ranges):
            if act_range is None:
                continue
            start, end = act_range
            for f in self._floors:
                if start <= f["floor"] < end and f["node"] == "boss":
                    rows.append({"act": self.acts[tier], "boss": f["seen"]})
        df = pd.DataFrame(rows, columns=["act", "boss"])
        return df

    def to_ancients_relics_df(self) -> pd.DataFrame:
        """One row per ancient relic option presented"""
        rows = []
        for f in self._floors:
            choices = f.get("ancient_choice")
            if not choices:
                continue
            for c in choices:
                rows.append(
                    {
                        "choices": c.get("TextKey"),
                        "ancient": f["seen"],
                        "taken": c.get("was_chosen"),
                    }
                )
        df = pd.DataFrame(rows)
        return df

    def to_card_choices_df(self) -> pd.DataFrame:
        """One row per card option presented, normally three rows per floor.

        FLOOR-RANGE FIX: "tier" is stamped here (via `_tier_of_floor`, using
        the real per-run act ranges) instead of leaving SQL queries to guess
        an act from the floor number with a hardcoded cutoff, which breaks
        whenever an act's actual length differs from the assumed one.
        """
        rows = []
        for f in self._floors:
            floor = f["floor"]
            choices = f.get("card_choices")
            if not choices:
                continue
            tier = self._tier_of_floor(floor)
            for card in choices:
                rows.append(
                    {
                        "floor": floor,
                        "tier": tier,
                        "choices": card.get("card").get("id"),
                        "taken": card.get("was_picked"),
                    }
                )
        df = pd.DataFrame(rows)
        return df

    def to_potions_choices_df(self) -> pd.DataFrame:
        """One row per potion seen. Includes potions seeen in shops!"""
        rows = []
        for f in self._floors:
            floor = f["floor"]
            choices = f.get("potion_choices")
            if not choices:
                continue
            for potion in choices:
                rows.append(
                    {
                        "floor": floor,
                        "choices": potion.get("choice"),
                        "taken": potion.get("was_picked"),
                    }
                )
        df = pd.DataFrame(rows)
        return df

    def to_potions_used_df(self) -> pd.DataFrame:
        """One row per potion used (possibly more than one per floor)"""
        rows = []
        for f in self._floors:
            floor = f["floor"]
            used = f.get("potion_used")
            if not used:
                continue
            for potion in used:
                rows.append(
                    {
                        "floor": floor,
                        "potion_used": potion,
                    }
                )
        df = pd.DataFrame(rows)
        return df

    def to_rest_choices_df(self) -> pd.DataFrame:
        rows = []
        for f in self._floors:
            floor = f["floor"]
            choices = f.get("rest_site_choices")
            if not choices:
                continue
            for done in choices:
                rows.append(
                    {
                        "floor": floor,
                        "rest_site_done": done,
                    }
                )
        df = pd.DataFrame(rows)
        return df

    # -----------
    # Display
    # -----------
    #
    def __str__(self):
        parts = [
            # self.run_summary_df.to_string(),
            # self.run_deck_df.to_string(),
            # self.run_relics_df.to_string(),
            # self.run_acts_df.to_string(),
            # self.run_ancients_relics_df.to_string(),
            self.run_nodes_df.to_string(),
            self.run_card_choices_df.to_string(),
            self.run_potions_choices_df.to_string(),
            self.run_potions_used_df.to_string(),
            self.run_rest_choices_df.to_string(),
        ]
        return "\n".join(parts)

    def __repr__(self):
        return self.__str__()


if __name__ == "__main__":
    import sys

    filepath = #ADD 
    run = Run(filepath, show=False)
    print(run)

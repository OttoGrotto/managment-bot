class Serializer:
    def __init__(self, res: list[str]) -> None:
        self.res = res
        self.SKILLS = [
            "Overall",
            "Attack",
            "Defence",
            "Strength",
            "Hitpoints",
            "Ranged",
            "Prayer",
            "Magic",
            "Cooking",
            "Woodcutting",
            "Fletching",
            "Fishing",
            "Firemaking",
            "Crafting",
            "Smithing",
            "Mining",
            "Herblore",
            "Agility",
            "Thieving",
            "Slayer",
            "Farming",
            "Runecrafting",
            "Hunter",
            "Construction"
        ]
        self.ACTIVITIES = [
            "League Points",
            "Deadman Points",
            "Bounty Hunter - Hunter",
            "Bounty Hunter - Rogue",
            "Bounty Hunter (Legacy) - Hunter",
            "Bounty Hunter (Legacy) - Rogue",
            "Clue Scrolls (all)",
            "Clue Scrolls (beginner)",
            "Clue Scrolls (easy)",
            "Clue Scrolls (medium)",
            "Clue Scrolls (hard)",
            "Clue Scrolls (elite)",
            "Clue Scrolls (master)",
            "LMS - Rank",
            "PvP Arena - Rank",
            "Soul Wars Zeal",
            "Rifts closed",
            "Colosseum Glory",
            "Abyssal Sire",
            "Alchemical Hydra",
            "Artio",
            "Barrows Chests",
            "Bryophyta",
            "Callisto",
            "Cal'varion",
            "Cerberus",
            "Chambers of Xeric",
            "Chambers of Xeric: Challenge Mode",
            "Chaos Elemental",
            "Chaos Fanatic",
            "Commander Zilyana",
            "Corporeal Beast",
            "Crazy Archaeologist",
            "Dagannoth Prime",
            "Dagannoth Rex",
            "Dagannoth Supreme",
            "Deranged Archaeologist",
            "Duke Sucellus",
            "General Graardor",
            "Giant Mole",
            "Grotesque Guardians",
            "Hespori",
            "Kalphite Queen",
            "King Black Dragon",
            "Kraken",
            "Kree'Arra",
            "K'ril Tsutsaroth",
            "Lunar Chests",
            "Mimic",
            "Nex",
            "Nightmare",
            "Phosani's Nightmare",
            "Obor",
            "Phantom Muspah",
            "Sarachnis",
            "Scorpia",
            "Scurrius",
            "Skotizo",
            "Sol Heredit",
            "Spindel",
            "Tempoross",
            "The Gauntlet",
            "The Corrupted Gauntlet",
            "The Leviathan",
            "The Whisperer",
            "Theatre of Blood",
            "Theatre of Blood: Hard Mode",
            "Thermonuclear Smoke Devil",
            "Tombs of Amascut",
            "Tombs of Amascut: Expert Mode",
            "TzKal-Zuk",
            "TzTok-Jad",
            "Vardorvis",
            "Venenatis",
            "Vet'ion",
            "Vorkath",
            "Wintertodt",
            "Zalcano",
            "Zulrah"
        ]

    def format(self, res: list[str] = None) -> dict[str, tuple[int, int, int | None]]:
        if not res:
            res = self.res
        if not res:
            raise ValueError("No data to format")
        statdict = {}
        for i in range(len(res)):
            # Skip empty or improperly formatted strings
            if not res[i] or ',' not in res[i]:
                continue
            data = res[i].split(",")
            # Ensure all parts can be converted to int; skip otherwise
            if not all(part == "-1" or part.isdigit() for part in data if part):
                continue
            if i < 24:
                # Assuming each SKILLS entry is always properly formatted
                statdict[self.SKILLS[i]] = tuple(map(int, data))
            else:
                r = i - 24  # Adjust index for activities
                if r < len(self.ACTIVITIES):
                    # Ensure activities index does not go out of bounds
                    try:
                        # Now safely attempting to map to int
                        statdict[self.ACTIVITIES[r]] = tuple(map(int, data))
                    except ValueError:
                        # Skip entries that cannot be converted to int
                        continue
        return statdict
    

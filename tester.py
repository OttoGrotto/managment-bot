from cogs.resources.osrswrapper.osrs import OSRS as API

def test():
    """
    Test the OSRS class
    """
    user = "SoloMisclick"
    type = "ironman"
    osrs = API(user, type)
    res = osrs.get()
    with open("osrs_test.txt", "w") as f:
        f.write("User: " + user + "\n")
        for k, v in res.items():
            f.write("result: " + k + " " + str(v) + "\n")

if __name__ == "__main__":
    test()
# In our vendored copy of this file, we reworked timestamp parsing for offline use.
def parse_timestamp(value):
    return int(value.strip())

from typing import List


def add(steps: List, new_steps: List):
    return steps + new_steps


def add_clear(steps: List, new_steps: List):
    if new_steps is None or len(new_steps) == 0:
        return []
    return steps + new_steps


def add_max_10(steps: List, new_steps: List):
    combined_steps = steps + new_steps
    return combined_steps[-10:]

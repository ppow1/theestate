import re

def next_number(prefix, text):
    pattern = re.compile(rf"{prefix}-(\d+)")
    nums = [int(m.group(1)) for m in pattern.finditer(text)]
    return max(nums) + 1 if nums else 1

def make_id(prefix, number):
    return f"{prefix}-{number:06d}"

"""
Simple demonstration of doing containmenet calculation using Redis HLLs

Example Usage:
    python basics.py
"""
import redis
import uuid

r = redis.Redis(decode_responses=True, db='3')


def con(a, b):
    card_a = r.pfcount(a)
    card_b = r.pfcount(b)
    inter = abs(card_a + card_b - r.pfcount(a, b))
    return inter / card_a


# A and B share 500 identical items
same = [uuid.uuid4().hex for _ in range(0, 500)]
# A contains 1000 items
f_a = [uuid.uuid4().hex for _ in range(0, 500)] + same
# B contains 1500 items
f_b = [uuid.uuid4().hex for _ in range(0, 1000)] + same
r.pfadd('f_a', *f_a)
r.pfadd('f_b', *f_b)
print(f'A in B: {con("f_a", "f_b")}')
print(f'B in A: {con("f_b", "f_a")}')

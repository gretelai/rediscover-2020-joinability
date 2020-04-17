import redis
import uuid

r = redis.Redis(decode_responses=True, db='3')


def con(a, b):
    card_a = r.pfcount(a)
    card_b = r.pfcount(b)
    inter = abs(card_a + card_b - r.pfcount(a, b))
    return inter / card_a


same = [uuid.uuid4().hex for _ in range(0, 500)]
f_a = [uuid.uuid4().hex for _ in range(0, 500)] + same
f_b = [uuid.uuid4().hex for _ in range(0, 1000)] + same
r.pfadd('f_a', *f_a)
r.pfadd('f_b', *f_b)
print(f'A in B: {con("f_a", "f_b")}')
print(f'B in A: {con("f_b", "f_a")}')

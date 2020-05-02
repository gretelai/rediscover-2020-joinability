"""
Example script that shows margin of error between HLLs with
much different approximate cardinalities.

Example usage:
    python compare.py

NOTE: This might take a while to run
"""
import random

import redis

REDIS = redis.Redis(decode_responses=True, db='2')
COMP_A = 'hll:compare:a'
COMP_B = 'hll:compare:b'
COMP_C = 'hll:compare:c'


def check_intersect(f1, f2, desc):
    card_a = REDIS.pfcount(f1)
    card_b = REDIS.pfcount(f2)
    union = REDIS.pfcount(f1, f2)
    print('*********')
    print(desc)
    print(f'Est card A: {card_a}')
    print(f'Est card B: {card_b}')
    print(f'Est union: {union}')
    print(f'Est intersection: {abs(card_a + card_b - union)}')


def rand_num_string(n):
    return ''.join([str(random.randint(0, 9)) for _ in range(0, n)])


def compare_number_strings():
    REDIS.flushdb()
    for _ in range(0, 100000):
        REDIS.pfadd(COMP_A, rand_num_string(10))
        REDIS.pfadd(COMP_B, rand_num_string(3))
    check_intersect(COMP_A, COMP_B, '10 digit numbers vs 3 digit numbers (random)')


if __name__ == '__main__':
    compare_number_strings()

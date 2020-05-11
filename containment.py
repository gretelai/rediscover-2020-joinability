from itertools import combinations
from dataclasses import dataclass, asdict
import base64
import json

import redis

from loader import HLL_PREFIX


STD_ERR = .05
MIN_UNIQUE = 1000
MIN_SCORE = .15


@dataclass
class ContainmentResult:
    source_file: str
    source_field: str
    source_unique: int
    dest_file: str
    dest_field: str
    dest_unique: str
    score: float


def _outside_std_err(c1, c2):
    """Determine if the smaller of the two
    values is smaller than the std err value
    of the larger value
    """
    return STD_ERR*max(c1, c2) >= min(c1, c2)


def parse_redis_key(key_string):
    """Since each file and column name
    is concatted into a single redis key
    we want to split them back out
    """
    parts = key_string.split(':')
    return parts[-2], parts[-1]


def get_single_containment(field1, field1_card, field2,
                           field2_card, intersection):
    """Compute the containment of field1 in field2
    """
    field1_filename, field1_field = parse_redis_key(field1)
    field2_filename, field2_field = parse_redis_key(field2)

    score = intersection / field1_card

    score = 1 if score > 1 else score

    containment = ContainmentResult(
        source_file=field1_filename,
        source_field=field1_field,
        source_unique=field1_card,
        dest_file=field2_filename,
        dest_field=field2_field,
        dest_unique=field2_card,
        score=score
    )

    # we don't care about scoring fields
    # that are from the same source file
    if field1_filename == field2_filename:
        containment.score = 0

    return containment


def compute_containment(keynames, scores):
    """Since a containment between two fields
    is asymmmetrical, we actually return
    2 ``ContainmentResult`` instances for each
    pair of fields we are analyzing
    """
    key1, key2 = keynames
    card1, card2, union = scores

    # if _outside_std_err(card1, card2):
    #    return []

    if card1 < MIN_UNIQUE or card2 < MIN_UNIQUE:
        return []

    intersection = abs(card1 + card2 - union)

    cons = []
    con1 = get_single_containment(key1, card1, key2, card2, intersection)
    con2 = get_single_containment(key2, card2, key1, card1, intersection)

    if con1.score > MIN_SCORE:
        cons.append(con1)

    if con2.score > MIN_SCORE:
        cons.append(con2)

    return cons


def process_all_pairs(prefix='hll:*'):
    r = redis.Redis(decode_responses=True)

    # do a simple scan to check for all keys that
    # are holding the HLLs
    keys = []
    for key in r.scan_iter(match=prefix):
        keys.append(key)
    key_combos = list(combinations(keys, 2))
    pipe = r.pipeline()
    for hll1, hll2 in key_combos:
        # for each key in a tuple (a field) we compute
        # the estimated cardinality of each one
        # and the estimated cardinality of the union
        # between the two fields
        pipe.pfcount(hll1)
        pipe.pfcount(hll2)
        pipe.pfcount(hll1, hll2)

    # this returns a list of all the counts from above
    raw_scores = pipe.execute()

    # but we want to track the estimated cardinalities of
    # each field and their union per 2-tuple of fields
    # so we convert this list of raw-scores into N
    # 3-tuples where N = len(raw_scores) / 3
    # so [A, B, C, D, E, F] => [(A, B, C), (D, E, F)]
    score_tuples = [iter(raw_scores)] * 3
    score_tuples = list(zip(*score_tuples))

    # now we can iterate over our
    # field 2-tuple and cardinality 3-tuples
    # and generate a containment score
    # for each field set
    scores = []
    for keyname, score_tuple in zip(key_combos, score_tuples):
        scores.extend(compute_containment(keyname, score_tuple))

    scores = sorted(scores, key=lambda x: x.score)

    for score in scores:
        print(asdict(score))
        print()


def _serialize_signature(source, field, context, sig):
    with open(source, 'w') as fp:
        out = {
            'field': field,
            'context': context,
            'hll': base64.b64encode(sig).decode()
        }
        json.dump(out, fp)


def generate_signatures():
    """Generate a sample signature
    for the known containment we are looking for.

    In practce we would have already generated the
    context data through pre-processing steps
    """
    r = redis.Redis()
    thief_key = f'{HLL_PREFIX}:the_thief.csv.gz:number'
    bank_key = f'{HLL_PREFIX}:the_bank.csv.gz:number'

    _serialize_signature('data/thief_sig.json', 'number', 'credit_card', r.get(thief_key))
    _serialize_signature('data/bank_sig.json', 'number', 'credit_card', r.get(bank_key))


def process_from_signatures():
    """Reload the signatures back into Redis
    and compute containments. Here we're ignoring
    validating that contexts are identical
    """
    r = redis.Redis()
    with open('data/bank_sig.json', 'r') as bankfp, open('data/thief_sig.json', 'r') as thieffp:
        bank_dict = json.loads(bankfp.read())
        thief_dict = json.loads(thieffp.read())

        r.set(f'restore:bank:{bank_dict["field"]}', base64.b64decode(bank_dict['hll']))
        r.set(f'restore:thief:{thief_dict["field"]}', base64.b64decode(thief_dict['hll']))

    process_all_pairs(prefix='restore:*')


if __name__ == '__main__':
    print('**** Processing HLLs in Redis ****\n')
    process_all_pairs()
    print('\n\n**** Exporting 2 HLLs to disk ****\n')
    generate_signatures()
    print('\n\n**** Restoring signatures from disk to Redis ****\n')
    process_from_signatures()

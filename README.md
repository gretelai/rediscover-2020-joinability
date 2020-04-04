# Getting Started

Be sure to have Docker installed and Python 3.7+ installed, that's what this was tested with, YMMV on older versions.

You'll also need `redis-cli` installed.

```
virtuenenv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run a localized Redis instance:

```
docker run -d --name redisconf -p 6379:6379
```

Generate some records, for the preso I generated 2M, 50k, and 25k bank records, thief records, and the intersection. Feel free to adjust. If you use
the same numbers, sit back and relax while they generate.

Alternatively, this sample data is available here:

- TODO
- TODO

You can download this into a `data` directory in the root of the repo.

```
python generate_bank_data.py 2000000 50000 25000
```

Now load this data into Redis using the mass ingest pipeline.

**NOTE:** We're not flushing Redis at all, so if you're trying this multiple times, flushing the db is up to you if you want.

```
python loader.py data | redis-cli --pipe
```

Generate the containment scores and output containment signature files

```
python containment.py
```

# Situation + Calculation in a perfect world

"The Bank" has 2 million credit card customers. Each customer with a unique credit card. We'll call this Field A.

"The Thief" has just published a collection of 50,000 credit cards, half of them are from "The Bank." We'll call this Field B. The other half
of "The Thief's" stash are from other banks.

## Using the Jaccard Index

Intersection (between The Bank and The Thief): 25,000

Union: 2,000,000 + 25,000 (The 50k not from "The Bank")

Intersection / Union = .

## Using Containment

The containment of A in inside of B can be calculated as:

intersection(A, B) / cardinality(A)

The intersection(A, B) can be calculated as:

cardinality(A) + cardinality(B) - cardinality(union(A, B))

### The containment of "The Bank's" card inside of "The Thief's" stash

cardinality(A) = 5,000,000
cardinality(B) = 100,000
cardinality(union(A, B)) = 5,050,000 (remember, half of "The Thief's" cards are from somewhere else)

intersection(A, B) = 5,000,000 + 100,000 - 5,050,000 = 50,000

Containment = 50,000 / 5,000,000 = 1%

So, 1% of "The Bank's" cards are inside of "The Thief's" stash.

### The containment of "The Thief's" cards inside of "The Bank's" customer list

We already know the intersection(A, B) is 50,000

Containment: 50,000 / 100,000 = 50%

So, 50% of "The Thief's" stash, are from the "The Bank"
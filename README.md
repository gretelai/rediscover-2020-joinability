# Getting Started

Be sure to have Docker installed and Python 3.7+ installed, that's what this was tested with, YMMV on older versions.

You'll also need `redis-cli` installed.

```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run a localized Redis instance:

```
docker run -d --name redisconf -p 6379:6379 redis:5
```

Generate some records, for the preso I generated 2M, 50k, and 25k bank records, thief records, and the intersection, respectively. Feel free to adjust. If you use
the same numbers, sit back and relax while they generate.

Alternatively, this sample data is available here:

- https://rediscover-joinability.s3-us-west-2.amazonaws.com/the_bank.csv.gz
- https://rediscover-joinability.s3-us-west-2.amazonaws.com/the_thief.csv.gz

You can download each file into a `data` directory in the root of the repo.

If you choose to generate your own...

```
python generate_bank_data.py 2000000 50000 25000
```

Now load this data into Redis using the mass ingest pipeline.

**NOTE:** We're not flushing Redis at all, so if you're trying this multiple times, flushing the db is up to you if you want.

```
python loader.py data | redis-cli --pipe
```

Generate the containment scores, output sample signatures, and restore signatures for comparison

```
python containment.py
```

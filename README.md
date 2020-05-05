# Getting Started

Be sure to have Docker installed and Python 3.7+ installed, that's what this was tested with, YMMV on older versions of Python.

You can run `redis-server` separate of Docker, too, as long as port 6379 is exposed to the localhost!

You'll also need `redis-cli` installed. I tested this on OS X so a `brew install redis` will install the client tools.

```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run a localized Redis instance:

```
docker run -d --name redisconf -p 6379:6379 redis:5
```

Generate some records, for the preso I generated 2M, 50k, and 25k bank records, thief records, and the intersection, respectively. Feel free to adjust. This dataset
takes a while to generate. You can use a smaller set of numbers like this to generate
some data locally fairly quickly:

```
python generate_bank_data.py 50000 10000 5000
```

Alternatively, this sample data is available here:

- https://rediscover-joinability.s3-us-west-2.amazonaws.com/the_bank.csv.gz
- https://rediscover-joinability.s3-us-west-2.amazonaws.com/the_thief.csv.gz

You can download each file into a `data` directory in the root of the repo.

Now load this data into Redis using the mass ingest pipeline.

**NOTE:** When loading the data, we'll automatically delete the previous
HLL keys that were used.

```
python loader.py data | redis-cli --pipe
```

Generate the containment scores, output sample signatures, and restore signatures for comparison

```
python containment.py
```

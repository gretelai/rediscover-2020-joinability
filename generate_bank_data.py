import logging
import csv
import random
import gzip
import sys

import faker
import faker.providers.credit_card as cc

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# generate a reverse mapping of a card type description
# to the actual card type string we can use in faker
CARD_MAP = {}
for card_type, CC in cc.Provider.credit_card_types.items():
    CARD_MAP[CC.name] = card_type


class Generator:

    BANK_HEADERS = ['type', 'name', 'number', 'exp', 'cvv']
    THIEF_HEADERS = ['type', 'number', 'cvv']

    def __init__(self, *, bank_card_type=None, bank_count,
                 thief_card_type=None, thief_count,
                 intersection):
        self.faker = faker.Faker()
        self.bank_card_type = bank_card_type
        self.thief_card_type = thief_card_type
        self.bank_count = bank_count
        self.thief_count = thief_count
        self.intersection = intersection

    def _generate_bank_row(self):
        provider = self.faker.credit_card_provider(
            card_type=self.bank_card_type
        )
        tmp = (
            provider,
            self.faker.name(),
            self.faker.credit_card_number(card_type=CARD_MAP[provider]),
            self.faker.credit_card_expire(),
            self.faker.credit_card_security_code(card_type=CARD_MAP[provider])
        )
        return dict(zip(self.BANK_HEADERS, tmp))

    def _generate_thief_row(self):
        provider = self.faker.credit_card_provider(
            card_type=self.thief_card_type
        )
        tmp = (
            provider,
            self.faker.credit_card_number(card_type=CARD_MAP[provider]),
            self.faker.credit_card_security_code(card_type=CARD_MAP[provider])
        )
        return dict(zip(self.THIEF_HEADERS, tmp))

    def start(self):
        # we will randomly extract the amount of overlapping records
        # between bank and thief as we generate the bank records
        # this way we don't have to reload the bank records to
        thief_idxs = sorted(random.sample(range(0, self.bank_count), self.intersection))

        logger.info(f'Generating {self.bank_count} bank records...')

        stolen = []

        with gzip.open('data/the_bank.csv.gz', 'wt') as fp:
            writer = csv.DictWriter(fp, fieldnames=self.BANK_HEADERS)
            writer.writeheader()

            for i in range(0, self.bank_count):
                row = self._generate_bank_row()
                writer.writerow(row)
                if i in thief_idxs:
                    stolen_row = {k: v for k, v in row.items() if k in self.THIEF_HEADERS}
                    stolen.append(stolen_row)

                    # truncate the stolen idx list
                    thief_idxs.pop(0)

        # how many more stolen cards should we generate that
        # are not part of The Bank
        more_stolen = self.thief_count - len(stolen)

        logger.info(f'Generating {more_stolen} additional stolen records...')

        if more_stolen > 0:
            for i in range(0, more_stolen):
                stolen.append(self._generate_thief_row())

        with gzip.open('data/the_thief.csv.gz', 'wt') as fp:
            writer = csv.DictWriter(fp, fieldnames=self.THIEF_HEADERS)
            writer.writeheader()
            for row in stolen:
                writer.writerow(row)


if __name__ == '__main__':
    bank_count, thief_count, intersection = sys.argv[1:]  # pylint: disable=unbalanced-tuple-unpacking
    generator = Generator(bank_count=int(bank_count), thief_count=int(thief_count), intersection=int(intersection))
    generator.start()

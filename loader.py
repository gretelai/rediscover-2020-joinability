from abc import ABC, abstractmethod
from pathlib import Path
from csv import DictReader
import sys
from base64 import b64encode

from smart_open import open

HLL_PREFIX = 'hll'


def create_resp(*cmd_parts):
    cmd = ''
    cmd += '*' + str(len(cmd_parts)) + '\r\n'
    for part in cmd_parts:
        cmd += '$' + str(len(part)) + '\r\n'
        cmd += part + '\r\n'
    return cmd


def create_redis_hll_command(source, field, value):
    """Given a data source name, create a PFCOUNT
    command to update the source + field's HLL
    bitfield
    """
    redis_key = f'{HLL_PREFIX}:{source}:{field}'
    # return create_resp(*['PFADD', redis_key, b64encode(value.lower().encode()).decode()])
    return create_resp(*['PFADD', redis_key, value.lower()])


class Dataset(ABC):

    def __init__(self, source, skip_values=[]):
        p = Path(source)
        self.files = []
        self.skip_values = frozenset(skip_values)
        if p.is_file():
            self.files.append(
                (p.name, str(p.resolve()))
            )
        elif p.is_dir():
            for child in p.iterdir():
                self.files.append(
                    (child.name, str(child.resolve()))
                )

    @abstractmethod
    def field_value_hll_commands(self):
        pass


class CSV(Dataset):

    def field_value_hll_commands(self):
        for fname, abs_path in self.files:
            if fname.startswith('.'):  # catch dumb shit like .DS_Store
                continue
            with open(abs_path, 'r') as fp:
                reader = DictReader(fp)
                try:
                    for row in reader:
                        for field, value in row.items():
                            if value not in self.skip_values:
                                resp = create_redis_hll_command(
                                    fname,
                                    field,
                                    str(value)
                                )
                                yield resp
                except Exception:
                    raise


if __name__ == '__main__':
    ds = CSV(sys.argv[1], skip_values=['NULL'])
    for resp in ds.field_value_hll_commands():
        if resp:
            sys.stdout.write(resp)

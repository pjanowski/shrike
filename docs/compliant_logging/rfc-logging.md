# Logging in Compliant ML

| Owner | Approvers | Participants |
| - | - | - |
| [Daniel Miller](mailto:danmill@microsoft.com) | [Jeff Omhover](mailto:jeomhove@microsoft.com) | AML DS Team |

In many corporations, data scientists are working to build and train machine
learning models under extremely strict compliance and privacy requirements.
These can include:

- Being unable to directly access or view the customer data used to train a
  model.
- Being unable to run unsigned code against customer data, except possibly in
  specialized compute clusters with no network access and other hardening in
  place.
- All training logs removed, except possibly those starting with some fixed
  prefix (e.g., `SystemLog:`).

Machine learning is already a hard problem &mdash; building and training models
under these constraints is even more difficult. This RFC (**R**equest **F**or
**C**omment) proposes the code patterns and expected behavior of a to-be-written
logging utility for compliant machine learning. It begins by outlining the
requirements this utility would need to satisfy, then gives a concrete proposal
with sample code. It proceeds to outline some alternatives, along with known
risks of the proposal.

The following topics are out of scope for this RFC:

- How to implement the proposed behavior. It considers only usage patterns and
  the intended behavior of the logging utility library.
- Compliant argument parsing.
- Compliant exception handling (how to keep and prefix the stack trace and
  exception type, while scrubbing exception messages).
- Languages besides Python.

## Requirements

Every call to log a message should be forced to include information on whether
the message is "safe" (does not contain any customer or sensitive data). If the
message is safe, the log line should be mutated to contain a configurable
prefix (e.g., `SystemLog:`).

The default behavior of this library should be to **not** add the "don't scrub"
prefix. It should only add that prefix if a conscious decision has been made,
possibly by choosing a different method name or parameter value.

This library should not rely on users naming variables "well". That is, if a
user accidentally names a logger `safeLogger`, there should be no data leak if
that logger was not pre-configured on some special way.

Code which consumes this library should have the same "look and feel" as code
consuming the Python standard library's
[`logging`](https://docs.python.org/3/library/logging.html) module.

:warning: This entire document relies on the assumption that the filtering
mechanism looks for a specific prefix in log lines.

## Proposal

I propose that the existing logging paradigm in Python be mostly unchanged, with
the following small differences:

- Calls to `getLogger` **must** include a `safe_prefix` parameter.
    - Open question: should this be more flexible, e.g. a callable or dictionary
      mapping data categories to prefixes or format strings?
- Calls to `logger.*` have a new optional parameter taking enum values. The
  default value is `CONTAINS_PRIVATE_DATA`, i.e. if this parameter is not
  explicitly provided the "safe" prefix will not be added.

Here is some sample code following this proposal.

```python
import argparse
from shrike.compliant_logging import logging
from shrike.compliant_logging.constants import DataCategory

def main(logger):
    # HAS a prefix.
    logger.warning('safe message', category=DataCategory.ONLY_PUBLIC_DATA)

    # DOES NOT have a prefix.
    logger.warning('unsafe message')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prefix', default='SystemLog:')
    args = parser.parse_args()

    # logger will be an instance of a subclass of the logging.Logger class.
    logger = logging.getLogger(__name__, args.prefix)
    main(logger)
```

Open question: should the compliant `logging.getLogger` method throw an
exception if the non-compliant `logging` namespace is in scope?

## Alternatives

### Global `log` function

Global `log` function.

Not just prefix, more complicated "mutation" logic.

### Hash unsafe log lines

Provide option to hash unsafe log lines.

- Not compliant.
- Other option, record their length `Unsafe log message of length 23`

### Write public logs to pre-specified location

Instead of adding a predetermined prefix to "public" logs, depending on the
log filtering / scrubbing mechanisms, another alternative would be to write
public logs to a specific file.

## Risks

### Abuse

This logging utility will not prevent malicious abuse. That is, there is no
way from the code to stop someone from writing a line like this.

```python
logger.info('private data', category=DataCategory.ONLY_PUBLIC_DATA)
```

However, this risk is not new, nor does it arise uniquely because of the
proposed library. There is **already** nothing to prevent a malicious actor from
writing this line

```python
print('SystemLog: private data')
```

Compliant machine learning in this context involves an element of trust, i.e.
it is not designed or intended to stop malicious actors.

We do **not** attempt to mitigate this risk by filtering out specific types of
objects from "public" logs. Standard Python types like `str` and
`pandas.DataFrame` can easily contain sensitive customer data. If we exclude
those from logging, we will be excluding nearly all helpful logs.

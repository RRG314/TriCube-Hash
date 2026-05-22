# Running Statistical Batteries

The scripts in this directory stream bytes from the C CLI into external tools.
They do not install those tools.

TriCube does not bundle PractRand, Dieharder, TestU01, SmokeRand, NIST STS, or
their binaries. Install each tool from its upstream source or your package
manager, then follow that tool's license. The repository notice table is
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

Most commands below test native stream output. Hash-mode testing is different:
it concatenates 32-byte digests of many deterministic messages. Use the helper
below when a battery input should come from the hash API rather than stream
mode, and label the result as a digest-concatenation test:

```bash
c/build/tricube digest-stream \
  --variant hashfast1024 \
  --seed 123 \
  --messages 524288 \
  --message-bytes 64 \
  --out - \
| RNG_test stdin32 -tlmin 1KB -tlmax 16MB -tf 2 -te 1
```

Digest-concatenation batteries are useful for hash-output screening, but they
do not replace native XOF/stream tests or cryptanalysis.

## PractRand

```bash
tools/run_practrand.sh 1073741824
VARIANT=fast8x tools/run_practrand.sh 1073741824
```

This runs `RNG_test stdin32` with expanded testing and extra folding. A WARN or
FAIL must be investigated. A pass does not prove security.

PractRand can be run at a fixed maximum length. For a quick regression screen,
use 256 MiB. For a standard development run, use 1-10 GiB. For a long campaign,
use 100 GiB or more across multiple seeds. Record any unusual, suspicious, or
FAIL rows as WARN or FAIL rather than smoothing them into a pass.

## Dieharder

```bash
tools/run_dieharder.sh 1073741824
VARIANT=fast8x tools/run_dieharder.sh 1073741824
```

This uses stdin generator mode (`-g 200`) and `-a` to request the installed
Dieharder battery.

Dieharder reports many p-values, so occasional WEAK rows can happen by chance.
The important questions are whether failures reproduce, whether the same test
keeps warning across seeds, and whether the input stream or stdin generator
exhausted before the battery finished.

## SmokeRand

```bash
tools/run_smokerand.sh express 536870912
VARIANT=fast8x tools/run_smokerand.sh express 536870912
UNBOUNDED=1 VARIANT=fast8x tools/run_smokerand.sh full 1099511627776
```

The SmokeRand wrapper streams 64-bit stdin input. `UNBOUNDED=1` is useful for
full batteries that decide their own stopping point.

SmokeRand supports `express`, `brief`, `default`, and `full` batteries. The
full battery is the right long-run target, but it should be recorded separately
from express results. A timeout is a harness/runtime blocker, not a statistical
failure.

## TestU01

```bash
TESTU01_STDIN=path/to/testu01_stdin32 tools/run_testu01.sh smallcrush 1073741824
TESTU01_STDIN=path/to/testu01_stdin32 tools/run_testu01.sh crush 1073741824
TESTU01_STDIN=path/to/testu01_stdin32 tools/run_testu01.sh bigcrush 1099511627776
VARIANT=fast8x TESTU01_STDIN=path/to/testu01_stdin32 tools/run_testu01.sh smallcrush 1073741824
```

The `testu01_stdin32` wrapper is not part of upstream TestU01; it must be built
by the reviewer or provided as an existing executable.

SmallCrush is a quick regression gate. Crush is the normal development target.
BigCrush is a long campaign and should be run with progress logging because it
can take hours depending on machine speed and input throughput.

## NIST STS

Follow the dedicated workflow in [run_nist_sts.md](run_nist_sts.md). The STS
`assess` binary uses its own experiment-directory format and should be treated
as an external tool, not as a bundled TriCube dependency.

## Suggested Profiles

Quick profile:

```bash
python tests/crypto_analysis/run_all_screens.py --profile quick --variants baseline,fast8x --out tests/crypto_analysis/results/quick-latest
tools/run_practrand.sh 268435456
tools/run_smokerand.sh express 536870912
TESTU01_STDIN=path/to/testu01_stdin32 tools/run_testu01.sh smallcrush 1073741824
```

Standard profile:

```bash
tools/run_practrand.sh 1073741824
VARIANT=fast8x tools/run_practrand.sh 10737418240
tools/run_dieharder.sh 1099511627776
TESTU01_STDIN=path/to/testu01_stdin32 tools/run_testu01.sh crush 1073741824
```

Long profile:

```bash
VARIANT=fast8x tools/run_practrand.sh 107374182400
UNBOUNDED=1 VARIANT=fast8x tools/run_smokerand.sh full 1099511627776
TESTU01_STDIN=path/to/testu01_stdin32 tools/run_testu01.sh bigcrush 1099511627776
```

Each run should record the variant, seed, byte count, command line, tool
version, machine, compiler, and whether the status is PASS, WARN, FAIL,
BLOCKED, or NOT_RUN.

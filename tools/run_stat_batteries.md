# Running Statistical Batteries

The scripts in this directory stream bytes from the C CLI into external tools.
They do not install those tools.

TriCube does not bundle PractRand, Dieharder, TestU01, SmokeRand, NIST STS, or
their binaries. Install each tool from its upstream source or your package
manager, then follow that tool's license. The repository notice table is
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

## PractRand

```bash
tools/run_practrand.sh 1073741824
VARIANT=fast8x tools/run_practrand.sh 1073741824
```

This runs `RNG_test stdin32` with expanded testing and extra folding. A WARN or
FAIL must be investigated. A pass does not prove security.

## Dieharder

```bash
tools/run_dieharder.sh 1073741824
VARIANT=fast8x tools/run_dieharder.sh 1073741824
```

This uses stdin generator mode (`-g 200`) and `-a` to request the installed
Dieharder battery.

## SmokeRand

```bash
tools/run_smokerand.sh express 536870912
VARIANT=fast8x tools/run_smokerand.sh express 536870912
UNBOUNDED=1 VARIANT=fast8x tools/run_smokerand.sh full 1099511627776
```

The SmokeRand wrapper streams 64-bit stdin input. `UNBOUNDED=1` is useful for
full batteries that decide their own stopping point.

## TestU01

```bash
TESTU01_STDIN=path/to/testu01_stdin32 tools/run_testu01.sh smallcrush 1073741824
TESTU01_STDIN=path/to/testu01_stdin32 tools/run_testu01.sh crush 1073741824
TESTU01_STDIN=path/to/testu01_stdin32 tools/run_testu01.sh bigcrush 1099511627776
VARIANT=fast8x TESTU01_STDIN=path/to/testu01_stdin32 tools/run_testu01.sh smallcrush 1073741824
```

The `testu01_stdin32` wrapper is not part of upstream TestU01; it must be built
locally or provided by the user.

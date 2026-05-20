# Third-Party Notices

TriCube is released under the MIT License. The Python package and wheel do not
bundle external statistical batteries, third-party cryptographic libraries,
large result logs, or prebuilt external-tool binaries.

The repository references optional external tools so reviewers can reproduce the
statistical screening described in the results. Those tools must be installed
separately and used under their own upstream licenses.

| Tool or project | How TriCube uses it | Bundled in TriCube? | License / source note |
|---|---|---:|---|
| SmokeRand | Optional statistical battery referenced in result summaries and reproduction notes. | No | Upstream repository reports MIT License: <https://github.com/alvoskov/SmokeRand>. |
| PractRand | Optional random-stream statistical testing through `RNG_test`. | No | SourceForge lists PractRand as Public Domain: <https://sourceforge.net/projects/pracrand/>. |
| Dieharder | Optional random-stream statistical battery through stdin generator mode. | No | Upstream COPYING grants use under GNU GPL v2 or later with the project's stated modification. See <https://github.com/seehuhn/dieharder>. |
| TestU01 | Optional SmallCrush, Crush, and BigCrush testing through a local stdin wrapper. | No | Current official TestU01-2009 repository reports Apache-2.0: <https://github.com/umontreal-simul/TestU01-2009>. Older archives or mirrors may carry different terms; use the license shipped with the copy you install. |
| NIST STS | Optional NIST Statistical Test Suite checks. | No | NIST describes the STS software as public domain with a software disclaimer. See <https://csrc.nist.gov/projects/random-bit-generation/documentation-and-software>. |
| SHA-2, SHA-3/SHAKE, BLAKE2, BLAKE3, Keccak, CubeHash, Xoodoo/Xoodyak, KangarooTwelve | Referenced for comparison and literature context. | No | These are citations and comparison targets only. TriCube does not copy their implementations. |
| Python `hashlib` | Used in local benchmark scripts for standard-library comparison. | No separate vendoring | Part of the Python standard library. |

Result logs may mention external tool names, versions, and output summaries.
Those logs are evidence records only; they are not redistributed copies of the
external tools.

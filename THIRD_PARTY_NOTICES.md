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
| Z3 | Optional SMT solver for future reduced-round bit-vector models. | No | MIT License. See <https://github.com/Z3Prover/z3>. |
| SageMath | Optional algebraic system for future Boolean polynomial and ANF experiments. | No | GPL-licensed open-source mathematics system. See <https://www.sagemath.org/>. |
| CryptoMiniSat | Optional SAT solver for future CNF experiments. | No | Upstream project reports default MIT-licensed build material; optional integrations can alter licensing. See <https://github.com/msoos/cryptominisat>. |
| CLAASP | Optional future framework for automated analysis of symmetric primitives. | No | PyPI metadata lists GPLv3. See <https://pypi.org/project/claasp/> and <https://claasp.readthedocs.io/>. |
| CryptoSMT | Optional future SMT/SAT cryptanalysis framework. | No | Upstream project: <https://github.com/kste/cryptosmt>. Use the license shipped with the installed copy. |
| ArxPy | Optional future ARX cryptanalysis framework to investigate. | No | Project documentation: <https://ranea.github.io/ArxPy/>. Use the license shipped with the installed copy. |
| SHA-2, SHA-3/SHAKE, BLAKE2, BLAKE3, Keccak, CubeHash, Xoodoo/Xoodyak, KangarooTwelve | Referenced for comparison and literature context. | No | These are citations and comparison targets only. TriCube does not copy their implementations. |
| Python `hashlib` | Used in local benchmark scripts for standard-library comparison. | No separate vendoring | Part of the Python standard library. |

Result logs may mention external tool names, versions, and output summaries.
Those logs are evidence records only; they are not redistributed copies of the
external tools.

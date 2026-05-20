# Comparison to Known Hash and XOF Work

TriCube sits near established hash and XOF design families, but it is not mature like those systems.

SHA-2 is standardized in NIST FIPS 180-4. SHA-3 and SHAKE are standardized in NIST FIPS 202 and are based on Keccak. BLAKE2 and BLAKE3 are mature high-performance hash designs with extensive public review and optimized implementations. CubeHash was a NIST SHA-3 competition candidate and is the closest name-level comparison because it also uses cube language, but TriCube's current candidate distinction is a tetrahedral/cube-connected state evolution rather than CubeHash's specific parameterized round function.

TriCube also resembles sponge and ARX systems in broad structure: it absorbs input, permutes state, and squeezes output using addition, xor, and rotation operations. Those ingredients are not novel by themselves.

## What May Be Distinctive

The part worth studying is the state topology:

- 2048-bit state with lanes mapped to a cube-connected vertex grid;
- deterministic tetrahedral decomposition of cube cells;
- orientation-dependent local tetrahedral mixing;
- edge-coupled propagation between neighboring vertices;
- shell/global lanes used for cross-state mixing and metadata.

That structure may or may not survive cryptanalytic review. The repository keeps the claim narrow so review can focus on the actual mechanism.

## Baselines and References

- NIST FIPS 180-4, Secure Hash Standard: https://csrc.nist.gov/pubs/fips/180-4/upd1/final
- NIST FIPS 202, SHA-3 Standard: https://csrc.nist.gov/pubs/fips/202/final
- BLAKE2: https://www.blake2.net/
- BLAKE3 implementation and specification links: https://github.com/BLAKE3-team/BLAKE3
- Keccak Team: https://keccak.team/
- KangarooTwelve: https://keccak.team/kangarootwelve.html
- CubeHash reference material: https://ehash.isec.tugraz.at/wiki/CubeHash.html

The comparison status is incomplete until TriCube has a full benchmark set against optimized C implementations and independent cryptanalysis against the reduced-round and full-round construction.


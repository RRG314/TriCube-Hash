# NIST STS Workflow

NIST STS expects bitstreams in its own input format and configuration flow.
TriCube does not bundle NIST STS.

Generate a stream first:

```bash
make -C c all
c/build/tricube stream --seed 123 --bytes 12500000 --out results/tmp/tricube_100m_bits.bin
```

Then follow the NIST STS documentation for binary-file input. A common starting
point is 100 streams of 1,000,000 bits, but the exact setup must be recorded in
the result artifact.

Official NIST RBG documentation and software:

https://csrc.nist.gov/Projects/random-bit-generation/Documentation-and-Software

Passing NIST STS is not a cryptographic-security proof.


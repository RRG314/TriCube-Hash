# PractRand 1 GiB Summary - 2026-05-19

Status: **WARN**

This run tested the C TriCube stream generator with PractRand 0.96 using the expanded test set and extra folding.

## Public Reproduction Command

```bash
make -C c all
c/build/tricube stream --seed 123 --bytes 1073741824 --out - \
| RNG_test stdin32 -tlmin 1KB -tlmax 1GB -tf 2 -te 1
```

## Result

PractRand reached `1 gigabyte (2^30 bytes)` and the final level reported:

```text
length= 1 gigabyte (2^30 bytes), time= 152 seconds
  no anomalies in 2050 test result(s)
```

Earlier levels reported low-bit anomalies:

```text
length= 1 megabyte (2^20 bytes)
  [Low1/64]NS3[2:hw:both]           R=  +5.1  p~=  1.4e-7   suspicious
  [Low1/64]NS3[2:hw:all-]           R=  +4.4  p~=  1.9e-6   unusual
  [Low4/32]NS3[4:hw:both]           R=  +4.9  p~=  3.8e-7   mildly suspicious
  [Low4/32]NS3[4:hw:all-]           R=  +4.0  p~=  1.2e-5   unusual

length= 2 megabytes (2^21 bytes)
  [Low1/64]NS3[2:hw:both]           R=  +4.1  p~=  1.7e-5   unusual

length= 512 megabytes (2^29 bytes)
  [Low1/32]NS3[1:pd:both]           R=  +4.0  p~=  3.5e-5   unusual
```

## Interpretation

This is not a clean pass. The final 1 GiB level reported no anomalies, but the earlier low-bit warnings are real and must be investigated. The right next steps are multi-seed reruns, low-bit-focused diagnosis, 10 GiB PractRand, TestU01 Crush/BigCrush, and reduced-round analysis.


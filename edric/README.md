# Edriç port workbench

This directory is for direct Edriç translations of the Futhark benchmarks.
The original `.fut` programs remain the semantic reference.

## Compiler target

The first `f32` port targets `isomorphisms/Idric` branch
`float32-primitive`, currently at commit
`249921a30b9fc5b9e842dbb6489a4d8d231b6174` (Idric PR #6).

That branch matters because Futhark `f32` must stay 32-bit.  Do not silently
translate it to `Double`.

New Edriç source should prefer the mathematical spellings already accepted in
`.idric` source, including `→` and `⇒`.  Locally useful mathematical operators
may also be defined explicitly; the first port defines `∘` for composition.

## Current boundary

The first translation is `micro/intra.fut` → `edric/micro/intra.idric`.
It preserves the computation but deliberately uses `List` as a temporary
semantic carrier.  This is **not** a performance port: Futhark arrays are
contiguous arrays, while Edriç does not yet have the benchmark-grade contiguous
array surface needed for a fair comparison.

So the order is:

1. preserve the computation and scalar semantics;
2. keep the Futhark program as the reference;
3. replace the temporary list carrier with a real Edriç array abstraction;
4. compare outputs on the same fixtures;
5. only then compare timings or generated backends.

For `micro/intra.fut`, Futhark's

```text
map (scan (+) 0 >-> f32.sum)
```

becomes the same composition directly in Edriç:

```text
map (sum_values ∘ prefix_sums 0)
```

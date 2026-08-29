# Edriç port workbench

This directory is for direct Edriç translations of the Futhark benchmarks.
The original `.fut` programs remain the semantic reference.

## Compiler target

The first `f32` ports target `isomorphisms/Idric` branch
`float32-primitive`, currently at commit
`249921a30b9fc5b9e842dbb6489a4d8d231b6174` (Idric PR #6).

That branch matters because Futhark `f32` must stay 32-bit. Do not silently
translate it to `Double`.

New Edriç source should prefer the mathematical spellings already accepted in
`.idric` source, including `→` and `⇒`. Locally useful mathematical operators
may also be defined explicitly; the `intra` port defines `∘` for composition.

## First translations

- `micro/intra.fut` → `edric/micro/intra.idric`
- `babelstream/babelstream.fut` → `edric/babelstream/babelstream.idric`

BabelStream carries over `copy`, scale/multiply, add, triad, dot, and nstream
for both 32-bit `Float` and 64-bit `Double`.

## Current boundary

These first translations preserve the computations but deliberately use `List`
as a temporary semantic carrier. This is **not** a performance port: Futhark
arrays are contiguous arrays, while Edriç does not yet have the benchmark-grade
contiguous array surface needed for a fair comparison.

Futhark also guarantees equal array shapes statically. The temporary BabelStream
`pair_map` assumes that invariant; behavior for unequal lists is not part of the
translation contract.

So the order is:

1. preserve the computation and scalar semantics;
2. keep the Futhark program as the reference;
3. replace the temporary list carrier with a real Edriç array abstraction;
4. make shape equality explicit at the Edriç boundary;
5. compare outputs on the same fixtures;
6. only then compare timings or generated backends.

For `micro/intra.fut`, Futhark's

```text
map (scan (+) 0 >-> f32.sum)
```

becomes the same composition directly in Edriç:

```text
map (sum_values ∘ prefix_sums 0)
```

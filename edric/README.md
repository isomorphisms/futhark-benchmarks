# Edriç port workbench

This directory is for direct Edriç translations of the Futhark benchmarks.
The original `.fut` programs remain the semantic reference.

## Compiler target

The `f32` ports target the exact `isomorphisms/Idric` commit
`249921a30b9fc5b9e842dbb6489a4d8d231b6174`.  At that commit, `Float` is a
primitive IEEE-754 binary32 value and every value-producing arithmetic
operation rounds at the binary32 boundary.

The checked Futhark reference compiler is version `0.27.1`.

Do not replace the commit with the moving `float32-primitive` branch name.  The
same open branch was later developed into a different source policy that
normalises `.idric` `Float` and `Float32` requests to `Float16`.  That policy
cannot serve as an oracle for a Futhark program whose source explicitly says
`f32`.  `edric/check` refuses any compiler commit other than the binary32 pin.

The pinned compiler cannot marshal its new `Float` primitive directly through
the inherited FFI.  The Chez storage adapter therefore transports a value
through `Double` immediately around the foreign call.  This does not change
the array contract: cells occupy four contiguous bytes, reads round back to
`Float`, all kernel arithmetic is `Float`, and the comparison checks resulting
binary32 bit patterns rather than printed decimal spelling.

## Shape and storage contract

`ContiguousArray.idric` supplies the forcing abstraction:

- `Shape` is a list of axis extents.  It is shape information, not storage and
  not a mathematical vector.
- `Array shape element` is row-major contiguous storage indexed by the entire
  shape and scalar type.
- The storage constructor is hidden.  The current checked constructors create
  exactly four bytes per `Float` cell and reject a wrong value count or a byte
  count that cannot fit in the host `Int` boundary.
- Kernels receive `Array shape Float` arguments with the same `shape` variable.
  There is no unequal-shape or truncating clause.
- `RuntimeArray` packages a runtime-discovered shape with the array it indexes.
  `same_shape` either returns two arrays sharing one type-level shape or an
  explicit `unequal_shapes` result.

A `List Float` appears only when a small diagnostic fixture is imported or
materialised for comparison.  It is no longer the kernel storage carrier.

## Direct ports

- `babelstream/babelstream.fut` → `BabelStream.idric`
- `micro/intra.fut` → `Intra.idric`

The BabelStream port covers the original binary32 `copy`, multiply, add,
triad, nstream, and dot entries.  The Futhark file's binary64 entries remain in
the reference file, but this Edriç boundary does not introduce a `Double`
array surface merely because BabelStream contains them.

`Intra.idric` has the exact entry shape `Array [rows, 6] Float`.  Its inclusive
row scan and row sum remain two explicit semantic phases.  A future optimiser
may fuse them; the source port does not manually pre-empt that compiler
decision.

## Semantic check

With the pinned compiler built and Futhark available:

```sh
EDRIC_ROOT=/path/to/Idric-at-249921a3 \
FUTHARK=/path/to/futhark \
sh edric/check
```

The check:

1. compile-checks the array and both port modules;
2. requires `ShapeMismatch.idric` to fail because `[2]` and `[3]` cannot unify;
3. checks runtime equal-shape acceptance, unequal-shape refusal, and exact cell
   count refusal;
4. runs deterministic fixtures through the Edriç ports and the original
   Futhark entries;
5. compares every output as IEEE-754 binary32 bits.

The checked fixture includes the `2^24` boundary, signed zero, non-exact
decimal inputs, all six binary32 BabelStream operations, and two independent
rows for `micro/intra`.

## Deliberately deferred

This is a semantic and storage boundary, not a timing result.  It does not yet
claim:

- benchmark-grade allocation or generated-code performance;
- mutable/linear reuse of BabelStream's unique `nstream` input;
- strides, views, broadcasting, reshaping, or a tensor interface;
- a final surface syntax for shapes;
- non-Chez storage adapters or direct CPU/GPU lowering;
- reconciliation of exact external `f32` requests with Idriç's later
  Float16-default source policy.

Those are separate decisions.  In particular, future tensor, Einstein-index,
and mathematical-vector structure should sit above this array/storage layer,
not be collapsed into it.

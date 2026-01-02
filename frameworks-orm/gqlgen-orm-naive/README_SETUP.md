# gqlgen-orm-naive Setup Issue

## Current Status
⚠️ **Not fully operational** - Code generation step has dependency issues

## Problem
The gqlgen code generation requires generated interfaces that don't exist yet, creating a bootstrap problem:
- `resolver.go` references `QueryResolver`, `UserResolver`, etc. interfaces
- These interfaces should be generated in `graph/generated.go`
- gqlgen generate crashes with segfault when trying to generate

## Error
```
panic: runtime error: invalid memory address or nil pointer dereference
at golang.org/x/tools/go/packages.(*loader).loadPackage
```

## What's Been Tried
1. ✅ Added gqlgen code generation step to Dockerfile
2. ✅ Updated Go version to 1.24 (required by dependencies)
3. ✅ Updated gqlgen to v0.17.31
4. ✅ Installed gqlgen as a tool before running generate
5. ❌ Segfault during code generation

## Potential Solutions
1. **Pre-generate code**: Generate `graph/generated.go` and `graph/model/models_gen.go` locally and commit them
2. **Use different gqlgen version**: Try older/newer versions that might not segfault
3. **Restructure project**: Match the structure of working `frameworks/go-gqlgen`
4. **Skip models generation**: Configure gqlgen to use existing GORM models instead of generating new ones

## Workaround
For benchmarking purposes, use the optimized `frameworks/go-gqlgen` which has working code generation, or manually generate the files locally and commit them to the repository.

## Files That Need Generation
- `graph/generated.go` - Main gqlgen generated code (~130KB)
- `graph/model/models_gen.go` - GraphQL model types


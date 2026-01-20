# ClangConverter

Bidirectional converter between Charless (v3) and C language.

## Tools

### charless2c.py
Transpiles Charless bytecode (.cless) to C source code (.c).

**Usage:**
```bash
python3 charless2c.py input.cless output.c
```

**Features:**
- Supports Charless v3 3-digit opcodes.
- Converts stack operations to C array operations.
- Handles string/char input/output.

### c2charless.py
Compiles a subset of C language to Charless bytecode (.cless).

**Usage:**
```bash
python3 c2charless.py input.c output.cless
```

**Supported C Subset:**
- Variables: `int` only.
- I/O: `printf("string")`, `printf("%d", var)`, `printf("%c", var)`.
- Control Flow: `if`, `while`.
- Arithmetic: `+`, `-`, `*`, `/`, `%`.
- Comparison: `==`, `!=`, `<`, `>`, `<=`, `>=`.
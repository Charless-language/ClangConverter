package transpiler

import (
	"fmt"
	"strconv"
	"strings"
)

// Reuse opcodes from compiler package if possible, but package structure might separate them.
// We'll just define the values we rely on or string match.

type Transpiler struct {
	code string
	len  int
}

func NewTranspiler() *Transpiler {
	return &Transpiler{}
}

func (t *Transpiler) Transpile(charlessCode string) (string, error) {
	t.code = strings.TrimSpace(charlessCode)
	t.len = len(t.code)

	var cCode []string
	cCode = append(cCode, "#include <stdio.h>")
	cCode = append(cCode, "#include <stdlib.h>")
	cCode = append(cCode, "#include <string.h>")
	cCode = append(cCode, "")
	cCode = append(cCode, "#define STACK_SIZE 1024")
	cCode = append(cCode, "#define MEMORY_SIZE 1024")
	cCode = append(cCode, "")
	cCode = append(cCode, "long stack[STACK_SIZE];")
	cCode = append(cCode, "int sp = -1;")
	cCode = append(cCode, "long memory[MEMORY_SIZE];")
	cCode = append(cCode, "")
	cCode = append(cCode, "void push(long value) {")
	cCode = append(cCode, "    if (sp >= STACK_SIZE - 1) { fprintf(stderr, \"Stack overflow\\n\"); exit(1); }")
	cCode = append(cCode, "    stack[++sp] = value;")
	cCode = append(cCode, "}")
	cCode = append(cCode, "")
	cCode = append(cCode, "long pop() {")
	cCode = append(cCode, "    if (sp < 0) { fprintf(stderr, \"Stack underflow\\n\"); exit(1); }")
	cCode = append(cCode, "    return stack[sp--];")
	cCode = append(cCode, "}")
	cCode = append(cCode, "")
	cCode = append(cCode, "int main() {")
	cCode = append(cCode, "    memset(memory, 0, sizeof(memory));")
	cCode = append(cCode, "")

	i := 0
	length := t.len
	code := t.code

	instructions := []struct {
		Addr int
		Code string
	}{}

	// Access helpers
	consume := func(s string) bool {
		if i+len(s) <= length && code[i:i+len(s)] == s {
			i += len(s)
			return true
		}
		return false
	}

	consumeSeparator := func() bool {
		if consume("200") {
			return true
		}
		if consume("20") {
			return true
		}
		return false
	}

	getNumberLiteral := func() (int64, bool) {
		startI := i
		// 990 prefix
		if !consume("990") {
			if consume("99") {
				// legacy
			} else {
				// Revert logic? If we fail to consume prefix, we return false
				i = startI
				return 0, false
			}
		}

		numBuf := ""
		for i < length && isDigit(code[i]) {
			// Peek ahead for separator
			if hasPrefix(code, i, "200") || hasPrefix(code, i, "20") {
				break
			}
			numBuf += string(code[i])
			i++
		}
		consumeSeparator()
		if numBuf == "" {
			return 0, true
		} // 990 + empty? valid 0?
		val, _ := strconv.ParseInt(numBuf, 10, 64)
		return val, true
	}

	for i < length {
		addr := i

		if isSpace(code[i]) {
			i++
			continue
		}

		// Comments
		if consume("90020") {
			for i < length && code[i] != '\n' {
				i++
			}
			continue
		}
		if consume("90120") {
			for i < length && !hasPrefix(code, i, "90120") {
				i++
			}
			consume("90120")
			continue
		}

		// Read Opcode
		opStr := ""
		digitsCount := 0
		tempI := i
		for tempI < length && digitsCount < 3 && isDigit(code[tempI]) {
			if hasPrefix(code, tempI, "200") || hasPrefix(code, tempI, "990") {
				break
			}
			opStr += string(code[tempI])
			tempI++
			digitsCount++
		}

		if len(opStr) == 0 {
			i++
			continue
		}

		i = tempI

		opcode, _ := strconv.Atoi(opStr)

		instrC := ""

		switch opcode {
		case 0: // HALT
			consumeSeparator()
			instrC = "return 0;"
		case 10: // PRINT_STR
			consumeSeparator()
			strContent := ""
			// Read until separator "200"
			for i < length && !hasPrefix(code, i, "200") {
				// Parse char len + val
				if !isDigit(code[i]) {
					break
				}
				lenCharVal, _ := strconv.Atoi(string(code[i]))
				i++
				if i+lenCharVal > length {
					break
				}
				valStr := code[i : i+lenCharVal]
				i += lenCharVal
				val, _ := strconv.Atoi(valStr)
				strContent += string(rune(val))
			}
			consumeSeparator()
			escaped := strings.ReplaceAll(strContent, "\\", "\\\\")
			escaped = strings.ReplaceAll(escaped, "\"", "\\\"")
			escaped = strings.ReplaceAll(escaped, "\n", "\\n")
			instrC = fmt.Sprintf("printf(\"%s\");", escaped)

		case 20: // PRINT_NUM
			consumeSeparator()
			instrC = "printf(\"%ld\", pop());"
		case 40: // PRINT_CHAR
			consumeSeparator()
			instrC = "printf(\"%c\", (char)pop());"
		case 100: // INPUT_CHAR
			consumeSeparator()
			instrC = "push(getchar());"
		case 101: // INPUT_NUM
			consumeSeparator()
			instrC = "{ long val; scanf(\"%ld\", &val); push(val); }"
		case 210: // PRINT_NEWLINE
			consumeSeparator()
			instrC = "printf(\"\\n\");"
		case 500: // PUSH
			consumeSeparator()
			val, ok := getNumberLiteral()
			if !ok {
				val = 0
			}
			instrC = fmt.Sprintf("push(%d);", val)
		case 501: // POP
			consumeSeparator()
			instrC = "pop();"
		case 510: // STORE
			consumeSeparator()
			instrC = "{ long addr = pop(); long val = pop(); if(addr >= 0 && addr < MEMORY_SIZE) memory[addr] = val; }"
		case 511: // LOAD
			consumeSeparator()
			instrC = "{ long addr = pop(); if(addr >= 0 && addr < MEMORY_SIZE) push(memory[addr]); else push(0); }"

		// Math
		case 600: // ADD
			consumeSeparator()
			instrC = "{ long b = pop(); long a = pop(); push(a + b); }"
		case 601: // SUB
			consumeSeparator()
			instrC = "{ long b = pop(); long a = pop(); push(a - b); }"
		case 602: // MUL
			consumeSeparator()
			instrC = "{ long b = pop(); long a = pop(); push(a * b); }"
		case 603: // DIV
			consumeSeparator()
			instrC = "{ long b = pop(); long a = pop(); if (b!=0) push(a / b); else { fprintf(stderr, \"Div by zero\\n\"); exit(1); } }"
		case 604: // MOD
			consumeSeparator()
			instrC = "{ long b = pop(); long a = pop(); if (b!=0) push(a % b); else { fprintf(stderr, \"Div by zero\\n\"); exit(1); } }"

		// Jumps
		case 700: // JUMP
			consumeSeparator()
			target, _ := getNumberLiteral()
			instrC = fmt.Sprintf("goto Label_%d;", target)
		case 701: // JZ
			consumeSeparator()
			target, _ := getNumberLiteral()
			instrC = fmt.Sprintf("if (pop() == 0) goto Label_%d;", target)
		case 702: // JNZ
			consumeSeparator()
			target, _ := getNumberLiteral()
			instrC = fmt.Sprintf("if (pop() != 0) goto Label_%d;", target)

		// Compare
		case 801: // EQN
			consumeSeparator()
			instrC = "{ long b = pop(); long a = pop(); push(a == b ? 1 : 0); }"
		case 802: // GT
			consumeSeparator()
			instrC = "{ long b = pop(); long a = pop(); push(a > b ? 1 : 0); }"
		case 803: // LT
			consumeSeparator()
			instrC = "{ long b = pop(); long a = pop(); push(a < b ? 1 : 0); }"
		case 804: // GTE
			consumeSeparator()
			instrC = "{ long b = pop(); long a = pop(); push(a >= b ? 1 : 0); }"
		case 805: // LTE
			consumeSeparator()
			instrC = "{ long b = pop(); long a = pop(); push(a <= b ? 1 : 0); }"

		default:
			// consumeSeparator() ?
		}

		if instrC != "" {
			instructions = append(instructions, struct {
				Addr int
				Code string
			}{addr, instrC})
		}
	}

	// Generate lines
	for _, inst := range instructions {
		cCode = append(cCode, fmt.Sprintf("    Label_%d: ;", inst.Addr))
		cCode = append(cCode, "    "+inst.Code)
	}

	// Emit label for EOF (in case jump targets end)
	cCode = append(cCode, fmt.Sprintf("    Label_%d: ;", length))

	cCode = append(cCode, "}")
	return strings.Join(cCode, "\n"), nil
}

func isDigit(ch byte) bool {
	return ch >= '0' && ch <= '9'
}

func isSpace(ch byte) bool {
	return ch == ' ' || ch == '\t' || ch == '\n' || ch == '\r'
}

func hasPrefix(s string, i int, prefix string) bool {
	if i+len(prefix) > len(s) {
		return false
	}
	return s[i:i+len(prefix)] == prefix
}

package compiler

import (
	"fmt"
	"regexp"
	"strconv"
	"strings"
)

type Token struct {
	Kind  string
	Value string
}

type Instruction interface{}

type RawInstruction string

type LabelDef struct {
	Label string
}

type JumpInstruction struct {
	Opcode string
	Label  string
}

type Compiler struct {
	tokens        []Token
	pos           int
	output        []Instruction
	vars          map[string]int
	memPtr        int
	labelCounters int
	code          string
}

func NewCompiler() *Compiler {
	return &Compiler{
		vars:   make(map[string]int),
		memPtr: 0,
	}
}

func (c *Compiler) getVarAddr(name string) int {
	if _, ok := c.vars[name]; !ok {
		c.vars[name] = c.memPtr
		c.memPtr++
	}
	return c.vars[name]
}

func (c *Compiler) Tokenize(code string) error {
	tokenSpec := []struct {
		Kind  string
		Regex string
	}{
		{"KEYWORD", `\b(if|while|return|int|printf|scanf)\b`},
		{"ID", `[a-zA-Z_][a-zA-Z0-9_]*`},
		{"NUMBER", `\d+`},
		{"STRING", `"[^"]*"`},
		{"OP", `==|!=|<=|>=|[+\-*/%<>=&|!(){};,]`},
		{"PREPROCESSOR", `#.*`},
		{"SKIP", `[ \t\n]+`},
	}

	// Build the regex
	var parts []string
	for _, spec := range tokenSpec {
		parts = append(parts, fmt.Sprintf("(?P<%s>%s)", spec.Kind, spec.Regex))
	}
	tokRegex := strings.Join(parts, "|")
	re := regexp.MustCompile(tokRegex)

	matches := re.FindAllStringSubmatchIndex(code, -1)

	// Since Go regexp doesn't directly give group names in match, we iterate
	groupNames := re.SubexpNames()

	for _, matchIdx := range matches {
		fullMatch := code[matchIdx[0]:matchIdx[1]]
		for i, name := range groupNames {
			if i == 0 || name == "" {
				continue
			}
			if matchIdx[2*i] != -1 {
				if name == "SKIP" || name == "PREPROCESSOR" {
					continue
				}
				c.tokens = append(c.tokens, Token{Kind: name, Value: fullMatch})
				break
			}
		}
	}
	c.tokens = append(c.tokens, Token{Kind: "EOF", Value: "EOF"})
	return nil
}

func (c *Compiler) peek(offset int) Token {
	if c.pos+offset >= len(c.tokens) {
		return Token{Kind: "EOF", Value: "EOF"}
	}
	return c.tokens[c.pos+offset]
}

func (c *Compiler) consume(expectedValue string, expectedKind string) (Token, error) {
	tok := c.peek(0)
	if expectedValue != "" && tok.Value != expectedValue {
		return tok, fmt.Errorf("expected '%s', got '%s'", expectedValue, tok.Value)
	}
	if expectedKind != "" && tok.Kind != expectedKind {
		return tok, fmt.Errorf("expected kind '%s', got '%s'", expectedKind, tok.Kind)
	}
	c.pos++
	return tok, nil
}

func (c *Compiler) emitRaw(s string) {
	c.output = append(c.output, RawInstruction(s))
}

func (c *Compiler) newLabel() string {
	c.labelCounters++
	return fmt.Sprintf("L%d", c.labelCounters)
}

func (c *Compiler) emitLabelDef(label string) {
	c.output = append(c.output, LabelDef{Label: label})
}

func (c *Compiler) emitJump(opcode string, label string) {
	c.output = append(c.output, JumpInstruction{Opcode: opcode, Label: label})
}

func (c *Compiler) Compile(code string) (string, error) {
	c.code = code // Storing code not strictly needed if passed to Tokenize
	if err := c.Tokenize(code); err != nil {
		return "", err
	}

	// Check for simple main wrapper
	if c.tokens[0].Value == "int" && c.tokens[1].Value == "main" {
		c.consume("int", "")
		c.consume("main", "")
		c.consume("(", "")
		c.consume(")", "")
		c.consume("{", "")

		for c.peek(0).Kind != "EOF" {
			if c.peek(0).Value == "}" {
				if c.pos == len(c.tokens)-2 { // EOF is last
					c.consume("}", "")
					break
				}
			}
			if err := c.parseStatement(); err != nil {
				return "", err
			}
		}
	} else {
		for c.peek(0).Kind != "EOF" {
			if err := c.parseStatement(); err != nil {
				return "", err
			}
		}
	}

	return c.resolve(), nil
}

func (c *Compiler) parseStatement() error {
	tok := c.peek(0)

	if tok.Kind == "KEYWORD" && tok.Value == "int" {
		c.consume("", "")
		nameTok, err := c.consume("", "ID")
		if err != nil {
			return err
		}
		addr := c.getVarAddr(nameTok.Value)

		if c.peek(0).Value == "=" {
			c.consume("=", "")
			c.parseExpression()
			c.emitRaw(OP_PUSH + SEP + PREFIX_NUM + strconv.Itoa(addr) + SEP)
			c.emitRaw(OP_STORE + SEP)
		}
		c.consume(";", "")

	} else if tok.Kind == "KEYWORD" && tok.Value == "while" {
		c.consume("", "")
		c.consume("(", "")

		startLabel := c.newLabel()
		endLabel := c.newLabel()

		c.emitLabelDef(startLabel)

		c.parseExpression()
		c.consume(")", "")

		c.emitJump(OP_JZ, endLabel)

		c.consume("{", "")
		for c.peek(0).Value != "}" {
			c.parseStatement()
		}
		c.consume("}", "")

		c.emitJump(OP_JUMP, startLabel)
		c.emitLabelDef(endLabel)

	} else if tok.Kind == "KEYWORD" && tok.Value == "if" {
		c.consume("", "")
		c.consume("(", "")
		c.parseExpression()
		c.consume(")", "")

		elseLabel := c.newLabel()
		endLabel := c.newLabel()

		c.emitJump(OP_JZ, elseLabel)

		c.consume("{", "")
		for c.peek(0).Value != "}" {
			c.parseStatement()
		}
		c.consume("}", "")

		c.emitJump(OP_JUMP, endLabel)
		c.emitLabelDef(elseLabel)
		// Else block logic would go here if implemented
		c.emitLabelDef(endLabel)

	} else if tok.Kind == "KEYWORD" && tok.Value == "printf" {
		c.consume("", "")
		c.consume("(", "")
		fmtTok, _ := c.consume("", "STRING")
		fmtStr := fmtTok.Value[1 : len(fmtTok.Value)-1] // Strip quotes

		if c.peek(0).Value == "," {
			c.consume(",", "")
			if strings.Contains(fmtStr, "%d") {
				c.parseExpression()
				c.emitRaw(OP_PRINT_NUM + SEP)
			} else if strings.Contains(fmtStr, "%c") {
				c.parseExpression()
				c.emitRaw(OP_PRINT_CHAR + SEP)
			}
		} else {
			// String literal
			decodedFmt := unescapeString(fmtStr)
			encoded := ""
			for _, char := range decodedFmt {
				val := strconv.Itoa(int(char))
				l := strconv.Itoa(len(val))
				encoded += l + val
			}
			c.emitRaw(OP_PRINT_STR + SEP + encoded + SEP)
		}
		c.consume(")", "")
		c.consume(";", "")

	} else if tok.Kind == "ID" {
		name := tok.Value
		c.consume("", "")
		if c.peek(0).Value == "=" {
			c.consume("=", "")
			addr := c.getVarAddr(name)
			c.emitRaw(OP_PUSH + SEP + PREFIX_NUM + strconv.Itoa(addr) + SEP)
			c.parseExpression()
			c.emitRaw(OP_STORE + SEP)
		}
		c.consume(";", "")

	} else if tok.Kind == "KEYWORD" && tok.Value == "return" {
		c.consume("", "")
		c.consume("", "NUMBER")
		c.consume(";", "")
		c.emitRaw(OP_HALT + SEP)
	} else {
		// Skip or error? Python skips.
		c.pos++
	}
	return nil
}

func (c *Compiler) parseExpression() {
	c.parseComparison()
}

func (c *Compiler) parseComparison() {
	c.parseSum()
	for {
		op := c.peek(0).Value
		if op == "==" || op == "!=" || op == "<" || op == ">" || op == "<=" || op == ">=" {
			c.consume("", "")
			c.parseSum()
			switch op {
			case "==":
				c.emitRaw(OP_EQN + SEP)
			case "!=":
				c.emitRaw(OP_EQN + SEP)
				c.emitRaw(OP_PUSH + SEP + PREFIX_NUM + "0" + SEP)
				c.emitRaw(OP_EQN + SEP)
			case ">":
				c.emitRaw(OP_GT + SEP)
			case "<":
				c.emitRaw(OP_LT + SEP)
			case ">=":
				c.emitRaw(OP_GTE + SEP)
			case "<=":
				c.emitRaw(OP_LTE + SEP)
			}
		} else {
			break
		}
	}
}

func (c *Compiler) parseSum() {
	c.parseTerm()
	for {
		op := c.peek(0).Value
		if op == "+" || op == "-" {
			c.consume("", "")
			c.parseTerm()
			if op == "+" {
				c.emitRaw(OP_ADD + SEP)
			} else {
				c.emitRaw(OP_SUB + SEP)
			}
		} else {
			break
		}
	}
}

func (c *Compiler) parseTerm() {
	c.parseFactor()
	for {
		op := c.peek(0).Value
		if op == "*" || op == "/" || op == "%" {
			c.consume("", "")
			c.parseFactor()
			if op == "*" {
				c.emitRaw(OP_MUL + SEP)
			} else if op == "/" {
				c.emitRaw(OP_DIV + SEP)
			} else {
				c.emitRaw(OP_MOD + SEP)
			}
		} else {
			break
		}
	}
}

func (c *Compiler) parseFactor() {
	tok := c.peek(0)
	if tok.Kind == "NUMBER" {
		c.consume("", "")
		c.emitRaw(OP_PUSH + SEP + PREFIX_NUM + tok.Value + SEP)
	} else if tok.Kind == "ID" {
		name := tok.Value
		c.consume("", "")
		addr := c.getVarAddr(name)
		c.emitRaw(OP_PUSH + SEP + PREFIX_NUM + strconv.Itoa(addr) + SEP)
		c.emitRaw(OP_LOAD + SEP)
	} else if tok.Value == "(" {
		c.consume("(", "")
		c.parseExpression()
		c.consume(")", "")
	}
}

func unescapeString(s string) string {
	// Simple unescape implementation
	// In Python `codecs.decode(fmt, 'unicode_escape')` handles \n, \t, etc.
	s = strings.ReplaceAll(s, `\n`, "\n")
	s = strings.ReplaceAll(s, `\t`, "\t")
	s = strings.ReplaceAll(s, `\"`, "\"")
	s = strings.ReplaceAll(s, `\\`, "\\")
	return s
}

func (c *Compiler) resolve() string {
	labelsMap := make(map[string]int)
	offset := 0

	// Two-pass resolution like in Python reference (simplified)
	// Python reference used `zfill(5)` for address placeholders.

	// First pass: Calculate offsets and find label positions
	tempBits := []struct {
		isRef bool
		val   string
		label string
		op    string
	}{}

	for _, instr := range c.output {
		switch v := instr.(type) {
		case RawInstruction:
			s := string(v)
			tempBits = append(tempBits, struct {
				isRef bool
				val   string
				label string
				op    string
			}{false, s, "", ""})
			offset += len(s)
		case LabelDef:
			labelsMap[v.Label] = offset
		case JumpInstruction:
			// "700" + SEP + PREFIX_NUM + "00000" + SEP
			// 3 + 3 + 3 + 5 + 3 = 17
			blockLen := len(v.Opcode) + len(SEP) + len(PREFIX_NUM) + 5 + len(SEP)
			tempBits = append(tempBits, struct {
				isRef bool
				val   string
				label string
				op    string
			}{true, "", v.Label, v.Opcode})
			offset += blockLen
		}
	}

	var resBuilder strings.Builder
	for _, bit := range tempBits {
		if !bit.isRef {
			resBuilder.WriteString(bit.val)
		} else {
			target := labelsMap[bit.label]
			targetStr := strconv.Itoa(target)
			// Pad to 5 digits
			if len(targetStr) < 5 {
				targetStr = strings.Repeat("0", 5-len(targetStr)) + targetStr
			}
			block := bit.op + SEP + PREFIX_NUM + targetStr + SEP
			resBuilder.WriteString(block)
		}
	}
	return resBuilder.String()
}

// Helper struct for internal storage
type compilerState struct {
	code string
}

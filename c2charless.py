import sys
import re

# Charless v3 opcodes
OP_HALT = "000"
OP_PRINT_STR = "010"
OP_PRINT_NUM = "020"
OP_PRINT_CHAR = "040"
OP_INPUT_CHAR = "100"
OP_INPUT_NUM = "101"
OP_PRINT_NEWLINE = "210"
OP_PUSH = "500"
OP_POP = "501"
OP_STORE = "510"
OP_LOAD = "511"
OP_ADD = "600"
OP_SUB = "601"
OP_MUL = "602"
OP_DIV = "603"
OP_MOD = "604"
OP_JUMP = "700"
OP_JZ = "701" # Jump if zero
OP_JNZ = "702"
OP_EQN = "801"
OP_GT = "802"
OP_LT = "803"

SEP = "200"
PREFIX_NUM = "990"

class C2Charless:
    def __init__(self):
        self.code = ""
        self.pos = 0
        self.output = []
        self.vars = {} # name -> memory_address
        self.mem_ptr = 0
        self.labels = {} # name -> placeholder_index
        self.label_counters = 0
        self.tokens = []
        
    def gen(self, chunk):
        self.output.append(str(chunk))

    def emit(self, chunk):
        if isinstance(chunk, list):
            self.output.append("".join(chunk))
        else:
            self.output.append(chunk)

    def get_var_addr(self, name):
        if name not in self.vars:
            self.vars[name] = self.mem_ptr
            self.mem_ptr += 1
        return self.vars[name]

    def tokenize(self, code):
        # A very simple tokenizer for the subset of C
        token_spec = [
            ('KEYWORD', r'\b(if|while|return|int|printf|scanf)\b'),
            ('ID', r'[a-zA-Z_][a-zA-Z0-9_]*'),
            ('NUMBER', r'\d+'),
            ('STRING', r'"[^"]*"'),
            ('OP', r'==|!=|<=|>=|[+\-*/%<>=&|!(){};,]'),
            ('SKIP', r'[ \t\n]+'),
        ]
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_spec)
        for mo in re.finditer(tok_regex, code):
            kind = mo.lastgroup
            value = mo.group()
            if kind == 'SKIP':
                continue
            self.tokens.append((kind, value))
        self.tokens.append(('EOF', 'EOF'))

    def peek(self, offset=0):
        if self.pos + offset >= len(self.tokens):
            return ('EOF', 'EOF')
        return self.tokens[self.pos + offset]

    def consume(self, expected_value=None, expected_kind=None):
        tok = self.peek()
        if expected_value and tok[1] != expected_value:
            raise Exception(f"Expected '{expected_value}', got '{tok[1]}'")
        if expected_kind and tok[0] != expected_kind:
            raise Exception(f"Expected kind '{expected_kind}', got '{tok[0]}'")
        self.pos += 1
        return tok

    def transpile(self, c_code):
        self.code = c_code
        self.tokenize(c_code)
        
        if self.tokens[0][1] == 'int' and self.tokens[1][1] == 'main':
             # Skip int main() {
             self.consume('int')
             self.consume('main')
             self.consume('(')
             self.consume(')')
             self.consume('{')
             
             while self.peek()[0] != 'EOF':
                 if self.peek()[1] == '}':
                     # Check if it's the last brace
                     if self.pos == len(self.tokens) - 2: # EOF is last
                         self.consume('}')
                         break
                 self.parse_statement()
        else:
            while self.peek()[0] != 'EOF':
                 self.parse_statement()
             
        # Resolve labels? Not using placeholder strategy here, but direct offset calculation strategy 
        # is hard because instruction lengths vary.
        # Instead, we will generate "assembly-like" intermediate code and then resolve addresses.
        # For this PoC, we will just assume fixed instruction sizes? No, that's impossible.
        # We need a 2-pass approach or post-processing.
        
        # Current strategy: `self.output` contains instructions. 
        # We need to compute byte offsets.
        
        final_code = ""
        # We need to handle jumps. 
        # Let's say we use special markers `LABEL_REF:name` and `LABEL_DEF:name`.
        
        # Calculate offsets
        # But wait, generated code is strings of digits.
        # We can simulate the generation to find offsets.
        
    def parse_statement(self):
        tok = self.peek()
        if tok[0] == 'KEYWORD' and tok[1] == 'int':
            self.consume()
            # int x = 5;
            name_tok = self.consume(expected_kind='ID')
            name = name_tok[1]
            addr = self.get_var_addr(name)
            
            if self.peek()[1] == '=':
                self.consume('=')
                self.parse_expression()
                self.consume('=')
                self.parse_expression()
                self.emit_raw(OP_PUSH + SEP + PREFIX_NUM + str(addr) + SEP)
                self.emit_raw(OP_STORE + SEP)
            
            self.consume(';')

        elif tok[0] == 'KEYWORD' and tok[1] == 'while':
             self.consume()
             self.consume('(')
             
             start_label = self.new_label()
             end_label = self.new_label()
             
             self.emit_label_def(start_label)
             
             self.parse_expression()
             self.consume(')')
             
             # If false (0), jump to end
             self.emit_jump(OP_JZ, end_label) # JZ end_label
             
             self.consume('{')
             while self.peek()[1] != '}':
                 self.parse_statement()
             self.consume('}')
             
             self.emit_jump(OP_JUMP, start_label) # JUMP start_label
             self.emit_label_def(end_label)
             
        elif tok[0] == 'KEYWORD' and tok[1] == 'if':
             self.consume()
             self.consume('(')
             self.parse_expression()
             self.consume(')')
             
             else_label = self.new_label()
             end_label = self.new_label()
             
             self.emit_jump(OP_JZ, else_label)
             
             self.consume('{')
             while self.peek()[1] != '}':
                 self.parse_statement()
             self.consume('}')
             
             self.emit_jump(OP_JUMP, end_label)
             self.emit_label_def(else_label)
             
             # Handle else? For now no.
             self.emit_label_def(end_label)

        elif tok[0] == 'KEYWORD' and tok[1] == 'printf':
            self.consume()
            self.consume('(')
            fmt_tok = self.consume(expected_kind='STRING')
            fmt = fmt_tok[1][1:-1] # Strip quotes
            
            if ',' in fmt:
                 # printf("%d", var)
                 # Not supported in basic string (010).
                 pass
            
            # Simple check if there are arguments
            if self.peek()[1] == ',':
                self.consume(',')
                # Check format specifier
                if "%d" in fmt:
                    # Print number
                    # Evaluate expr
                    self.parse_expression()
                    self.emit_raw(OP_PRINT_NUM + SEP)
                elif "%c" in fmt:
                     self.parse_expression()
                     self.emit_raw(OP_PRINT_CHAR + SEP)
            else:
                # Just string
                # Encode string
                # "ABC" -> 010 + 165 166 167 + 200
                # Wait, tokenizer logic for 010 was: 
                # `len_char` `val_str`
                # 'A' -> '200' check?
                # No, `ope01.c`: `char len_str[2]`. `len=atoi`. `read len`. `atol`.
                # If 'A' (65): len=2. `65`.
                # So "265".
                encoded = ""
                for char in fmt:
                    val = str(ord(char))
                    l = len(val)
                    encoded += str(l) + val
                
                self.emit_raw(OP_PRINT_STR + SEP + encoded + SEP)
                
            self.consume(')')
            self.consume(';')

        elif tok[0] == 'ID':
            # Assignment? x = 5;
            name = tok[1]
            self.consume()
            if self.peek()[1] == '=':
                self.consume('=')
                addr = self.get_var_addr(name)
                self.emit_raw(OP_PUSH + SEP + PREFIX_NUM + str(addr) + SEP)
                self.parse_expression()
                self.emit_raw(OP_STORE + SEP)
            self.consume(';')
            
        elif tok[0] == 'KEYWORD' and tok[1] == 'return':
             self.consume()
             self.consume(expected_kind='NUMBER') # Ignore return val
             self.consume(';')
             self.emit_raw(OP_HALT + SEP)

        else:
            # Skip unknown
            self.pos += 1

    def parse_expression(self):
        self.parse_comparison()

    def parse_comparison(self):
        self.parse_sum()
        while self.peek()[1] in ['==', '!=', '<', '>', '<=', '>=']:
            op = self.consume()[1]
            self.parse_sum()
            if op == '==': self.emit_raw(OP_EQN + SEP) # EQN (801)
            elif op == '!=': 
                 # EQN then NOT? Charless v3 doesn't have NOT?
                 # It has NO_OP? 
                 # v3 spec: 801 EQN, 802 GT, 803 LT, 804 GTE, 805 LTE.
                 # Wait, 801 is EQN.
                 # != is not directly supported?
                 # I can use EQN then check for 0?
                 # Or use JNZ logic?
                 # Actually, `pop() == 0` is NOT.
                 # But I don't see a `NOT` opcode in my list.
                 # `650-659` Bit ops.
                 # Maybe `EQN` returns 0 or 1.
                 # If `a == b`, returns 1.
                 # If `a != b`, returns 0.
                 # If I want `!=`, I want 1 if different.
                 # `EQN` -> 0 or 1.
                 # `PUSH 0` `EQN` ? (Negate)
                 self.emit_raw(OP_EQN + SEP)
                 self.emit_raw(OP_PUSH + SEP + PREFIX_NUM + "0" + SEP)
                 self.emit_raw(OP_EQN + SEP)
                 
            elif op == '>': self.emit_raw(OP_GT + SEP)
            elif op == '<': self.emit_raw(OP_LT + SEP)
            elif op == '>=': 
                # GTE? Not in my opcode list in script?
                # Script has OP_GT, OP_LT, OP_EQN.
                # v3 spec has GTE (804), LTE (805).
                # I should add them to constants.
                self.emit_raw("804" + SEP)
            elif op == '<=': self.emit_raw("805" + SEP)

    def parse_sum(self):
        self.parse_term()
        while self.peek()[1] in ['+', '-']:
            op = self.consume()[1]
            self.parse_term()
            if op == '+': self.emit_raw(OP_ADD + SEP)
            if op == '-': self.emit_raw(OP_SUB + SEP)

    def parse_term(self):
        self.parse_factor()
        while self.peek()[1] in ['*', '/', '%']:
            op = self.consume()[1]
            self.parse_factor()
            if op == '*': self.emit_raw(OP_MUL + SEP)
            if op == '/': self.emit_raw(OP_DIV + SEP)
            if op == '%': self.emit_raw(OP_MOD + SEP)

    def parse_factor(self):
        tok = self.peek()
        if tok[0] == 'NUMBER':
            self.consume()
            self.emit_raw(OP_PUSH + SEP + PREFIX_NUM + tok[1] + SEP)
        elif tok[0] == 'ID':
            name = tok[1]
            self.consume()
            addr = self.get_var_addr(name)
            self.emit_raw(OP_PUSH + SEP + PREFIX_NUM + str(addr) + SEP)
            self.emit_raw(OP_LOAD + SEP)
        elif tok[1] == '(':
            self.consume('(')
            self.parse_expression()
            self.consume(')')
        elif tok[1] == '-': # Unary minus?
             # Not implemented logic for unary
             pass

    # -- Code gen helpers --
    def emit_raw(self, s):
        self.output.append(s)

    def new_label(self):
        self.label_counters += 1
        return f"L{self.label_counters}"

    def emit_label_def(self, label):
        self.output.append({"type": "DEF", "label": label})

    def emit_jump(self, opcode, label):
        self.output.append({"type": "REF", "opcode": opcode, "label": label})

    def resolve(self):
        # Calculate offsets
        # First pass: calculate sizes and label positions
        # Note: Jump targets in Charless are BYTE OFFSETS from start of file.
        
        # We need to render the list to string to know lengths.
        # But jumps need the length of the jump instruction itself (which includes the address).
        # This is a circular dependency if address length changes.
        # But Charless addresses are just number strings.
        # We can pad addresses? No, Charless is flexible.
        
        # Iterative resolution:
        # Assume addresses are 4 digits (or 5) to start.
        # Check if they fit. Recalculate.
        
        # Simplified: Just assume addresses will be at most 5 digits (supports up to 99999 bytes).
        # Should be enough for small programs.
        
        final_bits = []
        labels_map = {}
        
        # Dry run to find labels
        offset = 0
        
        # We replace refs with placeholders first
        temp_bits = []
        for item in self.output:
            if isinstance(item, dict):
                if item["type"] == "DEF":
                    labels_map[item["label"]] = offset
                    # Label def produces no code
                elif item["type"] == "REF":
                    # Opcode + Sep + NumPrefix + Placeholder(5) + Sep
                    # Ex: 700 200 990 00000 200
                    # Length: 3 + 3 + 3 + 5 + 3 = 17 chars
                    block = item["opcode"] + SEP + PREFIX_NUM + "00000" + SEP
                    temp_bits.append({"label": item["label"], "start": offset, "orig": item})
                    offset += len(block)
            else:
                temp_bits.append(item)
                offset += len(item)
                
        # Fill in labels
        resString = ""
        current_offset = 0
        for item in self.output:
             if isinstance(item, dict):
                if item["type"] == "DEF":
                    pass # Done, just marks position
                elif item["type"] == "REF":
                    target = labels_map.get(item["label"], 0)
                    target_str = str(target)
                    # We reserved 5 digits "00000". If target is 123, use "123".
                    # But wait, if I use shorter string, subsequent offsets change!
                    # So I MUST pad with something or just accept `200` terminator defines length?
                    # The `get_number_literal` reads until separator.
                    # So "123" + "200" is fine.
                    # BUT if I reserve 5 chars and use 3, the code shrinks, changing targets.
                    # So I must pad? No, number literal doesn't support padding like `00123`?
                    # Yes `atol` handles `00123`.
                    # So I can zero-pad to fixed width to ensure stable offsets.
                    target_str = target_str.zfill(5)
                    
                    block = item["opcode"] + SEP + PREFIX_NUM + target_str + SEP
                    resString += block
                    current_offset += len(block)
             else:
                 resString += item
                 current_offset += len(item)
                 
        return resString

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input.c> <output.cless>")
        sys.exit(1)
        
    with open(sys.argv[1], 'r') as f:
        src = f.read()
        
    c2 = C2Charless()
    c2.transpile(src)
    res = c2.resolve()
    
    with open(sys.argv[2], 'w') as f:
        f.write(res)

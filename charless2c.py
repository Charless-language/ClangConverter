import sys
import os

def charless_to_c(input_file, output_file):
    with open(input_file, 'r') as f:
        content = f.read()

    charless_code = content.strip()
    
    c_code = []
    c_code.append("#include <stdio.h>")
    c_code.append("#include <stdlib.h>")
    c_code.append("#include <string.h>")
    c_code.append("")
    c_code.append("#define STACK_SIZE 1024")
    c_code.append("#define MEMORY_SIZE 1024")
    c_code.append("")
    c_code.append("long stack[STACK_SIZE];")
    c_code.append("int sp = -1;")
    c_code.append("long memory[MEMORY_SIZE];")
    c_code.append("")
    c_code.append("void push(long value) {")
    c_code.append("    if (sp >= STACK_SIZE - 1) { fprintf(stderr, \"Stack overflow\\n\"); exit(1); }")
    c_code.append("    stack[++sp] = value;")
    c_code.append("}")
    c_code.append("")
    c_code.append("long pop() {")
    c_code.append("    if (sp < 0) { fprintf(stderr, \"Stack underflow\\n\"); exit(1); }")
    c_code.append("    return stack[sp--];")
    c_code.append("}")
    c_code.append("")
    c_code.append("int main() {")
    c_code.append("    // Initialize memory")
    c_code.append("    memset(memory, 0, sizeof(memory));")
    c_code.append("")

    i = 0
    instructions = []
    
    # Pre-pass to find jump targets (labels)
    # Map from charless index to label index
    jump_targets = set()
    
    # Simple lexer
    while i < len(charless_code):
        # Skip whitespace/newlines
        if charless_code[i].isspace():
            i += 1
            continue
            
        # Parse opcode (3 digits)
        # Check for numeric
        if not charless_code[i].isdigit():
            i += 1
            continue

        # Check if it's a comment
        if charless_code[i:i+5] == "90020":
            # Single line comment
            i += 5
            while i < len(charless_code) and charless_code[i] != '\n':
                i += 1
            continue
        
        if charless_code[i:i+5] == "90120":
             # Multi-line comment
            i += 5
            while i < len(charless_code) and charless_code[i:i+5] != "90120":
                i += 1
            if i < len(charless_code):
                i += 5
            continue

        # Check opcode
        # We need to look ahead to ensure it's an opcode
        # Opcode is 3 digits followed by '20' (separator) usually, but arguments might follow '20'
        # Actually in Charless structure: [OPCODE (3)] [SEPARATOR (20)] [ARGS...]
        
        # Looking at `tokenizer.c`, it just grabs 3 digits if available.
        opcode_str = ""
        count = 0
        j = i
        while j < len(charless_code) and count < 3 and charless_code[j].isdigit():
             opcode_str += charless_code[j]
             j += 1
             count += 1
             
        if count == 3:
            # Check separator `200` (tokenizer `consume_separator` checks for `200` after literal/op?)
            # Wait, `get_opcode` in tokenizer.c says:
            # Reads 3 digits. Stops at `200` or `990`. 
            # Actually standard Charless structure is sequences of numbers.
            # Opcode is 3 digits.
            
            # Let's verify `consume_separator`: `strncmp(ip, "200", 3) == 0`.
            # So separator is `200`.
            
            op_val = int(opcode_str)
            instructions.append((i, op_val))
            i = j
            
            # Check for separator 200
            if i + 3 <= len(charless_code) and charless_code[i:i+3] == "200":
                i += 3
            elif i + 2 <= len(charless_code) and charless_code[i:i+2] == "20":
                # Legacy 20 separator might appear in old code but v3 uses 200?
                # `tokenizer.c`: `consume_separator` checks "200".
                # `command-set-v3-design.md`: "Since v3... Separator is 20 (? No, it says Separator (20) is unchanged)"
                # But tokenizer says `200`. Let's check `tokenizer.c` again.
                # Line 10: `strncmp(ip, "200", 3) == 0`.
                # So separator must be `200`.
                
                # However, the user request says: "Numerical literal (starts with 99) and separator (20) are unchanged."
                # But tokenizer implements `200`.
                # Let's look at `compiler.c` or usage.
                # `ope01.c`: `consume_separator()` -> checks "200".
                # Wait, earlier `command-set-v3-design.md` lines 303: "`20`（セパレータ）...は引き続き予約語".
                # But `tokenizer.c` uses `200`.
                # Maybe `20` is the *concept* but `200` is the token?
                # Ah, `20` is the old separator. The new tokenizer checks `200`.
                # But let's check legacy support. The code `consume_separator` ONLY checks `200`.
                # If the design doc says `20`, there is a discrepancy.
                # I will support `200` as per the C implementation.
                pass
                
        else:
            # Ignore or error? `compiler.c` loops until EOF.
            i += 1
            
    # Re-scan to generate code
    i = 0
    current_idx_map = {} # Maps code index to instruction index for jump targets code generation logic
    
    # We really need to know the arguments for each opcode to parse correctly.
    # This naive lexer above is insufficient because arguments (literals) are variable length.
    # I should implement a proper parser similar to `tokenizer.c`.

    return parse_and_generate(charless_code, c_code, output_file)

def parse_and_generate(code, c_code, output_file):
    i = 0
    length = len(code)
    
    # Helper to peek
    def peek(offset=0, size=1):
        if i + offset + size > length:
            return ""
        return code[i+offset : i+offset+size]

    def consume(s):
        nonlocal i
        if code.startswith(s, i):
            i += len(s)
            return True
        return False
        
    def consume_separator():
        # Try 200 (v3)
        if consume("200"): return True
        # Try 20 (legacy, but might be needed if docs are right vs code)
        if consume("20"): return True 
        return False

    def get_number_literal():
        nonlocal i
        buffer = ""
        # 990 prefix
        if not consume("990"):
            # Try 99 (legacy)?
            if consume("99"):
                pass
            else:
                 return None
                 
        start = i
        while i < length and code[i].isdigit():
            # Check for separator lookahead?
            if code.startswith("200", i) or code.startswith("20", i):
                break
            buffer += code[i]
            i += 1
            
        consume_separator()
        return int(buffer) if buffer else 0

    # Instructions list: (index (address), valid_c_str or valid_obj)
    # Since jumps target *byte offset* in Charless usually?
    # `codegen.c` says: `current_pos = ip - code`.
    # Yes, jumps in Charless are to the byte index in the source file!
    
    instructions = [] # item: (charless_addr, c_line)

    while i < length:
        addr = i
        
        # Skip whitespace
        if code[i].isspace():
            i += 1
            continue
            
        # Comments
        if consume("90020"): # Single line
            while i < length and code[i] != '\n': i += 1
            continue
        if consume("90120"): # Multi line
             while i < length and not code.startswith("90120", i): i += 1
             consume("90120")
             continue
             
        # Try to read opcode
        opcode_str = ""
        # Read 3 digits
        digits_count = 0
        temp_i = i
        while temp_i < length and digits_count < 3 and code[temp_i].isdigit():
            # Check if we hit a separator or special sequence
            if code.startswith("200", temp_i) or code.startswith("990", temp_i):
                break
            opcode_str += code[temp_i]
            temp_i += 1
            digits_count += 1
        
        if len(opcode_str) == 0:
            i += 1
            continue
            
        # Update i
        i = temp_i
        
        if len(opcode_str) < 3:
             # Just skip? Or error?
             pass
        
        opcode = int(opcode_str)
        
        # Parse arguments based on opcode
        instr_code = []
        instr_code.append(f"Label_{addr}: ;") 
        
        # We need to preserve the ability to jump to this instruction.
        # In C, we can label every instruction `Label_<index>:`.
        
        instr_c = ""
        
        if opcode == 0: # HALT
            consume_separator()
            instr_c = "return 0;"
        elif opcode == 10: # PRINT_STRING (010 -> 10)
            consume_separator()
            # Read string payload until separator
            # Format: [CHAR_CODE] [SEP] [CHAR_CODE] [SEP] ... [SEP] (End of string)
            # Actually ope01.c: while (strncmp != 200) { read_len; read_chars; }
            # Wait, ope01.c logic:
            #   while not 200:
            #      len_str = *ip (1 char) ?? No, `char len_str[2] = {*ip, '\0'}` -> Takes 1 digit as length?
            #      ip++
            #      len = atoi
            #      read `len` chars
            #      atoi(code_str) -> val
            #      print val as char? No `printf` with `mov rsi, val`.
            #      Wait, `lea rdi, char_format` implies printf("%s") or similar? 
            #      Actually let's look at `asm_header.c` or assumption.
            #      Usually `printf` takes format string.
            #      If `char_format` is "%c", then it prints a char.
            #      If `char_format` is "%s", it prints string.
            #      The generic tokenizer `get_number_literal` isn't used here.
            
            # Re-reading `ope01.c`:
            # `char len_str[2] = {*ip, '\0'}; ip++; int len = atoi(len_str);`
            # `strncpy(code_str, ip, len); ip+=len;`
            # `long val = atol(code_str);`
            # `fprintf(..., "mov rsi, %ld\n", val); call printf`
            # It seems it reads an ASCII value as a number, then prints it?
            # E.g. "65" -> 65 -> 'A'.
            # Yes, standard Charless string encoding is sequence of ASCII codes.
            # Format in Charless: `LEN` `DIGITS` `200`? No, logic above loops until `200`.
            # So: `1` `6` `5` (len 1, val 6?? No)
            # If input is 'A' (65):
            # `2` `6` `5` -> len 2, val 65.
            
            # So for converter:
            string_content = ""
            while not code.startswith("200", i) and i < length:
                len_char = code[i]
                i += 1
                if not len_char.isdigit(): break 
                l = int(len_char)
                val_str = code[i : i+l]
                i += l
                if val_str:
                    string_content += chr(int(val_str))
            consume_separator()
            
            # Escape string for C
            escaped = string_content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            instr_c = f'printf("{escaped}");'

        elif opcode == 20: # PRINT_NUM (020)
            consume_separator() # Consumes 200
            instr_c = 'printf("%ld", pop());'

        elif opcode == 40: # PRINT_CHAR (040)
            consume_separator()
            instr_c = 'printf("%c", (char)pop());'

        elif opcode == 100: # INPUT_CHAR
             consume_separator()
             instr_c = 'push(getchar());'
             
        elif opcode == 101: # INPUT_NUM
             consume_separator()
             instr_c = '{ long val; scanf("%ld", &val); push(val); }'

        elif opcode == 210: # PRINT_NEWLINE
             consume_separator()
             instr_c = 'printf("\\n");'
             
        elif opcode == 500: # PUSH (500)
            consume_separator()
            # Expect number literal `990`...
            val = get_number_literal()
            # If get_number_literal fails (e.g. no 990), val is None/0.
            if val is None: val = 0
            instr_c = f'push({val});'
            
        elif opcode == 501: # POP (501)
            consume_separator()
            instr_c = 'pop();'
            
        elif opcode == 510: # STORE (510)
            consume_separator()
            # Pops address, pops value. memory[addr] = value.
            # Wait, order? `ope53.c` (STORE):
            # `pop rbx` (address?)
            # `pop rax` (value?)
            # `mov [memory + rbx*8], rax`
            # So: address is TOS, value is required.
            instr_c = '{ long addr = pop(); long val = pop(); if(addr >= 0 && addr < MEMORY_SIZE) memory[addr] = val; }'

        elif opcode == 511: # LOAD (511)
            consume_separator()
            # Pop address, push value.
            instr_c = '{ long addr = pop(); if(addr >= 0 && addr < MEMORY_SIZE) push(memory[addr]); else push(0); }'

        elif opcode == 600: # ADD
            consume_separator()
            instr_c = '{ long b = pop(); long a = pop(); push(a + b); }'
        elif opcode == 601: # SUB
            consume_separator()
            instr_c = '{ long b = pop(); long a = pop(); push(a - b); }'
        elif opcode == 602: # MUL
            consume_separator()
            instr_c = '{ long b = pop(); long a = pop(); push(a * b); }'
        elif opcode == 603: # DIV
            consume_separator()
            instr_c = '{ long b = pop(); long a = pop(); if (b!=0) push(a / b); else { fprintf(stderr, "Div by zero\\n"); exit(1); } }'
        elif opcode == 604: # MOD
            consume_separator()
            instr_c = '{ long b = pop(); long a = pop(); if (b!=0) push(a % b); else { fprintf(stderr, "Div by zero\\n"); exit(1); } }'

        elif opcode == 700: # JUMP
            consume_separator()
            # Argument is address literal?
            # `codegen.c`: `strncmp(scanner, "70020990", 8)` -> expects literal.
            target = get_number_literal()
            instr_c = f'goto Label_{target};'
            
        elif opcode == 701: # JZ
            consume_separator()
            target = get_number_literal()
            instr_c = f'if (pop() == 0) goto Label_{target};'

        elif opcode == 702: # JNZ
            consume_separator()
            target = get_number_literal()
            instr_c = f'if (pop() != 0) goto Label_{target};'
            
        elif opcode == 801: # EQN
             consume_separator()
             instr_c = '{ long b = pop(); long a = pop(); push(a == b ? 1 : 0); }'
        elif opcode == 802: # GT
             consume_separator()
             instr_c = '{ long b = pop(); long a = pop(); push(a > b ? 1 : 0); }'
        elif opcode == 803: # LT
             consume_separator()
             instr_c = '{ long b = pop(); long a = pop(); push(a < b ? 1 : 0); }'
        
        # Add mapped instructions
        if instr_c:
            instructions.append((addr, instr_c))
        
        # Always try to consume a trailing separator if present?
        # consume_separator() is called inside opcodes.
        pass

    # Write instructions
    for addr, code in instructions:
        # Add indentation
        c_code.append("    " + code)

    # c_code.append("    return 0;") # HALT should handle this, or we trust flow
    c_code.append("}")

    # Write to file
    with open(output_file, 'w') as f:
        f.write('\n'.join(c_code))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input.cless> <output.c>")
        sys.exit(1)
    
    charless_to_c(sys.argv[1], sys.argv[2])

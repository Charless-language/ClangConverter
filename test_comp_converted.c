#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define STACK_SIZE 1024
#define MEMORY_SIZE 1024

long stack[STACK_SIZE];
int sp = -1;
long memory[MEMORY_SIZE];

void push(long value) {
    if (sp >= STACK_SIZE - 1) { fprintf(stderr, "Stack overflow\n"); exit(1); }
    stack[++sp] = value;
}

long pop() {
    if (sp < 0) { fprintf(stderr, "Stack underflow\n"); exit(1); }
    return stack[sp--];
}

int main() {
    // Initialize memory
    memset(memory, 0, sizeof(memory));

    Label_0: ; push(10);
    Label_14: ; push(0);
    Label_27: ; { long addr = pop(); long val = pop(); if(addr >= 0 && addr < MEMORY_SIZE) memory[addr] = val; }
    Label_33: ; push(20);
    Label_47: ; push(1);
    Label_60: ; { long addr = pop(); long val = pop(); if(addr >= 0 && addr < MEMORY_SIZE) memory[addr] = val; }
    Label_66: ; push(0);
    Label_79: ; { long addr = pop(); if(addr >= 0 && addr < MEMORY_SIZE) push(memory[addr]); else push(0); }
    Label_85: ; push(1);
    Label_98: ; { long addr = pop(); if(addr >= 0 && addr < MEMORY_SIZE) push(memory[addr]); else push(0); }
    Label_104: ; { long b = pop(); long a = pop(); push(a <= b ? 1 : 0); }
    Label_110: ; if (pop() == 0) goto Label_174;
    Label_127: ; printf("a <= b\n");
    Label_157: ; goto Label_174;
    Label_174: ; push(1);
    Label_187: ; { long addr = pop(); if(addr >= 0 && addr < MEMORY_SIZE) push(memory[addr]); else push(0); }
    Label_193: ; push(0);
    Label_206: ; { long addr = pop(); if(addr >= 0 && addr < MEMORY_SIZE) push(memory[addr]); else push(0); }
    Label_212: ; { long b = pop(); long a = pop(); push(a >= b ? 1 : 0); }
    Label_218: ; if (pop() == 0) goto Label_282;
    Label_235: ; printf("b >= a\n");
    Label_265: ; goto Label_282;
    Label_282: ; return 0;
}
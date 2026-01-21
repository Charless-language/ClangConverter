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

    Label_0: ; printf("Hello, World!\n");
    Label_59: ; return 0;
}
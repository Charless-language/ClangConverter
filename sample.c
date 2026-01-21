#include <stdio.h>

int main() {
  int a = 10;
  int b = 20;
  int c = a + b;
  printf("Sum: %d\n", c);

  if (c > 20) {
    printf("Greater than 20\n");
  } else {
    printf("Not greater\n");
  }

  int i = 0;
  while (i < 3) {
    printf("Loop %d\n", i);
    i = i + 1;
  }
}

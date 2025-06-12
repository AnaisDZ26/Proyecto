#ifndef STACK_H
#define STACK_H

#include <stdbool.h>

typedef struct Stack Stack;

// Creates an empty stack
Stack* stack_create();

// Pushes an element onto the top of the stack
void stack_push(Stack* stack, void* data);

// Removes and returns the element at the top of the stack
void* top(Stack* stack);

// Returns the element at the top without removing it
void* top(Stack* stack);

// Returns true if the stack is empty
bool empty(Stack* stack);

// Frees the memory allocated for the stack (does not free the elements themselves)
void stack_destroy(Stack* stack);

#endif

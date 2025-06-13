#include "stack.h"
#include <stdlib.h>

typedef struct Node {
    void* data;
    struct Node* next;
} Node;

struct Stack {
    Node* top;
};

Stack* stack_create() {
    Stack* new_stack = (Stack*)malloc(sizeof(Stack));
    new_stack->top = NULL;
    return new_stack;
}

void stack_push(Stack* stack, void* data) {
    Node* new_node = (Node*)malloc(sizeof(Node));
    new_node->data = data;
    new_node->next = stack->top;
    stack->top = new_node;
}

void* pop(Stack* stack) {
    if (empty(stack)) return NULL;

    Node* node_to_remove = stack->top;
    void* data = node_to_remove->data;
    stack->top = node_to_remove->next;
    free(node_to_remove);
    return data;
}

void* top(Stack* stack) {
    if (empty(stack)) return NULL;
    return stack->top->data;
}

bool empty(Stack* stack) {
    return stack->top == NULL;
}

void stack_destroy(Stack* stack) {
    while (!empty(stack)) {
        pop(stack);  // frees each node
    }
    free(stack);
}

#ifndef LIST_H
#define LIST_H

#include <stdio.h>
#include <stdlib.h> // Para size_t (aunque a veces se define en otros headers)
#include <string.h>

// LISTA
// Definición de un nodo de la lista
typedef struct Node {
    void *data;       // Puntero genérico para almacenar cualquier tipo de dato
    struct Node *next;
    struct Node *prev;
} Node;

// Definición de la estructura de la lista
typedef struct List {
    Node *head;       // Puntero al primer nodo
    Node *tail;       // Puntero al último nodo
    Node *current;    // Puntero al nodo actual para la iteración
    size_t size;      // Número de elementos en la lista
} List;

// Funciones públicas del TDA List

// Crea una nueva lista vacía.
List *list_create();

// Agrega un elemento al final de la lista.
void list_pushBack(List *list, void *data);

// Agrega un elemento al inicio de la lista.
void list_pushFront(List *list, void *data);

// Obtiene el primer elemento de la lista y posiciona el iterador 'current'.
void *list_first(List *list);

// Obtiene el siguiente elemento de la lista y avanza el iterador 'current'.
void *list_next(List *list);

// Obtiene el elemento anterior de la lista y retrocede el iterador 'current'.
void *list_prev(List *list);

// Obtiene el último elemento de la lista y posiciona el iterador 'current'.
void *list_last(List *list);

// Elimina el nodo apuntado por 'current' y retorna su dato.
// El iterador 'current' se mueve al siguiente nodo (si existe).
void *list_popCurrent(List *list);

// Elimina el primer nodo de la lista y retorna su dato.
void *list_popFront(List *list);

// Elimina el último nodo de la lista y retorna su dato.
void *list_popBack(List *list);

// Retorna el número de elementos en la lista.
size_t list_size(List *list);

// Limpia todos los elementos de la lista, liberando la memoria de los nodos.
// NO libera la memoria de los datos que los nodos apuntan.
void list_clean(List *list);

// Remueve un elemento específico de la lista.
// Retorna 1 si el elemento fue encontrado y removido, 0 en caso contrario.
// Asume que 'data' es el puntero al dato que se quiere remover.
int list_remove(List *list, void *data);

#endif /* LIST_H */
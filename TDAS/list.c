#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "list.h"

// Crea una nueva lista vacía.
List *list_create() {
    List *list = (List *)malloc(sizeof(List));
    if (list == NULL) {
        perror("Error de memoria al crear la lista");
        return NULL;
    }
    list->head = NULL;
    list->tail = NULL;
    list->current = NULL;
    list->size = 0;
    return list;
}

// Agrega un elemento al final de la lista.
void list_pushBack(List *list, void *data) {
    if (list == NULL) return;

    Node *newNode = (Node *)malloc(sizeof(Node));
    if (newNode == NULL) {
        perror("Error de memoria al crear nodo");
        return;
    }
    newNode->data = data;
    newNode->next = NULL;
    newNode->prev = list->tail; // Apunta al nodo anterior (el actual tail)

    if (list->tail != NULL) {
        list->tail->next = newNode; // El antiguo tail ahora apunta al nuevo nodo
    }
    list->tail = newNode; // El nuevo nodo es el nuevo tail

    if (list->head == NULL) {
        list->head = newNode; // Si la lista estaba vacía, el nuevo nodo también es head
    }
    list->size++;
}

// Agrega un elemento al inicio de la lista.
void list_pushFront(List *list, void *data) {
    if (list == NULL) return;

    Node *newNode = (Node *)malloc(sizeof(Node));
    if (newNode == NULL) {
        perror("Error de memoria al crear nodo");
        return;
    }
    newNode->data = data;
    newNode->next = list->head; // El nuevo nodo apunta al antiguo head
    newNode->prev = NULL;

    if (list->head != NULL) {
        list->head->prev = newNode; // El antiguo head ahora apunta al nuevo nodo
    }
    list->head = newNode; // El nuevo nodo es el nuevo head

    if (list->tail == NULL) {
        list->tail = newNode; // Si la lista estaba vacía, el nuevo nodo también es tail
    }
    list->size++;
}

// Obtiene el primer elemento de la lista y posiciona el iterador 'current'.
void *list_first(List *list) {
    if (list == NULL || list->head == NULL) {
        list->current = NULL;
        return NULL;
    }
    list->current = list->head;
    return list->current->data;
}

// Obtiene el siguiente elemento de la lista y avanza el iterador 'current'.
void *list_next(List *list) {
    if (list == NULL || list->current == NULL || list->current->next == NULL) {
        list->current = NULL; // No hay siguiente elemento o ya estamos al final
        return NULL;
    }
    list->current = list->current->next;
    return list->current->data;
}

// Obtiene el elemento anterior de la lista y retrocede el iterador 'current'.
void *list_prev(List *list) {
    if (list == NULL || list->current == NULL || list->current->prev == NULL) {
        list->current = NULL; // No hay elemento anterior o ya estamos al inicio
        return NULL;
    }
    list->current = list->current->prev;
    return list->current->data;
}

// Obtiene el último elemento de la lista y posiciona el iterador 'current'.
void *list_last(List *list) {
    if (list == NULL || list->tail == NULL) {
        list->current = NULL;
        return NULL;
    }
    list->current = list->tail;
    return list->current->data;
}

// Elimina el nodo apuntado por 'current' y retorna su dato.
void *list_popCurrent(List *list) {
    if (list == NULL || list->current == NULL) return NULL;

    Node *nodeToDelete = list->current;
    void *data = nodeToDelete->data;

    // Actualizar punteros de nodos vecinos
    if (nodeToDelete->prev != NULL) {
        nodeToDelete->prev->next = nodeToDelete->next;
    } else {
        list->head = nodeToDelete->next; // Era la cabeza
    }

    if (nodeToDelete->next != NULL) {
        nodeToDelete->next->prev = nodeToDelete->prev;
    } else {
        list->tail = nodeToDelete->prev; // Era la cola
    }

    // Mover el iterador 'current' al siguiente nodo para continuar la iteración
    list->current = nodeToDelete->next; 
    
    free(nodeToDelete);
    list->size--;
    return data;
}

// Elimina el primer nodo de la lista y retorna su dato.
void *list_popFront(List *list) {
    if (list == NULL || list->head == NULL) return NULL;

    Node *nodeToDelete = list->head;
    void *data = nodeToDelete->data;

    list->head = nodeToDelete->next;
    if (list->head != NULL) {
        list->head->prev = NULL;
    } else {
        list->tail = NULL; // La lista queda vacía
    }

    if (list->current == nodeToDelete) {
        list->current = list->head; // Si current era el nodo eliminado, moverlo
    }

    free(nodeToDelete);
    list->size--;
    return data;
}

// Elimina el último nodo de la lista y retorna su dato.
void *list_popBack(List *list) {
    if (list == NULL || list->tail == NULL) return NULL;

    Node *nodeToDelete = list->tail;
    void *data = nodeToDelete->data;

    list->tail = nodeToDelete->prev;
    if (list->tail != NULL) {
        list->tail->next = NULL;
    } else {
        list->head = NULL; // La lista queda vacía
    }

    if (list->current == nodeToDelete) {
        list->current = list->tail; // Si current era el nodo eliminado, moverlo
    }

    free(nodeToDelete);
    list->size--;
    return data;
}

// Retorna el número de elementos en la lista.
size_t list_size(List *list) {
    if (list == NULL) return 0;
    return list->size;
}

// Limpia todos los elementos de la lista, liberando la memoria de los nodos.
// NO libera la memoria de los datos que los nodos apuntan.
void list_clean(List *list) {
    if (list == NULL) return;

    Node *current = list->head;
    Node *next;
    while (current != NULL) {
        next = current->next;
        free(current); // Liberar el nodo
        current = next;
    }
    list->head = NULL;
    list->tail = NULL;
    list->current = NULL;
    list->size = 0;
}

// Remueve un elemento específico de la lista.
int list_remove(List *list, void *data) {
    if (list == NULL || list->head == NULL) return 0;

    Node *current_node = list->head;
    while (current_node != NULL) {
        if (current_node->data == data) { // Compara punteros de datos directamente
            // Guarda el nodo siguiente para mantener el iterador 'current' si apunta a este nodo
            Node *next_node = current_node->next;

            if (current_node->prev != NULL) {
                current_node->prev->next = current_node->next;
            } else {
                list->head = current_node->next; // El nodo a eliminar es la cabeza
            }

            if (current_node->next != NULL) {
                current_node->next->prev = current_node->prev;
            } else {
                list->tail = current_node->prev; // El nodo a eliminar es la cola
            }

            if (list->current == current_node) {
                list->current = next_node; // Mueve current al siguiente si era el nodo eliminado
            }
            
            free(current_node); // Libera el nodo, no el dato
            list->size--;
            return 1; // Elemento encontrado y removido
        }
        current_node = current_node->next;
    }
    return 0; // Elemento no encontrado
}
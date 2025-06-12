#ifndef MAP_H
#define MAP_H

#include <stdio.h>
#include <stdlib.h> // Para size_t (aunque a veces se define en otros headers)
#include <string.h>
#include "list.h"

// MAP
// Definición de una pareja clave-valor para el mapa
typedef struct MapPair {
    void *key;
    void *value;
} MapPair;

// Definición de la estructura del mapa
typedef struct Map {
    List **buckets; // Array de punteros a List (cada List es un "bucket" o cubo)
    long capacity;  // Capacidad actual de la tabla hash (número de buckets)
    long size;      // Número actual de elementos en el mapa
    long current_bucket; // Índice del cubo actual para iteración
    List *current_pair_list; // Puntero a la lista del cubo actual para iteración
    void *current_pair_node; // Puntero al nodo actual en la lista para iteración

    // Puntero a la función de comparación de claves.
    // Debe devolver 1 si key1 y key2 son iguales, 0 en caso contrario.
    int (*is_equal)(void *key1, void *key2); 

    // Puntero a la función hash.
    // Debe devolver un long para un dado void* key.
    long (*hash)(void *key, long capacity); 
} Map;

// Funciones públicas del TDA Map

// Crea un nuevo mapa.
// Requiere una función de comparación de claves.
Map *map_create(int (*is_equal)(void *key1, void *key2));

// Inserta un nuevo par clave-valor en el mapa.
// Si la clave ya existe, actualiza su valor.
void map_insert(Map *map, void *key, void *value);

// Busca un valor asociado a una clave.
// Retorna el valor si se encuentra, NULL si no.
void *map_search(Map *map, void *key);

// Elimina un par clave-valor del mapa.
// Retorna el valor eliminado si se encuentra, NULL si no.
void *map_remove(Map *map, void *key);

// Obtiene el primer par clave-valor para comenzar la iteración.
// Retorna un MapPair*, NULL si el mapa está vacío.
MapPair *map_first(Map *map);

// Obtiene el siguiente par clave-valor en la iteración.
// Retorna un MapPair*, NULL si no hay más elementos.
MapPair *map_next(Map *map);

// Limpia todos los elementos del mapa (libera las estructuras internas).
// No libera la memoria de las claves ni los valores, eso es responsabilidad del usuario.
void map_clean(Map *map);

// Funciones hash predefinidas (puedes elegir la que necesites)
long string_hash(void *key, long capacity);
long int_hash(void *key, long capacity);

#endif /* MAP_H */
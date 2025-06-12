#include "map.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// MAP
// --- Funciones Hash predefinidas ---

// Función hash para cadenas (strings)
long string_hash(void *key, long capacity) {
    char *str_key = (char *)key;
    unsigned long hash = 5381;
    int c;
    while ((c = *str_key++)) {
        hash = ((hash << 5) + hash) + c; // hash * 33 + c
    }
    return hash % capacity;
}

// Función hash para enteros (int*)
long int_hash(void *key, long capacity) {
    // Para enteros, simplemente usamos el valor del entero como hash.
    // Aseguramos que sea un valor positivo y dentro de la capacidad.
    return (*((int *)key) % capacity + capacity) % capacity;
}

// --- Funciones Auxiliares Internas del Mapa ---

// Redimensiona el mapa si se llena demasiado, aumentando su capacidad.
static void map_rehash(Map *map) {
    long old_capacity = map->capacity;
    map->capacity *= 2; // Duplicar la capacidad
    map->size = 0; // Reiniciar el tamaño, se recalculará al reinsertar
    
    // Almacenar los buckets viejos temporalmente
    List **old_buckets = map->buckets;
    
    // Asignar memoria para los nuevos buckets (listas de listas)
    map->buckets = (List **)calloc(map->capacity, sizeof(List *));
    if (map->buckets == NULL) {
        perror("Error de memoria al rehash (new buckets)");
        // No podemos continuar, el mapa queda en un estado inconsistente.
        // Podríamos intentar revertir o simplemente fallar.
        exit(EXIT_FAILURE); 
    }

    // Recorrer todos los elementos del mapa viejo y reinsertarlos en el nuevo mapa.
    for (long i = 0; i < old_capacity; i++) {
        if (old_buckets[i] != NULL) {
            // Recorrer la lista de pares en este bucket
            MapPair *pair = (MapPair *)list_first(old_buckets[i]);
            while (pair != NULL) {
                // Reinsertar el par en el nuevo mapa
                map_insert(map, pair->key, pair->value);
                // NOTA: map_insert creará un nuevo MapPair y lo agregará.
                // Aquí deberías decidir si quieres liberar los antiguos MapPair.
                // Para esta implementación, los MapPair antiguos de `old_buckets` 
                // serán liberados cuando se liberen las listas `old_buckets[i]`.
                pair = (MapPair *)list_next(old_buckets[i]);
            }
            list_clean(old_buckets[i]); // Limpiar la lista del bucket viejo
            free(old_buckets[i]);       // Liberar la memoria de la lista
        }
    }
    free(old_buckets); // Liberar el array de punteros a listas viejos
}

// Busca un par clave-valor en un bucket específico.
// Retorna el MapPair si se encuentra, NULL si no.
static MapPair *find_pair_in_bucket(List *bucket_list, void *key, int (*is_equal)(void *, void *)) {
    if (bucket_list == NULL) return NULL;

    MapPair *pair = (MapPair *)list_first(bucket_list);
    while (pair != NULL) {
        if (is_equal(pair->key, key)) {
            return pair;
        }
        pair = (MapPair *)list_next(bucket_list);
    }
    return NULL;
}

// --- Implementación de Funciones Públicas del TDA Map ---

Map *map_create(int (*is_equal)(void *key1, void *key2)) {
    Map *map = (Map *)malloc(sizeof(Map));
    if (map == NULL) {
        perror("Error de memoria al crear el mapa");
        return NULL;
    }

    map->capacity = 100; // Capacidad inicial
    map->size = 0;
    map->is_equal = is_equal;
    
    // Por defecto, usa hash de enteros. Puedes cambiarlo después si necesitas string_hash.
    // Idealmente, map_create debería recibir la función hash también.
    map->hash = int_hash; 

    map->buckets = (List **)calloc(map->capacity, sizeof(List *));
    if (map->buckets == NULL) {
        perror("Error de memoria al crear buckets del mapa");
        free(map);
        return NULL;
    }

    map->current_bucket = -1; // Para la iteración
    map->current_pair_list = NULL;
    map->current_pair_node = NULL;

    return map;
}

void map_insert(Map *map, void *key, void *value) {
    if (map == NULL) return;

    // Si el mapa está muy lleno, redimensionar
    if (map->size / (double)map->capacity > 0.75) { // Factor de carga del 75%
        map_rehash(map);
    }

    long bucket_index = map->hash(key, map->capacity);

    // Buscar si la clave ya existe en este bucket
    if (map->buckets[bucket_index] == NULL) {
        map->buckets[bucket_index] = list_create();
        if (map->buckets[bucket_index] == NULL) {
            perror("Error al crear lista para bucket");
            return;
        }
    }

    MapPair *existing_pair = find_pair_in_bucket(map->buckets[bucket_index], key, map->is_equal);

    if (existing_pair != NULL) {
        // La clave ya existe, actualizar el valor
        existing_pair->value = value;
    } else {
        // La clave no existe, crear un nuevo par y agregarlo
        MapPair *new_pair = (MapPair *)malloc(sizeof(MapPair));
        if (new_pair == NULL) {
            perror("Error de memoria al crear MapPair");
            return;
        }
        new_pair->key = key;
        new_pair->value = value;
        list_pushBack(map->buckets[bucket_index], new_pair);
        map->size++;
    }
}

void *map_search(Map *map, void *key) {
    if (map == NULL || map->size == 0) return NULL;

    long bucket_index = map->hash(key, map->capacity);

    // Si el bucket está vacío, la clave no puede estar ahí
    if (map->buckets[bucket_index] == NULL) {
        return NULL;
    }

    MapPair *pair = find_pair_in_bucket(map->buckets[bucket_index], key, map->is_equal);
    if (pair != NULL) {
        return pair->value;
    }
    return NULL;
}

void *map_remove(Map *map, void *key) {
    if (map == NULL || map->size == 0) return NULL;

    long bucket_index = map->hash(key, map->capacity);

    if (map->buckets[bucket_index] == NULL) {
        return NULL;
    }

    // Recorrer la lista para encontrar y eliminar el par
    MapPair *pair_to_remove = NULL;
    void *removed_value = NULL;
    
    list_first(map->buckets[bucket_index]); // Posiciona el iterador al inicio
    MapPair *current_pair = (MapPair *)list_first(map->buckets[bucket_index]);
    while (current_pair != NULL) {
        if (map->is_equal(current_pair->key, key)) {
            pair_to_remove = current_pair;
            removed_value = pair_to_remove->value; // Guardar el valor antes de liberar el par
            list_popCurrent(map->buckets[bucket_index]); // Elimina el nodo actual
            free(pair_to_remove); // Liberar la memoria del MapPair
            map->size--;
            break;
        }
        current_pair = (MapPair *)list_next(map->buckets[bucket_index]);
    }
    
    // Si el bucket queda vacío después de eliminar, podemos liberar la lista
    if (map->buckets[bucket_index] != NULL && list_size(map->buckets[bucket_index]) == 0) {
        list_clean(map->buckets[bucket_index]); // Limpiar la lista (aunque ya está vacía)
        free(map->buckets[bucket_index]);
        map->buckets[bucket_index] = NULL;
    }

    return removed_value;
}

MapPair *map_first(Map *map) {
    if (map == NULL || map->size == 0) return NULL;

    map->current_bucket = -1; // Resetear la iteración
    map->current_pair_list = NULL;
    map->current_pair_node = NULL;

    return map_next(map); // Usar map_next para encontrar el primer elemento
}

MapPair *map_next(Map *map) {
    if (map == NULL) return NULL;

    // Si ya estamos iterando en una lista de bucket
    if (map->current_pair_list != NULL) {
        MapPair *pair = (MapPair *)list_next(map->current_pair_list);
        if (pair != NULL) {
            return pair;
        }
        // Si la lista actual terminó, pasamos al siguiente bucket
        map->current_pair_list = NULL;
    }

    // Buscar el siguiente bucket no vacío
    for (map->current_bucket = map->current_bucket + 1; 
         map->current_bucket < map->capacity; 
         map->current_bucket++) {
        
        if (map->buckets[map->current_bucket] != NULL && 
            list_size(map->buckets[map->current_bucket]) > 0) {
            
            map->current_pair_list = map->buckets[map->current_bucket];
            MapPair *pair = (MapPair *)list_first(map->current_pair_list);
            return pair; // Encontramos el primer elemento en el nuevo bucket
        }
    }

    return NULL; // No hay más elementos en el mapa
}

void map_clean(Map *map) {
    if (map == NULL) return;

    for (long i = 0; i < map->capacity; i++) {
        if (map->buckets[i] != NULL) {
            // Recorrer la lista y liberar cada MapPair
            MapPair *pair = (MapPair *)list_first(map->buckets[i]);
            while (pair != NULL) {
                // NOTA: map_clean NO libera la memoria de key ni value.
                // Eso es responsabilidad del usuario si fueron asignados dinámicamente.
                free(pair); // Liberar el MapPair
                pair = (MapPair *)list_next(map->buckets[i]);
            }
            list_clean(map->buckets[i]); // Limpiar la lista (libera los nodos internos de la lista)
            free(map->buckets[i]);       // Liberar la estructura List
            map->buckets[i] = NULL;
        }
    }
    free(map->buckets); // Liberar el array de punteros a listas
    free(map);          // Liberar la estructura Map
}
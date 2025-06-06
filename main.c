#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_GRID_SIZE 20 // (?)
#define ID_LENGTH 5

typedef struct {
    char id[ID_LENGTH + 1];  // +1 for null terminator
    int width;
    int height;
    int grid[MAX_GRID_SIZE][MAX_GRID_SIZE]; // CAMBIAR POR ESTRUCTURA (?)
} Partida;

Partida* leerConfiguracion(const char* filename) {
    FILE* file = fopen(filename, "r");
    if (!file) {
        printf("Error: No se pudo abrir el archivo %s\n", filename);
        return NULL;
    }

    fclose(file);
    return NULL;
}

void iniciarJuego(const char* filename) {
    char fullpath[256];
    snprintf(fullpath, sizeof(fullpath), "cache/%s", filename);
    
    Partida* partida = leerConfiguracion(fullpath);
    if (!partida) {
        printf("Error: No se pudo cargar la configuración del juego\n");
        return;
    }

    printf("Partida iniciada con ID: %s\n", partida->id);

    free(partida);
}

void mostrarAyuda(const char* program_name) {
    printf("Battleship Game - Ayuda\n");
    printf("======================\n\n");
    printf("Uso: %s <accion> [parametros]\n\n", program_name);

    // ...
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        printf("Error: No se proporcionó ninguna acción\n");
        mostrarAyuda(argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "iniciarJuego") == 0) {
        if (argc != 3) {
            printf("Error: iniciarJuego requiere un archivo de configuración\n");
            mostrarAyuda(argv[0]);
            return 1;
        }
        iniciarJuego(argv[2]);
    } else if (strcmp(argv[1], "--help") == 0 || strcmp(argv[1], "-h") == 0) {
        mostrarAyuda(argv[0]);
    } else {
        printf("Error: Acción desconocida '%s'\n", argv[1]);
        mostrarAyuda(argv[0]);
        return 1;
    }

    return 0;
}
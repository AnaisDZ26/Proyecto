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

int iniciarJuego(const char* filename) {
    char fullpath[256];
    snprintf(fullpath, sizeof(fullpath), "cache/%s", filename);
    
    Partida* partida = leerConfiguracion(fullpath);
    if (!partida) {
        printf("Error: No se pudo cargar la configuración del juego\n");
        return 1;
    }

    printf("Partida iniciada con ID: %s\n", partida->id);

    free(partida);
    return 0;
}

int mostrarAyuda() {
    printf("Battleship Game - Ayuda\n");
    printf("======================\n\n");
    printf("Uso: <accion> [parametros]\n\n");

    // ...
    return 0;
}

int main(int n_args, char* args[]) {

    if (n_args < 2) {
        printf("Error: No se proporcionó ninguna acción\n");
        return mostrarAyuda();
    }

    // main.exe iniciarJuego <archivo_configuracion>
    if (strcmp(args[1], "iniciarJuego") == 0) {
        if (n_args != 3) {
            printf("Error: iniciarJuego requiere un archivo de configuración\n");
            mostrarAyuda();
            return 1;
        }
        return iniciarJuego(args[2]);
    }

    // main.exe listaHistorial
    if (strcmp(args[1], "listaHistorial") == 0) {
        return 1;
    }

    // main.exe buscarPartida <id_partida>
    if (strcmp(args[1], "buscarPartida") == 0) {
        return 1;
    }

    // main.exe ayuda
    if (strcmp(args[1], "ayuda") == 0)
        return mostrarAyuda();
    
    printf("Error: Acción desconocida '%s'\n", args[1]);
    mostrarAyuda();
    return 1;

}
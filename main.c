#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "TDAS/list.h"
#include "TDAS/map.h"
#include "TDAS/stack.h"

#define ID_LENGTH 5 
#define MAX_GRID 20  // Tamaño máximo permitido de la cuadrícula

typedef struct{
    int x;
    int y;
    int tamano;
    int orientacion; // 0 - Horizontal. 1 - Vertical.
    int id;         // ID del barco
} Barco;

typedef struct {
    int **valores;
    List *barcos;
    int ancho;
    int alto;
} Tablero;

typedef struct {
    Tablero *tablero;
    List *objetos;
} Jugador;

typedef struct
{
    char id[ID_LENGTH + 1]; // +1 para el terminador nulo
    List *jugadores;
} Partida;

typedef struct {
    int CoorX;
    int CoorY;
    int TypeMov; // 4 - Ataque. 5 - Usar Objeto.
} Movimiento;

// Función para imprimir un tablero
void imprimirTablero(Tablero *tablero, int es_bot) {
    printf("\nTablero del %s:\n", es_bot ? "Bot" : "Jugador");
    printf("  ");
    for (int j = 0; j < tablero->ancho; j++) {
        printf("%2d ", j);
    }
    printf("\n");

    for (int i = 0; i < tablero->alto; i++) {
        printf("%2d ", i);
        for (int j = 0; j < tablero->ancho; j++) {
            if (es_bot) {
                // Para el tablero del bot, mostrar los valores reales (IDs de barcos)
                printf("%2d ", tablero->valores[i][j]);
            } else {
                // Para el tablero del jugador, mostrar todos los barcos
                printf("%2d ", tablero->valores[i][j]);
            }
        }
        printf("\n");
    }
}

// Función para imprimir información de los barcos
void imprimirBarcos(List *barcos) {
    printf("\nBarcos:\n");
    printf("ID | Tamano | Orientacion | Posicion\n");
    printf("--------------------------------\n");
    
    for (Barco *b = list_first(barcos); b != NULL; b = list_next(barcos)) {
        printf("%2d | %6d | %10s | (%d,%d)\n", 
               b->id, 
               b->tamano, 
               b->orientacion == 0 ? "Horizontal" : "Vertical",
               b->x, b->y);
    }
}

void verEstadoPartida(Partida *partida) {
    if (!partida) {
        printf("Error: No hay partida activa\n");
        return;
    }

    printf("\n=== Estado de la Partida ===\n");
    printf("ID de la partida: %s\n", partida->id);

    // Get both players
    Jugador *jugador = list_first(partida->jugadores);
    Jugador *bot = list_next(partida->jugadores);

    if (!jugador || !bot) {
        printf("Error: No se encontraron los jugadores\n");
        return;
    }

    // Print player's board and boats
    imprimirTablero(jugador->tablero, 0);
    imprimirBarcos(jugador->tablero->barcos);

    // Print bot's board and boats
    imprimirTablero(bot->tablero, 1);
    imprimirBarcos(bot->tablero->barcos);

    // Print objects if any
    if (list_size(jugador->objetos) > 0) {
        printf("\nObjetos del jugador:\n");
        // TODO: Print objects when object structure is defined
    }

    if (list_size(bot->objetos) > 0) {
        printf("\nObjetos del bot:\n");
        // TODO: Print objects when object structure is defined
    }

    printf("\n=== Fin del Estado ===\n");
}

Tablero *inicializarTableroBot(List *player_boats, int ancho, int alto){
    Tablero *tablero = (Tablero *) malloc(sizeof(Tablero));
    if (!tablero)
    {
        printf("Error: No se pudo asignar memoria para el tablero\n");
        return NULL;
    }

    // Copiar dimensiones del tablero del jugador
    tablero->ancho = ancho;
    tablero->alto = alto;

    // Inicializar cuadrícula con ceros
    tablero->valores = (int **) malloc(tablero->alto * sizeof(int *));
    if (!tablero->valores) {
        printf("Error: No se pudo asignar memoria para la cuadrícula\n");
        free(tablero);
        return NULL;
    }

    for (int i = 0; i < tablero->alto; i++) {
        tablero->valores[i] = (int *) malloc(tablero->ancho * sizeof(int));
        if (!tablero->valores[i]) {
            printf("Error: No se pudo asignar memoria para la fila %d\n", i);
            // Liberar memoria previamente asignada
            for (int j = 0; j < i; j++) {
                free(tablero->valores[j]);
            }
            free(tablero->valores);
            free(tablero);
            return NULL;
        }
        // Inicializar fila con ceros
        for (int j = 0; j < tablero->ancho; j++) {
            tablero->valores[i][j] = 0;
        }
    }

    // Inicializar lista de barcos
    tablero->barcos = list_create();
    if (!tablero->barcos) {
        printf("Error: No se pudo crear la lista de barcos\n");
        for (int i = 0; i < tablero->alto; i++) {
            free(tablero->valores[i]);
        }
        free(tablero->valores);
        free(tablero);
        return NULL;
    }

    // Colocar barcos aleatoriamente, coincidiendo con los tamaños de los barcos del jugador
    srand(time(NULL));
    int boat_id = 1;
    
    // Iterar a través de los barcos del jugador para coincidir con sus tamaños
    for (Barco *player_boat = list_first(player_boats); player_boat != NULL; player_boat = list_next(player_boats)) {
        Barco *barco = (Barco *) malloc(sizeof(Barco));
        if (!barco) {
            printf("Error: No se pudo asignar memoria para el barco %d\n", boat_id);
            list_clean(tablero->barcos);
            for (int i = 0; i < tablero->alto; i++) {
                free(tablero->valores[i]);
            }
            free(tablero->valores);
            free(tablero);
            return NULL;
        }

        // Copiar tamaño del barco del jugador
        barco->tamano = player_boat->tamano;
        barco->orientacion = rand() % 2;   // 0 para horizontal, 1 para vertical
        barco->id = boat_id;

        // Intentar colocar el barco
        int max_attempts = 100;  // Prevenir bucles infinitos
        int placed = 0;
        
        while (!placed && max_attempts > 0) {
            // Obtener posición inicial aleatoria
            barco->x = rand() % (tablero->ancho - (barco->orientacion ? 0 : barco->tamano - 1));
            barco->y = rand() % (tablero->alto - (barco->orientacion ? barco->tamano - 1 : 0));

            // Verificar si el barco puede ser colocado
            int can_place = 1;
            for (int i = 0; i < barco->tamano && can_place; i++) {
                int x = barco->x + (barco->orientacion ? 0 : i);
                int y = barco->y + (barco->orientacion ? i : 0);

                // Verificar si la posición es válida y está vacía
                if (x >= tablero->ancho || y >= tablero->alto || tablero->valores[y][x] != 0) {
                    can_place = 0;
                }
            }

            if (can_place) {
                // Colocar el barco estableciendo los valores de la cuadrícula
                for (int i = 0; i < barco->tamano; i++) {
                    int x = barco->x + (barco->orientacion ? 0 : i);
                    int y = barco->y + (barco->orientacion ? i : 0);
                    // Establecer el valor de la celda al ID del barco
                    tablero->valores[y][x] = boat_id;
                }
                placed = 1;
            }
            max_attempts--;
        }

        if (!placed) {
            printf("Error: No se pudo colocar el barco %d después de varios intentos\n", boat_id);
            free(barco);
            list_clean(tablero->barcos);
            for (int i = 0; i < tablero->alto; i++) {
                free(tablero->valores[i]);
            }
            free(tablero->valores);
            free(tablero);
            return NULL;
        }

        // Agregar barco a la lista
        list_pushBack(tablero->barcos, barco);
        boat_id++;
    }

    return tablero;
}

// Función para manejar la creación y gestión de barcos para una celda
Barco *leerCelda(int boat_id, int i, int j, int rows, int cols, int **grid, List *barcos_temp, int *n_barcos) {
    if (boat_id <= 0) return NULL;

    // Verificar si este barco ya existe en nuestra lista
    Barco *barco = NULL;
    for (Barco *b = list_first(barcos_temp); b != NULL; b = list_next(barcos_temp)) {
        if (b->id == boat_id) {
            barco = b;
            break;
        }
    }

    if (barco == NULL) {
        // Crear nuevo barco
        barco = (Barco *)malloc(sizeof(Barco));
        if (!barco) {
            printf("Error: No se pudo asignar memoria para el barco\n");
            return NULL;
        }
        barco->id = boat_id;
        barco->x = j;  // Columna es x
        barco->y = i;  // Fila es y
        barco->tamano = 1;
        barco->orientacion = -1;  // No determinada aún
        list_pushBack(barcos_temp, barco);
        (*n_barcos)++;
    } else {
        // Actualizar barco existente
        barco->tamano++;
    }
    return barco;
}

Partida *leerConfiguracion(const char *archivo)
{
    FILE *file = fopen(archivo, "r");
    if (!file)
    {
        printf("Error: No se pudo abrir el archivo %s\n", archivo);
        return NULL;
    }

    Partida *partida = (Partida *) malloc(sizeof(Partida));
    if (!partida)
    {
        printf("Error: No se pudo asignar memoria para la partida\n");
        fclose(file);
        return NULL;
    }

    // Leer ID del juego
    if (fscanf(file, "%5s", partida->id) != 1) {
        printf("Error: No se pudo leer el ID de la partida\n");
        free(partida);
        fclose(file);
        return NULL;
    }

    // Inicializar lista de jugadores
    partida->jugadores = list_create();
    if (!partida->jugadores) {
        printf("Error: No se pudo crear la lista de jugadores\n");
        free(partida);
        fclose(file);
        return NULL;
    }

    Jugador *bot = (Jugador *) malloc(sizeof(Jugador));
    if (!bot)
    {
        printf("Error: No se pudo asignar memoria para el bot\n");
        list_clean(partida->jugadores);
        free(partida);
    }

    Jugador *usuario = (Jugador *) malloc(sizeof(Jugador));
    if (!usuario)
    {
        printf("Error: No se pudo asignar memoria para el jugador\n");
        list_clean(partida->jugadores);
        free(partida);
        fclose(file);
        return NULL;
    }

    Tablero *tablero_usuario = (Tablero *) malloc(sizeof(Tablero));
    if (!tablero_usuario)
    {
        printf("Error: No se pudo asignar memoria para el tablero\n");
        list_clean(partida->jugadores);
        free(partida);
        fclose(file);
        return NULL;
    }

    // Leer dimensiones de la cuadrícula
    int rows, cols;
    if (fscanf(file, "%d %d", &rows, &cols) != 2 || rows <= 0 || cols <= 0 || rows > MAX_GRID || cols > MAX_GRID) {
        printf("Error: Dimensiones de la cuadrícula inválidas\n");
        list_clean(partida->jugadores);
        free(partida);
        fclose(file);
        return NULL;
    }

    // Establecer dimensiones del tablero
    tablero_usuario->ancho = cols;
    tablero_usuario->alto = rows;

    // Asignar memoria para la cuadrícula
    tablero_usuario->valores = (int **) malloc(rows * sizeof(int *));
    if (!tablero_usuario->valores) {
        printf("Error: No se pudo asignar memoria para la cuadrícula\n");
        list_clean(partida->jugadores);
        free(tablero_usuario);
        free(usuario);
        free(partida);
        fclose(file);
        return NULL;
    }

    for (int i = 0; i < rows; i++) {
        tablero_usuario->valores[i] = (int *) malloc(cols * sizeof(int));
        if (!tablero_usuario->valores[i]) {
            printf("Error: No se pudo asignar memoria para la fila %d\n", i);
            // Liberar memoria previamente asignada
            for (int j = 0; j < i; j++) {
                free(tablero_usuario->valores[j]);
            }
            free(tablero_usuario->valores);
            list_clean(partida->jugadores);
            free(tablero_usuario);
            free(usuario);
            free(partida);
            fclose(file);
            return NULL;
        }
        // Inicializar fila con ceros
        for (int j = 0; j < cols; j++) {
            tablero_usuario->valores[i][j] = 0;
        }
    }

    // Leer los valores de la cuadrícula del archivo
    int n_barcos = 0;
    List *barcos_temp = list_create();  // Lista temporal para almacenar barcos mientras se leen
    if (!barcos_temp) {
        printf("Error: No se pudo crear la lista temporal de barcos\n");
        for (int i = 0; i < rows; i++) {
            free(tablero_usuario->valores[i]);
        }
        free(tablero_usuario->valores);
        list_clean(partida->jugadores);
        free(partida);
        fclose(file);
        return NULL;
    }

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (fscanf(file, "%d", &tablero_usuario->valores[i][j]) != 1) {
                printf("Error: No se pudo leer el valor en la posición [%d][%d]\n", i, j);
                list_clean(barcos_temp);
                for (int k = 0; k < rows; k++) {
                    free(tablero_usuario->valores[k]);
                }
                free(tablero_usuario->valores);
                list_clean(partida->jugadores);
                free(partida);
                fclose(file);
                return NULL;
            }

            Barco *barco = leerCelda(tablero_usuario->valores[i][j], i, j, rows, cols, 
                                   tablero_usuario->valores, barcos_temp, &n_barcos);
            if (!barco && tablero_usuario->valores[i][j] > 0) {
                // Error ocurrió en leerCelda
                list_clean(barcos_temp);
                for (int k = 0; k < rows; k++) {
                    free(tablero_usuario->valores[k]);
                }
                free(tablero_usuario->valores);
                list_clean(partida->jugadores);
                free(partida);
                fclose(file);
                return NULL;
            }
        }
    }

    // Transferir barcos de la lista temporal a la lista de barcos del tablero
    tablero_usuario->barcos = list_create();
    if (!tablero_usuario->barcos) {
        printf("Error: No se pudo crear la lista de barcos del tablero\n");
        list_clean(barcos_temp);
        for (int i = 0; i < rows; i++) {
            free(tablero_usuario->valores[i]);
        }
        free(tablero_usuario->valores);
        list_clean(partida->jugadores);
        free(tablero_usuario);
        free(usuario);
        free(partida);
        fclose(file);
        return NULL;
    }

    // Mover barcos de la lista temporal a la lista del tablero
    for (Barco *b = list_first(barcos_temp); b != NULL; b = list_next(barcos_temp)) {
        list_pushBack(tablero_usuario->barcos, b);
    }
    list_clean(barcos_temp);  // Solo destruir la lista, no los barcos

    // Determinar orientación de los barcos después de que todos están almacenados
    for (Barco *b = list_first(tablero_usuario->barcos); b != NULL; b = list_next(tablero_usuario->barcos)) {
        // Verificar si hay una celda de barco a la derecha
        if (b->x + 1 < cols && tablero_usuario->valores[b->y][b->x + 1] == b->id) {
            b->orientacion = 0;  // Horizontal
        }
        // Verificar si hay una celda de barco abajo
        else if (b->y + 1 < rows && tablero_usuario->valores[b->y + 1][b->x] == b->id) {
            b->orientacion = 1;  // Vertical
        }
    }

    usuario->tablero = tablero_usuario;
    usuario->objetos = list_create();
    if (!usuario->objetos) {
        printf("Error: No se pudo crear la lista de objetos\n");
        list_clean(tablero_usuario->barcos);
        for (int i = 0; i < rows; i++) {
            free(tablero_usuario->valores[i]);
        }
        free(tablero_usuario->valores);
        list_clean(partida->jugadores);
        free(tablero_usuario);
        free(usuario);
        free(partida);
        fclose(file);
        return NULL;
    }

    Tablero *tablero_bot = inicializarTableroBot(usuario->tablero->barcos, usuario->tablero->ancho, usuario->tablero->alto);
    if (!tablero_bot)
    {
        printf("Error: No se pudo inicializar el tablero del bot\n");
        list_clean(partida->jugadores);
        free(partida);
        fclose(file);
        return NULL;
    }
    bot->tablero = tablero_bot;
    bot->objetos = list_create();
    if (!bot->objetos) {
        printf("Error: No se pudo crear la lista de objetos\n");
        list_clean(tablero_bot->barcos);
        for (int i = 0; i < tablero_bot->alto; i++) {
            free(tablero_bot->valores[i]);
        }
        free(tablero_bot->valores);
        free(tablero_bot);
        list_clean(partida->jugadores);
        free(partida);
        fclose(file);
        return NULL;
    }

    // Agregar el usuario a la lista de jugadores
    list_pushBack(partida->jugadores, usuario);
    list_pushBack(partida->jugadores, bot);

    fclose(file);
    return partida;
}

int iniciarJuego(const char *archivo)
{
    char fullpath[256];
    snprintf(fullpath, sizeof(fullpath), "cache/%s", archivo);

    Partida *partida = leerConfiguracion(fullpath);
    if (!partida)
    {
        printf("Error: No se pudo cargar la configuración del juego\n");
        return 1;
    }

    printf("Partida iniciada con ID: %s\n", partida->id);
    verEstadoPartida(partida);

    free(partida);
    return 0;
}

int mostrarAyuda()
{
    printf("Battleship Game - Ayuda\n");
    printf("======================\n\n");
    printf("Uso: <accion> [parametros]\n\n");

    // ...
    return 0;
}

int main(int n_args, char *args[])
{
    if (n_args < 2)
    {
        printf("Error: No se proporcionó ninguna acción\n");
        return mostrarAyuda();
    }

    // main.exe iniciarJuego <archivo_configuracion>
    if (strcmp(args[1], "iniciarJuego") == 0)
    {
        if (n_args != 3)
        {
            printf("Error: iniciarJuego requiere un archivo de configuración\n");
            mostrarAyuda();
            return 1;
        }
        return iniciarJuego(args[2]);
    }

    // main.exe listaHistorial
    if (strcmp(args[1], "listaHistorial") == 0)
    {
        return 1;
    }

    // main.exe buscarPartida <id_partida>
    if (strcmp(args[1], "buscarPartida") == 0)
    {
        return 1;
    }

    // main.exe ayuda
    if (strcmp(args[1], "ayuda") == 0)
        return mostrarAyuda();

    printf("Error: Acción desconocida '%s'\n", args[1]);
    mostrarAyuda();
    return 1;
}
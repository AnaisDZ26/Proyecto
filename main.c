#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "TDAS/list.h"
#include "TDAS/map.h"
#include "TDAS/stack.h"

#define ID_LENGTH 5
#define MAX_GRID 20 // Tamaño máximo permitido de la cuadrícula
#define DEV 1

static int turno = 0; // Variable global para el turno actua / 0 = jugador, 1 = bot

typedef struct
{
    int x;
    int y;
    int tamano;
    int orientacion; // 0 - Horizontal. 1 - Vertical.
    int id;          // ID del barco
} Barco;

typedef struct
{
    int **valores;
    List *barcos;
    int ancho;
    int alto;
} Tablero;

typedef struct
{
    Tablero *tablero;
    List *objetos;
    char nombre[256];
} Jugador;

typedef struct
{
    char id[ID_LENGTH + 1]; // +1 para el terminador nulo
    List *jugadores;
    List *mensajesEstado;
    int puntaje;
    Stack *historial;
    FILE *archivo_partida;
} Partida;

typedef struct
{
    int idJugador; // 0 Bot - 1 Jugador

    int CoorX;
    int CoorY;
    int TypeMov; // 4 - Ataque. 5 - Usar Objeto.

    int *parametros_adicionales;
    int n_parametros_adicionales;
} Movimiento;

void aplicarAtaque(Partida *partida, int x, int y);

// Función para imprimir un tablero
void imprimirTablero(Tablero *tablero, int es_bot)
{
    printf("\nTablero del %s:\n", es_bot ? "Bot" : "Jugador");
    printf("  ");
    for (int j = 0; j < tablero->ancho; j++)
    {
        printf("%2d ", j);
    }
    printf("\n");

    for (int i = 0; i < tablero->alto; i++)
    {
        printf("%2d ", i);
        for (int j = 0; j < tablero->ancho; j++)
        {
            if (es_bot)
            {
                // Para el tablero del bot, mostrar los valores reales (IDs de barcos)
                printf("%2d ", tablero->valores[i][j]);
            }
            else
            {
                // Para el tablero del jugador, mostrar todos los barcos
                printf("%2d ", tablero->valores[i][j]);
            }
        }
        printf("\n");
    }
}

// Función para imprimir información de los barcos
void imprimirBarcos(List *barcos)
{
    printf("\nBarcos:\n");
    printf("ID | Tamano | Orientacion | Posicion\n");
    printf("--------------------------------\n");

    for (Barco *b = list_first(barcos); b != NULL; b = list_next(barcos))
    {
        printf("%2d | %6d | %10s | (%d,%d)\n",
               b->id,
               b->tamano,
               b->orientacion == 0 ? "Horizontal" : "Vertical",
               b->x, b->y);
    }
}

// Función para imprimir el estado de la partida
void verEstadoPartida(Partida *partida)
{
    if (!partida)
    {
        printf("Error: No hay partida activa\n");
        return;
    }

    printf("\n=== Estado de la Partida ===\n");
    printf("ID de la partida: %s\n", partida->id);

    // Get both players
    Jugador *jugador = list_first(partida->jugadores);
    Jugador *bot = list_next(partida->jugadores);

    if (!jugador || !bot)
    {
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
    if (list_size(jugador->objetos) > 0)
    {
        printf("\nObjetos del jugador:\n");
        // TODO: Print objects when object structure is defined
    }

    if (list_size(bot->objetos) > 0)
    {
        printf("\nObjetos del bot:\n");
        // TODO: Print objects when object structure is defined
    }

    printf("\n=== Fin del Estado ===\n");
}

// Función para inicializar el tablero del bot
Tablero *inicializarTableroBot(List *player_boats, int ancho, int alto)
{
    Tablero *tablero = (Tablero *)malloc(sizeof(Tablero));
    if (!tablero)
    {
        printf("Error: No se pudo asignar memoria para el tablero\n");
        return NULL;
    }

    // Copiar dimensiones del tablero del jugador
    tablero->ancho = ancho;
    tablero->alto = alto;

    // Inicializar cuadrícula con ceros
    tablero->valores = (int **)malloc(tablero->alto * sizeof(int *));
    if (!tablero->valores)
    {
        printf("Error: No se pudo asignar memoria para la cuadrícula\n");
        free(tablero);
        return NULL;
    }

    for (int i = 0; i < tablero->alto; i++)
    {
        tablero->valores[i] = (int *)malloc(tablero->ancho * sizeof(int));
        if (!tablero->valores[i])
        {
            printf("Error: No se pudo asignar memoria para la fila %d\n", i);
            // Liberar memoria previamente asignada
            for (int j = 0; j < i; j++)
            {
                free(tablero->valores[j]);
            }
            free(tablero->valores);
            free(tablero);
            return NULL;
        }
        // Inicializar fila con ceros
        for (int j = 0; j < tablero->ancho; j++)
        {
            tablero->valores[i][j] = 0;
        }
    }

    // Inicializar lista de barcos
    tablero->barcos = list_create();
    if (!tablero->barcos)
    {
        printf("Error: No se pudo crear la lista de barcos\n");
        for (int i = 0; i < tablero->alto; i++)
        {
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
    for (Barco *player_boat = list_first(player_boats); player_boat != NULL; player_boat = list_next(player_boats))
    {
        Barco *barco = (Barco *)malloc(sizeof(Barco));
        if (!barco)
        {
            printf("Error: No se pudo asignar memoria para el barco %d\n", boat_id);
            list_clean(tablero->barcos);
            for (int i = 0; i < tablero->alto; i++)
            {
                free(tablero->valores[i]);
            }
            free(tablero->valores);
            free(tablero);
            return NULL;
        }

        // Copiar tamaño del barco del jugador
        barco->tamano = player_boat->tamano;
        barco->orientacion = rand() % 2; // 0 para horizontal, 1 para vertical
        barco->id = boat_id;

        // Intentar colocar el barco
        int max_attempts = 100; // Prevenir bucles infinitos
        int placed = 0;

        while (!placed && max_attempts > 0)
        {
            // Obtener posición inicial aleatoria
            barco->x = rand() % (tablero->ancho - (barco->orientacion ? 0 : barco->tamano - 1));
            barco->y = rand() % (tablero->alto - (barco->orientacion ? barco->tamano - 1 : 0));

            // Verificar si el barco puede ser colocado
            int can_place = 1;
            for (int i = 0; i < barco->tamano && can_place; i++)
            {
                int x = barco->x + (barco->orientacion ? 0 : i);
                int y = barco->y + (barco->orientacion ? i : 0);

                // Verificar si la posición es válida y está vacía
                if (x >= tablero->ancho || y >= tablero->alto || tablero->valores[y][x] != 0)
                {
                    can_place = 0;
                }
            }

            if (can_place)
            {
                // Colocar el barco estableciendo los valores de la cuadrícula
                for (int i = 0; i < barco->tamano; i++)
                {
                    int x = barco->x + (barco->orientacion ? 0 : i);
                    int y = barco->y + (barco->orientacion ? i : 0);
                    // Establecer el valor de la celda al ID del barco
                    tablero->valores[y][x] = boat_id;
                }
                placed = 1;
            }
            max_attempts--;
        }

        if (!placed)
        {
            printf("Error: No se pudo colocar el barco %d después de varios intentos\n", boat_id);
            free(barco);
            list_clean(tablero->barcos);
            for (int i = 0; i < tablero->alto; i++)
            {
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
Barco *leerCelda(int boat_id, int i, int j, int rows, int cols, int **grid, List *barcos_temp, int *n_barcos)
{
    if (boat_id <= 0)
        return NULL;

    // Verificar si este barco ya existe en nuestra lista
    Barco *barco = NULL;
    for (Barco *b = list_first(barcos_temp); b != NULL; b = list_next(barcos_temp))
    {
        if (b->id == boat_id)
        {
            barco = b;
            break;
        }
    }

    if (barco == NULL)
    {
        // Crear nuevo barco
        barco = (Barco *)malloc(sizeof(Barco));
        if (!barco)
        {
            printf("Error: No se pudo asignar memoria para el barco\n");
            return NULL;
        }
        barco->id = boat_id;
        barco->x = j; // Columna es x
        barco->y = i; // Fila es y
        barco->tamano = 1;
        barco->orientacion = -1; // No determinada aún
        list_pushBack(barcos_temp, barco);
        (*n_barcos)++;
    }
    else
    {
        // Actualizar barco existente
        barco->tamano++;
    }
    return barco;
}

// Función para informar el estado de una casilla
void informarCasilla(Partida *partida, int x, int y)
{
    Jugador *usuario = list_first(partida->jugadores);
    Jugador *bot = list_next(partida->jugadores);

    int valor = bot->tablero->valores[y][x];

    if (valor == 0)
    {
        bot->tablero->valores[y][x] = 99;
        valor = 99;
    }

    char *mensaje = malloc(sizeof(char) * 256);
    sprintf(mensaje, "9 %d %d %d", x, y, valor); // Informe de estado de casilla
    list_pushBack(partida->mensajesEstado, mensaje);
}

// Funcion para aplicar ataque a una casilla
void aplicarAtaque(Partida *partida, int x, int y)
{
    Jugador *usuario = list_first(partida->jugadores);
    Jugador *bot = list_next(partida->jugadores);

    int ancho = bot->tablero->ancho;
    int alto = bot->tablero->alto;

    char *mensaje = malloc(sizeof(char) * 256);

    int valor;
    if (x >= 0 && x < ancho && y >= 0 && y < alto)
    {
        valor = bot->tablero->valores[y][x];

        // Check if this cell has already been attacked
        if (valor == 99 || valor < 0)
        {
            // Cell already attacked, don't attack again
            free(mensaje);
            return;
        }

        if (valor > 0) // Impacto a un barco
        {
            valor = -valor; // Mark as hit
        }
        else if (valor == 0)
        {
            valor = 99; // Impacto al agua
        }
        else
        {
            puts("Error: La coordenada ingresada no es válida :()\n");
            free(mensaje);
            exit(1);
        }
    }
    else
    {
        puts("Coordenada fuera de rango :(\n");
        free(mensaje);
        exit(1);
    }

    bot->tablero->valores[y][x] = valor;
    informarCasilla(partida, x, y);
}

// Función para crear un torpedo
void ObjectTorpedo(Partida *partida, Tablero *tablero, int CoorX, int CoorY, int Orientacion)
{
    // Validate initial coordinates
    if (CoorX < 0 || CoorX >= tablero->ancho || CoorY < 0 || CoorY >= tablero->alto)
    {
        printf("Error: Coordenadas iniciales fuera de rango\n");
        return;
    }

    // Determine direction based on orientation
    // Orientacion 6: Horizontal (left to right)
    // Orientacion 7: Vertical (top to bottom)
    int dir_x = 0, dir_y = 0;
    if (Orientacion == 6) // Horizontal
    {
        if (CoorX == 0)
            dir_x = 1; // Move right
        else
            dir_x = -1; // Move left
    }
    else if (Orientacion == 7) // Vertical
    {
        if (CoorY == 0)
            dir_y = 1; // Move down
        else
            dir_y = -1; // Move up
    }
    else
    {
        printf("Error: Orientación inválida para torpedo\n");
        return;
    }

    int x = CoorX, y = CoorY;

    // Check current position first
    int current = tablero->valores[y][x];
    if (current > 0 && current < 99)
    {
        aplicarAtaque(partida, x, y);
        return; // Hit a ship, stop
    }

    informarCasilla(partida, x, y);

    // Move in the specified direction until hitting a ship or reaching board boundary
    while (1)
    {
        x += dir_x;
        y += dir_y;

        // Check if we're still within board boundaries
        if (x < 0 || x >= tablero->ancho || y < 0 || y >= tablero->alto)
        {
            break; // Out of bounds, stop
        }

        current = tablero->valores[y][x];

        if (current > 0 && current < 99)
        {
            // Hit a ship
            aplicarAtaque(partida, x, y);
            break;
        }

        informarCasilla(partida, x, y);
    }
}

void usarObjeto(Partida *partida, char *buffer)
{
    int code, ID;
    sscanf(buffer, "%*d %d", &ID);

    Jugador *jugador = list_first(partida->jugadores);
    Jugador *bot = list_next(partida->jugadores);

    switch (ID)
    {
    case 1:
    { // Bomba

        int CoorX, CoorY;
        if (sscanf(buffer, "%*d %*d %d %d", &CoorX, &CoorY) != 2)
        {
            puts("Error: No se ingresaron parámetros válidos para el objeto");
            return;
        }

        for (int j = CoorY - 1; j <= CoorY + 1; j++)
        {
            for (int i = CoorX - 1; i <= CoorX + 1; i++)
            {
                if (i >= 0 && i < bot->tablero->ancho && j >= 0 && j < bot->tablero->alto)
                {
                    aplicarAtaque(partida, i, j);
                }
            }
        }
        break;
    }

    case 2:
    { // Catalejo
        int CoorX, CoorY;
        if (sscanf(buffer, "%*d %*d %d %d", &CoorX, &CoorY) != 2)
        {
            puts("Error: No se ingresaron parámetros válidos para el objeto");
            return;
        }

        informarCasilla(partida, CoorX, CoorY);

        break;
    }

    case 3:
    { // Torpedo
        int CoorX, CoorY, Orientacion;
        if (sscanf(buffer, "%*d %*d %d %d %d", &CoorX, &CoorY, &Orientacion) != 3)
        {
            puts("Error: No se ingresaron parámetros válidos para el objeto");
            return;
        }

        ObjectTorpedo(partida, bot->tablero, CoorX, CoorY, Orientacion);
        break;
    }

    default:
        printf("ERROR: ID de objeto incorrecta: %d\n", ID);
        break;
    }
}

// Función para leer la configuración de la partida desde un archivo
Partida *leerConfiguracion(const char *archivo)
{
    FILE *file = fopen(archivo, "r");
    if (!file)
    {
        printf("Error: No se pudo abrir el archivo %s\n", archivo);
        return NULL;
    }

    Partida *partida = (Partida *)malloc(sizeof(Partida));
    if (!partida)
    {
        printf("Error: No se pudo asignar memoria para la partida\n");
        fclose(file);
        return NULL;
    }
    partida->historial = stack_create();
    if (!partida->historial)
    {
        printf("Error: No se pudo crear la pila de historial\n");
        fclose(file);
        free(partida);
        return NULL;
    }

    // Leer ID del juego
    if (fscanf(file, "%5s", partida->id) != 1)
    {
        printf("Error: No se pudo leer el ID de la partida\n");
        free(partida);
        fclose(file);
        return NULL;
    }


    // Inicializar lista de jugadores
    partida->jugadores = list_create();
    if (!partida->jugadores)
    {
        printf("Error: No se pudo crear la lista de jugadores\n");
        free(partida);
        fclose(file);
        return NULL;
    }

    // Add this line to initialize mensajesEstado
    partida->mensajesEstado = list_create();
    if (!partida->mensajesEstado)
    {
        printf("Error: No se pudo crear la lista de mensajes de estado\n");
        list_clean(partida->jugadores);
        free(partida);
        fclose(file);
        return NULL;
    }

    Jugador *bot = (Jugador *)malloc(sizeof(Jugador));
    if (!bot)
    {
        printf("Error: No se pudo asignar memoria para el bot\n");
        list_clean(partida->jugadores);
        free(partida);
        fclose(file);
        return NULL;
    }

    strcpy(bot->nombre, "Arturo Prat");

    Jugador *usuario = (Jugador *)malloc(sizeof(Jugador));
    if (!usuario)
    {
        printf("Error: No se pudo asignar memoria para el jugador\n");
        list_clean(partida->jugadores);
        free(partida);
        fclose(file);
        return NULL;
    }

    if (fscanf(file, "%255s", usuario->nombre) != 1)
    {
        printf("Error: No se pudo leer el nombre del jugador\n");
        free(partida);
        fclose(file);
        return NULL;
    }


    Tablero *tablero_usuario = (Tablero *)malloc(sizeof(Tablero));
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
    if (fscanf(file, "%d %d", &rows, &cols) != 2 || rows <= 0 || cols <= 0 || rows > MAX_GRID || cols > MAX_GRID)
    {
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
    tablero_usuario->valores = (int **)malloc(rows * sizeof(int *));
    if (!tablero_usuario->valores)
    {
        printf("Error: No se pudo asignar memoria para la cuadrícula\n");
        list_clean(partida->jugadores);
        free(tablero_usuario);
        free(usuario);
        free(partida);
        fclose(file);
        return NULL;
    }

    for (int i = 0; i < rows; i++)
    {
        tablero_usuario->valores[i] = (int *)malloc(cols * sizeof(int));
        if (!tablero_usuario->valores[i])
        {
            printf("Error: No se pudo asignar memoria para la fila %d\n", i);
            // Liberar memoria previamente asignada
            for (int j = 0; j < i; j++)
            {
                free(tablero_usuario->valores[j]);
            }
            free(tablero_usuario->valores);
            list_clean(partida->jugadores);
            free(partida);
            fclose(file);
            return NULL;
        }
        // Inicializar fila con ceros
        for (int j = 0; j < cols; j++)
        {
            tablero_usuario->valores[i][j] = 0;
        }
    }

    // Leer los valores de la cuadrícula del archivo
    int n_barcos = 0;
    List *barcos_temp = list_create(); // Lista temporal para almacenar barcos mientras se leen
    if (!barcos_temp)
    {
        printf("Error: No se pudo crear la lista temporal de barcos\n");
        for (int i = 0; i < rows; i++)
        {
            free(tablero_usuario->valores[i]);
        }
        free(tablero_usuario->valores);
        list_clean(partida->jugadores);
        free(partida);
        fclose(file);
        return NULL;
    }

    for (int i = 0; i < rows; i++)
    {
        for (int j = 0; j < cols; j++)
        {
            if (fscanf(file, "%d", &tablero_usuario->valores[i][j]) != 1)
            {
                printf("Error: No se pudo leer el valor en la posición [%d][%d]\n", i, j);
                list_clean(barcos_temp);
                for (int k = 0; k < rows; k++)
                {
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
            if (!barco && tablero_usuario->valores[i][j] > 0)
            {
                // Error ocurrió en leerCelda
                list_clean(barcos_temp);
                for (int k = 0; k < rows; k++)
                {
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
    if (!tablero_usuario->barcos)
    {
        printf("Error: No se pudo crear la lista de barcos del tablero\n");
        list_clean(barcos_temp);
        for (int i = 0; i < rows; i++)
        {
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
    for (Barco *b = list_first(barcos_temp); b != NULL; b = list_next(barcos_temp))
    {
        list_pushBack(tablero_usuario->barcos, b);
    }
    list_clean(barcos_temp); // Solo destruir la lista, no los barcos

    // Determinar orientación de los barcos después de que todos están almacenados
    for (Barco *b = list_first(tablero_usuario->barcos); b != NULL; b = list_next(tablero_usuario->barcos))
    {
        // Verificar si hay una celda de barco a la derecha
        if (b->x + 1 < cols && tablero_usuario->valores[b->y][b->x + 1] == b->id)
        {
            b->orientacion = 0; // Horizontal
        }
        // Verificar si hay una celda de barco abajo
        else if (b->y + 1 < rows && tablero_usuario->valores[b->y + 1][b->x] == b->id)
        {
            b->orientacion = 1; // Vertical
        }
    }

    usuario->tablero = tablero_usuario;
    usuario->objetos = list_create();
    if (!usuario->objetos)
    {
        printf("Error: No se pudo crear la lista de objetos\n");
        list_clean(tablero_usuario->barcos);
        for (int i = 0; i < rows; i++)
        {
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

    char buffer[51];
    int actual = 0;
    while (fgets(buffer, sizeof(buffer), file))
    {
        if (actual == 0)
        {
            actual++;
            continue;
        }

        int id, cantidad;
        if (sscanf(buffer, "%d %d", &id, &cantidad) == 2)
        {
            for (int i = 0; i < cantidad; i++)
            {
                int *id_ptr = malloc(sizeof(int));
                *id_ptr = id;
                list_pushBack(usuario->objetos, id_ptr);
            }
        }
        actual++;
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
    if (!bot->objetos)
    {
        printf("Error: No se pudo crear la lista de objetos\n");
        list_clean(tablero_bot->barcos);
        for (int i = 0; i < tablero_bot->alto; i++)
        {
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

int mostrarAyuda()
{
    printf("Battleship Game - Ayuda\n");
    printf("======================\n\n");
    printf("Uso: <accion> [parametros]\n\n");
    printf("Acciones disponibles:\n");
    printf("  iniciarJuego <archivo_configuracion> - Inicia una nueva partida\n");
    printf("  buscarPartida <id_partida> - Muestra el historial de una partida\n");
    printf("  ayuda - Muestra esta ayuda\n\n");
    printf("Formato de entrada durante el juego:\n");
    printf("  <codigo_turno> <numero_acciones>\n");
    printf("  <tipo_accion> [parametros]\n\n");
    printf("Tipos de acción:\n");
    printf("  4 <x> <y> - Ataque en coordenadas (x,y)\n");
    printf("  5 <id_objeto> <x> <y> <orientacion> - Usar objeto\n\n");
    printf("Objetos disponibles:\n");
    printf("  1 - Bomba (ataca área 3x3)\n");
    printf("  2 - Catalejo (revela área 3x3)\n");
    printf("  3 - Torpedo (ataca en línea)\n");
    return 0;
}

// Función para cerrar el archivo de partida y moverlo a la carpeta data
// También actualiza la lista de partidas en data/list.txt
void cerrarArchivoPartida(Partida *partida)
{
    fclose(partida->archivo_partida);

    char old_path[256];
    snprintf(old_path, sizeof(old_path), "cache/%s.txt", partida->id);

    char new_path[256];
    snprintf(new_path, sizeof(new_path), "data/%s.txt", partida->id);
    rename(old_path, new_path);

    FILE *list_file = fopen("data/list.txt", "a");
    fprintf(list_file, "%s\n", partida->id);
    fclose(list_file);
}

void mostrarMensajesEstado(Partida *partida)
{

    FILE *archivo_partida = partida->archivo_partida;

    int n_mensajes = list_size(partida->mensajesEstado);
    printf("8 %d\n", n_mensajes);
    fprintf(archivo_partida, "8 %d\n", n_mensajes);

    char *mensaje;
    while ((mensaje = list_popFront(partida->mensajesEstado)) != NULL)
    {
        printf("%s\n", mensaje);

        fprintf(archivo_partida, "%s\n", mensaje);
        if (strncmp(mensaje, "777", 3) == 0)
            cerrarArchivoPartida(partida);
    }

    fflush(stdout);
}

void registrarMovimientoArchivo(const char *rutaArchivo, Movimiento *mov)
{
    FILE *file = fopen(rutaArchivo, "a");
    if (!file)
    {
        printf("Error: No se pudo abrir el archivo para registrar movimiento\n");
        return;
    }
    fprintf(file, "MOV %d %d %d\n", mov->TypeMov, mov->CoorX, mov->CoorY);
    fclose(file);
}

void leerAccion(Partida *partida, char *buffer)
{
    int tipo_accion;

    if (sscanf(buffer, "%d", &tipo_accion) != 1)
    {
        puts("Error: No se ingresó un tipo de acción válido");
        return;
    }

    if (tipo_accion == 4)
    {
        int x, y;
        if (sscanf(buffer, "%*d %d %d", &x, &y) != 2)
        {
            puts("Error: No se ingresaron coordenadas válidas para el ataque");
            return;
        }

        aplicarAtaque(partida, x, y);

        Movimiento *mov = malloc(sizeof(Movimiento));
        if (!mov)
            return;

        mov->CoorX = x;
        mov->CoorY = y;
        mov->TypeMov = 4;

        stack_push(partida->historial, mov);
    }
    else if (tipo_accion == 5)
    {

        usarObjeto(partida, buffer);

        /*
        Movimiento *mov = malloc(sizeof(Movimiento));
        if (!mov)a
            return;

        mov->CoorX = x;
        mov->CoorY = y;
        mov->TypeMov = 5;

        stack_push(partida->historial, mov); */
    }
    else
    {
        puts("Error: No se ingresó un tipo de acción válido");
        mostrarAyuda();
        exit(1);
    }
}

void leerTurno(Partida *partida, char *eleccion)
{
    int codigo, n_acciones;
    if (sscanf(eleccion, "%d %d", &codigo, &n_acciones) != 2)
    {
        puts("Error: La elección no es correcta");
        exit(1);
        return;
    }

    list_clean(partida->mensajesEstado);

    FILE *archivo_partida = partida->archivo_partida;
    fprintf(archivo_partida, "%s\n", eleccion);

    for (int i = 0; i < n_acciones; i++)
    {
        char buffer[256];
        if (fgets(buffer, sizeof(buffer), stdin) == NULL)
        {
            puts("Error: No se pudo leer la entrada");
            return;
        }

        // Remove newline character if present
        size_t len = strlen(buffer);
        if (len > 0 && buffer[len - 1] == '\n')
        {
            buffer[len - 1] = '\0';
        }

        fprintf(archivo_partida, "%s\n", buffer);

        leerAccion(partida, buffer);
    }
}

int verificarFinalizacion(Partida *partida) // 0 - No finalizado, 1 - Ganador, 2 - Perdedor
{
    Jugador *current = list_first(partida->jugadores);
    if (current == NULL)
    {
        return true;
    }

    FILE *file = NULL;
    if (DEV)
    {
        file = fopen("cache/state.txt", "w");
        if (!file)
        {
            printf("Error: No se pudo abrir el archivo para registrar el estado\n");
            return true;
        }
    }

    int winner = 1;
    // Check both players
    do
    {
        bool hasIntactShips = false;
        for (int i = 0; i < current->tablero->alto; i++)
        {
            for (int j = 0; j < current->tablero->ancho; j++)
            {
                // Check for intact ships (positive values that are not 99)
                if (current->tablero->valores[i][j] > 0 && current->tablero->valores[i][j] != 99)
                {
                    hasIntactShips = true;
                    break;
                }

                if (DEV)
                    fprintf(file, "%d ", current->tablero->valores[i][j]);
            }

            if (DEV)
                fprintf(file, "\n");

            if (hasIntactShips && !DEV)
                break;
        }

        if (DEV)
            fprintf(file, "\n");

        // If this player has no intact ships, game is over
        if (!hasIntactShips)
            return winner;

        winner++;

        current = list_next(partida->jugadores);
    } while (current != NULL);

    if (DEV)
        fclose(file);

    // Both players still have intact ships
    return 0;
}

// Función para tomar una decisión de ataque del bot
// Implementa una estrategia de ataque basada en impactos previos y patrones de búsqueda
void tomarDecision(Partida *partida) {
    Jugador *jugador = list_first(partida->jugadores);
    Tablero *tablero = jugador->tablero;
    int ancho = tablero->ancho;
    int alto = tablero->alto;
    int x_decidida = -1, y_decidida = -1;

    // 1. Buscar impactos previos para completar barcos
    for (int y = 0; y < alto && x_decidida == -1; y++) {
        for (int x = 0; x < ancho && x_decidida == -1; x++) {
            int valor = tablero->valores[x][y]; 
            if (valor < 0) { // Celda con impacto
                // Verificar las 4 direcciones adyacentes
                int dx[] = {1, -1, 0, 0};
                int dy[] = {0, 0, 1, -1};
                
                for (int i = 0; i < 4 && x_decidida == -1; i++) {
                    int nx = x + dx[i];
                    int ny = y + dy[i];
                    
                    int delta = tablero->valores[nx][ny];
                    if (nx >= 0 && nx < ancho && ny >= 0 && ny < alto &&
                        delta >= 0 && delta != 99) {
                        x_decidida = nx;
                        y_decidida = ny;
                    }
                }
            }
        }
    }

    // 2. Si no encontró impactos pendientes, usar patrón de búsqueda
    if (x_decidida == -1) {
        static int last_x = 0, last_y = 0;
        int encontrado = 0;
        
        for (int y = last_y; y < alto && !encontrado; y++) {
            for (int x = (y == last_y ? last_x : 0); x < ancho && !encontrado; x++) {
                int valor = tablero->valores[y][x];
                if ((x + y) % 2 == 0 && valor >= 0 && valor != 99) {
                    x_decidida = x;
                    y_decidida = y;
                    encontrado = 1;
                    
                    // Actualizar última posición
                    last_x = x + 1;
                    last_y = y;
                    if (last_x >= ancho) {
                        last_x = 0;
                        last_y++;
                    }
                }
            }
        }
    }
    // 3. Si aún no encontró coordenadas válidas, buscar cualquier celda vacía
    if (x_decidida == -1) {
        for (int y = 0; y < alto && x_decidida == -1; y++) {
            for (int x = 0; x < ancho && x_decidida == -1; x++) {
                int valor = tablero->valores[x][y];
                if (valor >= 0 && valor != 99) {
                    x_decidida = x;
                    y_decidida = y;
                }
            }
        }
    }
    // Si encontró coordenadas válidas, realizar el ataque
    if (x_decidida != -1 && y_decidida != -1) {
        int valor = tablero->valores[x_decidida][y_decidida];
        if (valor > 0) valor = -valor; // Impacto en barco
        else if (valor == 0) valor = 99; // Agua
        
        tablero->valores[x_decidida][y_decidida] = valor;

        // Registrar el mensaje
        char *mensaje = malloc(sizeof(char) * 256);
        if (mensaje) {
            sprintf(mensaje, "4 %d %d", x_decidida, y_decidida);
            list_pushBack(partida->mensajesEstado, mensaje);
        }

        // Registrar en el historial
        Movimiento *mov = malloc(sizeof(Movimiento));
        if (mov) {
            mov->CoorX = x_decidida;
            mov->CoorY = y_decidida;
            mov->TypeMov = 4;
            mov->idJugador = 0; // ID del bot
            stack_push(partida->historial, mov);
        }
    }
}

int calcularPuntajeJugador(Partida *partida)
{
    Jugador *jugador = list_first(partida->jugadores);
    Jugador *bot = list_next(partida->jugadores);

    int puntos = 0;

    for (int i = 0; i < bot->tablero->alto; i++)
    {
        for (int j = 0; j < bot->tablero->ancho; j++)
        {
            if (bot->tablero->valores[i][j] < 0)
                puntos += 5;
        }
    }

    for (int i = 0; i < jugador->tablero->alto; i++)
    {
        for (int j = 0; j < jugador->tablero->ancho; j++)
        {
            if (jugador->tablero->valores[i][j] < 0)
                puntos -= 2;
        }
    }
    return puntos < 0 ? 0 : puntos;
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

    printf("PARDTIDA INICIADA ID %s\n", partida->id);
    fflush(stdout);

    partida->archivo_partida = fopen(fullpath, "a");
    if (!partida->archivo_partida)
        exit(1);
    char buffer[256];
    while (fgets(buffer, sizeof(buffer), stdin))
    {
        size_t len = strlen(buffer);
        if (len > 0 && buffer[len - 1] == '\n')
        {
            buffer[len - 1] = '\0';
        }

        leerTurno(partida, buffer);
        tomarDecision(partida);

        // Check if game is finished after processing the turn
        int resultado = verificarFinalizacion(partida);
        if (resultado > 0)
        {
            char *mensaje = malloc(sizeof(char) * 256);
            partida->puntaje = calcularPuntajeJugador(partida);
            sprintf(mensaje, "777 %d %d", resultado, partida->puntaje);

            list_pushBack(partida->mensajesEstado, mensaje);
        }

        mostrarMensajesEstado(partida);
        fflush(stdout);
    }

    free(partida);
    return 0;
}

// Función para leer una partida desde un archivo de texto
// Devuelve un puntero a una estructura Partida con los datos leídos
Partida *leerPartida(const char *linea)
{
    // Remove newline character safely
    char id[256];
    size_t len = strlen(linea);

    // Check if the line ends with newline and remove it
    if (len > 0 && linea[len - 1] == '\n')
    {
        strncpy(id, linea, len - 1);
        id[len - 1] = '\0'; // Ensure null termination
    }
    else
    {
        strcpy(id, linea); // No newline, copy as is
    }

    char fullpath[256];
    snprintf(fullpath, sizeof(fullpath), "data/%s.txt", id);

    FILE *f = fopen(fullpath, "r");
    if (!f)
        return NULL;

    int victoria = -1, puntuacion = -1; // Initialize with invalid values
    char nombre[256] = ""; // Initialize as empty string

    Stack *pila_historial = stack_create();

    char l[256];
    int i = 0;
    int current_turn = 0; // 0 = bot, 1 = jugador

    while (fgets(l, sizeof(l), f))
    {
        // Remove newline from the line
        size_t line_len = strlen(l);
        if (line_len > 0 && l[line_len - 1] == '\n')
        {
            l[line_len - 1] = '\0';
        }

        if (strncmp(l, "777", 3) == 0)
        {
            sscanf(l, "%*d %d %d", &victoria, &puntuacion);
            // victoria: 1 = player wins, 2 = bot wins
            // Convert to: 1 = player wins, 0 = bot wins
            victoria = (victoria == 1) ? 1 : 0;
        }

        if (strncmp(l, "8", 1) == 0)
            current_turn = current_turn == 0 ? 1 : 0;

        if (strncmp(l, "4", 1) == 0)
        {
            Movimiento *movimiento = malloc(sizeof(Movimiento));
            sscanf(l, "%*d %d %d", &movimiento->CoorX, &movimiento->CoorY);
            movimiento->TypeMov = 4;
            movimiento->idJugador = current_turn;
            stack_push(pila_historial, movimiento);
        }

        if (strncmp(l, "5", 1) == 0)
        {
            Movimiento *movimiento = malloc(sizeof(Movimiento));
            int id_objeto;
            sscanf(l, "%*d %d %d %d", &id_objeto, &movimiento->CoorX, &movimiento->CoorY);

            int n_parametros_adicionales = 0;
            int parametros[2];
            parametros[0] = id_objeto;

            if (id_objeto == 1) // Bomba
                n_parametros_adicionales = 1;

            else if (id_objeto == 2) // Catalejo
                n_parametros_adicionales = 1;

            else if (id_objeto == 3) // Torpedo
            {
                int dir = 0;
                sscanf(l, "%*d %d %d %d", &dir);
                parametros[1] = dir;
                n_parametros_adicionales = 2;
            }

            movimiento->parametros_adicionales = malloc(sizeof(int) * n_parametros_adicionales);
            movimiento->n_parametros_adicionales = n_parametros_adicionales;
            for (int i = 0; i < n_parametros_adicionales; i++)
            {
                movimiento->parametros_adicionales[i] = parametros[i];
            }

            movimiento->TypeMov = 5;
            movimiento->idJugador = current_turn;
            stack_push(pila_historial, movimiento);
        }

        if (i == 1)
            strcpy(nombre, l);

        i++;
    }

    // Check if we found valid data
    if (victoria == -1 || puntuacion == -1 || strlen(nombre) == 0)
    {
        printf("Error: Datos incompletos en el archivo %s\n", id);
        fclose(f);
        return NULL;
    }

    printf("%s %s %d %d\n", id, nombre, victoria, puntuacion);
    fclose(f);

    Partida *partida = malloc(sizeof(Partida));
    if (!partida)
    {
        printf("Error: No se pudo asignar memoria para la partida\n");
        stack_destroy(pila_historial);
        return NULL;
    }
    
    strcpy(partida->id, id);
    partida->historial = pila_historial;
    partida->jugadores = NULL;  // Not needed for history display
    partida->mensajesEstado = NULL;  // Not needed for history display
    partida->puntaje = puntuacion;
    partida->archivo_partida = NULL;  // Not needed for history display

    return partida;
}

int cargarHistorial(Map *partidas)
{
    FILE *list_file = fopen("data/list.txt", "r");
    if (!list_file)
    {
        printf("Error: No se pudo abrir el archivo de lista de partidas\n");
        return 1;
    }


    char linea[256];
    int loaded_count = 0;
    while (fgets(linea, sizeof(linea), list_file))
    {
        Partida *partida = leerPartida(linea);
        if (partida == NULL)
        {
            printf("Error: No se pudo leer una partida del archivo\n");
            continue; // Continue with next line instead of returning error
        }

        map_insert(partidas, partida->id, partida);
        loaded_count++;
    }

    fclose(list_file);

    printf("---\n");
    fflush(stdout);
    
    if (loaded_count == 0)
    {
        printf("Advertencia: No se cargaron partidas del historial\n");
    }
    
    return 0; // Return success even if some entries failed
}

// Función para comparar dos partidas por su ID
// Devuelve 1 si son iguales, 0 si son diferentes
int partidas_iguales(void *a, void *b)
{
    Partida *partida_a = (Partida *)a;
    Partida *partida_b = (Partida *)b;

    return strcmp(partida_a->id, partida_b->id) == 0;
}

void imprimirHistorial(Partida *partida)
{
    // Check for null pointers
    if (!partida || !partida->historial)
    {
        printf("Error: Partida o historial no válido\n");
        return;
    }

    Stack *pila_historial = partida->historial;
    Stack *aux = stack_create();
    
    if (!aux)
    {
        printf("Error: No se pudo crear la pila auxiliar\n");
        return;
    }

    // Print movements in reverse order (LIFO)
    while (!empty(pila_historial))
    {
        Movimiento *movimiento = (Movimiento *)pop(pila_historial);
        if (movimiento)
        {
            if (movimiento->TypeMov == 4)
                printf("%d %d %d %d\n", movimiento->TypeMov, movimiento->CoorX, movimiento->CoorY, movimiento->idJugador);
            else if (movimiento->TypeMov == 5)
            {
                int id_objeto = movimiento->parametros_adicionales[0];
                printf("%d %d %d %d", movimiento->TypeMov, id_objeto, movimiento->CoorX, movimiento->CoorY);
                for (int i = 1; i < movimiento->n_parametros_adicionales; i++)
                    printf(" %d", movimiento->parametros_adicionales[i]);
                printf(" %d\n", movimiento->idJugador);
            }
            stack_push(aux, movimiento);
        }
    }

    // Restore the original stack
    while (!empty(aux))
    {
        Movimiento *movimiento = (Movimiento *)pop(aux);
        if (movimiento)
        {
            stack_push(pila_historial, movimiento);
        }
    }

    // Clean up auxiliary stack
    stack_destroy(aux);
}

int iniciarHistorial()
{
    Map *partidas = map_create(partidas_iguales);
    if (!partidas)
    {
        printf("Error: No se pudo crear el mapa de partidas\n");
        return 1;
    }

    if (cargarHistorial(partidas) == 1)
    {
        printf("Error: No se pudo cargar el historial\n");
        return 1;
    }

    char buffer[256];
    while(fgets(buffer, sizeof(buffer), stdin))
    {
        // Remove newline character
        size_t len = strlen(buffer);
        if (len > 0 && buffer[len - 1] == '\n')
        {
            buffer[len - 1] = '\0';
            len--;
        }
        
        if (strcmp(buffer, "exit") == 0)
            break;

        if (len == 0)
            continue;

        char id[256];
        strncpy(id, buffer, sizeof(id) - 1);
        id[sizeof(id) - 1] = '\0';  // Ensure null termination
        
        Partida *partida = map_search(partidas, id);
        if (partida == NULL)
        {
            printf("Error: Partida no encontrada\n");
            continue;
        }

        imprimirHistorial(partida);
        printf("---\n");
        fflush(stdout);
    }

    // Clean up map and its contents
    // Note: This would require implementing map_destroy if it doesn't exist
    // For now, we'll just return without cleaning up to avoid crashes
    
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
        return iniciarHistorial();

    // main.exe ayuda
    if (strcmp(args[1], "ayuda") == 0)
        return mostrarAyuda();

    printf("Error: Acción desconocida '%s'\n", args[1]);
    mostrarAyuda();

    return 1;
}
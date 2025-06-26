# ByteWave
---
## Embárcate en la batalla definitiva en ByteWave!

¿Estás listo para sumergirte en una guerra digital donde la lógica es tu única arma? ByteWave es un juego táctico por turnos que mezcla estrategia naval con un toque de locura informática. Enfrenta mares de código, enemigos invisibles y una narrativa tan absurda como épica.

### ¿Qué te espera en ByteWave?
Tú eres la última esperanza:
El grupo *Ensalada César* ha sido atrapado en una dimensión de datos corruptos y tú eres quien debe guiarlos. Cada disparo cuenta, cada decisión puede cambiar el rumbo de la batalla.

Guerra digital estratégica:
Enfréntate a la flota espectral de *Arturo Prat* en partidas de estilo Battleship con una vuelta de tuerca: deberás usar lógica, memoria y visión espacial para encontrar y destruir buques escondidos entre bits.

Objetos especiales:
Desbloquea y usa bombas, torpedos, catalejos y cañones para mejorar tu puntería y superar a los marines fantasmas que amenazan con formatear tu existencia.

¿Tienes lo que se necesita para decodificar el misterio, liderar al escuadrón y regresar al mundo real?
**ByteWave** no es solo un juego, es una misión desesperada por la supervivencia digital.

¿Te atreves a enfrentarlo?

---
## Cómo compilar y ejecutar

Este sistema ha sido desarrollado en lenguaje C, con una interfaz grafica en Python y puede ejecutarse fácilmente utilizando **Visual Studio Code** junto con una extensión para C/C++, como **C/C++ Extension Pack** de Microsoft. Para comenzar a trabajar con el sistema en tu equipo local, sigue estos pasos:
---
### Requisitos previos:

- Tener instalado [Visual Studio Code](https://code.visualstudio.com/).
- Instalar la extensión **C/C++** (Microsoft).
- Tener instalado un compilador de C (como **gcc**). Si estás en Windows, se recomienda instalar [MinGW](https://www.mingw-w64.org/) o utilizar el entorno [WSL](https://learn.microsoft.com/en-us/windows/wsl/).

- Tener instalado [Python](https://www.python.org/).
- Instalar la extensión **Python**
- Ejecutar el siguiente comando en la consola para importar **pygame**
  ```
  $ pip install pygame
  ```

---
### Pasos para compilar y ejecutar:

- Descarga y descomprime el archivo .zip en una carpeta de tu elección.
- Abre el proyecto en Visual Studio Code
- Inicia Visual Studio Code.
    Selecciona **Archivo > Abrir carpeta...** y elige la carpeta donde descomprimiste el proyecto.
- Compila el código
    Abre el archivo principal (**main.c**).
    Abre la terminal integrada (**Terminal > Nueva terminal**).
    En la terminal, ejecuta el programa con el siguiente comando:
        ```
        python game.py
        ```
---
## Funcionalidades

### Funcionando correctamente:

- Menú Principal.
- Historial de Partidas.
- Jugabilidad General.
- Funcionalidad de los Objetos.
- Funcionalidad General de la Interfaz.
- Funcionalidad de Victoria y Derrota.
- Funcionalidad del Bot Automatizado.

### Problemas conocidos:

- Seleccionar más de un objeto puede generar desfase a la hora de ejecutar un disparo.

### A mejorar:

- 

## Diseño del sistema y estructura de datos



## Ejemplo de uso

**1) Menú Principal**

![MenuImage](imageReadme/Menu)

Dentro de este menú podemos encontrar dos botones en el centro, uno que nos lleva hasta el registro de *historial* y otro que nos lleva a la partida (*jugar*)

**2) Historial**

![HistorialImage](imageReadme/Historial)

Dentro de este apartado podemos encontrar (en caso de haber jugado antes) la lista de partidas junto a sus respectivos puntajes.

**3) Jugar**

![ImageLore](imageReadme/Lore)

Antes de empezar a posicionar nuestros barcos vemos la historia del juego en el que nos sometemos.

**3.1) Seleccion de Barcos**

![ImageBoatSelection](ImageReadme/Boats)

Dentro de este apartado podemos seleccionar las posiciones de los barcos, rotando sus posiciones con la tecla *"r"*. Tambien podemos elegir la cantidad de objetos que queremos.

**Consideracion Importante**: El bot tendrá la misma cantidad de botes que el jugador.

**3.2) Dentro de la partida**

![imageNotSelection](ImageReadme/notSelectionTable)

Dentro de esta pantalla podemos observar la cantidad de objetos que poseemos, nuestro tablero arriba a la izquierda y en grande el tablero del bot. Podemos seleccionar casillas con el mouse y confirmar el disparo con la tecla *espacio* o con el boton *"Terminar Turno"*.

![ImageSelection](ImageReadme/SelectionTable)

**3.3) Objetos**

Para usar un objeto basta con seleccionarlos con el mouse, de esta forma al pasar el raton por encima de el objeto, el juego mostrará un cuadro de texto explicando el funcionamiento de el objeto.

![ImageObjectExample](ImageReadme/ObjectExample)

*Objetos Disponibles: Bomba, Catalejo, Torpedo.*

**4) Definicion de partida**

Al concluir la partida podremos encontrar distintas pantallas de finalización, dependiendo de el resultado de la partida, junto con dos botones, uno que nos lleva al *menú principal* y otro que nos propone *jugar de nuevo*.

![ImageExampleFinish](ImageReadme/ExampleFinished)

## Contribuciones
---
### Anais Diaz
- 
---
### Cristian Gallardo
-
---
### Daniel Gajardo
-
---
### Matías Salas
- 
---

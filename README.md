# Dashboard de Análisis de Estrategias

Este proyecto contiene un dashboard interactivo construido con Dash (Python) para visualizar y analizar datos de estrategias de trading.

## Cómo Empezar

Sigue estas instrucciones para ejecutar el dashboard en tu máquina local.

### Prerrequisitos

*   Python 3.6 o superior
*   pip (manejador de paquetes de Python)

### Instalación

1.  **Clona el repositorio (si aplica):**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Instala las dependencias:**
    Crea un entorno virtual (recomendado) y luego instala los paquetes necesarios que se encuentran en `requirements.txt`.
    ```bash
    # Crea y activa un entorno virtual (opcional pero recomendado)
    python3 -m venv venv
    source venv/bin/activate  # En Windows usa `venv\Scripts\activate`

    # Instala las dependencias
    pip install -r requirements.txt
    ```

### Ejecutar la Aplicación

Una vez que las dependencias estén instaladas, puedes iniciar el dashboard con el siguiente comando desde la raíz del proyecto:

```bash
python3 src/app.py
```

Después de ejecutar el comando, verás un mensaje en tu terminal similar a este:

```
Dash is running on http://127.0.0.1:8050/
```

Abre tu navegador web y ve a la dirección **http://127.0.0.1:8050/** para ver y utilizar el dashboard.

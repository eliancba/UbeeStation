# UBEEstation

**Sistema de despacho y gestión operativa para remiserías.**

UBEEstation es una herramienta diseñada para agilizar el despacho de viajes, el control de la flota y el arqueo de caja en remiserías, operando de manera rápida y sin ventanas emergentes molestas.

## Características

- 🚖 **Gestión de Flota:** Control de choferes, móviles y estados (Libre / En viaje).
- ⚡ **Despacho Rápido:** Creación de viajes con un solo clic y gestión de cola de pendientes.
- 📊 **Panel de Insights:** Estadísticas en tiempo real del turno (Efectivo, Transferencias, Fiados, Neto Caja).
- 📜 **Historial Permanente:** Registro inmutable de todos los viajes finalizados y cancelados.
- 💾 **Backups Locales:** Copias de seguridad de la base de datos con un clic.

## Requisitos Previos

Asegúrate de tener instalado **Python 3.8** o superior en tu computadora. Puedes descargarlo desde [python.org](https://www.python.org/downloads/). 
*(Durante la instalación, asegúrate de marcar la casilla **"Add Python to PATH"**).*

## Instalación

1. Descarga o clona este repositorio en tu computadora.
2. Abre una terminal (o consola de comandos) en la carpeta del proyecto.
3. Instala las dependencias necesarias ejecutando:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

Para iniciar el sistema, simplemente haz doble clic en el archivo `run.bat` (en Windows), o ejecuta el siguiente comando en la terminal:

```bash
python main.py
```

### Primeros pasos recomendados:
1. Ve a la sección **Choferes** y agrega tus móviles.
2. En la barra lateral, haz clic en el `+` junto a "Operador..." para agregar tu nombre.
3. Ve a **Despacho** y comienza a cargar viajes.

---
*Desarrollado para agilizar tu remisería las 24 horas.*

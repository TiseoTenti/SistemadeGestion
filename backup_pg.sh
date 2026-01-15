#!/bin/bash

# -------------------------------
# Configuración
# -------------------------------
# Carpeta donde se guardarán los backups
BACKUP_DIR="./backups"

# Número de backups a conservar
MAX_BACKUPS=7

# Usuario de Postgres (de tu .env)
POSTGRES_USER=${POSTGRES_USER:-inventario_user}

# Contenedor de Postgres (de tu docker-compose)
DB_CONTAINER=${DB_CONTAINER:-inventario_db}

# -------------------------------
# Crear carpeta de backups si no existe
# -------------------------------
mkdir -p "$BACKUP_DIR"

# -------------------------------
# Nombre del backup con timestamp
# -------------------------------
TIMESTAMP=$(date +"%F_%H-%M-%S")
FILENAME="backup_$TIMESTAMP.sql"
FULL_PATH="$BACKUP_DIR/$FILENAME"

echo "🟢 Iniciando backup: $FULL_PATH"

# -------------------------------
# Ejecutar backup
# -------------------------------
if docker exec -t "$DB_CONTAINER" pg_dumpall -c -U "$POSTGRES_USER" > "$FULL_PATH"; then
    echo "✅ Backup completado correctamente: $FILENAME"
else
    echo "❌ Error: no se pudo generar el backup"
    exit 1
fi

# -------------------------------
# Limitar número de backups
# -------------------------------
echo "🟢 Eliminando backups antiguos, manteniendo los últimos $MAX_BACKUPS..."
cd "$BACKUP_DIR" || exit
BACKUPS_TO_DELETE=$(ls -1t | tail -n +$((MAX_BACKUPS + 1)))
if [ ! -z "$BACKUPS_TO_DELETE" ]; then
    echo "$BACKUPS_TO_DELETE" | xargs rm -f
    echo "✅ Backups antiguos eliminados"
else
    echo "⚡ No hay backups antiguos para eliminar"
fi

echo "🟢 Backup finalizado correctamente"

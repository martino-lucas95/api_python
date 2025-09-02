#!/bin/bash

# Script para cambiar el tráfico entre Blue y Green en el deployment
# Uso: ./switch-traffic.sh [blue|green]

NAMESPACE="api-notes"
SERVICE_NAME="api-notes"

if [ $# -eq 0 ]; then
    echo "Error: Debe especificar el entorno (blue o green)"
    echo "Uso: $0 [blue|green]"
    echo ""
    echo "Ejemplos:"
    echo "  $0 blue   # Dirigir tráfico de producción a Blue (v2.0.0)"
    echo "  $0 green  # Dirigir tráfico de producción a Green (v3.0.0)"
    exit 1
fi

TARGET_ENV=$1

if [ "$TARGET_ENV" != "blue" ] && [ "$TARGET_ENV" != "green" ]; then
    echo "Error: El entorno debe ser 'blue' o 'green'"
    exit 1
fi

echo "🚀 Cambiando tráfico de producción a: $TARGET_ENV"
echo ""

# Obtener estado actual
CURRENT_VERSION=$(kubectl get service $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.selector.version}' 2>/dev/null)
if [ -z "$CURRENT_VERSION" ]; then
    echo "⚠️  No se pudo obtener la versión actual del servicio"
else
    echo "📍 Versión actual: $CURRENT_VERSION"
fi

# Verificar que el deployment objetivo existe y está listo
echo "🔍 Verificando estado del deployment $TARGET_ENV..."
READY_REPLICAS=$(kubectl get deployment api-notes-$TARGET_ENV -n $NAMESPACE -o jsonpath='{.status.readyReplicas}' 2>/dev/null)
DESIRED_REPLICAS=$(kubectl get deployment api-notes-$TARGET_ENV -n $NAMESPACE -o jsonpath='{.spec.replicas}' 2>/dev/null)

if [ -z "$READY_REPLICAS" ] || [ -z "$DESIRED_REPLICAS" ]; then
    echo "❌ Error: El deployment api-notes-$TARGET_ENV no existe o no está disponible"
    exit 1
fi

if [ "$READY_REPLICAS" != "$DESIRED_REPLICAS" ]; then
    echo "⚠️  Advertencia: El deployment $TARGET_ENV no está completamente listo"
    echo "   Réplicas listas: $READY_REPLICAS/$DESIRED_REPLICAS"
    echo "   ¿Continuar de todos modos? (y/N)"
    read -r CONTINUE
    if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
        echo "❌ Operación cancelada"
        exit 1
    fi
else
    echo "✅ Deployment $TARGET_ENV está listo ($READY_REPLICAS/$DESIRED_REPLICAS réplicas)"
fi

# Cambiar el selector del servicio
echo ""
echo "🔄 Actualizando servicio para dirigir tráfico a $TARGET_ENV..."
kubectl patch service $SERVICE_NAME -n $NAMESPACE -p '{"spec":{"selector":{"version":"'$TARGET_ENV'"}}}'

if [ $? -eq 0 ]; then
    echo "✅ Tráfico cambiado exitosamente a: $TARGET_ENV"
    
    # Verificar el cambio
    NEW_VERSION=$(kubectl get service $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.selector.version}')
    echo "📍 Nueva versión activa: $NEW_VERSION"
    
    # Mostrar información de versión
    if [ "$TARGET_ENV" == "blue" ]; then
        echo "📦 Versión: v2.0.0 (Stable)"
        echo "🎯 Características: Crear, Listar, Eliminar notas"
    else
        echo "📦 Versión: v3.0.0 (New)"
        echo "🎯 Características: Crear, Listar, Eliminar notas + Endpoint /version"
    fi
    
    echo ""
    echo "🧪 Para probar el cambio:"
    echo "   kubectl port-forward -n $NAMESPACE service/$SERVICE_NAME 8080:80"
    echo "   curl http://localhost:8080/"
    echo "   curl http://localhost:8080/version"
    
else
    echo "❌ Error al cambiar el tráfico"
    exit 1
fi

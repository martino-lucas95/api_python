# API de Notas - Sistema de Versiones

Este proyecto contiene una API RESTful en Python para guardar y gestionar notas, implementada con Flask. El proyecto está diseñado para demostrar diferentes estrategias de deployment en Kubernetes.

## Versiones

### v1.0.0 - API Básica ✅
**Estado:** Implementada

API básica con funcionalidad esencial para gestión de notas.

#### Endpoints

- **GET /** - Mensaje indicando que el API está activo
  - Respuesta: `{"message": "API de Notas v1.0.0 está activo"}`

- **POST /add/{title}** - Agregar una nota con un título
  - Parámetros:
    - `title` (path): Título de la nota
    - Body JSON: `{"note": "contenido de la nota"}`
  - Respuesta: `{"message": "Nota '{title}' agregada exitosamente"}`

- **GET /list** - Lista todas las notas creadas
  - Respuesta: Array de notas `[{"title": "...", "note": "..."}]`

#### Características v1.0.0
- ✅ 3 endpoints básicos funcionales
- ✅ Persistencia en volumen mediante archivo JSON
- ✅ Documentación Swagger disponible en `/apidocs/`
- ✅ Health check en `/healthz` para Kubernetes probes
- ✅ Manejo de errores básico

#### Uso

**Agregar una nota:**
```bash
curl -X POST "http://localhost:5001/add/Mi%20Primera%20Nota" \
  -H "Content-Type: application/json" \
  -d '{"note": "Este es el contenido de mi primera nota"}'
```

**Listar notas:**
```bash
curl http://localhost:5001/list
```

**Verificar que el API está activo:**
```bash
curl http://localhost:5001/
```

#### Deployment

**Construcción de imagen:**
```bash
docker build -t notes-api:v1.0.0 .
```

**Ejecución local:**
```bash
docker run -p 5001:5001 -v notes_data:/data notes-api:v1.0.0
```


### v2.0.0 - Con Funcionalidad de Eliminación ✅
**Estado:** Implementada y desplegada

Extensión de v1.0.0 agregando capacidad de eliminar notas.

#### Nuevas características v2.0.0
- ✅ **DELETE /delete/{title}** - Eliminar una nota por título
- ✅ Deployment mediante RollingUpdate
- ✅ Mantenimiento de compatibilidad con v1.0.0
- ✅ Funciones auxiliares para manejo del archivo de notas
- ✅ Volumen persistente configurado

#### Uso v2.0.0

**Eliminar una nota:**
```bash
curl -X DELETE "http://localhost:5001/delete/Mi%20Primera%20Nota"
```

### v3.0.0 - Blue-Green Deployment ✅
**Estado:** Implementada y lista para blue-green

Versión basada en v2.0.0 preparada para blue-green deployment.

#### Nuevas características v3.0.0
- ✅ **GET /version** - Endpoint de información de versión y entorno
- ✅ Detección automática de entorno (Blue/Green)
- ✅ Configuración para blue-green deployment
- ✅ Script automatizado para cambio de tráfico
- ✅ Variables de entorno para identificación de deployment

#### Uso v3.0.0

**Información de versión:**
```bash
curl http://localhost:5001/version
# Respuesta:
# {
#   "version": "v3.0.0",
#   "environment": "blue|green",
#   "hostname": "pod-hostname",
#   "deployment_type": "blue-green",
#   "features": ["create", "read", "delete", "version-switching"],
#   "status": "ready"
# }
```

## Arquitectura

### Persistencia
- Las notas se guardan en un archivo JSON línea por línea
- Utiliza volumen persistente montado en `/data/notes.json`
- Configuración via variable de entorno `NOTES_PATH`

### Infraestructura
- **Base:** Python 3.12 Alpine
- **Framework:** Flask + Flasgger (Swagger)
- **Puerto:** 5001
- **Probes:** Health check en `/healthz`

## Deployment en Kubernetes

### Deployment Standard (RollingUpdate)
El proyecto incluye configuración para deployment estándar en `api-deployment.yaml`:

- **Namespace:** `api-notes`
- **ConfigMap:** Configuración de `NOTES_PATH`
- **Deployment:** 3 réplicas con RollingUpdate strategy
- **Service:** ClusterIP en puerto 80 → 5001

```bash
kubectl apply -f api-deployment.yaml
```

### Blue-Green Deployment
Para blue-green deployment, usar `blue-green-deployment.yaml`:

#### Configuración Blue-Green
- **Blue Environment:** v2.0.0 (Estable)
- **Green Environment:** v3.0.0 (Nueva versión)
- **3 Servicios:**
  - `api-notes`: Servicio de producción (configurable)
  - `api-notes-blue`: Acceso directo al entorno Blue
  - `api-notes-green`: Acceso directo al entorno Green

#### Despliegue Blue-Green
```bash
# Aplicar configuración blue-green
kubectl apply -f blue-green-deployment.yaml

# Verificar deployments
kubectl get pods -n api-notes

# Cambiar tráfico a Green (v3.0.0)
./switch-traffic.sh green

# Cambiar tráfico de vuelta a Blue (v2.0.0)
./switch-traffic.sh blue
```

#### Testing de Entornos
```bash
# Probar producción (depende del entorno activo)
kubectl port-forward -n api-notes service/api-notes 8080:80
curl http://localhost:8080/version

# Probar Blue directamente
kubectl port-forward -n api-notes service/api-notes-blue 8081:80
curl http://localhost:8081/version

# Probar Green directamente  
kubectl port-forward -n api-notes service/api-notes-green 8082:80
curl http://localhost:8082/version
```

## Desarrollo

### Requisitos
- Python 3.12+
- Flask
- Flasgger

### Instalación local
```bash
pip install -r requirements.txt
python main.py
```

### Testing de endpoints
La documentación interactiva está disponible en: `http://localhost:5001/apidocs/`

## Archivos del Proyecto

### Código Fuente
- `main.py` - Código principal de la API (todas las versiones)
- `requirements.txt` - Dependencias de Python
- `Dockerfile` - Configuración para construcción de imágenes

### Deployment Files
- `api-deployment.yaml` - Deployment estándar con RollingUpdate
- `blue-green-deployment.yaml` - Configuración blue-green deployment
- `switch-traffic.sh` - Script para cambiar tráfico entre Blue/Green

### Imágenes Docker Generadas
- `notes-api:v1.0.0` - API básica (3 endpoints)
- `notes-api:v2.0.0` - API con eliminación (4 endpoints)
- `notes-api:v3.0.0` - API preparada para blue-green (5 endpoints)

## Resumen del Proceso Implementado

✅ **Paso 1:** Limpieza de imágenes existentes en minikube  
✅ **Paso 2:** Implementación de v1.0.0 - API básica con 3 endpoints  
✅ **Paso 3:** Construcción y carga de imagen v1.0.0  
✅ **Paso 4:** Implementación de v2.0.0 - Agregado endpoint DELETE  
✅ **Paso 5:** Deployment v2.0.0 usando RollingUpdate strategy  
✅ **Paso 6:** Implementación de v3.0.0 - Preparación para blue-green  
✅ **Paso 7:** Configuración completa de blue-green deployment  
✅ **Paso 8:** Script automatizado para switching de tráfico  

---

**✨ Proyecto completado exitosamente**  
*Tres versiones implementadas con diferentes estrategias de deployment*

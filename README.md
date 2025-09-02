# Notes API - DevOps Demo Completo

Demostración completa de herramientas DevOps con API de notas que incluye:
- **Versionado de API** (v1 y v2 compatibles)
- **Rolling Updates** sin downtime
- **Blue/Green Deployment** con rollback automático
- **Frontend** para visualización de errores
- **Health checks** y monitoring
- **Documentación completa** de cambios y procedimientos

### Endpoints

- **v0 (legacy)**:
  - `GET /list` — lista notas (esquema `{title, note}`)
  - `POST /add/<title>` — crea nota con cuerpo `{note}`
- **v1**:
  - `GET /api/v1/notes` — lista notas (esquema `{title, note}`)
  - `POST /api/v1/notes` — crea nota `{title, note}`
- **v2**:
  - `GET /api/v2/notes` — lista notas (esquema enriquecido con metadatos)
  - `POST /api/v2/notes` — crea nota `{title, content, [tags], [archived]}`
  - `PATCH /api/v2/notes/{id}` — edita nota (¡CON BUG en v1.2.0!)
- **Frontend**:
  - `GET /ui` — interfaz web simple para probar API
- **Health**:
  - `GET /healthz` — para probes de K8s

### Versionado de la imagen

- `notes-api:v1.0.0` — versión inicial sin probes ni rutas versionadas
- `notes-api:v1.1.0` — añade `/healthz`, rutas `/api/v1` y `/api/v2`
- `notes-api:v1.2.0` — añade frontend `/ui` y `PATCH` (con bug intencional)
- `notes-api:v1.2.1` — frontend moderno separado en `static/index.html`
- `notes-api:v2.0.0` — versión final con frontend moderno, API versionada y health checks

### Rolling Update en Kubernetes

Archivo: `api-deployment.yaml`

- **Estrategia**: `RollingUpdate` con `maxSurge: 1`, `maxUnavailable: 0`
- **Probes**: `readinessProbe` y `livenessProbe` en `/healthz`
- **Réplicas**: `3`

#### Comandos útiles

```bash
# Desplegar/actualizar manifiestos
kubectl apply -f api-deployment.yaml

# Ver estado del rollout
kubectl rollout status deployment/api-notes -n api-notes

# Actualizar la imagen (ejemplo a v1.1.0)
kubectl -n api-notes set image deployment/api-notes api-notes=notes-api:v1.1.0 --record

# Ver historial de rollouts
kubectl rollout history deployment/api-notes -n api-notes

# Hacer rollback
kubectl rollout undo deployment/api-notes -n api-notes
```

### Blue/Green Deployment

Archivo: `blue-green-deployment.yaml`

```bash
# 1. Deploy blue/green environments
kubectl apply -f blue-green-deployment.yaml

# 2. Build new version with bug
minikube image build -t notes-api:v1.2.0 .

# 3. Test green environment before switching
kubectl port-forward -n api-notes service/api-notes-green 8082:80 &

# 4. Switch traffic to green (CAREFUL - has bug!)
kubectl patch service api-notes -n api-notes -p '{"spec":{"selector":{"version":"green"}}}'

# 5. If error detected, immediate rollback to blue
kubectl patch service api-notes -n api-notes -p '{"spec":{"selector":{"version":"blue"}}}'

# 6. Clean up green deployment if needed
kubectl delete deployment api-notes-green -n api-notes
```

### Build local y ejecución

```bash
# Build
docker build -t notes-api:v1.1.0 .
# Run
docker run --rm -p 5001:5001 -e NOTES_PATH=/data/notes.json -v $(pwd):/data notes-api:v1.1.0
```

### Resumen de lo Implementado

#### 🚀 **Estrategias de Deployment**
1. **Rolling Update**: Actualización gradual sin downtime
2. **Blue/Green Deployment**: Cambio instantáneo con rollback inmediato

#### 🔧 **Versionado de API**
- **Compatibilidad hacia atrás**: v0 legacy + v1 + v2
- **Esquemas progresivos**: v1 simple, v2 con metadatos enriquecidos
- **Misma base de datos**: transformaciones en tiempo real

#### 🎯 **Herramientas DevOps Demostradas**
- ✅ **Kubernetes**: Rolling updates, probes, services
- ✅ **Docker**: Multi-stage builds, image versioning
- ✅ **Minikube**: Local development environment
- ✅ **Health Checks**: Readiness/liveness probes
- ✅ **Service Mesh**: Blue/green traffic switching
- ✅ **Error Simulation**: Bug intencional + rollback
- ✅ **Frontend Integration**: Visualización de errores

#### 📋 **Flujo de Demostración Ejecutado**

1. **Setup inicial**: API v1.0.0 en K8s con Minikube
2. **Rolling update**: v1.0.0 → v1.1.0 → v2.0.0 (health checks + versionado + frontend)
3. **Blue/green setup**: Despliegue paralelo v2.0.0 (blue) y v3.0.0 (green con API v3)
4. **Ambientes paralelos**: 6 pods corriendo (3 blue + 3 green)
5. **Testing green**: Service fijo 8082 para probar v3.0.0 antes del switch
6. **Traffic switch**: Service principal 8081 cambia de blue a green instantáneamente
7. **Functional testing**: API v3 (PUT/DELETE) disponible solo en green
8. **Emergency rollback**: Vuelta inmediata a blue con un comando patch
9. **Validation**: Zero downtime confirmado, switch funcional demostrado

### Changelog Detallado

#### v3.0.0 (🚀 **GREEN DEPLOYMENT - API v3**)
- ➕ **API v3 completa**: Endpoints PUT/DELETE para edición/eliminación de notas
- ➕ **GET `/api/v3/notes`**: Lista con metadata enhanced y features array
- ➕ **POST `/api/v3/notes`**: Crear con validación enhanced (título 1-100 chars)
- ➕ **PUT `/api/v3/notes/{id}`**: Editar nota completa (NEW FEATURE)
- ➕ **DELETE `/api/v3/notes/{id}`**: Eliminar nota (NEW FEATURE)
- 🎯 **Blue/Green ready**: Versión green para deployment paralelo con blue v2.0.0

#### v2.0.0 (🔧 **BLUE DEPLOYMENT - STABLE**)
- ✨ **Frontend consolidado**: UI moderna en `static/index.html`
- ✨ **API v1/v2 estable**: Compatibilidad completa hacia atrás
- ✨ **Health monitoring**: Endpoints `/version` y `/healthz` para observabilidad
- 🎯 **Blue/Green ready**: Versión blue para deployment paralelo

#### v1.2.2 (🎯 **INDICADORES VISUALES**)
- 🎯 **Detección automática**: Endpoint `/version` detecta environment (blue/green)
- 🎯 **Badge dinámico**: Color azul para blue, verde para green
- 🎯 **Info detallada**: Hostname, versión, estado del bug
- 🎯 **Alerts contextuales**: Mensajes diferentes según environment
- 🔧 **Variables de entorno**: `DEPLOYMENT_ENV` para identificación

#### v1.2.1 (✨ **FRONTEND MEJORADO**)
- ✨ **Frontend moderno**: Separado en `static/index.html` con diseño responsive
- ✨ **UI/UX mejorada**: CSS grid, animaciones, alerts, loading states
- ✨ **Arquitectura limpia**: Frontend separado del backend Flask
- 🔧 **Mantiene bug PATCH**: Para demostración de rollback

#### v1.2.0 (🚨 **CON BUG INTENCIONAL**)
- ➕ **Frontend `/ui`**: Interfaz web completa para crear/editar notas
- ➕ **`PATCH /api/v2/notes/{id}`**: Endpoint de edición (SIEMPRE devuelve 500)
- ➕ **`blue-green-deployment.yaml`**: Configuración para deployment paralelo
- 🎯 **Propósito**: Simular error de producción para rollback demo

#### v1.1.0 (✅ **ESTABLE**)
- ➕ **Health endpoint `/healthz`**: Para readiness/liveness probes
- ➕ **API versionada**: Rutas `/api/v1/notes` y `/api/v2/notes`
- ➕ **Metadata v2**: `id`, `created_at`, `updated_at`, `tags[]`, `archived`
- ➕ **Rolling update config**: `maxSurge: 1`, `maxUnavailable: 0`
- 🔧 **`api-deployment.yaml`**: Estrategia RollingUpdate + probes

#### v1.0.0 (📦 **INICIAL**)
- 🎯 **API base**: `GET /list`, `POST /add/<title>`
- 🎯 **Storage**: Archivo JSON línea por línea
- 🎯 **Swagger docs**: `/apidocs/` con Flasgger

### Blue/Green Deployment - Pasos Ejecutados

#### Preparación del Ambiente
```bash
# 1. Detener deployment original para evitar conflictos
kubectl scale deployment api-notes --replicas=0 -n api-notes

# 2. Construir imágenes diferenciadas
minikube image build -t notes-api:v2.0.0 .  # Blue (base)
minikube image build -t notes-api:v3.0.0 .  # Green (con API v3)

# 3. Deploy ambientes paralelos
kubectl apply -f blue-green-deployment.yaml

# 4. Port-forward a ambos servicios
kubectl port-forward -n api-notes service/api-notes 8081:80 &      # Switcheable
kubectl port-forward -n api-notes service/api-notes-green 8082:80 & # Fijo green
```

#### Demostración de Switch
```bash
# 5. Verificar estado inicial (BLUE)
curl http://localhost:8081/version
kubectl get pods -n api-notes  # 3 blue + 3 green

# 6. Crear datos en BLUE
curl -X POST http://localhost:8081/api/v2/notes \
  -H "Content-Type: application/json" \
  -d '{"title":"Nota en BLUE","content":"Creada en ambiente blue"}'

# 7. Switch instantáneo a GREEN
kubectl patch service api-notes -n api-notes -p '{"spec":{"selector":{"version":"green"}}}'
curl http://localhost:8081/version  # Ahora environment: "green"

# 8. Crear datos en GREEN
curl -X POST http://localhost:8081/api/v2/notes \
  -H "Content-Type: application/json" \
  -d '{"title":"Nota en GREEN","content":"Creada en ambiente green"}'

# 9. Rollback instantáneo a BLUE
kubectl patch service api-notes -n api-notes -p '{"spec":{"selector":{"version":"blue"}}}'

# 10. Verificar diferencias de funcionalidad
curl http://localhost:8081/api/v3/notes  # Blue (v2.0.0)
curl http://localhost:8082/api/v3/notes  # Green (v3.0.0)
```

#### Características Demostradas
✅ **Switch instantáneo**: Cambio de tráfico sin downtime  
✅ **Ambientes paralelos**: 6 pods corriendo simultáneamente (3 blue + 3 green)  
✅ **Rollback rápido**: Vuelta a versión anterior en segundos  
✅ **Testing seguro**: Service green fijo (8082) para probar antes del switch  
✅ **Zero downtime**: Sin interrupciones para usuarios  
✅ **Control granular**: Selector de service controla el tráfico  

#### Cleanup
```bash
kubectl delete deployment api-notes-blue api-notes-green -n api-notes
kubectl delete service api-notes-green -n api-notes
kubectl scale deployment api-notes --replicas=3 -n api-notes  # Restaurar original
```

### Archivos del Proyecto

- **`main.py`**: API Flask con versionado, endpoints y bug simulado
- **`static/index.html`**: Frontend moderno separado con CSS responsive
- **`api-deployment.yaml`**: Rolling update deployment
- **`blue-green-deployment.yaml`**: Blue/green deployment paralelo
- **`requirements.txt`**: Dependencies (flask, flasgger)
- **`Dockerfile`**: Container build
- **`README.md`**: Esta documentación completa

### Evidencia de Éxito

#### Rolling Update Demostrado
✅ **Zero-downtime deployment**: Rolling update v1.0.0 → v1.1.0 → v2.0.0 sin interrupciones  
✅ **Health checks funcionando**: Probes de readiness/liveness en todos los deployments  
✅ **Versionado backward-compatible**: v0, v1, v2, v3 API conviven simultáneamente  

#### Blue/Green Deployment Demostrado  
✅ **Switch instantáneo**: Cambio de blue a green sin downtime verificado  
✅ **Ambientes paralelos**: 6 pods corriendo simultáneamente (3 blue + 3 green)  
✅ **Rollback funcional**: Vuelta a versión anterior en < 5 segundos  
✅ **Testing seguro**: Service green fijo para probar antes del switch  
✅ **Control granular**: Selector de service controla el tráfico perfectamente  

#### Funcionalidades Integradas
✅ **Frontend operativo**: Interfaz web moderna en puerto 8081/8082  
✅ **API v3 implementada**: Endpoints PUT/DELETE para edición/eliminación  
✅ **Error simulation**: PATCH endpoint con bug intencional para rollback demo  
✅ **Monitoring endpoints**: `/version`, `/healthz` para observabilidad  
✅ **Documentation completa**: Pasos ejecutados y procedimientos documentados

### Tecnologías Utilizadas

- **Kubernetes**: Orchestration + service mesh
- **Docker**: Containerization
- **Flask**: Python web framework
- **Minikube**: Local K8s cluster
- **Swagger/Flasgger**: API documentation
- **HTML/JavaScript**: Frontend simple
- **YAML**: Infrastructure as Code

Este proyecto demuestra un pipeline DevOps completo con versionado, deployment strategies, error handling y rollback procedures.

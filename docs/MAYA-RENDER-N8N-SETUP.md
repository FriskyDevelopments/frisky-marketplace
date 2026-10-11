# Maya — Brief: conectar Render y n8n a Frisky

Fecha: 2026-10-11. Contexto: Frisky (Grok) no tiene conectores de Render ni n8n activos en esta sesión. Los plugins ya existen en el marketplace `FriskyDevelopments/frisky-marketplace` y solo falta conectar las credenciales.

## 1) Render — plugin `render/`

- **MCP oficial de Render**: `https://mcp.render.com/mcp` (hosted). El plugin ya apunta ahí en `render/kimi.plugin.json`.
- **Credencial**: una **API key** de Render (no client ID / client secret — eso es OAuth de otra cosa; Render usa Bearer token).
  - Render Dashboard → Account Settings → **API Keys** → Create API Key.
  - Conectar el MCP con `Authorization: Bearer <key>` en la UI de conexión del plugin/MCP. **Nunca pegar la key en el chat** — va solo en la configuración de conexión.
- **Flujo estándar**: primero seleccionar el workspace activo, luego listar servicios. El servidor soporta crear web services, static sites, cron jobs, Postgres y Key Value; leer deploys, logs y métricas; reemplazar env vars; SQL de solo lectura en Render Postgres.
- **Límites**: no borra servicios, no dispara deploys manuales, no cambia scaling. SQL solo lectura.
- **Nota de seguridad**: la key tiene alcance amplio en todos los workspaces — crear una dedicada y revocarla al terminar.

## 2) n8n — plugin `n8n-connector/`

- **Endpoint MCP**: `https://n8n.friskydev.com/mcp-server/http` (ya configurado en `n8n-connector/kimi.plugin.json`).
- **Autenticación**: OAuth a nivel de instancia. La primera llamada abre la página de autorización de n8n — iniciar sesión en n8n.friskydev.com y aprobar.
- **Importante**: los workflows que se quieran ejecutar desde el MCP deben estar marcados como **Available in MCP** dentro de n8n.
- Capacidades: buscar y disparar workflows, crear/editar workflows y data tables, gestionar registros de ejecución.

## 3) Make (alternativa más fácil, si n8n se complica)

- Make tiene conector MCP / webhooks HTTP. Opción A: crear un **webhook** en un escenario de Make que reciba el payload y lo enrute. Opción B: si Make expone MCP, conectar el endpoint igual que n8n. Pedir a Frisky el webhook URL y el secret; se guardan en la config de conexión, no en el chat.

## 4) Lo que NO hacer

- No pedir ni aceptar API keys, client secrets o tokens por voz/chat. Usar links de un solo uso (1Password) o la UI de conexión del plugin.
- No asumir que un conector "existe" sin verificarlo con las herramientas disponibles primero.

## 5) Verificación rápida

- Render: "lista mis servicios de Render" → debe devolver tabla nombre/tipo/estado/último deploy.
- n8n: "busca workflows en n8n" → debe listar los marcados como Available in MCP.
- Si falla con 401/403: regenerar la key (Render) o re-autorizar OAuth (n8n) y reintentar.

## 6) Deploy

- El marketplace ya está en GitHub; no requiere redeploy para que el plugin funcione — solo la conexión de credenciales. Si se necesita desplegar algo en OpenShift, usar el conector OPENSHIP (proyectos, clusters, bases de datos) con el workspace correcto.

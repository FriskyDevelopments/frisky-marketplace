---
name: framer
description: Usa cuando el usuario quiera diseñar, editar, analizar o publicar un sitio web en Framer — leer páginas y estructura del proyecto, crear/editar contenido del CMS, aplicar cambios en el canvas, previsualizar, publicar o desplegar. También para migrar contenido a Framer o auditar un sitio hecho en Framer. El usuario dirá cosas como "edita mi sitio de Framer", "publica la landing en Framer", "actualiza el CMS de Framer", "conecta Framer con mis datos".
---

# Framer (MCP)

Este skill conecta Kimi con **Framer** (framer.com) a través del MCP stdio comunitario `framer-mcp-server` (npm, se lanza con `npx -y framer-mcp-server`). Las herramientas MCP ya vienen declaradas en el plugin; el agente las invoca directamente como cualquier otra herramienta MCP.

## Prerequisitos (configuración previa)

El servidor MCP necesita dos variables de entorno:

1. **`FRAMER_API_KEY`** — clave de la **Framer Server API** (beta abierta, gratuita). Se crea en el editor de Framer: **Site Settings → General → API**. Copia el token completo.
2. **`FRAMER_PROJECT_URL`** — URL del proyecto, con la forma `https://framer.com/projects/<Nombre>--<id>` (está en la barra de direcciones del dashboard de Framer).

Ambas van en el campo `env` del servidor MCP `framer` en `kimi.plugin.json` del plugin. Si llegan vacías al usar el skill:

- Pídele al usuario la **API key** y la **URL del proyecto** (nunca inventarlas ni registrarlas en ningún archivo del workspace ni del historial; trátalas como secreto y no las imprimas completa en la respuesta).
- Una vez proporcionadas, el usuario debe rellenarlas en la configuración del plugin (o reinstalar el plugin con el manifest actualizado); el agente no puede editar la config del MCP en caliente desde la conversación.

**Requisito técnico:** `node` + `npx` disponibles en el PATH (el servidor se descarga solo al primer uso vía `npx -y`).

## Herramientas MCP disponibles

| Herramienta | Para qué |
|---|---|
| `framer_mcp_read_page` | Leer el contenido y la estructura de una página del sitio |
| `framer_mcp_get_page_context` | Obtener contexto del proyecto/página (estructura, rutas, componentes) |
| `framer_mcp_get_collection_items` | Listar/leer items de una colección CMS |
| `framer_mcp_add_collection_items` | Añadir items a una colección CMS |
| `framer_mcp_apply_changes` | Aplicar cambios en el canvas/páginas |
| `framer_mcp_preview` | Generar/obtener una previsualización de los cambios |
| `framer_mcp_publish` | Publicar el sitio (producción) |

## Flujo de trabajo recomendado

1. **Explorar antes de tocar**: usa `framer_mcp_get_page_context` y `framer_mcp_read_page` para entender el sitio. Resume al usuario qué encontraste (estructura, páginas, colecciones) antes de proponer cambios.
2. **Cambios**: aplica con `framer_mcp_apply_changes` y verifica con `framer_mcp_preview` antes de cualquier publicación. Los cambios llevan *undo* por snapshot, pero igualmente confirma con el usuario los cambios de gran alcance.
3. **CMS**: para contenido repetitivo (blog, equipo, productos) usa `framer_mcp_get_collection_items` / `framer_mcp_add_collection_items` en vez de editar páginas a mano.
4. **Publicación**: `framer_mcp_publish` y cualquier despliegue afectan al sitio **en producción, visible para los visitantes**. Antes de llamarla, muestra al usuario exactamente qué se va a publicar y espera su confirmación explícita.

## Guardarraíles

- **Confirmar antes de publicar/desplegar**: `framer_mcp_publish` es una acción de producción. Siempre confirma con el usuario (qué cambios, qué sitio) antes de ejecutarla.
- **Nunca exponer la API key**: no la imprimas en respuestas, no la escribas en archivos del workspace, no la incluyas en URLs.
- **Un proyecto por configuración**: el MCP está ligado al `FRAMER_PROJECT_URL` configurado. Si el usuario quiere trabajar con otro proyecto, necesita cambiar la variable (o instalar una segunda entrada del plugin con otro manifest).
- **Fallback sin MCP**: si el MCP no arranca (node ausente, red, key inválida), se puede automatizar lo mismo con la librería oficial `framer-api` (npm): `connect(projectUrl, apiKey)` → `getProjectInfo()`, `getChangedPaths()`, CRUD de CMS, `publish()`, `deploy(id)`. Usa Bash + un script temporal en el workspace para flujos puntuales, y avisa al usuario de que el MCP no está disponible.
- **Errores de autenticación**: si las herramientas devuelven 401/unauthorized, la `FRAMER_API_KEY` falta, está mal copiada o fue revocada; pide al usuario regenerarla en Site Settings → General → API.

## Limitaciones

- La edición fina del canvas (layouts pixel a pixel, animaciones complejas) la hace mejor la IA de Framer dentro de su editor; este skill brilla en contenido, CMS, auditoría y publicación asistida.
- `framer-mcp-server` es un proyecto comunitario (MIT): si Framer cambia su API interna, alguna herramienta puede dejar de funcionar hasta que se actualice el paquete; en ese caso usa el fallback con `framer-api`.

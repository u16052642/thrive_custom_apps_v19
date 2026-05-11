# ONLYOFFICE Chatter Integration

Addon para Odoo que permite crear documentos OnlyOffice directamente desde el Chatter de cualquier registro.

## Qué hace

- Agrega un botón **"Nuevo"** junto a la actividad del Chatter.
- Permite crear un documento en blanco de OnlyOffice en formato `docx`, `xlsx` o `pptx`.
- Guarda el archivo como un registro `ir.attachment` vinculado al modelo y registro actual.
- Redirige automáticamente al editor OnlyOffice después de crear el documento.
- Funciona en Odoo Community Edition y no depende del app Enterprise `documents.document`.

## Características principales

- Integración nativa con el Chatter de cualquier modelo que implemente `mail.thread`.
- Creación de archivos con nombre validado y protegido contra caracteres inseguros.
- Usa el servicio de OnlyOffice del addon `onlyoffice_odoo` para generar plantillas predeterminadas.
- Interfaz de diálogo OWL para seleccionar formato y título.

## Dependencias

- `mail`
- `onlyoffice_odoo`

## Instalación

1. Copia el addon `onlyoffice_chatter` a tu carpeta de addons de Odoo.
2. Asegúrate de que Odoo pueda encontrar la ruta: agrega el directorio al `addons_path` si es necesario.
3. Reinicia el servidor de Odoo.
4. Actualiza la lista de aplicaciones y encuentra el addon **ONLYOFFICE Chatter Integration**.
5. Instálalo.

## Uso

1. Abre cualquier registro con Chatter habilitado.
2. Haz clic en el botón **Nuevo** que aparece junto a los controles del Chatter.
3. Escribe un título para el documento.
4. Selecciona el formato deseado: Documento (`docx`), Hoja de cálculo (`xlsx`) o Presentación (`pptx`).
5. Haz clic en **Crear**.
6. El documento se crea como un `ir.attachment` y se abre en el editor OnlyOffice.

## Estructura del addon

- `__manifest__.py` — definición del addon y assets.
- `controllers/main.py` — controlador HTTP JSON para crear el archivo y adjuntarlo.
- `static/src/js/chatter_patch.js` — patch del Chatter en la interfaz web.
- `static/src/xml/chatter_patch.xml` — plantilla OWL para el diálogo y el botón.

## Licencia

- `LGPL-3`

## Autor

- Victor Bastías Escobar
- Sitio: https://vicbas.com/addons_odoo.html
- Soporte: contacto@vicbas.com, contacto@vibasertec.com

========================================
 ONLYOFFICE Chatter Integration
========================================

Overview
========

This module adds a **"New"** button to the Chatter of any Odoo record,
allowing users to create blank OnlyOffice documents (DOCX, XLSX, PPTX)
as native ``ir.attachment`` files — without requiring the Enterprise
Documents app.

Works with **Odoo Community Edition**.

Prerequisites
=============

1. **onlyoffice_odoo** module must be installed and configured.
   Available on the `Odoo Apps Store
   <https://apps.thrive.com/apps/modules/19.0/onlyoffice_odoo/>`_.

2. An **ONLYOFFICE Document Server** must be running and accessible
   from the Odoo instance.

3. **Odoo 19.0** (Community or Enterprise).

Installation
============

1. Clone or download this module into your Odoo addons directory.

2. Update the **Apps List** in Odoo (Settings → Activate Developer Mode
   → Update Apps List).

3. Search for **"ONLYOFFICE Chatter"** in the Apps module and click
   **Install**.

Usage
=====

1. Open any record that has a Chatter (e.g. a CRM Lead, Project Task,
   Sale Order, etc.).

2. Click the **"New"** button that appears next to the Chatter action
   buttons.

3. In the dialog, select the document format:

   - **Document** (.docx)
   - **Spreadsheet** (.xlsx)
   - **Presentation** (.pptx)

4. Enter a title for the file.

5. Click **"Create"**.

The document is created as an attachment on the record and opened in
the ONLYOFFICE editor in a new browser tab.

Supported Languages
===================

- English (default)
- Spanish (es)
- French (fr)
- Russian (ru)
- Chinese Simplified (zh_CN)
- Dutch Belgium (nl_BE)

Configuration
=============

No additional configuration is needed beyond what ``onlyoffice_odoo``
requires. The module automatically detects the OnlyOffice Document
Server URL from the ``onlyoffice_odoo`` settings.

License
=======

LGPL-3. See the ``LICENSE`` file for details.

This module depends on ``onlyoffice_odoo`` by José Padilla, licensed
under the MIT License.

Support
=======

For bug reports, feature requests, or questions:

- Email: contacto@vicbas.com
- Website: https://vicbas.com/addons_odoo.html

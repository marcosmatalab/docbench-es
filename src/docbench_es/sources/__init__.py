"""Conectores de plataforma sobre `benchcore.contracts`. Vacío hasta **L15**.

Aquí van `sharepoint`, `onedrive`, `azure_blob`, `s3`, `gcs`, `minio`, `sftp`,
`sql`, `http_api`, `alfresco` y `documentum` (§8 del manual). Son **de dónde se
sacan los bytes en una instalación de cliente**, no adaptadores de entidad.

**Este docstring decía «Lo rellena L3, con el adaptador `boe_xml`», y era falso.**
El manual pone `boe_xml.py` en `entity/` en tres sitios —el árbol de ficheros, el
título de §9.4 (*«`entity.boe` y `entity.boe_xml`»*) y la fila de L3 en §16—.

Lo escribió L0, sobre un módulo que L0 no estaba construyendo, y **sobrevivió
hasta el hito que se lo iba a creer**: el plan de L3 llegó a plantearse si
`boe_xml` iba aquí. Es el mismo patrón que el `is_header` de L1 —que L2 destapó— y
que los recuentos que se quedaron viejos en tres documentos: **una afirmación
sobre algo que no se está construyendo no la comprueba nadie hasta que alguien la
necesita.** Corregido al preparar L3.
"""

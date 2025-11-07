# Factura OCR Processor - Web Interface

## Descripción

Interfaz web moderna para procesar facturas PDF usando OCR. Permite procesar archivos individuales o múltiples archivos en lote.

## Características

- ✅ Interfaz web moderna y responsive
- ✅ Procesamiento de archivos individuales
- ✅ Procesamiento en lote (múltiples archivos)
- ✅ Detección automática del tipo de factura
- ✅ Visualización de resultados en tabla
- ✅ Descarga de resultados en formato CSV
- ✅ Drag & drop de archivos
- ✅ Indicadores de progreso

## Instalación

1. Instala las dependencias (si aún no lo has hecho):
```bash
pip install -r requirements.txt
```

2. Asegúrate de que Tesseract y Poppler estén configurados correctamente en las rutas especificadas en `text_extractor.py`.

## Uso

1. Inicia el servidor web:
```bash
python app.py
```

2. Abre tu navegador y ve a:
```
http://127.0.0.1:5000
```

3. Selecciona o arrastra un archivo PDF de factura

4. Haz clic en "Procesar Factura"

5. Los resultados se mostrarán automáticamente y podrás descargarlos como CSV

## Tipos de Factura Soportados

- BBI
- Hellen
- Agro
- Cuotas
- Yardins
- Latam
- Avianca
- Procafe
- D1

## Notas

- El procesamiento puede tardar varios segundos dependiendo del tamaño del archivo
- Los archivos se procesan temporalmente y se eliminan después
- La interfaz detecta automáticamente el tipo de factura

## Solución de Problemas

Si encuentras errores:
1. Verifica que Tesseract y Poppler estén instalados correctamente
2. Asegúrate de que los archivos PDF no estén corruptos
3. Revisa la consola del servidor para mensajes de error detallados


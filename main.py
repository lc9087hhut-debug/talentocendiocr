import os
from factura_processor import FacturaProcessor
from structure_analyzer import StructureAnalyzer

# FUNCIÓN: Detección automática del tipo de factura
def detect_factura_type(file_path):
    print(f"\nAnalizando estructura de: {os.path.basename(file_path)}")
    try:
        if not os.path.exists(file_path):
            print(f"El archivo no existe: {file_path}")
            return "desconocido"
        if not file_path.lower().endswith('.pdf'):
            print(f"El archivo no es un PDF: {file_path}")
            return "desconocido"

        from formats.factura_bbi import FacturaExtractorBBI
        from formats.factura_hellen import FacturaExtractorHellen
        from formats.factura_agro import FacturaExtractorAgro
        from formats.factura_cuotas import FacturaExtractorCuotas
        from formats.factura_latam import FacturaExtractorLatam
        from formats.factura_avianca import FacturaExtractorAvianca
        from formats.factura_procafe import FacturaExtractorProcafe
        from formats.factura_d1 import FacturaExtractorD1

        from text_extractor import TextExtractor

        EXTRACTORS = [
            ("bbi", FacturaExtractorBBI),
            ("hellen", FacturaExtractorHellen),
            ("agro", FacturaExtractorAgro),
            ("cuotas", FacturaExtractorCuotas),
            ("latam", FacturaExtractorLatam),
            ("avianca", FacturaExtractorAvianca),
            ("procafe", FacturaExtractorProcafe),
            ("d1", FacturaExtractorD1),
        ]
        temp = TextExtractor(file_path)
        text = temp.extract_text(quick=True)

        # Validar texto más inteligentemente
        if not isinstance(text, str) or len(text.strip()) < 100:
            print("Texto OCR corto o incompleto. Reintentando con OCR completo...")
            text = temp.extract_text(quick=False)
        if not text or len(text.strip()) == 0:
            print("El texto OCR sigue vacío o no es válido tras reintento.")
            return "desconocido"

        # Mostrar parte del texto OCR
        preview = text[:400].replace("\n", " ")
        print(f"Fragmento OCR detectado ({len(text)} caracteres):\n{preview}...\n")
        # Normalización ligera para buscar patrones aproximados
        clean_text = text.upper().replace(" ", "").replace("\n", "")

        # Detección rápida por palabras clave
        if any(keyword in clean_text for keyword in ["BBICOLOMBIA", "B8ICOLOMBIA", "BBICOLOMBIASAS"]):
            print("Detección heurística: factura tipo BBI")
            return "BBI"
        if "HELLEN" in clean_text:
            print("Detección heurística: factura tipo HELLEN")
            return "HELLEN"
        if "AGRO" in clean_text:
            print("Detección heurística: factura tipo AGRO")
            return "AGRO"
        if "CUOTAS" in clean_text:
            print("Detección heurística: factura tipo CUOTAS")
            return "CUOTAS"
        if "LATAM" in clean_text:
            print("Detección heurística: factura tipo LATAM")
            return "LATAM"
        if "AVIANCA" in clean_text:
            print("Detección heurística: factura tipo AVIANCA")
            return "AVIANCA"
        if "PROCAFE" in clean_text:
            print("Detección heurística: factura tipo PROCAFE")
            return "PROCAFE"
        if "D1" in clean_text:
            print("Detección heurística: factura tipo D1")
            return "D1"
          ### hola soy una prueba .....  

        # Si falla la heurística, usar extractores formales
        for tipo, extractor_class in EXTRACTORS:
            if hasattr(extractor_class, 'matches'):
                try:
                    if extractor_class.matches(text):
                        print(f"Tipo detectado: {tipo.upper()}")
                        return tipo.upper()
                except Exception as e:
                    print(f"Error en matches() de {extractor_class.__name__}: {e}")
        print("Ningún extractor coincidió con el texto OCR.")
        return "desconocido"
    except Exception as e:
        print(f"Error durante la detección: {e}")
        return "desconocido"

# FUNCIÓN PRINCIPAL
def main():
    print("\n=== EXTRACTOR DE DATOS DE FACTURAS ===")
    print("Procesar un archivo específico")
    print("Procesar todos los PDFs en una carpeta")

    opcion = input("\nSeleccione una opción (1 o 2): ").strip()
    if opcion == "1":
        file_path = input("Ingrese la ruta completa del archivo de la factura: ").strip()
        if not os.path.exists(file_path):
            print(f"El archivo no existe: {file_path}")
            return
        if not file_path.lower().endswith('.pdf'):
            print(f"El archivo no es un PDF: {file_path}")
            return
        factura_type = detect_factura_type(file_path)
        if factura_type == "desconocido":
            print("No se pudo detectar el tipo de factura.")
            factura_type = input("Ingrese manualmente el tipo de factura (BBI/HELLEN/CUOTAS): ").strip().upper()

            # Validar el tipo ingresado
            if factura_type not in ['BBI', 'HELLEN', 'CUOTAS', 'AGRO']:
                print("Tipo de factura no válido. Debe ser BBI, HELLEN o CUOTAS.")
                return

        # Procesar la factura
        print(f"\nIniciando procesamiento con extractor: FacturaExtractor{factura_type}")
        success, data = FacturaProcessor.process_factura(file_path, factura_type)

        if success:
            print("\nDATOS EXTRAÍDOS:")
            for k, v in data.items():
                print(f"{k}: {v}")

            # Guardar CSV
            output_dir = os.path.join(os.path.dirname(file_path), "data")
            os.makedirs(output_dir, exist_ok=True)
            csv_file = os.path.join(output_dir, os.path.splitext(os.path.basename(file_path))[0] + "_extracted.csv")

            with open(csv_file, "w", encoding="utf-8") as f:
                f.write("Campo,Valor\n")
                for k, v in data.items():
                    f.write(f"{k},{v}\n")

            print(f"Datos guardados en: {csv_file}")
        else:
            print("No se pudo procesar la factura.")

  
    # OPCIÓN 2: Carpeta completa
    elif opcion == "2":
        folder_path = input("Ingrese la ruta de la carpeta con los PDFs: ").strip()

        # Verificar si la carpeta existe
        if not os.path.exists(folder_path):
            print(f"La carpeta no existe: {folder_path}")
            return

        # Obtener todos los archivos PDF en la carpeta
        pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
        if not pdf_files:
            print("No se encontraron archivos PDF en la carpeta.")
            return
        print(f"\nSe encontraron {len(pdf_files)} archivos PDF:")
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"{i}. {pdf_file}")

        confirm = input("\n¿Procesar todos? (s/n): ").strip().lower()
        if confirm != "s":
            print("Proceso cancelado.")
            return
        # Procesar cada archivo
        for pdf_file in pdf_files:
            file_path = os.path.join(folder_path, pdf_file)
            print(f"\nProcesando: {pdf_file}")

            try:
                # Detectar el tipo de factura
                factura_type = detect_factura_type(file_path)
                # Si no se detecta, omitir el archivo
                if factura_type == "desconocido":
                    print("No se detectó el tipo. Omitiendo...")
                    continue

                # Procesar la factura
                print(f"\nIniciando procesamiento con extractor: FacturaExtractor{factura_type}")
                success, data = FacturaProcessor.process_factura(file_path, factura_type)
                if success:
                    # Crear directorio de salida si no existe
                    output_dir = os.path.join(folder_path, "data")
                    os.makedirs(output_dir, exist_ok=True)
                    csv_file = os.path.join(output_dir, os.path.splitext(pdf_file)[0] + "_extracted.csv")
                    with open(csv_file, "w", encoding="utf-8") as f:
                        f.write("Campo,Valor\n")
                        for k, v in data.items():
                            f.write(f"{k},{v}\n")

                    print(f"Datos guardados en: {csv_file}")
                else:
                    print("No se pudo procesar la factura.")
            except Exception as e:
                print(f"Error procesando {pdf_file}: {e}")
                print("Omitiendo este archivo y continuando con el siguiente...")
    else:
        print("Opción no válida. Elija 1 o 2.")

# PUNTO DE ENTRADA
if __name__ == "__main__":
    main()

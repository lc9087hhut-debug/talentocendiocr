import re
import pytesseract
import os
import subprocess
import cv2
import numpy as np
from PIL import Image
import shutil
import tempfile
import getpass

class TextExtractor:
    """
    Clase base para extracción de texto desde PDF o imagen usando Tesseract + Poppler.
    Soporta PDFs de múltiples páginas y unifica el texto en un solo bloque.
    """
    def __init__(self, file_path):
        self.file_path = file_path
        self.text = ""

        # Obtener usuario actual de Windows
        user = getpass.getuser()

        # Configuración de rutas (modificar las rutas el usuario)
        default_tesseract = fr"utils\Tesseract-OCR\tesseract.exe"
        default_poppler = fr"utils\poppler-24.08.0\Library\bin"

        # Validar y configurar Tesseract
        if os.path.exists(default_tesseract):
            self.tesseract_path = default_tesseract
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
            print(f"Tesseract configurado en: {self.tesseract_path}")
        else:
            print(f"No se encontró Tesseract en {self.tesseract_path}")
            self.tesseract_path = None

        # Validar Poppler
        if os.path.exists(default_poppler):
            self.poppler_path = default_poppler
            print(f"Poppler encontrado en: {self.poppler_path}")
        else:
            print(f"No se encontró Poppler en {self.poppler_path}")
            self.poppler_path = None

    # Conversión PDF → múltiples imágenes
    def _pdf_to_images(self, pdf_path: str, quick=False):
        """Convierte un PDF multipágina en varias imágenes PNG."""
        if not self.poppler_path:
            raise RuntimeError("Poppler no está disponible")

        temp_dir = tempfile.mkdtemp(prefix="ocr_temp_")
        print(f"Directorio temporal creado: {temp_dir}")

        try:
            pdftoppm_path = os.path.join(self.poppler_path, "pdftoppm.exe")
            if not os.path.exists(pdftoppm_path):
                raise RuntimeError(f"No se encontró pdftoppm.exe en {self.poppler_path}")

            pdf_filename = os.path.basename(pdf_path)
            temp_pdf_path = os.path.join(temp_dir, pdf_filename)
            shutil.copy2(pdf_path, temp_pdf_path)
            cmd = [pdftoppm_path, "-png", "-r", "150" if quick else "300", temp_pdf_path, os.path.join(temp_dir, "page")]
            if quick:
                cmd[1:1] = ["-f", "1", "-l", "1"]
            print(f"➡️ Ejecutando Poppler ({'primera página' if quick else 'todas las páginas'}): {' '.join(cmd)}")
            subprocess.run(cmd, check=True, cwd=self.poppler_path, capture_output=True, text=True)
            image_files = sorted(
                [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith(".png")],
                key=lambda f: int(re.search(r"page-(\d+)\.png", f).group(1)) if re.search(r"page-(\d+)\.png", f) else 0
            )
            if not image_files:
                raise FileNotFoundError("No se generaron imágenes con Poppler.")
            print(f"{len(image_files)} páginas convertidas a imágenes.")
            return image_files, temp_dir
        except subprocess.CalledProcessError as e:
            print(f"Error ejecutando Poppler: {e.stderr}")
            raise RuntimeError(f"Error ejecutando Poppler: {e.stderr}")
        except Exception as e:
            raise RuntimeError(f"Error general al convertir PDF a imágenes: {e}")

    # Preprocesamiento de imagen
    def preprocess_image(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            raise RuntimeError(f"No se pudo abrir la imagen: {image_path}")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        if np.mean(thresh) < 127:
            thresh = cv2.bitwise_not(thresh)

        return thresh
  
    # OCR completo o rápido (quick mode)
    def extract_text(self, force_extract=False, quick=False):
        """
        Extrae texto OCR de todas las páginas o solo la primera si quick=True.
        Retorna SIEMPRE una cadena con el texto extraído (nunca un bool).
        """
        # Si ya hay texto y no se fuerza extracción, retornarlo directamente
        if self.text and not force_extract:
            print("Texto ya extraído, omitiendo paso de extracción.")
            return self.text
        try:
            # Convertir PDF a imágenes
            if self.file_path.lower().endswith(".pdf"):
                image_paths, temp_dir = self._pdf_to_images(self.file_path, quick=quick)
            else:
                image_paths, temp_dir = [self.file_path], None
            all_text = []
            pages_to_read = image_paths if not quick else [image_paths[0]]
            for i, img_path in enumerate(pages_to_read, start=1):
                print(f"OCR procesando página {i}/{len(pages_to_read)}...")
                processed = self.preprocess_image(img_path)
                text = pytesseract.image_to_string(processed, lang="spa")

                # Limpieza de texto
                #clean = re.sub(r"[^\w\s\.\-\:/\$º°ºªÑñáéíóúÁÉÍÓÚ]", " ", text)
                clean = re.sub(r"[^\w\s\.\-\:/]", " ", text)
                clean = re.sub(r"\s+", " ", clean).strip()
                if len(clean) < 30:
                    print(f"Texto OCR muy corto ({len(clean)} caracteres), posible error.")
                all_text.append(clean)
            # Unificar texto
            self.text = "\n---PAGE_BREAK---\n".join(all_text)
            char_count = len(self.text)
            if char_count < 50:
                print("El texto OCR está vacío o no es válido.")
            else:
                print(f"Texto combinado de {len(pages_to_read)} páginas ({char_count} caracteres totales).")
            # Mostrar fragmento
            print(self.text[:800] + ("..." if char_count > 800 else ""))
            # Eliminar temporales
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                print(f"Directorio temporal eliminado: {temp_dir}")
            # DEVOLVER SIEMPRE STRING
            return self.text.strip()

        except Exception as e:
            print(f"Error al extraer texto multipágina: {e}")
            return ""

    def get_text(self):
        """Devuelve el texto extraído (unificado)."""
        return self.text or ""
    def has_text(self):
        """Verifica si ya se ha extraído texto."""
        return bool(self.text)

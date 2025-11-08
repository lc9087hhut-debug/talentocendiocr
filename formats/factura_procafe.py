import re
from text_extractor import TextExtractor
class FacturaExtractorProcafe(TextExtractor):
    """
    Clase para extraer datos específicos del formato de factura PROCAFE.
    """

    def extract_data(self):
        """
        Extrae los datos requeridos de la factura usando expresiones regulares
        específicas para el formato PROCAFE.
        """
        extracted_data = {}
        
        # --- NIT Emisor ---
        nit_emisor_patterns = [
            r'NIT[:\s]*([0-9.\- ]+)',            # NIT: 830112317-1 o NIT 830112317 - 1
            r'N\.?I\.?T\.?[:\s]*([0-9.\- ]+)',   # N.I.T.: 830112317-1 o N.I.T 830112317 - 1
            r'NIT\s*No\.?\s*[:\-]?\s*([0-9.\- ]+)', # NIT No. 830112317-1
            r'NIT\s+([0-9]{3,}[\- ]?[0-9]{1,})',   # NIT 830112317-1 sin separadores
    
        ]
        extracted_data['nit_emisor'] = self._search_patterns(nit_emisor_patterns)

        # --- NIT Cliente ---
        nit_cliente_patterns = [
                r'C[eé]dula\s+de\s+ciudadan[ií]a[:\s]*([0-9.\-]+)',    # Cédula de ciudadanía: 123456789 o con tilde
                r'C[eé]dula[:\s]*([0-9.\-]+)',                         # Cédula: 123456789
                r'CC[:\s]*([0-9.\-]+)',                                # CC: 123456789
                r'C\.?C\.?[:\s]*([0-9.\-]+)',                          # C.C.: 123456789 o C C 123456789
                r'Identificaci[oó]n[:\s]*([0-9.\-]+)',                 # Identificación: 123456789
                r'Documento\s*(No\.?|N°|#)?[:\s]*([0-9.\-]+)',         # Documento No: 123456789
        ]
        extracted_data['nit_cliente'] = self._search_patterns(nit_cliente_patterns)

        # --- Fecha Emisión ---
        fecha_emision_patterns = [
            r'Fecha\s+de\s+Emisi[oó]n[:\s\-]*([0-9]{4}[-/][0-9]{2}[-/][0-9]{2})',          # Fecha de Emisión: 2025-10-12
            r'Fecha\s+Emisi[oó]n[:\s\-]*([0-9]{4}[-/][0-9]{2}[-/][0-9]{2})',               # Fecha Emisión: 2025-10-12
            r'Fecha\s+de\s+Emisi[oó]n[:\s\-]*([0-9]{2}[-/][0-9]{2}[-/][0-9]{4})',          # Fecha de Emisión: 12/10/2025
            r'Fecha\s+Emisi[oó]n[:\s\-]*([0-9]{2}[-/][0-9]{2}[-/][0-9]{4})',               # Fecha Emisión: 12-10-2025
            r'Fecha\s+Emisi[oó]n[:\s\-]*([0-9]{4}[-/][0-9]{2}[-/][0-9]{2}\s*[-]?\s*[0-9:]{2,8})',  # Fecha Emisión: 2025-10-12 - 17:38:56
            r'Fecha\s+de\s+Emisi[oó]n[:\s\-]*([0-9]{2}[-/][0-9]{2}[-/][0-9]{4}\s*[0-9:]{0,8})',    # Fecha de Emisión: 12/10/2025 17:38
        ]
        extracted_data['fecha_emision'] = self._search_patterns(fecha_emision_patterns)

        # --- RAZÓN SOCIAL (Cliente) ---
        razon_patterns = [   # Pendiente revisar, tiene misma estructura cliente
            r'Raz[oó]n\s*Social\s*/\s*Nombre[:\s]*([A-Z0-9ÁÉÍÓÚÑÜ.\-&\s]+)',   # Razón Social/ Nombre: PROCAFECOL S.A.
            r'Raz[oó]n\s*Social\s*[:\s]*([A-Z0-9ÁÉÍÓÚÑÜ.\-&\s]+)',              # Razón Social: Empresa XYZ S.A.S.
            r'Nombre\s*[:\s]*([A-Z0-9ÁÉÍÓÚÑÜ.\-&\s]+)',                        # Nombre: Juan Pérez
            r'Raz[oó]n\s*Social\s*y\s*Nombre[:\s]*([A-Z0-9ÁÉÍÓÚÑÜ.\-&\s]+)',   # Razón Social y Nombre: ...
            r'Nombre\s*/\s*Raz[oó]n\s*Social[:\s]*([A-Z0-9ÁÉÍÓÚÑÜ.\-&\s]+)',   # Nombre / Razón Social:
        ]
        razon_social = self._search_patterns(razon_patterns)
        if razon_social:
            # Tomamos solo el primer nombre (antes del espacio)
            extracted_data['razon_social'] = razon_social.split()[0]
        else:
            extracted_data['razon_social'] = ""

        # --- NÚMERO DE FACTURA ---
        # Buscamos específicamente después de "FACTURA ELECTRÓNICA DE VENTA"
        factura_patterns = [
            r'FACTURA\s+ELECTR[OÓ]NICA\s+DE\s+VENTA\s*[:\-]?\s*(?:No\.?|N°|#)?\s*(F[\-]?\d+)',   # FACTURA ELECTRÓNICA DE VENTA F11368513
            r'FACTURA\s+DE\s+VENTA\s+ELECTR[OÓ]NICA\s*[:\-]?\s*(?:No\.?|N°|#)?\s*(F[\-]?\d+)',   # FACTURA DE VENTA ELECTRÓNICA F11368513
            r'FACTURA\s+ELECTR[OÓ]NICA\s*[:\-]?\s*(?:No\.?|N°|#)?\s*(F[\-]?\d+)',                # FACTURA ELECTRÓNICA F11368513
            r'FACTURA\s+DE\s+VENTA\s*[:\-]?\s*(?:No\.?|N°|#)?\s*(F[\-]?\d+)',                    # FACTURA DE VENTA No. F11368513
            r'(?:^|\n)\s*(F\d{5,})', 
        ]
        extracted_data['numero_factura'] = self._search_patterns(factura_patterns)

        # --- SUBTOTAL (TOTAL BRUTO) ---
        subtotal_patterns = [
            r'SUB\s*TOTAL[:\s]*\$?\s*([0-9.,]+)',            # SUB TOTAL  15,798.32  o SUB TOTAL: $15.798,32
            r'SUBTOTAL[:\s]*\$?\s*([0-9.,]+)',               # SUBTOTAL: 15798.32
            r'Valor\s*SUBTOTAL[:\s]*\$?\s*([0-9.,]+)',       # Valor SUBTOTAL: 15798
            r'SUB\s*TOTAL\s*BASE[:\s]*\$?\s*([0-9.,]+)',     # SUB TOTAL BASE 15798, común en algunas plantillas
        ]
        subtotal = self._search_patterns(subtotal_patterns)
        extracted_data['subtotal'] = self._normalize_amount(subtotal)

        # --- IVA ---
        iva_patterns = [
            r'IVA[:\s]*\$?\s*([0-9.,]+)',                      # IVA  3,001.68  o IVA: $3.001,68
            r'IVA\s*\(?\d{1,2}%\)?[:\s]*\$?\s*([0-9.,]+)',     # IVA (19%): 3,001.68
            r'Impuesto\s*IVA[:\s]*\$?\s*([0-9.,]+)',           # Impuesto IVA: 3001.68
            r'IVA\s*\d{1,2}%?\s*[:\-]?\s*\$?\s*([0-9.,]+)',    # IVA 19% 3001.68 o IVA-19%: $3001.68
        ]
        iva = self._search_patterns(iva_patterns)
        extracted_data['iva'] = self._normalize_amount(iva)

        # --- TOTAL ---
        total_patterns = [
            r'VALOR TOTAL[:\s]*([0-9., ]+)',
        ]
        total = self._search_patterns(total_patterns)
        extracted_data['valor_total'] = self._normalize_amount(total)

        return extracted_data

    def _search_patterns(self, patterns):
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                try:
                    return match.group(1).strip()
                except IndexError:
                    return match.group(0).strip()
        return ""

    def process(self):
        if not self.extract_text():
            return False, []
        extracted_data = self.extract_data()
        required_fields = ['nit_emisor', 'nit_cliente', 'fecha_emision', 'iva', 'razon_social', 'numero_factura', 'valor_total']
        missing = [f for f in required_fields if not extracted_data.get(f)]
        if missing:
            return False, missing
        return True, extracted_data
    
    @staticmethod
    def _normalize_amount(value):
        if not value:
            return "0,00"         
        value = re.sub(r'\s+', '', value)
        clean = re.sub(r"[^\d,\.]", "", value)
        
        if ',' in clean and '.' in clean:
            clean = clean.replace('.', '').replace(',', '.')
        elif ',' in clean:
            clean = clean.replace(',', '.')
        elif '.' in clean:
            pass      
        try:
            num = float(clean)
            return f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return "0,00"

    @staticmethod
    def matches(text):
        if not isinstance(text, str):
            return False
        text_upper = text.upper()
        return "PROCAFECOL" in text_upper or "FACTURA ELECTRÓNICA DE VENTA" in text_upper
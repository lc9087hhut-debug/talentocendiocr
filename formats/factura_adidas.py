
import re
from text_extractor import TextExtractor

class FacturaExtractoradidas(TextExtractor):
    """
    Clase para extraer datos específicos del formato de factura ADIDAS.
    """

    def extract_data(self):
        """
        Extrae los datos requeridos de la factura usando expresiones regulares
        específicas para el formato ADIDAS.
        """
        extracted_data = {}

        # --- NIT Emisor ---
        nit_emisor_patterns = [
            r'NIT[:\s]*([0-9.\-]+)',
            r'N\.?I\.?T\.?[:\s]*([0-9\-]+)',
        ]
        extracted_data['nit_emisor'] = self._search_patterns(nit_emisor_patterns)
        

        # --- NIT Cliente ---
        nit_cliente_patterns = [
            r'(?:Identificación|Identificacion|Nit Cliente)[:\s]*([0-9.\-]+)',
            r'Cliente[:\sA-Za-z]*([0-9]{6,})',     # captura número al final de la línea del cliente
            r'fina\s*ni[:\s]*([0-9]{6,})',         # cubre errores OCR como "fina ni"
            r'([0-9]{7,}-\d)',   
        ]
        extracted_data['nit_cliente'] = self._search_patterns(nit_cliente_patterns)
        
        # --- Fecha y Hora (Fecha de Emisión) ---
        fecha_emision_patterns = [
            r'Fecha y Hora[:\s]*(\d{2}/\d{2}/\d{4}\s*-\s*\d{2}:\d{2}:\d{2})',
            r'Fecha\s*[:\s]*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})',
        ]
        extracted_data['fecha_emision'] = self._search_patterns(fecha_emision_patterns)
        
        # --- Razón Social (Cliente) ---
        razon_patterns = [
            r'Adidas Colombia Ltda\.?',
            r'adidas\s*([^\n]+)',
        ]
        razon_social = self._search_patterns(razon_patterns)
        extracted_data['razon_social'] = razon_social.strip() if razon_social else ""


        # --- Número Interno ---
        numero_interno_patterns = [
            r'Número Interno[:\s]*([0-9]{17})',
            r'Num\.?\s*Interno[:\s]*([0-9]{17})',
        ]
        extracted_data['numero_interno'] = self._search_patterns(numero_interno_patterns)
        
        # --- Subtotal ---
        subtotal_patterns = [
            r'SUBTOTAL[:\s]*([0-9., ]+)',
        ]
        subtotal = self._search_patterns(subtotal_patterns)
        extracted_data['subtotal'] = self._normalize_amount(subtotal)
        
        # --- IVA ---
        iva_patterns = [
            r'IVA[:\s]+[0-9.,]+%?\s*([0-9., ]+)',
            r'IMPUESTO\s*[A-Z%]*\s*([0-9., ]+)',
        ]
        iva = self._search_patterns(iva_patterns)
        extracted_data['iva'] = self._normalize_amount(iva)

        return extracted_data

    # ==================================================
    # MÉTODOS AUXILIARES
    # ==================================================

    def _search_patterns(self, patterns):
        """Busca y devuelve el primer valor que coincida con los patrones."""
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                try:
                    return match.group(1).strip()
                except IndexError:
                    return match.group(0).strip()
        return ""

    def process(self):
        """Procesa el texto y valida que se encuentren los campos requeridos."""
        if not self.extract_text():
            return False, []

        extracted_data = self.extract_data()

        required_fields = [
            'nit_emisor',
            'nit_cliente',
            #'fecha_emision',
            #'razon_social',
            #'numero_factura',
            #'valor_total'
        ]

        missing = [f for f in required_fields if not extracted_data.get(f)]
        if missing:
            return False, missing

        return True, extracted_data

    @staticmethod
    def _normalize_amount(value):
        """Normaliza valores numéricos (montos) al formato 0,00."""
        if not value or not isinstance(value, str):
            return "0,00"

        # Eliminar espacios y caracteres no numéricos
        value = value.strip()
        value = re.sub(r'\s+', '', value)
        clean = re.sub(r"[^\d,.,]", "", value)

        # Manejo de formatos con miles/puntos y decimales/comas
        # Ejemplo: 1.234.567,89 → 1234567.89
        if clean.count(',') > 1:
            # Si hay más de una coma, probablemente son separadores de miles
            clean = clean.replace(',', '')
        elif ',' in clean and '.' in clean:
            # Formato europeo: 1.234,56
            clean = clean.replace('.', '').replace(',', '.')
        elif ',' in clean:
            # Si solo hay coma, es decimal
            clean = clean.replace(',', '.')
        elif '.' in clean:
            # Si solo hay punto, verificar si es decimal o miles
            parts = clean.split('.')
            if len(parts[-1]) != 2:  # si no parece decimal (2 cifras), eliminar puntos
                clean = clean.replace('.', '')

        # Intentar convertir a float de manera segura
        try:
            num = float(clean)
            return f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            return "0,00"


    @staticmethod
    def matches(text):
        """Verifica si el texto corresponde a una factura de ADIDAS."""
        if not isinstance(text, str):
            return False
        text_upper = text.upper()
        return "ADIDAS COLOMBIA LTDA" in text_upper or "805.011.074-2" in text_upper

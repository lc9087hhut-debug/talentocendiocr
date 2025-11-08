import re
from text_extractor import TextExtractor

class FacturaExtractorD1(TextExtractor):
    """
    Clase para extraer datos específicos de facturas D1 S.A.S.
    """

    def extract_data(self):
        """
        Extrae los datos requeridos de la factura D1 usando expresiones regulares.
        """
        extracted_data = {}
        
        # --- 1. Fecha de Emisión ---
        fecha_emision_patterns = [
            r'FECHA:\s*(\d{4}-\d{2}-\d{2})',
            r'Fecha:\s*(\d{4}-\d{2}-\d{2})',
        ]
        extracted_data['fecha_emision'] = self._search_patterns(fecha_emision_patterns)

        # --- 2. Número de Factura ---
        numero_factura_patterns = [
            r'FACTURA\s+ELECTR[OÓ]NICA\s+DE\s+VENTA\s+N:\s*([A-Z0-9]+)',
            r'VENTA\s+N:\s*([A-Z0-9]+)',
        ]
        extracted_data['numero_factura'] = self._search_patterns(numero_factura_patterns)

        # --- 3. Total ---
        valor_total_patterns = [
            r'TOTAL:\s*([\d\.,]+)',
            r'\[TOTALES\s+DE\s+FACTURA\].*?TOTAL:\s*([\d\.,]+)',
        ]
        total_str = self._search_patterns(valor_total_patterns)
        extracted_data['valor_total'] = self._normalize_amount(total_str)

        # --- 4. Subtotal ---
        subtotal_patterns = [
            r'SUBTOTAL:\s*([\d\.,]+)',
        ]
        subtotal_str = self._search_patterns(subtotal_patterns)
        extracted_data['subtotal'] = self._normalize_amount(subtotal_str)

        # --- 5. IVA ---
        iva_patterns = [
            r'IVA:\s*([\d\.,]+)',
            r'\[TOTALES\s+DE\s+FACTURA\].*?IVA:\s*([\d\.,]+)',
        ]
        iva_str = self._search_patterns(iva_patterns)
        extracted_data['iva'] = self._normalize_amount(iva_str)

        # --- 6. Razón Social ---
        razon_social_patterns = [
            r'^(D1\s+S\s+A\s+S)',
            r'(D1\s+S\s*A\s*S)',
        ]
        razon_social = self._search_patterns(razon_social_patterns)
        if not razon_social:
            razon_social = "D1 S A S"
        extracted_data['razon_social'] = razon_social

        # --- 7. NIT Emisor ---
        nit_emisor_patterns = [
            r'D1\s+S\s+A\s+S\s+NIT\s+([\d\-]+)',
            r'NIT\s+([\d\-]+)',
        ]
        extracted_data['nit_emisor'] = self._search_patterns(nit_emisor_patterns)

        # --- 8. NIT/Documento Cliente ---
        nit_cliente_patterns = [
            r'NUM\.\s+DOCUMENTO:\s*(\d+)',
            r'DOCUMENTO:\s*(\d+)',
        ]
        extracted_data['nit_cliente'] = self._search_patterns(nit_cliente_patterns)

        return extracted_data

    def _search_patterns(self, patterns):
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
            if match:
                try:
                    result = match.group(1).strip()
                    result = re.sub(r'\s+', ' ', result).strip()
                    return result
                except IndexError:
                    result = match.group(0).strip()
                    return re.sub(r'\s+', ' ', result).strip()
        return ""

    def process(self):
        if not self.extract_text():
            return False, []
        
        # DEBUG: Mostrar secciones clave
        print(f"\n=== DEBUG D1: Secciones clave ===")
        
        # Mostrar cabecera
        if "FACTURA" in self.text:
            idx = self.text.find("FACTURA")
            print(f"Cabecera: '{self.text[max(0, idx-20):idx+150]}'")
        
        # Mostrar sección de totales
        if "SUBTOTAL" in self.text:
            idx = self.text.find("SUBTOTAL")
            print(f"Totales: '{self.text[max(0, idx-50):idx+200]}'")
        
        # Mostrar NIT emisor
        if "NIT" in self.text:
            matches = [m.start() for m in re.finditer(r'NIT', self.text)]
            for i, idx in enumerate(matches[:2], 1):
                print(f"NIT {i}: '{self.text[max(0, idx-30):idx+50]}'")
        
        print("==================================\n")
            
        extracted_data = self.extract_data()
        
        required_fields = [
            'fecha_emision', 
            'numero_factura', 
            'valor_total', 
            'subtotal', 
            'iva', 
            'razon_social', 
            'nit_emisor', 
            'nit_cliente'
        ]
        
        missing = [f for f in required_fields if not extracted_data.get(f)]
        if missing:
            print(f"Campos faltantes: {missing}")
            print(f"Datos extraídos: {extracted_data}")
            return False, missing
            
        return True, extracted_data
    
    @staticmethod
    def _normalize_amount(value):
        if not value:
            return "0,00"

        value = re.sub(r'\s+', '', value)
        clean = re.sub(r"[^\d,\.]", "", value)
        
        if not clean:
            return "0,00"
        
        last_comma_pos = clean.rfind(',')
        last_dot_pos = clean.rfind('.')
        
        if last_comma_pos != -1 and last_dot_pos != -1:
            if last_comma_pos > last_dot_pos:
                clean = clean.replace('.', '').replace(',', '.')
            else:
                clean = clean.replace(',', '')
        
        elif last_comma_pos != -1:    
            parts = clean.split(',')
            last_part = parts[-1]
            if len(last_part) == 2:    
                clean = clean.replace('.', '').replace(',', '.')
            elif len(last_part) == 3:
                clean = clean.replace(',', '')
            else:
                clean = clean.replace(',', '.')
        
        elif last_dot_pos != -1:
            parts = clean.split('.')
            last_part = parts[-1]
            if len(last_part) == 2:
                pass
            elif len(last_part) == 3:
                clean = clean.replace('.', '')
            else:
                if clean.count('.') == 1:
                    pass 
                else:
                    clean = clean.replace('.', '')
        
        try:
            num = float(clean)
            formatted = f"{num:,.2f}" 
            result = formatted.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
            return result
        except ValueError:
            return "0,00"

    @staticmethod
    def matches(text):
        """
        Detecta si el texto corresponde a una factura D1.
        """
        if not isinstance(text, str):
            return False
        text_upper = text.upper()
        
        has_d1 = "D1" in text_upper and ("S A S" in text_upper or "SAS" in text_upper)
        has_indicators = (
            "FACTURA ELECTRÓNICA" in text_upper or
            "FACTURA ELECTRONICA" in text_upper or
            "TIENDA-" in text_upper
        )
        
        return has_d1 and has_indicators
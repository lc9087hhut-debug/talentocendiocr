import numpy as np
from text_extractor import TextExtractor
import re

class StructureAnalyzer:
    """
    Analiza la estructura general de una factura (sin depender del texto literal)
    para identificar el tipo de formato (BBI, Hellen, Cuotas, etc.).
    """
    def __init__(self, file_path):
        self.file_path = file_path
        self.text_extractor = TextExtractor(file_path)
        self.text = ""

    def analyze(self):
        """
        Extrae texto con OCR y calcula métricas estructurales aproximadas.
        Estas métricas reflejan la "densidad" y el orden visual del texto.
        """
        print(f"\n📄 Analizando estructura de: {self.file_path}")
        success = self.text_extractor.extract_text()
        if not success:
            print("No se pudo extraer texto OCR para análisis estructural.")
            return {}
        self.text = self.text_extractor.get_text()
        lines = [line.strip() for line in re.split(r"[\\n\\r]+", self.text) if line.strip()]
        if not lines:
            print("No se detectaron líneas válidas en el OCR.")
            return {}

        # Estimaciones estructurales a partir de características del texto
        num_blocks = len(lines)
        avg_line_len = np.mean([len(l) for l in lines])
        height_var = np.var([len(l) for l in lines])
        empty_lines = sum(1 for l in lines if len(l.strip()) < 3)
        density = round(num_blocks / (empty_lines + 1), 2)

        # Detección de columnas simulada: si hay muchos guiones/tabulaciones
        column_markers = sum(1 for l in lines if re.search(r"\s{5,}", l))
        estimated_columns = 1 + (1 if column_markers > len(lines) * 0.1 else 0)

        # Detectar palabras clave específicas de cada formato (más específicas)
        bbi_keywords = sum(1 for line in lines if re.search(r'\bBBI\b|BBICOLOMBIASAS', line, re.IGNORECASE))
        hellen_keywords = sum(1 for line in lines if re.search(r'\bCINE\s+COLOMBIA\b|CINE\s+S\.A\.S\.', line, re.IGNORECASE))
        cuotas_keywords = sum(1 for line in lines if re.search(r'\bCUOTAS\b|PLAN\s+DE\s+PAGO', line, re.IGNORECASE))

        metrics = {
            "num_blocks": num_blocks,
            "avg_width": avg_line_len,
            "avg_height": np.mean([len(l.split()) for l in lines]),
            "y_density": density,
            "height_var": height_var,
            "column_count": estimated_columns,
            "bbi_keywords": bbi_keywords,
            "hellen_keywords": hellen_keywords,
            "cuotas_keywords": cuotas_keywords,
        }
        print(f"📊 Métricas detectadas: {metrics}")
        return metrics

    def detect_structure(self):
        """
        Determina el tipo de factura (BBI, Hellen, Cuotas, etc.)
        basándose en patrones de estructura visual y palabras clave.
        """
        metrics = self.analyze()
        if not metrics:
            return "desconocido"
        # --- Patrones basados en métricas y palabras clave ---
        patterns = {
            "bbi": {
                "num_blocks": (100, 200),     
                "avg_width": (10, 20),        
                "column_count": (1, 2),
                "y_density": (7, 10),
                "bbi_keywords": (1, 10),      
                "hellen_keywords": (0, 0),     
                "cuotas_keywords": (0, 0),    
            },
            "hellen": {
                "num_blocks": (30, 60),
                "avg_width": (20, 30),
                "column_count": (1, 1),
                "y_density": (3, 5),
                "bbi_keywords": (0, 0),
                "hellen_keywords": (1, 5),
                "cuotas_keywords": (0, 0),
            },
            "cuotas": {
                "num_blocks": (20, 50),
                "avg_width": (20, 40),
                "column_count": (1, 1),
                "y_density": (2, 6),
                "bbi_keywords": (0, 0),
                "hellen_keywords": (0, 0),
                "cuotas_keywords": (1, 5),
            },
        }
        best_match = None
        best_score = -1

        for tipo, pattern in patterns.items():
            score = self._compare_metrics(metrics, pattern)
            print(f"Coincidencia {tipo.upper()}: {score:.2f}")
            if score > best_score:
                best_score = score
                best_match = tipo
        # Umbral mínimo de confianza
        if best_score < 0.5:
            print("Confianza baja en la detección estructural.")
            return "desconocido"
        print(f"Estructura detectada como: {best_match.upper()}")
        return best_match.upper()

    def _compare_metrics(self, metrics, pattern):
        """Evalúa coincidencia entre métricas detectadas y patrón base."""
        score = 0
        total_weight = 0
        
        # Pesos para cada métrica (más peso = más importante)
        weights = {
            "num_blocks": 1.2,
            "avg_width": 1.0,
            "column_count": 1.0,
            "y_density": 1.0,
            "bbi_keywords": 2.5,    
            "hellen_keywords": 2.5,
            "cuotas_keywords": 2.5,
        }
        
        for key, (min_val, max_val) in pattern.items():
            if key not in metrics:
                continue               
            val = metrics[key]
            weight = weights.get(key, 1.0)           
            # Verificar si el valor está dentro del rango esperado
            if min_val <= val <= max_val:
                # Calcular qué tan cerca está del centro del rango
                center = (min_val + max_val) / 2
                range_size = max_val - min_val
                if range_size > 0:
                    distance = abs(val - center) / range_size
                    proximity = 1 - distance
                else:
                    proximity = 1.0
                
                score += weight * proximity
            else:
                # Fuera del rango, penalización
                score += 0                
            total_weight += weight        
        # Normalizar puntuación
        if total_weight == 0:
            return 0           
        return score / total_weight
# START: Generador de Currículum de Inferencia Activa

Un pipeline sofisticado para generar, analizar y visualizar currículos personalizados de Inferencia Activa a través de dominios, audiencias e idiomas. Esta herramienta permite la creación automatizada de guías "COMIENZA AQUÍ" adaptadas a dominios y audiencias específicas, con potentes capacidades de visualización y análisis.

## 🚀 Características

### Generación de Currículo
- Investigación y generación de contenido específico por dominio
- Análisis y adaptación de perspectiva de audiencia
- Soporte de traducción multilingüe (más de 85 idiomas)
- Mecanismos de control y refinamiento de calidad

### Visualización Avanzada
- Modelado de temas y agrupación jerárquica
- Análisis de redes de rutas de aprendizaje
- Mapeo de conceptos con detección de comunidades
- Métricas cuantitativas y análisis comparativo

### Arquitectura Modular
- Estructura de carpetas basada en entidades
- Diseño de pipeline extensible
- Configurable para varios casos de uso
- Sistema de procesamiento escalable

## 📦 Scripts Principales

### Investigación de Dominio (`1_Research_Domain.py`)
- Realiza investigación específica del dominio usando Perplexity
- Analiza terminología y conceptos específicos del campo
- Genera comprensión contextual
- Crea base de conocimiento del dominio

### Análisis de Perspectiva (`1_Research_Perspective.py`)
- Analiza características del público objetivo
- Determina niveles apropiados de complejidad
- Identifica ejemplos y analogías relevantes
- Adapta estilo y enfoque del contenido

### Generación de Contenido (`2_Write_Introduction.py`)
- Genera contenido curricular
- Integra conocimientos del dominio y audiencia
- Estructura la progresión del aprendizaje
- Asegura coherencia pedagógica

### Sistema de Visualización (`3_Introduction_Visualizations.py`)
- Mapas de calor de distribución de temas
- Gráficos de red de rutas de aprendizaje
- Mapeo de relaciones conceptuales
- Visualización de métricas curriculares

### Pipeline de Traducción (`4_Translate_Introductions.py`)
- Traducción multilingüe
- Adaptación de scripts
- Consideración cultural
- Verificación de calidad

## 🛠️ Instalación

```bash
# Clonar el repositorio
git clone https://github.com/ActiveInferenceInstitute/Start.git

```

## 🎯 Uso

### Generación Básica de Currículo
```python
# Generar currículo específico del dominio
python Languages/Perplexity/1_Research_Domain.py --input "your_domain.md"

# Adaptar para audiencia específica
python Languages/Perplexity/1_Research_Perspective.py --audience "target_audience"

# Generar currículo
python Languages/Perplexity/2_Write_Introduction.py

# Crear visualizaciones
python Languages/Perplexity/3_Introduction_Visualizations.py

# Traducir contenido
python Languages/Perplexity/4_Translate_Introductions.py
```

### Estructura de Directorios
```
Languages/
├── Perplexity/
│   ├── 1_Research_Domain.py
│   ├── 1_Research_Perspective.py
│   ├── 2_Write_Introduction.py
│   ├── 3_Introduction_Visualizations.py
│   └── 4_Translate_Introductions.py
├── Inputs_and_Outputs/
│   ├── Domain/
│   ├── Written_Curriculums/
│   └── Translations/
```

## 📊 Ejemplos de Visualización

### Análisis de Temas
- Agrupación jerárquica de temas curriculares
- Distribuciones de frecuencia de palabras
- Redes de relaciones conceptuales
- Progresiones de rutas de aprendizaje

### Métricas
- Análisis de complejidad de contenido
- Medición de cobertura de temas
- Evaluación de coherencia estructural
- Comparaciones entre currículos

## 🎯 Aplicaciones

- Difusión de investigación
- Desarrollo de contenido educativo
- Redacción de propuestas de subvención
- Documentación de proyectos
- Gestión del conocimiento organizacional
- Desarrollo de catecismo
- Creación de material de capacitación

## 🔄 Flujo del Pipeline

1. **Procesamiento de Entrada**
   - Recopilación de investigación de dominio
   - Análisis de audiencia
   - Estructuración de contenido

2. **Generación de Contenido**
   - Redacción curricular
   - Evaluación de calidad
   - Optimización estructural

3. **Análisis y Visualización**
   - Modelado de temas
   - Análisis de redes
   - Generación de métricas
   - Representación visual

4. **Traducción y Distribución**
   - Conversión multilingüe
   - Adaptación de formato
   - Verificación de calidad

## 🛣️ Hoja de Ruta

Consulta [ToDo.md](ToDo.md) para planes detallados de desarrollo que incluyen:
- Integración con ORCID
- Implementación de base de datos
- Soporte organizacional
- Características avanzadas de visualización
- Desarrollo de plataforma comunitaria

## 🤝 Contribución

¡Damos la bienvenida a las contribuciones! Consulta nuestra [Guía de Contribución](CONTRIBUTING.md) para detalles sobre:
- Estilo de código
- Proceso de desarrollo
- Procedimiento de pull request
- Pautas de la comunidad

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - consulta el archivo [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- Instituto de Inferencia Activa
- Contribuyentes de la comunidad
- Dependencias de código abierto

## 📬 Contacto

- Issues de GitHub: [Project Issues](https://github.com/ActiveInferenceInstitute/Start/issues)
- Email: [blanket@activeinference.org](mailto:blanket@activeinference.institute)

## 🌟 Únete a la Comunidad

¡Juntos estamos construyendo herramientas para hacer que la Inferencia Activa sea accesible y adaptable a través de dominios, idiomas y perspectivas. ¡Hagamos que el conocimiento fluya libremente!
# 💰 Calculadora de Comisiones de Ventas

Dashboard interactivo en Streamlit para calcular comisiones de ventas basado en archivos Excel.

## 🚀 Características

- **Carga de archivos Excel**: Sube archivos .xlsx con datos de ventas
- **Procesamiento automático de reversiones**: Detecta y cancela automáticamente las ventas reversadas
- **Cálculo de comisiones**: Calcula comisiones por vendedor con porcentaje configurable
- **Visualizaciones**: Gráficos de barras para comisiones y ventas
- **Exportación**: Descarga los resultados en formato Excel

## 📋 Requisitos

- Python 3.8 o superior
- Dependencias listadas en `requirements.txt`

## 🔧 Instalación

1. Clona o descarga este repositorio
2. Instala las dependencias:

```bash
pip install -r requirements.txt
```

## 🎯 Uso

1. Ejecuta la aplicación:

```bash
streamlit run app.py
```

2. Abre tu navegador en la URL que aparece (generalmente `http://localhost:8501`)
3. En la barra lateral, configura el porcentaje de comisión deseado
4. Sube tu archivo Excel (.xlsx) con los datos de ventas
5. Visualiza los resultados y descarga el reporte si lo deseas

## 📊 Formato del Archivo Excel

El archivo Excel debe contener las siguientes columnas (al menos):

- **asesor**: Nombre del vendedor
- **TotalFac**: Valor total de la factura (puede ser positivo o negativo)
- **Identificacion**: Identificación del cliente

### Lógica de Procesamiento

- Cuando `TotalFac` es negativo, el sistema busca una entrada positiva con:
  - La misma `Identificacion`
  - El mismo valor absoluto de `TotalFac`
- Ambos registros se eliminan del cálculo (representan una reversión)
- Esto permite manejar casos donde una venta fue reversada y luego recreada

## 📝 Notas

- El porcentaje de comisión se puede ajustar en la barra lateral
- Los resultados incluyen:
  - Total de ventas por vendedor
  - Número de facturas
  - Clientes únicos
  - Comisión calculada
- El reporte descargable incluye tanto el resumen de comisiones como los datos procesados


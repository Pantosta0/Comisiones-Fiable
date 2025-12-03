import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# Page configuration
st.set_page_config(
    page_title="Calculadora de Comisiones",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Calculadora de Comisiones de Ventas")
st.markdown("---")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuración de Comisiones")
    st.info("""
    **Estructura de Comisiones:**
    - **< 3 ventas**: 0.5% de comisión
    - **≥ 3 ventas**: 1% de comisión
    """)
    st.markdown("---")
    st.markdown("### 📋 Instrucciones")
    st.markdown("""
    1. Suba un archivo Excel (.xlsx) con los datos de ventas
    2. El archivo debe contener las columnas:
       - **asesor**: Nombre del vendedor
       - **TotalFac**: Valor total de la factura
       - **Identificacion**: Identificación del cliente
    3. Las ventas reversadas (TotalFac negativo) se cancelarán automáticamente con ventas positivas del mismo cliente
    """)


def process_reversals(df):
    """
    Process negative TotalFac values by matching them with positive entries
    that have the same Identificacion and same absolute TotalFac value.
    Each pair is removed once.
    """
    # Create a copy to avoid modifying the original
    df_processed = df.copy()
    
    # Find negative TotalFac entries
    negative_mask = df_processed['TotalFac'] < 0
    negative_df = df_processed[negative_mask].copy()
    positive_df = df_processed[~negative_mask].copy()
    
    # Track indices to remove
    indices_to_remove = set()
    
    # Process each negative entry
    for idx, neg_row in negative_df.iterrows():
        # Skip if already processed
        if idx in indices_to_remove:
            continue
            
        neg_identificacion = neg_row['Identificacion']
        neg_total_abs = abs(neg_row['TotalFac'])
        
        # Find matching positive entry with same Identificacion and same absolute TotalFac
        matching_positive = positive_df[
            (positive_df['Identificacion'] == neg_identificacion) &
            (positive_df['TotalFac'] == neg_total_abs)
        ]
        
        if not matching_positive.empty:
            # Get the first matching positive entry
            pos_idx = matching_positive.index[0]
            
            # Mark both for removal
            indices_to_remove.add(idx)
            indices_to_remove.add(pos_idx)
            
            # Remove from positive_df to avoid matching it again
            positive_df = positive_df.drop(pos_idx)
    
    # Remove all matched pairs
    df_processed = df_processed.drop(indices_to_remove)
    
    return df_processed, len(indices_to_remove)


def calculate_commissions(df):
    """
    Calculate commissions per sales person (asesor)
    - Less than 3 sales: 0.5% commission
    - 3 or more sales: 1% commission
    """
    # Group by asesor and calculate totals
    commission_summary = df.groupby('asesor').agg({
        'TotalFac': ['sum', 'count'],
        'Identificacion': 'nunique'
    }).reset_index()
    
    # Flatten column names
    commission_summary.columns = ['asesor', 'total_ventas', 'num_facturas', 'clientes_unicos']
    
    # Apply tiered commission rate based on number of sales
    commission_summary['tasa_comision'] = commission_summary['num_facturas'].apply(
        lambda x: 0.5 if x < 3 else 1.0
    )
    
    # Calculate commission
    commission_summary['comision'] = commission_summary['total_ventas'] * (commission_summary['tasa_comision'] / 100)
    
    # Sort by total sales descending
    commission_summary = commission_summary.sort_values('total_ventas', ascending=False)
    
    return commission_summary


def calculate_commissions_by_product(df):
    """
    Calculate commissions per sales person (asesor) grouped by product (producto)
    Returns a dictionary with product names as keys and commission summaries as values
    """
    commissions_by_product = {}
    
    if 'producto' not in df.columns:
        return commissions_by_product
    
    # Get unique products
    unique_products = df['producto'].dropna().unique()
    
    for product in unique_products:
        # Filter data for this product
        product_df = df[df['producto'] == product]
        
        # Calculate commissions for this product
        commission_summary = product_df.groupby('asesor').agg({
            'TotalFac': ['sum', 'count'],
            'Identificacion': 'nunique'
        }).reset_index()
        
        # Flatten column names
        commission_summary.columns = ['asesor', 'total_ventas', 'num_facturas', 'clientes_unicos']
        
        # Apply tiered commission rate based on number of sales
        commission_summary['tasa_comision'] = commission_summary['num_facturas'].apply(
            lambda x: 0.5 if x < 3 else 1.0
        )
        
        # Calculate commission
        commission_summary['comision'] = commission_summary['total_ventas'] * (commission_summary['tasa_comision'] / 100)
        
        # Sort by total sales descending
        commission_summary = commission_summary.sort_values('total_ventas', ascending=False)
        
        commissions_by_product[product] = commission_summary
    
    return commissions_by_product


# File upload
uploaded_file = st.file_uploader(
    "Subir archivo Excel (.xlsx)",
    type=['xlsx'],
    help="Seleccione el archivo Excel con los datos de ventas"
)

if uploaded_file is not None:
    try:
        # Read Excel file
        with st.spinner("Leyendo archivo Excel..."):
            df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ Archivo cargado exitosamente. {len(df)} registros encontrados.")
        
        # Validate required columns
        required_columns = ['asesor', 'TotalFac', 'Identificacion']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"❌ Faltan las siguientes columnas requeridas: {', '.join(missing_columns)}")
            st.info("Columnas disponibles en el archivo:")
            st.write(df.columns.tolist())
        else:
            # Product filter
            if 'producto' in df.columns:
                st.markdown("---")
                st.subheader("🔍 Filtro por Producto")
                
                # Get unique products
                unique_products = sorted(df['producto'].dropna().unique().tolist())
                
                if len(unique_products) > 0:
                    selected_products = st.multiselect(
                        "Seleccione los productos a incluir (deje vacío para incluir todos):",
                        options=unique_products,
                        default=unique_products,
                        help="Seleccione uno o más productos para filtrar las ventas. Si no selecciona ninguno, se incluirán todos los productos."
                    )
                    
                    # Apply product filter
                    if len(selected_products) > 0:
                        df = df[df['producto'].isin(selected_products)]
                        st.info(f"📦 Filtrando por {len(selected_products)} producto(s) seleccionado(s). {len(df)} registros después del filtro.")
                    # If no products selected, include all (no filter applied)
                else:
                    st.warning("⚠️ No se encontraron productos en la columna 'producto'.")
                    selected_products = []
            else:
                st.warning("⚠️ La columna 'producto' no está presente en el archivo. No se aplicará filtro por producto.")
                selected_products = []
            
            st.markdown("---")
            # Display raw data info
            with st.expander("📊 Información del archivo cargado"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Registros", len(df))
                with col2:
                    st.metric("Vendedores Únicos", df['asesor'].nunique())
                with col3:
                    st.metric("Total Ventas (Bruto)", f"${df['TotalFac'].sum():,.2f}")
            
            # Process reversals
            with st.spinner("Procesando reversiones y cancelaciones..."):
                df_processed, removed_count = process_reversals(df)
            
            st.success(f"✅ Procesamiento completado. {removed_count} registros cancelados (pares de reversión).")
            
            # Display processing info
            with st.expander("📈 Estadísticas de Procesamiento"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Registros Originales", len(df))
                with col2:
                    st.metric("Registros Procesados", len(df_processed))
                with col3:
                    st.metric("Registros Eliminados", removed_count)
                with col4:
                    st.metric("Total Ventas (Neto)", f"${df_processed['TotalFac'].sum():,.2f}")
            
            # Calculate commissions
            with st.spinner("Calculando comisiones..."):
                commission_summary = calculate_commissions(df_processed)
                commissions_by_product = calculate_commissions_by_product(df_processed)
            
            # Display results
            st.markdown("---")
            st.header("📊 Resumen de Comisiones por Vendedor")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Vendedores", len(commission_summary))
            with col2:
                st.metric("Total Ventas Netas", f"${commission_summary['total_ventas'].sum():,.2f}")
            with col3:
                st.metric("Total Comisiones", f"${commission_summary['comision'].sum():,.2f}")
            with col4:
                st.metric("Comisión Promedio", f"${commission_summary['comision'].mean():,.2f}")
            
            # Display commission table
            st.subheader("💼 Detalle de Comisiones")
            
            # Format the dataframe for display
            display_df = commission_summary.copy()
            display_df['total_ventas'] = display_df['total_ventas'].apply(lambda x: f"${x:,.2f}")
            display_df['tasa_comision'] = display_df['tasa_comision'].apply(lambda x: f"{x}%")
            display_df['comision'] = display_df['comision'].apply(lambda x: f"${x:,.2f}")
            display_df.columns = ['Vendedor', 'Total Ventas', 'N° Facturas', 'Clientes Únicos', 'Tasa Comisión', 'Comisión']
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Download button
            st.markdown("---")
            st.subheader("💾 Exportar Resultados")
            
            # Convert to Excel - organized by product
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Commissions by product (separate sheet for each product) - PRIMARY ORGANIZATION
                if commissions_by_product:
                    for product, product_commissions in commissions_by_product.items():
                        # Format product commission data
                        product_download = product_commissions.copy()
                        product_download['tasa_comision'] = product_download['tasa_comision'].apply(lambda x: f"{x}%")
                        product_download.columns = ['Vendedor', 'Total Ventas', 'N° Facturas', 'Clientes Únicos', 'Tasa Comisión', 'Comisión']
                        
                        # Clean sheet name (Excel has 31 char limit and some special chars are not allowed)
                        sheet_name = str(product)[:31]
                        sheet_name = sheet_name.replace('/', '_').replace('\\', '_').replace('?', '_').replace('*', '_').replace('[', '_').replace(']', '_').replace(':', '_')
                        
                        product_download.to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    # If no product column, create a single sheet with all commissions
                    download_df = commission_summary.copy()
                    download_df['tasa_comision'] = download_df['tasa_comision'].apply(lambda x: f"{x}%")
                    download_df.columns = ['Vendedor', 'Total Ventas', 'N° Facturas', 'Clientes Únicos', 'Tasa Comisión', 'Comisión']
                    download_df.to_excel(writer, sheet_name='Comisiones', index=False)
                
                # Processed data
                df_processed.to_excel(writer, sheet_name='Datos Procesados', index=False)
            
            output.seek(0)
            
            st.download_button(
                label="📥 Descargar Reporte Excel",
                data=output,
                file_name="reporte_comisiones.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {str(e)}")
        st.exception(e)
else:
    st.info("👆 Por favor, suba un archivo Excel para comenzar.")


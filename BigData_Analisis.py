"""
Script para operaciones HBase con dataset Auto Sales Data
Requerimientos: happybase, pandas, matplotlib
"""
import happybase
import pandas as pd
import matplotlib.pyplot as plt

# Bloque principal de ejecución
try:
  # 1. Conexión a HBase
  connection = happybase.Connection('localhost')
  connection.open()
  print("Conexión establecida con HBase")

  # 2. Crear tabla con familias de columnas
  table_name = 'auto_sales'
  column_families = {
      'order_info': dict(),
      'customer': dict(),
      'product': dict(),
      'sales': dict()
  }
      
  if table_name.encode() not in connection.tables():
    connection.create_table(table_name, column_families)

  # 3. Cargar datos desde CSV
  df = pd.read_csv('auto-sales-data.csv', parse_dates=['ORDERDATE'], dayfirst=True)

  # 4. Función para transformar datos a formato HBase
  def create_hbase_row(row):
      row_key = f"{row['ORDERNUMBER']}_{row['PRODUCTCODE']}".encode()
      
      data = {  
          b'order_info:order_date': str(row['ORDERDATE']).encode(),
          b'order_info:status': row['STATUS'].encode(),
          b'customer:name': row['CUSTOMERNAME'].encode(),
          b'customer:country': row['COUNTRY'].encode(),
          b'product:line': row['PRODUCTLINE'].encode(),
          b'product:msrp': str(row['MSRP']).encode(),
          b'sales:quantity': str(row['QUANTITYORDERED']).encode(),
          b'sales:price': str(row['PRICEEACH']).encode(),
          b'sales:total': str(row['SALES']).encode(),
          b'sales:deal_size': row['DEALSIZE'].encode()
      }
      return row_key, data

  # 5. Insertar datos en HBase
  table = connection.table(table_name)

  batch_size = 100
  with table.batch(batch_size=batch_size) as batch:
      for _, row in df.iterrows():
          try:
              row_key, data = create_hbase_row(row)
              batch.put(row_key, data)
          except Exception as e:
              print(f"Error insertando fila {row['ORDERNUMBER']}: {str(e)}")

  # 6. Operaciones CRUD y Consultas -------------------------------------------------

  # Operación 1: Obtener una orden específica
  def get_order(order_number, product_code):
      row_key = f"{order_number}_{product_code}".encode()
      return table.row(row_key)

  # Ejemplo de uso
  order_data = get_order(10107, 'S10_1678')
  print("\nDatos de orden 10107:")
  print({k.decode(): v.decode() for k, v in order_data.items()})

  # Operación 2: Actualizar estado de una orden
  def update_order_status(order_number, product_code, new_status):
      row_key = f"{order_number}_{product_code}".encode()
      table.put(row_key, {b'order_info:status': new_status.encode()})

  update_order_status(10107, 'S10_1678', 'Cancelled')

  # Operación 3: Consulta compleja - Ventas grandes por país
  def get_large_sales_by_country(country):
      filter = "SingleColumnValueFilter('customer', 'country', =, 'binary:%s')" % country
      results = []
      
      for key, data in table.scan(filter=filter, columns=[b'sales:total']):
          total_sale = float(data[b'sales:total'])
          if total_sale > 5000:
              results.append({
                  'row_key': key.decode(),
                  'total_sale': total_sale
              })
      return results

  large_sales_usa = get_large_sales_by_country('USA')
  print("\nVentas grandes en USA:")
  for sale in large_sales_usa:
      print(f"Orden: {sale['row_key']} - Total: ${sale['total_sale']:.2f}")

  # 7. Análisis de Datos -----------------------------------------------------------

  # Convertir datos HBase a DataFrame para análisis
  rows = []
  for key, data in table.scan():
      row = {
          'order_id': key.decode(),
          'date': data.get(b'order_info:order_date', b'').decode(),
          'status': data.get(b'order_info:status', b'').decode(),
          'product_line': data.get(b'product:line', b'').decode(),
          'country': data.get(b'customer:country', b'').decode(),
          'quantity': float(data.get(b'sales:quantity', b'0').decode()),
          'total': float(data.get(b'sales:total', b'0').decode()),
          'deal_size': data.get(b'sales:deal_size', b'').decode()
      }
      rows.append(row)

  analysis_df = pd.DataFrame(rows)

  # Métricas clave
  metrics = {
      'total_ventas': analysis_df['total'].sum(),
      'venta_promedio': analysis_df['total'].mean(),
      'ordenes_por_pais': analysis_df['country'].value_counts().head(5),
      'distribucion_linea_producto': analysis_df['product_line'].value_counts(),
      'tamano_transaccion_promedio': analysis_df.groupby('deal_size')['total'].mean()
  }

  # 8. Visualización de Resultados
  plt.figure(figsize=(12, 6))

  # Gráfico 1: Ventas por línea de producto
  analysis_df.groupby('product_line')['total'].sum().sort_values().plot(
      kind='barh', 
      title='Ventas Totales por Línea de Producto',
      color='skyblue'
  )
  plt.xlabel('Total de Ventas ($)')
  plt.ylabel('Línea de Producto')
  plt.grid(axis='x')

  plt.tight_layout()
  plt.show()

  # 9. Resultados del Análisis
  print("\nResumen Analítico:")
  print(f"1. Ventas totales: ${metrics['total_ventas']:,.2f}")
  print(f"2. Venta promedio por orden: ${metrics['venta_promedio']:,.2f}")
  print("\n3. Top 5 países por número de órdenes:")
  print(metrics['ordenes_por_pais'])
  print("\n4. Distribución por línea de producto:")
  print(metrics['distribucion_linea_producto'])
  print("\n5. Tamaño promedio de transacción:")
  print(metrics['tamano_transaccion_promedio'])
  
except Exception as e:
  print(f"Error: {str(e)}")
finally:
  #10. Cerrar la conexión
  connection.close()
  print("Conexión cerrada con HBase")

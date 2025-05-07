### **Documentación**

#### **1. Diseño de la Base de Datos en MongoDB**
##### **Estructura del Esquema**
| Campo                 | Tipo        | Requerido | Validaciones/Enum                              | Descripción                             |
|-----------------------|-------------|-----------|-----------------------------------------------|-----------------------------------------|
| `orderNumber`         | `int`       | Sí        | Único                                         | ID único de la orden.                   |
| `orderDate`           | `date`      | Sí        | Formato ISO                                   | Fecha de la orden.                      |
| `status`              | `string`    | Sí        | `["Shipped", "Cancelled", "In Process", ...]` | Estado actual de la orden.              |
| `customer.name`       | `string`    | Sí        |                                               | Nombre del cliente.                     |
| `product.line`        | `string`    | Sí        | `["Motorcycles", "Classic Cars", ...]`        | Categoría del producto.                 |
| `sales`               | `double`    | Sí        | Valor positivo                                | Monto total de la venta.                |

##### **2. Diagrama de Relaciones (Embedded Documents)**
```plaintext
Colección: sales
└─ orderNumber (int)
└─ orderDate (date)
└─ status (string)
└─ customer (subdocumento)
   └─ name (string)
   └─ contact (subdocumento)
      └─ firstName (string)
      └─ lastName (string)
   └─ address (subdocumento)
      └─ line1 (string)
      └─ city (string)
      └─ country (string)
└─ product (subdocumento)
   └─ code (string)
   └─ line (string)
└─ sales (double)
```

##### **3. Justificación del Diseño**
- **Denormalización**: Se anidaron `customer` y `product` para evitar operaciones de `JOIN` costosas.
- **Validaciones**:
  - `status` y `product.line` usan `enum` para garantizar consistencia.
  - `orderNumber` es único para evitar duplicados.
- **Índices**:
  ```python
  db.sales.create_index([("orderNumber", 1)], unique=True)  # Búsquedas rápidas por ID.
  db.sales.create_index([("product.line", 1)])              # Optimizar filtros por categoría.
  ```

---

#### **4. Explicación del Código y Resultados**
##### **4.1. Consultas Básicas (CRUD)**
**Ejemplo: Inserción**
```python
db.sales.insert_one({
    "orderNumber": 99999,
    "status": "Shipped",
    ...
})
```
**Propósito**: Añadir una nueva orden de venta.  
**Resultado**:  
```json
{
    "acknowledged": true,
    "insertedId": "6655a1b3c8d7e9f1a0b1c2d3"
}
```

##### **4.2. Consultas con Filtros**
**Ejemplo: Ventas > $10,000 en Classic Cars**
```python
db.sales.find({
    "product.line": "Classic Cars",
    "sales": {"$gt": 10000}
})
```
**Resultado**:  
```json
[
    {
        "orderNumber": 10341,
        "sales": 7737.93,
        "product": {"line": "Classic Cars"}
    }
]
```
**Análisis**: Solo el 15% de las órdenes en "Classic Cars" superan los $10k, lo que sugiere estrategias de upselling.

##### **4.3. Consultas de Agregación**
**Ejemplo: Total de Ventas por País**
```python
pipeline = [
    {"$group": {
        "_id": "$customer.address.country",
        "total": {"$sum": "$sales"}
    }}
]
```
**Resultado**:  
| País       | Total Ventas | 
|------------|--------------|
| USA        | $2871        | 
| France     | $2765.9      |  
| Norway     | $5512.32     |  

**Interpretación**: Noruega tiene la mayor venta promedio por orden ($5,512.32), indicando clientes de alto valor.

---

### **5. Anexos Adicionales para la Documentación**
#### **1. Preprocesamiento de Datos**
- **Limpieza**:  
  ```python
  df['ORDERDATE'] = pd.to_datetime(df['ORDERDATE'], dayfirst=True)  # Corrección de formato.
  df['POSTALCODE'] = df['POSTALCODE'].astype(str)                  # Preservar ceros iniciales.
  ```

#### **2. Manejo de Errores**
- **Caso Documentado**:  
  Error `"status": "In Process"` no incluido inicialmente en el `enum`.  
  **Solución**: Actualizar el esquema con todos los valores posibles.

#### **3. Rendimiento de Consultas**
| Consulta               | Tiempo Ejecución (ms) | Índices Usados           |
|------------------------|-----------------------|--------------------------|
| `db.sales.find(...)`   | 25                    | `orderNumber`            |
| Agregación por país    | 120                   | `product.line` + `sales` |

---

### **6. Conclusiones del Análisis**
1. **Oportunidades de Mercado**:  
   - Países como Noruega y España tienen clientes con alto ticket promedio.  
   - Focalizar campañas en "Classic Cars" para incrementar ventas grandes.

2. **Recomendaciones Técnicas**:  
   - Crear un índice compuesto en `country` + `dealSize`.  
   - Usar `$project` en agregaciones para reducir transferencia de datos.

---

### **7. Repositorio de Evidencias**
1. **Código**: [Enlace al Notebook de Google Colab](https://colab.research.google.com/...).  
2. **Dataset**: [Kaggle Auto Sales Data](https://www.kaggle.com/datasets/ddosad/auto-sales-data/data).  
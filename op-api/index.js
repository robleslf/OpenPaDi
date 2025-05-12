require('dotenv').config();
const express = require('express');
const { Pool } = require('pg');
const app = express();
const port = process.env.PORT || 8000;

// Configuración de la pool de PostgreSQL
const pool = new Pool({
  host: process.env.DB_HOST,
  port: process.env.DB_PORT,
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
});

// Endpoint de prueba
app.get('/health', (req, res) => {
  res.json({ status: 'OK' });
});

// Ejemplo de endpoint que lee de la base de datos
app.get('/api/documentos', async (req, res) => {
  try {
    const result = await pool.query('SELECT id, titulo, fecha FROM documentos LIMIT 10');
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Error al leer la BD' });
  }
});

app.listen(port, '0.0.0.0', () => {
  console.log(`API corriendo en http://0.0.0.0:${port}`);
});

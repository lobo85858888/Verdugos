from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

DATABASE = 'vcf_database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Crear las tablas si no existen
def init_db():
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS contadores (
                rango TEXT PRIMARY KEY,
                contador INTEGER NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                accion TEXT NOT NULL,
                nombre TEXT NOT NULL,
                fecha_hora TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS personas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                rango TEXT NOT NULL,
                codigo TEXT NOT NULL,
                persona_que_metio TEXT NOT NULL
            )
        ''')
        conn.commit()

init_db()

# Diccionario de rangos
rangos = {
    "escolta": "E",
    "vendedor": "V",
    "sicario": "A",
    "jefe_sicario": "M",
    "encargado_en_punto": "J",
    "lugar_teniente": "L",
    "subjefe": "Z",
    "jefe": "R",
    "asociado": "P",
}

def asignar_codigo_por_rango(rango):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('SELECT contador FROM contadores WHERE rango = ?', (rango,))
        result = c.fetchone()
        if result:
            contador = result['contador'] + 1
        else:
            contador = 1
        c.execute('INSERT OR REPLACE INTO contadores (rango, contador) VALUES (?, ?)', (rango, contador))
        conn.commit()
    return f"{rangos[rango]}{contador}"

def obtener_fecha_hora_actual():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def obtener_personas_desde_bd():
    with get_db() as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM personas')
        return c.fetchall()

@app.route('/personas')
def mostrar_personas():
    personas = obtener_personas_desde_bd()
    return render_template('personas.html', personas=personas)

@app.route('/')
def index():
    return redirect(url_for('mostrar_personas'))

@app.route('/reclutar', methods=['GET', 'POST'])
def reclutar():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        rango = request.form.get('rango')
        persona_que_metio = request.form.get('persona_que_metio')

        nuevo_codigo = asignar_codigo_por_rango(rango)

        with get_db() as conn:
            c = conn.cursor()
            c.execute('INSERT INTO personas (nombre, rango, codigo, persona_que_metio) VALUES (?, ?, ?, ?)',
                      (nombre, rango, nuevo_codigo, persona_que_metio))
            conn.commit()

            accion = f'Reclutada Persona: {nombre}'
            fecha_hora = obtener_fecha_hora_actual()
            c.execute('INSERT INTO registros (accion, nombre, fecha_hora) VALUES (?, ?, ?)',
                      (accion, persona_que_metio, fecha_hora))
            conn.commit()

        flash('Persona reclutada con éxito!')
        return redirect(url_for('mostrar_personas'))

    return render_template('reclutar.html', rangos=rangos)

@app.route('/pkt', methods=['GET', 'POST'])
def pkt():
    personas = obtener_personas_desde_bd()
    if request.method == 'POST':
        nombre_eliminar = request.form.get('nombre_eliminar')
        nombre_eliminador = request.form.get('nombre_eliminador')
        motivos = request.form.get('motivos')

        with get_db() as conn:
            c = conn.cursor()
            c.execute('DELETE FROM personas WHERE nombre=?', (nombre_eliminar,))
            conn.commit()

            accion = f'Eliminada Persona: {nombre_eliminar} - Motivos: {motivos}'
            fecha_hora = obtener_fecha_hora_actual()
            c.execute('INSERT INTO registros (accion, nombre, fecha_hora) VALUES (?, ?, ?)',
                      (accion, nombre_eliminador, fecha_hora))
            conn.commit()

        flash('Persona eliminada con éxito!')
        return redirect(url_for('mostrar_personas'))

    return render_template('pkt.html', personas=personas)

@app.route('/registro')
def registro():
    with get_db() as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM registros')
        registros = c.fetchall()
    return render_template('registro.html', registros=registros)

@app.route('/ascensos', methods=['GET', 'POST'])
def ascensos():
    if request.method == 'POST':
        nombre_ascensor = request.form.get('nombre_ascensor')
        nombre_ascendido = request.form.get('nombre_ascendido')
        nuevo_rango = request.form.get('nuevo_rango')

        with get_db() as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM personas WHERE nombre=?', (nombre_ascendido,))
            detalles_persona = c.fetchone()

            if detalles_persona:
                nuevo_codigo = asignar_codigo_por_rango(nuevo_rango)
                c.execute('UPDATE personas SET rango=?, codigo=? WHERE nombre=?',
                          (nuevo_rango, nuevo_codigo, nombre_ascendido))
                conn.commit()

                accion = f'Ascendida Persona: {nombre_ascendido} a {nuevo_rango}'
                fecha_hora = obtener_fecha_hora_actual()
                c.execute('INSERT INTO registros (accion, nombre, fecha_hora) VALUES (?, ?, ?)',
                          (accion, nombre_ascensor, fecha_hora))
                conn.commit()

        flash('Persona ascendida con éxito!')
        return redirect(url_for('mostrar_personas'))

    personas = obtener_personas_desde_bd()
    return render_template('ascensos.html', personas=personas, rangos=rangos)

if __name__ == '__main__':
    app.run(debug=True)

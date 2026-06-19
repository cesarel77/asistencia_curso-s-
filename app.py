# app.py --- Proyecto Asistencia de Curso(s)
# Asistencia Flask + MySQL - TNS Informática - Programación II

import mysql.connector
from flask import Flask, render_template, jsonify, request, abort, g

app = Flask(__name__)

# ================================================================
# CONFIGURACIÓN DE LA BASE DE DATOS
# ================================================================
DB_CONFIG = {
    'host':     '127.0.0.1',
    'port':     3306,
    'user':     'root',
    'password': '',
    'database': 'asistencia_cursos',
    'charset':  'utf8mb4',
}

# ================================================================
# HELPERS DE CONEXIÓN
# ================================================================
def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(**DB_CONFIG)
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def query(sql, params=(), one=False):
    db     = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(sql, params)
    result = cursor.fetchone() if one else cursor.fetchall()
    cursor.close()
    return result

def execute(sql, params=()):
    db     = get_db()
    cursor = db.cursor()
    cursor.execute(sql, params)
    db.commit()
    lastrowid = cursor.lastrowid
    cursor.close()
    return lastrowid

# ================================================================
# CONSTANTES
# ================================================================
ESTADOS_ASISTENCIA_VALIDOS = ('PRESENTE', 'AUSENTE', 'TARDE', 'JUSTIFICADO')
BLOQUES_VALIDOS = ('1° BLOQUE', '2° BLOQUE', '3° BLOQUE', '4° BLOQUE', '5° BLOQUE')

# ================================================================
# RUTAS HTML
# ================================================================
@app.route('/')
def inicio():
    total_estudiantes = query('SELECT COUNT(*) AS total FROM estudiantes', one=True)['total']
    total_cursos = query('SELECT COUNT(*) AS total FROM cursos', one=True)['total']
    total_profesores = query('SELECT COUNT(*) AS total FROM profesores', one=True)['total']
    total_asistencias = query('SELECT COUNT(*) AS total FROM asistencias', one=True)['total']
    total_sesiones = query('SELECT COUNT(*) AS total FROM sesiones_clase', one=True)['total']
    total_periodos = query('SELECT COUNT(*) AS total FROM periodos_academicos', one=True)['total']
    total_justificaciones = query('SELECT COUNT(*) AS total FROM justificaciones', one=True)['total']
    
    return render_template('inicio.html', 
                         titulo='Inicio - Asistencia de Cursos',
                         total_estudiantes=total_estudiantes,
                         total_cursos=total_cursos,
                         total_profesores=total_profesores,
                         total_asistencias=total_asistencias,
                         total_sesiones=total_sesiones,
                         total_periodos=total_periodos,
                         total_justificaciones=total_justificaciones)

# --- RUTAS HTML: ESTUDIANTES ---
@app.route('/estudiantes/')
def lista_estudiantes_html():
    estudiantes = query(
        'SELECT e.*, c.nombre_curso AS curso_nombre'
        ' FROM estudiantes e'
        ' LEFT JOIN cursos c ON e.id_curso = c.id'
        ' ORDER BY e.apellido, e.nombre'
    )
    for e in estudiantes:
        if e.get('fecha_nacimiento'):
            e['fecha_nacimiento'] = str(e['fecha_nacimiento'])
    return render_template('estudiantes/lista.html', titulo='Estudiantes', estudiantes=estudiantes)

@app.route('/estudiantes/<int:id>')
def detalle_estudiante_html(id):
    estudiante = query(
        'SELECT e.*, c.nombre_curso AS curso_nombre'
        ' FROM estudiantes e'
        ' LEFT JOIN cursos c ON e.id_curso = c.id'
        ' WHERE e.id = %s',
        (id,), one=True
    )
    if estudiante is None:
        abort(404)
    if estudiante.get('fecha_nacimiento'):
        estudiante['fecha_nacimiento'] = str(estudiante['fecha_nacimiento'])
    return render_template('estudiantes/detalle.html', titulo=estudiante['nombre'], estudiante=estudiante)

@app.route('/estudiantes/crear')
def crear_estudiante_html():
    cursos = query('SELECT * FROM cursos ORDER BY nombre_curso')
    return render_template('estudiantes/crear.html', titulo='Crear Estudiante', cursos=cursos)

@app.route('/estudiantes/<int:id>/editar')
def editar_estudiante_html(id):
    estudiante = query('SELECT * FROM estudiantes WHERE id = %s', (id,), one=True)
    if estudiante is None:
        abort(404)
    cursos = query('SELECT * FROM cursos ORDER BY nombre_curso')
    return render_template('estudiantes/editar.html', titulo='Editar Estudiante', estudiante=estudiante, cursos=cursos)

@app.route('/estudiantes/<int:id>/eliminar')
def eliminar_estudiante_html(id):
    estudiante = query('SELECT * FROM estudiantes WHERE id = %s', (id,), one=True)
    if estudiante is None:
        abort(404)
    return render_template('estudiantes/eliminar.html', titulo='Eliminar Estudiante', estudiante=estudiante)

# --- RUTAS HTML: CURSOS ---
@app.route('/cursos/')
def lista_cursos_html():
    cursos = query(
        'SELECT c.*, CONCAT(p.nombre, " ", p.apellido) AS profesor_nombre'
        ' FROM cursos c'
        ' LEFT JOIN profesores p ON c.id_profesor_jefe = p.id'
        ' ORDER BY c.nivel, c.letra'
    )
    return render_template('cursos/lista.html', titulo='Cursos', cursos=cursos)

@app.route('/cursos/<int:id>')
def detalle_curso_html(id):
    curso = query(
        'SELECT c.*, CONCAT(p.nombre, " ", p.apellido) AS profesor_nombre'
        ' FROM cursos c'
        ' LEFT JOIN profesores p ON c.id_profesor_jefe = p.id'
        ' WHERE c.id = %s',
        (id,), one=True
    )
    if curso is None:
        abort(404)
    return render_template('cursos/detalle.html', titulo=curso['nombre_curso'], curso=curso)

@app.route('/cursos/crear')
def crear_curso_html():
    profesores = query('SELECT * FROM profesores ORDER BY apellido, nombre')
    return render_template('cursos/crear.html', titulo='Crear Curso', profesores=profesores)

@app.route('/cursos/<int:id>/editar')
def editar_curso_html(id):
    curso = query('SELECT * FROM cursos WHERE id = %s', (id,), one=True)
    if curso is None:
        abort(404)
    profesores = query('SELECT * FROM profesores ORDER BY apellido, nombre')
    return render_template('cursos/editar.html', titulo='Editar Curso', curso=curso, profesores=profesores)

@app.route('/cursos/<int:id>/asignar_profesor')
def asignar_profesor_html(id):
    curso = query('SELECT * FROM cursos WHERE id = %s', (id,), one=True)
    if curso is None:
        abort(404)
    profesores = query('SELECT * FROM profesores ORDER BY apellido, nombre')
    return render_template('cursos/asignar_profesor.html', titulo='Asignar Profesor Jefe', curso=curso, profesores=profesores)

# --- RUTAS HTML: PROFESORES ---
@app.route('/profesores/')
def lista_profesores_html():
    profesores = query(
        'SELECT p.*, COUNT(c.id) AS total_cursos'
        ' FROM profesores p'
        ' LEFT JOIN cursos c ON c.id_profesor_jefe = p.id'
        ' GROUP BY p.id'
        ' ORDER BY p.apellido, p.nombre'
    )
    return render_template('profesores/lista.html', titulo='Profesores', profesores=profesores)

@app.route('/profesores/<int:id>')
def detalle_profesor_html(id):
    profesor = query('SELECT * FROM profesores WHERE id = %s', (id,), one=True)
    if profesor is None:
        abort(404)
    cursos = query(
        'SELECT * FROM cursos WHERE id_profesor_jefe = %s ORDER BY nombre_curso',
        (id,)
    )
    return render_template('profesores/detalle.html', titulo=profesor['nombre'], profesor=profesor, cursos=cursos)

@app.route('/profesores/crear')
def crear_profesor_html():
    return render_template('profesores/crear.html', titulo='Crear Profesor')

@app.route('/profesores/<int:id>/editar')
def editar_profesor_html(id):
    profesor = query('SELECT * FROM profesores WHERE id = %s', (id,), one=True)
    if profesor is None:
        abort(404)
    return render_template('profesores/editar.html', titulo='Editar Profesor', profesor=profesor)

@app.route('/profesores/<int:id>/eliminar')
def eliminar_profesor_html(id):
    profesor = query('SELECT * FROM profesores WHERE id = %s', (id,), one=True)
    if profesor is None:
        abort(404)
    return render_template('profesores/eliminar.html', titulo='Eliminar Profesor', profesor=profesor)

# --- RUTAS HTML: ASISTENCIAS ---
@app.route('/asistencias/')
def lista_asistencias_html():
    asistencias = query(
        'SELECT a.*, CONCAT(e.nombre, " ", e.apellido) AS estudiante_nombre,'
        '       s.fecha AS sesion_fecha'
        ' FROM asistencias a'
        ' JOIN estudiantes e ON a.id_estudiante = e.id'
        ' JOIN sesiones_clase s ON a.id_sesion = s.id'
        ' ORDER BY s.fecha DESC, a.id DESC'
        ' LIMIT 100'
    )
    for a in asistencias:
        if a.get('hora_registro'):
            a['hora_registro'] = str(a['hora_registro'])
    cursos = query('SELECT * FROM cursos ORDER BY nombre_curso')
    return render_template('asistencias/lista.html', titulo='Asistencias', asistencias=asistencias, cursos=cursos)

@app.route('/asistencias/registrar')
def registrar_asistencia_html():
    cursos = query('SELECT * FROM cursos ORDER BY nombre_curso')
    return render_template('asistencias/registrar.html', titulo='Registrar Asistencia', cursos=cursos)

@app.route('/asistencias/registrar_individual')
def registrar_asistencia_individual_html():
    estudiantes = query(
        'SELECT e.*, c.nombre_curso AS curso_nombre'
        ' FROM estudiantes e'
        ' JOIN cursos c ON e.id_curso = c.id'
        ' ORDER BY e.apellido, e.nombre'
    )
    sesiones = query(
        'SELECT s.*, c.nombre_curso AS curso_nombre'
        ' FROM sesiones_clase s'
        ' JOIN cursos c ON s.id_curso = c.id'
        ' ORDER BY s.fecha DESC'
        ' LIMIT 50'
    )
    return render_template('asistencias/registrar_individual.html', titulo='Registrar Asistencia Individual', estudiantes=estudiantes, sesiones=sesiones)

@app.route('/asistencias/registrar_masiva')
def registrar_asistencia_masiva_html():
    cursos = query('SELECT * FROM cursos ORDER BY nombre_curso')
    return render_template('asistencias/registrar_masiva.html', titulo='Registro Masivo de Asistencia', cursos=cursos)

@app.route('/asistencias/curso/<int:id_curso>')
def lista_asistencias_curso_html(id_curso):
    curso = query('SELECT * FROM cursos WHERE id = %s', (id_curso,), one=True)
    if curso is None:
        abort(404)
    asistencias = query(
        'SELECT a.*, CONCAT(e.nombre, " ", e.apellido) AS estudiante_nombre,'
        '       s.fecha AS sesion_fecha'
        ' FROM asistencias a'
        ' JOIN estudiantes e ON a.id_estudiante = e.id'
        ' JOIN sesiones_clase s ON a.id_sesion = s.id'
        ' WHERE s.id_curso = %s'
        ' ORDER BY s.fecha DESC, a.id DESC',
        (id_curso,)
    )
    for a in asistencias:
        if a.get('hora_registro'):
            a['hora_registro'] = str(a['hora_registro'])
    return render_template('asistencias/lista_curso.html', titulo=f'Asistencias - {curso["nombre_curso"]}', curso=curso, asistencias=asistencias)

@app.route('/asistencias/estudiante/<int:id_estudiante>')
def historial_asistencia_estudiante_html(id_estudiante):
    estudiante = query('SELECT * FROM estudiantes WHERE id = %s', (id_estudiante,), one=True)
    if estudiante is None:
        abort(404)
    asistencias = query(
        'SELECT a.*, s.fecha AS sesion_fecha, s.hora_inicio, c.nombre_curso AS curso_nombre'
        ' FROM asistencias a'
        ' JOIN sesiones_clase s ON a.id_sesion = s.id'
        ' JOIN cursos c ON s.id_curso = c.id'
        ' WHERE a.id_estudiante = %s'
        ' ORDER BY s.fecha DESC',
        (id_estudiante,)
    )
    for a in asistencias:
        if a.get('hora_registro'):
            a['hora_registro'] = str(a['hora_registro'])
    # Estadísticas
    total = len(asistencias)
    presentes = sum(1 for a in asistencias if a['estado'] == 'PRESENTE')
    ausentes = sum(1 for a in asistencias if a['estado'] == 'AUSENTE')
    tardes = sum(1 for a in asistencias if a['estado'] == 'TARDE')
    justificados = sum(1 for a in asistencias if a['estado'] == 'JUSTIFICADO')
    return render_template('asistencias/historial_estudiante.html', 
                          titulo=f'Historial - {estudiante["nombre"]} {estudiante["apellido"]}',
                          estudiante=estudiante, asistencias=asistencias,
                          total=total, presentes=presentes, ausentes=ausentes,
                          tardes=tardes, justificados=justificados)

@app.route('/asistencias/sesion/<int:id_sesion>')
def lista_asistencias_sesion_html(id_sesion):
    sesion = query(
        'SELECT s.*, c.nombre_curso AS curso_nombre'
        ' FROM sesiones_clase s'
        ' JOIN cursos c ON s.id_curso = c.id'
        ' WHERE s.id = %s',
        (id_sesion,), one=True
    )
    if sesion is None:
        abort(404)
    asistencias = query(
        'SELECT a.*, CONCAT(e.nombre, " ", e.apellido) AS estudiante_nombre'
        ' FROM asistencias a'
        ' JOIN estudiantes e ON a.id_estudiante = e.id'
        ' WHERE a.id_sesion = %s'
        ' ORDER BY e.apellido, e.nombre',
        (id_sesion,)
    )
    for a in asistencias:
        if a.get('hora_registro'):
            a['hora_registro'] = str(a['hora_registro'])
    return render_template('asistencias/lista_sesion.html', titulo=f'Sesión - {sesion["curso_nombre"]}', 
                          sesion=sesion, asistencias=asistencias)

@app.route('/asistencias/<int:id>/editar')
def editar_asistencia_html(id):
    asistencia = query(
        'SELECT a.*, CONCAT(e.nombre, " ", e.apellido) AS estudiante_nombre'
        ' FROM asistencias a'
        ' JOIN estudiantes e ON a.id_estudiante = e.id'
        ' WHERE a.id = %s',
        (id,), one=True
    )
    if asistencia is None:
        abort(404)
    return render_template('asistencias/editar.html', titulo='Editar Asistencia', asistencia=asistencia)

# --- RUTAS HTML: SESIONES ---
@app.route('/sesiones/')
def lista_sesiones_html():
    sesiones = query(
        'SELECT s.*, c.nombre_curso AS curso_nombre,'
        '       CONCAT(p.nombre, " ", p.apellido) AS profesor_nombre'
        ' FROM sesiones_clase s'
        ' JOIN cursos c ON s.id_curso = c.id'
        ' JOIN profesores p ON s.id_profesor = p.id'
        ' ORDER BY s.fecha DESC, s.hora_inicio'
        ' LIMIT 100'
    )
    return render_template('sesiones/lista.html', titulo='Sesiones de Clase', sesiones=sesiones)

@app.route('/sesiones/<int:id>')
def detalle_sesion_html(id):
    sesion = query(
        'SELECT s.*, c.nombre_curso AS curso_nombre,'
        '       CONCAT(p.nombre, " ", p.apellido) AS profesor_nombre'
        ' FROM sesiones_clase s'
        ' JOIN cursos c ON s.id_curso = c.id'
        ' JOIN profesores p ON s.id_profesor = p.id'
        ' WHERE s.id = %s',
        (id,), one=True
    )
    if sesion is None:
        abort(404)
    total_asistencias = query('SELECT COUNT(*) AS total FROM asistencias WHERE id_sesion = %s', (id,), one=True)
    return render_template('sesiones/detalle.html', titulo=f'Sesión {sesion["id"]}', sesion=sesion, total_asistencias=total_asistencias['total'])

@app.route('/sesiones/crear')
def crear_sesion_html():
    cursos = query('SELECT * FROM cursos ORDER BY nombre_curso')
    profesores = query('SELECT * FROM profesores ORDER BY apellido, nombre')
    return render_template('sesiones/crear.html', titulo='Crear Sesión', cursos=cursos, profesores=profesores)

@app.route('/sesiones/<int:id>/editar')
def editar_sesion_html(id):
    sesion = query('SELECT * FROM sesiones_clase WHERE id = %s', (id,), one=True)
    if sesion is None:
        abort(404)
    cursos = query('SELECT * FROM cursos ORDER BY nombre_curso')
    profesores = query('SELECT * FROM profesores ORDER BY apellido, nombre')
    return render_template('sesiones/editar.html', titulo='Editar Sesión', sesion=sesion, cursos=cursos, profesores=profesores)

@app.route('/sesiones/curso/<int:id_curso>')
def lista_sesiones_curso_html(id_curso):
    curso = query('SELECT * FROM cursos WHERE id = %s', (id_curso,), one=True)
    if curso is None:
        abort(404)
    sesiones = query(
        'SELECT s.*, CONCAT(p.nombre, " ", p.apellido) AS profesor_nombre'
        ' FROM sesiones_clase s'
        ' JOIN profesores p ON s.id_profesor = p.id'
        ' WHERE s.id_curso = %s'
        ' ORDER BY s.fecha DESC, s.hora_inicio',
        (id_curso,)
    )
    return render_template('sesiones/lista_curso.html', titulo=f'Sesiones - {curso["nombre_curso"]}', curso=curso, sesiones=sesiones)

@app.route('/sesiones/<int:id>/cerrar')
def cerrar_sesion_html(id):
    sesion = query(
        'SELECT s.*, c.nombre_curso AS curso_nombre'
        ' FROM sesiones_clase s'
        ' JOIN cursos c ON s.id_curso = c.id'
        ' WHERE s.id = %s',
        (id,), one=True
    )
    if sesion is None:
        abort(404)
    return render_template('sesiones/cerrar.html', titulo='Cerrar Sesión', sesion=sesion)

# --- RUTAS HTML: PERIODOS ACADÉMICOS ---
@app.route('/periodos/')
def lista_periodos_html():
    periodos = query('SELECT * FROM periodos_academicos ORDER BY fecha_inicio DESC')
    for p in periodos:
        if p.get('fecha_inicio'):
            p['fecha_inicio'] = str(p['fecha_inicio'])
        if p.get('fecha_fin'):
            p['fecha_fin'] = str(p['fecha_fin'])
    return render_template('periodos/lista.html', titulo='Períodos Académicos', periodos=periodos)

@app.route('/periodos/<int:id>')
def detalle_periodo_html(id):
    periodo = query('SELECT * FROM periodos_academicos WHERE id = %s', (id,), one=True)
    if periodo is None:
        abort(404)
    if periodo.get('fecha_inicio'):
        periodo['fecha_inicio'] = str(periodo['fecha_inicio'])
    if periodo.get('fecha_fin'):
        periodo['fecha_fin'] = str(periodo['fecha_fin'])
    return render_template('periodos/detalle.html', titulo=f'Período {periodo["id"]}', periodo=periodo)

@app.route('/periodos/crear')
def crear_periodo_html():
    return render_template('periodos/crear.html', titulo='Crear Período Académico')

@app.route('/periodos/<int:id>/editar')
def editar_periodo_html(id):
    periodo = query('SELECT * FROM periodos_academicos WHERE id = %s', (id,), one=True)
    if periodo is None:
        abort(404)
    return render_template('periodos/editar.html', titulo='Editar Período', periodo=periodo)

@app.route('/periodos/<int:id>/activar')
def activar_periodo_html(id):
    periodo = query('SELECT * FROM periodos_academicos WHERE id = %s', (id,), one=True)
    if periodo is None:
        abort(404)
    return render_template('periodos/activar.html', titulo='Activar Período', periodo=periodo)

# --- RUTAS HTML: JUSTIFICACIONES ---
@app.route('/justificaciones/')
def lista_justificaciones_html():
    justificaciones = query(
        'SELECT j.*, CONCAT(e.nombre, " ", e.apellido) AS estudiante_nombre,'
        '       a.estado AS asistencia_estado, s.fecha AS sesion_fecha'
        ' FROM justificaciones j'
        ' JOIN asistencias a ON j.id_asistencia = a.id'
        ' JOIN estudiantes e ON a.id_estudiante = e.id'
        ' JOIN sesiones_clase s ON a.id_sesion = s.id'
        ' ORDER BY j.fecha_documentacion DESC'
        ' LIMIT 100'
    )
    for j in justificaciones:
        if j.get('fecha_documentacion'):
            j['fecha_documentacion'] = str(j['fecha_documentacion'])
    return render_template('justificaciones/lista.html', titulo='Justificaciones', justificaciones=justificaciones)

@app.route('/justificaciones/crear')
def crear_justificacion_html():
    asistencias = query(
        'SELECT a.id, CONCAT(e.nombre, " ", e.apellido) AS estudiante_nombre,'
        '       s.fecha AS sesion_fecha, a.estado'
        ' FROM asistencias a'
        ' JOIN estudiantes e ON a.id_estudiante = e.id'
        ' JOIN sesiones_clase s ON a.id_sesion = s.id'
        ' ORDER BY s.fecha DESC'
        ' LIMIT 100'
    )
    return render_template('justificaciones/crear.html', titulo='Crear Justificación', asistencias=asistencias)

@app.route('/justificaciones/<int:id>')
def detalle_justificacion_html(id):
    justificacion = query(
        'SELECT j.*, CONCAT(e.nombre, " ", e.apellido) AS estudiante_nombre,'
        '       a.estado AS asistencia_estado, s.fecha AS sesion_fecha'
        ' FROM justificaciones j'
        ' JOIN asistencias a ON j.id_asistencia = a.id'
        ' JOIN estudiantes e ON a.id_estudiante = e.id'
        ' JOIN sesiones_clase s ON a.id_sesion = s.id'
        ' WHERE j.id = %s',
        (id,), one=True
    )
    if justificacion is None:
        abort(404)
    if justificacion.get('fecha_documentacion'):
        justificacion['fecha_documentacion'] = str(justificacion['fecha_documentacion'])
    return render_template('justificaciones/detalle.html', titulo='Detalle Justificación', justificacion=justificacion)

@app.route('/justificaciones/pendientes')
def justificaciones_pendientes_html():
    justificaciones = query(
        'SELECT j.*, CONCAT(e.nombre, " ", e.apellido) AS estudiante_nombre,'
        '       a.estado AS asistencia_estado'
        ' FROM justificaciones j'
        ' JOIN asistencias a ON j.id_asistencia = a.id'
        ' JOIN estudiantes e ON a.id_estudiante = e.id'
        ' WHERE j.validada = FALSE'
        ' ORDER BY j.fecha_documentacion DESC'
    )
    for j in justificaciones:
        if j.get('fecha_documentacion'):
            j['fecha_documentacion'] = str(j['fecha_documentacion'])
    return render_template('justificaciones/pendientes.html', titulo='Justificaciones Pendientes', justificaciones=justificaciones)

@app.route('/justificaciones/<int:id>/validar')
def validar_justificacion_html(id):
    justificacion = query(
        'SELECT j.*, CONCAT(e.nombre, " ", e.apellido) AS estudiante_nombre'
        ' FROM justificaciones j'
        ' JOIN asistencias a ON j.id_asistencia = a.id'
        ' JOIN estudiantes e ON a.id_estudiante = e.id'
        ' WHERE j.id = %s',
        (id,), one=True
    )
    if justificacion is None:
        abort(404)
    return render_template('justificaciones/validar.html', titulo='Validar Justificación', justificacion=justificacion)

@app.route('/justificaciones/<int:id>/editar')
def editar_justificacion_html(id):
    justificacion = query('SELECT * FROM justificaciones WHERE id = %s', (id,), one=True)
    if justificacion is None:
        abort(404)
    return render_template('justificaciones/editar.html', titulo='Editar Justificación', justificacion=justificacion)

@app.route('/justificaciones/<int:id>/eliminar')
def eliminar_justificacion_html(id):
    justificacion = query('SELECT * FROM justificaciones WHERE id = %s', (id,), one=True)
    if justificacion is None:
        abort(404)
    return render_template('justificaciones/eliminar.html', titulo='Eliminar Justificación', justificacion=justificacion)


# ================================================================
# RUTAS API — ESTUDIANTES
# ================================================================
@app.route('/api/estudiantes/', methods=['GET', 'POST'])
def api_estudiantes():
    if request.method == 'POST':
        datos = request.get_json()
        if not datos:
            return jsonify({'error': 'El cuerpo debe ser JSON válido'}), 400

        nombre = datos.get('nombre', '').strip()
        apellido = datos.get('apellido', '').strip()
        rut = datos.get('rut', '').strip()
        email = datos.get('email', '').strip()
        fecha_nacimiento = datos.get('fecha_nacimiento')
        id_curso = datos.get('id_curso')

        # Validaciones
        if not nombre:
            return jsonify({'error': 'El campo nombre es obligatorio'}), 400
        if len(nombre) > 100:
            return jsonify({'error': 'El nombre no puede superar los 100 caracteres'}), 400
        if not apellido:
            return jsonify({'error': 'El campo apellido es obligatorio'}), 400
        if len(apellido) > 100:
            return jsonify({'error': 'El apellido no puede superar los 100 caracteres'}), 400
        if not rut:
            return jsonify({'error': 'El campo RUT es obligatorio'}), 400
        if len(rut) > 12:
            return jsonify({'error': 'El RUT no puede superar los 12 caracteres'}), 400
        if not email:
            return jsonify({'error': 'El campo email es obligatorio'}), 400
        if len(email) > 200:
            return jsonify({'error': 'El email no puede superar los 200 caracteres'}), 400
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'Formato de email inválido. Debe ser usuario@dominio.com'}), 400

        # Validar que el curso existe
        if id_curso is not None:
            curso = query('SELECT id FROM cursos WHERE id=%s', (id_curso,), one=True)
            if curso is None:
                return jsonify({'error': f'El curso con ID {id_curso} no existe'}), 400

        nuevo_id = execute(
            'INSERT INTO estudiantes (nombre, apellido, rut, email, fecha_nacimiento, id_curso)'
            ' VALUES (%s, %s, %s, %s, %s, %s)',
            (nombre, apellido, rut, email, fecha_nacimiento, id_curso)
        )
        nuevo = query('SELECT * FROM estudiantes WHERE id=%s', (nuevo_id,), one=True)
        if nuevo and nuevo.get('fecha_nacimiento'):
            nuevo['fecha_nacimiento'] = str(nuevo['fecha_nacimiento'])
        return jsonify({'mensaje': 'Estudiante creado exitosamente', 'id': nuevo_id, 'data': nuevo}), 201

    # GET
    estudiantes = query(
        'SELECT e.*, c.nombre_curso AS curso_nombre'
        ' FROM estudiantes e'
        ' LEFT JOIN cursos c ON e.id_curso = c.id'
        ' ORDER BY e.apellido, e.nombre'
    )
    for e in estudiantes:
        if e.get('fecha_nacimiento'):
            e['fecha_nacimiento'] = str(e['fecha_nacimiento'])
    return jsonify({'total': len(estudiantes), 'estudiantes': estudiantes})


@app.route('/api/estudiantes/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_estudiante(id):
    estudiante = query(
        'SELECT e.*, c.nombre_curso AS curso_nombre'
        ' FROM estudiantes e'
        ' LEFT JOIN cursos c ON e.id_curso = c.id'
        ' WHERE e.id = %s',
        (id,), one=True
    )
    if estudiante is None:
        return jsonify({'error': 'Estudiante no encontrado', 'id': id}), 404

    if request.method == 'GET':
        if estudiante.get('fecha_nacimiento'):
            estudiante['fecha_nacimiento'] = str(estudiante['fecha_nacimiento'])
        return jsonify(estudiante)

    if request.method == 'DELETE':
        nombre = f"{estudiante['nombre']} {estudiante['apellido']}"
        execute('DELETE FROM estudiantes WHERE id=%s', (id,))
        return jsonify({'mensaje': f'Estudiante "{nombre}" eliminado.', 'id': id})

    # PUT
    datos = request.get_json()
    if not datos:
        return jsonify({'error': 'El cuerpo debe ser JSON'}), 400

    nombre = datos.get('nombre', estudiante['nombre']).strip()
    apellido = datos.get('apellido', estudiante['apellido']).strip()
    rut = datos.get('rut', estudiante['rut']).strip()
    email = datos.get('email', estudiante['email']).strip()
    fecha_nacimiento = datos.get('fecha_nacimiento', estudiante['fecha_nacimiento'])
    id_curso = datos.get('id_curso', estudiante['id_curso'])

    if not nombre:
        return jsonify({'error': 'nombre no puede quedar vacío'}), 400
    if not apellido:
        return jsonify({'error': 'apellido no puede quedar vacío'}), 400
    if not rut:
        return jsonify({'error': 'RUT no puede quedar vacío'}), 400
    if not email:
        return jsonify({'error': 'email no puede quedar vacío'}), 400
    if '@' not in email or '.' not in email:
        return jsonify({'error': 'Formato de email inválido'}), 400

    if id_curso is not None:
        curso = query('SELECT id FROM cursos WHERE id=%s', (id_curso,), one=True)
        if curso is None:
            return jsonify({'error': f'El curso con ID {id_curso} no existe'}), 400

    execute(
        'UPDATE estudiantes'
        ' SET nombre=%s, apellido=%s, rut=%s, email=%s, fecha_nacimiento=%s, id_curso=%s'
        ' WHERE id=%s',
        (nombre, apellido, rut, email, fecha_nacimiento, id_curso, id)
    )
    actualizado = query('SELECT * FROM estudiantes WHERE id=%s', (id,), one=True)
    if actualizado and actualizado.get('fecha_nacimiento'):
        actualizado['fecha_nacimiento'] = str(actualizado['fecha_nacimiento'])
    return jsonify({'mensaje': 'Estudiante actualizado', 'estudiante': actualizado})


@app.route('/api/cursos/<int:id_curso>/estudiantes')
def api_estudiantes_por_curso(id_curso):
    curso = query('SELECT * FROM cursos WHERE id=%s', (id_curso,), one=True)
    if curso is None:
        return jsonify({'error': 'Curso no encontrado', 'id': id_curso}), 404

    estudiantes = query(
        'SELECT e.* FROM estudiantes e'
        ' WHERE e.id_curso = %s'
        ' ORDER BY e.apellido, e.nombre',
        (id_curso,)
    )
    for e in estudiantes:
        if e.get('fecha_nacimiento'):
            e['fecha_nacimiento'] = str(e['fecha_nacimiento'])
    return jsonify({
        'id_curso': id_curso,
        'curso': curso['nombre_curso'],
        'total_estudiantes': len(estudiantes),
        'estudiantes': estudiantes
    })


# ================================================================
# RUTAS API — CURSOS
# ================================================================
@app.route('/api/cursos/', methods=['GET', 'POST'])
def api_cursos():
    if request.method == 'POST':
        datos = request.get_json()
        if not datos:
            return jsonify({'error': 'El cuerpo debe ser JSON válido'}), 400

        nombre_curso = datos.get('nombre_curso', '').strip()
        nivel = datos.get('nivel', '').strip()
        letra = datos.get('letra', '').strip()
        año_lectivo = datos.get('año_lectivo')
        id_profesor_jefe = datos.get('id_profesor_jefe')

        if not nombre_curso:
            return jsonify({'error': 'El campo nombre_curso es obligatorio'}), 400
        if len(nombre_curso) > 100:
            return jsonify({'error': 'El nombre del curso no puede superar los 100 caracteres'}), 400
        if not nivel:
            return jsonify({'error': 'El campo nivel es obligatorio'}), 400
        if not letra:
            return jsonify({'error': 'El campo letra es obligatorio'}), 400
        if len(letra) > 12:
            return jsonify({'error': 'La letra no puede superar los 12 caracteres'}), 400
        if año_lectivo is None:
            return jsonify({'error': 'El campo año_lectivo es obligatorio'}), 400
        if año_lectivo < 2000 or año_lectivo > 2027:
            return jsonify({'error': 'El año lectivo debe estar entre 2000 y 2027'}), 400

        if id_profesor_jefe is not None:
            profesor = query('SELECT id FROM profesores WHERE id=%s', (id_profesor_jefe,), one=True)
            if profesor is None:
                return jsonify({'error': f'El profesor con ID {id_profesor_jefe} no existe'}), 400

        nuevo_id = execute(
            'INSERT INTO cursos (nombre_curso, nivel, letra, año_lectivo, id_profesor_jefe)'
            ' VALUES (%s, %s, %s, %s, %s)',
            (nombre_curso, nivel, letra, año_lectivo, id_profesor_jefe)
        )
        nuevo = query('SELECT * FROM cursos WHERE id=%s', (nuevo_id,), one=True)
        return jsonify({'mensaje': 'Curso creado exitosamente', 'id': nuevo_id, 'data': nuevo}), 201

    # GET
    cursos = query(
        'SELECT c.*, CONCAT(p.nombre, " ", p.apellido) AS profesor_nombre'
        ' FROM cursos c'
        ' LEFT JOIN profesores p ON c.id_profesor_jefe = p.id'
        ' ORDER BY c.nivel, c.letra'
    )
    return jsonify({'total': len(cursos), 'cursos': cursos})


@app.route('/api/cursos/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_curso(id):
    curso = query(
        'SELECT c.*, CONCAT(p.nombre, " ", p.apellido) AS profesor_nombre'
        ' FROM cursos c'
        ' LEFT JOIN profesores p ON c.id_profesor_jefe = p.id'
        ' WHERE c.id = %s',
        (id,), one=True
    )
    if curso is None:
        return jsonify({'error': 'Curso no encontrado', 'id': id}), 404

    if request.method == 'GET':
        return jsonify(curso)

    if request.method == 'DELETE':
        nombre = curso['nombre_curso']
        execute('DELETE FROM cursos WHERE id=%s', (id,))
        return jsonify({'mensaje': f'Curso "{nombre}" eliminado.', 'id': id})

    # PUT
    datos = request.get_json()
    if not datos:
        return jsonify({'error': 'El cuerpo debe ser JSON'}), 400

    nombre_curso = datos.get('nombre_curso', curso['nombre_curso']).strip()
    nivel = datos.get('nivel', curso['nivel']).strip()
    letra = datos.get('letra', curso['letra']).strip()
    año_lectivo = datos.get('año_lectivo', curso['año_lectivo'])
    id_profesor_jefe = datos.get('id_profesor_jefe', curso['id_profesor_jefe'])

    if not nombre_curso:
        return jsonify({'error': 'nombre_curso no puede quedar vacío'}), 400
    if not nivel:
        return jsonify({'error': 'nivel no puede quedar vacío'}), 400
    if not letra:
        return jsonify({'error': 'letra no puede quedar vacío'}), 400
    if año_lectivo < 2000 or año_lectivo > 2027:
        return jsonify({'error': 'El año lectivo debe estar entre 2000 y 2027'}), 400

    if id_profesor_jefe is not None:
        profesor = query('SELECT id FROM profesores WHERE id=%s', (id_profesor_jefe,), one=True)
        if profesor is None:
            return jsonify({'error': f'El profesor con ID {id_profesor_jefe} no existe'}), 400

    execute(
        'UPDATE cursos'
        ' SET nombre_curso=%s, nivel=%s, letra=%s, año_lectivo=%s, id_profesor_jefe=%s'
        ' WHERE id=%s',
        (nombre_curso, nivel, letra, año_lectivo, id_profesor_jefe, id)
    )
    actualizado = query('SELECT * FROM cursos WHERE id=%s', (id,), one=True)
    return jsonify({'mensaje': 'Curso actualizado', 'curso': actualizado})


# ================================================================
# RUTAS API — PROFESORES
# ================================================================
@app.route('/api/profesores/', methods=['GET', 'POST'])
def api_profesores():
    if request.method == 'POST':
        datos = request.get_json()
        if not datos:
            return jsonify({'error': 'El cuerpo debe ser JSON válido'}), 400

        nombre = datos.get('nombre', '').strip()
        apellido = datos.get('apellido', '').strip()
        rut = datos.get('rut', '').strip()
        email = datos.get('email', '').strip()
        especialidad = datos.get('especialidad', '').strip()

        if not nombre:
            return jsonify({'error': 'El campo nombre es obligatorio'}), 400
        if len(nombre) > 100:
            return jsonify({'error': 'El nombre no puede superar los 100 caracteres'}), 400
        if not apellido:
            return jsonify({'error': 'El campo apellido es obligatorio'}), 400
        if len(apellido) > 100:
            return jsonify({'error': 'El apellido no puede superar los 100 caracteres'}), 400
        if not rut:
            return jsonify({'error': 'El campo RUT es obligatorio'}), 400
        if len(rut) > 12:
            return jsonify({'error': 'El RUT no puede superar los 12 caracteres'}), 400
        if not email:
            return jsonify({'error': 'El campo email es obligatorio'}), 400
        if len(email) > 200:
            return jsonify({'error': 'El email no puede superar los 200 caracteres'}), 400
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'Formato de email inválido'}), 400
        if not especialidad:
            return jsonify({'error': 'El campo especialidad es obligatorio'}), 400
        if len(especialidad) > 300:
            return jsonify({'error': 'La especialidad no puede superar los 300 caracteres'}), 400

        nuevo_id = execute(
            'INSERT INTO profesores (nombre, apellido, rut, email, especialidad)'
            ' VALUES (%s, %s, %s, %s, %s)',
            (nombre, apellido, rut, email, especialidad)
        )
        nuevo = query('SELECT * FROM profesores WHERE id=%s', (nuevo_id,), one=True)
        return jsonify({'mensaje': 'Profesor creado exitosamente', 'id': nuevo_id, 'data': nuevo}), 201

    # GET
    profesores = query(
        'SELECT p.*, COUNT(c.id) AS total_cursos'
        ' FROM profesores p'
        ' LEFT JOIN cursos c ON c.id_profesor_jefe = p.id'
        ' GROUP BY p.id'
        ' ORDER BY p.apellido, p.nombre'
    )
    return jsonify({'total': len(profesores), 'profesores': profesores})


@app.route('/api/profesores/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_profesor(id):
    profesor = query('SELECT * FROM profesores WHERE id = %s', (id,), one=True)
    if profesor is None:
        return jsonify({'error': 'Profesor no encontrado', 'id': id}), 404

    if request.method == 'GET':
        return jsonify(profesor)

    if request.method == 'DELETE':
        nombre = f"{profesor['nombre']} {profesor['apellido']}"
        execute('DELETE FROM profesores WHERE id=%s', (id,))
        return jsonify({'mensaje': f'Profesor "{nombre}" eliminado.', 'id': id})

    # PUT
    datos = request.get_json()
    if not datos:
        return jsonify({'error': 'El cuerpo debe ser JSON'}), 400

    nombre = datos.get('nombre', profesor['nombre']).strip()
    apellido = datos.get('apellido', profesor['apellido']).strip()
    rut = datos.get('rut', profesor['rut']).strip()
    email = datos.get('email', profesor['email']).strip()
    especialidad = datos.get('especialidad', profesor['especialidad']).strip()

    if not nombre:
        return jsonify({'error': 'nombre no puede quedar vacío'}), 400
    if not apellido:
        return jsonify({'error': 'apellido no puede quedar vacío'}), 400
    if not rut:
        return jsonify({'error': 'RUT no puede quedar vacío'}), 400
    if not email:
        return jsonify({'error': 'email no puede quedar vacío'}), 400
    if '@' not in email or '.' not in email:
        return jsonify({'error': 'Formato de email inválido'}), 400
    if not especialidad:
        return jsonify({'error': 'especialidad no puede quedar vacía'}), 400

    execute(
        'UPDATE profesores'
        ' SET nombre=%s, apellido=%s, rut=%s, email=%s, especialidad=%s'
        ' WHERE id=%s',
        (nombre, apellido, rut, email, especialidad, id)
    )
    actualizado = query('SELECT * FROM profesores WHERE id=%s', (id,), one=True)
    return jsonify({'mensaje': 'Profesor actualizado', 'profesor': actualizado})


# ================================================================
# RUTAS API — ASISTENCIAS
# ================================================================
@app.route('/api/asistencias/', methods=['GET', 'POST'])
def api_asistencias():
    if request.method == 'POST':
        datos = request.get_json()
        if not datos:
            return jsonify({'error': 'El cuerpo debe ser JSON válido'}), 400

        id_estudiante = datos.get('id_estudiante')
        id_sesion_clase = datos.get('id_sesion_clase')
        estado = datos.get('estado', '').upper()
        observacion = datos.get('observacion', '')

        if id_estudiante is None:
            return jsonify({'error': 'El campo id_estudiante es obligatorio'}), 400
        estudiante = query('SELECT id FROM estudiantes WHERE id=%s', (id_estudiante,), one=True)
        if estudiante is None:
            return jsonify({'error': f'El estudiante con ID {id_estudiante} no existe'}), 400

        if id_sesion_clase is None:
            return jsonify({'error': 'El campo id_sesion_clase es obligatorio'}), 400
        sesion = query('SELECT id FROM sesiones_clase WHERE id=%s', (id_sesion_clase,), one=True)
        if sesion is None:
            return jsonify({'error': f'La sesión con ID {id_sesion_clase} no existe'}), 400

        if not estado:
            return jsonify({'error': 'El campo estado es obligatorio'}), 400
        if estado not in ESTADOS_ASISTENCIA_VALIDOS:
            return jsonify({'error': f'estado inválido. Opciones: {ESTADOS_ASISTENCIA_VALIDOS}'}), 400

        if len(observacion) > 500:
            return jsonify({'error': 'La observación no puede superar los 500 caracteres'}), 400

        nuevo_id = execute(
            'INSERT INTO asistencias (id_estudiante, id_sesion, estado, observacion)'
            ' VALUES (%s, %s, %s, %s)',
            (id_estudiante, id_sesion_clase, estado, observacion)
        )
        nueva = query('SELECT * FROM asistencias WHERE id=%s', (nuevo_id,), one=True)
        if nueva and nueva.get('hora_registro'):
            nueva['hora_registro'] = str(nueva['hora_registro'])
        return jsonify({'mensaje': 'Asistencia registrada exitosamente', 'id': nuevo_id, 'data': nueva}), 201

    # GET
    asistencias = query(
        'SELECT a.*, CONCAT(e.nombre, " ", e.apellido) AS estudiante_nombre,'
        '       s.fecha AS sesion_fecha'
        ' FROM asistencias a'
        ' JOIN estudiantes e ON a.id_estudiante = e.id'
        ' JOIN sesiones_clase s ON a.id_sesion = s.id'
        ' ORDER BY a.id DESC'
        ' LIMIT 100'
    )
    for a in asistencias:
        if a.get('hora_registro'):
            a['hora_registro'] = str(a['hora_registro'])
    return jsonify({'total': len(asistencias), 'asistencias': asistencias})


@app.route('/api/asistencias/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_asistencia(id):
    asistencia = query(
        'SELECT a.*, CONCAT(e.nombre, " ", e.apellido) AS estudiante_nombre'
        ' FROM asistencias a'
        ' JOIN estudiantes e ON a.id_estudiante = e.id'
        ' WHERE a.id = %s',
        (id,), one=True
    )
    if asistencia is None:
        return jsonify({'error': 'Registro de asistencia no encontrado', 'id': id}), 404

    if request.method == 'GET':
        if asistencia.get('hora_registro'):
            asistencia['hora_registro'] = str(asistencia['hora_registro'])
        return jsonify(asistencia)

    if request.method == 'DELETE':
        execute('DELETE FROM asistencias WHERE id=%s', (id,))
        return jsonify({'mensaje': f'Asistencia eliminada.', 'id': id})

    # PUT
    datos = request.get_json()
    if not datos:
        return jsonify({'error': 'El cuerpo debe ser JSON'}), 400

    estado = datos.get('estado', asistencia['estado']).upper()
    observacion = datos.get('observacion', asistencia['observacion'])

    if estado not in ESTADOS_ASISTENCIA_VALIDOS:
        return jsonify({'error': f'estado inválido. Opciones: {ESTADOS_ASISTENCIA_VALIDOS}'}), 400

    execute(
        'UPDATE asistencias'
        ' SET estado=%s, observacion=%s'
        ' WHERE id=%s',
        (estado, observacion, id)
    )
    actualizado = query('SELECT * FROM asistencias WHERE id=%s', (id,), one=True)
    if actualizado and actualizado.get('hora_registro'):
        actualizado['hora_registro'] = str(actualizado['hora_registro'])
    return jsonify({'mensaje': 'Asistencia actualizada', 'asistencia': actualizado})


@app.route('/api/estudiantes/<int:id_estudiante>/asistencias')
def api_asistencias_por_estudiante(id_estudiante):
    estudiante = query('SELECT * FROM estudiantes WHERE id=%s', (id_estudiante,), one=True)
    if estudiante is None:
        return jsonify({'error': 'Estudiante no encontrado', 'id': id_estudiante}), 404

    asistencias = query(
        'SELECT a.*, s.fecha AS sesion_fecha, c.nombre_curso AS curso_nombre'
        ' FROM asistencias a'
        ' JOIN sesiones_clase s ON a.id_sesion = s.id'
        ' JOIN cursos c ON s.id_curso = c.id'
        ' WHERE a.id_estudiante = %s'
        ' ORDER BY s.fecha DESC',
        (id_estudiante,)
    )
    for a in asistencias:
        if a.get('hora_registro'):
            a['hora_registro'] = str(a['hora_registro'])

    total = len(asistencias)
    presentes = sum(1 for a in asistencias if a['estado'] == 'PRESENTE')
    ausentes = sum(1 for a in asistencias if a['estado'] == 'AUSENTE')
    tardes = sum(1 for a in asistencias if a['estado'] == 'TARDE')
    justificados = sum(1 for a in asistencias if a['estado'] == 'JUSTIFICADO')

    return jsonify({
        'id_estudiante': id_estudiante,
        'estudiante': f"{estudiante['nombre']} {estudiante['apellido']}",
        'total': total,
        'asistencias': asistencias,
        'estadisticas': {
            'presentes': presentes,
            'ausentes': ausentes,
            'tardes': tardes,
            'justificados': justificados,
            'total': total
        }
    })


@app.route('/api/sesiones/<int:id_sesion>/asistencias')
def api_asistencias_por_sesion(id_sesion):
    sesion = query(
        'SELECT s.*, c.nombre_curso AS curso_nombre,'
        '       CONCAT(p.nombre, " ", p.apellido) AS profesor_nombre'
        ' FROM sesiones_clase s'
        ' JOIN cursos c ON s.id_curso = c.id'
        ' JOIN profesores p ON s.id_profesor = p.id'
        ' WHERE s.id = %s',
        (id_sesion,), one=True
    )
    if sesion is None:
        return jsonify({'error': 'Sesión no encontrada', 'id': id_sesion}), 404

    asistencias = query(
        'SELECT a.*, CONCAT(e.nombre, " ", e.apellido) AS estudiante_nombre'
        ' FROM asistencias a'
        ' JOIN estudiantes e ON a.id_estudiante = e.id'
        ' WHERE a.id_sesion = %s'
        ' ORDER BY e.apellido, e.nombre',
        (id_sesion,)
    )
    for a in asistencias:
        if a.get('hora_registro'):
            a['hora_registro'] = str(a['hora_registro'])

    return jsonify({
        'id_sesion': id_sesion,
        'fecha': str(sesion['fecha']),
        'curso': sesion['curso_nombre'],
        'profesor': sesion['profesor_nombre'],
        'total_asistencias': len(asistencias),
        'asistencias': asistencias
    })


@app.route('/api/cursos/<int:id_curso>/asistencias')
def api_asistencias_por_curso(id_curso):
    curso = query('SELECT * FROM cursos WHERE id=%s', (id_curso,), one=True)
    if curso is None:
        return jsonify({'error': 'Curso no encontrado', 'id': id_curso}), 404

    asistencias = query(
        'SELECT a.*, CONCAT(e.nombre, " ", e.apellido) AS estudiante_nombre,'
        '       s.fecha AS sesion_fecha'
        ' FROM asistencias a'
        ' JOIN estudiantes e ON a.id_estudiante = e.id'
        ' JOIN sesiones_clase s ON a.id_sesion = s.id'
        ' WHERE s.id_curso = %s'
        ' ORDER BY s.fecha DESC, a.id',
        (id_curso,)
    )
    for a in asistencias:
        if a.get('hora_registro'):
            a['hora_registro'] = str(a['hora_registro'])

    return jsonify({
        'id_curso': id_curso,
        'curso': curso['nombre_curso'],
        'total': len(asistencias),
        'asistencias': asistencias
    })


# ================================================================
# RUTAS API — SESIONES
# ================================================================
@app.route('/api/sesiones/', methods=['GET', 'POST'])
def api_sesiones():
    if request.method == 'POST':
        datos = request.get_json()
        if not datos:
            return jsonify({'error': 'El cuerpo debe ser JSON válido'}), 400

        id_curso = datos.get('id_curso')
        id_profesor = datos.get('id_profesor')
        fecha = datos.get('fecha')
        hora_inicio = datos.get('hora_inicio')
        hora_fin = datos.get('hora_fin')
        bloque_horario = datos.get('bloque_horario', '').upper()

        if id_curso is None:
            return jsonify({'error': 'El campo id_curso es obligatorio'}), 400
        curso = query('SELECT id FROM cursos WHERE id=%s', (id_curso,), one=True)
        if curso is None:
            return jsonify({'error': f'El curso con ID {id_curso} no existe'}), 400

        if id_profesor is None:
            return jsonify({'error': 'El campo id_profesor es obligatorio'}), 400
        profesor = query('SELECT id FROM profesores WHERE id=%s', (id_profesor,), one=True)
        if profesor is None:
            return jsonify({'error': f'El profesor con ID {id_profesor} no existe'}), 400

        if not fecha:
            return jsonify({'error': 'El campo fecha es obligatorio'}), 400
        if not hora_inicio:
            return jsonify({'error': 'El campo hora_inicio es obligatorio'}), 400
        if not hora_fin:
            return jsonify({'error': 'El campo hora_fin es obligatorio'}), 400

        if hora_inicio >= hora_fin:
            return jsonify({'error': 'La hora de inicio debe ser menor que la hora de fin'}), 400

        if bloque_horario and bloque_horario not in BLOQUES_VALIDOS:
            return jsonify({'error': f'bloque_horario inválido. Opciones: {BLOQUES_VALIDOS}'}), 400

        nuevo_id = execute(
            'INSERT INTO sesiones_clase (id_curso, id_profesor, fecha, hora_inicio, hora_fin, bloque_horario)'
            ' VALUES (%s, %s, %s, %s, %s, %s)',
            (id_curso, id_profesor, fecha, hora_inicio, hora_fin, bloque_horario)
        )
        nueva = query('SELECT * FROM sesiones_clase WHERE id=%s', (nuevo_id,), one=True)
        return jsonify({'mensaje': 'Sesión creada exitosamente', 'id': nuevo_id, 'data': nueva}), 201

    # GET
    sesiones = query(
        'SELECT s.*, c.nombre_curso AS curso_nombre,'
        '       CONCAT(p.nombre, " ", p.apellido) AS profesor_nombre'
        ' FROM sesiones_clase s'
        ' JOIN cursos c ON s.id_curso = c.id'
        ' JOIN profesores p ON s.id_profesor = p.id'
        ' ORDER BY s.fecha DESC, s.hora_inicio'
        ' LIMIT 100'
    )
    return jsonify({'total': len(sesiones), 'sesiones': sesiones})


@app.route('/api/sesiones/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_sesion(id):
    sesion = query(
        'SELECT s.*, c.nombre_curso AS curso_nombre,'
        '       CONCAT(p.nombre, " ", p.apellido) AS profesor_nombre'
        ' FROM sesiones_clase s'
        ' JOIN cursos c ON s.id_curso = c.id'
        ' JOIN profesores p ON s.id_profesor = p.id'
        ' WHERE s.id = %s',
        (id,), one=True
    )
    if sesion is None:
        return jsonify({'error': 'Sesión no encontrada', 'id': id}), 404

    if request.method == 'GET':
        return jsonify(sesion)

    if request.method == 'DELETE':
        execute('DELETE FROM sesiones_clase WHERE id=%s', (id,))
        return jsonify({'mensaje': f'Sesión eliminada.', 'id': id})

    # PUT
    datos = request.get_json()
    if not datos:
        return jsonify({'error': 'El cuerpo debe ser JSON'}), 400

    id_curso = datos.get('id_curso', sesion['id_curso'])
    id_profesor = datos.get('id_profesor', sesion['id_profesor'])
    fecha = datos.get('fecha', sesion['fecha'])
    hora_inicio = datos.get('hora_inicio', sesion['hora_inicio'])
    hora_fin = datos.get('hora_fin', sesion['hora_fin'])
    bloque_horario = datos.get('bloque_horario', sesion['bloque_horario']).upper()

    if hora_inicio >= hora_fin:
        return jsonify({'error': 'La hora de inicio debe ser menor que la hora de fin'}), 400

    if bloque_horario and bloque_horario not in BLOQUES_VALIDOS:
        return jsonify({'error': f'bloque_horario inválido. Opciones: {BLOQUES_VALIDOS}'}), 400

    execute(
        'UPDATE sesiones_clase'
        ' SET id_curso=%s, id_profesor=%s, fecha=%s, hora_inicio=%s, hora_fin=%s, bloque_horario=%s'
        ' WHERE id=%s',
        (id_curso, id_profesor, fecha, hora_inicio, hora_fin, bloque_horario, id)
    )
    actualizado = query('SELECT * FROM sesiones_clase WHERE id=%s', (id,), one=True)
    return jsonify({'mensaje': 'Sesión actualizada', 'sesion': actualizado})


@app.route('/api/cursos/<int:id_curso>/sesiones')
def api_sesiones_por_curso(id_curso):
    curso = query('SELECT * FROM cursos WHERE id=%s', (id_curso,), one=True)
    if curso is None:
        return jsonify({'error': 'Curso no encontrado', 'id': id_curso}), 404

    sesiones = query(
        'SELECT s.*, CONCAT(p.nombre, " ", p.apellido) AS profesor_nombre,'
        '       COUNT(a.id) AS total_asistencias'
        ' FROM sesiones_clase s'
        ' JOIN profesores p ON s.id_profesor = p.id'
        ' LEFT JOIN asistencias a ON a.id_sesion = s.id'
        ' WHERE s.id_curso = %s'
        ' GROUP BY s.id'
        ' ORDER BY s.fecha DESC, s.hora_inicio',
        (id_curso,)
    )

    return jsonify({
        'id_curso': id_curso,
        'curso': curso['nombre_curso'],
        'total_sesiones': len(sesiones),
        'sesiones': sesiones
    })


# ================================================================
# RUTAS API — PERIODOS ACADÉMICOS
# ================================================================
@app.route('/api/periodos/', methods=['GET', 'POST'])
def api_periodos():
    if request.method == 'POST':
        datos = request.get_json()
        if not datos:
            return jsonify({'error': 'El cuerpo debe ser JSON válido'}), 400

        fecha_inicio = datos.get('fecha_inicio')
        fecha_fin = datos.get('fecha_fin')

        if not fecha_inicio:
            return jsonify({'error': 'El campo fecha_inicio es obligatorio'}), 400
        if not fecha_fin:
            return jsonify({'error': 'El campo fecha_fin es obligatorio'}), 400
        if fecha_inicio > fecha_fin:
            return jsonify({'error': 'La fecha de inicio debe ser menor que la fecha de fin'}), 400

        # Si es activo, desactivar otros
        activo = datos.get('activo', False)
        if activo:
            execute('UPDATE periodos_academicos SET activo = FALSE WHERE activo = TRUE')

        nuevo_id = execute(
            'INSERT INTO periodos_academicos (fecha_inicio, fecha_fin, activo)'
            ' VALUES (%s, %s, %s)',
            (fecha_inicio, fecha_fin, activo)
        )
        nuevo = query('SELECT * FROM periodos_academicos WHERE id=%s', (nuevo_id,), one=True)
        if nuevo.get('fecha_inicio'):
            nuevo['fecha_inicio'] = str(nuevo['fecha_inicio'])
        if nuevo.get('fecha_fin'):
            nuevo['fecha_fin'] = str(nuevo['fecha_fin'])
        return jsonify({'mensaje': 'Período creado exitosamente', 'id': nuevo_id, 'data': nuevo}), 201

    # GET
    periodos = query('SELECT * FROM periodos_academicos ORDER BY fecha_inicio DESC')
    for p in periodos:
        if p.get('fecha_inicio'):
            p['fecha_inicio'] = str(p['fecha_inicio'])
        if p.get('fecha_fin'):
            p['fecha_fin'] = str(p['fecha_fin'])
    return jsonify({'total': len(periodos), 'periodos': periodos})


@app.route('/api/periodos/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_periodo(id):
    periodo = query('SELECT * FROM periodos_academicos WHERE id=%s', (id,), one=True)
    if periodo is None:
        return jsonify({'error': 'Período no encontrado', 'id': id}), 404

    if request.method == 'GET':
        if periodo.get('fecha_inicio'):
            periodo['fecha_inicio'] = str(periodo['fecha_inicio'])
        if periodo.get('fecha_fin'):
            periodo['fecha_fin'] = str(periodo['fecha_fin'])
        return jsonify(periodo)

    if request.method == 'DELETE':
        execute('DELETE FROM periodos_academicos WHERE id=%s', (id,))
        return jsonify({'mensaje': 'Período eliminado.', 'id': id})

    # PUT
    datos = request.get_json()
    if not datos:
        return jsonify({'error': 'El cuerpo debe ser JSON'}), 400

    fecha_inicio = datos.get('fecha_inicio', periodo['fecha_inicio'])
    fecha_fin = datos.get('fecha_fin', periodo['fecha_fin'])
    activo = datos.get('activo', periodo['activo'])

    if fecha_inicio > fecha_fin:
        return jsonify({'error': 'La fecha de inicio debe ser menor que la fecha de fin'}), 400

    if activo and not periodo['activo']:
        execute('UPDATE periodos_academicos SET activo = FALSE WHERE activo = TRUE')

    execute(
        'UPDATE periodos_academicos'
        ' SET fecha_inicio=%s, fecha_fin=%s, activo=%s'
        ' WHERE id=%s',
        (fecha_inicio, fecha_fin, activo, id)
    )
    actualizado = query('SELECT * FROM periodos_academicos WHERE id=%s', (id,), one=True)
    if actualizado.get('fecha_inicio'):
        actualizado['fecha_inicio'] = str(actualizado['fecha_inicio'])
    if actualizado.get('fecha_fin'):
        actualizado['fecha_fin'] = str(actualizado['fecha_fin'])
    return jsonify({'mensaje': 'Período actualizado', 'periodo': actualizado})


# ================================================================
# RUTAS API — JUSTIFICACIONES
# ================================================================
@app.route('/api/justificaciones/', methods=['GET', 'POST'])
def api_justificaciones():
    if request.method == 'POST':
        datos = request.get_json()
        if not datos:
            return jsonify({'error': 'El cuerpo debe ser JSON válido'}), 400

        id_asistencia = datos.get('id_asistencia')
        motivo = datos.get('motivo', '').strip()
        documento_adjunto = datos.get('documento_adjunto', '').strip()
        fecha_documentacion = datos.get('fecha_documentacion')

        if id_asistencia is None:
            return jsonify({'error': 'El campo id_asistencia es obligatorio'}), 400
        asistencia = query('SELECT id FROM asistencias WHERE id=%s', (id_asistencia,), one=True)
        if asistencia is None:
            return jsonify({'error': f'La asistencia con ID {id_asistencia} no existe'}), 400

        # Verificar que no exista ya una justificación para esta asistencia
        existente = query('SELECT id FROM justificaciones WHERE id_asistencia=%s', (id_asistencia,), one=True)
        if existente:
            return jsonify({'error': 'Ya existe una justificación para esta asistencia'}), 400

        if not motivo:
            return jsonify({'error': 'El campo motivo es obligatorio'}), 400
        if len(motivo) > 200:
            return jsonify({'error': 'El motivo no puede superar los 200 caracteres'}), 400
        if len(documento_adjunto) > 255:
            return jsonify({'error': 'La ruta del documento no puede superar los 255 caracteres'}), 400
        if not fecha_documentacion:
            return jsonify({'error': 'El campo fecha_documentacion es obligatorio'}), 400

        nuevo_id = execute(
            'INSERT INTO justificaciones (id_asistencia, motivo, documento_adjunto, fecha_documentacion)'
            ' VALUES (%s, %s, %s, %s)',
            (id_asistencia, motivo, documento_adjunto, fecha_documentacion)
        )
        nueva = query('SELECT * FROM justificaciones WHERE id=%s', (nuevo_id,), one=True)
        if nueva and nueva.get('fecha_documentacion'):
            nueva['fecha_documentacion'] = str(nueva['fecha_documentacion'])
        return jsonify({'mensaje': 'Justificación creada exitosamente', 'id': nuevo_id, 'data': nueva}), 201

    # GET
    justificaciones = query(
        'SELECT j.*, CONCAT(e.nombre, " ", e.apellido) AS estudiante_nombre,'
        '       a.estado AS asistencia_estado, s.fecha AS sesion_fecha'
        ' FROM justificaciones j'
        ' JOIN asistencias a ON j.id_asistencia = a.id'
        ' JOIN estudiantes e ON a.id_estudiante = e.id'
        ' JOIN sesiones_clase s ON a.id_sesion = s.id'
        ' ORDER BY j.fecha_documentacion DESC'
        ' LIMIT 100'
    )
    for j in justificaciones:
        if j.get('fecha_documentacion'):
            j['fecha_documentacion'] = str(j['fecha_documentacion'])
    return jsonify({'total': len(justificaciones), 'justificaciones': justificaciones})


@app.route('/api/justificaciones/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_justificacion(id):
    justificacion = query(
        'SELECT j.*, CONCAT(e.nombre, " ", e.apellido) AS estudiante_nombre'
        ' FROM justificaciones j'
        ' JOIN asistencias a ON j.id_asistencia = a.id'
        ' JOIN estudiantes e ON a.id_estudiante = e.id'
        ' WHERE j.id = %s',
        (id,), one=True
    )
    if justificacion is None:
        return jsonify({'error': 'Justificación no encontrada', 'id': id}), 404

    if request.method == 'GET':
        if justificacion.get('fecha_documentacion'):
            justificacion['fecha_documentacion'] = str(justificacion['fecha_documentacion'])
        return jsonify(justificacion)

    if request.method == 'DELETE':
        execute('DELETE FROM justificaciones WHERE id=%s', (id,))
        return jsonify({'mensaje': 'Justificación eliminada.', 'id': id})

    # PUT
    datos = request.get_json()
    if not datos:
        return jsonify({'error': 'El cuerpo debe ser JSON'}), 400

    motivo = datos.get('motivo', justificacion['motivo']).strip()
    documento_adjunto = datos.get('documento_adjunto', justificacion['documento_adjunto']).strip()
    validada = datos.get('validada', justificacion['validada'])

    if not motivo:
        return jsonify({'error': 'motivo no puede quedar vacío'}), 400

    execute(
        'UPDATE justificaciones'
        ' SET motivo=%s, documento_adjunto=%s, validada=%s'
        ' WHERE id=%s',
        (motivo, documento_adjunto, validada, id)
    )
    actualizado = query('SELECT * FROM justificaciones WHERE id=%s', (id,), one=True)
    if actualizado.get('fecha_documentacion'):
        actualizado['fecha_documentacion'] = str(actualizado['fecha_documentacion'])
    return jsonify({'mensaje': 'Justificación actualizada', 'justificacion': actualizado})


# ================================================================
# RUTAS API — RESUMEN / REPORTES
# ================================================================
@app.route('/api/resumen/')
def api_resumen():
    total_estudiantes = query('SELECT COUNT(*) AS total FROM estudiantes', one=True)['total']
    total_cursos = query('SELECT COUNT(*) AS total FROM cursos', one=True)['total']
    total_profesores = query('SELECT COUNT(*) AS total FROM profesores', one=True)['total']
    total_sesiones = query('SELECT COUNT(*) AS total FROM sesiones_clase', one=True)['total']
    total_asistencias = query('SELECT COUNT(*) AS total FROM asistencias', one=True)['total']
    total_justificaciones = query('SELECT COUNT(*) AS total FROM justificaciones', one=True)['total']

    por_estado = {}
    for estado in ESTADOS_ASISTENCIA_VALIDOS:
        resultado = query(
            'SELECT COUNT(*) AS total FROM asistencias WHERE estado=%s',
            (estado,), one=True
        )
        por_estado[estado] = resultado['total']

    return jsonify({
        'total_estudiantes': total_estudiantes,
        'total_cursos': total_cursos,
        'total_profesores': total_profesores,
        'total_sesiones': total_sesiones,
        'total_asistencias': total_asistencias,
        'total_justificaciones': total_justificaciones,
        'asistencias_por_estado': por_estado
    })


# ================================================================
# MANEJO DE ERRORES
# ================================================================
@app.errorhandler(404)
def no_encontrado(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Recurso no encontrado'}), 404
    return render_template('404.html', titulo='No encontrado'), 404

@app.errorhandler(500)
def error_servidor(e):
    return jsonify({'error': 'Error interno del servidor'}), 500


# ================================================================
# INICIO
# ================================================================
if __name__ == '__main__':
    app.run(debug=True)
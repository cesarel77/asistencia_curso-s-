# asistencia_curso(s)

# 1.-Instalar venv
    se utiliza el siguiente comando para instalar venv

    python -m venv venv

# 2.- activacion del venv
    se activa el venv con el siguiente comando

    venv\Scripts\activate

# 3.- se instara el flask
    para la instalacion de flask se instalo con el siguiente comando

    pip install flask

# 4.- se revisa la version 
      se revisa la version con el comando:

      python -c "import flask; print(flask.__version__)"

# 5.- se crea un documento txt para guardar dependencias
     se crea el documento txt con el siguiente comando

     pip freeze > requirements.txt

# 6.- se instalo mysql-connector-python 
       para esto se ocupo el siguiente comando

       pip install mysql-connector-python

# 7.- se actualizo el documento txt 
    esto se iso con el siguiente comando

    pip freeze > requirements.txt

# 8.-creacion de templates archivos

templates/
├── base.html
├── inicio.html
├── 404.html
├── estudiantes/
│   ├── lista.html
│   ├── detalle.html
│   ├── crear.html
│   ├── editar.html
│   └── eliminar.html
├── cursos/
│   ├── lista.html
│   ├── detalle.html
│   ├── crear.html
│   ├── editar.html
│   └── asignar_profesor.html
├── profesores/
│   ├── lista.html
│   ├── detalle.html
│   ├── crear.html
│   ├── editar.html
│   └── eliminar.html
├── asistencia/
│   ├── registrar.html
│   ├── registrar_individual.html
│   ├── registrar_masiva.html
│   ├── lista_curso.html
│   ├── lista_curso_fecha.html
│   ├── historial_estudiante.html
│   ├── lista_sesion.html
│   ├── reporte_inasistencias.html
│   ├── resumen_curso.html
│   └── editar.html
├── sesiones/
│   ├── lista.html
│   ├── detalle.html
│   ├── crear.html
│   ├── editar.html
│   ├── lista_curso.html
│   ├── rango_fechas.html
│   └── cerrar.html
├── justificaciones/
│   ├── crear.html
│   ├── lista.html
│   ├── pendientes.html
│   ├── detalle.html
│   └── validar.html
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_marshmallow import Marshmallow

# Inicializamos la aplicación
app = Flask(__name__)

# Configuramos la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializamos SQLAlchemy y Marshmallow
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Definimos el modelo de los animes
class Anime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"Anime('{self.title}', '{self.status}')"

# Definimos el esquema de Marshmallow para cada anime
class AnimeSchema(ma.Schema):
    class Meta:
        fields = ('id', 'title', 'status')

# Inicializamos el esquema de Marshmallow
anime_schema = AnimeSchema()
animes_schema = AnimeSchema(many=True)

#Establecemos los estados
anime_status = {"Finalizado", "Emisión"}

# Creamos la ruta para obtener todos los animes
@app.route('/animes', methods=['GET'])
def get_animes():
    try:
        animes = Anime.query.all()
        result = animes_schema.dump(animes)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Creamos la ruta para obtener un anime por su id
@app.route('/animes/<int:id>', methods=['GET'])
def get_anime(id):
    try:
        anime = Anime.query.get(id)
        if anime:
            return anime_schema.jsonify(anime)
        else:
            return jsonify({'error': 'Anime no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Creamos la ruta para obtener un anime por su nombre
@app.route('/animes/<string:title>', methods=['GET'])
def get_anime_by_title(title):
    try:
        anime = Anime.query.filter(func.lower(Anime.title) == func.lower(title)).first()
        if anime:
            return anime_schema.jsonify(anime)
        else:
            return jsonify({'error': 'Anime no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Creamos la ruta para agregar un nuevo anime
@app.route('/animes', methods=['POST'])
def add_anime():
    try:
        title = request.json['title']
        status = request.json['status']

        # Convertir título a minúsculas para comparar con títulos existentes
        title_lower = title.lower()

        #Se realizan correcciones en caso de escribir mal el estado
        if status == 'emisión' or status == 'emision':
            status = 'Emisión'
        elif status == 'finalizado':
            status = 'Finalizado' 

        if status not in anime_status:
            return jsonify({'error': 'El estado debe ser "Emisión" o "Finalizado"'}), 400

        anime = Anime.query.filter(func.lower(Anime.title) == title_lower).first()
        if anime:
            return jsonify({'error': 'Ya existe un anime con este título'}), 400

        new_anime = Anime(title=title, status=status)
        db.session.add(new_anime)
        db.session.commit()

        return anime_schema.jsonify(new_anime)
    except KeyError:
        return jsonify({'error': 'Los campos título y estado son requeridos'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400



# Creamos la ruta para actualizar un anime existente
@app.route('/animes/<int:id>', methods=['PUT'])
def update_anime(id):
    try:
        anime = Anime.query.get(id)

        if not anime:
            return jsonify({'error': 'Anime no encontrado'}), 404

        title = request.json['title']
        status = request.json['status']
        
        #Se realizan correcciones en caso de escribir mal el estado        
        if status == 'emisión' or status == 'emision':
            status = 'Emisión'
        elif status == 'finalizado':
            status = 'Finalizado'    

        if status not in anime_status:
            return jsonify({'error': 'El estado debe ser "Emisión" o "Finalizado"'}), 400

        anime_with_title = Anime.query.filter_by(title=title).first()
        if anime_with_title and anime_with_title.id != id:
            return jsonify({'error': 'Ya existe un anime con este título'}), 400

        anime.title = title
        anime.status = status

        db.session.commit()

        return anime_schema.jsonify(anime)
    except KeyError:
        return jsonify({'error': 'Los campos título y estado son requeridos'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# Creamos la ruta para eliminar un anime existente por id
@app.route('/animes/<int:id>', methods=['DELETE'])
def delete_anime(id):
    anime = Anime.query.get(id)

    if anime:
        db.session.delete(anime)
        db.session.commit()

        return anime_schema.jsonify(anime)
    else:
        return jsonify({'message': 'Anime no encontrado'}), 404

# Creamos la ruta para eliminar un anime existente por nombre
@app.route('/animes/<string:title>', methods=['DELETE'])
def delete_anime_by_title(title):
    anime = Anime.query.filter(func.lower(Anime.title) == func.lower(title)).first()
    if anime:
        db.session.delete(anime)
        db.session.commit()

        return anime_schema.jsonify(anime)
    else:
        return jsonify({'message': 'Anime no encontrado'}), 404        

# Creamos la ruta para eliminar todos los animes
@app.route('/animes', methods=['DELETE'])
def delete_all_animes():
    try:
        Anime.query.delete()
        db.session.commit()
        return jsonify({'message': 'Todos los animes han sido eliminados exitosamente.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Creamos una clase para manejar los errores personalizados
class MyError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.status_code = status_code


# Creamos una ruta para manejar errores 400
@app.errorhandler(400)
def handle_bad_request(error):
    response = jsonify({'error': error.description})
    response.status_code = 400
    return response

# Creamos una ruta para manejar errores 404
@app.errorhandler(404)
def handle_not_found(error):
    response = jsonify({'error': error.description})
    response.status_code = 404
    return response

# Creamos una ruta para manejar errores 500
@app.errorhandler(500)
def handle_server_error(error):
    response = jsonify({'error': error.description})
    response.status_code = 500
    return response


# Inicializamos la aplicación
if __name__ == '__main__':
    app.run(debug=True)


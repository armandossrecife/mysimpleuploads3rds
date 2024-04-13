from flask_sqlalchemy import SQLAlchemy
import sys

# componente de banco de dados
db = SQLAlchemy()

# Classe que representa os dados de um arquivo
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(100))
    filename = db.Column(db.String(100))
    bucket = db.Column(db.String(100))
    region = db.Column(db.String(100))

# Cria as tabelas do banco
def create_tables(app, drop_data_base):
    try:
        with app.app_context():
            print('Carrega as tabelas do banco')
            if drop_data_base: 
                db.drop_all()
                db.create_all()
                db.session.commit()
            print('Tabelas carregadas com sucesso!')
    except Exception as ex:
        print(f'Erro ao carregar o banco! {str(ex)}')
        sys.exit(1)
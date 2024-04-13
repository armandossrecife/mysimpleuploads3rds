from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import banco
import s3_handle
import uuid
import utilidades
import requests
import base64
import io

# True para limpar a instancia banco de dados atual
# Obs: o valor deve ser True na 1a execucao da aplicacao
#      para criar um banco limpo a estrutura limpa das tabelas
DROP_DATA_BASE = True

# Carrega os valores das credenciais de acesso da AWS
ACCESS_KEY_ID = os.getenv('ACCESS_KEY_ID')
SECRET_ACCESS_KEY = os.getenv('SECRET_ACCESS_KEY')
DB_USER = os.getenv('DB_USER')
PASSWORD_DB_USER = os.getenv('PASSWORD_DB_USER')
INSTANCIA_DB_AWS_RDS = 'mydbfilesteste.cdwkkuakqpji.us-east-1.rds.amazonaws.com'
BANCO_AWS_RDS = 'mydbfiles'
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{PASSWORD_DB_USER}@{INSTANCIA_DB_AWS_RDS}/{BANCO_AWS_RDS}'

# Instancia principal da aplicação
app = Flask(__name__)
app.secret_key = 'thisismysecretkeyfrommywebapplication'
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI

# Inicializa a instância do banco de dados
banco.db.init_app(app)
banco.create_tables(app, DROP_DATA_BASE)

# Carrega o componente S3
print('Carregando as credenciais da AWS')
s3 = s3_handle.carrega_s3(ACCESS_KEY_ID, SECRET_ACCESS_KEY)

# Rota para a pagina home
@app.route("/")
def home_page():
    return render_template("home.html")

# Rota para a pagina de uploads
@app.route("/upload", methods=["GET", "POST"])
def upload_page():
    if request.method == "POST":
        try: 
            uploaded_file = request.files["file-to-save"]
            
            if not utilidades.allowed_file(uploaded_file.filename):
                flash("Tipo de arquivo não permitido!")
                return redirect(url_for('upload_page'))

            new_filename = uuid.uuid4().hex + '.' + uploaded_file.filename.rsplit('.', 1)[1].lower()
            s3.upload_fileobj(uploaded_file, s3_handle.BUCKET_NAME, new_filename)
            file = banco.File(original_filename=uploaded_file.filename, filename=new_filename,
                bucket=s3_handle.BUCKET_NAME, region=s3_handle.AWS_S3_REGION)
            banco.db.session.add(file)
            banco.db.session.commit()
        except Exception as ex: 
            flash(f"Erro no upload! {str(ex)}")
            return redirect(url_for('upload_page'))

        return redirect(url_for("upload_page"))

    files = banco.File.query.all()

    return render_template("upload.html", files=files)

# Rota que carrega a pagina de downloads dos arquivos
@app.route("/downloads", methods=["GET"])
def downloads_page():
    files = banco.File.query.all()

    if not files: 
        flash('Nenhum arquivo para download!')
        return redirect(url_for('home_page'))

    return render_template("downloads.html", files=files)

# Recupera os bytes de uma imagem do bucket S3
def get_image_bytes(image_url):
    response = requests.get(image_url)
    response.raise_for_status()  # Raise an exception for non-200 status codes
    return response.content

# Rota que recupera os bytes da imagem e guarda em um formato base64
# para exibir o conteudo na pagina image_form
@app.route("/myimage/<nome>")
def show_image(nome):
    bucket_path = "https://my-app-files-bucket.s3.amazonaws.com"
    image_url = bucket_path + "/" + nome
    image_bytes = get_image_bytes(image_url)
    extensao = utilidades.get_file_extension(nome)

    encoded_bytes = base64.b64encode(image_bytes).decode('utf-8')  # Encode as base64 and decode for URI
    image_data_uri = f"data:image/{extensao};base64,{encoded_bytes}"

    return render_template("image_form.html", image_data_uri=image_data_uri)

# Recupera os bytes da imagem e guarda em memoria
@app.route("/myimage2/<nome>")
def show_image2(nome):
    bucket_path = "https://my-app-files-bucket.s3.amazonaws.com"
    image_url = bucket_path + "/" + nome
    image_bytes = get_image_bytes(image_url)

    extensao = utilidades.get_file_extension(nome)
    my_mimetype = "image" + "/" + extensao
    
    return send_file(io.BytesIO(image_bytes), mimetype=my_mimetype)

if __name__=='__main__':
    app.run(debug=True)
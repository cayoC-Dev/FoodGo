import os
from flask import Flask, abort, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_migrate import Migrate

# =========================================
# CONFIGURAÇÃO DO FLASK
# =========================================

app = Flask(__name__)

app.config['SECRET_KEY'] = 'chave-secreta'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///delivery.db'

db = SQLAlchemy(app)

migrate = Migrate(app, db)

# =========================================
# LOGIN MANAGER
# =========================================

login_manager = LoginManager(app)

login_manager.login_view = 'login'

login_manager.login_message = 'Faça login primeiro!'

login_manager.login_message_category = 'info'

# =========================================
# CONFRIGURAÇÃO DAS ROTAS
# =========================================

from functools import wraps

def role_required(roles):

    def decorator(f):

        @wraps(f)

        def decorated_function(*args, **kwargs):

            if current_user.role not in roles:

                abort(403)

            return f(*args, **kwargs)

        return decorated_function

    return decorator

# =========================================
# MODELO DE USUÁRIO
# =========================================

class User(UserMixin, db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(100),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        default='Cliente'
    )


# =========================================
# MODELO DE PRODUTOS
# =========================================

class Produto(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(100),
        nullable=False
    )

    preco = db.Column(
        db.Float,
        nullable=False
    )

    categoria = db.Column(
        db.String(50)
    )

    descricao = db.Column(
        db.String(300)
    )

    imagem = db.Column(
        db.String(300)
    )

    estoque = db.Column(
        db.Integer,
        default=1
    )


# =========================================
# MODELO DO CARRINHO
# =========================================

class Carrinho(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

    produto_id = db.Column(
        db.Integer,
        db.ForeignKey('produto.id')
    )

    quantidade = db.Column(
        db.Integer,
        default=1
    )

    produto = db.relationship(
        'Produto'
    )


# =========================================
# MODELO DOS PEDIDOS
# =========================================

class Pedido(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

    total = db.Column(
        db.Float
    )

    status = db.Column(
        db.String(50),
        default='Recebido'
    )

@app.route('/pedidos')
@login_required
def pedidos():

    pedidos = Pedido.query.filter_by(
        usuario_id=current_user.id
    ).all()

    return render_template(
        'pedidos.html',
        pedidos=pedidos
    )
    
@app.route('/listar_pedidos')
@login_required
@role_required(['Admin', 'Funcionario'])
def listar_pedidos():

    pedidos = Pedido.query.all()

    return render_template(
        'listar_pedidos.html',
        pedidos=pedidos
    )    

@app.route('/alterar_status/<int:id>/<status>')
@login_required
@role_required(['Admin', 'Funcionario'])
def alterar_status(id, status):

    pedido = Pedido.query.get_or_404(id)

    pedido.status = status

    db.session.commit()

    flash(
        'Status atualizado!'
    )

    return redirect(
        url_for('listar_pedidos')
    )

@app.route('/deletar_pedido/<int:id>')
@login_required
def deletar_pedido(id):

    pedido = Pedido.query.get_or_404(id)

    if pedido.usuario_id != current_user.id and current_user.role != 'Admin':
        flash('Você não tem permissão para excluir este pedido!')
        return redirect(url_for('pedidos'))

    db.session.delete(pedido)

    db.session.commit()

    flash(
        'Pedido excluído com sucesso!'
    )

    return redirect(
        url_for('pedidos')
    )

# =========================================
# USER LOADER
# =========================================

@login_manager.user_loader
def load_user(user_id):

    return User.query.get(
        int(user_id)
    )


# =========================================
# DECORADOR DE CARGOS
# =========================================

def role_required(roles):

    def decorator(f):

        @wraps(f)

        def decorated_function(
            *args,
            **kwargs
        ):

            if current_user.role not in roles:

                abort(403)

            return f(
                *args,
                **kwargs
            )

        return decorated_function

    return decorator


# =========================================
# DASHBOARD
# =========================================

@app.route('/')
@login_required
def dashboard():

    produtos = Produto.query.all()

    total_produtos = Produto.query.count()

    return render_template(

        'dashboard.html',

        produtos=produtos,

        total=total_produtos

    )


# =========================================
# LOGIN
# =========================================

@app.route(
    '/login',
    methods=['GET', 'POST']
)
def login():

    if request.method == 'POST':

        user = User.query.filter_by(

            username=request.form[
                'username'
            ]

        ).first()

        if user and check_password_hash(

            user.password,

            request.form[
                'password'
            ]

        ):

            login_user(user)

            flash(
                'Login realizado com sucesso!'
            )

            return redirect(
                url_for(
                    'dashboard'
                )
            )

        flash(
            'Usuário ou senha incorretos!'
        )

    return render_template(
        'login.html'
    )


# =========================================
# LOGOUT
# =========================================

@app.route('/logout')
@login_required
def logout():

    logout_user()

    flash(
        'Logout realizado!'
    )

    return redirect(
        url_for(
            'login'
        )
    )


# =========================================
# CADASTRO
# =========================================

@app.route(
    '/cadastro',
    methods=['GET', 'POST']
)
def cadastro():

    if request.method == 'POST':

        usuario_existente = User.query.filter_by(

            username=request.form[
                'username'
            ]

        ).first()

        if usuario_existente:

            flash(
                'Usuário já existe!'
            )

            return redirect(
                url_for(
                    'cadastro'
                )
            )

        senha_hash = generate_password_hash(

            request.form[
                'password'
            ]

        )

        novo_user = User(

            username=request.form[
                'username'
            ],

            password=senha_hash,

            role='Cliente'

        )

        db.session.add(
            novo_user
        )

        db.session.commit()

        flash(
            'Conta criada com sucesso!'
        )

        return redirect(
            url_for(
                'login'
            )
        )

    return render_template(
        'cadastro.html'
    )


# =========================================
# PRODUTOS
# =========================================

@app.route(
    '/produtos',
    methods=['GET', 'POST']
)
@login_required
@role_required(
    ['Admin', 'Funcionario']
)
def produtos():

    if request.method == 'POST':

        novo_produto = Produto(

            nome=request.form[
                'nome'
            ],

            preco=float(
                request.form[
                    'preco'
                ]
            ),

            categoria=request.form[
                'categoria'
            ],

            descricao=request.form[
                'descricao'
            ],

            imagem=request.form[
                'imagem'
            ],

            estoque=int(
                request.form[
                    'estoque'
                ]
            )

        )

        db.session.add(
            novo_produto
        )

        db.session.commit()

        flash(
            'Produto criado com sucesso!'
        )

        return redirect(
            url_for(
                'produtos'
            )
        )

    lista_produtos = Produto.query.all()

    return render_template(

        'produtos.html',

        produtos=lista_produtos

    )


# =========================================
# ADICIONAR AO CARRINHO
# =========================================

@app.route(
    '/adicionar_carrinho/<int:id>'
)
@login_required
def adicionar_carrinho(id):

    item = Carrinho.query.filter_by(

        usuario_id=current_user.id,

        produto_id=id

    ).first()

    if item:

        item.quantidade += 1

    else:

        item = Carrinho(

            usuario_id=current_user.id,

            produto_id=id,

            quantidade=1

        )

        db.session.add(
            item
        )

    db.session.commit()

    flash(
        'Produto adicionado ao carrinho!'
    )

    return redirect(
        url_for(
            'dashboard'
        )
    )

@app.route('/aumentar_item/<int:id>')
@login_required
def aumentar_item(id):

    item = Carrinho.query.get_or_404(id)

    item.quantidade += 1

    db.session.commit()

    return redirect(
        url_for('carrinho')
    )

@app.route('/diminuir_item/<int:id>')
@login_required
def diminuir_item(id):

    item = Carrinho.query.get_or_404(id)

    if item.quantidade > 1:

        item.quantidade -= 1

    else:

        db.session.delete(item)

    db.session.commit()

    return redirect(
        url_for('carrinho')
    )

@app.route('/remover_item/<int:id>')
@login_required
def remover_item(id):

    item = Carrinho.query.get_or_404(id)

    db.session.delete(item)

    db.session.commit()

    flash(
        'Produto removido do carrinho!'
    )

    return redirect(
        url_for('carrinho')
    )
    
# =========================================
# CARRINHO
# =========================================

@app.route('/carrinho')
@login_required
def carrinho():

    itens = Carrinho.query.filter_by(

        usuario_id=current_user.id

    ).all()

    total = 0

    for item in itens:

        total += (

            item.produto.preco *

            item.quantidade

        )

    return render_template(

        'carrinho.html',

        itens=itens,

        total=total

    )
# =========================================
# EDITAR PRODUTO
# =========================================

@app.route(
    '/editar_produto/<int:id>',
    methods=['GET', 'POST']
)
@login_required
@role_required(
    ['Admin', 'Funcionario']
)
def editar_produto(id):

    produto = Produto.query.get_or_404(
        id
    )

    if request.method == 'POST':

        produto.nome = request.form[
            'nome'
        ]

        produto.preco = float(
            request.form[
                'preco'
            ]
        )

        produto.categoria = request.form[
            'categoria'
        ]

        produto.descricao = request.form[
            'descricao'
        ]

        produto.imagem = request.form[
            'imagem'
        ]

        produto.estoque = int(
            request.form[
                'estoque'
            ]
        )

        db.session.commit()

        flash(
            'Produto atualizado!'
        )

        return redirect(
            url_for(
                'produtos'
            )
        )

    return render_template(

        'editar_produto.html',

        produto=produto

    )


# =========================================
# DELETAR PRODUTO
# =========================================

@app.route(
    '/deletar_produto/<int:id>'
)
@login_required
@role_required(
    ['Admin']
)
def deletar_produto(id):

    produto = Produto.query.get_or_404(
        id
    )

    db.session.delete(
        produto
    )

    db.session.commit()

    flash(
        'Produto removido!'
    )

    return redirect(
        url_for(
            'produtos'
        )
    )


# =========================================
# USUÁRIOS
# =========================================

@app.route('/usuarios')
@login_required
@role_required(
    ['Admin']
)
def usuarios():

    lista_usuarios = User.query.all()

    return render_template(

        'usuarios.html',

        usuarios=lista_usuarios

    )


# =========================================
# EDITAR USUÁRIO
# =========================================

@app.route(
    '/editar_usuario/<int:id>',
    methods=['GET', 'POST']
)
@login_required
@role_required(
    ['Admin']
)
def editar_usuario(id):

    user = User.query.get_or_404(
        id
    )

    if request.method == 'POST':

        user.username = request.form[
            'username'
        ]

        user.role = request.form[
            'role'
        ]

        if request.form[
            'password'
        ]:

            user.password = generate_password_hash(

                request.form[
                    'password'
                ]

            )

        db.session.commit()

        flash(
            'Usuário atualizado!'
        )

        return redirect(
            url_for(
                'usuarios'
            )
        )

    return render_template(

        'editar_usuario.html',

        user=user

    )


# =========================================
# DELETAR USUÁRIO
# =========================================

@app.route(
    '/deletar_usuario/<int:id>'
)
@login_required
@role_required(
    ['Admin']
)
def deletar_usuario(id):

    if id == current_user.id:

        flash(
            'Você não pode deletar sua própria conta!'
        )

        return redirect(
            url_for(
                'usuarios'
            )
        )

    user = User.query.get_or_404(
        id
    )

    db.session.delete(
        user
    )

    db.session.commit()

    flash(
        'Usuário removido!'
    )

    return redirect(
        url_for(
            'usuarios'
        )
    )


# =========================================
# PERFIL
# =========================================

@app.route(
    '/perfil',
    methods=['GET', 'POST']
)
@login_required
def perfil():

    if request.method == 'POST':

        current_user.username = request.form[
            'username'
        ]

        if request.form[
            'password'
        ]:

            current_user.password = generate_password_hash(

                request.form[
                    'password'
                ]

            )

        db.session.commit()

        flash(
            'Perfil atualizado!'
        )

    return render_template(
        'perfil.html'
    )


# =========================================
# FINALIZAR COMPRA
# =========================================

@app.route(
    '/finalizar_compra'
)
@login_required
def finalizar_compra():

    itens = Carrinho.query.filter_by(

        usuario_id=current_user.id

    ).all()

    if not itens:

        flash(
            'Seu carrinho está vazio!'
        )

        return redirect(
            url_for(
                'carrinho'
            )
        )

    total = 0

    for item in itens:

        total += (

            item.produto.preco *

            item.quantidade

        )

    pedido = Pedido(

        usuario_id=current_user.id,

        total=total

    )

    db.session.add(
        pedido
    )

    for item in itens:

        db.session.delete(
            item
        )

    db.session.commit()

    flash(
        'Compra realizada com sucesso!'
    )

    return redirect(
        url_for(
            'dashboard'
        )
    )


# =========================================
# INICIALIZAÇÃO
# =========================================

if __name__ == '__main__':

    with app.app_context():

        db.create_all()

        admin = User.query.filter_by(

            username='admin'

        ).first()

        if not admin:

            admin_user = User(

                username='admin',

                password=generate_password_hash(
                    'admin123'
                ),

                role='Admin'

            )

            db.session.add(
                admin_user
            )

            db.session.commit()

            print(
                'Admin criado com sucesso!'
            )

    app.run(
        debug=True
    )
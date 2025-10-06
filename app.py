# app.py

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

# --- 1. アプリケーションとデータベースの初期設定 ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-very-secret-key-that-no-one-should-know'
# Renderの環境変数DATABASE_URLを読み込む。なければローカルのSQLiteを使う。
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///lab_data.db')

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- 2. データベースモデル（テーブルの設計図）の定義 ---
# Userモデル: ユーザー情報を格納
class User(UserMixin, db.Model):
    id = db.Column(db.String(100), primary_key=True)  # 学籍番号
    password = db.Column(db.String(200), nullable=False)

# Labモデル: 研究室情報を格納 (教員名と定員フィールドを追加)
class Lab(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    professor = db.Column(db.String(100)) # ★★ 教員名フィールドを追加 ★★
    capacity = db.Column(db.Integer)      # ★★ 定員フィールドを追加 ★★

# Choiceモデル: ユーザーの選択希望を格納
class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), db.ForeignKey('user.id'), nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    lab_id = db.Column(db.Integer, db.ForeignKey('lab.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# --- 3. 各ページの処理（ルーティング） ---

@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        Choice.query.filter_by(user_id=current_user.id).delete()
        
        choice1_id = request.form.get('choice1')
        choice2_id = request.form.get('choice2')
        choice3_id = request.form.get('choice3')

        if not all([choice1_id, choice2_id, choice3_id]) or len(set([choice1_id, choice2_id, choice3_id])) < 3:
            flash('異なる3つの研究室を選択してください。', 'error')
            return redirect(url_for('dashboard'))

        db.session.add(Choice(user_id=current_user.id, priority=1, lab_id=choice1_id))
        db.session.add(Choice(user_id=current_user.id, priority=2, lab_id=choice2_id))
        db.session.add(Choice(user_id=current_user.id, priority=3, lab_id=choice3_id))
        db.session.commit()
        
        flash('希望を登録しました。', 'success')
        return redirect(url_for('dashboard'))

    lab_counts = []
    all_labs = Lab.query.order_by('name').all()
    for lab in all_labs:
        p1 = Choice.query.filter_by(lab_id=lab.id, priority=1).count()
        p2 = Choice.query.filter_by(lab_id=lab.id, priority=2).count()
        p3 = Choice.query.filter_by(lab_id=lab.id, priority=3).count()
        lab_counts.append({
            'name': lab.name,
            'professor': lab.professor,
            'capacity': lab.capacity,
            'p1': p1, 'p2': p2, 'p3': p3
        })
        
    return render_template('dashboard.html', lab_counts=lab_counts, labs=all_labs)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('student_id')
        password = request.form.get('password')
        user = User.query.get(user_id)
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('学籍番号またはパスワードが正しくありません。')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = request.form.get('student_id')
        password = request.form.get('password')
        
        if User.query.get(user_id):
            flash('その学籍番号は既に登録されています。')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(id=user_id, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('登録が完了しました。ログインしてください。')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# --- アプリケーションの実行と初期データ設定 ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # ★★ PDFの情報を反映した初期データ ★★
        # 初回起動時に研究室データがなければ登録する
        if Lab.query.count() == 0:
            labs_to_add = [
                Lab(name="インタラクション研究室", professor="井上 智", capacity=3),
                Lab(name="メタデータ研究室", professor="長森 光", capacity=3),
                Lab(name="応用数理システム研究室", professor="平林 晃", capacity=7),
                Lab(name="自然言語処理研究室(グループ)", professor="(記載なし)", capacity=None),
                Lab(name="システム数理研究室", professor="野村 T", capacity=3),
                Lab(name="グラフィックデザイン研究室", professor="(記載なし)", capacity=3),
                Lab(name="計算知能とグラフィックス研究室", professor="金森 亮", capacity=2),
                Lab(name="イメージングサイエンス・AI医用画像研究室", professor="(記載なし)", capacity=3),
                Lab(name="プログラミング言語研究室", professor="中野 圭介", capacity=3),
                Lab(name="ソーシャルロボット研究室", professor="三河 正彦", capacity=3),
                Lab(name="インタラクティブプログラミング研究室", professor="宇田 智一", capacity=None),
                Lab(name="行動変容研究室", professor="森田 ひろみ、Wang", capacity=4),
                Lab(name="融合知能デザイン研究室", professor="GING, Arkaprava Saha, Ichikawa", capacity=2),
                Lab(name="エンタテインメントコンピューティング研究室", professor="星野 准一", capacity=2),
                Lab(name="ソーシャルネットワークサービス研究室", professor="ATARASHI, Asako", capacity=3),
                Lab(name="メタバースメディア研究室", professor="平木 敬", capacity=3),
                Lab(name="データベースコンピュータグラフィックス研究室", professor="藤澤 誠", capacity=3),
                Lab(name="人と音の情報学研究室", professor="善甫 康子、麦踏 なみ", capacity=5),
                Lab(name="カードベース・パズル・ゲーム研究室", professor="品川 和雅", capacity=2),
                Lab(name="認知科学理解研究室", professor="(記載なし)", capacity=3),
                Lab(name="デジタルネイチャー研究室", professor="落合 陽一, Lingling", capacity=None),
                Lab(name="数式処理研究室", professor="森継 修", capacity=3),
                Lab(name="カエル研究室", professor="國府田 一斗", capacity=2)
            ]
            db.session.bulk_save_objects(labs_to_add)
            db.session.commit()
            
    app.run(debug=True)
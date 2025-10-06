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
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///lab_data_v2.db')

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
    # ログインしているユーザーが既に希望を提出したか確認
    existing_choice = Choice.query.filter_by(user_id=current_user.id).first()
    if existing_choice:
        # 提出済みならダッシュボード（更新ページ）へ
        return redirect(url_for('dashboard'))
    else:
        # 未提出なら新規登録ページへ
        return redirect(url_for('register_choices'))

# ★★ 新規登録専用ページ ★★
@app.route('/register-choices', methods=['GET', 'POST'])
@login_required
def register_choices():
    # 既に提出済みのユーザーがアクセスしたらダッシュボードに飛ばす
    if Choice.query.filter_by(user_id=current_user.id).first():
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        choice1_id = request.form.get('choice1')
        choice2_id = request.form.get('choice2')
        choice3_id = request.form.get('choice3')

        if not all([choice1_id, choice2_id, choice3_id]) or len(set([choice1_id, choice2_id, choice3_id])) < 3:
            flash('異なる3つの研究室を選択してください。', 'error')
            return redirect(url_for('register_choices'))

        # 新しい希望をDBに保存
        db.session.add(Choice(user_id=current_user.id, priority=1, lab_id=choice1_id))
        db.session.add(Choice(user_id=current_user.id, priority=2, lab_id=choice2_id))
        db.session.add(Choice(user_id=current_user.id, priority=3, lab_id=choice3_id))
        db.session.commit()
        
        flash('希望を新規登録しました。', 'success')
        # 登録後はダッシュボード（更新ページ）へリダイレクト
        return redirect(url_for('dashboard'))

    labs_for_select = Lab.query.all()
    return render_template('register_choices.html', labs=labs_for_select)


# ★★ 更新専用のダッシュボードページ ★★
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    # まだ提出していないユーザーがアクセスしたら新規登録ページに飛ばす
    existing_choice = Choice.query.filter_by(user_id=current_user.id).first()
    if not existing_choice:
        return redirect(url_for('register_choices'))

    if request.method == 'POST':
        # 既存の希望を一度削除
        Choice.query.filter_by(user_id=current_user.id).delete()
        
        choice1_id = request.form.get('choice1')
        choice2_id = request.form.get('choice2')
        choice3_id = request.form.get('choice3')

        if not all([choice1_id, choice2_id, choice3_id]) or len(set([choice1_id, choice2_id, choice3_id])) < 3:
            flash('異なる3つの研究室を選択してください。', 'error')
            # 更新失敗時は再度ダッシュボードを表示
            return redirect(url_for('dashboard'))

        # 新しい希望を保存（更新）
        db.session.add(Choice(user_id=current_user.id, priority=1, lab_id=choice1_id))
        db.session.add(Choice(user_id=current_user.id, priority=2, lab_id=choice2_id))
        db.session.add(Choice(user_id=current_user.id, priority=3, lab_id=choice3_id))
        db.session.commit()
        
        flash('希望を更新しました。', 'success')
        return redirect(url_for('dashboard'))

    # --- 表示ロジック ---
    lab_counts = []
    all_labs_for_count = Lab.query.order_by('name').all()
    for lab in all_labs_for_count:
        p1 = Choice.query.filter_by(lab_id=lab.id, priority=1).count()
        p2 = Choice.query.filter_by(lab_id=lab.id, priority=2).count()
        p3 = Choice.query.filter_by(lab_id=lab.id, priority=3).count()
        lab_counts.append({
            'name': lab.name, 'professor': lab.professor, 'capacity': lab.capacity,
            'p1': p1, 'p2': p2, 'p3': p3
        })
    
    labs_for_select = Lab.query.all()
    return render_template('dashboard.html', lab_counts=lab_counts, labs=labs_for_select)

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
    # この部分はローカルで python app.py を実行した時のみ使われる
    with app.app_context():
        db.create_all()
    app.run(debug=True)
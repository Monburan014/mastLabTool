# app.py

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

# --- 1. アプリケーションとデータベースの初期設定 ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-very-secret-key-that-no-one-should-know' # 必ず複雑なものに変更してください
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lab_data.db' # instanceフォルダ内にDBファイルが作られます
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # 未ログイン時にリダイレクトする先

# --- 2. データベースモデル（テーブルの設計図）の定義 ---
class User(UserMixin, db.Model):
    id = db.Column(db.String(100), primary_key=True)  # 学籍番号をIDとする
    password = db.Column(db.String(200), nullable=False)

class Lab(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), db.ForeignKey('user.id'), nullable=False)
    priority = db.Column(db.Integer, nullable=False) # 1: 第一希望, 2: 第二希望...
    lab_id = db.Column(db.Integer, db.ForeignKey('lab.id'), nullable=False)

# Flask-Loginがユーザー情報を取得するための必須関数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# --- 3. 各ページの処理（ルーティング） ---

# トップページはダッシュボードへリダイレクト
@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))

# ダッシュボード（希望提出＆結果表示）
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        # 既存の希望があれば削除
        Choice.query.filter_by(user_id=current_user.id).delete()
        
        # 新しい希望をデータベースに保存
        choice1_id = request.form.get('choice1')
        choice2_id = request.form.get('choice2')
        choice3_id = request.form.get('choice3')

        if not all([choice1_id, choice2_id, choice3_id]):
            flash('すべての希望を選択してください。', 'error')
            return redirect(url_for('dashboard'))

        db.session.add(Choice(user_id=current_user.id, priority=1, lab_id=choice1_id))
        db.session.add(Choice(user_id=current_user.id, priority=2, lab_id=choice2_id))
        db.session.add(Choice(user_id=current_user.id, priority=3, lab_id=choice3_id))
        db.session.commit()
        
        flash('希望を登録しました。', 'success')
        return redirect(url_for('dashboard'))

    # --- 希望人数の集計 (SQL) ---
    # 研究室ごとに、各希望順位の人数をカウントする
    counts = db.session.query(
        Lab.id,
        Lab.name,
        func.count(func.nullif(Choice.priority, 1)).label('p1_count'),
        func.count(func.nullif(Choice.priority, 2)).label('p2_count'),
        func.count(func.nullif(Choice.priority, 3)).label('p3_count')
    ).outerjoin(Choice, Lab.id == Choice.lab_id)\
     .group_by(Lab.id)\
     .order_by(Lab.name)\
     .all()

    # 集計結果を整形 (例: [(1, 'A研', 5, 3, 2), ...])
    # SQLの count(case when ...) を使う方がより効率的ですが、ここでは分かりやすさを優先
    lab_counts = []
    all_labs = Lab.query.order_by('name').all()
    for lab in all_labs:
        p1 = Choice.query.filter_by(lab_id=lab.id, priority=1).count()
        p2 = Choice.query.filter_by(lab_id=lab.id, priority=2).count()
        p3 = Choice.query.filter_by(lab_id=lab.id, priority=3).count()
        lab_counts.append({'name': lab.name, 'p1': p1, 'p2': p2, 'p3': p3})
        
    labs_for_select = Lab.query.all()
    return render_template('dashboard.html', lab_counts=lab_counts, labs=labs_for_select)

# ログインページ
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

# 新規登録ページ
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = request.form.get('student_id')
        password = request.form.get('password')
        
        # 既に同じIDのユーザーがいないかチェック
        if User.query.get(user_id):
            flash('その学籍番号は既に登録されています。')
            return redirect(url_for('register'))
            
        # パスワードをハッシュ化して安全に保存
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(id=user_id, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('登録が完了しました。ログインしてください。')
        return redirect(url_for('login'))
        
    return render_template('register.html')

# ログアウト
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all() # データベースとテーブルがなければ作成

        # 初期データとして研究室を登録（初回実行時のみ）
        if Lab.query.count() == 0:
            labs_to_add = [
                Lab(name="情報科学研究室"), Lab(name="生命工学研究室"),
                Lab(name="機械システム研究室"), Lab(name="環境化学研究室"),
                Lab(name="建築デザイン研究室")
            ]
            db.session.bulk_save_objects(labs_to_add)
            db.session.commit()
            
    app.run(debug=True)
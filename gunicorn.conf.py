# gunicorn.conf.py

from app import app, db, Lab # Labモデルもインポート

def on_starting(server):
    """
    Gunicornのマスタープロセスが起動するときに一度だけ実行されるフック
    """
    with app.app_context():
        # すべてのテーブルを作成する
        db.create_all()

        # 研究室データがなければ登録する
        if Lab.query.count() == 0:
            labs_to_add = [
                Lab(name="インタラクション研究室", professor="井上智雄", capacity=3),
                Lab(name="メタデータ研究室", professor="永森光晴", capacity=3),
                Lab(name="応用数理システム研究室", professor="河辺徹,平⽥祥⼈,池⽥春之介", capacity=7),
                Lab(name="⾃然⾔語処理 on the Web 研究室（乾グループ）", professor="乾孝司", capacity=3),
                Lab(name="システム数理研究室", professor="佐野良夫", capacity=3),
                Lab(name="グラフィックデザイン研究室", professor="⾦尚泰", capacity=3),
                Lab(name="計算幾何学とグラフィックス研究室", professor="⾦森由博，遠藤結城", capacity=2),
                Lab(name="イメージングサイエンス・AI医用画像", professor="⼯藤博幸", capacity=3),
                Lab(name="プログラミング言語研究室", professor="中井央", capacity=3),
                Lab(name="ソーシャルロボット研究室", professor="三河正彦", capacity=3),
                Lab(name="インタラクティブプログラミング研究室", professor="志築⽂太郎，川⼝⼀画", capacity=6),
                Lab(name="知覚・認知・⾏動研究室", professor="森田ひろみ,藤崎樹", capacity=4),
                Lab(name="融合知能デザイン研究室", professor="森嶋厚⾏・徐哲林 (伊藤寛祥,Arkaprava Saha,Jiachuan Wang)", capacity=2),
                Lab(name="エンタテインメントコンピューティング研究室", professor="星野准一", capacity=2),
                Lab(name="陳漢雄", professor="陳漢雄", capacity=3),
                Lab(name="ソーシャルネットワーク研究室", professor="津川翔", capacity=3),
                Lab(name="メタバースメディア研究室", professor="平⽊剛史", capacity=3),
                Lab(name="物理ベースコンピュータグラフィックス研究室", professor="藤澤誠", capacity=3),
                Lab(name="人と音の情報学研究室", professor="寺澤洋⼦,飯野なみ", capacity=5),
                Lab(name="暗号・パズル・ゲーム研究室", professor="品川和雅", capacity=2),
                Lab(name="機械学習・⾔語理解研究室", professor="若林啓", capacity=3),
                Lab(name="デジタルネイチャー研究室", professor="落合陽⼀,伏⾒⿓樹,Li Jingjing", capacity=6),
                Lab(name="数式処理研究室", professor="森継修一", capacity=3),
                Lab(name="カエル研究室", professor="合原⼀究（兼担）", capacity=2)
            ]
            db.session.bulk_save_objects(labs_to_add)
            db.session.commit()
"""「aはbがc割」形式のタイトルパーサーのテスト"""

import pytest
from python_template_for_ai_assistant.title_parser import parse_ratio_title


class TestParseRatioTitle:
    """parse_ratio_title関数のテスト"""

    def test_正常系_半角数字の割合(self):
        """「aはbがc割」形式（半角数字）で正しくパースできる"""
        title = "人は見た目が9割"
        a, b, c = parse_ratio_title(title)
        assert a == "人"
        assert b == "見た目"
        assert c == 9

    def test_正常系_漢数字の割合(self):
        """「aはbがc割」形式（漢数字）で正しくパースできる"""
        title = "人は見た目が九割"
        a, b, c = parse_ratio_title(title)
        assert a == "人"
        assert b == "見た目"
        assert c == 9

    def test_正常系_複数の漢数字(self):
        """1割から9割まで全てパースできる"""
        test_cases = [
            ("人は見た目が一割", 1),
            ("人は見た目が二割", 2),
            ("人は見た目が三割", 3),
            ("人は見た目が四割", 4),
            ("人は見た目が五割", 5),
            ("人は見た目が六割", 6),
            ("人は見た目が七割", 7),
            ("人は見た目が八割", 8),
            ("人は見た目が九割", 9),
        ]
        for title, expected_c in test_cases:
            a, b, c = parse_ratio_title(title)
            assert a == "人"
            assert b == "見た目"
            assert c == expected_c

    def test_正常系_複数の半角数字(self):
        """1割から9割まで全てパースできる（半角）"""
        for i in range(1, 10):
            title = f"人は見た目が{i}割"
            a, b, c = parse_ratio_title(title)
            assert a == "人"
            assert b == "見た目"
            assert c == i

    def test_正常系_空白を含む(self):
        """「が」と「割」の間に空白があってもパースできる"""
        title = "人は見た目が9 割"
        a, b, c = parse_ratio_title(title)
        assert a == "人"
        assert b == "見た目"
        assert c == 9

    def test_正常系_前後に空白がある(self):
        """タイトルの前後に空白があってもパースできる"""
        title = "  人は見た目が9割  "
        a, b, c = parse_ratio_title(title)
        assert a == "人"
        assert b == "見た目"
        assert c == 9

    def test_正常系_長いaとb(self):
        """aとbが複数文字でもパースできる"""
        title = "日本人はコミュニケーション能力が8割"
        a, b, c = parse_ratio_title(title)
        assert a == "日本人"
        assert b == "コミュニケーション能力"
        assert c == 8

    def test_異常系_パターンにマッチしない(self):
        """「aはbがc割」形式でない場合はNoneを返す"""
        title = "人の見た目は9割"  # 「が」がない
        a, b, c = parse_ratio_title(title)
        assert a is None
        assert b is None
        assert c is None

    def test_異常系_はがない(self):
        """「は」がない場合はaがNoneになる"""
        title = "見た目が9割"
        a, b, c = parse_ratio_title(title)
        assert a is None
        assert b is None
        assert c is None

    def test_異常系_がの代わりにのがある(self):
        """「が」の代わりに「の」がある場合はaとbがNoneになる"""
        title = "医者の9割は不摂生"
        a, b, c = parse_ratio_title(title)
        assert a is None
        assert b is None
        assert c is None

    def test_異常系_割合がない(self):
        """割合の記載がない場合はNoneを返す"""
        title = "人は見た目が大事"
        a, b, c = parse_ratio_title(title)
        assert a is None
        assert b is None
        assert c is None

    def test_異常系_空文字列(self):
        """空文字列の場合はNoneを返す"""
        a, b, c = parse_ratio_title("")
        assert a is None
        assert b is None
        assert c is None

    def test_異常系_None(self):
        """Noneの場合はNoneを返す"""
        a, b, c = parse_ratio_title(None)
        assert a is None
        assert b is None
        assert c is None

    def test_エッジケース_0割(self):
        """0割は不正な値として扱う"""
        title = "人は見た目が0割"
        a, b, c = parse_ratio_title(title)
        assert a is None
        assert b is None
        assert c is None

    def test_エッジケース_10割以上(self):
        """10割以上も抽出"""
        title = "人は見た目が10割"
        a, b, c = parse_ratio_title(title)
        assert a == "人"
        assert b == "見た目"
        assert c == 10

    def test_正常系_実データ_儲かる会社はホームページが9割(self):
        """実データ: 儲かる会社はホームページが9割!"""
        title = "儲かる会社はホームページが9割!"
        a, b, c = parse_ratio_title(title)
        # 末尾に「!」があるが記号を除去して抽出
        assert a == "会社"
        assert b == "ホームページ"
        assert c == 9

    def test_異常系_実データ_見た目が9割をどう生きる(self):
        """実データ: 「見た目が9割」をどう生きる（「は」がない）"""
        title = "「見た目が9割」をどう生きる"
        a, b, c = parse_ratio_title(title)
        assert a is None
        assert b is None
        assert c is None

    def test_正常系_実データ_リーダーは話し方が9割_コロン以降あり(self):
        """実データ: リーダーは話し方が9割 : 1分で..."""
        title = "リーダーは話し方が9割 : 1分でやる気を引き出し、100%好かれる話し方のコツ"
        a, b, c = parse_ratio_title(title)
        # コロン以降があるためマッチしない
        assert a == "リーダー"
        assert b == "話し方"
        assert c == 9

    def test_正常系_実データ_リーダーは時間の使い方が9割_記号あり(self):
        """実データ: リーダーは「時間の使い方」が9割!（記号がある）"""
        title = "リーダーは「時間の使い方」が9割!"
        a, b, c = parse_ratio_title(title)
        assert a == "リーダー"
        assert b == "時間の使い方" # 記号は削除
        assert c == 9

    def test_正常系_実データ_人の一生は運が八割残る二割は(self):
        """実データ: 人の一生は「運」が八割残る二割は...（八割の後に続く文字列がある）"""
        title = "人の一生は「運」が八割残る二割は「偶然」と「実力」"
        a, b, c = parse_ratio_title(title)
        # 「八割」の後に続く文字列があるためマッチしない
        assert a == "一生"
        assert b == "運"
        assert c == 8

    def test_正常系_実データ_家は見た目が九割だけど(self):
        """実データ: 解体新居 : 家づくりを根本から考える : 家は見た目が九割だけど…（末尾に「だけど…」がある）"""
        title = "解体新居 : 家づくりを根本から考える : 家は見た目が九割だけど…"
        a, b, c = parse_ratio_title(title)
        # コロンがあり、「九割」の後に「だけど…」があるためマッチしない
        assert a == "家"
        assert b == "見た目"
        assert c == 9

    def test_異常系_実データ_美肌_太らない_老けないは食べ方が9割(self):
        """実データ: 美肌、太らない、老けないは食べ方が9割（複数の「、」がある）"""
        title = "美肌、太らない、老けないは食べ方が9割"
        a, b, c = parse_ratio_title(title)
        assert a is None
        assert b is None
        assert c is None
    
    def test_正常系_実データ_病気の原因は栄養欠損が9割(self):
        """実データ: 病気の原因は栄養欠損が9割 : 分子栄養医学を超えた抗老化健康術（コロン以降がある）"""
        title = "病気の原因は栄養欠損が9割 : 分子栄養医学を超えた抗老化健康術"
        a, b, c = parse_ratio_title(title)
        # コロン以降があるためマッチしない
        assert a == "原因"
        assert b == "栄養欠損"
        assert c == 9
    
    def test_正常系_実データ_病状経過と早期対応は病態生理が9割(self):
        """実データ: 病状経過と早期対応は病態生理が9割 : ICUナースのための病態生理（コロン以降がある）"""
        title = "病状経過と早期対応は病態生理が9割 : ICUナースのための病態生理"
        a, b, c = parse_ratio_title(title)
        # コロン以降があるためマッチしない
        assert a == "早期対応"
        assert b == "病態生理"
        assert c == 9
    
    def test_正常系_実データ_美容はメンタルが9割(self):
        """実データ: 美容はメンタルが9割（末尾に「」がない）"""
        title = "美容はメンタルが9割"
        a, b, c = parse_ratio_title(title)
        assert a == "美容"
        assert b == "メンタル"
        assert c == 9

    def test_正常系_実データ_美容はメンタルが9割(self):
        """実データ: 美容はメンタルが9割（末尾に「」がない）"""
        title = "美容は'''メンタル'''が9割"
        a, b, c = parse_ratio_title(title)
        assert a == "美容"
        assert b == "メンタル"
        assert c == 9

    def test_正常系_実データ_美容はメンタルが9割(self):
        """実データ: 美容はメンタルが9割（末尾に「」がない）"""
        title = '美容は"""メンタル"""が9割'
        a, b, c = parse_ratio_title(title)
        assert a == "美容"
        assert b == "メンタル"
        assert c == 9

    def test_正常系_実データ_不動産投資は組み合わせが9割(self):
        """実データ: 不動産投資は組み合わせが9割 : 家賃収入1000万円を最速で叶えるトライアングル不動産投資術（コロン以降がある）"""
        title = "不動産投資は組み合わせが9割 : 家賃収入1000万円を最速で叶えるトライアングル不動産投資術"
        a, b, c = parse_ratio_title(title)
        # コロン以降があるためマッチしない
        assert a == "不動産投資"
        assert b == "組み合わせ"
        assert c == 9
    def test_正常系_実データ_不動産投資は出口戦略が9割(self):
        """実データ: 不動産投資は出口戦略が9割（コロン以降がない）"""
        title = "不動産投資は出口戦略が9割"
        a, b, c = parse_ratio_title(title)
        assert a == "不動産投資"
        assert b == "出口戦略"
        assert c == 9
      
    def test_正常系_実データ_不良品が多い工場の原因は地盤が9割(self):
        """実データ: 不良品が多い工場の原因は地盤が9割（コロン以降がない）"""
        title = "不良品が多い工場の原因は地盤が9割"
        a, b, c = parse_ratio_title(title)
        assert a == "原因"
        assert b == "地盤"
        assert c == 9
    def test_異常系_実データ_不老も長寿も血糖値が9割(self):
        """実データ: 不老も長寿も「血糖値」が9割 : インスリンを減らせば老化は遅くなる（コロン以降がある）"""
        title = "不老も長寿も「血糖値」が9割 : インスリンを減らせば老化は遅くなる"
        a, b, c = parse_ratio_title(title)
        # コロン以降があるためマッチしない
        assert a is None
        assert b is None
        assert c is None

    def test_正常系_実データ_部下の育成は仕組みが9割(self):
        """実データ: 部下の育成は「仕組み」が9割 : 1分でできる部下のやる気を引き出すコツ（コロン以降がある）"""
        title = "部下の育成は「仕組み」が9割 : 1分でできる部下のやる気を引き出すコツ"
        a, b, c = parse_ratio_title(title)
        assert a == "育成"
        assert b == "仕組み"
        assert c == 9

    def test_正常系_実データ_まんが疲れの原因は糖が9割(self):
        """実データ: まんが疲れの原因は糖が9割 : 健康診断ではみつからない不調の正体（コロン以降がある）"""
        title = "まんが疲れの原因は糖が9割 : 健康診断ではみつからない不調の正体"
        a, b, c = parse_ratio_title(title)
        assert a == "原因"
        assert b == "糖"
        assert c == 9

    def test_正常系_実データ_漫画で分かる株はメンタルが9割(self):
        """実データ: 漫画で分かる株はメンタルが9割 : 誰も教えてくれなかった投資の最重要法則（コロン以降がある）"""
        title = "漫画で分かる株はメンタルが9割 : 誰も教えてくれなかった投資の最重要法則"
        a, b, c = parse_ratio_title(title)
        assert a == "株"
        assert b == "メンタル"
        assert c == 9

    def test_正常系_実データ_デザインは余白が9割(self):
        """実データ: 漫画でわかるけっきょく、よはく。 : デザインは「余白」が9割（コロン以降にパターンがある）"""
        title = "漫画でわかるけっきょく、よはく。 : デザインは「余白」が9割"
        a, b, c = parse_ratio_title(title)
        assert a == "デザイン"
        assert b == "余白"
        assert c == 9

    def test_異常系_実データ_まんがでわかる伝え方が9割(self):
        """実データ: まんがでわかる伝え方が9割（「は」がない）"""
        title = "まんがでわかる伝え方が9割"
        a, b, c = parse_ratio_title(title)
        assert a is None
        assert b is None
        assert c is None

    def test_異常系_実データ_まんがでわかる伝え方が9割_強いコトバ(self):
        """実データ: まんがでわかる伝え方が9割〈強いコトバ〉（「は」がなく、末尾に記号がある）"""
        title = "まんがでわかる伝え方が9割〈強いコトバ〉"
        a, b, c = parse_ratio_title(title)
        assert a is None
        assert b is None
        assert c is None

    def test_異常系_実データ_見た目が9割_内定術(self):
        """実データ: 「見た目が9割」内定術（「は」がない）"""
        title = "「見た目が9割」内定術"
        a, b, c = parse_ratio_title(title)
        assert a is None
        assert b is None
        assert c is None

    def test_正常系_実データ_無印良品は仕組みが9割(self):
        """実データ: 無印良品は、仕組みが9割 : 仕事はシンプルにやりなさい（aの中にカンマがあり、コロン以降がある）"""
        title = "無印良品は、仕組みが9割 : 仕事はシンプルにやりなさい"
        a, b, c = parse_ratio_title(title)
        assert a == "無印良品"
        assert b == "仕組み"
        assert c == 9

    def test_正常系_実データ_ひとり終活は備えが9割(self):
        """実データ: ひとり終活は備えが9割 : 事例と解説でわかる「安心老後」の分かれ道"""
        title = "「ひとり終活」は備えが9割 : 事例と解説でわかる「安心老後」の分かれ道"
        a, b, c = parse_ratio_title(title)
        assert a == "ひとり終活"
        assert b == "備え"
        assert c == 9

    def test_正常系_実データ_長引く痛みの原因は血管が9割(self):
        """実データ: 長引く痛みの原因は、血管が9割（bの先頭にカンマがある）"""
        title = "長引く痛みの原因は、血管が9割"
        a, b, c = parse_ratio_title(title)
        assert a == "原因"
        assert b == "血管"
        assert c == 9

    def test_異常系_実データ_日経ヘルス(self):
        """実データ: 日経ヘルス（「aはbがc割」形式ではない）"""
        title = "日経ヘルス"
        a, b, c = parse_ratio_title(title)
        assert a is None
        assert b is None
        assert c is None

    def test_異常系_実データ_日本人が9割間違える日本語(self):
        """実データ: 日本人が「9割間違える」日本語（「9割」が動詞の修飾で「c割」の形式ではない）"""
        title = "日本人が「9割間違える」日本語 : あなたも使っていませんか?"
        a, b, c = parse_ratio_title(title)
        assert a is None
        assert b is None
        assert c is None

    def test_正常系_実データ_日本の古典はエロが9割(self):
        """実データ: 日本の古典はエロが9割 : ちんまん日本文学史"""
        title = "日本の古典はエロが9割 : ちんまん日本文学史"
        a, b, c = parse_ratio_title(title)
        assert a == "古典"
        assert b == "エロ"
        assert c == 9

    def test_正常系_実データ_マスコミはウソが9割(self):
        """実データ: 日本も世界もマスコミはウソが9割（複数の「も」があり、最後の「は」を使う）"""
        title = "日本も世界もマスコミはウソが9割 : 出版コードぎりぎり〈FACT対談〉"
        a, b, c = parse_ratio_title(title)
        assert a == "マスコミ"
        assert b == "ウソ"
        assert c == 9

    def test_正常系_実データ_入札参加資格申請は事前知識が9割(self):
        """実データ: 入札参加資格申請は事前知識が9割 : 東京都入札資格 (物品・委託) と全省庁統一資格"""
        title = "入札参加資格申請は事前知識が9割 : 東京都入札資格 (物品・委託) と全省庁統一資格"
        a, b, c = parse_ratio_title(title)
        assert a == "入札参加資格申請"
        assert b == "事前知識"
        assert c == 9

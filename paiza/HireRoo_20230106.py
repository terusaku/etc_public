pattern = {
    "(": ")",
    "{": "}",
    "[": "]",
}


def main(s):
    if not (len(s) % 2) == 0:
        return False
    
    input_data = [i for i in s]
    end_sign = []
    for data in input_data:
        if data in end_sign:
            if data == end_sign[-1]:
                del end_sign[-1]
                continue
            else:
                return False
        else:
            try:
                end_sign.append(pattern[data])
            except KeyError:
                return False

    if not end_sign:
        return True
    else:
        return False

# - `pattern`に開始・終了の記号を連想配列で保存する
# - 入力文字列を配列として先頭からループ処理する
# - 期待する文字列の順序としては次の通り
#     - 文字列長は必ず偶数：Line:9の判定
#     - 終了記号はLIFOの順でくる：Line15~20のように`end_sign`配列を末尾から処理する
#     - 終了記号の前に開始記号がくる：Line: 21~25の例外処理
# - Line:27以降では`end_sign`に未処理の終了記号が残っているか判定している
#     - 開始記号のみで閉じられていない場合はFalse

# Charless Go Converter

C言語（サブセット）とCharlessバイトコードを相互に変換するツールのGo言語実装です。
以前のPython実装を置き換えるもので、より高速で、配布しやすい形式になっています。

## 内容物

- **c2charless**: C言語のソースコードをCharlessバイトコード（`.cless`形式）にコンパイルします。
- **charless2c**: CharlessバイトコードをC言語のソースコードにトランスパイル（逆変換）します。

## インストール

### Debian/Ubuntu (.deb)

リリースされている `.deb` パッケージを使用する場合：

```bash
sudo dpkg -i charless-converter_1.0.0_amd64.deb
```

## 使い方

### c2charless (C -> Charless)

```bash
c2charless <input.c> <output.cless>
```

例:
```bash
c2charless sample.c output.cless
```

### charless2c (Charless -> C)

```bash
charless2c <input.cless> <output.c>
```

例:
```bash
charless2c output.cless result.c
```

## ビルド方法

ソースコードからビルドするには Go (1.16以上推奨) と Make が必要です。

```bash
cd GoConverter
make
```

以下のバイナリが `bin/` ディレクトリに生成されます。
- `bin/c2charless`
- `bin/charless2c`

パッケージを作成する場合：
```bash
make package
```
これにより `.deb` パッケージが生成されます。

## 機能・対応状況

- **基本命令**: PRINT, INPUT, PUSH, POP など
- **演算**: 四則演算 (ADD, SUB, MUL, DIV), 剰余 (MOD)
- **制御構文**: if, while (JUMP, JZ, JNZ)
- **変数**: ローカル変数（簡易実装）
- **文字列**: 文字列リテラルの出力
- **v3オペコード対応**: `GTE` (804), `LTE` (805) を含むCharless v3仕様に完全対応しています。

## 開発者向け情報

### テスト

付属の `verify_go.sh` スクリプトを実行することで、変換の整合性をテストできます。

```bash
bash ../verify_go.sh
```

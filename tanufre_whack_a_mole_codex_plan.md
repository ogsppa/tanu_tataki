# タヌフレぱーく：プロジェクター式もぐらたたき 実装計画

## 目的

プロジェクターで壁に「タヌフレぱーく」の看板を投影し、看板からタヌキ・イノシシ・ハムスターが出たり隠れたりする、もぐらたたき風のインタラクティブゲームを作る。

入力は最終的に **Ultraleapのハンドトラッキング** を使う想定だが、開発初期は **マウス入力** でも同じゲームロジックを動かせるようにする。

---

## 前提技術

- Python
- Pygame
- Ultraleap / Leap Motion 系のPython連携コード
- プロジェクターによる全画面表示
- キャラクター画像は個別の透過PNGとして用意する

---

## 基本方針

最初からUltraleap前提で作り込まず、以下の順番で進める。

1. Pygameでマウス版を完成させる
2. 入力処理を抽象化する
3. Ultraleapで取得した手の座標を画面座標に変換する
4. 手の座標でキャラクターを叩けるようにする
5. プロジェクター投影環境で座標補正する
6. ヒット演出・スコア・効果音・全画面表示を整える

重要なのは、**ゲーム本体と入力装置を分離すること**。
マウス入力、キーボード入力、Ultraleap入力を差し替えられる構成にする。

---

## ゲーム内容

### 表示内容

- 背景または黒背景
- 「タヌフレぱーく」の看板画像
- 看板から出る3体のキャラクター
  - タヌキ
  - イノシシ
  - ハムスター
- スコア
- 残り時間
- 必要に応じてデバッグ用の手カーソル表示

### 基本ルール

- 3体のうちランダムに1体または複数体が出る
- 出ているキャラクターを叩くとスコア加算
- 叩かれたキャラクターは一瞬ヒット画像に切り替わり、その後すぐ引っ込む
- 一定時間叩かれなかったキャラクターも引っ込む
- 制限時間終了でゲーム終了

---

## キャラクター画像仕様

各キャラクターごとに、最低2種類の透過PNGを用意する。

```text
assets/
  sign.png

  tanuki_normal.png
  tanuki_hit.png

  boar_normal.png
  boar_hit.png

  hamster_normal.png
  hamster_hit.png
```

### 画像切り替えの考え方

叩かれた瞬間は、通常画像からヒット画像に切り替える。

```text
通常画像
↓
ヒット画像に切り替え
↓ 0.1〜0.2秒程度表示
効果音・スコア加算
↓
看板の裏へ引っ込む
```

「ヒット画像に変えてから通常画像に戻す」よりも、**ヒット画像を一瞬表示して、そのまま引っ込む**ほうが、もぐらたたきらしい手応えが出る。

---

## キャラクター状態管理

キャラクターごとに状態を持たせる。

```text
hidden   : 完全に隠れている
rising   : 看板から出てくる途中
visible  : 叩ける状態
hit      : 叩かれてヒット画像を表示中
falling  : 引っ込む途中
```

### 状態遷移

```text
hidden
  ↓
rising
  ↓
visible
  ↓ 叩かれた場合
hit
  ↓
falling
  ↓
hidden
```

叩かれずに一定時間経過した場合も、`visible` から `falling` に移る。

---

## Moleクラスのイメージ

```python
class Mole:
    def __init__(self, name, normal_img, hit_img, x, y):
        self.name = name
        self.normal_img = normal_img
        self.hit_img = hit_img
        self.x = x
        self.y = y
        self.state = "hidden"
        self.visible_amount = 0.0
        self.hit_timer = 0.0
        self.visible_timer = 0.0
        self.cooldown = 0.0
```

### visible_amount

`visible_amount` を `0.0〜1.0` で持つ。

```text
0.0 : 完全に隠れている
0.5 : 半分出ている
1.0 : 完全に出ている
```

これを使って、看板からキャラクターが「にゅっ」と出る動きを作る。

---

## 入力処理の抽象化

ゲーム本体は、入力がマウスなのかUltraleapなのかを意識しない。

入力側は、毎フレーム `InputPoint` のリストを返すだけにする。

```python
class InputPoint:
    def __init__(self, x, y, z=0, vx=0, vy=0, vz=0, active=False):
        self.x = x
        self.y = y
        self.z = z
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.active = active
```

ゲーム側は以下のように扱う。

```python
points = input_provider.get_points()

for point in points:
    check_hit(point)
```

### 入力プロバイダー候補

```text
MouseInput      : マウス位置とクリックを使う
KeyboardInput   : 1/2/3キーなどで強制ヒットさせるデバッグ用
UltraleapInput  : Ultraleapから手の位置を取得する
```

開発時・展示時のトラブル対策として、マウス入力とキーボード入力は残しておく。

---

## Ultraleap入力の考え方

Ultraleapから取得するのは、空間上の手の位置。
Pygameで必要なのは、画面上の座標。

そのため、以下の変換が必要。

```text
Ultraleapの手座標
例: x=-120, y=250, z=80

↓ 座標変換

Pygame画面座標
例: x=640, y=360
```

### 座標変換の基本式

```python
screen_x = (hand_x - leap_min_x) / (leap_max_x - leap_min_x) * screen_width
screen_y = screen_height - (hand_y - leap_min_y) / (leap_max_y - leap_min_y) * screen_height
```

`screen_y` は、Ultraleapの上方向と画面座標の下方向が逆になる可能性があるため、必要に応じて反転する。

---

## キャリブレーション設定

プロジェクター投影環境では、手の位置と画面上の座標がズレやすい。
そのため、座標変換の範囲は設定ファイルで調整できるようにする。

```json
{
  "screen_width": 1280,
  "screen_height": 720,
  "fullscreen": false,

  "leap_min_x": -250,
  "leap_max_x": 250,
  "leap_min_y": 100,
  "leap_max_y": 500,

  "hit_vz_threshold": 300,
  "hit_cooldown": 0.3,
  "show_debug_cursor": true
}
```

最初は厳密なキャリブレーションUIを作らず、設定値を編集して合わせる方式でよい。
余裕があれば、後で画面四隅を手で合わせるキャリブレーション画面を追加する。

---

## ヒット判定

### 最初の実装

まずは単純に、手またはマウスの座標がキャラクターの当たり判定内に入ったらヒットにする。

```text
キャラクターが visible 状態
かつ
入力座標が hitbox 内
→ ヒット
```

### 次の段階

誤反応を減らすため、以下の条件を追加する。

```text
キャラクターが visible 状態
かつ
入力座標が hitbox 内
かつ
前回ヒットから一定時間以上経過
かつ
必要に応じて、手が壁方向へ動いている
```

コードイメージ：

```python
if mole.state == "visible":
    if mole.hitbox.collidepoint(point.x, point.y):
        if point.active:
            mole.hit()
```

押し込み速度を使う場合：

```python
if mole.state == "visible":
    if mole.hitbox.collidepoint(point.x, point.y):
        if point.vz > hit_vz_threshold:
            mole.hit()
```

ただし、UltraleapのZ方向は設置方法によって意味が変わるため、最初は速度条件なしで作る。

---

## 手のどこで叩くか

最初は **手のひら中心** を使うのがおすすめ。

```text
手のひら中心:
  もぐらたたきっぽい。
  ラフに叩いても判定しやすい。

人差し指先:
  精密に押せるが、叩くよりタッチ操作に近くなる。

複数指先:
  判定点が増えるため、誤反応が起きやすい可能性がある。
```

最初は手のひら中心で実装し、必要に応じて人差し指先に切り替えられるようにする。

---

## 描画レイヤー

看板からキャラクターが出る表現を作るため、描画順を意識する。

基本の描画順：

```text
背景
↓
キャラクター
↓
看板前面レイヤー
↓
スコア・時間・デバッグ表示
```

理想的には、看板画像を以下の2枚に分ける。

```text
sign_back.png   : 背景用
sign_front.png  : キャラクターを隠すための前面マスク用
```

ただし初期実装では `sign.png` 1枚でもよい。
その場合は、キャラクターの表示位置やクリッピングで、看板から出ているように見せる。

---

## 推奨ディレクトリ構成

```text
tanufre_whack/
  main.py

  game/
    mole.py
    game_state.py
    renderer.py

  input/
    base.py
    mouse_input.py
    keyboard_input.py
    ultraleap_input.py

  config/
    settings.json

  assets/
    sign.png
    tanuki_normal.png
    tanuki_hit.png
    boar_normal.png
    boar_hit.png
    hamster_normal.png
    hamster_hit.png
    hit.wav
```

---

## 開発ステップ

### Step 1: Pygame表示

- Pygameウィンドウを開く
- 看板画像を表示する
- キャラクター画像を指定位置に表示する

### Step 2: マウス版ヒット判定

- マウスクリックでキャラクターを叩けるようにする
- 叩いたらスコアを加算する

### Step 3: ヒット画像切り替え

- 通常画像とヒット画像を切り替える
- ヒット画像を0.1〜0.2秒表示する
- その後キャラクターを引っ込める

### Step 4: キャラクター出現制御

- ランダムにキャラクターが出る
- 一定時間で引っ込む
- 複数体同時出現も後から対応できるようにする

### Step 5: ゲームUI

- スコア表示
- 残り時間表示
- ゲーム開始・終了状態
- リセット機能

### Step 6: 入力抽象化

- `MouseInput`
- `KeyboardInput`
- `UltraleapInput`

を同じインターフェースで使えるようにする。

### Step 7: Ultraleap座標表示

- Ultraleapで手の位置を取得する
- Pygame画面上にデバッグ用の丸を表示する
- 実際の手の位置と投影位置が合うように設定値を調整する

### Step 8: Ultraleapヒット判定

- 手のひら中心、または指先がキャラクターの当たり判定に入ったらヒットにする
- クールダウンを入れて連続誤判定を防ぐ

### Step 9: プロジェクター調整

- 全画面表示に対応する
- 投影サイズに合わせて座標を調整する
- デバッグカーソルのON/OFFを設定可能にする

### Step 10: 展示向け調整

- 効果音
- コンボ
- 難易度上昇
- 待機画面
- 自動リスタート
- 入力エラー時のフォールバック

---

## 最初に作るべき最小版

まずは以下の仕様を満たすものを作る。

```text
- 60秒ゲーム
- 3匹のうち1匹がランダムに出る
- マウスクリックで叩ける
- 叩いたらヒット画像に変わる
- スコアが増える
- キャラクターがすぐ引っ込む
```

この最小版ができてからUltraleap入力を接続する。

---

## Codexへの実装指示メモ

実装時は以下を優先する。

1. まずPygame + マウス入力で動く最小版を作る
2. 入力処理は必ず抽象化し、後からUltraleap入力を追加できるようにする
3. キャラクター状態は `hidden / rising / visible / hit / falling` で管理する
4. 画像パス、座標、速度、ヒット判定、Ultraleap座標範囲は設定ファイルから変更できるようにする
5. デバッグ表示として、入力座標・当たり判定・現在状態を画面に表示できるようにする
6. Ultraleapが未接続でも、マウス入力で起動・テストできるようにする
7. 最初から複雑な演出を入れず、遊べる最小版を優先する

---

## 将来的な追加案

- 叩いた瞬間に星や煙のエフェクトを出す
- キャラクターごとに点数を変える
- ハムスターは小さくて高得点にする
- イノシシは出現時間が短い
- タヌキはフェイントで一瞬だけ出る
- コンボ表示
- ランキング
- 待機中のデモアニメーション
- 物理ボタン入力やキーボード入力との併用
- キャリブレーション画面

---

## 実装上の注意

- Ultraleapの座標は設置向きによって軸の意味が変わる可能性がある
- 最初はZ方向の押し込み速度を使わず、手の位置だけでヒット判定する
- 誤反応が多い場合に、クールダウンや速度条件を追加する
- プロジェクター環境では、実際の手の位置と画面上の座標がズレるため、調整用の設定を必ず用意する
- 展示時にUltraleapが認識しづらい場合に備え、マウス・キーボード入力を残す
- 画面上にデバッグカーソルを出せるようにしておくと、現地調整がかなり楽になる

import pyxel


class HanoiGame:
    WIDTH = 240
    HEIGHT = 180

    # 棒の x 座標
    PEG_X = [45, 120, 195]

    # 棒と床の位置
    FLOOR_Y = 150
    PEG_TOP_Y = 45

    # アニメーション速度
    ANIMATION_SPEED = 0.28

    def __init__(self):
        pyxel.init(self.WIDTH, self.HEIGHT, title="ハノイの塔")
        pyxel.mouse(True)

        self.scene = "select"
        self.ring_count = 4

        # 各棒に置かれている輪
        self.pegs = []

        # 輪を持っている状態
        self.dragging = False
        self.drag_ring = None
        self.drag_from = None
        self.drag_target = None

        # 持っている輪の座標
        self.drag_x = 0
        self.drag_y = 0

        # 持ち上げアニメーション用
        self.animating = False
        self.anim_type = None
        self.anim_start_y = 0
        self.anim_end_y = 0
        self.anim_t = 0

        # 落下中の輪
        self.falling_rings = []

        self.moves = 0

        pyxel.run(self.update, self.draw)

    # -------------------------
    # ゲーム開始・リセット
    # -------------------------

    def start_game(self):
        self.pegs = [
            list(range(self.ring_count, 0, -1)),
            [],
            []
        ]

        self.moves = 0

        self.dragging = False
        self.drag_ring = None
        self.drag_from = None
        self.drag_target = None

        self.animating = False
        self.anim_type = None
        self.anim_t = 0

        self.falling_rings = []

        self.scene = "game"

    def reset_game(self):
        """現在の輪の数のまま、初期配置に戻す"""
        self.pegs = [
            list(range(self.ring_count, 0, -1)),
            [],
            []
        ]

        self.moves = 0

        self.dragging = False
        self.drag_ring = None
        self.drag_from = None
        self.drag_target = None

        self.animating = False
        self.anim_type = None
        self.anim_t = 0

        self.falling_rings = []

    # -------------------------
    # 更新処理
    # -------------------------

    def update(self):
        if self.scene == "select":
            self.update_select()

        elif self.scene == "game":
            self.update_game()

        elif self.scene == "clear":
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                self.scene = "select"

    def update_select(self):
        # キーボードで輪の数を変更
        if pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_MINUS):
            self.ring_count = max(3, self.ring_count - 1)

        if pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_PLUS):
            self.ring_count = min(8, self.ring_count + 1)

        # マウスで輪の数を変更・ゲーム開始
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            x = pyxel.mouse_x
            y = pyxel.mouse_y

            # −ボタン
            if 30 <= x <= 85 and 90 <= y <= 115:
                self.ring_count = max(3, self.ring_count - 1)

            # ＋ボタン
            elif 155 <= x <= 210 and 90 <= y <= 115:
                self.ring_count = min(8, self.ring_count + 1)

            # STARTボタン
            elif 80 <= x <= 160 and 125 <= y <= 150:
                self.start_game()

    def update_game(self):
        # -------------------------
        # RESET / TITLE ボタン
        # -------------------------

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            x = pyxel.mouse_x
            y = pyxel.mouse_y

            # RESETボタン
            if 145 <= x <= 190 and 5 <= y <= 18:
                self.reset_game()
                return

            # TITLEボタン
            if 195 <= x <= 235 and 5 <= y <= 18:
                self.dragging = False
                self.drag_ring = None
                self.drag_from = None
                self.drag_target = None

                self.animating = False
                self.anim_type = None
                self.anim_t = 0

                self.falling_rings = []
                self.scene = "select"
                return

        # 落下中の輪は、ほかの操作と同時に更新する
        self.update_falling_rings()

        # -------------------------
        # 持ち上げアニメーション中
        # -------------------------

        if self.animating:
            # 持ち上げ中に指を離したら元の場所へ戻す
            if self.anim_type == "lift":
                if not pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
                    self.cancel_lift()
                    return

                self.update_animation()
                return

        # -------------------------
        # 輪を持っていない状態
        # -------------------------

        if not self.dragging:
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                peg = self.get_peg_at_mouse()

                # 棒の一番上の輪を持ち上げる
                if peg is not None and len(self.pegs[peg]) > 0:
                    self.start_lift_animation(peg)

            return

        # -------------------------
        # 輪を持って移動中
        # -------------------------

        # マウスに一番近い棒を取得
        nearest_peg = self.get_nearest_peg()

        # 輪を一番近い棒の中央へスナップ
        self.drag_target = nearest_peg
        self.drag_x = self.PEG_X[nearest_peg]

        # クリックを離した
        if pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT):
            if self.can_put(nearest_peg, self.drag_ring):
                # 置ける場合は落下アニメーション
                self.start_drop_animation(nearest_peg)
            else:
                # 置けない場合は元の棒へ瞬間的に戻す
                self.pegs[self.drag_from].append(self.drag_ring)

                self.dragging = False
                self.drag_ring = None
                self.drag_from = None
                self.drag_target = None

    # -------------------------
    # 輪を持ち上げる処理
    # -------------------------

    def start_lift_animation(self, peg):
        """棒から一番上の輪を取り出して持ち上げる"""
        self.dragging = True
        self.drag_from = peg
        self.drag_target = peg

        # 棒の一番上の輪を取り出す
        self.drag_ring = self.pegs[peg].pop()

        self.drag_x = self.PEG_X[peg]

        # 輪が置かれていた位置
        start_level = len(self.pegs[peg])
        self.drag_y = self.get_ring_y(start_level)

        # 上へ持ち上げる
        self.anim_start_y = self.drag_y
        self.anim_end_y = 25
        self.anim_t = 0

        self.anim_type = "lift"
        self.animating = True

    def cancel_lift(self):
        """持ち上げ中に指を離した場合、元の棒へ戻す"""
        if self.drag_from is not None and self.drag_ring is not None:
            self.pegs[self.drag_from].append(self.drag_ring)

        self.dragging = False
        self.drag_ring = None
        self.drag_from = None
        self.drag_target = None

        self.animating = False
        self.anim_type = None
        self.anim_t = 0

    # -------------------------
    # 輪を落とす処理
    # -------------------------

    def start_drop_animation(self, peg):
        """
        目的の棒へ輪を落とす。
        落下中も別の輪を操作できるようにする。
        """
        self.drag_target = peg
        self.drag_x = self.PEG_X[peg]

        # 輪を置く高さ
        target_level = len(self.pegs[peg])
        target_y = self.get_ring_y(target_level)

        # 論理上は先に棒へ入れておく
        # これにより次の操作の判定が可能になる
        self.pegs[peg].append(self.drag_ring)

        # 落下中の輪として登録
        self.falling_rings.append({
            "ring": self.drag_ring,
            "peg": peg,
            "x": self.PEG_X[peg],
            "y": self.drag_y,
            "start_y": self.drag_y,
            "target_y": target_y,
            "t": 0
        })

        self.moves += 1

        # 現在の操作を終了
        self.dragging = False
        self.drag_ring = None
        self.drag_from = None
        self.drag_target = None

        # 右端の棒にすべて移動したらクリア
        # if self.pegs[2] == list(range(self.ring_count, 0, -1)):
        #     self.scene = "clear"
        
    def update_falling_rings(self):
        """落下中の輪を更新する"""
        finished = []
    
        for falling in self.falling_rings:
            falling["t"] += self.ANIMATION_SPEED
    
            if falling["t"] >= 1:
                falling["t"] = 1
                falling["y"] = falling["target_y"]
                finished.append(falling)
    
            else:
                t = self.ease_out(falling["t"])
    
                falling["y"] = (
                    falling["start_y"]
                    + (
                        falling["target_y"]
                        - falling["start_y"]
                    ) * t
                )
    
        # 落下完了した輪を一覧から削除
        for falling in finished:
            if falling in self.falling_rings:
                self.falling_rings.remove(falling)
    
        # まだ落下中の輪がある場合は、クリア判定しない
        if self.falling_rings:
            return
    
        # すべての輪が右端にあり、落下も完全に終わった場合だけクリア
        if self.pegs[2] == list(range(self.ring_count, 0, -1)):
            self.scene = "clear"

    def update_animation(self):
        """持ち上げアニメーションを更新する"""
        self.anim_t += self.ANIMATION_SPEED

        if self.anim_t >= 1:
            self.anim_t = 1
            self.drag_y = self.anim_end_y
            self.animating = False

            # 持ち上げ完了
            if self.anim_type == "lift":
                self.drag_y = 25
                self.anim_type = None

            return

        # なめらかに動かす
        t = self.ease_out(self.anim_t)

        self.drag_y = (
            self.anim_start_y
            + (
                self.anim_end_y
                - self.anim_start_y
            ) * t
        )

    def ease_out(self, t):
        """最初は速く、最後はゆっくりになる動き"""
        return 1 - (1 - t) * (1 - t)

    # -------------------------
    # 判定
    # -------------------------

    def get_peg_at_mouse(self):
        """
        棒の範囲全体をタップ判定にする。
        輪そのものをタップしなくてもよい。
        """
        mouse_x = pyxel.mouse_x
        mouse_y = pyxel.mouse_y

        for i, peg_x in enumerate(self.PEG_X):
            # 落下中の輪がある棒は操作しない
            if self.has_falling_ring_on_peg(i):
                continue

            # 棒の左右28ピクセル以内
            if abs(mouse_x - peg_x) <= 28:

                # 棒の上端から床までの範囲
                if self.PEG_TOP_Y - 10 <= mouse_y <= self.FLOOR_Y + 8:
                    return i

        return None

    def get_nearest_peg(self):
        """マウスに一番近い棒を返す"""
        mouse_x = pyxel.mouse_x

        distances = [
            abs(mouse_x - peg_x)
            for peg_x in self.PEG_X
        ]

        return distances.index(min(distances))

    def has_falling_ring_on_peg(self, peg):
        """その棒に落下中の輪があるか調べる"""
        for falling in self.falling_rings:
            if falling["peg"] == peg:
                return True

        return False

    def can_put(self, peg, ring):
        """その棒に輪を置けるか判定"""
        # 落下中の輪がある棒には置けない
        if self.has_falling_ring_on_peg(peg):
            return False

        # 空の棒には置ける
        if not self.pegs[peg]:
            return True

        # 小さい輪の上に大きい輪は置けない
        return self.pegs[peg][-1] > ring

    # -------------------------
    # 座標計算
    # -------------------------

    def get_ring_y(self, level):
        """輪の段数を画面上の y 座標へ変換する"""
        return self.FLOOR_Y - 7 - level * 9

    # -------------------------
    # 描画
    # -------------------------

    def draw(self):
        pyxel.cls(1)

        if self.scene == "select":
            self.draw_select()

        elif self.scene == "game":
            self.draw_game()

        elif self.scene == "clear":
            self.draw_game()
            self.draw_clear()

    def draw_select(self):
        pyxel.text(75, 25, "HANOI TOWER", 7)
        pyxel.text(68, 45, "RING SELECT", 6)

        pyxel.text(42, 75, "RINGS", 7)
        pyxel.text(112, 75, str(self.ring_count), 10)

        # −ボタン
        pyxel.rect(30, 90, 55, 25, 8)
        pyxel.text(53, 99, "-", 7)

        # ＋ボタン
        pyxel.rect(155, 90, 55, 25, 11)
        pyxel.text(178, 99, "+", 7)

        # STARTボタン
        pyxel.rect(80, 125, 80, 25, 3)
        pyxel.text(96, 134, "START", 7)

        pyxel.text(35, 165, "LEFT/RIGHT: SELECT", 6)

    def draw_game(self):
        pyxel.text(8, 8, f"MOVES: {self.moves}", 7)

        # RESETボタン
        pyxel.rect(145, 5, 45, 14, 10)
        pyxel.text(149, 9, "RESET", 7)

        # TITLEボタン
        pyxel.rect(195, 5, 40, 14, 8)
        pyxel.text(199, 9, "TITLE", 7)

        # 棒
        for x in self.PEG_X:
            pyxel.rect(
                x - 2,
                self.PEG_TOP_Y,
                5,
                self.FLOOR_Y - self.PEG_TOP_Y,
                13
            )

            # 棒の土台
            pyxel.rect(
                x - 25,
                self.FLOOR_Y,
                50,
                5,
                13
            )

        # 棒に置かれている輪
        for peg_index, rings in enumerate(self.pegs):
            visible_rings = list(rings)

            # 落下中の輪は、棒側の描画から一時的に除外する
            for falling in self.falling_rings:
                if falling["peg"] == peg_index:
                    if falling["ring"] in visible_rings:
                        visible_rings.remove(falling["ring"])

            for level, ring in enumerate(visible_rings):
                x = self.PEG_X[peg_index]
                y = self.get_ring_y(level)

                self.draw_ring(x, y, ring)

        # 持って移動中の輪
        if self.dragging:
            self.draw_ring(
                self.drag_x,
                int(self.drag_y),
                self.drag_ring
            )

        # 落下中の輪
        for falling in self.falling_rings:
            self.draw_ring(
                falling["x"],
                int(falling["y"]),
                falling["ring"]
            )

        # 左端の色見本
        self.draw_ring_legend()

    def draw_ring(self, x, y, ring):
        """通常の輪を描画する"""
        width = 12 + ring * 7
        height = 7

        color = 2 + (ring % 12)

        # 輪本体
        pyxel.rect(
            x - width // 2,
            y - height // 2,
            width,
            height,
            color
        )

        # 輪の枠線
        pyxel.rectb(
            x - width // 2,
            y - height // 2,
            width,
            height,
            7
        )

    def draw_ring_legend(self):
        """
        画面左端に色見本を表示する。
        上が小さい輪、下が大きい輪。
        """
        x = 3
        start_y = 70
        square_size = 7
        gap = 2

        for index, ring in enumerate(
            range(1, self.ring_count + 1)
        ):
            y = start_y + index * (square_size + gap)
            color = 2 + (ring % 12)

            # 大きさが均一の四角
            pyxel.rect(
                x,
                y,
                square_size,
                square_size,
                color
            )

            pyxel.rectb(
                x,
                y,
                square_size,
                square_size,
                7
            )

    def draw_clear(self):
        pyxel.rect(35, 65, 170, 55, 0)
        pyxel.rectb(35, 65, 170, 55, 7)

        pyxel.text(78, 78, "CLEAR!", 10)
        pyxel.text(58, 93, f"MOVES: {self.moves}", 7)
        pyxel.text(50, 108, "CLICK TO CONTINUE", 6)


HanoiGame()

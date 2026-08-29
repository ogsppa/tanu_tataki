(function () {
  "use strict";

  var DESIGN_WIDTH = 1200;
  var DESIGN_HEIGHT = 900;
  var GAME_SECONDS = 30;
  var COUNTDOWN_SECONDS = 3.8;
  var RESULT_SECONDS = 30;
  var PRIZE_SCORE = 50;
  var NAVY = "#122e58";
  var WHITE = "#ffffff";
  var SHADOW = "#141822";

  var canvas = document.getElementById("game");
  var ctx = canvas.getContext("2d");
  var images = {};
  var imageMasks = {};
  var sounds = {};
  var viewport = { x: 0, y: 0, width: DESIGN_WIDTH, height: DESIGN_HEIGHT, scale: 1 };
  var state = {
    screen: "loading",
    score: 0,
    remaining: GAME_SECONDS,
    countdown: 0,
    resultTimer: 0,
    spawnTimer: 0,
    speedUpTimer: 0,
    combo: 0,
    comboTimer: 0,
    comboPopTimer: 0,
    comboBonusTimer: 0,
    lastPhase: 0,
    moles: [],
    pointer: { x: 0, y: 0, active: false },
    lastTime: 0
  };

  var assets = {
    background: "assets/background.png",
    menuBg: "assets/bg.png",
    title: "assets/title.png",
    sign: "assets/sign.png",
    instructionTanu: "assets/instruction_tanu.png",
    instructionIno: "assets/instruction_ino.png",
    tanukiNormal: "assets/tanuki_normal.png",
    tanukiHit: "assets/tanuki_hit.png",
    boarNormal: "assets/boar_normal.png",
    boarHit: "assets/boar_hit.png",
    hamsterNormal: "assets/hamster_normal.png",
    hamsterHit: "assets/hamster_hit.png"
  };

  var soundAssets = {
    gameBgm: "assets/sounds/bgm.mp3",
    menuBgm: "assets/sounds/bgm_menu.mp3",
    hit: "assets/sounds/hit.mp3",
    ok: "assets/sounds/ok.mp3"
  };

  var moleSpecs = [
    { name: "tanuki", normal: "tanukiNormal", hit: "tanukiHit", width: 242, points: 1, reaction: "うわ！" },
    { name: "boar", normal: "boarNormal", hit: "boarHit", width: 265, points: 1, reaction: "ギャ！" },
    { name: "hamster", normal: "hamsterNormal", hit: "hamsterHit", width: 220, points: 1, reaction: "ぴー！" }
  ];

  function loadImages() {
    var keys = Object.keys(assets);
    var loaded = 0;
    keys.forEach(function (key) {
      var image = new Image();
      image.onload = function () {
        loaded += 1;
        if (loaded === keys.length) {
          buildImageMasks();
          initGame();
        }
      };
      image.onerror = function () {
        loaded += 1;
        if (loaded === keys.length) {
          buildImageMasks();
          initGame();
        }
      };
      image.src = assets[key];
      images[key] = image;
    });
  }

  function buildImageMasks() {
    Object.keys(images).forEach(function (key) {
      var image = images[key];
      if (!image || !image.width || !image.height) return;
      try {
        var buffer = document.createElement("canvas");
        var bufferCtx = buffer.getContext("2d");
        buffer.width = image.width;
        buffer.height = image.height;
        bufferCtx.drawImage(image, 0, 0);
        imageMasks[key] = bufferCtx.getImageData(0, 0, image.width, image.height).data;
      } catch (error) {}
    });
  }

  function loadSounds() {
    Object.keys(soundAssets).forEach(function (key) {
      var audio = new Audio(soundAssets[key]);
      audio.preload = "auto";
      audio.volume = key === "gameBgm" || key === "menuBgm" ? 0.45 : 0.8;
      if (key === "gameBgm" || key === "menuBgm") audio.loop = true;
      sounds[key] = audio;
    });
  }

  function initGame() {
    state.moles = moleSpecs.map(function (spec) {
      return {
        spec: spec,
        state: "hidden",
        visibleAmount: 0,
        visibleTimer: 0,
        hitTimer: 0,
        cooldown: 0,
        edge: "top",
        hiddenCenter: { x: DESIGN_WIDTH / 2, y: DESIGN_HEIGHT / 2 },
        targetCenter: { x: DESIGN_WIDTH / 2, y: DESIGN_HEIGHT / 2 },
        riseSeconds: 0.22,
        fallSeconds: 0.2
      };
    });
    state.screen = "start";
    state.lastTime = nowMs();
    resize();
    requestAnimationFrame(loop);
  }

  function resize() {
    var ratio = 1;
    var width = Math.max(1, Math.floor(window.innerWidth * ratio));
    var height = Math.max(1, Math.floor(window.innerHeight * ratio));
    var scale = Math.min(width / DESIGN_WIDTH, height / DESIGN_HEIGHT);
    var viewportWidth = DESIGN_WIDTH * scale;
    var viewportHeight = DESIGN_HEIGHT * scale;
    canvas.width = width;
    canvas.height = height;
    viewport = {
      x: (width - viewportWidth) / 2,
      y: (height - viewportHeight) / 2,
      width: viewportWidth,
      height: viewportHeight,
      scale: scale
    };
    applyGameTransform();
  }

  function loop(now) {
    var dt = Math.min(0.05, (now - state.lastTime) / 1000 || 0);
    state.lastTime = now;
    update(dt);
    draw();
    requestAnimationFrame(loop);
  }

  function update(dt) {
    if (state.screen === "countdown") {
      state.countdown = Math.max(0, state.countdown - dt);
      if (state.countdown <= 0) {
        startPlaying();
      }
      return;
    }
    if (state.screen === "result") {
      state.resultTimer = Math.max(0, state.resultTimer - dt);
      if (state.resultTimer <= 0) {
        state.screen = "start";
        playMenuBgm();
      }
      return;
    }
    if (state.screen !== "playing") {
      return;
    }

    state.remaining = Math.max(0, state.remaining - dt);
    if (state.remaining <= 0) {
      state.screen = "result";
      state.resultTimer = RESULT_SECONDS;
      hideAllMoles();
      stopGameBgm();
      playMenuBgm();
      return;
    }

    var phase = speedPhase();
    if (phase > state.lastPhase) {
      state.lastPhase = phase;
      state.speedUpTimer = 1.5;
    }
    state.speedUpTimer = Math.max(0, state.speedUpTimer - dt);
    state.comboTimer = Math.max(0, state.comboTimer - dt);
    state.comboPopTimer = Math.max(0, state.comboPopTimer - dt);
    state.comboBonusTimer = Math.max(0, state.comboBonusTimer - dt);
    if (state.comboTimer <= 0) state.combo = 0;

    state.moles.forEach(function (mole) {
      updateMole(mole, dt);
    });

    state.spawnTimer -= dt;
    if (state.spawnTimer <= 0) {
      spawnRandomMole();
      var interval = spawnInterval();
      state.spawnTimer = randomBetween(interval[0], interval[1]);
    }
  }

  function updateMole(mole, dt) {
    if (mole.cooldown > 0) {
      mole.cooldown = Math.max(0, mole.cooldown - dt);
    }
    if (mole.state === "rising") {
      mole.visibleAmount = Math.min(1, mole.visibleAmount + dt / mole.riseSeconds);
      if (mole.visibleAmount >= 1) mole.state = "visible";
    } else if (mole.state === "visible") {
      mole.visibleTimer -= dt;
      if (mole.visibleTimer <= 0) mole.state = "falling";
    } else if (mole.state === "hit") {
      mole.hitTimer -= dt;
      if (mole.hitTimer <= 0) mole.state = "falling";
    } else if (mole.state === "falling") {
      mole.visibleAmount = Math.max(0, mole.visibleAmount - dt / mole.fallSeconds);
      if (mole.visibleAmount <= 0) {
        mole.state = "hidden";
        mole.cooldown = 0.15;
      }
    }
  }

  function draw() {
    clear();
    if (state.screen === "start" || state.screen === "instructions") {
      drawMenuBackground();
    } else {
      drawCover(images.background, 0, 0, DESIGN_WIDTH, DESIGN_HEIGHT);
      drawMoles();
      drawImageFit(images.sign, signRect());
      drawHitReactions();
      drawCombo();
    }
    drawHud();
  }

  function clear() {
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = WHITE;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.restore();
  }

  function drawMenuBackground() {
    drawCover(images.menuBg, 0, 0, DESIGN_WIDTH, DESIGN_HEIGHT);
    var size = DESIGN_HEIGHT;
    ctx.fillStyle = WHITE;
    ctx.fillRect((DESIGN_WIDTH - size) / 2, 0, size, size);
  }

  function drawHud() {
    if (state.screen === "playing" || state.screen === "countdown" || state.screen === "result") {
      label("SCORE " + state.score, 28, 54, 34, WHITE, true);
      label("TIME " + twoDigits(Math.ceil(state.remaining)), DESIGN_WIDTH - 190, 54, 34, WHITE, true);
    }
    if (state.screen === "start") {
      drawImageContain(images.title, DESIGN_WIDTH / 2, DESIGN_HEIGHT * 0.34, DESIGN_WIDTH * 0.52, DESIGN_HEIGHT * 0.46);
      button("すたーと！", buttonRect("start"));
      centerText("50てんいじょうで あいことばをげっとしよう！", DESIGN_HEIGHT - 40, 24, NAVY, false);
    } else if (state.screen === "instructions") {
      drawInstructions();
    } else if (state.screen === "countdown") {
      centerText(countdownText(), 235, 76, WHITE, true);
    } else if (state.screen === "result") {
      centerText("FINISH  SCORE " + state.score, 250, 64, WHITE, true);
      drawResultMessage();
      button("さいしょにもどる", buttonRect("result"));
    } else if (state.speedUpTimer > 0) {
      centerText("SPEED UP", 104, 64, WHITE, true);
    }
  }

  function drawInstructions() {
    var lines = [
      "まんなかのかんばんから、",
      "タヌキ、イノシシさん、はむさんがとびだすよ！",
      "でてきたらタップしよう！"
    ];
    lines.forEach(function (line, index) {
      centerText(line, 118 + index * 42, 30, NAVY, false);
    });
    drawImageContain(images.instructionTanu, DESIGN_WIDTH / 2 - 150, 530, 250, 270);
    drawImageContain(images.instructionIno, DESIGN_WIDTH / 2 + 155, 530, 300, 270);
    button("げーむすたーと", buttonRect("instructions"));
  }

  function drawResultMessage() {
    var lines = state.score >= PRIZE_SCORE
      ? [
          "もくひょうクリアー！おめでとう♪",
          "合言葉は「てんさい」だよ！"
        ]
      : ["おしかった！", "よかったらまたあそんでね！"];
    var startY = state.score >= PRIZE_SCORE ? 630 : 642;
    lines.forEach(function (line, index) {
      centerText(line, startY + index * 34, 24, NAVY, false);
    });
  }

  function drawMoles() {
    state.moles.forEach(function (mole) {
      if (mole.state === "hidden") return;
      var rect = moleRect(mole);
      var image = images[mole.state === "hit" ? mole.spec.hit : mole.spec.normal];
      drawImageFit(image, rect);
    });
  }

  function drawHitReactions() {
    state.moles.forEach(function (mole) {
      if (mole.state !== "hit") return;
      drawReactionText(mole, moleRect(mole));
    });
  }

  function drawCombo() {
    if (state.screen !== "playing" || state.combo < 2) return;
    var pop = 1 + state.comboPopTimer * 0.35;
    ctx.save();
    ctx.translate(DESIGN_WIDTH / 2, 100);
    ctx.rotate(-0.04);
    setFont(Math.round(46 * pop));
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.lineWidth = 10;
    ctx.strokeStyle = "#122e58";
    ctx.fillStyle = "#ffd94a";
    ctx.strokeText(state.combo + "れんぞく！", 0, 0);
    ctx.fillText(state.combo + "れんぞく！", 0, 0);
    if (state.comboBonusTimer > 0) {
      setFont(Math.round(34 * (1 + state.comboBonusTimer * 0.4)));
      ctx.strokeText("+3", 132, 4);
      ctx.fillText("+3", 132, 4);
    }
    ctx.restore();
  }

  function drawReactionText(mole, rect) {
    var pos = reactionPosition(mole, rect);
    var pop = 1 + mole.hitTimer * 1.8;
    ctx.save();
    ctx.translate(pos.x, pos.y);
    ctx.rotate(pos.rotate);
    setFont(Math.round(48 * pop));
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.lineWidth = 9;
    ctx.strokeStyle = "#122e58";
    ctx.fillStyle = "#ffd94a";
    ctx.strokeText(mole.spec.reaction, 0, 0);
    ctx.fillText(mole.spec.reaction, 0, 0);
    ctx.restore();
  }

  function reactionPosition(mole, rect) {
    var x = rect.x + rect.width / 2;
    var y = rect.y - 18;
    var rotate = -0.12;
    if (mole.edge === "bottom") {
      y = rect.y + rect.height + 22;
      rotate = 0.1;
    } else if (mole.edge === "left") {
      x = rect.x - 46;
      y = rect.y + rect.height / 2;
      rotate = -0.18;
    } else if (mole.edge === "right") {
      x = rect.x + rect.width + 46;
      y = rect.y + rect.height / 2;
      rotate = 0.18;
    }
    return {
      x: clamp(x, 88, DESIGN_WIDTH - 88),
      y: clamp(y, 88, DESIGN_HEIGHT - 62),
      rotate: rotate
    };
  }

  function pointerDown(event) {
    var point = eventPoint(event);
    state.pointer = { x: point.x, y: point.y, active: true };
    if (state.screen === "start" && inRect(point, buttonRect("start"))) {
      playSound("ok");
      state.screen = "instructions";
      playMenuBgm();
    } else if (state.screen === "instructions" && inRect(point, buttonRect("instructions"))) {
      playSound("ok");
      beginCountdown();
    } else if (state.screen === "result" && inRect(point, buttonRect("result"))) {
      playSound("ok");
      state.screen = "start";
      state.resultTimer = 0;
      playMenuBgm();
    } else if (state.screen === "playing") {
      if (!hitMoles(point)) resetCombo();
    }
    event.preventDefault();
  }

  function pointerUp(event) {
    state.pointer.active = false;
    event.preventDefault();
  }

  function eventPoint(event) {
    var touch = event.changedTouches && event.changedTouches[0];
    var source = touch || event;
    var rect = canvas.getBoundingClientRect();
    var canvasX = source.clientX - rect.left;
    var canvasY = source.clientY - rect.top;
    return {
      x: (canvasX - viewport.x) / viewport.scale,
      y: (canvasY - viewport.y) / viewport.scale
    };
  }

  function hitMoles(point) {
    if (pointInSign(point)) return true;
    for (var i = 0; i < state.moles.length; i += 1) {
      var mole = state.moles[i];
      if (mole.state === "visible" && pointHitsMole(point, mole)) {
        mole.state = "hit";
        mole.hitTimer = 0.16;
        state.score += mole.spec.points;
        registerCombo();
        playSound("hit");
        return true;
      }
    }
    return false;
  }

  function registerCombo() {
    state.combo += 1;
    state.comboTimer = 1.25;
    state.comboPopTimer = 0.45;
    if (state.combo % 3 === 0) {
      state.score += 3;
      state.comboBonusTimer = 0.75;
    }
  }

  function resetCombo() {
    state.combo = 0;
    state.comboTimer = 0;
    state.comboPopTimer = 0;
    state.comboBonusTimer = 0;
  }

  function beginCountdown() {
    state.score = 0;
    state.remaining = GAME_SECONDS;
    state.countdown = COUNTDOWN_SECONDS;
    state.resultTimer = 0;
    state.screen = "countdown";
    hideAllMoles();
    resetCombo();
    stopMenuBgm();
    playGameBgm();
  }

  function startPlaying() {
    state.score = 0;
    state.remaining = GAME_SECONDS;
    state.spawnTimer = 0.15;
    state.speedUpTimer = 0;
    state.lastPhase = 0;
    state.screen = "playing";
    hideAllMoles();
    resetCombo();
  }

  function hideAllMoles() {
    state.moles.forEach(function (mole) {
      mole.state = "hidden";
      mole.visibleAmount = 0;
      mole.visibleTimer = 0;
      mole.hitTimer = 0;
      mole.cooldown = 0;
    });
  }

  function spawnRandomMole() {
    var activeCount = state.moles.filter(function (mole) { return mole.state !== "hidden"; }).length;
    if (activeCount >= 2) return;
    var choices = state.moles.filter(function (mole) {
      return mole.state === "hidden" && mole.cooldown <= 0;
    });
    shuffle(choices);
    for (var i = 0; i < choices.length; i += 1) {
      var spawn = findSpawn(choices[i]);
      if (!spawn) continue;
      var motion = motionSeconds();
      choices[i].edge = spawn.edge;
      choices[i].hiddenCenter = spawn.hiddenCenter;
      choices[i].targetCenter = spawn.targetCenter;
      choices[i].riseSeconds = motion[0];
      choices[i].fallSeconds = motion[1];
      choices[i].visibleTimer = randomBetween(visibleSeconds()[0], visibleSeconds()[1]);
      choices[i].visibleAmount = 0;
      choices[i].state = "rising";
      return;
    }
  }

  function findSpawn(mole) {
    var edges = ["top", "right", "bottom", "left"];
    for (var i = 0; i < 24; i += 1) {
      var edge = edges[Math.floor(Math.random() * edges.length)];
      var centers = spawnCenters(mole, edge);
      var targetRect = rectAt(mole, centers.targetCenter);
      targetRect.x -= 14;
      targetRect.y -= 14;
      targetRect.width += 28;
      targetRect.height += 28;
      if (!overlapsActive(mole, targetRect)) {
        return { edge: edge, hiddenCenter: centers.hiddenCenter, targetCenter: centers.targetCenter };
      }
    }
    return null;
  }

  function spawnCenters(mole, edge) {
    var size = moleSize(mole);
    var sign = signVisibleRect();
    var halfW = size.width / 2;
    var halfH = size.height / 2;
    var minX = Math.max(halfW, sign.x + halfW);
    var maxX = Math.min(DESIGN_WIDTH - halfW, sign.x + sign.width - halfW);
    var minY = Math.max(halfH, sign.y + halfH);
    var maxY = Math.min(DESIGN_HEIGHT - halfH, sign.y + sign.height - halfH);
    if (edge === "top") {
      var xTop = randomBetween(minX, maxX);
      return { hiddenCenter: { x: xTop, y: sign.y + halfH }, targetCenter: { x: xTop, y: sign.y - 2 } };
    }
    if (edge === "bottom") {
      var xBottom = randomBetween(minX, maxX);
      return { hiddenCenter: { x: xBottom, y: sign.y + sign.height - halfH }, targetCenter: { x: xBottom, y: sign.y + sign.height + 2 } };
    }
    if (edge === "left") {
      var yLeft = randomBetween(minY, maxY);
      return { hiddenCenter: { x: sign.x + halfW, y: yLeft }, targetCenter: { x: sign.x - 2, y: yLeft } };
    }
    var yRight = randomBetween(minY, maxY);
    return { hiddenCenter: { x: sign.x + sign.width - halfW, y: yRight }, targetCenter: { x: sign.x + sign.width + 2, y: yRight } };
  }

  function overlapsActive(candidate, rect) {
    for (var i = 0; i < state.moles.length; i += 1) {
      var mole = state.moles[i];
      if (mole === candidate || mole.state === "hidden") continue;
      var other = rectAt(mole, mole.targetCenter);
      other.x -= 14;
      other.y -= 14;
      other.width += 28;
      other.height += 28;
      if (rectsOverlap(rect, other)) return true;
    }
    return false;
  }

  function speedPhase() {
    var elapsed = GAME_SECONDS - state.remaining;
    if (elapsed >= GAME_SECONDS * 2 / 3) return 2;
    if (elapsed >= GAME_SECONDS / 3) return 1;
    return 0;
  }

  function spawnInterval() {
    var phase = speedPhase();
    if (phase === 2) return [0.22, 0.44];
    if (phase === 1) return [0.38, 0.68];
    return [0.62, 0.96];
  }

  function visibleSeconds() {
    var phase = speedPhase();
    if (phase === 2) return [0.46, 0.74];
    if (phase === 1) return [0.68, 1.0];
    return [0.92, 1.32];
  }

  function motionSeconds() {
    var phase = speedPhase();
    if (phase === 2) return [0.14, 0.13];
    if (phase === 1) return [0.22, 0.19];
    return [0.32, 0.27];
  }

  function countdownText() {
    var elapsed = COUNTDOWN_SECONDS - state.countdown;
    if (elapsed < 1) return "3";
    if (elapsed < 2) return "2";
    if (elapsed < 3) return "1";
    return "すたーと！";
  }

  function signRect() {
    return containRect(images.sign, DESIGN_WIDTH * 0.66, DESIGN_HEIGHT * 0.56, DESIGN_WIDTH / 2, DESIGN_HEIGHT / 2);
  }

  function signVisibleRect() {
    var rect = signRect();
    return {
      x: rect.x + rect.width * 0.03,
      y: rect.y + rect.height * 0.20,
      width: rect.width * 0.94,
      height: rect.height * 0.59
    };
  }

  function pointInSign(point) {
    var rect = signVisibleRect();
    return inRect(point, rect);
  }

  function moleSize(mole) {
    var image = images[mole.spec.normal];
    var ratio = mole.spec.width / image.width;
    return { width: mole.spec.width, height: image.height * ratio };
  }

  function moleRect(mole) {
    var size = moleSize(mole);
    var start = mole.hiddenCenter;
    var end = mole.targetCenter;
    var x = start.x + (end.x - start.x) * mole.visibleAmount;
    var y = start.y + (end.y - start.y) * mole.visibleAmount;
    return { x: x - size.width / 2, y: y - size.height / 2, width: size.width, height: size.height };
  }

  function pointHitsMole(point, mole) {
    var rect = moleRect(mole);
    var padding = 18;
    if (!inRect(point, inflateRect(rect, padding))) return false;
    var image = images[mole.spec.normal];
    var mask = imageMasks[mole.spec.normal];
    if (!image || !mask) return true;
    var localX = point.x - rect.x;
    var localY = point.y - rect.y;
    return nearOpaquePixel(mask, image.width, image.height, localX, localY, rect.width, rect.height, padding);
  }

  function nearOpaquePixel(mask, imageWidth, imageHeight, localX, localY, drawWidth, drawHeight, padding) {
    for (var dy = -padding; dy <= padding; dy += 4) {
      for (var dx = -padding; dx <= padding; dx += 4) {
        if (dx * dx + dy * dy > padding * padding) continue;
        var sampleX = Math.round((localX + dx) / drawWidth * imageWidth);
        var sampleY = Math.round((localY + dy) / drawHeight * imageHeight);
        if (sampleX < 0 || sampleY < 0 || sampleX >= imageWidth || sampleY >= imageHeight) continue;
        if (mask[(sampleY * imageWidth + sampleX) * 4 + 3] > 8) return true;
      }
    }
    return false;
  }

  function rectAt(mole, center) {
    var size = moleSize(mole);
    return { x: center.x - size.width / 2, y: center.y - size.height / 2, width: size.width, height: size.height };
  }

  function buttonRect(name) {
    var centerY = name === "result" ? DESIGN_HEIGHT - 70 : name === "instructions" ? DESIGN_HEIGHT - 76 : DESIGN_HEIGHT - 158;
    return { x: DESIGN_WIDTH / 2 - 180, y: centerY - 38, width: 360, height: 76 };
  }

  function drawImageFit(image, rect) {
    if (!image || !image.width) return;
    ctx.drawImage(image, rect.x, rect.y, rect.width, rect.height);
  }

  function drawImageContain(image, cx, cy, maxW, maxH) {
    if (!image || !image.width) return;
    var rect = containRect(image, maxW, maxH, cx, cy);
    drawImageFit(image, rect);
  }

  function containRect(image, maxW, maxH, cx, cy) {
    var scale = Math.min(maxW / image.width, maxH / image.height);
    var width = image.width * scale;
    var height = image.height * scale;
    return { x: cx - width / 2, y: cy - height / 2, width: width, height: height };
  }

  function drawCover(image, x, y, width, height) {
    if (!image || !image.width) return;
    var scale = Math.max(width / image.width, height / image.height);
    var drawW = image.width * scale;
    var drawH = image.height * scale;
    ctx.drawImage(image, x + (width - drawW) / 2, y + (height - drawH) / 2, drawW, drawH);
  }

  function button(text, rect) {
    ctx.fillStyle = "#1c2a3d";
    roundRect(rect.x, rect.y, rect.width, rect.height, 8);
    ctx.fill();
    ctx.strokeStyle = WHITE;
    ctx.lineWidth = 2;
    roundRect(rect.x, rect.y, rect.width, rect.height, 8);
    ctx.stroke();
    centerText(text, rect.y + rect.height / 2 + 1, 34, WHITE, true);
  }

  function label(text, x, y, size, color, shadow) {
    setFont(size);
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    if (shadow) {
      ctx.fillStyle = SHADOW;
      ctx.fillText(text, x + 3, y + 3);
    }
    ctx.fillStyle = color;
    ctx.fillText(text, x, y);
  }

  function centerText(text, y, size, color, shadow) {
    setFont(size);
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    if (shadow) {
      ctx.fillStyle = SHADOW;
      ctx.fillText(text, DESIGN_WIDTH / 2 + 4, y + 4);
    }
    ctx.fillStyle = color;
    ctx.fillText(text, DESIGN_WIDTH / 2, y);
  }

  function setFont(size) {
    ctx.font = "700 " + size + "px 'Arial Rounded MT Bold', 'Hiragino Maru Gothic ProN', 'Yu Gothic', 'Meiryo', sans-serif";
  }

  function roundRect(x, y, width, height, radius) {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + width - radius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    ctx.lineTo(x + width, y + height - radius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    ctx.lineTo(x + radius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
  }

  function inRect(point, rect) {
    return point.x >= rect.x && point.x <= rect.x + rect.width && point.y >= rect.y && point.y <= rect.y + rect.height;
  }

  function rectsOverlap(a, b) {
    return a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y;
  }

  function inflateRect(rect, amount) {
    return {
      x: rect.x - amount,
      y: rect.y - amount,
      width: rect.width + amount * 2,
      height: rect.height + amount * 2
    };
  }

  function randomBetween(min, max) {
    return min + Math.random() * (max - min);
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function playSound(name) {
    var sound = sounds[name];
    if (!sound) return;
    try {
      var player = sound.cloneNode ? sound.cloneNode() : new Audio(soundAssets[name]);
      player.volume = sound.volume;
      var promise = player.play();
      if (promise && promise.catch) promise.catch(function () {});
    } catch (error) {}
  }

  function playGameBgm() {
    stopMenuBgm();
    playLoop("gameBgm");
  }

  function playMenuBgm() {
    stopGameBgm();
    playLoop("menuBgm");
  }

  function stopGameBgm() {
    stopLoop("gameBgm");
  }

  function stopMenuBgm() {
    stopLoop("menuBgm");
  }

  function playLoop(name) {
    var bgm = sounds[name];
    if (!bgm || !bgm.paused) return;
    try {
      bgm.currentTime = 0;
      var promise = bgm.play();
      if (promise && promise.catch) promise.catch(function () {});
    } catch (error) {}
  }

  function stopLoop(name) {
    var bgm = sounds[name];
    if (!bgm) return;
    try {
      bgm.pause();
      bgm.currentTime = 0;
    } catch (error) {}
  }

  function twoDigits(value) {
    return value < 10 ? "0" + value : String(value);
  }

  function nowMs() {
    return window.performance && performance.now ? performance.now() : Date.now();
  }

  function applyGameTransform() {
    ctx.setTransform(viewport.scale, 0, 0, viewport.scale, viewport.x, viewport.y);
  }

  function shuffle(items) {
    for (var i = items.length - 1; i > 0; i -= 1) {
      var j = Math.floor(Math.random() * (i + 1));
      var temp = items[i];
      items[i] = items[j];
      items[j] = temp;
    }
  }

  window.addEventListener("resize", resize);
  canvas.addEventListener("mousedown", pointerDown);
  canvas.addEventListener("mouseup", pointerUp);
  canvas.addEventListener("touchstart", pointerDown, false);
  canvas.addEventListener("touchend", pointerUp, false);
  canvas.addEventListener("touchmove", function (event) { event.preventDefault(); }, false);
  loadSounds();
  loadImages();
}());

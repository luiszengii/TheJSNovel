《第 159 次记录: 周六傍晚的数学探索 —— 贝塞尔曲线与缓动函数》

---

## 业余项目的动画困扰

周六傍晚 6 点半, 你坐在家里的电脑前, 窗外夕阳的余晖透过百叶窗洒在键盘上。

你正在为自己的业余项目添加一个侧边栏滑入动画。最初你用了最简单的 CSS transition:

```css
.sidebar {
    transition: transform 0.3s;
}

.sidebar.open {
    transform: translateX(0);
}
```

动画确实能工作, 但总觉得有些生硬——侧边栏以恒定速度滑入, 既不优雅也不自然。你想起在各大网站上看到的那种流畅的动画: 开始时缓缓启动, 中间加速, 最后轻柔地停下, 就像现实世界中物体的运动一样。

"应该可以改进的。" 你在 Chrome DevTools 中打开 Animations 面板, 仔细观察自己写的动画曲线——一条笔直的斜线, 代表匀速运动。

你模糊记得 CSS 有个 `ease` 关键字可以让动画更自然。你修改代码:

```css
.sidebar {
    transition: transform 0.3s ease;
}
```

效果确实好了很多! 侧边栏滑入时有了加速和减速的过程, 看起来顺滑了不少。

但你的好奇心被激发了: "ease 到底做了什么? 为什么它能让动画看起来更自然?"

你打开 MDN 文档, 在 `transition-timing-function` 条目下看到了一长串选项:

```
linear - 匀速
ease - 慢速开始, 然后变快, 最后慢速结束
ease-in - 慢速开始
ease-out - 慢速结束
ease-in-out - 慢速开始和结束
cubic-bezier(x1, y1, x2, y2) - 自定义贝塞尔曲线
```

"cubic-bezier?" 你盯着这个陌生的术语, "这是什么数学魔法?"

你点开 Chrome DevTools 的 Timing Function 编辑器, 一个交互式的曲线编辑面板展现在眼前: 两个控制点, 一条优美的曲线, 以及下方不断变化的数值 `cubic-bezier(0.25, 0.1, 0.25, 1.0)`。

你拖动控制点, 看到曲线实时变化, 侧边栏的动画也随之改变——有的像弹簧一样回弹, 有的像汽车一样急停, 有的像羽毛一样飘落。

"这些曲线到底是怎么控制动画的?" 你关掉项目, 决定今晚好好研究一下这个神奇的数学工具。

---

## 贝塞尔曲线的第一次接触

你新建了一个实验项目 `bezier-lab/`, 准备从零开始理解贝塞尔曲线。

首先你需要可视化这条曲线。你写了一个简单的 Canvas 绘制程序:

```html
<!DOCTYPE html>
<html>
<head>
    <title>贝塞尔曲线实验室</title>
    <style>
        canvas {
            border: 1px solid #ccc;
            cursor: crosshair;
        }
        .info {
            font-family: 'Courier New', monospace;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <h2>贝塞尔曲线可视化</h2>
    <canvas id="canvas" width="400" height="400"></canvas>
    <div class="info">
        <div>P0: (0, 400) - 起点 (固定)</div>
        <div>P1: <span id="p1"></span> - 控制点 1 (可拖动)</div>
        <div>P2: <span id="p2"></span> - 控制点 2 (可拖动)</div>
        <div>P3: (400, 0) - 终点 (固定)</div>
        <div style="margin-top: 10px;">
            CSS: <code id="css"></code>
        </div>
    </div>

    <script src="bezier.js"></script>
</body>
</html>
```

然后你实现了交互式的曲线编辑器:

```javascript
// bezier.js
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

// 四个控制点
const points = {
    p0: { x: 0, y: 400 },      // 起点 (0, 1) 在 CSS 坐标系
    p1: { x: 100, y: 300 },    // 控制点 1
    p2: { x: 300, y: 100 },    // 控制点 2
    p3: { x: 400, y: 0 }       // 终点 (1, 0) 在 CSS 坐标系
};

let dragging = null;

// 绘制坐标系
function drawGrid() {
    ctx.strokeStyle = '#eee';
    ctx.lineWidth = 1;

    // 垂直线
    for (let x = 0; x <= 400; x += 50) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, 400);
        ctx.stroke();
    }

    // 水平线
    for (let y = 0; y <= 400; y += 50) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(400, y);
        ctx.stroke();
    }

    // 坐标轴
    ctx.strokeStyle = '#999';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, 400);
    ctx.lineTo(400, 400);
    ctx.lineTo(400, 0);
    ctx.stroke();
}

// 绘制贝塞尔曲线
function drawBezier() {
    ctx.strokeStyle = '#2196F3';
    ctx.lineWidth = 3;

    ctx.beginPath();
    ctx.moveTo(points.p0.x, points.p0.y);
    ctx.bezierCurveTo(
        points.p1.x, points.p1.y,  // 控制点 1
        points.p2.x, points.p2.y,  // 控制点 2
        points.p3.x, points.p3.y   // 终点
    );
    ctx.stroke();
}

// 绘制控制点和辅助线
function drawControlPoints() {
    // 辅助线
    ctx.strokeStyle = '#ccc';
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 5]);

    ctx.beginPath();
    ctx.moveTo(points.p0.x, points.p0.y);
    ctx.lineTo(points.p1.x, points.p1.y);
    ctx.moveTo(points.p2.x, points.p2.y);
    ctx.lineTo(points.p3.x, points.p3.y);
    ctx.stroke();

    ctx.setLineDash([]);

    // 控制点
    Object.entries(points).forEach(([key, point]) => {
        ctx.fillStyle = (key === 'p0' || key === 'p3') ? '#999' : '#FF5722';
        ctx.beginPath();
        ctx.arc(point.x, point.y, 6, 0, Math.PI * 2);
        ctx.fill();
    });
}

// 转换为 CSS cubic-bezier 坐标
function toCSSCoords(point) {
    return {
        x: (point.x / 400).toFixed(3),
        y: ((400 - point.y) / 400).toFixed(3)  // Y 轴翻转
    };
}

// 更新显示
function updateDisplay() {
    const p1CSS = toCSSCoords(points.p1);
    const p2CSS = toCSSCoords(points.p2);

    document.getElementById('p1').textContent = `(${p1CSS.x}, ${p1CSS.y})`;
    document.getElementById('p2').textContent = `(${p2CSS.x}, ${p2CSS.y})`;
    document.getElementById('css').textContent =
        `cubic-bezier(${p1CSS.x}, ${p1CSS.y}, ${p2CSS.x}, ${p2CSS.y})`;
}

// 渲染
function render() {
    ctx.clearRect(0, 0, 400, 400);
    drawGrid();
    drawBezier();
    drawControlPoints();
    updateDisplay();
}

// 鼠标事件
canvas.addEventListener('mousedown', (e) => {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // 检查是否点击了可拖动的控制点
    ['p1', 'p2'].forEach(key => {
        const point = points[key];
        const distance = Math.hypot(x - point.x, y - point.y);
        if (distance < 10) {
            dragging = key;
        }
    });
});

canvas.addEventListener('mousemove', (e) => {
    if (dragging) {
        const rect = canvas.getBoundingClientRect();
        points[dragging].x = Math.max(0, Math.min(400, e.clientX - rect.left));
        points[dragging].y = Math.max(0, Math.min(400, e.clientY - rect.top));
        render();
    }
});

canvas.addEventListener('mouseup', () => {
    dragging = null;
});

// 初始渲染
render();
```

你打开 `index.html`, 看到一个交互式的曲线编辑器出现在屏幕上。你尝试拖动蓝色的控制点, 曲线实时变化, 下方显示对应的 CSS 值:

```
P1: (0.250, 0.250) - 控制点 1
P2: (0.750, 0.750) - 控制点 2
CSS: cubic-bezier(0.250, 0.250, 0.750, 0.750)
```

"原来如此!" 你盯着屏幕, "贝塞尔曲线是由四个点定义的: 起点、终点和两个控制点。控制点决定了曲线的形状。"

你开始系统地实验不同的控制点位置:

1. **两个控制点都在对角线上** → 接近线性, 匀速运动
2. **P1 靠近起点, P2 靠近终点** → 先慢后快再慢, 类似 ease
3. **P1 在上方, P2 在下方** → 先加速后减速, 类似 ease-in-out
4. **P1 超出范围 (y < 0)** → 曲线回弹, 产生弹跳效果!

"等等, 控制点可以超出 [0, 1] 范围?" 你意识到这意味着动画可以 "超调"——先冲过目标, 再回弹到最终位置。

你修改代码, 测试 `cubic-bezier(0.5, -0.5, 0.5, 1.5)`:

```javascript
// 在实际动画中测试
const box = document.createElement('div');
box.style.cssText = `
    width: 100px;
    height: 100px;
    background: #2196F3;
    transition: transform 1s cubic-bezier(0.5, -0.5, 0.5, 1.5);
`;
document.body.appendChild(box);

setTimeout(() => {
    box.style.transform = 'translateX(300px)';
}, 100);
```

盒子滑动时, 先向左回退了一小段, 然后加速向右, 最后超过目标位置又回弹——就像真实世界中的弹簧运动!

"太神奇了, " 你在笔记中写道, "四个数字就能精确控制动画的整个运动轨迹。"

---

## 数学原理的探索

你决定深入理解贝塞尔曲线背后的数学。

你找到了贝塞尔曲线的数学定义: 三次贝塞尔曲线是由四个控制点 P0, P1, P2, P3 定义的参数曲线, 公式为:

```
B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3
其中 t ∈ [0, 1]
```

"这是什么?" 你盯着公式, "看起来像是插值..."

你尝试手动实现这个公式:

```javascript
// 计算三次贝塞尔曲线上的点
function cubicBezier(t, p0, p1, p2, p3) {
    const t2 = t * t;
    const t3 = t2 * t;
    const mt = 1 - t;
    const mt2 = mt * mt;
    const mt3 = mt2 * mt;

    return {
        x: mt3 * p0.x + 3 * mt2 * t * p1.x + 3 * mt * t2 * p2.x + t3 * p3.x,
        y: mt3 * p0.y + 3 * mt2 * t * p1.y + 3 * mt * t2 * p2.y + t3 * p3.y
    };
}

// 绘制曲线 (手动实现, 不用 Canvas API)
function drawBezierManual() {
    ctx.strokeStyle = '#FF5722';
    ctx.lineWidth = 2;
    ctx.beginPath();

    for (let t = 0; t <= 1; t += 0.01) {
        const point = cubicBezier(t, points.p0, points.p1, points.p2, points.p3);

        if (t === 0) {
            ctx.moveTo(point.x, point.y);
        } else {
            ctx.lineTo(point.x, point.y);
        }
    }

    ctx.stroke();
}
```

你对比 Canvas 原生 API 和手动实现的结果——两条曲线完美重合!

"所以 t 是时间参数, " 你理解了, "从 0 到 1 代表动画的进度。贝塞尔曲线计算出每个时刻对应的位置。"

但你意识到一个问题: CSS 动画的缓动函数是 y = f(x), 而贝塞尔曲线给出的是 (x(t), y(t))。如何从 x 反推 t, 再计算 y?

你查阅资料, 发现这需要求解三次方程:

```
x = (1-t)³ * 0 + 3(1-t)²t * x1 + 3(1-t)t² * x2 + t³ * 1

求解这个方程得到 t, 然后代入:
y = (1-t)³ * 0 + 3(1-t)²t * y1 + 3(1-t)t² * y2 + t³ * 1
```

"这不是简单的代数运算, " 你意识到, "需要数值方法求解。"

你实现了一个简化版的牛顿迭代法:

```javascript
// 求解 x(t) = targetX, 返回对应的 t
function solveBezierX(targetX, x1, x2, epsilon = 0.0001) {
    // 牛顿迭代法
    let t = targetX;  // 初始猜测

    for (let i = 0; i < 10; i++) {
        // 计算当前 t 对应的 x
        const x = cubicBezierX(t, x1, x2);
        const error = x - targetX;

        if (Math.abs(error) < epsilon) {
            return t;
        }

        // 计算导数 dx/dt
        const derivative = cubicBezierXDerivative(t, x1, x2);

        // 牛顿迭代: t_new = t - f(t) / f'(t)
        t -= error / derivative;
    }

    return t;
}

function cubicBezierX(t, x1, x2) {
    const mt = 1 - t;
    return 3 * mt * mt * t * x1 + 3 * mt * t * t * x2 + t * t * t;
}

function cubicBezierXDerivative(t, x1, x2) {
    const mt = 1 - t;
    return 3 * mt * mt * x1 + 6 * mt * t * (x2 - x1) + 3 * t * t * (1 - x2);
}

// 完整的缓动函数
function cubicBezierEasing(x1, y1, x2, y2) {
    return function(progress) {
        // 给定动画进度 progress (0-1), 返回缓动后的值
        if (progress === 0) return 0;
        if (progress === 1) return 1;

        // 1. 从 x (progress) 求解 t
        const t = solveBezierX(progress, x1, x2);

        // 2. 用 t 计算 y
        const mt = 1 - t;
        return 3 * mt * mt * t * y1 + 3 * mt * t * t * y2 + t * t * t;
    };
}

// 测试
const ease = cubicBezierEasing(0.25, 0.1, 0.25, 1.0);  // CSS ease

console.log('progress -> eased value:');
for (let p = 0; p <= 1; p += 0.1) {
    console.log(`${p.toFixed(1)} -> ${ease(p).toFixed(3)}`);
}
```

运行结果:

```
progress -> eased value:
0.0 -> 0.000
0.1 -> 0.026
0.2 -> 0.106
0.3 -> 0.236
0.4 -> 0.406
0.5 -> 0.594
0.6 -> 0.764
0.7 -> 0.894
0.8 -> 0.974
0.9 -> 1.000
1.0 -> 1.000
```

你对比浏览器的 CSS `ease` 曲线——数值几乎完全一致!

"我成功实现了 CSS 缓动函数的核心算法, " 你满意地点头, "现在终于理解它是如何工作的了。"

---

## 预设缓动函数的逆向工程

你想知道 CSS 预设的缓动函数对应的贝塞尔参数是什么。

你打开 Chrome DevTools, 逐个查看:

```css
/* CSS 预设缓动函数 */
linear:        cubic-bezier(0.0, 0.0, 1.0, 1.0)
ease:          cubic-bezier(0.25, 0.1, 0.25, 1.0)
ease-in:       cubic-bezier(0.42, 0.0, 1.0, 1.0)
ease-out:      cubic-bezier(0.0, 0.0, 0.58, 1.0)
ease-in-out:   cubic-bezier(0.42, 0.0, 0.58, 1.0)
```

你在自己的可视化工具中逐个绘制这些曲线, 观察它们的形状:

```javascript
// 预设缓动函数库
const easings = {
    linear: [0, 0, 1, 1],
    ease: [0.25, 0.1, 0.25, 1],
    easeIn: [0.42, 0, 1, 1],
    easeOut: [0, 0, 0.58, 1],
    easeInOut: [0.42, 0, 0.58, 1]
};

// 在 Canvas 上绘制所有曲线对比
function drawAllEasings() {
    const colors = ['#000', '#2196F3', '#4CAF50', '#FF9800', '#F44336'];

    Object.entries(easings).forEach(([name, [x1, y1, x2, y2]], index) => {
        ctx.strokeStyle = colors[index];
        ctx.lineWidth = 2;
        ctx.beginPath();

        for (let t = 0; t <= 1; t += 0.01) {
            const x = cubicBezierX(t, x1, x2) * 400;
            const y = 400 - cubicBezierX(t, y1, y2) * 400;

            if (t === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }

        ctx.stroke();

        // 绘制图例
        ctx.fillStyle = colors[index];
        ctx.fillText(name, 10, 20 + index * 20);
    });
}
```

你观察曲线的形状, 总结它们的特点:

```
linear: 对角线, 匀速
ease: 两端平缓, 中间陡峭 → 慢-快-慢
ease-in: 起点平缓 → 慢速启动
ease-out: 终点平缓 → 慢速停止
ease-in-out: 两端都平缓 → 慢-快-慢 (对称)
```

"原来 `ease` 和 `ease-in-out` 很相似, " 你发现, "但 `ease` 的曲线更陡峭, 加速更明显。"

你开始测试一些流行的缓动函数库提供的曲线, 比如 Robert Penner 的经典缓动方程:

```javascript
// Robert Penner 缓动函数 (转为贝塞尔近似)
const pennerEasings = {
    // 二次方
    easeInQuad: [0.55, 0.085, 0.68, 0.53],
    easeOutQuad: [0.25, 0.46, 0.45, 0.94],
    easeInOutQuad: [0.455, 0.03, 0.515, 0.955],

    // 三次方
    easeInCubic: [0.55, 0.055, 0.675, 0.19],
    easeOutCubic: [0.215, 0.61, 0.355, 1],
    easeInOutCubic: [0.645, 0.045, 0.355, 1],

    // 四次方
    easeInQuart: [0.895, 0.03, 0.685, 0.22],
    easeOutQuart: [0.165, 0.84, 0.44, 1],
    easeInOutQuart: [0.77, 0, 0.175, 1],

    // 五次方
    easeInQuint: [0.755, 0.05, 0.855, 0.06],
    easeOutQuint: [0.23, 1, 0.32, 1],
    easeInOutQuint: [0.86, 0, 0.07, 1],

    // 正弦
    easeInSine: [0.47, 0, 0.745, 0.715],
    easeOutSine: [0.39, 0.575, 0.565, 1],
    easeInOutSine: [0.445, 0.05, 0.55, 0.95],

    // 指数
    easeInExpo: [0.95, 0.05, 0.795, 0.035],
    easeOutExpo: [0.19, 1, 0.22, 1],
    easeInOutExpo: [1, 0, 0, 1],

    // 圆形
    easeInCirc: [0.6, 0.04, 0.98, 0.335],
    easeOutCirc: [0.075, 0.82, 0.165, 1],
    easeInOutCirc: [0.785, 0.135, 0.15, 0.86]
};

// 测试所有缓动函数
Object.entries(pennerEasings).forEach(([name, params]) => {
    const easing = cubicBezierEasing(...params);

    console.log(`${name}:`);
    console.log(`  cubic-bezier(${params.join(', ')})`);
    console.log(`  0.5 -> ${easing(0.5).toFixed(3)}`);
});
```

"这些数字是怎么推导出来的?" 你好奇地想, "肯定有数学公式和曲线拟合过程。"

你尝试自己设计一些有趣的缓动函数:

```javascript
// 自定义缓动函数
const customEasings = {
    // 弹性回弹 (超调)
    bounce: [0.5, -0.5, 0.5, 1.5],

    // 强力加速
    powerIn: [0.9, 0, 1, 0.2],

    // 强力减速
    powerOut: [0, 0.8, 0.1, 1],

    // 极端对比
    snap: [0, 1, 1, 0]
};
```

你在动画中测试这些自定义曲线, 看到各种奇特的效果:
- `bounce`: 元素先回退再加速, 最后超过目标又回弹
- `powerIn`: 缓慢启动后突然爆发
- `powerOut`: 快速启动后突然刹车
- `snap`: 开始时瞬间完成一半, 然后缓慢完成剩余部分

"贝塞尔曲线的表达能力太强了, " 你感慨, "四个参数就能创造出无穷的运动模式。"

---

## JavaScript 动画引擎的实现

你决定实现一个简单但完整的 JavaScript 动画引擎, 使用自己写的贝塞尔缓动函数。

```javascript
// 动画引擎
class Animator {
    constructor() {
        this.animations = [];
        this.rafId = null;
    }

    // 创建动画
    animate({
        element,
        properties,
        duration = 1000,
        easing = [0.25, 0.1, 0.25, 1],  // CSS ease
        onUpdate = null,
        onComplete = null
    }) {
        const startTime = performance.now();
        const easingFn = cubicBezierEasing(...easing);

        // 记录初始值
        const startValues = {};
        Object.keys(properties).forEach(prop => {
            const computed = window.getComputedStyle(element);
            startValues[prop] = parseFloat(computed[prop]) || 0;
        });

        const animation = {
            element,
            properties,
            startValues,
            endValues: properties,
            duration,
            easingFn,
            startTime,
            onUpdate,
            onComplete
        };

        this.animations.push(animation);

        // 启动 RAF 循环
        if (!this.rafId) {
            this.rafId = requestAnimationFrame(this.tick.bind(this));
        }

        return animation;
    }

    // RAF 循环
    tick(currentTime) {
        const completedAnimations = [];

        this.animations.forEach(anim => {
            const elapsed = currentTime - anim.startTime;
            const progress = Math.min(elapsed / anim.duration, 1);

            // 应用缓动函数
            const easedProgress = anim.easingFn(progress);

            // 更新所有属性
            Object.keys(anim.properties).forEach(prop => {
                const start = anim.startValues[prop];
                const end = anim.endValues[prop];
                const current = start + (end - start) * easedProgress;

                // 应用到元素
                if (prop === 'opacity') {
                    anim.element.style.opacity = current;
                } else if (prop === 'transform') {
                    // 简化: 只处理 translateX
                    anim.element.style.transform = `translateX(${current}px)`;
                } else {
                    anim.element.style[prop] = `${current}px`;
                }
            });

            // 调用更新回调
            if (anim.onUpdate) {
                anim.onUpdate(easedProgress, progress);
            }

            // 检查是否完成
            if (progress >= 1) {
                completedAnimations.push(anim);

                if (anim.onComplete) {
                    anim.onComplete();
                }
            }
        });

        // 移除已完成的动画
        this.animations = this.animations.filter(
            anim => !completedAnimations.includes(anim)
        );

        // 继续循环
        if (this.animations.length > 0) {
            this.rafId = requestAnimationFrame(this.tick.bind(this));
        } else {
            this.rafId = null;
        }
    }

    // 停止所有动画
    stopAll() {
        if (this.rafId) {
            cancelAnimationFrame(this.rafId);
            this.rafId = null;
        }
        this.animations = [];
    }
}

// 使用示例
const animator = new Animator();

const box = document.querySelector('.box');

animator.animate({
    element: box,
    properties: {
        transform: 300  // translateX(300px)
    },
    duration: 1000,
    easing: [0.5, -0.5, 0.5, 1.5],  // 弹性回弹
    onUpdate: (easedProgress, rawProgress) => {
        console.log(`Progress: ${(rawProgress * 100).toFixed(1)}% -> ${(easedProgress * 100).toFixed(1)}%`);
    },
    onComplete: () => {
        console.log('动画完成!');
    }
});
```

你测试这个引擎, 看到控制台输出:

```
Progress: 0.0% -> 0.0%
Progress: 10.2% -> -5.3%    ← 负值! 元素回退
Progress: 20.4% -> -8.1%
Progress: 30.6% -> 2.7%     ← 开始前进
Progress: 40.8% -> 24.1%
Progress: 51.0% -> 50.0%
Progress: 61.2% -> 75.9%
Progress: 71.4% -> 97.3%
Progress: 81.6% -> 108.1%   ← 超过 100%! 元素超调
Progress: 91.8% -> 105.3%
Progress: 100.0% -> 100.0%  ← 最终回到 100%
动画完成!
```

"太神奇了!" 你盯着输出, "进度值可以超出 [0, 1] 范围, 这就是回弹和超调效果的来源!"

你继续完善引擎, 添加了多属性动画、动画队列、动画组合等功能:

```javascript
// 复杂动画示例: 序列动画
animator.animate({
    element: box,
    properties: { transform: 100 },
    duration: 500,
    easing: [0.42, 0, 1, 1],  // ease-in
    onComplete: () => {
        // 第一个动画完成后, 启动第二个
        animator.animate({
            element: box,
            properties: { transform: 300 },
            duration: 500,
            easing: [0, 0, 0.58, 1]  // ease-out
        });
    }
});

// 并行动画
animator.animate({
    element: box,
    properties: { transform: 300 },
    duration: 1000,
    easing: [0.25, 0.1, 0.25, 1]
});

animator.animate({
    element: box,
    properties: { opacity: 0 },
    duration: 1000,
    easing: [0.42, 0, 0.58, 1]
});
```

---

## 性能优化与实际应用

晚上 10 点, 你已经研究了快 4 个小时。

你开始思考性能问题: "每帧都要计算贝塞尔曲线, 会不会影响性能?"

你实现了一个基于查找表的优化版本:

```javascript
// 优化版: 预计算查找表
function createEasingLUT(x1, y1, x2, y2, samples = 100) {
    const lut = [];

    for (let i = 0; i <= samples; i++) {
        const progress = i / samples;
        const t = solveBezierX(progress, x1, x2);
        const mt = 1 - t;
        const value = 3 * mt * mt * t * y1 + 3 * mt * t * t * y2 + t * t * t;
        lut.push(value);
    }

    // 返回快速查找函数
    return function(progress) {
        if (progress <= 0) return 0;
        if (progress >= 1) return 1;

        const index = progress * samples;
        const lower = Math.floor(index);
        const upper = Math.ceil(index);

        if (lower === upper) {
            return lut[lower];
        }

        // 线性插值
        const t = index - lower;
        return lut[lower] * (1 - t) + lut[upper] * t;
    };
}

// 性能对比
const easing1 = cubicBezierEasing(0.25, 0.1, 0.25, 1);
const easing2 = createEasingLUT(0.25, 0.1, 0.25, 1);

console.time('实时计算 (1000次)');
for (let i = 0; i < 1000; i++) {
    easing1(Math.random());
}
console.timeEnd('实时计算 (1000次)');

console.time('查找表 (1000次)');
for (let i = 0; i < 1000; i++) {
    easing2(Math.random());
}
console.timeEnd('查找表 (1000次)');
```

测试结果:

```
实时计算 (1000次): 8.2ms
查找表 (1000次): 0.9ms
```

"查找表快了 9 倍!" 你惊讶地发现, "但代价是预计算时间和内存占用。"

你决定在动画引擎中默认使用查找表, 但提供一个选项让用户选择:

```javascript
class Animator {
    constructor(options = {}) {
        this.animations = [];
        this.rafId = null;
        this.useLUT = options.useLUT !== false;  // 默认启用
        this.lutCache = new Map();
    }

    getEasingFn(params) {
        if (!this.useLUT) {
            return cubicBezierEasing(...params);
        }

        // 查找缓存
        const key = params.join(',');
        if (this.lutCache.has(key)) {
            return this.lutCache.get(key);
        }

        // 创建并缓存
        const fn = createEasingLUT(...params);
        this.lutCache.set(key, fn);
        return fn;
    }

    // ... 其他方法
}
```

你还实现了一些实用的工具函数:

```javascript
// 工具函数库
const EasingUtils = {
    // 反转缓动函数
    reverse(easing) {
        return [1 - easing[2], 1 - easing[3], 1 - easing[0], 1 - easing[1]];
    },

    // 组合缓动函数 (先 easeIn, 后 easeOut)
    combine(easeIn, easeOut) {
        return function(progress) {
            if (progress < 0.5) {
                const fn = cubicBezierEasing(...easeIn);
                return fn(progress * 2) / 2;
            } else {
                const fn = cubicBezierEasing(...easeOut);
                return 0.5 + fn((progress - 0.5) * 2) / 2;
            }
        };
    },

    // 将任意函数转为缓动函数
    fromFunction(fn) {
        return function(progress) {
            return fn(progress);
        };
    },

    // 生成弹跳效果
    bounce(bounciness = 2) {
        return [0.5, -bounciness, 0.5, 1 + bounciness];
    },

    // 生成弹性效果
    elastic(elasticity = 0.5) {
        return [0.5, -elasticity, 0.5, 1 + elasticity];
    }
};

// 测试工具函数
const easeInOut = EasingUtils.combine(
    [0.42, 0, 1, 1],  // ease-in
    [0, 0, 0.58, 1]   // ease-out
);

const bounce = EasingUtils.bounce(2.0);
```

你在实际项目中测试了这些工具:

```javascript
// 实际应用: 侧边栏滑入动画
const sidebar = document.querySelector('.sidebar');

animator.animate({
    element: sidebar,
    properties: {
        transform: 0  // 从 -300px 滑到 0
    },
    duration: 400,
    easing: [0, 0, 0.58, 1],  // ease-out
    onComplete: () => {
        console.log('侧边栏已打开');
    }
});

// 通知消息弹出 (带回弹)
const notification = document.querySelector('.notification');

animator.animate({
    element: notification,
    properties: {
        transform: 0,
        opacity: 1
    },
    duration: 600,
    easing: EasingUtils.bounce(1.5)
});

// 加载进度条 (线性增长)
const progressBar = document.querySelector('.progress-bar');

animator.animate({
    element: progressBar,
    properties: {
        width: 100  // 0% → 100%
    },
    duration: 3000,
    easing: [0, 0, 1, 1],  // linear
    onUpdate: (progress) => {
        progressBar.textContent = `${Math.round(progress * 100)}%`;
    }
});
```

---

## 深夜的总结

晚上 11 点半, 你关掉实验项目, 整理今天的收获。

你创建了一个总结文档 `bezier-notes.md`:

```markdown
# 贝塞尔曲线与缓动函数总结

## 核心原理

三次贝塞尔曲线由 4 个控制点定义:
- P0 (0, 0): 起点
- P1 (x1, y1): 控制点 1
- P2 (x2, y2): 控制点 2
- P3 (1, 1): 终点

数学公式:
B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3

## CSS 语法

cubic-bezier(x1, y1, x2, y2)

- 只需指定两个控制点的坐标
- x1, x2 通常在 [0, 1] 范围内
- y1, y2 可以超出 [0, 1], 产生超调效果

## 常用预设

linear:        cubic-bezier(0, 0, 1, 1)
ease:          cubic-bezier(0.25, 0.1, 0.25, 1)
ease-in:       cubic-bezier(0.42, 0, 1, 1)
ease-out:      cubic-bezier(0, 0, 0.58, 1)
ease-in-out:   cubic-bezier(0.42, 0, 0.58, 1)

## 自定义效果

弹性:   cubic-bezier(0.5, -0.5, 0.5, 1.5)
强力:   cubic-bezier(0.9, 0, 1, 0.2)
对比:   cubic-bezier(0, 1, 1, 0)

## 性能优化

1. 预计算查找表 (9x 提速)
2. 缓存缓动函数实例
3. 使用 requestAnimationFrame
4. 避免 layout thrashing
```

你对比了自己实现的动画引擎和浏览器原生 CSS 动画:

```
性能对比 (1000 个元素同时动画):

CSS Transitions:     16ms/frame  (原生优化)
JS + RAF:            24ms/frame  (手动实现)
JS + setInterval:    45ms/frame  (不推荐)

结论: CSS 动画性能更好, 但 JS 动画更灵活
```

你还发现了一些有趣的事实:

```
1. CSS 动画在主线程阻塞时仍能运行 (某些属性)
2. transform 和 opacity 动画可以在 GPU 上执行
3. 贝塞尔曲线无法表示弹跳效果 (需要多段曲线)
4. steps() 函数适合逐帧动画, 不需要贝塞尔
5. spring() 函数 (提案中) 将提供基于物理的动画
```

你看着侧边栏的滑入动画, 现在使用了 `cubic-bezier(0, 0, 0.58, 1)` —— 优雅、流畅、自然。

"从今天开始, 我不仅知道如何使用缓动函数, " 你在笔记中写道, "更重要的是, 我理解了它背后的数学原理和实现机制。"

窗外夜色已深, 但你感觉收获满满。明天你可以将这些知识应用到实际项目中, 创造更流畅的用户体验。

---

## 知识档案: 贝塞尔曲线与缓动函数的八个核心机制

**规则 1: 三次贝塞尔曲线由 4 个控制点定义, CSS 只需指定中间两个**

贝塞尔曲线是参数曲线, 由起点、终点和两个控制点确定形状。

```javascript
// 三次贝塞尔曲线的数学定义
B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3

// CSS 缓动函数固定起点 (0, 0) 和终点 (1, 1)
cubic-bezier(x1, y1, x2, y2)

// 等价于
B(t) = 3(1-t)²t·(x1, y1) + 3(1-t)t²·(x2, y2) + t³·(1, 1)

// 实现
function cubicBezier(t, p0, p1, p2, p3) {
    const t2 = t * t;
    const t3 = t2 * t;
    const mt = 1 - t;
    const mt2 = mt * mt;
    const mt3 = mt2 * mt;

    return {
        x: mt3 * p0.x + 3 * mt2 * t * p1.x + 3 * mt * t2 * p2.x + t3 * p3.x,
        y: mt3 * p0.y + 3 * mt2 * t * p1.y + 3 * mt * t2 * p2.y + t3 * p3.y
    };
}
```

控制点位置决定曲线形状:
- **P1 靠近起点**: 慢速启动 (ease-in)
- **P2 靠近终点**: 慢速停止 (ease-out)
- **两个控制点都靠近对角线**: 接近线性 (linear)
- **控制点远离对角线**: 加速/减速更明显

---

**规则 2: CSS 预设缓动函数是常用贝塞尔曲线的快捷方式**

浏览器内置了 5 个预设缓动函数, 对应特定的贝塞尔参数。

```javascript
// CSS 预设缓动函数及其参数
const presets = {
    'linear':      [0.0, 0.0, 1.0, 1.0],   // 匀速
    'ease':        [0.25, 0.1, 0.25, 1.0], // 慢-快-慢 (默认)
    'ease-in':     [0.42, 0.0, 1.0, 1.0],  // 慢速启动
    'ease-out':    [0.0, 0.0, 0.58, 1.0],  // 慢速停止
    'ease-in-out': [0.42, 0.0, 0.58, 1.0]  // 慢-快-慢 (对称)
};

// 使用预设
.element {
    transition: transform 0.3s ease-out;
}

// 等价于
.element {
    transition: transform 0.3s cubic-bezier(0, 0, 0.58, 1);
}
```

预设函数的特点:
- **linear**: 对角线, 匀速运动, 机械感
- **ease**: 两端缓和, 最常用, 默认值
- **ease-in**: 加速启动, 适合消失动画
- **ease-out**: 减速停止, 适合出现动画
- **ease-in-out**: 对称曲线, 适合来回运动

选择建议:
- **出现动画**: ease-out (快速出现, 缓慢停止)
- **消失动画**: ease-in (缓慢启动, 快速消失)
- **位置变化**: ease 或 ease-in-out (自然过渡)
- **循环动画**: ease-in-out (对称, 适合反复)

---

**规则 3: 控制点 y 坐标可以超出 [0, 1] 范围, 产生超调效果**

y 坐标超出范围会让动画值超过目标, 产生回弹或超调效果。

```javascript
// 超调效果: y 值超出 [0, 1]
cubic-bezier(0.5, -0.5, 0.5, 1.5)

// y1 = -0.5: 动画开始时回退 (负值)
// y2 = 1.5:  动画结束前超调 (大于 1)

// 实际效果
const bounce = cubicBezierEasing(0.5, -0.5, 0.5, 1.5);

console.log(bounce(0.1));  // -0.053  ← 负值! 回退
console.log(bounce(0.5));  // 0.500   ← 中点
console.log(bounce(0.9));  // 1.053   ← 超过 1! 超调

// 应用到 transform
.element {
    transition: transform 0.6s cubic-bezier(0.5, -0.5, 0.5, 1.5);
}

/*
当元素从 0 移动到 100px:
- 开始时先向后移动到 -5px
- 然后加速向前
- 最后超过目标到 105px, 再回弹到 100px
*/
```

超调效果的应用场景:
- **弹性按钮**: 点击后略微回弹
- **通知消息**: 弹出时带弹性效果
- **模态框**: 出现时轻微弹跳
- **加载完成**: 进度条冲过 100% 再回落

注意事项:
- 超调幅度不宜过大 (y 值建议在 [-0.5, 1.5] 范围)
- 不适合需要精确停止的动画 (如滚动定位)
- 会增加动画时长感知

---

**规则 4: 从 x 反求 t 需要数值方法, 查找表可优化性能**

CSS 缓动函数是 y = f(x), 但贝塞尔曲线给出的是 (x(t), y(t)), 需要反求。

```javascript
// 问题: 给定动画进度 x, 求缓动后的值 y
// 步骤 1: 从 x 反求参数 t
// 步骤 2: 用 t 计算 y

// x(t) 是三次方程, 没有简单的代数解
// 需要数值方法: 牛顿迭代法

function solveBezierX(targetX, x1, x2, epsilon = 0.0001) {
    let t = targetX;  // 初始猜测

    for (let i = 0; i < 10; i++) {
        // 计算当前 t 对应的 x
        const x = cubicBezierX(t, x1, x2);
        const error = x - targetX;

        if (Math.abs(error) < epsilon) {
            return t;  // 收敛
        }

        // 牛顿迭代: t_new = t - f(t) / f'(t)
        const derivative = cubicBezierXDerivative(t, x1, x2);
        t -= error / derivative;
    }

    return t;
}

function cubicBezierX(t, x1, x2) {
    const mt = 1 - t;
    return 3 * mt * mt * t * x1 + 3 * mt * t * t * x2 + t * t * t;
}

function cubicBezierXDerivative(t, x1, x2) {
    const mt = 1 - t;
    return 3 * mt * mt * x1 + 6 * mt * t * (x2 - x1) + 3 * t * t * (1 - x2);
}

// 完整缓动函数
function cubicBezierEasing(x1, y1, x2, y2) {
    return function(progress) {
        if (progress === 0) return 0;
        if (progress === 1) return 1;

        const t = solveBezierX(progress, x1, x2);
        const mt = 1 - t;
        return 3 * mt * mt * t * y1 + 3 * mt * t * t * y2 + t * t * t;
    };
}
```

性能优化: 预计算查找表

```javascript
// 查找表优化 (9x 提速)
function createEasingLUT(x1, y1, x2, y2, samples = 100) {
    const lut = [];

    for (let i = 0; i <= samples; i++) {
        const progress = i / samples;
        const t = solveBezierX(progress, x1, x2);
        const mt = 1 - t;
        const value = 3 * mt * mt * t * y1 + 3 * mt * t * t * y2 + t * t * t;
        lut.push(value);
    }

    return function(progress) {
        if (progress <= 0) return 0;
        if (progress >= 1) return 1;

        const index = progress * samples;
        const lower = Math.floor(index);
        const upper = Math.ceil(index);

        if (lower === upper) return lut[lower];

        // 线性插值
        const t = index - lower;
        return lut[lower] * (1 - t) + lut[upper] * t;
    };
}

// 性能对比
实时计算: 8.2ms / 1000次调用
查找表:   0.9ms / 1000次调用
提速:     9.1x
```

---

**规则 5: JavaScript 动画需要 requestAnimationFrame 和缓动函数结合**

使用 RAF 驱动动画循环, 在每帧应用缓动函数计算当前值。

```javascript
// JavaScript 动画引擎基础结构
function animate({
    element,
    property,
    from,
    to,
    duration,
    easing = [0.25, 0.1, 0.25, 1]
}) {
    const startTime = performance.now();
    const easingFn = cubicBezierEasing(...easing);

    function tick(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // 应用缓动函数
        const easedProgress = easingFn(progress);

        // 计算当前值
        const current = from + (to - from) * easedProgress;

        // 更新元素
        element.style[property] = `${current}px`;

        // 继续或完成
        if (progress < 1) {
            requestAnimationFrame(tick);
        }
    }

    requestAnimationFrame(tick);
}

// 使用
const box = document.querySelector('.box');
animate({
    element: box,
    property: 'transform',
    from: 0,
    to: 300,
    duration: 1000,
    easing: [0.5, -0.5, 0.5, 1.5]  // 弹性效果
});
```

RAF 动画的最佳实践:
- **使用 performance.now()**: 高精度时间戳, 不受系统时间影响
- **检查进度上限**: `Math.min(progress, 1)` 避免超过 100%
- **分离逻辑和渲染**: 缓动计算 → 值计算 → DOM 更新
- **批量更新**: 多个动画在同一帧中更新 DOM

性能优化:
- **缓存 DOM 引用**: 避免重复查询
- **优先使用 transform/opacity**: GPU 加速
- **避免 layout thrashing**: 读写分离
- **使用查找表**: 复杂缓动函数预计算

---

**规则 6: CSS 动画性能优于 JavaScript, 但 JavaScript 更灵活**

CSS 动画在某些情况下性能更好, 但 JavaScript 提供更多控制。

```javascript
// 性能对比 (1000 个元素同时动画)

/* CSS Transitions */
.box {
    transition: transform 1s cubic-bezier(0.25, 0.1, 0.25, 1);
}
.box.animate {
    transform: translateX(300px);
}
// 性能: 16ms/frame (60 FPS)
// GPU 加速: ✅
// 主线程阻塞影响: ✅ 部分属性不受影响

/* JavaScript + RAF */
boxes.forEach(box => {
    animate({
        element: box,
        property: 'transform',
        to: 300,
        duration: 1000
    });
});
// 性能: 24ms/frame (41 FPS)
// GPU 加速: ✅ (使用 transform)
// 主线程阻塞影响: ❌ 完全受影响

/* JavaScript + setInterval */
boxes.forEach(box => {
    let progress = 0;
    const interval = setInterval(() => {
        progress += 0.01;
        box.style.transform = `translateX(${progress * 300}px)`;
        if (progress >= 1) clearInterval(interval);
    }, 16);
});
// 性能: 45ms/frame (22 FPS)
// GPU 加速: ✅
// 精度: ❌ 时间不准确
```

CSS vs JavaScript 选择指南:

**选择 CSS 的场景**:
- 简单的状态切换 (hover, active, class toggle)
- 固定的动画轨迹 (不需要动态调整)
- 性能敏感的场景 (移动端, 低端设备)
- 页面加载/卸载动画

**选择 JavaScript 的场景**:
- 需要动态计算目标值
- 需要中途修改动画
- 需要复杂的动画编排 (序列, 并行, 同步)
- 需要精确控制进度
- 需要回调和事件通知

混合方案:
```javascript
// CSS 负责简单动画
.fade-in {
    animation: fadeIn 0.3s ease-out;
}

// JavaScript 负责复杂动画
animator.animate({
    element: modal,
    properties: {
        scale: 1,
        opacity: 1
    },
    duration: 400,
    easing: [0.5, -0.5, 0.5, 1.5]
});
```

---

**规则 7: 常用缓动函数库提供了丰富的预设曲线**

专业动画库提供了经过优化的贝塞尔参数和额外的缓动函数。

```javascript
// Robert Penner 经典缓动方程 (贝塞尔近似)
const easings = {
    // 二次方 (Quadratic)
    easeInQuad:     [0.55, 0.085, 0.68, 0.53],
    easeOutQuad:    [0.25, 0.46, 0.45, 0.94],
    easeInOutQuad:  [0.455, 0.03, 0.515, 0.955],

    // 三次方 (Cubic)
    easeInCubic:    [0.55, 0.055, 0.675, 0.19],
    easeOutCubic:   [0.215, 0.61, 0.355, 1],
    easeInOutCubic: [0.645, 0.045, 0.355, 1],

    // 四次方 (Quartic)
    easeInQuart:    [0.895, 0.03, 0.685, 0.22],
    easeOutQuart:   [0.165, 0.84, 0.44, 1],
    easeInOutQuart: [0.77, 0, 0.175, 1],

    // 五次方 (Quintic)
    easeInQuint:    [0.755, 0.05, 0.855, 0.06],
    easeOutQuint:   [0.23, 1, 0.32, 1],
    easeInOutQuint: [0.86, 0, 0.07, 1],

    // 正弦 (Sine)
    easeInSine:     [0.47, 0, 0.745, 0.715],
    easeOutSine:    [0.39, 0.575, 0.565, 1],
    easeInOutSine:  [0.445, 0.05, 0.55, 0.95],

    // 指数 (Exponential)
    easeInExpo:     [0.95, 0.05, 0.795, 0.035],
    easeOutExpo:    [0.19, 1, 0.22, 1],
    easeInOutExpo:  [1, 0, 0, 1],

    // 圆形 (Circular)
    easeInCirc:     [0.6, 0.04, 0.98, 0.335],
    easeOutCirc:    [0.075, 0.82, 0.165, 1],
    easeInOutCirc:  [0.785, 0.135, 0.15, 0.86]
};

// Material Design 缓动曲线
const materialEasings = {
    standard:              [0.4, 0.0, 0.2, 1],    // 标准
    deceleration:          [0.0, 0.0, 0.2, 1],    // 减速
    acceleration:          [0.4, 0.0, 1, 1],      // 加速
    sharp:                 [0.4, 0.0, 0.6, 1]     // 锐利
};

// iOS 缓动曲线
const iosEasings = {
    default:               [0.25, 0.1, 0.25, 1],
    keyboard:              [0.36, 0.66, 0.04, 1]
};

// 自定义效果
const customEasings = {
    bounce:                [0.5, -0.5, 0.5, 1.5],   // 弹性
    anticipate:            [0.3, -0.3, 0.7, 1.3],   // 预期
    overshoot:             [0.5, 0, 0.5, 1.3],      // 超调
    strongEaseIn:          [0.9, 0, 1, 0.2],        // 强力启动
    strongEaseOut:         [0, 0.8, 0.1, 1]         // 强力停止
};
```

使用建议:
- **easeOutQuad/Cubic**: 最常用, 适合大部分场景
- **easeInOutQuad/Cubic**: 对称动画, 适合来回运动
- **easeInExpo**: 强力启动, 适合爆炸/发射效果
- **easeOutExpo**: 强力停止, 适合急刹车效果
- **Material Design 曲线**: Android 应用
- **iOS 曲线**: iOS 应用
- **bounce/anticipate**: 特殊效果, 谨慎使用

---

**规则 8: 贝塞尔曲线有局限性, 复杂动画需要其他方法**

贝塞尔曲线无法表示某些运动模式, 需要其他技术。

```javascript
// 贝塞尔曲线的局限

// 1. 无法表示真正的弹跳 (多次回弹)
// 贝塞尔曲线是单调或有一个拐点, 无法多次振荡

// 解决方案: 多段贝塞尔曲线
function bounceEasing(progress) {
    if (progress < 0.25) {
        return cubicBezierEasing(0, 0, 0.58, 1)(progress * 4);
    } else if (progress < 0.5) {
        return 1 - cubicBezierEasing(0.42, 0, 1, 1)((progress - 0.25) * 4) * 0.3;
    } else if (progress < 0.75) {
        return 1 - cubicBezierEasing(0.42, 0, 1, 1)((progress - 0.5) * 4) * 0.1;
    } else {
        return 1 - cubicBezierEasing(0.42, 0, 1, 1)((progress - 0.75) * 4) * 0.03;
    }
}

// 2. 无法表示基于物理的弹簧运动
// 弹簧运动由质量、刚度、阻尼决定, 不是简单的曲线

// 解决方案: 物理模拟
function springEasing(mass = 1, stiffness = 100, damping = 10) {
    return function(progress) {
        const t = progress;
        const w0 = Math.sqrt(stiffness / mass);
        const zeta = damping / (2 * Math.sqrt(stiffness * mass));

        if (zeta < 1) {
            // 欠阻尼: 振荡
            const wd = w0 * Math.sqrt(1 - zeta * zeta);
            const A = 1;
            const B = (zeta * w0) / wd;
            return 1 - Math.exp(-zeta * w0 * t) * (A * Math.cos(wd * t) + B * Math.sin(wd * t));
        } else if (zeta === 1) {
            // 临界阻尼
            return 1 - (1 + w0 * t) * Math.exp(-w0 * t);
        } else {
            // 过阻尼
            const r1 = -w0 * (zeta - Math.sqrt(zeta * zeta - 1));
            const r2 = -w0 * (zeta + Math.sqrt(zeta * zeta - 1));
            const A = 1;
            const B = -1 / (r2 - r1);
            return 1 - (A * Math.exp(r1 * t) + B * Math.exp(r2 * t));
        }
    };
}

// 3. 逐帧动画 (sprite animation)
// 不需要缓动, 需要离散的帧切换

// 解决方案: steps() 函数
.sprite {
    animation: sprite 1s steps(10) infinite;
}

@keyframes sprite {
    from { background-position: 0 0; }
    to { background-position: -1000px 0; }
}

// JavaScript 实现
function stepsEasing(steps) {
    return function(progress) {
        return Math.floor(progress * steps) / steps;
    };
}

// 4. 路径动画 (沿 SVG path 运动)
// 需要 SVG path 的长度计算和切线方向

// 解决方案: offset-path (CSS) 或 PathFollower (JS)
.element {
    offset-path: path('M 0 0 Q 50 100 100 0');
    offset-distance: 0%;
    animation: followPath 2s cubic-bezier(0.25, 0.1, 0.25, 1);
}

@keyframes followPath {
    to { offset-distance: 100%; }
}
```

替代技术:
- **steps()**: 逐帧动画, 帧切换
- **spring()**: 基于物理的弹簧 (CSS 提案)
- **多段贝塞尔**: 复杂曲线拼接
- **Web Animations API**: 编程式关键帧动画
- **FLIP 技术**: 布局动画优化
- **SVG path**: 路径动画

选择建议:
- **90% 场景**: 贝塞尔曲线足够
- **弹簧/弹性**: 使用物理模拟库 (react-spring, popmotion)
- **复杂编排**: 使用动画库 (GSAP, Anime.js)
- **高性能**: 优先使用 CSS, 必要时用 JS

---

**事故档案编号**: NETWORK-2024-1959
**影响范围**: 贝塞尔曲线、CSS 缓动函数、动画性能、JavaScript 动画引擎
**根本原因**: 缺乏对缓动函数背后数学原理的理解, 导致动画生硬、性能低下、无法实现复杂效果
**学习成本**: 中高 (需理解三次贝塞尔曲线数学定义、数值求解方法、动画性能优化)

这是 JavaScript 世界第 159 次被记录的网络与数据事故。三次贝塞尔曲线由 4 个控制点定义, CSS 缓动函数固定起点和终点, 只需指定中间两个控制点坐标。CSS 预设缓动函数 (ease, ease-in, ease-out 等) 是常用贝塞尔参数的快捷方式。控制点 y 坐标可以超出 [0, 1] 范围, 产生回弹和超调效果。从 x 反求参数 t 需要数值方法 (牛顿迭代), 查找表可实现 9 倍性能提升。JavaScript 动画需要 requestAnimationFrame 驱动循环, 在每帧应用缓动函数计算当前值。CSS 动画在简单场景下性能更好, 但 JavaScript 提供更多控制和灵活性。专业动画库提供了丰富的预设曲线, 覆盖常见动画需求。贝塞尔曲线有局限性, 真正的弹跳、物理弹簧、路径动画需要其他技术。理解贝塞尔曲线的数学原理和实现机制是创造流畅、自然动画效果的基础。

---

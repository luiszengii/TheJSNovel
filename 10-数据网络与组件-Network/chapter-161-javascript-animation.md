《第 161 次记录: 周四的代码审查 —— requestAnimationFrame 动画引擎的性能之争》

---

## PR 评审现场

周四下午 2 点, 会议室的投影屏幕上显示着你的 Pull Request。

"#847 - 实现平滑滚动动画效果" - 你三天前提交的 PR, 今天终于排到了代码审查。你本以为这是个简单的功能增强, 甚至已经在开发环境测试通过, 准备合并了。

但昨天下午, 资深前端老张在 PR 下留了一条评论:

```
@yourname 这个实现有性能问题。你在每一帧都在计算复杂的缓动函数,
而且没有做节流处理。我建议用 CSS transition 代替。
```

你当时回复说: "CSS transition 无法实现这种动态目标的滚动效果, 必须用 JavaScript 控制。而且我用的是 requestAnimationFrame, 性能应该没问题。"

老张没有继续争论, 而是直接约了今天的代码审查会议。现在会议室里坐着你、老张、技术主管老李, 还有前端组的小陈和小王。

老张打开你的代码, 投影在屏幕上:

```javascript
// smooth-scroll.js - 你的实现
function smoothScrollTo(targetY, duration = 1000) {
    const startY = window.scrollY;
    const distance = targetY - startY;
    const startTime = performance.now();

    function scroll() {
        const currentTime = performance.now();
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // ❓ 老张质疑的地方: 复杂的缓动计算
        const easing = easeInOutCubic(progress);
        const currentY = startY + distance * easing;

        window.scrollTo(0, currentY);

        if (progress < 1) {
            requestAnimationFrame(scroll);
        }
    }

    requestAnimationFrame(scroll);
}

function easeInOutCubic(t) {
    return t < 0.5
        ? 4 * t * t * t
        : 1 - Math.pow(-2 * t + 2, 3) / 2;
}
```

"看起来很标准的 RAF 动画实现, " 老张说, "但问题在这里。"

他打开 Chrome DevTools, 录制了一段 Performance 分析。你看到火焰图中, JavaScript 执行占用了大量时间, 而且在滚动过程中有明显的帧率波动。

"在我的测试机上, " 老张指着屏幕, "FPS 从 60 掉到了 45, 尤其是在低端设备上。"

你皱起眉头: "但 requestAnimationFrame 不是应该自动匹配屏幕刷新率吗? 为什么会掉帧?"

老李插话: "RAF 只是保证在合适的时机调用你的回调, 但如果回调本身执行时间过长, 一帧的时间预算超了, 照样会掉帧。"

小陈举手: "那 CSS transition 不是更好吗? 浏览器会自动优化。"

你摇头: "问题是我们的滚动目标是动态的。用户点击导航时, 目标位置是实时计算的, 取决于内容高度和当前滚动位置。CSS 无法处理这种情况。"

老张点头: "这是个好观点。所以问题不是该不该用 JavaScript 动画, 而是**如何正确使用 RAF**。"

他切换到另一个标签页: "我重写了你的代码, 性能提升了 40%。"

---

## 性能对比与优化

老张的代码显示在屏幕上:

```javascript
// smooth-scroll-optimized.js - 老张的优化版本
class SmoothScroller {
    constructor() {
        this.rafId = null;
        this.isScrolling = false;
    }

    scrollTo(targetY, duration = 1000) {
        // ✅ 优化 1: 取消之前的动画
        if (this.rafId) {
            cancelAnimationFrame(this.rafId);
        }

        const startY = window.scrollY;
        const distance = targetY - startY;
        const startTime = performance.now();

        // ✅ 优化 2: 预计算常量
        const halfDuration = duration / 2;

        const scroll = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // ✅ 优化 3: 简化缓动函数
            let easing;
            if (progress < 0.5) {
                const t = progress * 2;
                easing = 2 * t * t;
            } else {
                const t = (progress - 0.5) * 2;
                easing = 0.5 + 2 * t * (1 - t * 0.5);
            }

            const currentY = startY + distance * easing;

            // ✅ 优化 4: 批量操作
            window.scrollTo(0, currentY);

            if (progress < 1) {
                this.rafId = requestAnimationFrame(scroll);
            } else {
                this.rafId = null;
                this.isScrolling = false;
            }
        };

        this.isScrolling = true;
        this.rafId = requestAnimationFrame(scroll);
    }

    cancel() {
        if (this.rafId) {
            cancelAnimationFrame(this.rafId);
            this.rafId = null;
            this.isScrolling = false;
        }
    }
}
```

"有什么区别?" 小王问。

老张开始讲解:

"**第一点, 取消旧动画。** 你的代码没有处理用户快速点击导航的情况。如果用户连续点击, 会创建多个并发的 RAF 循环, 互相干扰。"

他演示了一下你的代码: 快速点击三次导航按钮, 页面滚动变得抖动和混乱。

"看到了吗?" 老张说, "三个动画同时运行, 都在试图控制滚动位置。这不仅性能差, 而且用户体验很糟糕。"

你点头: "确实, 我没考虑到这一点。"

"**第二点, 预计算常量。**" 老张继续, "你在每一帧都计算 `elapsed / duration`, 但 `duration` 是常量。虽然这个计算很快, 但在 60fps 的循环中, 每个毫秒都很宝贵。"

"**第三点, 简化缓动函数。**" 老张指着屏幕, "你的 `easeInOutCubic` 调用了 `Math.pow`, 这是个相对昂贵的操作。我重写了它, 用简单的乘法代替。"

小陈皱眉: "但效果会不会不一样?"

老张播放了两个动画的对比视频: 肉眼几乎看不出差别。

"数学上略有不同, 但视觉效果几乎相同, " 老张解释, "这就是工程权衡 —— 牺牲一点点数学精确性, 换取显著的性能提升。"

"**第四点, 状态管理。**" 老张指着 `isScrolling` 标志, "我加了状态追踪, 这样其他代码可以知道当前是否有动画在运行, 避免冲突。"

老李问了一个关键问题: "性能提升有多少?"

老张打开 Performance 面板, 并排显示两个火焰图:

```
你的实现:
- 平均帧时间: 18.5ms
- 帧率: 45-54 fps
- JavaScript 执行时间: 8.2ms/帧
- 掉帧次数: 23 次 (1 秒内)

老张的优化:
- 平均帧时间: 14.2ms
- 帧率: 58-60 fps
- JavaScript 执行时间: 4.1ms/帧
- 掉帧次数: 2 次 (1 秒内)
```

你看着数据, 不得不承认: "确实快了很多。"

但你想到了另一个问题: "那如果我需要更复杂的缓动函数呢? 比如弹性效果或者回弹?"

老张笑了: "好问题。这就要说到 RAF 动画的第二个层次了。"

---

## 深入 requestAnimationFrame 机制

老张在白板上画了一个时间轴图:

```
浏览器的一帧 (16.67ms @ 60fps):
┌──────────────────────────────────────────────┐
│ JavaScript 执行 → 样式计算 → 布局 → 绘制 → 合成 │
└──────────────────────────────────────────────┘
    ↑ RAF 回调在这里执行
```

"requestAnimationFrame 的回调会在浏览器绘制下一帧之前执行, " 老张解释, "这给了我们一个黄金时机: 在渲染之前更新所有动画状态。"

"但关键是, " 他强调, "**你的回调必须足够快**, 否则就会超出一帧的时间预算。"

小陈问: "什么是时间预算?"

老李回答: "60fps 意味着每帧有 16.67 毫秒。但浏览器不会把所有时间都给你的 JavaScript —— 它还要做样式计算、布局、绘制等。通常你的 JavaScript 执行应该控制在 **10 毫秒以内**。"

"所以, " 老张继续, "如果你需要复杂的缓动函数, 有两个策略。"

他写下第一个策略:

```javascript
// 策略 1: 预计算缓动函数 (查找表)
class EasingLUT {
    constructor(easingFunction, samples = 100) {
        this.lut = [];
        for (let i = 0; i <= samples; i++) {
            const t = i / samples;
            this.lut.push(easingFunction(t));
        }
    }

    getValue(progress) {
        const index = progress * (this.lut.length - 1);
        const lower = Math.floor(index);
        const upper = Math.ceil(index);

        if (lower === upper) {
            return this.lut[lower];
        }

        // 线性插值
        const t = index - lower;
        return this.lut[lower] * (1 - t) + this.lut[upper] * t;
    }
}

// 使用
function expensiveEasing(t) {
    // 复杂的数学计算
    return Math.sin(t * Math.PI / 2) * (1 - Math.exp(-5 * t));
}

const easingTable = new EasingLUT(expensiveEasing, 100);

function scroll(currentTime) {
    // ...
    const easing = easingTable.getValue(progress);  // ✅ O(1) 查找
    // ...
}
```

"预计算把复杂的数学运算移到初始化阶段, " 老张说, "运行时只需要做简单的查表和插值。"

"**策略 2: Web Worker。**"

```javascript
// animation-worker.js - 在 Worker 中计算
self.onmessage = function(e) {
    const { progress, type } = e.data;

    let easing;
    if (type === 'bounce') {
        // 复杂的弹跳计算
        const n1 = 7.5625;
        const d1 = 2.75;
        if (progress < 1 / d1) {
            easing = n1 * progress * progress;
        } else if (progress < 2 / d1) {
            const t = progress - 1.5 / d1;
            easing = n1 * t * t + 0.75;
        } else if (progress < 2.5 / d1) {
            const t = progress - 2.25 / d1;
            easing = n1 * t * t + 0.9375;
        } else {
            const t = progress - 2.625 / d1;
            easing = n1 * t * t + 0.984375;
        }
    }

    self.postMessage({ easing });
};

// 主线程
const worker = new Worker('animation-worker.js');

function scroll(currentTime) {
    const progress = (currentTime - startTime) / duration;

    worker.postMessage({ progress, type: 'bounce' });

    worker.onmessage = (e) => {
        const { easing } = e.data;
        const currentY = startY + distance * easing;
        window.scrollTo(0, currentY);
    };

    // ...
}
```

"但是, " 你指出一个问题, "Worker 通信是异步的, 会不会导致延迟?"

老张点头: "是的, 所以 Worker 方案不适合简单动画。它适合的场景是: **有大量并发动画**, 比如粒子系统、游戏场景, 计算密集到主线程扛不住的时候。"

小王举手: "那什么时候该用 JavaScript 动画, 什么时候该用 CSS?"

这个问题让会议室安静了几秒。老李开口:

"这是个好问题。我们来总结一下。"

---

## 最佳实践与决策指南

老李在白板上画了一个决策树:

```
动画实现决策树:

是否需要动态计算目标值?
├─ 是 → 必须用 JavaScript
│   ├─ 简单缓动 → RAF + 优化的缓动函数
│   ├─ 复杂缓动 → RAF + 预计算查找表
│   └─ 大量并发 → RAF + Web Worker
│
└─ 否 → 优先考虑 CSS
    ├─ 简单状态切换 → CSS transition
    ├─ 关键帧动画 → CSS @keyframes
    ├─ 复杂交互 → JavaScript 控制 CSS 类
    └─ 极致性能 → CSS + will-change
```

"CSS 动画的优势, " 老李总结, "是浏览器可以优化到合成线程, 甚至在主线程阻塞时仍然流畅。但代价是灵活性 —— 你无法动态调整目标值。"

"JavaScript 动画的优势是完全控制, " 他继续, "你可以根据用户输入、滚动位置、甚至陀螺仪数据实时调整动画。但代价是性能 —— 必须小心优化。"

老张补充: "还有一个混合方案: **JavaScript 控制逻辑, CSS 执行动画。**"

他展示了一个例子:

```javascript
// 混合方案: 动态设置 CSS 变量
function smoothScrollWithCSS(targetY, duration = 1000) {
    const startY = window.scrollY;
    const distance = targetY - startY;

    // ✅ JavaScript 计算目标, CSS 执行动画
    document.documentElement.style.setProperty('--scroll-start', startY);
    document.documentElement.style.setProperty('--scroll-end', targetY);
    document.documentElement.style.setProperty('--scroll-duration', `${duration}ms`);

    document.documentElement.classList.add('scrolling');

    setTimeout(() => {
        document.documentElement.classList.remove('scrolling');
        window.scrollTo(0, targetY);
    }, duration);
}
```

```css
/* CSS 定义动画 */
@keyframes scroll-smooth {
    from {
        transform: translateY(calc(var(--scroll-start) * -1px));
    }
    to {
        transform: translateY(calc(var(--scroll-end) * -1px));
    }
}

.scrolling {
    animation: scroll-smooth var(--scroll-duration) cubic-bezier(0.4, 0, 0.2, 1);
}
```

"这样既有动态计算的灵活性, 又有 CSS 动画的性能优势, " 老张说。

你若有所思: "但这种方案有限制吧? 不是所有动画都能这样做。"

老张点头: "确实。这个方案的前提是: **目标值在动画开始前就确定了**。如果目标值在动画过程中还会变化, 比如跟随鼠标的动画, 就只能用纯 JavaScript。"

会议室又陷入了讨论。小陈提出了几个实际场景:

"**场景 1: 跟随鼠标的悬浮提示。**" 小陈说, "目标位置每一帧都在变, 必须用 JavaScript。"

老张: "对。而且这种情况下, 你应该考虑用 `transform` 而不是 `top/left`, 因为 `transform` 不会触发重排。"

"**场景 2: 视差滚动效果。**" 小王补充, "背景图随滚动移动, 但速度不同。"

老李: "这个可以用 CSS 的 `background-attachment: fixed` 或者 CSS 自定义属性 + `scroll()` 函数。但如果需要复杂的数学曲线, 还是 JavaScript + RAF。"

"**场景 3: 物理模拟, 比如弹簧效果。**" 你说出自己之前想实现的需求。

老张: "这就必须用 JavaScript 了。因为弹簧的运动方程是微分方程, 需要逐帧计算速度和加速度。"

他写下弹簧动画的例子:

```javascript
// 弹簧动画 (基于物理模拟)
class SpringAnimator {
    constructor(target, stiffness = 200, damping = 20) {
        this.target = target;
        this.current = 0;
        this.velocity = 0;
        this.stiffness = stiffness;
        this.damping = damping;
        this.rafId = null;
    }

    setTarget(newTarget) {
        this.target = newTarget;

        if (!this.rafId) {
            this.rafId = requestAnimationFrame(this.update.bind(this));
        }
    }

    update(currentTime) {
        if (!this.lastTime) {
            this.lastTime = currentTime;
        }

        const dt = (currentTime - this.lastTime) / 1000;  // 转为秒
        this.lastTime = currentTime;

        // 弹簧物理方程: F = -k * x - c * v
        const force = -this.stiffness * (this.current - this.target) - this.damping * this.velocity;
        this.velocity += force * dt;
        this.current += this.velocity * dt;

        // 应用到 DOM
        window.scrollTo(0, this.current);

        // 检查是否静止
        const isAtRest = Math.abs(this.velocity) < 0.1 && Math.abs(this.current - this.target) < 0.1;

        if (isAtRest) {
            this.current = this.target;
            this.velocity = 0;
            window.scrollTo(0, this.target);
            cancelAnimationFrame(this.rafId);
            this.rafId = null;
            this.lastTime = null;
        } else {
            this.rafId = requestAnimationFrame(this.update.bind(this));
        }
    }
}
```

"看到了吗?" 老张说, "弹簧动画的每一帧都依赖前一帧的状态。这种情况下, CSS 无能为力, 必须用 JavaScript。"

"而且, " 他强调, "这个实现每一帧只做了简单的数学运算 —— 加减乘除, 没有复杂函数。这是性能优化的关键: **保持每帧的计算量在 10 毫秒以内**。"

你终于理解了: "所以问题不是 JavaScript 动画天生性能差, 而是要**根据场景选择合适的技术**, 并且**仔细优化关键路径**。"

老李点头: "正解。"

会议结束时, 你决定采纳老张的优化建议, 重构你的 PR。老张也提议将今天讨论的内容整理成团队的动画开发指南。

晚上, 你重新提交了 PR, 附上了性能对比数据和优化说明。第二天, PR 顺利通过了审查并合并。

但更重要的是, 你深刻理解了 requestAnimationFrame 的工作机制, 以及如何在实际项目中权衡 CSS 和 JavaScript 动画的选择。

---

## 知识档案: requestAnimationFrame 动画控制的八个核心机制

**规则 1: requestAnimationFrame 在浏览器绘制之前执行, 每帧调用一次**

RAF 的回调会在浏览器准备绘制下一帧之前执行, 这是更新动画状态的最佳时机。

```javascript
// RAF 的基本使用
function animate(currentTime) {
    // currentTime 是 DOMHighResTimeStamp, 表示当前时间
    // 单位: 毫秒, 精度: 微秒

    // 更新动画状态
    updateAnimation(currentTime);

    // 继续动画
    requestAnimationFrame(animate);
}

requestAnimationFrame(animate);

// 浏览器的渲染流程
// 1. RAF 回调执行 ← 更新 DOM 和样式
// 2. 样式计算 ← 计算元素的最终样式
// 3. 布局 (Layout) ← 计算元素的位置和大小
// 4. 绘制 (Paint) ← 绘制像素到图层
// 5. 合成 (Composite) ← 将图层合并到屏幕

// RAF 回调的特点
// - 自动匹配屏幕刷新率 (通常 60Hz, 即 16.67ms/帧)
// - 页面不可见时自动暂停 (节省 CPU 和电池)
// - 比 setTimeout 更精确, 不受系统定时器精度限制
```

RAF 与 setTimeout 的区别:
- **RAF**: 浏览器控制调用时机, 与屏幕刷新同步, 精度高
- **setTimeout**: 固定时间间隔, 无法保证与屏幕刷新同步, 可能浪费帧

---

**规则 2: 每帧的 JavaScript 执行时间应控制在 10 毫秒以内**

浏览器需要在一帧 (16.67ms @ 60fps) 内完成所有工作, JavaScript 只能占用其中一部分。

```javascript
// 时间预算分配 (60fps, 16.67ms/帧)
// - JavaScript 执行: 目标 < 10ms
// - 样式计算: ~1-2ms
// - 布局: ~2-3ms
// - 绘制: ~2-3ms
// - 合成: ~1-2ms
// 总计: ~16.67ms

// ❌ 错误: 耗时的帧内计算
function expensiveAnimate(currentTime) {
    const progress = (currentTime - startTime) / duration;

    // 复杂的数学运算
    const easing = Math.sin(progress * Math.PI / 2) * Math.exp(-5 * progress);

    // 大量 DOM 操作
    for (let i = 0; i < 100; i++) {
        elements[i].style.transform = `translateX(${easing * distances[i]}px)`;
    }

    requestAnimationFrame(expensiveAnimate);
}
// 结果: 帧时间 > 16.67ms → 掉帧 → 卡顿

// ✅ 正确: 优化的帧内计算
const easingTable = precomputeEasing(100);  // 初始化时预计算

function optimizedAnimate(currentTime) {
    const progress = (currentTime - startTime) / duration;

    // O(1) 查表
    const easing = easingTable.getValue(progress);

    // 批量更新 (减少重排次数)
    const fragment = document.createDocumentFragment();
    for (let i = 0; i < 100; i++) {
        elements[i].style.transform = `translateX(${easing * distances[i]}px)`;
    }

    requestAnimationFrame(optimizedAnimate);
}
// 结果: 帧时间 < 10ms → 流畅 60fps
```

性能监控:
```javascript
// 监控帧时间
let lastFrameTime = performance.now();

function monitoredAnimate(currentTime) {
    const frameDuration = currentTime - lastFrameTime;
    lastFrameTime = currentTime;

    if (frameDuration > 16.67) {
        console.warn(`Long frame: ${frameDuration.toFixed(2)}ms`);
    }

    // 动画逻辑...

    requestAnimationFrame(monitoredAnimate);
}
```

---

**规则 3: 必须正确取消旧动画, 避免并发冲突**

多个 RAF 循环同时运行会导致冲突、性能下降和不可预测的行为。

```javascript
// ❌ 错误: 没有取消旧动画
let rafId;

function startAnimation() {
    function animate() {
        // 动画逻辑...
        rafId = requestAnimationFrame(animate);
    }

    animate();  // 问题: 每次调用都创建新循环, 旧循环还在运行
}

// 用户快速点击 3 次
startAnimation();  // 循环 1 启动
startAnimation();  // 循环 2 启动, 循环 1 仍在运行
startAnimation();  // 循环 3 启动, 循环 1, 2 仍在运行
// 结果: 3 个循环互相干扰, 性能下降 3 倍

// ✅ 正确: 取消旧动画再启动新动画
let rafId = null;

function startAnimation() {
    // 取消旧动画
    if (rafId !== null) {
        cancelAnimationFrame(rafId);
    }

    function animate() {
        // 动画逻辑...
        rafId = requestAnimationFrame(animate);
    }

    animate();
}

// 用户快速点击 3 次
startAnimation();  // 循环启动
startAnimation();  // 取消旧循环, 启动新循环
startAnimation();  // 取消旧循环, 启动新循环
// 结果: 只有 1 个循环运行, 性能正常

// 完整的动画管理类
class AnimationController {
    constructor() {
        this.rafId = null;
        this.isRunning = false;
    }

    start(animationCallback) {
        // 取消旧动画
        this.stop();

        this.isRunning = true;

        const animate = (currentTime) => {
            if (!this.isRunning) return;

            animationCallback(currentTime);

            this.rafId = requestAnimationFrame(animate);
        };

        this.rafId = requestAnimationFrame(animate);
    }

    stop() {
        if (this.rafId !== null) {
            cancelAnimationFrame(this.rafId);
            this.rafId = null;
        }
        this.isRunning = false;
    }

    pause() {
        this.isRunning = false;
    }

    resume(animationCallback) {
        if (!this.isRunning) {
            this.isRunning = true;
            this.rafId = requestAnimationFrame(animationCallback);
        }
    }
}
```

---

**规则 4: 使用 performance.now() 而非 Date.now() 计算时间**

performance.now() 提供高精度时间戳, 不受系统时间调整影响, 更适合动画计算。

```javascript
// ❌ 错误: 使用 Date.now()
const startTime = Date.now();

function animate() {
    const elapsed = Date.now() - startTime;
    const progress = elapsed / duration;
    // 问题:
    // 1. 精度低 (只到毫秒)
    // 2. 受系统时间调整影响 (用户修改时间, NTP 同步)
    // 3. 不单调递增 (时间可能倒退)
}

// ✅ 正确: 使用 performance.now()
const startTime = performance.now();

function animate(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = elapsed / duration;
    // 优势:
    // 1. 精度高 (微秒级, 0.001ms)
    // 2. 不受系统时间影响
    // 3. 单调递增 (永不倒退)
    // 4. RAF 回调自动传入 currentTime 参数
}

// 时间精度对比
console.log(Date.now());          // 1704038400000 (毫秒)
console.log(performance.now());   // 1234567.891234 (微秒精度)

// 实际影响
const start = performance.now();
// 极短的操作
const end = performance.now();

console.log(end - start);         // 0.012345 (可以测量微秒级操作)

const start2 = Date.now();
// 极短的操作
const end2 = Date.now();

console.log(end2 - start2);       // 0 (毫秒级无法测量)
```

performance.now() 的特点:
- **原点**: 页面导航开始时刻 (不是 Unix 纪元)
- **精度**: 微秒级 (0.001ms), 但出于安全考虑可能降低精度
- **单调性**: 永远递增, 不会倒退
- **独立性**: 不受系统时间调整影响

---

**规则 5: 缓动函数应预计算或使用查找表优化**

复杂的数学计算会占用大量帧时间, 预计算可将运行时开销降到最低。

```javascript
// ❌ 错误: 每帧计算复杂缓动函数
function animate(currentTime) {
    const progress = (currentTime - startTime) / duration;

    // 每帧都执行复杂计算
    const easing = Math.sin(progress * Math.PI / 2) * (1 - Math.exp(-5 * progress));

    applyAnimation(easing);
    requestAnimationFrame(animate);
}
// 性能: 60fps 时每秒执行 60 次复杂计算

// ✅ 正确: 预计算查找表
class EasingLUT {
    constructor(easingFunction, samples = 100) {
        this.lut = [];
        this.samples = samples;

        // 初始化时预计算
        for (let i = 0; i <= samples; i++) {
            const t = i / samples;
            this.lut.push(easingFunction(t));
        }
    }

    getValue(progress) {
        // 运行时只做查表和线性插值
        const index = progress * this.samples;
        const lower = Math.floor(index);
        const upper = Math.ceil(index);

        if (lower === upper) {
            return this.lut[lower];
        }

        const t = index - lower;
        return this.lut[lower] * (1 - t) + this.lut[upper] * t;
    }
}

// 初始化 (只执行一次)
const easing = new EasingLUT(
    t => Math.sin(t * Math.PI / 2) * (1 - Math.exp(-5 * t)),
    100
);

// 运行时 (每帧执行)
function animate(currentTime) {
    const progress = (currentTime - startTime) / duration;
    const easedProgress = easing.getValue(progress);  // O(1) 查找

    applyAnimation(easedProgress);
    requestAnimationFrame(animate);
}
// 性能: 60fps 时每秒只做 60 次简单查表和插值, 快 10-100 倍

// 性能对比
const complexEasing = t => Math.sin(t * Math.PI / 2) * (1 - Math.exp(-5 * t));
const simpleLUT = new EasingLUT(complexEasing, 100);

console.time('Direct calculation (1000 times)');
for (let i = 0; i < 1000; i++) {
    const result = complexEasing(i / 1000);
}
console.timeEnd('Direct calculation (1000 times)');
// 直接计算: 15.2ms

console.time('LUT lookup (1000 times)');
for (let i = 0; i < 1000; i++) {
    const result = simpleLUT.getValue(i / 1000);
}
console.timeEnd('LUT lookup (1000 times)');
// 查找表: 0.8ms (快 19 倍)
```

查找表权衡:
- **优势**: 运行时性能显著提升 (10-100 倍)
- **代价**: 初始化时间增加, 内存占用增加 (samples 个浮点数)
- **精度**: 取决于 samples 数量 (100 通常足够, 视觉上无差异)
- **适用场景**: 复杂数学函数, 高频调用 (每帧执行)

---

**规则 6: 使用 transform 而非 top/left, 避免触发重排**

transform 属性可以被浏览器优化到合成线程, 不触发重排和重绘, 性能远超 position 属性。

```javascript
// ❌ 错误: 使用 top/left 动画
function animatePosition(currentTime) {
    const progress = (currentTime - startTime) / duration;
    const easing = easeOut(progress);

    // 修改 top/left 触发重排
    element.style.top = startY + (targetY - startY) * easing + 'px';
    element.style.left = startX + (targetX - startX) * easing + 'px';

    requestAnimationFrame(animatePosition);
}
// 性能: 每帧触发重排 → Layout → Paint → Composite (很慢)

// ✅ 正确: 使用 transform 动画
function animateTransform(currentTime) {
    const progress = (currentTime - startTime) / duration;
    const easing = easeOut(progress);

    const currentX = startX + (targetX - startX) * easing;
    const currentY = startY + (targetY - startY) * easing;

    // transform 不触发重排, 只触发合成
    element.style.transform = `translate(${currentX}px, ${currentY}px)`;

    requestAnimationFrame(animateTransform);
}
// 性能: 直接在合成线程执行 (极快)

// 浏览器渲染流程对比
// 修改 top/left:
// JavaScript → 样式计算 → 布局 (重排) → 绘制 (重绘) → 合成
//                           ↑ 昂贵           ↑ 昂贵

// 修改 transform:
// JavaScript → 样式计算 → 合成
//                        ↑ 仅此步骤, 极快

// 性能数据对比
// top/left 动画: 每帧 ~12ms (重排 + 重绘)
// transform 动画: 每帧 ~2ms (仅合成)
```

GPU 加速属性:
- ✅ `transform`: translate, scale, rotate, skew, matrix
- ✅ `opacity`: 透明度
- ❌ `top`, `left`, `right`, `bottom`: 触发重排
- ❌ `width`, `height`: 触发重排
- ❌ `margin`, `padding`: 触发重排
- ❌ `background`, `color`: 触发重绘

最佳实践:
```javascript
// 使用 will-change 提示浏览器提前优化
element.style.willChange = 'transform, opacity';

// 或使用 transform: translateZ(0) 强制创建合成层
element.style.transform = 'translateZ(0)';

// 动画结束后清理 will-change
function animateComplete() {
    element.style.willChange = 'auto';
}
```

---

**规则 7: 物理模拟动画需要基于时间差 (delta time) 计算**

物理动画的每一帧依赖前一帧的状态, 必须使用时间差来保证不同帧率下的一致性。

```javascript
// ❌ 错误: 固定步长的物理模拟
class SpringAnimatorBad {
    constructor() {
        this.position = 0;
        this.velocity = 0;
        this.target = 0;
    }

    update() {
        // 假设每帧 16.67ms, 但实际帧率可能变化
        const dt = 0.01667;  // 固定时间步长

        const force = -200 * (this.position - this.target) - 20 * this.velocity;
        this.velocity += force * dt;
        this.position += this.velocity * dt;

        applyPosition(this.position);
        requestAnimationFrame(() => this.update());
    }
}
// 问题: 帧率变化时, 动画速度会变化 (30fps 时速度减半)

// ✅ 正确: 基于实际时间差的物理模拟
class SpringAnimatorGood {
    constructor(stiffness = 200, damping = 20) {
        this.position = 0;
        this.velocity = 0;
        this.target = 0;
        this.stiffness = stiffness;
        this.damping = damping;
        this.lastTime = null;
    }

    update(currentTime) {
        if (this.lastTime === null) {
            this.lastTime = currentTime;
        }

        // 计算实际时间差 (自适应帧率)
        const dt = (currentTime - this.lastTime) / 1000;  // 转为秒
        this.lastTime = currentTime;

        // 胡克定律: F = -k * x - c * v
        const force = -this.stiffness * (this.position - this.target) - this.damping * this.velocity;
        this.velocity += force * dt;
        this.position += this.velocity * dt;

        applyPosition(this.position);

        // 检查是否静止
        const isAtRest = Math.abs(this.velocity) < 0.1 && Math.abs(this.position - this.target) < 0.1;

        if (!isAtRest) {
            requestAnimationFrame((t) => this.update(t));
        }
    }

    setTarget(newTarget) {
        this.target = newTarget;
        this.lastTime = null;
        requestAnimationFrame((t) => this.update(t));
    }
}
// 优势: 任何帧率下动画速度一致 (30fps, 60fps, 120fps 都相同)

// 时间差的重要性示例
// 假设目标是 1 秒内移动 100 像素

// 固定步长 (错误):
// 60fps: 100 / 60 = 1.67px/帧 → 1 秒后移动 100px ✓
// 30fps: 100 / 30 = 3.33px/帧 → 1 秒后移动 100px ✓
// 但物理公式中的 dt 是固定的 0.01667s, 导致:
// 30fps 时实际 dt = 0.0333s, 但公式用的是 0.01667s
// 结果: 30fps 时动画速度减半 ✗

// 基于时间差 (正确):
// 60fps: dt = 0.01667s → 每帧计算正确
// 30fps: dt = 0.0333s → 每帧计算正确
// 结果: 任何帧率下动画速度相同 ✓
```

物理模拟参数:
- **stiffness (刚度)**: 弹簧强度, 值越大恢复越快
- **damping (阻尼)**: 阻力, 值越大振荡越少
- **mass (质量)**: 影响加速度, 通常固定为 1

---

**规则 8: 根据场景选择 CSS 或 JavaScript 动画, 或使用混合方案**

CSS 和 JavaScript 动画各有优劣, 应根据需求选择最合适的技术。

```javascript
// 决策矩阵

// 场景 1: 简单状态切换 (hover, active, focus)
// → 使用 CSS transition
.button {
    transition: background-color 0.3s ease-out;
}
.button:hover {
    background-color: #007bff;
}
// 优势: 浏览器自动优化, 性能最佳, 代码简洁

// 场景 2: 关键帧动画 (固定序列)
// → 使用 CSS @keyframes
@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}
.icon {
    animation: pulse 2s infinite;
}
// 优势: 不占用主线程, 即使 JS 阻塞也流畅

// 场景 3: 动态目标值 (根据用户输入实时计算)
// → 必须使用 JavaScript + RAF
function smoothScrollTo(targetY) {
    // targetY 是动态计算的, CSS 无法实现
    const start = window.scrollY;
    const distance = targetY - start;

    function animate(currentTime) {
        const progress = (currentTime - startTime) / duration;
        const easing = easeOut(progress);
        const currentY = start + distance * easing;

        window.scrollTo(0, currentY);

        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }

    requestAnimationFrame(animate);
}

// 场景 4: 跟随鼠标/手指的交互动画
// → 必须使用 JavaScript
let mouseX = 0, mouseY = 0;

document.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
});

function followCursor(currentTime) {
    // 元素跟随鼠标, 每帧目标都不同
    const currentX = parseFloat(tooltip.style.left) || 0;
    const currentY = parseFloat(tooltip.style.top) || 0;

    const dx = (mouseX - currentX) * 0.1;
    const dy = (mouseY - currentY) * 0.1;

    tooltip.style.transform = `translate(${currentX + dx}px, ${currentY + dy}px)`;

    requestAnimationFrame(followCursor);
}

// 场景 5: 混合方案 - JavaScript 控制, CSS 执行
// → 动态设置 CSS 变量
function animateWithCSS(targetValue) {
    // JavaScript 计算目标值
    const distance = targetValue - currentValue;

    // 设置 CSS 变量
    element.style.setProperty('--start', currentValue);
    element.style.setProperty('--end', targetValue);
    element.style.setProperty('--duration', '500ms');

    // CSS 执行动画
    element.classList.add('animating');

    setTimeout(() => {
        element.classList.remove('animating');
        currentValue = targetValue;
    }, 500);
}

/* CSS 定义动画 */
@keyframes move {
    from { transform: translateX(calc(var(--start) * 1px)); }
    to { transform: translateX(calc(var(--end) * 1px)); }
}

.animating {
    animation: move var(--duration) cubic-bezier(0.4, 0, 0.2, 1);
}

// 场景 6: 物理模拟 (弹簧, 惯性)
// → 必须使用 JavaScript 物理引擎
class PhysicsAnimator {
    // 弹簧方程: F = -k * x - c * v
    // 需要逐帧计算速度和加速度
}

// 场景 7: 大量并发动画 (粒子系统, 游戏)
// → JavaScript + Web Worker
const worker = new Worker('particles-worker.js');

worker.postMessage({ particles: 1000, deltaTime: dt });

worker.onmessage = (e) => {
    const { positions } = e.data;
    updateParticles(positions);
};
```

选择建议:
- **CSS 优先**: 简单状态切换, 固定序列动画, 性能关键场景
- **JavaScript 必需**: 动态目标, 实时交互, 物理模拟, 复杂逻辑
- **混合方案**: 需要动态计算但目标值固定的场景
- **性能优先级**: CSS transition > CSS @keyframes > JS + transform > JS + position

性能对比:
```
场景: 同时动画 100 个元素

CSS transition:
- 主线程占用: ~5%
- FPS: 60
- 帧时间: 16.5ms

JS + transform + RAF:
- 主线程占用: ~25%
- FPS: 58-60
- 帧时间: 16.8ms

JS + top/left + RAF:
- 主线程占用: ~80%
- FPS: 35-45
- 帧时间: 25-30ms
```

---

**事故档案编号**: NETWORK-2024-1961
**影响范围**: requestAnimationFrame, JavaScript 动画控制, 性能优化, CSS 对比
**根本原因**: RAF 回调执行时间过长导致掉帧, 未取消旧动画导致并发冲突, 缺乏优化意识
**学习成本**: 中 (需理解浏览器渲染流程、RAF 时机、性能优化技巧)

这是 JavaScript 世界第 161 次被记录的网络与数据事故。requestAnimationFrame 在浏览器绘制之前执行, 每帧调用一次, 自动匹配屏幕刷新率。每帧的 JavaScript 执行时间应控制在 10 毫秒以内, 避免超出时间预算导致掉帧。必须正确取消旧动画, 避免多个 RAF 循环并发运行导致冲突和性能下降。使用 performance.now() 而非 Date.now() 计算时间, 提供微秒级精度和单调递增保证。复杂的缓动函数应预计算或使用查找表优化, 避免每帧重复计算。使用 transform 而非 top/left 动画, transform 可被优化到合成线程, 不触发重排和重绘。物理模拟动画需要基于时间差 (delta time) 计算, 保证不同帧率下的一致性。根据场景选择 CSS 或 JavaScript 动画: CSS 适合简单状态切换和固定序列, JavaScript 适合动态目标和实时交互, 混合方案结合两者优势。理解 RAF 机制和优化技巧是实现流畅高性能动画的基础。

---

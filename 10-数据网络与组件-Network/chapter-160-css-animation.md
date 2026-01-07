《第 160 次记录: 周一的技术债务 —— JavaScript 动画向 CSS 动画系统的渐进迁移》

---

## 遗留代码的性能危机

周一上午九点, 你打开项目代码库的第一天。

这是公司接手的一个外包项目, 前端代码已经运行了两年, 但最近用户投诉越来越多: "在手机上滑动很卡"、"动画效果一顿一顿的"、"打开页面就发热"。

技术经理老李把你叫到办公室: "这个项目的动画实现有问题, 你先评估一下, 看能不能优化。"

你打开 Chrome DevTools 的 Performance 面板, 录制了一次页面交互。火焰图让你倒吸一口凉气——**JavaScript 执行占用了 87% 的主线程时间**, 几乎每一帧都在执行动画计算。

你翻开代码, 看到了这样的实现:

```javascript
// legacy-animation.js - 遗留的动画实现
class LegacyAnimator {
    constructor(element) {
        this.element = element;
        this.isRunning = false;
    }

    // 淡入动画
    fadeIn(duration = 500) {
        this.isRunning = true;
        const startTime = Date.now();
        const startOpacity = parseFloat(getComputedStyle(this.element).opacity) || 0;

        const animate = () => {
            if (!this.isRunning) return;

            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // ❌ 每帧都在操作 DOM 和计算样式
            this.element.style.opacity = startOpacity + progress * (1 - startOpacity);

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    // 滑入动画
    slideIn(duration = 500, distance = 100) {
        this.isRunning = true;
        const startTime = Date.now();

        const animate = () => {
            if (!this.isRunning) return;

            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // ❌ transform 计算在主线程
            const currentDistance = distance * (1 - progress);
            this.element.style.transform = `translateX(${currentDistance}px)`;

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    // 脉冲动画
    pulse(duration = 1000) {
        this.isRunning = true;
        const startTime = Date.now();

        const animate = () => {
            if (!this.isRunning) return;

            const elapsed = Date.now() - startTime;
            const progress = (elapsed % duration) / duration;

            // ❌ 复杂的缓动函数计算
            const scale = 1 + Math.sin(progress * Math.PI * 2) * 0.1;
            this.element.style.transform = `scale(${scale})`;

            if (this.isRunning) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    stop() {
        this.isRunning = false;
    }
}

// 页面中有 50+ 个动画同时运行
document.querySelectorAll('.card').forEach(card => {
    const animator = new LegacyAnimator(card);
    animator.fadeIn(500);
    animator.pulse(2000);
});
```

你在笔记中写下问题清单:

```
性能问题分析:

1. 主线程阻塞:
   - 50+ 个动画同时在 JavaScript 中计算
   - 每帧执行 50+ 次 style 操作
   - requestAnimationFrame 回调过多

2. 无 GPU 加速:
   - 直接操作 style.opacity 和 style.transform
   - 浏览器无法优化到合成层

3. 内存泄漏风险:
   - 动画对象未正确清理
   - 闭包持有 DOM 引用

4. 代码维护成本高:
   - 每个动画都需要手写缓动函数
   - 时间控制逻辑重复
   - 难以调试和修改
```

"这些动画完全可以用 CSS 实现, " 你对老李说, "但不能一次性全改, 风险太大。我建议渐进式迁移。"

老李点头: "好, 你做个迁移方案, 我们分三周逐步推进。"

---

## 第一周: 基础迁移与工具建设

你从最简单的淡入动画开始。

### 迁移第一步: 定义 CSS @keyframes

你创建了一个新的样式文件 `animations.css`:

```css
/* animations.css - CSS 动画系统 */

/* 淡入动画 */
@keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

/* 滑入动画 */
@keyframes slideInRight {
    from {
        transform: translateX(100px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

/* 脉冲动画 */
@keyframes pulse {
    0% {
        transform: scale(1);
    }
    50% {
        transform: scale(1.1);
    }
    100% {
        transform: scale(1);
    }
}

/* 旋转加载 */
@keyframes spin {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}

/* 弹跳进入 */
@keyframes bounceIn {
    0% {
        transform: scale(0.3);
        opacity: 0;
    }
    50% {
        transform: scale(1.05);
    }
    70% {
        transform: scale(0.9);
    }
    100% {
        transform: scale(1);
        opacity: 1;
    }
}

/* 摇晃 */
@keyframes shake {
    0%, 100% {
        transform: translateX(0);
    }
    10%, 30%, 50%, 70%, 90% {
        transform: translateX(-10px);
    }
    20%, 40%, 60%, 80% {
        transform: translateX(10px);
    }
}
```

### 迁移第二步: 创建工具类

你定义了一套可复用的 CSS 类:

```css
/* 动画工具类 */

/* 淡入动画 - 不同持续时间 */
.animate-fadeIn {
    animation-name: fadeIn;
    animation-duration: 0.5s;
    animation-timing-function: ease-out;
    animation-fill-mode: both;
}

.animate-fadeIn-fast {
    animation-name: fadeIn;
    animation-duration: 0.3s;
    animation-timing-function: ease-out;
    animation-fill-mode: both;
}

.animate-fadeIn-slow {
    animation-name: fadeIn;
    animation-duration: 1s;
    animation-timing-function: ease-out;
    animation-fill-mode: both;
}

/* 滑入动画 */
.animate-slideInRight {
    animation-name: slideInRight;
    animation-duration: 0.5s;
    animation-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
    animation-fill-mode: both;
}

/* 脉冲动画 - 无限循环 */
.animate-pulse {
    animation-name: pulse;
    animation-duration: 2s;
    animation-timing-function: ease-in-out;
    animation-iteration-count: infinite;
}

/* 旋转加载 */
.animate-spin {
    animation-name: spin;
    animation-duration: 1s;
    animation-timing-function: linear;
    animation-iteration-count: infinite;
}

/* 弹跳进入 */
.animate-bounceIn {
    animation-name: bounceIn;
    animation-duration: 0.6s;
    animation-timing-function: cubic-bezier(0.68, -0.55, 0.265, 1.55);
    animation-fill-mode: both;
}

/* 摇晃 */
.animate-shake {
    animation-name: shake;
    animation-duration: 0.5s;
    animation-timing-function: linear;
    animation-fill-mode: both;
}

/* 延迟变体 */
.animate-delay-100 {
    animation-delay: 0.1s;
}

.animate-delay-200 {
    animation-delay: 0.2s;
}

.animate-delay-300 {
    animation-delay: 0.3s;
}

.animate-delay-500 {
    animation-delay: 0.5s;
}

/* GPU 加速优化 */
.animate-gpu-accelerated {
    will-change: transform, opacity;
    transform: translateZ(0);
}

/* 暂停动画 */
.animate-paused {
    animation-play-state: paused;
}
```

### 迁移第三步: JavaScript 工具封装

你创建了一个轻量级的 JavaScript 工具类, 用于动态控制 CSS 动画:

```javascript
// css-animator.js - CSS 动画控制工具
class CSSAnimator {
    constructor(element) {
        this.element = element;
    }

    // 播放动画
    play(animationClass, options = {}) {
        return new Promise((resolve) => {
            // 移除可能存在的旧动画类
            this.element.classList.remove(animationClass);

            // 触发重排以重启动画
            void this.element.offsetWidth;

            // 添加动画类
            this.element.classList.add(animationClass);

            // 添加延迟类
            if (options.delay) {
                const delayClass = `animate-delay-${options.delay}`;
                this.element.classList.add(delayClass);
            }

            // 监听动画结束
            const handleAnimationEnd = (e) => {
                if (e.target === this.element) {
                    this.element.removeEventListener('animationend', handleAnimationEnd);

                    // 清理延迟类
                    if (options.delay) {
                        const delayClass = `animate-delay-${options.delay}`;
                        this.element.classList.remove(delayClass);
                    }

                    // 清理动画类 (如果需要)
                    if (options.removeOnComplete) {
                        this.element.classList.remove(animationClass);
                    }

                    resolve();
                }
            };

            this.element.addEventListener('animationend', handleAnimationEnd);
        });
    }

    // 暂停动画
    pause() {
        this.element.classList.add('animate-paused');
    }

    // 恢复动画
    resume() {
        this.element.classList.remove('animate-paused');
    }

    // 停止动画
    stop(animationClass) {
        this.element.classList.remove(animationClass);
    }

    // 序列动画
    async sequence(animations) {
        for (const { class: animationClass, options } of animations) {
            await this.play(animationClass, options);
        }
    }
}

// 使用示例
const card = document.querySelector('.card');
const animator = new CSSAnimator(card);

// 单个动画
animator.play('animate-fadeIn');

// 带选项的动画
animator.play('animate-slideInRight', {
    delay: 200,
    removeOnComplete: true
});

// 序列动画
animator.sequence([
    { class: 'animate-fadeIn', options: {} },
    { class: 'animate-shake', options: { removeOnComplete: true } },
    { class: 'animate-bounceIn', options: {} }
]);
```

### 第一周成果验证

周五下午, 你将第一批 20 个简单动画迁移到了 CSS 实现。你再次录制 Performance 面板:

```
性能对比 (20 个动画):

迁移前 (JavaScript):
- 主线程占用: 87%
- FPS: 45-50
- 内存: 125MB

迁移后 (CSS):
- 主线程占用: 12%
- FPS: 58-60
- 内存: 98MB

✅ 主线程占用下降 86%
✅ FPS 提升 20%
✅ 内存占用下降 22%
```

"效果很明显, " 老李看着监控数据说, "继续推进。"

---

## 第二周: 复杂动画与组合

第二周, 你开始迁移更复杂的动画效果。

### 多属性组合动画

原来的 JavaScript 代码实现了一个复杂的卡片翻转效果:

```javascript
// 旧实现: JavaScript 翻转动画
function flipCard(card) {
    const duration = 600;
    const startTime = Date.now();

    const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // 计算旋转角度
        const rotateY = progress * 180;

        // 计算缩放 (中间缩小)
        const scale = 1 - Math.sin(progress * Math.PI) * 0.1;

        // 计算阴影
        const shadow = 10 + Math.sin(progress * Math.PI) * 20;

        card.style.transform = `perspective(1000px) rotateY(${rotateY}deg) scale(${scale})`;
        card.style.boxShadow = `0 ${shadow}px ${shadow * 2}px rgba(0,0,0,0.3)`;

        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    };

    requestAnimationFrame(animate);
}
```

你用 CSS @keyframes 重新实现:

```css
/* 卡片翻转动画 */
@keyframes flipCard {
    0% {
        transform: perspective(1000px) rotateY(0deg) scale(1);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
    }
    50% {
        transform: perspective(1000px) rotateY(90deg) scale(0.9);
        box-shadow: 0 30px 60px rgba(0, 0, 0, 0.3);
    }
    100% {
        transform: perspective(1000px) rotateY(180deg) scale(1);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
    }
}

.animate-flipCard {
    animation: flipCard 0.6s cubic-bezier(0.4, 0, 0.2, 1) both;
    transform-style: preserve-3d;
}

/* 翻转容器 */
.flip-container {
    perspective: 1000px;
}

.flip-card {
    position: relative;
    width: 100%;
    height: 100%;
    transform-style: preserve-3d;
    transition: transform 0.6s;
}

.flip-card.flipped {
    transform: rotateY(180deg);
}

.flip-card-front,
.flip-card-back {
    position: absolute;
    width: 100%;
    height: 100%;
    backface-visibility: hidden;
}

.flip-card-back {
    transform: rotateY(180deg);
}
```

### 关键帧的精细控制

你发现有些动画需要在特定时刻改变速度或方向:

```css
/* 复杂的弹跳路径 */
@keyframes complexBounce {
    0% {
        transform: translateY(0) scale(1, 1);
        animation-timing-function: ease-in;
    }
    25% {
        transform: translateY(-100px) scale(1.1, 0.9);
        animation-timing-function: ease-out;
    }
    40% {
        transform: translateY(-50px) scale(0.9, 1.1);
        animation-timing-function: ease-in;
    }
    55% {
        transform: translateY(-25px) scale(1.05, 0.95);
        animation-timing-function: ease-out;
    }
    70% {
        transform: translateY(-10px) scale(0.95, 1.05);
        animation-timing-function: ease-in;
    }
    85% {
        transform: translateY(-5px) scale(1.02, 0.98);
        animation-timing-function: ease-out;
    }
    100% {
        transform: translateY(0) scale(1, 1);
    }
}

.animate-complexBounce {
    animation: complexBounce 1.2s both;
}
```

### 多动画并行

你学会了如何同时运行多个独立的动画:

```css
/* 同时进行淡入和滑入 */
.animate-fadeAndSlide {
    animation: fadeIn 0.5s ease-out both,
               slideInRight 0.5s cubic-bezier(0.4, 0, 0.2, 1) both;
}

/* 循环脉冲 + 旋转 */
.animate-pulseAndSpin {
    animation: pulse 2s ease-in-out infinite,
               spin 4s linear infinite;
}

/* 组合动画: 进入 + 强调 */
@keyframes enter {
    from {
        transform: translateY(50px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}

@keyframes emphasize {
    0%, 100% {
        transform: scale(1);
    }
    50% {
        transform: scale(1.05);
    }
}

.animate-enterAndEmphasize {
    animation: enter 0.5s ease-out both,
               emphasize 0.3s ease-in-out 0.5s both;
}
```

### 动画事件监听

你发现 CSS 动画也支持事件监听:

```javascript
// 监听 CSS 动画事件
class AnimationEventHandler {
    constructor(element) {
        this.element = element;
        this.listeners = new Map();
    }

    // 动画开始
    onStart(callback) {
        const handler = (e) => {
            if (e.target === this.element) {
                callback(e);
            }
        };

        this.element.addEventListener('animationstart', handler);
        this.listeners.set('start', handler);
        return this;
    }

    // 动画结束
    onEnd(callback) {
        const handler = (e) => {
            if (e.target === this.element) {
                callback(e);
            }
        };

        this.element.addEventListener('animationend', handler);
        this.listeners.set('end', handler);
        return this;
    }

    // 动画迭代 (循环动画每次完成时)
    onIteration(callback) {
        const handler = (e) => {
            if (e.target === this.element) {
                callback(e);
            }
        };

        this.element.addEventListener('animationiteration', handler);
        this.listeners.set('iteration', handler);
        return this;
    }

    // 移除所有监听器
    removeAll() {
        this.listeners.forEach((handler, event) => {
            this.element.removeEventListener(`animation${event}`, handler);
        });
        this.listeners.clear();
    }
}

// 使用示例
const element = document.querySelector('.animated');
const events = new AnimationEventHandler(element);

events
    .onStart((e) => {
        console.log('动画开始:', e.animationName);
    })
    .onEnd((e) => {
        console.log('动画结束:', e.animationName);
        element.classList.add('animation-completed');
    })
    .onIteration((e) => {
        console.log('动画循环:', e.elapsedTime);
    });
```

### 第二周性能验证

```
性能对比 (50 个复杂动画):

迁移前 (JavaScript):
- 主线程占用: 92%
- FPS: 38-42
- Composite Layers: 5
- GPU Memory: 45MB

迁移后 (CSS):
- 主线程占用: 8%
- FPS: 59-60
- Composite Layers: 52
- GPU Memory: 78MB

✅ 主线程占用下降 91%
✅ FPS 提升 45%
⚠️ GPU 内存增加 (合理范围内)
✅ 合成层数量增加 (GPU 加速生效)
```

---

## 第三周: 性能优化与最佳实践

第三周, 你专注于性能优化和建立最佳实践规范。

### GPU 加速优化

你发现并不是所有 CSS 属性都能享受 GPU 加速:

```css
/* ✅ GPU 加速的属性 (推荐) */
.gpu-optimized {
    /* transform 属性 */
    transform: translate3d(0, 0, 0);
    transform: translateX(100px);
    transform: scale(1.2);
    transform: rotate(45deg);

    /* opacity 属性 */
    opacity: 0.8;

    /* 提示浏览器提前创建合成层 */
    will-change: transform, opacity;
}

/* ❌ 无 GPU 加速的属性 (避免动画) */
.non-gpu-properties {
    /* 这些属性会触发重排或重绘 */
    width: 100px;       /* 触发重排 */
    height: 200px;      /* 触发重排 */
    top: 50px;          /* 触发重排 */
    left: 100px;        /* 触发重排 */
    margin: 20px;       /* 触发重排 */
    padding: 15px;      /* 触发重排 */
    color: red;         /* 触发重绘 */
    background: blue;   /* 触发重绘 */
    border: 1px solid;  /* 触发重绘 */
}
```

你创建了一个优化指南:

```css
/* 性能优化最佳实践 */

/* 1. 使用 transform 代替 position */
/* ❌ 差: 触发重排 */
.slide-bad {
    position: relative;
    animation: slideBad 1s;
}

@keyframes slideBad {
    from { left: 0; }
    to { left: 100px; }
}

/* ✅ 好: 使用 transform */
.slide-good {
    animation: slideGood 1s;
}

@keyframes slideGood {
    from { transform: translateX(0); }
    to { transform: translateX(100px); }
}

/* 2. 使用 opacity 代替 display 或 visibility */
/* ❌ 差: 无法动画 */
.fade-bad {
    display: none;
}

/* ✅ 好: 可以平滑过渡 */
.fade-good {
    opacity: 0;
    pointer-events: none;
}

/* 3. 使用 will-change 提示浏览器 */
/* 为即将动画的元素添加 will-change */
.will-animate {
    will-change: transform, opacity;
}

/* 动画结束后移除 will-change */
.animation-complete {
    will-change: auto;
}

/* 4. 避免同时动画过多元素 */
/* 使用 animation-delay 错开动画 */
.stagger-animation:nth-child(1) { animation-delay: 0s; }
.stagger-animation:nth-child(2) { animation-delay: 0.1s; }
.stagger-animation:nth-child(3) { animation-delay: 0.2s; }
.stagger-animation:nth-child(4) { animation-delay: 0.3s; }

/* 5. 使用 transform: translateZ(0) 强制 GPU 加速 */
.force-gpu {
    transform: translateZ(0);
    /* 或 */
    transform: translate3d(0, 0, 0);
}

/* 6. 避免在动画中改变 box-shadow (性能差) */
/* ❌ 差: box-shadow 动画很慢 */
@keyframes shadowBad {
    from { box-shadow: 0 0 0 rgba(0,0,0,0); }
    to { box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
}

/* ✅ 好: 使用伪元素 + opacity */
.shadow-good {
    position: relative;
}

.shadow-good::after {
    content: '';
    position: absolute;
    inset: 0;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    opacity: 0;
    transition: opacity 0.3s;
}

.shadow-good:hover::after {
    opacity: 1;
}
```

### 调试工具

你整理了一套调试 CSS 动画的方法:

```css
/* 动画调试工具 */

/* 1. 放慢动画速度 (调试时) */
.debug-slow * {
    animation-duration: 5s !important;
    transition-duration: 5s !important;
}

/* 2. 暂停所有动画 */
.debug-pause * {
    animation-play-state: paused !important;
}

/* 3. 显示合成层边界 (Chrome DevTools) */
/* 在 DevTools → Rendering → Layer borders 中启用 */

/* 4. 动画性能分析 */
/* Chrome DevTools → Performance → 录制 → 分析 Animation 轨道 */

/* 5. will-change 使用检测 */
/* DevTools → Coverage 查看是否有未使用的 will-change */
```

```javascript
// JavaScript 调试工具
class AnimationDebugger {
    // 列出所有活动动画
    static listActiveAnimations() {
        const animations = [];

        document.querySelectorAll('*').forEach(element => {
            const computed = getComputedStyle(element);
            const animationName = computed.animationName;

            if (animationName && animationName !== 'none') {
                animations.push({
                    element,
                    name: animationName,
                    duration: computed.animationDuration,
                    iterationCount: computed.animationIterationCount,
                    playState: computed.animationPlayState
                });
            }
        });

        return animations;
    }

    // 暂停所有动画
    static pauseAll() {
        document.querySelectorAll('*').forEach(element => {
            const computed = getComputedStyle(element);
            if (computed.animationName !== 'none') {
                element.style.animationPlayState = 'paused';
            }
        });
    }

    // 恢复所有动画
    static resumeAll() {
        document.querySelectorAll('*').forEach(element => {
            element.style.animationPlayState = '';
        });
    }

    // 检查 GPU 加速状态
    static checkGPUAcceleration(element) {
        const computed = getComputedStyle(element);
        const transform = computed.transform;
        const willChange = computed.willChange;

        return {
            hasTransform: transform !== 'none',
            willChange: willChange,
            likely3DAccelerated: transform.includes('matrix3d') || willChange.includes('transform')
        };
    }
}

// 使用
console.table(AnimationDebugger.listActiveAnimations());
```

### 完整迁移对比

三周结束后, 你整理了完整的对比数据:

```
完整迁移对比 (80+ 个动画):

代码量:
- 迁移前 JavaScript: 2847 行
- 迁移后 CSS: 456 行 (84% 减少)
- 迁移后 JavaScript: 183 行 (仅控制逻辑)

性能指标:
                    迁移前      迁移后      提升
主线程占用          89%         6%         93%
FPS (移动端)        42          59         40%
首屏渲染时间        2.8s        1.2s       57%
内存占用            142MB       89MB       37%
GPU 内存            38MB        95MB       -150%*

* GPU 内存增加是正常的, 因为动画被移到了合成层

开发效率:
- 新动画开发时间: 从 2 小时 → 20 分钟
- 动画调试时间: 从 1 小时 → 5 分钟
- 跨浏览器兼容性: 从 3 天测试 → 自动兼容

用户体验:
- 移动端流畅度: 从 "一顿一顿" → "丝般顺滑"
- 用户投诉: 从每周 20+ 条 → 0 条
- 页面互动满意度: 从 67% → 94%
```

### 迁移决策指南

你为团队写了一份决策指南:

```markdown
# CSS 动画 vs JavaScript 动画 - 决策指南

## 何时使用 CSS 动画

✅ **推荐使用 CSS 动画的场景**:
1. 简单的状态切换 (hover, active, focus)
2. UI 反馈动画 (按钮点击, 加载指示器)
3. 页面进入/离开动画
4. 循环动画 (脉冲, 旋转, 呼吸灯)
5. 基于媒体查询的响应式动画
6. 性能敏感的移动端动画

**优势**:
- 🚀 GPU 加速, 性能更好
- 🎯 不阻塞主线程
- 📱 移动端更流畅
- 🔧 浏览器自动优化
- 📝 代码更简洁
- 🐛 更易调试 (DevTools 支持完善)

**限制**:
- ❌ 无法动态计算目标值
- ❌ 难以实现复杂交互逻辑
- ❌ 无法中途修改动画参数
- ❌ 不支持物理模拟

## 何时使用 JavaScript 动画

✅ **推荐使用 JavaScript 动画的场景**:
1. 需要动态计算动画目标
2. 复杂的交互逻辑 (拖拽, 滚动联动)
3. 物理模拟 (弹簧, 惯性)
4. 游戏动画
5. Canvas/WebGL 动画
6. 需要精确控制进度的场景

**优势**:
- 🎮 完全控制动画逻辑
- 🧮 动态计算能力
- 🔄 中途修改参数
- 📊 精确的进度反馈
- 🎯 复杂交互支持

**限制**:
- ❌ 占用主线程
- ❌ 移动端性能较差
- ❌ 代码复杂度高
- ❌ 需要处理 requestAnimationFrame

## 混合方案

✅ **最佳实践: CSS + JavaScript 配合**

```javascript
// CSS 负责动画本身
// JavaScript 负责控制逻辑

class HybridAnimator {
    constructor(element) {
        this.element = element;
    }

    // 动态选择动画
    async playDynamic(type) {
        const animations = {
            fast: 'animate-fadeIn-fast',
            normal: 'animate-fadeIn',
            slow: 'animate-fadeIn-slow'
        };

        const animationClass = animations[type];
        this.element.classList.add(animationClass);

        await this.waitForAnimation();

        this.element.classList.remove(animationClass);
    }

    // 条件动画
    async conditionalAnimation(condition) {
        if (condition) {
            this.element.classList.add('animate-success');
        } else {
            this.element.classList.add('animate-error');
        }

        await this.waitForAnimation();
    }

    // 等待 CSS 动画完成
    waitForAnimation() {
        return new Promise(resolve => {
            const handler = (e) => {
                if (e.target === this.element) {
                    this.element.removeEventListener('animationend', handler);
                    resolve();
                }
            };
            this.element.addEventListener('animationend', handler);
        });
    }
}
```

## 性能检查清单

迁移或创建动画前, 检查以下项目:

- [ ] 是否可以用 transform/opacity 实现?
- [ ] 是否避免了 width/height/top/left 动画?
- [ ] 是否添加了 will-change 提示?
- [ ] 是否在动画结束后清理 will-change?
- [ ] 是否使用了合理的 animation-duration?
- [ ] 是否考虑了移动端性能?
- [ ] 是否使用了浏览器前缀 (如需兼容旧版)?
- [ ] 是否在 DevTools 中验证了性能?
```

---

## 迁移总结与经验沉淀

三周的迁移工作结束后, 你在团队分享会上做了总结。

"这次迁移最大的收获不是性能提升, " 你说, "而是我们建立了一套可维护的动画系统。"

你展示了最终的项目结构:

```
animations/
├── keyframes.css          # 所有 @keyframes 定义
├── utilities.css          # 工具类 (animate-*)
├── performance.css        # 性能优化类
├── debug.css              # 调试工具类
├── animator.js            # JavaScript 控制工具
└── README.md              # 使用文档

核心设计原则:
1. CSS 负责动画本身 (what)
2. JavaScript 负责控制逻辑 (when & how)
3. 优先使用 transform 和 opacity
4. 合理使用 will-change
5. 提供调试工具
6. 建立性能检查清单
```

你在文档中写下了关键经验:

```
渐进式迁移的关键:

1. 分阶段迁移:
   - 第一周: 简单动画 + 工具建设
   - 第二周: 复杂动画 + 组合效果
   - 第三周: 性能优化 + 规范建立

2. 保持向后兼容:
   - 旧代码逐步废弃, 不强制删除
   - 提供迁移指南和工具
   - 新老代码可以共存

3. 持续监控:
   - 每个阶段都验证性能
   - 收集用户反馈
   - 及时调整策略

4. 知识传递:
   - 编写详细文档
   - 团队培训分享
   - 建立最佳实践

最重要的经验:
不要试图一次性重写所有代码,
而是建立新的系统, 然后逐步迁移。
```

你看着监控面板上的性能曲线, 三周来 FPS 从 42 稳定提升到了 59, 主线程占用从 89% 降到了 6%。

更重要的是, 团队现在有了一套清晰的动画开发流程, 新来的前端开发者也能快速上手。

"技术债务不是一天积累的, " 你在笔记中写道, "也不应该试图一天还清。渐进式迁移让我们在保持业务稳定的同时, 完成了技术升级。"

---

## 知识档案: CSS 动画系统的八个核心机制

**规则 1: @keyframes 定义动画序列, animation 属性应用动画**

CSS 动画系统分为定义和应用两部分, @keyframes 定义动画的关键帧序列, animation 属性将其应用到元素上。

```css
/* 定义: @keyframes 描述动画序列 */
@keyframes fadeIn {
    from {  /* 或 0% */
        opacity: 0;
    }
    to {    /* 或 100% */
        opacity: 1;
    }
}

/* 或使用百分比定义多个关键帧 */
@keyframes complexAnimation {
    0% {
        transform: translateX(0) scale(1);
    }
    50% {
        transform: translateX(100px) scale(1.2);
    }
    100% {
        transform: translateX(200px) scale(1);
    }
}

/* 应用: animation 属性绑定动画 */
.element {
    animation-name: fadeIn;                    /* 动画名称 */
    animation-duration: 1s;                    /* 持续时间 */
    animation-timing-function: ease-in-out;    /* 缓动函数 */
    animation-delay: 0.5s;                     /* 延迟时间 */
    animation-iteration-count: infinite;       /* 循环次数 */
    animation-direction: alternate;            /* 播放方向 */
    animation-fill-mode: both;                 /* 填充模式 */
    animation-play-state: running;             /* 播放状态 */
}

/* 简写形式 */
.element {
    animation: fadeIn 1s ease-in-out 0.5s infinite alternate both;
    /*         名称   时长  缓动     延迟  次数    方向     填充 */
}
```

关键帧定义规则:
- **from/to**: 等价于 0% 和 100%, 适合简单动画
- **百分比**: 精确控制动画进度, 支持任意数量关键帧
- **多属性**: 每个关键帧可包含多个 CSS 属性
- **timing-function**: 可在每个关键帧单独设置缓动

---

**规则 2: animation 8 个子属性控制动画的完整行为**

animation 简写属性包含 8 个子属性, 每个控制动画的不同方面。

```css
/* 1. animation-name: 动画名称 */
.element {
    animation-name: fadeIn;           /* 单个动画 */
    animation-name: fadeIn, slideIn;  /* 多个动画 */
    animation-name: none;             /* 禁用动画 */
}

/* 2. animation-duration: 持续时间 */
.element {
    animation-duration: 1s;           /* 秒 */
    animation-duration: 500ms;        /* 毫秒 */
    animation-duration: 1s, 2s;       /* 多个动画不同时长 */
}

/* 3. animation-timing-function: 缓动函数 */
.element {
    animation-timing-function: linear;                      /* 匀速 */
    animation-timing-function: ease;                        /* 默认, 慢-快-慢 */
    animation-timing-function: ease-in;                     /* 慢速开始 */
    animation-timing-function: ease-out;                    /* 慢速结束 */
    animation-timing-function: ease-in-out;                 /* 慢-快-慢 */
    animation-timing-function: cubic-bezier(0.4, 0, 0.2, 1); /* 自定义贝塞尔 */
    animation-timing-function: steps(4, end);               /* 分步动画 */
}

/* 4. animation-delay: 延迟启动 */
.element {
    animation-delay: 0.5s;            /* 延迟 0.5 秒 */
    animation-delay: -0.5s;           /* 负延迟, 从中间开始 */
}

/* 5. animation-iteration-count: 循环次数 */
.element {
    animation-iteration-count: 1;     /* 播放一次 (默认) */
    animation-iteration-count: 3;     /* 播放三次 */
    animation-iteration-count: infinite; /* 无限循环 */
    animation-iteration-count: 2.5;   /* 播放 2.5 次 */
}

/* 6. animation-direction: 播放方向 */
.element {
    animation-direction: normal;      /* 正常播放 (默认) */
    animation-direction: reverse;     /* 反向播放 */
    animation-direction: alternate;   /* 正向-反向交替 */
    animation-direction: alternate-reverse; /* 反向-正向交替 */
}

/* 7. animation-fill-mode: 填充模式 */
.element {
    animation-fill-mode: none;        /* 默认, 动画外不应用样式 */
    animation-fill-mode: forwards;    /* 保持结束状态 */
    animation-fill-mode: backwards;   /* 应用开始状态 (delay 期间) */
    animation-fill-mode: both;        /* forwards + backwards */
}

/* 8. animation-play-state: 播放状态 */
.element {
    animation-play-state: running;    /* 播放中 (默认) */
    animation-play-state: paused;     /* 暂停 */
}
```

fill-mode 详解:
- **none**: 动画前后不应用任何样式
- **forwards**: 动画结束后保持最后一帧状态
- **backwards**: delay 期间应用第一帧状态
- **both**: 结合 forwards 和 backwards

---

**规则 3: 多动画可以并行执行, 用逗号分隔**

一个元素可以同时运行多个独立的动画, 每个动画控制不同的属性。

```css
/* 同时运行多个动画 */
.element {
    animation:
        fadeIn 1s ease-out,           /* 淡入 */
        slideUp 1s ease-out,          /* 上移 */
        rotate 2s linear infinite;    /* 持续旋转 */
}

/* 分别定义每个动画 */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideUp {
    from { transform: translateY(50px); }
    to { transform: translateY(0); }
}

@keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

/* 多动画的复杂组合 */
.complex {
    animation:
        enter 0.5s ease-out both,           /* 进入动画 */
        emphasize 0.3s ease-in-out 0.5s,    /* 0.5s 后强调 */
        pulse 2s ease-in-out 0.8s infinite; /* 0.8s 后持续脉冲 */
}
```

多动画注意事项:
- **属性冲突**: 多个动画不应修改相同属性, 否则后者覆盖前者
- **独立控制**: 每个动画可以有不同的 duration, delay, iteration-count
- **时序编排**: 通过 delay 控制动画启动顺序
- **性能考虑**: 过多动画会影响性能, 建议不超过 3-5 个并行动画

---

**规则 4: transform 和 opacity 是 GPU 加速的首选属性**

只有特定 CSS 属性能享受 GPU 加速, transform 和 opacity 性能最佳。

```css
/* ✅ GPU 加速属性 (推荐在动画中使用) */

/* transform 的子属性 */
.gpu-transform {
    animation: transformAnimation 1s;
}

@keyframes transformAnimation {
    from {
        transform: translateX(0) translateY(0);     /* 平移 */
        transform: scale(1);                        /* 缩放 */
        transform: rotate(0deg);                    /* 旋转 */
        transform: skew(0deg);                      /* 倾斜 */
        transform: translate3d(0, 0, 0);            /* 3D 平移 */
        transform: perspective(1000px) rotateY(0);  /* 3D 透视 */
    }
    to {
        transform: translateX(100px) translateY(50px);
        transform: scale(1.5);
        transform: rotate(360deg);
        transform: skew(20deg);
    }
}

/* opacity */
.gpu-opacity {
    animation: fadeAnimation 1s;
}

@keyframes fadeAnimation {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* ❌ 非 GPU 加速属性 (避免在动画中使用) */

/* 触发重排 (reflow) 的属性 */
@keyframes badLayout {
    from {
        width: 100px;        /* ❌ 触发重排 */
        height: 100px;       /* ❌ 触发重排 */
        top: 0;              /* ❌ 触发重排 */
        left: 0;             /* ❌ 触发重排 */
        margin: 0;           /* ❌ 触发重排 */
        padding: 0;          /* ❌ 触发重排 */
    }
    to {
        width: 200px;
        height: 200px;
    }
}

/* 触发重绘 (repaint) 的属性 */
@keyframes badPaint {
    from {
        color: red;          /* ❌ 触发重绘 */
        background: blue;    /* ❌ 触发重绘 */
        border-color: green; /* ❌ 触发重绘 */
        box-shadow: none;    /* ❌ 触发重绘 */
    }
    to {
        color: yellow;
        background: purple;
    }
}
```

GPU 加速优化技巧:
- **强制 GPU 加速**: 使用 `transform: translateZ(0)` 或 `transform: translate3d(0, 0, 0)`
- **will-change 提示**: 提前告知浏览器哪些属性将要动画
- **避免混合**: 不要在同一动画中混用 GPU 和非 GPU 属性

```css
/* 提前创建合成层 */
.will-animate {
    will-change: transform, opacity;
}

/* 动画结束后清理 will-change */
.animation-done {
    will-change: auto;
}
```

---

**规则 5: animation-fill-mode 控制动画前后的样式状态**

fill-mode 决定动画开始前 (delay 期间) 和结束后元素的样式。

```css
/* fill-mode 四种模式对比 */

/* none: 默认, 动画外不应用样式 */
.fill-none {
    opacity: 1;  /* 初始样式 */
    animation: fadeOut 1s none;
}

@keyframes fadeOut {
    from { opacity: 1; }
    to { opacity: 0; }
}

/* 行为:
   - 动画前: opacity: 1 (初始样式)
   - 动画中: opacity 从 1 → 0
   - 动画后: opacity: 1 (恢复初始样式) */

/* forwards: 保持结束状态 */
.fill-forwards {
    opacity: 1;
    animation: fadeOut 1s forwards;
}

/* 行为:
   - 动画前: opacity: 1 (初始样式)
   - 动画中: opacity 从 1 → 0
   - 动画后: opacity: 0 (保持结束状态) ✅ */

/* backwards: 应用开始状态 (delay 期间) */
.fill-backwards {
    opacity: 1;
    animation: fadeIn 1s 2s backwards;  /* 2s 延迟 */
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* 行为:
   - 动画前 (delay 期间): opacity: 0 (应用开始状态) ✅
   - 动画中: opacity 从 0 → 1
   - 动画后: opacity: 1 (恢复初始样式) */

/* both: forwards + backwards */
.fill-both {
    opacity: 1;
    animation: fadeInOut 1s 2s both;
}

@keyframes fadeInOut {
    0% { opacity: 0; }
    50% { opacity: 1; }
    100% { opacity: 0; }
}

/* 行为:
   - 动画前 (delay 期间): opacity: 0 (应用开始状态) ✅
   - 动画中: opacity 0 → 1 → 0
   - 动画后: opacity: 0 (保持结束状态) ✅ */
```

实际应用场景:
- **进入动画**: 使用 `both`, 确保元素一开始就隐藏, 结束后保持显示
- **加载指示器**: 使用 `none`, 动画循环时不保持状态
- **页面转场**: 使用 `forwards`, 保持转场后的状态

---

**规则 6: animation-direction 控制动画播放方向和交替模式**

direction 决定动画是正向播放、反向播放还是交替播放。

```css
/* normal: 正向播放 (默认) */
.direction-normal {
    animation: slide 2s normal;
}

@keyframes slide {
    from { transform: translateX(0); }
    to { transform: translateX(100px); }
}

/* 播放顺序: 0 → 100px */

/* reverse: 反向播放 */
.direction-reverse {
    animation: slide 2s reverse;
}

/* 播放顺序: 100px → 0 (反向) */

/* alternate: 正向-反向交替 */
.direction-alternate {
    animation: slide 2s alternate infinite;
}

/* 播放顺序:
   第 1 次: 0 → 100px (正向)
   第 2 次: 100px → 0 (反向)
   第 3 次: 0 → 100px (正向)
   第 4 次: 100px → 0 (反向)
   ... */

/* alternate-reverse: 反向-正向交替 */
.direction-alternate-reverse {
    animation: slide 2s alternate-reverse infinite;
}

/* 播放顺序:
   第 1 次: 100px → 0 (反向)
   第 2 次: 0 → 100px (正向)
   第 3 次: 100px → 0 (反向)
   ... */
```

与 iteration-count 的结合:
```css
/* alternate + iteration-count */
.bounce {
    animation: bounce 0.5s ease-in-out alternate 6;
}

@keyframes bounce {
    from { transform: translateY(0); }
    to { transform: translateY(-50px); }
}

/* 播放顺序:
   1: 上升 (0 → -50px)
   2: 下降 (-50px → 0)
   3: 上升 (0 → -50px)
   4: 下降 (-50px → 0)
   5: 上升 (0 → -50px)
   6: 下降 (-50px → 0)
   总共播放 6 次, 形成 3 次完整的弹跳 */
```

---

**规则 7: animation 事件提供动画生命周期的 JavaScript 钩子**

CSS 动画触发三种事件: animationstart, animationiteration, animationend。

```javascript
/* 三种动画事件 */

const element = document.querySelector('.animated');

// 1. animationstart: 动画开始时触发
element.addEventListener('animationstart', (e) => {
    console.log('动画开始:');
    console.log('- 动画名称:', e.animationName);
    console.log('- 已用时间:', e.elapsedTime);  // 通常为 0

    // 实际用途: 禁用按钮, 显示加载提示
    element.setAttribute('disabled', true);
});

// 2. animationiteration: 每次循环完成时触发 (不包括最后一次)
element.addEventListener('animationiteration', (e) => {
    console.log('动画循环:');
    console.log('- 循环次数:', Math.floor(e.elapsedTime / animationDuration));
    console.log('- 已用时间:', e.elapsedTime);

    // 实际用途: 更新循环计数, 检查停止条件
    if (shouldStop(e.elapsedTime)) {
        element.style.animationPlayState = 'paused';
    }
});

// 3. animationend: 动画结束时触发
element.addEventListener('animationend', (e) => {
    console.log('动画结束:');
    console.log('- 动画名称:', e.animationName);
    console.log('- 总用时:', e.elapsedTime);

    // 实际用途: 清理动画类, 启用按钮, 触发后续动作
    element.classList.remove('animate-fadeIn');
    element.removeAttribute('disabled');
});
```

事件对象属性:
```javascript
element.addEventListener('animationend', (e) => {
    // AnimationEvent 特有属性
    e.animationName;    // 动画名称 (字符串)
    e.elapsedTime;      // 已用时间 (秒, 浮点数)
    e.pseudoElement;    // 伪元素名称 (如 "::before")

    // 继承自 Event 的属性
    e.target;           // 触发事件的元素
    e.currentTarget;    // 监听器绑定的元素
    e.bubbles;          // true, 事件冒泡
    e.cancelable;       // false, 不可取消
});
```

实际应用模式:
```javascript
// 序列动画: 一个动画结束后启动下一个
class AnimationSequence {
    constructor(element) {
        this.element = element;
        this.queue = [];
        this.running = false;
    }

    add(animationClass) {
        this.queue.push(animationClass);
        if (!this.running) {
            this.next();
        }
        return this;
    }

    next() {
        if (this.queue.length === 0) {
            this.running = false;
            return;
        }

        this.running = true;
        const animationClass = this.queue.shift();

        // 清理旧动画
        this.element.className = this.element.className.replace(/animate-\S+/g, '');

        // 添加新动画
        this.element.classList.add(animationClass);

        // 等待动画结束
        const handler = (e) => {
            if (e.target === this.element) {
                this.element.removeEventListener('animationend', handler);
                this.next();  // 播放下一个
            }
        };

        this.element.addEventListener('animationend', handler);
    }
}

// 使用
const sequence = new AnimationSequence(element);
sequence
    .add('animate-fadeIn')
    .add('animate-shake')
    .add('animate-pulse');
```

---

**规则 8: CSS 动画性能优于 JavaScript, 但灵活性较低, 需根据场景选择**

CSS 动画和 JavaScript 动画各有优劣, 选择取决于具体需求。

```
CSS 动画 vs JavaScript 动画:

性能对比:
                    CSS Animation       JavaScript (RAF)
主线程占用          极低 (~5%)         中高 (30-50%)
GPU 加速            自动               需手动优化
移动端流畅度        优秀 (58-60 FPS)   一般 (40-50 FPS)
浏览器优化          完全自动           需手动实现
代码复杂度          低                 高

功能对比:
                    CSS Animation       JavaScript (RAF)
动态目标值          ❌ 不支持           ✅ 完全支持
中途修改参数        ❌ 困难             ✅ 容易
精确进度控制        ❌ 有限             ✅ 完全控制
复杂交互逻辑        ❌ 不支持           ✅ 完全支持
物理模拟            ❌ 不支持           ✅ 支持
跨属性同步          ❌ 困难             ✅ 容易
```

选择决策树:
```javascript
function chooseAnimationMethod(requirements) {
    const {
        needsDynamicTarget,      // 需要动态计算目标
        needsComplexInteraction, // 需要复杂交互
        needsPhysicsSimulation,  // 需要物理模拟
        isMobileCritical,        // 移动端性能关键
        isSimpleStateChange,     // 简单状态切换
        needsPreciseControl      // 需要精确控制
    } = requirements;

    // JavaScript 动画的场景
    if (
        needsDynamicTarget ||
        needsComplexInteraction ||
        needsPhysicsSimulation ||
        needsPreciseControl
    ) {
        return 'JavaScript Animation';
    }

    // CSS 动画的场景
    if (
        isSimpleStateChange ||
        isMobileCritical
    ) {
        return 'CSS Animation';
    }

    // 混合方案
    return 'Hybrid (CSS + JavaScript)';
}

// 示例判断
chooseAnimationMethod({
    isSimpleStateChange: true,
    isMobileCritical: true
});
// → "CSS Animation"

chooseAnimationMethod({
    needsDynamicTarget: true,
    needsComplexInteraction: true
});
// → "JavaScript Animation"
```

混合方案最佳实践:
```javascript
// CSS 负责动画本身, JavaScript 负责控制
class HybridAnimator {
    constructor(element) {
        this.element = element;
    }

    // 动态选择 CSS 动画
    async play(animationType) {
        const animations = {
            'quick': 'animate-fadeIn-fast',
            'normal': 'animate-fadeIn',
            'slow': 'animate-fadeIn-slow'
        };

        const animationClass = animations[animationType];
        this.element.classList.add(animationClass);

        await this.waitForEnd();

        this.element.classList.remove(animationClass);
    }

    // JavaScript 控制复杂逻辑
    async complexSequence(data) {
        // 根据数据动态决定动画
        if (data.isSuccess) {
            await this.play('quick');
            this.element.classList.add('state-success');
        } else {
            await this.play('slow');
            this.element.classList.add('state-error');
        }
    }

    waitForEnd() {
        return new Promise(resolve => {
            const handler = (e) => {
                if (e.target === this.element) {
                    this.element.removeEventListener('animationend', handler);
                    resolve();
                }
            };
            this.element.addEventListener('animationend', handler);
        });
    }
}
```

性能优化检查清单:
```
CSS 动画性能清单:

✅ 必须做:
- [ ] 使用 transform 和 opacity (避免 width/height/top/left)
- [ ] 为动画元素添加 will-change
- [ ] 动画结束后移除 will-change (避免内存浪费)
- [ ] 使用 transform: translateZ(0) 强制 GPU 加速
- [ ] 限制同时运行的动画数量 (<10 个)

⚠️ 避免:
- [ ] 不要动画 box-shadow (改用伪元素 + opacity)
- [ ] 不要动画 border (改用 transform: scale)
- [ ] 不要动画 background-position (改用 transform)
- [ ] 不要在动画中使用 calc()
- [ ] 不要过度使用 will-change (最多 2-3 个属性)

🔧 调试工具:
- [ ] Chrome DevTools → Performance 录制
- [ ] 检查 Animation 轨道的 FPS
- [ ] 启用 Rendering → Layer borders 查看合成层
- [ ] 使用 Coverage 检查未使用的 will-change
```

---

**事故档案编号**: NETWORK-2024-1960
**影响范围**: CSS 动画系统、@keyframes、animation 属性、性能优化、渐进式迁移
**根本原因**: 遗留项目使用大量 JavaScript 动画导致移动端性能问题, 主线程占用过高, 缺少 GPU 加速优化
**学习成本**: 中 (需理解 @keyframes 定义、animation 8 个子属性、GPU 加速原理、渐进式迁移策略)

这是 JavaScript 世界第 160 次被记录的网络与数据事故。CSS 动画系统通过 @keyframes 定义动画序列, animation 属性应用动画到元素。animation 包含 8 个子属性: name, duration, timing-function, delay, iteration-count, direction, fill-mode, play-state, 每个控制动画的不同方面。多个动画可以并行执行, 用逗号分隔, 但需避免属性冲突。transform 和 opacity 是 GPU 加速的首选属性, 避免动画 width/height/top/left 等触发重排的属性。animation-fill-mode 控制动画前后的样式状态, forwards 保持结束状态, backwards 应用开始状态, both 结合两者。animation-direction 控制播放方向, alternate 实现正向-反向交替。CSS 动画触发 animationstart/animationiteration/animationend 事件, 提供 JavaScript 钩子。CSS 动画性能优于 JavaScript 但灵活性较低, 应根据场景选择: 简单状态切换和移动端性能关键用 CSS, 动态目标和复杂交互用 JavaScript, 或采用混合方案。渐进式迁移策略分阶段进行: 第一周基础迁移和工具建设, 第二周复杂动画和组合效果, 第三周性能优化和规范建立, 在保持业务稳定的同时完成技术升级。

---

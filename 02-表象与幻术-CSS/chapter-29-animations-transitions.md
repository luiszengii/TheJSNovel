《第29次记录:动画系统事故 —— 时间轴的掌控之术》

---

## 事故现场

周三上午十点,你正在优化网站的交互体验。办公室里放着轻音乐,气氛还不错。

你想给按钮添加一个悬停效果,鼠标移上去时背景色变化。你直接改变background:

```css
.button {
    background: blue;
}

.button:hover {
    background: green;
}
```

效果生硬,瞬间变色。你想添加平滑过渡,尝试`transition`:

```css
.button {
    background: blue;
    transition: background 0.3s;
}

.button:hover {
    background: green;
}
```

现在平滑了!但你想做一个循环的loading动画,发现`transition`只能从A状态到B状态,无法循环。

你改用`animation`:

```css
@keyframes loading {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.spinner {
    animation: loading 1s linear infinite;
}
```

loading动画成功了,但你发现动画结束后元素突然跳回原位。你尝试`animation-fill-mode`:

```css
.element {
    animation: slideIn 1s forwards;  /* 保持结束状态 */
}
```

现在不跳回了,但你想让动画延迟2秒开始,设置了`animation-delay`:

```css
.element {
    animation: slideIn 1s 2s forwards;
}
```

结果元素在2秒延迟期间完全消失了。

"animation和transition的区别是什么?什么时候用哪个?"

---

## 深入迷雾

上午十一点,UI设计师小美发来消息:"动画能不能做得更流畅一些?感觉有点生硬。"你点点头,决定系统学习CSS动画。

你开始系统学习CSS动画。首先理解`transition`的四个属性:

```css
/* transition: property duration timing-function delay */

.element {
    transition-property: background;      /* 要过渡的属性 */
    transition-duration: 0.3s;            /* 持续时间 */
    transition-timing-function: ease;     /* 缓动函数 */
    transition-delay: 0s;                 /* 延迟时间 */

    /* 简写 */
    transition: background 0.3s ease 0s;
}

/* 多个属性过渡 */
.element {
    transition: background 0.3s, transform 0.5s, opacity 0.2s;
}

/* 所有属性过渡 */
.element {
    transition: all 0.3s;
}
```

你测试了不同的缓动函数:

```css
/* 预定义缓动 */
transition-timing-function: linear;        /* 匀速 */
transition-timing-function: ease;          /* 慢-快-慢(默认) */
transition-timing-function: ease-in;       /* 慢-快 */
transition-timing-function: ease-out;      /* 快-慢 */
transition-timing-function: ease-in-out;   /* 慢-快-慢(比ease更明显) */

/* 自定义贝塞尔曲线 */
transition-timing-function: cubic-bezier(0.42, 0, 0.58, 1);

/* 步进函数 */
transition-timing-function: steps(4, end);  /* 4步,结束时跳变 */
```

你学习了`animation`的八个属性:

```css
@keyframes slidein {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(0); }
}

.element {
    animation-name: slidein;              /* 动画名称 */
    animation-duration: 1s;               /* 持续时间 */
    animation-timing-function: ease;      /* 缓动函数 */
    animation-delay: 0s;                  /* 延迟 */
    animation-iteration-count: 1;         /* 播放次数 */
    animation-direction: normal;          /* 播放方向 */
    animation-fill-mode: none;            /* 填充模式 */
    animation-play-state: running;        /* 播放状态 */

    /* 简写 */
    animation: slidein 1s ease 0s 1 normal none running;
}
```

你测试了`animation-fill-mode`的四个值:

```css
/* none (默认): 不保留状态 */
animation-fill-mode: none;
/* 动画开始前: 元素初始状态 */
/* 动画进行中: 动画状态 */
/* 动画结束后: 元素初始状态 */

/* forwards: 保持结束状态 */
animation-fill-mode: forwards;
/* 动画结束后: 保持100%关键帧状态 */

/* backwards: 应用开始状态 */
animation-fill-mode: backwards;
/* 延迟期间: 应用0%关键帧状态 */

/* both: forwards + backwards */
animation-fill-mode: both;
```

你发现关键帧可以使用百分比或from/to:

```css
/* 百分比语法 */
@keyframes slide {
    0% { transform: translateX(0); }
    50% { transform: translateX(100px); opacity: 0.5; }
    100% { transform: translateX(200px); }
}

/* from/to语法 */
@keyframes fade {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* 多个关键帧共享样式 */
@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-20px); }
}
```

---

## 真相浮现

中午十二点,你完成了所有动画优化,使用合适的缓动函数让交互更自然。小美看了新版本后说:"完美!这才是我想要的感觉。"

你整理了transition和animation的完整规则:

**规则1:Transition vs Animation**

```css
/* Transition: 简单过渡 */
.element {
    transition: transform 0.3s;
}
.element:hover {
    transform: scale(1.1);
}

/* 特点 */
✅ 需要触发(hover, class变化)
✅ 只有开始和结束两个状态
✅ 自动反向过渡
❌ 无法循环
❌ 无法在中间暂停

/* Animation: 复杂动画 */
@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}
.element {
    animation: pulse 1s infinite;
}

/* 特点 */
✅ 自动播放
✅ 可定义多个关键帧
✅ 可循环、反向、暂停
✅ 可在中间插入状态
✅ 更精细的控制
```

你创建了完整测试:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSS动画测试</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            padding: 50px;
            font-family: Arial, sans-serif;
        }

        .demo {
            margin-bottom: 80px;
        }

        .box {
            width: 100px;
            height: 100px;
            background: lightblue;
            border: 2px solid #0066cc;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin: 20px;
            font-size: 12px;
            text-align: center;
        }

        /* 测试1: Transition基础 */
        .transition-basic {
            transition: background 0.3s, transform 0.3s;
        }

        .transition-basic:hover {
            background: lightcoral;
            transform: scale(1.2);
        }

        /* 测试2: 不同缓动函数 */
        .ease { transition: transform 1s ease; }
        .linear { transition: transform 1s linear; }
        .ease-in { transition: transform 1s ease-in; }
        .ease-out { transition: transform 1s ease-out; }
        .ease-in-out { transition: transform 1s ease-in-out; }

        .ease:hover, .linear:hover, .ease-in:hover,
        .ease-out:hover, .ease-in-out:hover {
            transform: translateX(200px);
        }

        /* 测试3: Animation循环 */
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .spinner {
            animation: rotate 2s linear infinite;
        }

        /* 测试4: 复杂关键帧 */
        @keyframes bounce {
            0%, 100% {
                transform: translateY(0);
            }
            25% {
                transform: translateY(-30px);
            }
            50% {
                transform: translateY(0);
            }
            75% {
                transform: translateY(-15px);
            }
        }

        .bounce {
            animation: bounce 2s ease infinite;
        }

        /* 测试5: Fill Mode */
        @keyframes slideIn {
            from {
                transform: translateX(-100px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        .fill-none {
            animation: slideIn 1s 1s none;
            background: lightcoral;
        }

        .fill-backwards {
            animation: slideIn 1s 1s backwards;
            background: lightgreen;
        }

        .fill-forwards {
            animation: slideIn 1s 1s forwards;
            background: lightyellow;
        }

        .fill-both {
            animation: slideIn 1s 1s both;
            background: lightpink;
        }

        /* 测试6: 动画控制 */
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.2); }
        }

        .paused {
            animation: pulse 1s ease infinite;
            animation-play-state: paused;
        }

        .paused:hover {
            animation-play-state: running;
        }

        /* 测试7: 步进动画 */
        @keyframes stepAnimation {
            from { transform: translateX(0); }
            to { transform: translateX(200px); }
        }

        .steps {
            animation: stepAnimation 2s steps(4, end) infinite;
        }

        /* 测试8: 多动画组合 */
        @keyframes colorChange {
            0% { background: lightblue; }
            33% { background: lightgreen; }
            66% { background: lightyellow; }
            100% { background: lightcoral; }
        }

        @keyframes moveAndRotate {
            from {
                transform: translateX(0) rotate(0deg);
            }
            to {
                transform: translateX(200px) rotate(360deg);
            }
        }

        .multi-animation {
            animation:
                colorChange 3s ease infinite,
                moveAndRotate 3s ease infinite;
        }

        code {
            background: #f5f5f5;
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <h1>CSS动画完整测试</h1>

    <div class="demo">
        <h3>测试1: Transition (悬停触发)</h3>
        <code>transition: background 0.3s, transform 0.3s;</code>
        <div class="box transition-basic">Hover Me</div>
    </div>

    <div class="demo">
        <h3>测试2: 缓动函数对比 (悬停触发)</h3>
        <div class="box ease">ease</div>
        <div class="box linear">linear</div>
        <div class="box ease-in">ease-in</div>
        <div class="box ease-out">ease-out</div>
        <div class="box ease-in-out">ease-in-out</div>
    </div>

    <div class="demo">
        <h3>测试3: 循环旋转动画</h3>
        <code>animation: rotate 2s linear infinite;</code>
        <div class="box spinner">Spin</div>
    </div>

    <div class="demo">
        <h3>测试4: 弹跳动画</h3>
        <code>多关键帧动画</code>
        <div class="box bounce">Bounce</div>
    </div>

    <div class="demo">
        <h3>测试5: Fill Mode (1秒延迟)</h3>
        <div class="box fill-none">none</div>
        <div class="box fill-backwards">backwards</div>
        <div class="box fill-forwards">forwards</div>
        <div class="box fill-both">both</div>
    </div>

    <div class="demo">
        <h3>测试6: 动画控制 (悬停播放)</h3>
        <code>animation-play-state: paused → running</code>
        <div class="box paused">Paused<br>Hover Play</div>
    </div>

    <div class="demo">
        <h3>测试7: 步进动画</h3>
        <code>steps(4, end)</code>
        <div class="box steps">Steps</div>
    </div>

    <div class="demo">
        <h3>测试8: 多动画组合</h3>
        <code>颜色变化 + 移动旋转</code>
        <div class="box multi-animation">Multi</div>
    </div>

    <script>
        // 检测动画状态
        function checkAnimation(selector) {
            const el = document.querySelector(selector);
            if (!el) return;

            const computed = getComputedStyle(el);
            console.log(`${selector}:`);
            console.log('  animation:', computed.animation);
            console.log('  animation-name:', computed.animationName);
            console.log('  animation-duration:', computed.animationDuration);
            console.log('  animation-timing-function:', computed.animationTimingFunction);
        }

        checkAnimation('.spinner');
        checkAnimation('.bounce');

        // 监听动画事件
        const spinner = document.querySelector('.spinner');
        spinner.addEventListener('animationstart', () => {
            console.log('动画开始');
        });
        spinner.addEventListener('animationiteration', () => {
            console.log('动画迭代');
        });
        spinner.addEventListener('animationend', () => {
            console.log('动画结束');
        });
    </script>
</body>
</html>
```

---

## 世界法则

**世界规则 1:Transition的四个属性**

```css
/* transition: property duration timing-function delay */

.element {
    /* 完整写法 */
    transition-property: transform;       /* 要过渡的属性 */
    transition-duration: 0.3s;            /* 持续时间 */
    transition-timing-function: ease;     /* 缓动函数 */
    transition-delay: 0s;                 /* 延迟时间 */

    /* 简写 */
    transition: transform 0.3s ease 0s;

    /* 多个属性 */
    transition:
        transform 0.3s ease,
        opacity 0.5s linear,
        background 0.2s;

    /* 所有属性(慎用) */
    transition: all 0.3s;
}
```

**可过渡的属性**: 数值、颜色、transform、opacity等。不能过渡display, visibility等离散属性。

---

**世界规则 2:Animation的八个属性**

```css
@keyframes myAnimation {
    /* 关键帧定义 */
}

.element {
    animation-name: myAnimation;          /* 动画名称 */
    animation-duration: 1s;               /* 持续时间 */
    animation-timing-function: ease;      /* 缓动函数 */
    animation-delay: 0s;                  /* 延迟 */
    animation-iteration-count: infinite;  /* 播放次数:数字或infinite */
    animation-direction: normal;          /* 播放方向 */
    animation-fill-mode: none;            /* 填充模式 */
    animation-play-state: running;        /* 播放状态:running或paused */

    /* 简写: name duration timing-function delay iteration-count direction fill-mode */
    animation: myAnimation 1s ease 0s infinite normal none;
}
```

---

**世界规则 3:Animation Direction (播放方向)**

```css
/* normal: 正向播放(默认) */
animation-direction: normal;
/* 0% → 100% */

/* reverse: 反向播放 */
animation-direction: reverse;
/* 100% → 0% */

/* alternate: 交替播放 */
animation-direction: alternate;
/* 第1次: 0% → 100% */
/* 第2次: 100% → 0% */
/* 第3次: 0% → 100% */

/* alternate-reverse: 反向交替 */
animation-direction: alternate-reverse;
/* 第1次: 100% → 0% */
/* 第2次: 0% → 100% */
```

---

**世界规则 4:Animation Fill Mode (填充模式)**

```css
/* none (默认): 不保留状态 */
animation-fill-mode: none;
/* 延迟期间: 元素初始状态 */
/* 播放结束: 元素初始状态 */

/* forwards: 保持结束状态 */
animation-fill-mode: forwards;
/* 播放结束: 保持100%关键帧 */

/* backwards: 应用开始状态 */
animation-fill-mode: backwards;
/* 延迟期间: 应用0%关键帧 */

/* both: forwards + backwards */
animation-fill-mode: both;
/* 延迟期间: 应用0%关键帧 */
/* 播放结束: 保持100%关键帧 */
```

**用例**: 入场动画使用`both`,确保延迟期间和结束后都正确显示。

---

**世界规则 5:缓动函数 (Timing Functions)**

```css
/* 预定义缓动 */
linear            /* 匀速 */
ease              /* 慢-快-慢 (默认) */
ease-in           /* 慢-快 */
ease-out          /* 快-慢 */
ease-in-out       /* 慢-快-慢 (更明显) */

/* 贝塞尔曲线 */
cubic-bezier(0.42, 0, 0.58, 1)  /* 自定义曲线 */
cubic-bezier(0.68, -0.55, 0.265, 1.55)  /* 回弹效果 */

/* 步进函数 */
steps(4, end)     /* 4步,结束时跳变 */
steps(4, start)   /* 4步,开始时跳变 */
step-start        /* 等同于 steps(1, start) */
step-end          /* 等同于 steps(1, end) */
```

**贝塞尔曲线工具**: [cubic-bezier.com](https://cubic-bezier.com)

---

**世界规则 6:关键帧定义**

```css
/* 百分比语法 */
@keyframes slide {
    0% {
        transform: translateX(0);
        opacity: 0;
    }
    50% {
        transform: translateX(100px);
        opacity: 0.5;
    }
    100% {
        transform: translateX(200px);
        opacity: 1;
    }
}

/* from/to语法 */
@keyframes fade {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* 多个关键帧共享 */
@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-20px); }
}

/* 关键帧可嵌套其他动画 */
@keyframes complex {
    0% { animation-timing-function: ease-in; }
    50% { animation-timing-function: ease-out; }
}
```

---

**世界规则 7:动画事件监听**

```javascript
const element = document.querySelector('.animated');

/* animationstart: 动画开始 */
element.addEventListener('animationstart', (e) => {
    console.log('动画开始:', e.animationName);
});

/* animationiteration: 每次迭代 */
element.addEventListener('animationiteration', (e) => {
    console.log('迭代:', e.elapsedTime);
});

/* animationend: 动画结束 */
element.addEventListener('animationend', (e) => {
    console.log('动画结束');
    element.classList.remove('animated');  /* 移除动画 */
});

/* transitionend: 过渡结束 */
element.addEventListener('transitionend', (e) => {
    console.log('过渡结束:', e.propertyName);
});
```

---

**事故档案编号**:CSS-2024-1629
**影响范围**:交互反馈、视觉效果、用户体验
**根本原因**:不理解transition和animation的区别及fill-mode的作用
**修复成本**:低(理解后选择正确的动画方式)

这是CSS世界第29次被记录的动画系统事故。CSS提供两种动画机制——transition处理简单状态过渡,animation处理复杂关键帧动画。transition需要触发,animation自动播放;transition双向,animation可循环、反向、暂停。理解fill-mode,理解缓动函数,就理解了CSS如何在时间轴上控制元素的运动。

《第30次记录:样式重排事故 —— 渲染性能的隐形杀手》

---

## 事故现场

周四下午两点,你的电商网站刚上线,运营总监就打来电话。窗外开始下雨,你的心情也跟着沉重起来。

你的电商网站上线后,用户投诉:"商品列表滚动时很卡顿,手机上尤其明显。"

你打开Chrome DevTools的Performance面板录制滚动操作——火焰图上密密麻麻全是紫色的Layout(重排)条,帧率只有15FPS。

你检查代码,发现滚动时在读取每个商品卡片的offsetHeight:

```javascript
window.addEventListener('scroll', () => {
    document.querySelectorAll('.product-card').forEach(card => {
        const height = card.offsetHeight;  /* 强制重排! */
        if (height > 300) {
            card.classList.add('large');
        }
    });
});
```

"为什么读取offsetHeight会导致重排?"

你尝试优化,把读取和写入分离:

```javascript
const heights = [];
document.querySelectorAll('.product-card').forEach(card => {
    heights.push(card.offsetHeight);  /* 批量读取 */
});

document.querySelectorAll('.product-card').forEach((card, index) => {
    if (heights[index] > 300) {
        card.classList.add('large');  /* 批量写入 */
    }
});
```

帧率提升到30FPS,但还是卡。你发现`.large`类会改变元素的width:

```css
.product-card.large {
    width: 350px;  /* 触发重排! */
}
```

你改用transform:

```css
.product-card.large {
    transform: scale(1.1);  /* 只触发重绘 */
}
```

帧率飙升到60FPS!但你困惑:"为什么改width会重排,transform不会?"

---

## 深入迷雾

下午三点,性能优化专家老张走过来:"卡顿问题找到原因了吗?我看你一直在调Performance面板。"你摇摇头,他说:"可能是重排问题,我给你讲讲渲染流水线。"

你开始系统学习浏览器的渲染过程。首先理解渲染流水线:

```
1. JavaScript: 修改DOM/CSSOM
   ↓
2. Style: 计算样式(Recalculate Style)
   ↓
3. Layout: 计算布局(Reflow/重排)
   ↓
4. Paint: 绘制像素(Repaint/重绘)
   ↓
5. Composite: 合成图层
```

你测试了哪些属性会触发重排:

```javascript
/* 触发重排的属性(Reflow/Layout) */
width, height
margin, padding, border
top, left, right, bottom
font-size, line-height
text-align, vertical-align
display, float, position
overflow, white-space

/* 触发重绘但不重排的属性(Repaint/Paint) */
color, background-color
border-color, border-style
visibility, outline
box-shadow, border-radius

/* 只触发合成的属性(Composite Only) */
transform, opacity
filter, will-change
```

你发现读取某些属性会强制同步重排:

```javascript
/* 强制同步重排的属性(Forced Synchronous Layout) */
element.offsetTop, element.offsetLeft
element.offsetWidth, element.offsetHeight
element.clientTop, element.clientLeft
element.clientWidth, element.clientHeight
element.scrollTop, element.scrollLeft
element.scrollWidth, element.scrollHeight
element.getBoundingClientRect()
window.getComputedStyle(element)

/* 示例:重排抖动(Layout Thrashing) */
for (let i = 0; i < 100; i++) {
    const height = element.offsetHeight;  /* 读取:触发重排 */
    element.style.height = height + 10 + 'px';  /* 写入:标记需重排 */
    /* 下次读取又触发重排,循环100次! */
}
```

你学习了批量读写的正确模式:

```javascript
/* ❌ 错误:交替读写 */
elements.forEach(el => {
    const height = el.offsetHeight;  /* 读 */
    el.style.height = height * 2 + 'px';  /* 写 */
});

/* ✅ 正确:先读后写 */
const heights = [];
elements.forEach(el => {
    heights.push(el.offsetHeight);  /* 批量读 */
});
elements.forEach((el, i) => {
    el.style.height = heights[i] * 2 + 'px';  /* 批量写 */
});

/* ✅ 更好:使用requestAnimationFrame */
requestAnimationFrame(() => {
    elements.forEach(el => {
        const height = el.offsetHeight;
        el.style.height = height * 2 + 'px';
    });
});
```

你测试了合成层(Compositor Layer):

```css
/* 创建合成层的方式 */

/* 1. will-change */
.element {
    will-change: transform;  /* 提示浏览器 */
}

/* 2. 3D transform */
.element {
    transform: translateZ(0);  /* 或任何3D变换 */
}

/* 3. video/canvas */
<video>, <canvas>  /* 自动创建 */

/* 4. CSS动画的transform/opacity */
@keyframes slide {
    from { transform: translateX(0); }
    to { transform: translateX(100px); }
}
```

---

## 真相浮现

下午五点,你完成了所有性能优化,商品列表滚动帧率稳定在60FPS。老张测试后说:"不错,现在丝般顺滑。"你把优化报告发给运营总监,终于松了一口气。

你整理了CSS性能优化的完整规则:

**规则1:渲染流水线的三个阶段**

```
完整渲染:
JS → Style → Layout → Paint → Composite

只重绘:
JS → Style → Paint → Composite

只合成:
JS → Style → Composite
```

**属性分类**:

```css
/* Layout(最昂贵): ~10-20ms */
width, height, margin, padding, border, top, left, position, float, display

/* Paint(中等): ~3-5ms */
color, background, border-color, box-shadow, border-radius

/* Composite(最快): ~1ms */
transform, opacity, filter, will-change
```

你创建了性能测试:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSS性能测试</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            padding: 20px;
            font-family: Arial, sans-serif;
        }

        .demo {
            margin-bottom: 50px;
        }

        .box {
            width: 100px;
            height: 100px;
            background: lightblue;
            border: 2px solid #0066cc;
            margin: 10px;
            display: inline-block;
        }

        /* 测试1: Layout属性(慢) */
        .layout-animation {
            animation: layoutMove 2s infinite;
        }

        @keyframes layoutMove {
            0%, 100% { margin-left: 0; }
            50% { margin-left: 200px; }
        }

        /* 测试2: Paint属性(中) */
        .paint-animation {
            animation: paintChange 2s infinite;
        }

        @keyframes paintChange {
            0%, 100% { background: lightblue; }
            50% { background: lightcoral; }
        }

        /* 测试3: Composite属性(快) */
        .composite-animation {
            animation: compositeMove 2s infinite;
        }

        @keyframes compositeMove {
            0%, 100% { transform: translateX(0); }
            50% { transform: translateX(200px); }
        }

        /* 测试4: will-change优化 */
        .optimized {
            will-change: transform;
            animation: compositeMove 2s infinite;
        }

        .stats {
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 15px;
            border-radius: 5px;
            font-size: 14px;
            z-index: 1000;
        }

        code {
            background: #f5f5f5;
            padding: 2px 5px;
            border-radius: 3px;
            color: #333;
        }
    </style>
</head>
<body>
    <div class="stats">
        FPS: <span id="fps">-</span><br>
        Frame Time: <span id="frameTime">-</span>ms
    </div>

    <h1>CSS性能优化测试</h1>

    <div class="demo">
        <h3>测试1: Layout属性动画(触发重排,慢)</h3>
        <code>margin-left</code>
        <br>
        <div class="box layout-animation">Layout</div>
        <div class="box layout-animation">Layout</div>
        <div class="box layout-animation">Layout</div>
        <div class="box layout-animation">Layout</div>
        <div class="box layout-animation">Layout</div>
    </div>

    <div class="demo">
        <h3>测试2: Paint属性动画(触发重绘,中)</h3>
        <code>background-color</code>
        <br>
        <div class="box paint-animation">Paint</div>
        <div class="box paint-animation">Paint</div>
        <div class="box paint-animation">Paint</div>
        <div class="box paint-animation">Paint</div>
        <div class="box paint-animation">Paint</div>
    </div>

    <div class="demo">
        <h3>测试3: Composite属性动画(只合成,快)</h3>
        <code>transform</code>
        <br>
        <div class="box composite-animation">Composite</div>
        <div class="box composite-animation">Composite</div>
        <div class="box composite-animation">Composite</div>
        <div class="box composite-animation">Composite</div>
        <div class="box composite-animation">Composite</div>
    </div>

    <div class="demo">
        <h3>测试4: will-change优化</h3>
        <code>will-change: transform</code>
        <br>
        <div class="box optimized">Optimized</div>
        <div class="box optimized">Optimized</div>
        <div class="box optimized">Optimized</div>
        <div class="box optimized">Optimized</div>
        <div class="box optimized">Optimized</div>
    </div>

    <script>
        // FPS计数器
        let lastTime = performance.now();
        let frames = 0;
        let fps = 0;

        function measureFPS() {
            frames++;
            const currentTime = performance.now();
            const deltaTime = currentTime - lastTime;

            if (deltaTime >= 1000) {
                fps = Math.round((frames * 1000) / deltaTime);
                frames = 0;
                lastTime = currentTime;

                document.getElementById('fps').textContent = fps;
                document.getElementById('frameTime').textContent =
                    (1000 / fps).toFixed(2);
            }

            requestAnimationFrame(measureFPS);
        }

        measureFPS();

        // 性能测试工具
        function testPerformance(fn, iterations = 1000) {
            const start = performance.now();
            for (let i = 0; i < iterations; i++) {
                fn();
            }
            const end = performance.now();
            return end - start;
        }

        // 测试:读取offsetHeight
        const readTime = testPerformance(() => {
            document.querySelectorAll('.box').forEach(box => {
                const _ = box.offsetHeight;
            });
        });
        console.log('读取offsetHeight 1000次:', readTime.toFixed(2) + 'ms');

        // 测试:修改transform
        const transformTime = testPerformance(() => {
            document.querySelectorAll('.box').forEach(box => {
                box.style.transform = 'translateX(10px)';
            });
        });
        console.log('修改transform 1000次:', transformTime.toFixed(2) + 'ms');

        // 测试:修改width(触发重排)
        const widthTime = testPerformance(() => {
            document.querySelectorAll('.box').forEach(box => {
                box.style.width = '110px';
            });
        });
        console.log('修改width 1000次:', widthTime.toFixed(2) + 'ms');
    </script>
</body>
</html>
```

---

## 世界法则

**世界规则 1:渲染流水线的三个阶段**

```
JavaScript → Style → Layout → Paint → Composite

1. Style (样式计算):
   - 计算每个元素的最终样式
   - 约1-2ms

2. Layout (布局/重排):
   - 计算元素的几何信息(位置、大小)
   - 最昂贵,约10-20ms

3. Paint (绘制/重绘):
   - 填充像素(颜色、阴影、边框)
   - 约3-5ms

4. Composite (合成):
   - 合成图层到屏幕
   - 最快,约1ms
```

---

**世界规则 2:重排 vs 重绘 vs 合成**

```css
/* 触发重排(Layout):最昂贵 */
width, height, margin, padding, border
top, left, right, bottom
font-size, line-height
display, position, float, overflow

/* 触发重绘(Paint):中等 */
color, background, background-color
border-color, border-style
box-shadow, border-radius
visibility, outline

/* 只触发合成(Composite):最快 */
transform, opacity
filter, will-change
```

**性能对比**:
- 重排: ~10-20ms (+ 重绘 + 合成)
- 重绘: ~3-5ms (+ 合成)
- 合成: ~1ms

---

**世界规则 3:强制同步重排(Forced Synchronous Layout)**

```javascript
/* ❌ 强制同步重排:读写交替 */
for (let i = 0; i < elements.length; i++) {
    const height = elements[i].offsetHeight;  /* 读:触发重排 */
    elements[i].style.height = height + 10 + 'px';  /* 写 */
    /* 每次循环都重排! */
}

/* ✅ 避免强制重排:先读后写 */
const heights = [];
for (let i = 0; i < elements.length; i++) {
    heights.push(elements[i].offsetHeight);  /* 批量读 */
}
for (let i = 0; i < elements.length; i++) {
    elements[i].style.height = heights[i] + 10 + 'px';  /* 批量写 */
}
```

**会触发强制重排的属性**:
```javascript
offsetTop/Left/Width/Height
clientTop/Left/Width/Height
scrollTop/Left/Width/Height
getBoundingClientRect()
getComputedStyle()
```

---

**世界规则 4:使用transform代替position/margin**

```css
/* ❌ 触发重排:移动元素 */
.element {
    position: relative;
    left: 100px;  /* 重排 */
    top: 50px;    /* 重排 */
}

.element {
    margin-left: 100px;  /* 重排 */
}

/* ✅ 只触发合成:transform */
.element {
    transform: translate(100px, 50px);  /* 合成 */
}

/* ❌ 触发重排:缩放 */
.element {
    width: 200px;   /* 重排 */
    height: 200px;  /* 重排 */
}

/* ✅ 只触发合成:transform */
.element {
    transform: scale(2);  /* 合成 */
}
```

---

**世界规则 5:使用will-change提示浏览器**

```css
/* will-change: 提前通知浏览器 */
.element {
    will-change: transform;  /* 即将变换 */
}

.element:hover {
    transform: scale(1.1);
}

/* 常用值 */
will-change: auto;         /* 默认 */
will-change: transform;    /* 变换 */
will-change: opacity;      /* 透明度 */
will-change: scroll-position;  /* 滚动 */
will-change: contents;     /* 内容 */

/* ⚠️ 注意事项 */
/* 1. 不要过度使用 */
* {
    will-change: transform;  /* ❌ 消耗内存 */
}

/* 2. 动画结束后移除 */
element.addEventListener('animationend', () => {
    element.style.willChange = 'auto';  /* ✅ 清理 */
});

/* 3. 不要太早设置 */
/* ❌ 页面加载时就设置 */
.element { will-change: transform; }

/* ✅ 用户交互时设置 */
.element:hover { will-change: transform; }
```

---

**世界规则 6:requestAnimationFrame优化**

```javascript
/* ❌ 直接操作DOM */
window.addEventListener('scroll', () => {
    element.style.transform = `translateY(${window.scrollY}px)`;
    /* 可能在单帧内执行多次 */
});

/* ✅ 使用requestAnimationFrame */
let ticking = false;

window.addEventListener('scroll', () => {
    if (!ticking) {
        requestAnimationFrame(() => {
            element.style.transform = `translateY(${window.scrollY}px)`;
            ticking = false;
        });
        ticking = true;
    }
});

/* ✅ 读写分离 + requestAnimationFrame */
let scrollY = 0;

window.addEventListener('scroll', () => {
    scrollY = window.scrollY;  /* 读取 */
});

function update() {
    element.style.transform = `translateY(${scrollY}px)`;  /* 写入 */
    requestAnimationFrame(update);
}

update();
```

---

**世界规则 7:性能优化最佳实践**

```css
/* 1. 使用GPU加速的属性 */
✅ transform, opacity, filter
❌ width, height, margin, padding

/* 2. 创建合成层 */
.element {
    transform: translateZ(0);  /* 或 will-change */
}

/* 3. 避免Layout Thrashing */
/* ✅ 批量读取,批量写入 */
const heights = elements.map(el => el.offsetHeight);
elements.forEach((el, i) => el.style.height = heights[i] + 'px');

/* 4. 使用CSS动画代替JS动画 */
/* ✅ CSS动画可以在合成线程运行 */
@keyframes slide {
    from { transform: translateX(0); }
    to { transform: translateX(100px); }
}

/* 5. 减少DOM深度和复杂度 */
/* ❌ 深层嵌套 */
<div><div><div><div><p>文本</p></div></div></div></div>

/* ✅ 扁平结构 */
<p>文本</p>

/* 6. 使用contain属性 */
.card {
    contain: layout style paint;
    /* 隔离重排影响 */
}

/* 7. 虚拟化长列表 */
/* 只渲染可见区域,不是全部1000个元素 */
```

---

**事故档案编号**:CSS-2024-1630
**影响范围**:页面性能、滚动流畅度、交互体验
**根本原因**:不理解重排、重绘、合成的区别和性能影响
**修复成本**:中等(需重构为GPU加速属性)

这是CSS世界第30次被记录的样式重排事故,也是Part 2的最后一章。浏览器渲染分为Layout、Paint、Composite三个阶段。改变width触发重排,改变color触发重绘,改变transform只触发合成——性能差距10-20倍。强制同步重排(读写交替)是性能杀手,will-change是优化提示,requestAnimationFrame是帧同步利器。理解渲染流水线,就理解了CSS性能优化的本质。

---

**Part 2完结记录**

你历经15次CSS表象事故,从样式如何降临世界(附着方式),到选择器如何定位元素(规则命中),从权重如何裁决冲突(特异性战争),到继承如何传播特征(血缘链条)。

你见证了盒模型的度量之争(content-box vs border-box),display的形态转换(块级、行内、弹性),position的坐标参考(static、relative、absolute、fixed、sticky),z-index的层叠迷局(层叠上下文的隔离)。

你掌握了Flex的一维分配(主轴与交叉轴),Grid的二维网格(行列同控),媒体查询的响应断点(移动优先),overflow的溢出裁剪(可见、隐藏、滚动)。

你理解了transform的空间魔法(不影响文档流的变换),animation的时间控制(关键帧与缓动函数),以及渲染流水线的性能法则(重排、重绘、合成)。

CSS不是简单的样式声明,而是表象世界的完整法则系统。它控制着元素如何出现、如何排列、如何变换、如何运动。这15次事故,记录了从无知到理解,从困惑到掌控的完整旅程。

**Part 2:表象与幻术-CSS** 完结。

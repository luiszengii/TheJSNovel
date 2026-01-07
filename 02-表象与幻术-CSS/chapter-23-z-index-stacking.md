《第23次记录:z-index迷局 —— 层叠上下文的战争》

---

## 事故现场

周四上午十点,你正在实现一个弹窗功能。窗外开始下小雨,办公室里有些闷热。

你在做一个弹窗,想让它显示在所有内容上方。你给弹窗设置了超高的z-index:

```css
.modal {
    position: fixed;
    z-index: 999999;
}
```

刷新页面——弹窗确实在大部分内容上方,但被导航栏遮挡了。你检查导航栏的z-index:

```css
.navbar {
    position: relative;
    z-index: 100;
}
```

"z-index: 100怎么可能盖过999999?"

你尝试给弹窗加更大的值:

```css
.modal {
    z-index: 9999999;
}
```

没用,弹窗还是在导航栏下面。

更诡异的是,你发现某个z-index: 10的元素,竟然在z-index: 1的元素下面:

```html
<div class="parent">
    <div class="child1" style="z-index: 1;">Child 1</div>
</div>
<div class="child2" style="z-index: 10;">Child 2</div>
```

Child 2应该在上面,但实际在Child 1下面。

"z-index到底是怎么工作的?"

---

## 深入迷雾

上午十一点,你决定彻底搞清楚z-index的规则。产品经理发来消息:"弹窗的层级问题解决了吗?下午要演示给客户。"你心里有些着急。

你开始系统测试z-index的规则。首先发现了前提条件:

```css
/* ❌ 无效: position是static */
.box {
    position: static;
    z-index: 999;  /* 完全无效 */
}

/* ✅ 有效: position不是static */
.box {
    position: relative;
    z-index: 999;  /* 生效 */
}
```

你测试了同级元素的z-index:

```html
<div class="box1" style="position: relative; z-index: 1;">Box 1</div>
<div class="box2" style="position: relative; z-index: 2;">Box 2</div>
```

Box 2在Box 1上面,符合预期。

但嵌套元素就出问题了:

```html
<div class="parent1" style="position: relative; z-index: 1;">
    <div class="child1" style="position: relative; z-index: 9999;">
        Child 1 (z-index: 9999)
    </div>
</div>

<div class="parent2" style="position: relative; z-index: 2;">
    <div class="child2" style="position: relative; z-index: 1;">
        Child 2 (z-index: 1)
    </div>
</div>
```

Child 2在Child 1上面!即使Child 1的z-index是9999。

你发现了"层叠上下文"(Stacking Context)的概念:

```javascript
// 检测元素的层叠关系
function checkStacking(el) {
    const computed = getComputedStyle(el);
    console.log('Element:', el.className);
    console.log('  position:', computed.position);
    console.log('  z-index:', computed.zIndex);
    console.log('  opacity:', computed.opacity);
    console.log('  transform:', computed.transform);
}
```

你发现创建层叠上下文的多种方式:

```css
/* 方式1: position + z-index */
position: relative;
z-index: 1;

/* 方式2: opacity */
opacity: 0.99;

/* 方式3: transform */
transform: translateZ(0);

/* 方式4: filter */
filter: blur(0);

/* 方式5: will-change */
will-change: transform;
```

---

## 真相浮现

中午十二点,你终于理解了层叠上下文的隔离规则。你重构了弹窗的层级结构,这次正确地显示在所有内容上方。你把修复后的代码发给产品经理,松了一口气。

你整理了z-index和层叠上下文的完整规则:

**规则1:层叠上下文的七层规则**

```
从下到上的层叠顺序:
1. 根元素背景和边框
2. 负z-index的定位子元素
3. 块级盒子
4. 浮动盒子
5. 行内盒子
6. z-index: 0 / auto的定位子元素
7. 正z-index的定位子元素
```

**规则2:创建层叠上下文的条件**

```css
/* 1. 根元素 <html> */

/* 2. position + z-index */
position: relative | absolute | fixed | sticky;
z-index: <integer>;  /* 不是auto */

/* 3. flex/grid子元素 + z-index */
.flex-container { display: flex; }
.flex-item { z-index: 1; }  /* 自动创建层叠上下文 */

/* 4. opacity < 1 */
opacity: 0.99;

/* 5. transform 不是 none */
transform: translateZ(0);

/* 6. filter 不是 none */
filter: blur(5px);

/* 7. will-change */
will-change: opacity | transform;

/* 8. isolation */
isolation: isolate;

/* 9. mix-blend-mode 不是 normal */
mix-blend-mode: multiply;
```

你创建了完整测试:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Z-index与层叠上下文测试</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        .demo {
            margin: 50px;
            position: relative;
        }

        /* 测试1: 基础z-index */
        .test1 .box {
            width: 200px;
            height: 200px;
            position: absolute;
        }

        .test1 .box1 {
            background: rgba(255, 0, 0, 0.7);
            top: 0;
            left: 0;
            z-index: 1;
        }

        .test1 .box2 {
            background: rgba(0, 255, 0, 0.7);
            top: 50px;
            left: 50px;
            z-index: 2;
        }

        .test1 .box3 {
            background: rgba(0, 0, 255, 0.7);
            top: 100px;
            left: 100px;
            z-index: 3;
        }

        /* 测试2: 层叠上下文陷阱 */
        .test2 .parent {
            width: 300px;
            height: 150px;
            position: relative;
            margin: 10px;
        }

        .test2 .parent1 {
            background: rgba(255, 200, 200, 0.8);
            z-index: 1;  /* 创建层叠上下文 */
        }

        .test2 .parent2 {
            background: rgba(200, 255, 200, 0.8);
            z-index: 2;  /* 创建层叠上下文 */
            margin-top: -100px;
        }

        .test2 .child {
            width: 100px;
            height: 100px;
            position: absolute;
            top: 20px;
            left: 20px;
        }

        .test2 .child1 {
            background: red;
            z-index: 9999;  /* 无法超越parent2 */
        }

        .test2 .child2 {
            background: green;
            z-index: 1;  /* 只需要1就能盖住child1 */
        }

        /* 测试3: 创建层叠上下文的各种方式 */
        .test3 .item {
            width: 150px;
            height: 100px;
            margin: 10px;
            padding: 10px;
            border: 2px solid #333;
            float: left;
        }

        .test3 .opacity-context {
            opacity: 0.99;  /* 创建层叠上下文 */
            background: lightblue;
        }

        .test3 .transform-context {
            transform: translateZ(0);  /* 创建层叠上下文 */
            background: lightgreen;
        }

        .test3 .filter-context {
            filter: blur(0);  /* 创建层叠上下文 */
            background: lightcoral;
        }

        /* 测试4: 负z-index */
        .test4 {
            position: relative;
            background: lightyellow;
            padding: 20px;
            z-index: 0;  /* 创建层叠上下文 */
        }

        .test4 .negative {
            position: absolute;
            top: 10px;
            left: 10px;
            width: 100px;
            height: 100px;
            background: red;
            z-index: -1;  /* 在父元素背景之上,内容之下 */
        }

        /* 测试5: flex子元素的z-index */
        .test5 {
            display: flex;
        }

        .test5 .flex-item {
            width: 100px;
            height: 100px;
            margin: -20px;
            background: lightblue;
        }

        .test5 .flex-item:nth-child(1) { z-index: 3; background: red; }
        .test5 .flex-item:nth-child(2) { z-index: 1; background: green; }
        .test5 .flex-item:nth-child(3) { z-index: 2; background: blue; }
    </style>
</head>
<body>
    <div class="demo test1">
        <h3>测试1: 基础z-index (同级比较)</h3>
        <div class="box box1">z-index: 1</div>
        <div class="box box2">z-index: 2</div>
        <div class="box box3">z-index: 3</div>
    </div>

    <div class="demo test2">
        <h3>测试2: 层叠上下文陷阱</h3>
        <div class="parent parent1">
            Parent 1 (z-index: 1)
            <div class="child child1">Child 1<br>(z-index: 9999)</div>
        </div>
        <div class="parent parent2">
            Parent 2 (z-index: 2)
            <div class="child child2">Child 2<br>(z-index: 1)</div>
        </div>
        <p style="clear: both; padding-top: 120px;">
            Child 2在Child 1上面,因为Parent 2的z-index(2) > Parent 1的z-index(1)
        </p>
    </div>

    <div class="demo test3">
        <h3>测试3: 创建层叠上下文的方式</h3>
        <div class="item opacity-context">
            opacity: 0.99
        </div>
        <div class="item transform-context">
            transform: translateZ(0)
        </div>
        <div class="item filter-context">
            filter: blur(0)
        </div>
        <p style="clear: both;">这些都创建了独立的层叠上下文</p>
    </div>

    <div class="demo test4">
        <h3>测试4: 负z-index</h3>
        <div class="negative">z-index: -1</div>
        <p>负z-index在父元素背景之上,但在内容之下</p>
    </div>

    <div class="demo test5">
        <h3>测试5: flex子元素的z-index</h3>
        <div class="flex-item">Item 1<br>z: 3</div>
        <div class="flex-item">Item 2<br>z: 1</div>
        <div class="flex-item">Item 3<br>z: 2</div>
    </div>

    <script>
        // 检测层叠上下文
        function detectStackingContext(selector) {
            const el = document.querySelector(selector);
            if (!el) return;

            const computed = getComputedStyle(el);

            console.log(`${selector}:`);
            console.log('  position:', computed.position);
            console.log('  z-index:', computed.zIndex);
            console.log('  opacity:', computed.opacity);
            console.log('  transform:', computed.transform);
            console.log('  filter:', computed.filter);

            // 判断是否创建层叠上下文
            const createsContext =
                computed.position !== 'static' && computed.zIndex !== 'auto' ||
                parseFloat(computed.opacity) < 1 ||
                computed.transform !== 'none' ||
                computed.filter !== 'none';

            console.log('  Creates stacking context:', createsContext);
        }

        detectStackingContext('.test2 .parent1');
        detectStackingContext('.test2 .parent2');
        detectStackingContext('.test3 .opacity-context');
    </script>
</body>
</html>
```

---

## 世界法则

**世界规则 1:z-index的生效前提**

```css
/* ❌ 无效: position是static (默认) */
.box {
    z-index: 999;  /* 完全无效,被忽略 */
}

/* ✅ 有效: position是relative/absolute/fixed/sticky */
.box {
    position: relative;
    z-index: 999;  /* 生效 */
}

/* ✅ 有效: flex/grid子元素 */
.container {
    display: flex;
}
.item {
    z-index: 1;  /* 生效,即使没有position */
}
```

**关键点**: z-index只对定位元素(position不是static)或flex/grid子元素生效。

---

**世界规则 2:层叠上下文的创建条件**

```css
/* 1. 根元素 <html> 自动创建 */

/* 2. position + z-index (z-index不是auto) */
position: relative;
z-index: 1;  /* 创建层叠上下文 */

/* 3. opacity < 1 */
opacity: 0.99;  /* 创建层叠上下文 */

/* 4. transform 不是 none */
transform: translateZ(0);  /* 创建层叠上下文 */
transform: rotate(0deg);   /* 创建层叠上下文 */

/* 5. filter 不是 none */
filter: blur(5px);  /* 创建层叠上下文 */

/* 6. flex/grid子元素 + z-index */
.flex-container { display: flex; }
.flex-item { z-index: 1; }  /* 创建层叠上下文 */

/* 7. isolation */
isolation: isolate;  /* 显式创建层叠上下文 */

/* 8. will-change */
will-change: opacity | transform;  /* 创建层叠上下文 */
```

---

**世界规则 3:层叠上下文的隔离规则**

```html
<div class="parent1" style="z-index: 1;">
    <div class="child1" style="z-index: 9999;">Child 1</div>
</div>
<div class="parent2" style="z-index: 2;">
    <div class="child2" style="z-index: 1;">Child 2</div>
</div>
```

**比较规则**:
1. Child 1和Child 2不在同一层叠上下文
2. 先比较父元素: parent2 (z:2) > parent1 (z:1)
3. parent2整体在parent1上面
4. 所以Child 2在Child 1上面,无论Child 1的z-index多大

**关键点**: 子元素的z-index只在父元素的层叠上下文内有效,无法跨越父级边界。

---

**世界规则 4:同一层叠上下文的七层顺序**

```
从下到上:
1. 层叠上下文的背景和边框
2. z-index为负的定位子元素
3. 块级盒子 (display: block)
4. 浮动盒子 (float)
5. 行内盒子 (display: inline)
6. z-index为0或auto的定位子元素
7. z-index为正的定位子元素
```

**示例**:

```css
.context {
    position: relative;
    z-index: 0;
    background: yellow;  /* 层级1 */
}

.negative {
    position: absolute;
    z-index: -1;  /* 层级2:在背景之上 */
}

.block {
    display: block;  /* 层级3 */
}

.float {
    float: left;  /* 层级4 */
}

.inline {
    display: inline;  /* 层级5 */
}

.zero {
    position: relative;
    z-index: 0;  /* 层级6 */
}

.positive {
    position: relative;
    z-index: 1;  /* 层级7:最上面 */
}
```

---

**世界规则 5:负z-index的特殊用途**

```css
.container {
    position: relative;
    z-index: 0;  /* 创建层叠上下文 */
    background: white;
}

.background-layer {
    position: absolute;
    z-index: -1;
    /* 在容器背景之上,但在内容之下 */
}
```

**用例**: 创建背景装饰效果,不遮挡内容

```html
<div class="card">
    <div class="decoration"></div>
    <h2>标题</h2>
    <p>内容在decoration之上</p>
</div>
```

```css
.card {
    position: relative;
    z-index: 0;
}

.decoration {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(45deg, blue, purple);
    opacity: 0.1;
    z-index: -1;  /* 在背景层,不遮挡文字 */
}
```

---

**世界规则 6:flex/grid子元素的z-index特殊性**

```css
/* flex/grid子元素不需要position也能用z-index */
.flex-container {
    display: flex;
}

.flex-item {
    z-index: 1;  /* ✅ 生效,且创建层叠上下文 */
    /* 不需要position: relative */
}
```

**对比**:

```html
<!-- 普通div -->
<div>
    <div style="z-index: 1;">无效</div>
</div>

<!-- flex子元素 -->
<div style="display: flex;">
    <div style="z-index: 1;">有效</div>
</div>
```

---

**世界规则 7:调试层叠上下文的方法**

```javascript
// 方法1: 检测是否创建层叠上下文
function createsStackingContext(el) {
    const computed = getComputedStyle(el);

    const checks = [
        // position + z-index
        computed.position !== 'static' && computed.zIndex !== 'auto',
        // opacity
        parseFloat(computed.opacity) < 1,
        // transform
        computed.transform !== 'none',
        // filter
        computed.filter !== 'none',
        // isolation
        computed.isolation === 'isolate',
        // will-change
        computed.willChange === 'opacity' || computed.willChange === 'transform'
    ];

    return checks.some(check => check);
}

// 方法2: 可视化z-index
function visualizeZIndex(el) {
    const rect = el.getBoundingClientRect();
    const computed = getComputedStyle(el);

    console.log('Element:', el);
    console.log('  z-index:', computed.zIndex);
    console.log('  stacking context:', createsStackingContext(el));
    console.log('  bounding rect:', rect);
}

// 方法3: Chrome DevTools
// Elements → Layers tab → 查看层叠关系
// Elements → Computed → filter "z-index"
```

**最佳实践**:
- ✅ 使用`isolation: isolate`显式创建层叠上下文
- ✅ 避免z-index数值竞赛(9999, 99999)
- ✅ 建立z-index规范(modal: 1000, dropdown: 100, tooltip: 10)
- ❌ 不要在不理解层叠上下文时随意增加z-index

---

**事故档案编号**:CSS-2024-1623
**影响范围**:元素层叠、弹窗定位、遮罩层级
**根本原因**:不理解层叠上下文的隔离规则
**修复成本**:中高(需要重构层级结构或z-index体系)

这是CSS世界第23次被记录的z-index迷局事故。z-index不是简单的数字大小比较,而是在层叠上下文内的局部比较。每个层叠上下文是一个独立的层级体系,子元素无法跨越父级边界。理解层叠上下文,就理解了CSS在Z轴上的空间划分。

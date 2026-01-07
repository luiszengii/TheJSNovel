《第19次记录:继承链断裂事故 —— 表象的血缘传播》

---

## 事故现场

周一上午九点，你在做一个博客网站,想让所有文字都用`Arial`字体。办公室里刚开完晨会，你戴上耳机开始工作。

你在`body`上设置:

```css
body {
    font-family: Arial, sans-serif;
}
```

刷新页面——大部分文字确实变成了Arial,但你发现`<button>`和`<input>`还是系统默认字体。

"为什么button不继承body的字体?"

你给button单独设置:

```css
button {
    font-family: inherit;
}
```

现在button的字体正常了。但你困惑:"为什么有些属性会继承,有些不会?"

更诡异的是,当你设置body的`border`:

```css
body {
    border: 1px solid red;
}
```

只有body元素有边框,所有子元素都没有边框。但当你设置`color`:

```css
body {
    color: blue;
}
```

所有文字都变蓝了。

"同样是CSS属性,为什么border不继承,color会继承?"

---

## 深入迷雾

上午十点，你开始系统地测试哪些属性会继承。首先是文本相关属性:

```html
<div style="color: red; font-size: 20px; font-family: Arial;">
    父元素
    <p>子元素 - 继承了父元素的样式</p>
</div>
```

子元素的`color`、`font-size`、`font-family`都被继承了。

然后你测试盒模型属性:

```html
<div style="margin: 20px; padding: 10px; border: 1px solid red;">
    父元素
    <p>子元素 - 没有继承margin/padding/border</p>
</div>
```

子元素没有继承任何盒模型属性。

你测试了布局属性:

```html
<div style="width: 500px; height: 300px; display: flex;">
    父元素
    <p>子元素 - 没有继承width/height/display</p>
</div>
```

也没有继承。

你发现了`inherit`关键字:

```css
button {
    font-family: inherit;  /* 强制继承父元素的font-family */
}

.box {
    border: inherit;  /* 强制继承父元素的border */
}
```

还有`initial`和`unset`:

```css
.reset {
    color: initial;  /* 重置为浏览器默认值 */
    font-size: unset;  /* 如果可继承则继承,否则重置为默认 */
}
```

你测试了继承的优先级:

```html
<div style="color: red;">
    <p style="color: blue;">
        直接设置 > 继承
        <span>这里是什么颜色?</span>
    </p>
</div>
```

`<span>`继承了`<p>`的`blue`,而不是`<div>`的`red`。"继承总是来自直接父元素。"

但当`<span>`自己有样式时:

```css
span {
    color: green;
}
```

结果是绿色。"直接设置 > 继承。"

---

## 真相浮现

你整理了CSS继承的完整规则:

**可继承属性(主要是文本相关)**:

```css
/* 字体属性 */
font-family, font-size, font-style, font-weight, font-variant
line-height, letter-spacing, word-spacing

/* 文本属性 */
color, text-align, text-indent, text-transform
white-space, word-break, word-wrap

/* 列表属性 */
list-style, list-style-type, list-style-position

/* 其他 */
visibility, cursor
```

**不可继承属性(主要是盒模型和布局)**:

```css
/* 盒模型 */
width, height, margin, padding, border

/* 布局 */
display, position, float, clear
top, right, bottom, left

/* 背景 */
background, background-color, background-image

/* 其他 */
opacity, overflow, z-index
```

**控制继承的关键字**:

```css
/* inherit: 强制继承 */
.child {
    border: inherit;  /* 即使border不可继承,也强制继承 */
}

/* initial: 重置为默认值 */
.reset {
    color: initial;  /* 重置为浏览器默认 */
}

/* unset: 智能重置 */
.smart-reset {
    color: unset;  /* 可继承属性→继承,不可继承→initial */
}

/* revert: 回退到用户代理样式 */
.revert {
    all: revert;  /* 回退所有属性 */
}
```

你创建了完整测试:

```html
<!DOCTYPE html>
<html>
<head>
    <title>CSS继承测试</title>
    <style>
        /* 测试1: 可继承属性 */
        .inherit-test {
            color: red;
            font-size: 20px;
            font-family: Arial;
            line-height: 2;
        }

        /* 测试2: 不可继承属性 */
        .no-inherit-test {
            border: 2px solid blue;
            margin: 20px;
            padding: 10px;
            background: yellow;
        }

        /* 测试3: 强制继承 */
        .force-inherit {
            border: 1px solid red;
        }
        .force-inherit p {
            border: inherit;  /* 强制继承border */
        }

        /* 测试4: 继承优先级 */
        .parent {
            color: blue;
        }
        .child {
            /* color没有设置,会继承parent的blue */
        }
        .child-override {
            color: green;  /* 覆盖继承 */
        }

        /* 测试5: all属性 */
        .reset-all {
            all: initial;  /* 重置所有属性 */
        }
        .inherit-all {
            all: inherit;  /* 继承所有属性 */
        }
    </style>
</head>
<body>
    <h2>测试1: 可继承属性</h2>
    <div class="inherit-test">
        父元素文字
        <p>子元素 - 继承了color, font-size, font-family, line-height</p>
    </div>

    <h2>测试2: 不可继承属性</h2>
    <div class="no-inherit-test">
        父元素
        <p>子元素 - 没有border, margin, padding, background</p>
    </div>

    <h2>测试3: 强制继承</h2>
    <div class="force-inherit">
        父元素
        <p>子元素 - 使用inherit强制继承border</p>
    </div>

    <h2>测试4: 继承优先级</h2>
    <div class="parent">
        <div class="child">继承的蓝色</div>
        <div class="child-override">覆盖的绿色</div>
    </div>

    <h2>测试5: 表单元素继承</h2>
    <div style="font-family: Arial; font-size: 18px; color: red;">
        <button>按钮 - 默认不继承字体</button>
        <button style="font: inherit;">按钮 - 使用inherit</button>
        <input type="text" value="输入框">
        <input type="text" value="继承字体" style="font: inherit; color: inherit;">
    </div>

    <script>
        // 检查属性是否可继承
        function isInherited(element, property) {
            const parent = element.parentElement;
            if (!parent) return false;

            const parentValue = getComputedStyle(parent)[property];
            const childValue = getComputedStyle(element)[property];

            return parentValue === childValue;
        }

        const p = document.querySelector('.inherit-test p');
        console.log('color继承:', isInherited(p, 'color'));
        console.log('border继承:', isInherited(p, 'borderWidth'));
    </script>
</body>
</html>
```

---

## 世界法则

**世界规则 1:只有部分CSS属性会自动继承**

**可继承属性(主要是文本相关)**:

```css
/* 字体 */
font-family, font-size, font-weight, font-style
line-height, letter-spacing, word-spacing

/* 文本 */
color, text-align, text-indent, text-decoration
text-transform, white-space

/* 列表 */
list-style, list-style-type

/* 其他 */
visibility, cursor, quotes
```

**不可继承属性(主要是盒模型和布局)**:

```css
/* 盒模型 */
width, height, margin, padding, border

/* 定位 */
display, position, float, top, left

/* 背景 */
background, background-color

/* 其他 */
overflow, z-index, opacity
```

**记忆规则**: 与文本相关的属性通常可继承,与盒子布局相关的属性通常不可继承。

---

**世界规则 2:继承来自直接父元素**

```html
<div style="color: red;">       <!-- 祖父 -->
    <p style="color: blue;">    <!-- 父 -->
        <span>文本</span>        <!-- 子 -->
    </p>
</div>
```

`<span>`的颜色是`blue`,不是`red`。继承总是从**直接父元素**获取,不会跨越层级。

---

**世界规则 3:继承的优先级最低**

```css
/* 权重优先级: */
直接设置 > 继承

/* 示例 */
<div style="color: red;">
    <p style="color: blue;">
        <span>蓝色</span>  <!-- 继承p的blue -->
    </p>
</div>

span {
    color: green;  /* 绿色 - 直接设置覆盖继承 */
}
```

即使是权重为0的通配符选择器,也比继承优先:

```css
* {
    color: black;  /* 权重(0,0,0,0),但覆盖所有继承 */
}
```

---

**世界规则 4:四个继承控制关键字**

```css
/* inherit: 强制继承父元素 */
button {
    font-family: inherit;  /* 强制继承,即使默认不继承 */
}

/* initial: 重置为CSS规范定义的初始值 */
p {
    color: initial;  /* 通常是black */
    margin: initial;  /* 通常是0 */
}

/* unset: 智能重置 */
div {
    color: unset;     /* 可继承属性→继承 */
    margin: unset;    /* 不可继承→initial */
}

/* revert: 回退到用户代理样式表 */
h1 {
    font-size: revert;  /* 回退到浏览器默认的2em */
}
```

**区别对比**:

| 关键字 | 可继承属性 | 不可继承属性 |
|-------|----------|------------|
| `inherit` | 继承父元素 | 继承父元素 |
| `initial` | CSS初始值 | CSS初始值 |
| `unset` | 继承父元素 | CSS初始值 |
| `revert` | 用户代理样式 | 用户代理样式 |

---

**世界规则 5:all属性批量控制继承**

```css
/* all属性: 控制除了unicode-bidi和direction外的所有属性 */

.reset-all {
    all: initial;  /* 重置所有属性为初始值 */
}

.inherit-all {
    all: inherit;  /* 继承所有属性 */
}

.unset-all {
    all: unset;  /* 智能重置所有属性 */
}

.revert-all {
    all: revert;  /* 回退所有属性到用户代理样式 */
}
```

**用例: 重置第三方组件样式**:

```css
.third-party-widget {
    all: initial;  /* 隔离外部样式影响 */
    /* 然后重新定义需要的样式 */
    font-family: Arial;
    color: black;
}
```

---

**世界规则 6:表单元素默认不继承字体**

```html
<div style="font-family: Arial; font-size: 16px; color: blue;">
    <p>段落文字 - 继承Arial, 16px, 蓝色</p>
    <button>按钮 - 不继承字体</button>
    <input type="text" value="输入框 - 不继承字体">
</div>
```

**原因**: 浏览器给表单元素设置了默认字体,覆盖了继承。

**解决方案**:

```css
/* 方案1: 单独设置 */
button, input, select, textarea {
    font-family: inherit;
    font-size: inherit;
    color: inherit;
}

/* 方案2: 使用font简写 */
button, input, select, textarea {
    font: inherit;
}
```

---

**世界规则 7:继承性能影响**

```css
/* ❌ 不必要的继承 */
* {
    box-sizing: border-box;  /* 每个元素都要计算 */
}

/* ✅ 使用继承 */
html {
    box-sizing: border-box;
}
*, *::before, *::after {
    box-sizing: inherit;  /* 继承比重新设置快 */
}
```

**原因**: 继承值已经计算好,不需要重新计算。

**最佳实践**:

```css
/* 全局设置可继承属性 */
body {
    font-family: Arial, sans-serif;
    font-size: 16px;
    line-height: 1.5;
    color: #333;
}

/* 表单元素强制继承 */
button, input, select, textarea {
    font: inherit;
    color: inherit;
}

/* 特殊元素覆盖 */
h1, h2, h3 {
    line-height: 1.2;  /* 覆盖继承的1.5 */
}
```

上午十一点，你把博客网站的字体继承规则整理完成。所有文字元素现在都正确继承了`Arial`字体，包括表单元素。

你靠在椅背上，点了点头。CSS继承规则，终于搞清楚了。

---

**事故档案编号**:CSS-2024-1619
**影响范围**:样式继承、表单元素、全局样式设计
**根本原因**:不理解哪些属性可继承,哪些不可继承
**修复成本**:低(理解规则后使用inherit关键字)

这是CSS世界第19次被记录的继承链断裂事故。CSS继承像血缘传播——文本相关的特征会遗传(字体、颜色),但结构相关的特征不会(盒模型、布局)。表单元素像是"继承突变体",它们有自己的默认样式,不愿意继承祖先的字体设置。理解继承规则,就能用更少的代码实现一致的视觉效果。

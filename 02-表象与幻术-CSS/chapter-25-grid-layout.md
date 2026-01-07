《第25次记录:Grid法则事故 —— 二维网格的空间魔法》

---

## 事故现场

周五下午两点,你接到一个仪表板布局任务。办公室里很安静,大部分同事都去参加下午的技术分享会了。

你在做一个仪表板布局,想要一个侧边栏、顶部导航、内容区和底部。你尝试用flexbox嵌套:

```css
.dashboard {
    display: flex;
    flex-direction: column;
}

.top {
    display: flex;
}

.sidebar {
    flex: 0 0 250px;
}

.content {
    flex: 1;
}
```

代码越写越复杂,嵌套越来越深,还要处理各种边距对齐问题。

你听说CSS Grid可以解决这个问题,尝试改用Grid:

```css
.dashboard {
    display: grid;
    grid-template-columns: 250px 1fr;
    grid-template-rows: 60px 1fr 40px;
}
```

刷新页面——布局立刻清晰了!但你想让侧边栏跨越多行:

```css
.sidebar {
    grid-row: 1 / 4;  /* 不知道这是什么意思 */
}
```

结果侧边栏确实跨越了,但导航栏跑到右边去了。你尝试了`grid-template-areas`:

```css
.dashboard {
    display: grid;
    grid-template-areas:
        "sidebar header header"
        "sidebar main main"
        "sidebar footer footer";
}

.sidebar { grid-area: sidebar; }
.header { grid-area: header; }
```

现在布局完美了,但你困惑:"grid-template-columns的fr单位是什么?grid-area又是怎么工作的?"

---

## 深入迷雾

下午三点,你决定系统学习CSS Grid。前端架构师老王路过你的工位,看了一眼你的代码:"用Grid做这种布局会简单很多。"

你开始系统学习Grid。首先发现Grid是二维布局,同时控制行和列:

```css
/* Flexbox: 一维 */
.flex {
    display: flex;  /* 只控制一个方向 */
}

/* Grid: 二维 */
.grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;  /* 列 */
    grid-template-rows: 100px auto 50px;    /* 行 */
}
```

你测试了各种单位:

```css
/* px: 固定像素 */
grid-template-columns: 200px 300px 400px;

/* %: 百分比 */
grid-template-columns: 25% 50% 25%;

/* fr: fraction (比例单位) */
grid-template-columns: 1fr 2fr 1fr;  /* 1:2:1 */

/* auto: 自动(内容决定) */
grid-template-columns: auto 1fr auto;

/* minmax(): 最小最大值 */
grid-template-columns: minmax(200px, 1fr) 1fr 1fr;

/* repeat(): 重复模式 */
grid-template-columns: repeat(3, 1fr);  /* 等同于 1fr 1fr 1fr */
grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));  /* 自动填充 */
```

你测试了网格线命名和定位:

```css
/* 网格线从1开始编号 */
.container {
    display: grid;
    grid-template-columns: 100px 200px 100px;
    /*                     ^1    ^2    ^3    ^4 */
}

.item {
    grid-column-start: 2;
    grid-column-end: 4;    /* 占据第2-3列 */
    /* 简写: grid-column: 2 / 4; */
}
```

你发现了`grid-template-areas`的强大:

```css
.grid {
    display: grid;
    grid-template-areas:
        "header header header"
        "sidebar main main"
        "footer footer footer";
    grid-template-columns: 200px 1fr 1fr;
    grid-template-rows: 60px 1fr 40px;
}

.header { grid-area: header; }   /* 自动占据header区域 */
.sidebar { grid-area: sidebar; }
.main { grid-area: main; }
.footer { grid-area: footer; }
```

你测试了`gap`属性:

```css
.grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;  /* 行列间距都是20px */
    /* 或分别设置 */
    row-gap: 20px;
    column-gap: 10px;
}
```

---

## 真相浮现

下午四点半,你用Grid重构了整个仪表板布局,代码从150行减少到50行,而且更清晰易懂。老王走过来看了看:"不错,Grid就是专门解决这种二维布局的。"

你整理了Grid的完整规则:

**规则1:Grid的容器和子元素属性**

```css
/* 容器属性 */
display: grid;
grid-template-columns: <track-size> ...;
grid-template-rows: <track-size> ...;
grid-template-areas: "<area-name> ...";
gap: <row-gap> <column-gap>;
justify-items: start | end | center | stretch;
align-items: start | end | center | stretch;
justify-content: start | end | center | stretch | space-between | space-around | space-evenly;
align-content: start | end | center | stretch | space-between | space-around | space-evenly;

/* 子元素属性 */
grid-column: <start> / <end>;
grid-row: <start> / <end>;
grid-area: <name> | <row-start> / <col-start> / <row-end> / <col-end>;
justify-self: start | end | center | stretch;
align-self: start | end | center | stretch;
```

你创建了完整测试:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Grid布局测试</title>
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

        h3 {
            margin: 20px 0 10px;
        }

        code {
            background: #f5f5f5;
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 14px;
        }

        .grid {
            display: grid;
            border: 2px solid #333;
            background: #f0f0f0;
            min-height: 200px;
        }

        .item {
            background: lightblue;
            border: 2px solid #0066cc;
            padding: 20px;
            text-align: center;
        }

        /* 测试1: 基础3列布局 */
        .test1 {
            grid-template-columns: 1fr 1fr 1fr;
            gap: 10px;
            padding: 10px;
        }

        /* 测试2: 不同单位 */
        .test2 {
            grid-template-columns: 200px 1fr 2fr;
            gap: 10px;
            padding: 10px;
        }

        /* 测试3: repeat() */
        .test3 {
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            padding: 10px;
        }

        /* 测试4: 网格线定位 */
        .test4 {
            grid-template-columns: repeat(3, 1fr);
            grid-template-rows: repeat(3, 100px);
            gap: 10px;
            padding: 10px;
        }

        .test4 .item1 {
            grid-column: 1 / 3;  /* 占据第1-2列 */
            background: lightcoral;
        }

        .test4 .item2 {
            grid-row: 1 / 3;  /* 占据第1-2行 */
            background: lightgreen;
        }

        .test4 .item3 {
            grid-column: 2 / 4;
            grid-row: 2 / 4;
            background: lightyellow;
        }

        /* 测试5: grid-template-areas */
        .test5 {
            grid-template-areas:
                "header header header"
                "sidebar main main"
                "footer footer footer";
            grid-template-columns: 200px 1fr 1fr;
            grid-template-rows: 60px 1fr 40px;
            height: 400px;
            gap: 10px;
            padding: 10px;
        }

        .test5 .header {
            grid-area: header;
            background: lightcoral;
        }

        .test5 .sidebar {
            grid-area: sidebar;
            background: lightgreen;
        }

        .test5 .main {
            grid-area: main;
            background: lightblue;
        }

        .test5 .footer {
            grid-area: footer;
            background: lightyellow;
        }

        /* 测试6: 响应式Grid */
        .test6 {
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
            padding: 10px;
        }

        /* 测试7: justify和align */
        .test7 {
            grid-template-columns: repeat(3, 100px);
            grid-template-rows: repeat(2, 100px);
            justify-content: center;
            align-content: center;
            height: 400px;
            gap: 10px;
        }

        /* 测试8: 圣杯布局 */
        .test8 {
            grid-template-areas:
                "header header header"
                "nav content sidebar"
                "footer footer footer";
            grid-template-columns: 150px 1fr 150px;
            grid-template-rows: auto 1fr auto;
            height: 500px;
            gap: 10px;
            padding: 10px;
        }

        .test8 .header { grid-area: header; background: #f44336; color: white; }
        .test8 .nav { grid-area: nav; background: #2196F3; color: white; }
        .test8 .content { grid-area: content; background: #4CAF50; color: white; }
        .test8 .sidebar { grid-area: sidebar; background: #FF9800; color: white; }
        .test8 .footer { grid-area: footer; background: #9C27B0; color: white; }
    </style>
</head>
<body>
    <h1>CSS Grid完整测试</h1>

    <div class="demo">
        <h3>测试1: 基础3列等分</h3>
        <code>grid-template-columns: 1fr 1fr 1fr;</code>
        <div class="grid test1">
            <div class="item">1</div>
            <div class="item">2</div>
            <div class="item">3</div>
            <div class="item">4</div>
            <div class="item">5</div>
            <div class="item">6</div>
        </div>
    </div>

    <div class="demo">
        <h3>测试2: 混合单位</h3>
        <code>grid-template-columns: 200px 1fr 2fr;</code>
        <div class="grid test2">
            <div class="item">200px</div>
            <div class="item">1fr</div>
            <div class="item">2fr</div>
        </div>
    </div>

    <div class="demo">
        <h3>测试3: repeat()函数</h3>
        <code>grid-template-columns: repeat(4, 1fr);</code>
        <div class="grid test3">
            <div class="item">1</div>
            <div class="item">2</div>
            <div class="item">3</div>
            <div class="item">4</div>
        </div>
    </div>

    <div class="demo">
        <h3>测试4: 网格线定位</h3>
        <code>grid-column: 1 / 3 (占据2列)</code>
        <div class="grid test4">
            <div class="item item1">跨2列</div>
            <div class="item item2">跨2行</div>
            <div class="item item3">跨2行2列</div>
            <div class="item">4</div>
            <div class="item">5</div>
        </div>
    </div>

    <div class="demo">
        <h3>测试5: grid-template-areas</h3>
        <code>语义化区域命名</code>
        <div class="grid test5">
            <div class="item header">Header</div>
            <div class="item sidebar">Sidebar</div>
            <div class="item main">Main Content</div>
            <div class="item footer">Footer</div>
        </div>
    </div>

    <div class="demo">
        <h3>测试6: 响应式Grid (调整窗口大小查看效果)</h3>
        <code>repeat(auto-fill, minmax(150px, 1fr))</code>
        <div class="grid test6">
            <div class="item">1</div>
            <div class="item">2</div>
            <div class="item">3</div>
            <div class="item">4</div>
            <div class="item">5</div>
            <div class="item">6</div>
        </div>
    </div>

    <div class="demo">
        <h3>测试7: 对齐方式</h3>
        <code>justify-content: center; align-content: center;</code>
        <div class="grid test7">
            <div class="item">1</div>
            <div class="item">2</div>
            <div class="item">3</div>
            <div class="item">4</div>
            <div class="item">5</div>
            <div class="item">6</div>
        </div>
    </div>

    <div class="demo">
        <h3>测试8: 圣杯布局</h3>
        <div class="grid test8">
            <div class="item header">Header</div>
            <div class="item nav">Navigation</div>
            <div class="item content">Main Content</div>
            <div class="item sidebar">Sidebar</div>
            <div class="item footer">Footer</div>
        </div>
    </div>

    <script>
        // 分析Grid布局
        function analyzeGrid(selector) {
            const container = document.querySelector(selector);
            const computed = getComputedStyle(container);

            console.log(`${selector}:`);
            console.log('  grid-template-columns:', computed.gridTemplateColumns);
            console.log('  grid-template-rows:', computed.gridTemplateRows);
            console.log('  gap:', computed.gap);
        }

        analyzeGrid('.test1');
        analyzeGrid('.test2');
        analyzeGrid('.test5');
    </script>
</body>
</html>
```

---

## 世界法则

**世界规则 1:Grid vs Flexbox**

```css
/* Flexbox: 一维布局 */
.flex {
    display: flex;
    /* 只控制一个方向(行或列) */
    /* 适合: 导航栏、卡片列表、对齐 */
}

/* Grid: 二维布局 */
.grid {
    display: grid;
    /* 同时控制行和列 */
    /* 适合: 整体页面布局、仪表板、复杂网格 */
}
```

**选择建议**:
- 一维排列 → Flexbox
- 二维网格 → Grid
- 需要精确控制 → Grid
- 内容决定布局 → Flexbox

---

**世界规则 2:fr单位 (fraction,分数)**

```css
/* fr: 可用空间的比例 */

.grid {
    display: grid;
    width: 600px;
    grid-template-columns: 1fr 2fr 1fr;
}

/* 计算 */
总份数 = 1 + 2 + 1 = 4
第1列 = 600 * 1/4 = 150px
第2列 = 600 * 2/4 = 300px
第3列 = 600 * 1/4 = 150px

/* 混合单位 */
grid-template-columns: 200px 1fr 2fr;
/* 先分配固定值200px,剩余400px按1:2分配 */
第2列 = 400 * 1/3 ≈ 133px
第3列 = 400 * 2/3 ≈ 267px
```

---

**世界规则 3:repeat()函数**

```css
/* 基础重复 */
grid-template-columns: repeat(3, 1fr);
/* 等同于: 1fr 1fr 1fr */

/* 复杂模式重复 */
grid-template-columns: repeat(3, 100px 200px);
/* 等同于: 100px 200px 100px 200px 100px 200px */

/* auto-fill: 自动填充 */
grid-template-columns: repeat(auto-fill, 200px);
/* 尽可能多地放置200px列,直到填满容器 */

/* auto-fit: 自动适应 */
grid-template-columns: repeat(auto-fit, 200px);
/* 与auto-fill类似,但会拉伸最后一行/列 */

/* 配合minmax()实现响应式 */
grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
/* 每列最小200px,最大1fr,自动调整列数 */
```

---

**世界规则 4:网格线定位**

```css
/* 网格线从1开始编号 */
.grid {
    grid-template-columns: 100px 200px 100px;
    /*                     ^1    ^2    ^3    ^4 */
    grid-template-rows: 50px 100px;
    /*                  ^1   ^2    ^3 */
}

/* 方式1: 指定起止线 */
.item {
    grid-column-start: 1;
    grid-column-end: 3;    /* 占据第1-2列 */
    grid-row-start: 1;
    grid-row-end: 2;       /* 占据第1行 */
}

/* 方式2: 简写 */
.item {
    grid-column: 1 / 3;    /* start / end */
    grid-row: 1 / 2;
}

/* 方式3: span关键字 */
.item {
    grid-column: 1 / span 2;  /* 从第1线开始,跨越2列 */
    grid-row: span 2;          /* 跨越2行 */
}

/* 负数: 从末尾倒数 */
.item {
    grid-column: 1 / -1;  /* 从第1线到最后一线(占满) */
}
```

---

**世界规则 5:grid-template-areas语义化布局**

```css
.grid {
    display: grid;
    grid-template-areas:
        "header header header"
        "nav content sidebar"
        "footer footer footer";
    grid-template-columns: 150px 1fr 150px;
    grid-template-rows: 60px 1fr 40px;
}

/* 区域命名规则 */
✅ 必须形成矩形
✅ 同名区域会合并
✅ 用 . 表示空白

/* 示例: 非矩形无效 */
grid-template-areas:
    "header header sidebar"   /* ❌ sidebar不是矩形 */
    "nav content sidebar"
    "footer footer footer";

/* 正确: */
grid-template-areas:
    "header header header"
    "nav content sidebar"
    "footer footer footer";

/* 子元素使用 */
.header { grid-area: header; }
.nav { grid-area: nav; }
```

**优点**:
- 语义清晰,一目了然
- 易于维护和重构
- 支持媒体查询切换布局

---

**世界规则 6:gap间距**

```css
/* gap: <row-gap> <column-gap> */

/* 统一间距 */
.grid {
    gap: 20px;  /* 行列间距都是20px */
}

/* 分别设置 */
.grid {
    gap: 20px 10px;  /* 行间距20px, 列间距10px */
}

/* 单独设置 */
.grid {
    row-gap: 20px;
    column-gap: 10px;
}
```

**注意**: gap不会在边缘产生间距,只在网格线之间。

---

**世界规则 7:对齐属性**

```css
/* justify-*: 主轴(水平)对齐 */
/* align-*: 交叉轴(垂直)对齐 */

/* justify-items / align-items: 所有子元素在单元格内的对齐 */
.grid {
    justify-items: start | end | center | stretch;  /* 默认stretch */
    align-items: start | end | center | stretch;
}

/* justify-content / align-content: 整个网格在容器内的对齐 */
.grid {
    justify-content: start | end | center | stretch | space-between | space-around | space-evenly;
    align-content: start | end | center | stretch | space-between | space-around | space-evenly;
}

/* justify-self / align-self: 单个子元素的对齐 */
.item {
    justify-self: start | end | center | stretch;
    align-self: start | end | center | stretch;
}
```

**对比**:

| 属性 | 作用对象 | 方向 |
|-----|---------|------|
| justify-items | 所有子元素在单元格内 | 水平 |
| align-items | 所有子元素在单元格内 | 垂直 |
| justify-content | 整个网格在容器内 | 水平 |
| align-content | 整个网格在容器内 | 垂直 |
| justify-self | 单个子元素在单元格内 | 水平 |
| align-self | 单个子元素在单元格内 | 垂直 |

---

**事故档案编号**:CSS-2024-1625
**影响范围**:二维布局、页面结构、响应式设计
**根本原因**:尝试用Flexbox实现Grid才能胜任的布局
**修复成本**:低(Grid语法直观,迁移简单)

这是CSS世界第25次被记录的Grid法则事故。Grid是CSS的二维布局系统,同时控制行和列,用fr单位分配空间,用grid-template-areas实现语义化布局。Flexbox是一维流式布局,Grid是二维网格布局——选择正确的工具,就能用更少的代码实现更复杂的布局。

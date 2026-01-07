《第3次记录：秩序分界事故 —— Head 与 Body 的职责边界》

---

## 事故现场

周一上午八点半,你刚打开电脑,就看到监控告警:网站首页的加载速度突然变得极慢,白屏时间长达五秒。用户投诉邮件蜂拥而至。

办公室里已经有几个同事在讨论这个问题。窗外的阳光很刺眼,你拉上了窗帘,专注地打开Chrome DevTools的Network面板。

你看到一个令人费解的现象:一个 5KB 的JavaScript文件阻塞了整个页面渲染,它后面的所有资源——CSS、图片、甚至HTML结构本身——都在等待它下载完成。

"这不应该,"你皱眉,"我明明把这个脚本放在body底部了..."

你打开HTML源码，滚动到底部，确实，那个脚本在 `</body>` 标签之前。但当你滚动到顶部时，你的心沉了下去。

在 `<head>` 里面，有一个你遗忘了的 `<script>` 标签：

```html
<head>
    <meta charset="UTF-8">
    <title>首页</title>
    <link rel="stylesheet" href="styles.css">
    <script src="analytics.js"></script>  <!-- 这个！ -->
</head>
```

这个分析脚本是三个月前加的，当时你只是想"尽早初始化追踪"。但你没想到，它会成为整个页面的性能瓶颈。

更诡异的是，当你尝试在 `<head>` 中添加一个 `<h1>` 标签用于测试时：

```html
<head>
    <title>测试</title>
    <h1>这是标题</h1>  <!-- 这行会怎样？ -->
</head>
```

刷新页面，打开Elements面板——那个 `<h1>` 不见了。不，更准确地说，它被浏览器强制移到了 `<body>` 里面。

---

## 深入迷雾

上午九点,产品经理发来消息:"首页性能问题找到原因了吗?运营那边说用户流失率在上升。"

"正在排查,"你回复,手心开始冒汗。你开始系统地测试 `<head>` 和 `<body>` 的边界规则。

首先，你在 `<head>` 中放入各种内容：

```html
<head>
    <meta charset="UTF-8">
    <title>测试页面</title>

    <!-- 这些是允许的 -->
    <link rel="stylesheet" href="style.css">
    <script src="script.js"></script>
    <style>body { color: red; }</style>
    <meta name="viewport" content="width=device-width">

    <!-- 这些会被移走 -->
    <div>内容</div>
    <p>段落</p>
    <h1>标题</h1>
</head>
<body>
    <h2>正常内容</h2>
</body>
```

打开DevTools的Elements面板，你看到浏览器的自动修正：

```html
<head>
    <meta charset="UTF-8">
    <title>测试页面</title>
    <link rel="stylesheet" href="style.css">
    <script src="script.js"></script>
    <style>body { color: red; }</style>
    <meta name="viewport" content="width=device-width">
</head>
<body>
    <div>内容</div>  <!-- 被移到这里 -->
    <p>段落</p>      <!-- 被移到这里 -->
    <h1>标题</h1>    <!-- 被移到这里 -->
    <h2>正常内容</h2>
</body>
```

所有"可见内容"都被强制移到了 `<body>` 中。浏览器在解析HTML时，遇到不属于 `<head>` 的元素，会立即关闭 `<head>`，开启 `<body>`，然后把那些元素放进去。

但 `<script>` 是特殊的。你做了个实验：

```html
<head>
    <script>
        console.time('head-script');
        // 模拟耗时操作
        for (let i = 0; i < 1000000000; i++) {}
        console.timeEnd('head-script');
    </script>
</head>
<body>
    <h1>页面内容</h1>
</body>
```

刷新页面——白屏。整整三秒的白屏。然后控制台输出：`head-script: 3000ms`，页面内容才渲染出来。

你把同样的脚本移到 `<body>` 底部：

```html
<body>
    <h1>页面内容</h1>
    <script>
        console.time('body-script');
        for (let i = 0; i < 1000000000; i++) {}
        console.timeEnd('body-script');
    </script>
</body>
```

刷新页面——`<h1>` 立即显示，然后页面卡住三秒，控制台输出：`body-script: 3000ms`。

区别是巨大的。`<head>` 中的脚本会**阻塞整个页面的渲染**，而 `<body>` 底部的脚本只会在渲染完成后执行。

上午十点,性能优化组的老陈路过你的工位:"听说首页有性能问题?脚本放在head里了?"

"对,"你点点头,"我发现head里的脚本会阻塞整个页面渲染。"

"嗯,建议你用defer或async属性,"老陈说,"或者直接把非关键脚本移到body底部。"

你测试了 CSS 的加载：

```html
<head>
    <link rel="stylesheet" href="large-file.css">  <!-- 5MB的CSS -->
</head>
<body>
    <h1>内容</h1>
</body>
```

结果：白屏，直到CSS加载完成。CSS也会阻塞渲染。

但如果你把CSS放在 `<body>` 里呢？

```html
<body>
    <h1>这会先显示吗？</h1>
    <link rel="stylesheet" href="large-file.css">
    <div>这个呢？</div>
</body>
```

浏览器的行为让你惊讶：`<h1>` 仍然不会显示，直到CSS加载完成。虽然浏览器允许你在 `<body>` 中放 `<link>`，但它仍然会阻塞渲染。

---

## 真相浮现

你画了一张图，理清 `<head>` 和 `<body>` 的职责：

```
<head>：元数据和资源声明
  ├─ 必须有：<title>
  ├─ 可以有：<meta>, <link>, <style>, <script>, <base>
  └─ 不能有：可见内容元素（<div>, <p>, <h1>等）

<body>：可见内容
  ├─ 所有用户可见的HTML元素
  ├─ 也可以有：<script>, <style>（但不推荐）
  └─ 渲染顺序：从上到下
```

你制定了优化策略：

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width">
    <title>优化后的页面</title>

    <!-- CSS：保留在head，但做性能优化 -->
    <link rel="stylesheet" href="critical.css">  <!-- 关键CSS -->
    <link rel="preload" href="non-critical.css" as="style" onload="this.rel='stylesheet'">

    <!-- ❌ 不要在这里放JavaScript（除非必须） -->
    <!-- <script src="heavy.js"></script> -->

    <!-- ✅ 只放必须首先执行的脚本，且使用defer或async -->
    <script src="critical.js" defer></script>
</head>
<body>
    <header>
        <h1>网站标题</h1>
    </header>

    <main>
        <p>页面内容...</p>
    </main>

    <!-- ✅ 非关键JavaScript放在底部 -->
    <script src="analytics.js"></script>
    <script src="interactive.js"></script>
</body>
</html>
```

你测试了 `defer` 和 `async` 的区别：

```html
<head>
    <!-- 默认：阻塞解析和渲染 -->
    <script src="blocking.js"></script>

    <!-- async：异步下载，下载完立即执行（阻塞渲染） -->
    <script src="async.js" async></script>

    <!-- defer：异步下载，等待HTML解析完成后执行 -->
    <script src="defer.js" defer></script>
</head>
```

Network面板的时间线清楚地展示了区别：
- 默认脚本：下载时HTML解析停止
- `async` 脚本：下载时HTML继续解析，但下载完就立即执行（打断解析）
- `defer` 脚本：下载时HTML继续解析，等待 `DOMContentLoaded` 前执行

你重构了首页的资源加载：

1. 将所有非关键CSS通过 `preload` 实现异步加载
2. 将分析脚本从 `<head>` 移到 `<body>` 底部
3. 给必须在 `<head>` 中的脚本添加 `defer` 属性

中午十二点,你部署了修复版本。首页的白屏时间从 5 秒降到了 0.8 秒。

你给产品经理发了条消息:"性能问题已解决,白屏时间从5秒降到0.8秒。已部署到生产环境。"

下午一点,产品经理回复:"太好了!运营确认用户流失率已经恢复正常。总结一下这次问题的原因,发到技术群里,大家都学习一下。"

你靠在椅背上,长长地呼出一口气。head和body的职责边界,看似简单,但影响却如此深远。

---

## 世界法则

**世界规则 1：head 用于元数据，body 用于内容**

`<head>` 和 `<body>` 有严格的职责分工：

```html
<!-- head：不可见的元数据 -->
<head>
    <meta charset="UTF-8">        <!-- 字符编码 -->
    <title>页面标题</title>       <!-- 标签页标题 -->
    <link rel="stylesheet">       <!-- 样式表 -->
    <script>                      <!-- 脚本（不推荐） -->
    <meta name="description">     <!-- SEO元数据 -->
    <link rel="icon">             <!-- 网站图标 -->
</head>

<!-- body：用户可见的内容 -->
<body>
    <header>, <nav>, <main>, <article>, <section>, <div>, <p>, <h1-h6>...
    所有用户可以看到的元素
</body>
```

---

**世界规则 2：浏览器会自动修正错误的嵌套**

如果你在 `<head>` 中放入可见内容元素，浏览器会自动将其移到 `<body>`：

```html
<!-- 你写的代码 -->
<head>
    <title>测试</title>
    <div>内容</div>  <!-- ❌ 错误位置 -->
</head>

<!-- 浏览器自动修正为 -->
<head>
    <title>测试</title>
</head>
<body>
    <div>内容</div>  <!-- 自动移到这里 -->
</body>
```

---

**世界规则 3：head 中的脚本阻塞渲染**

`<head>` 中的 `<script>`（没有 `defer` 或 `async`）会**阻塞整个页面的渲染**：

```html
<head>
    <script src="heavy.js"></script>  <!-- 下载和执行期间，页面白屏 -->
</head>
<body>
    <h1>这个标题要等脚本执行完才显示</h1>
</body>
```

**性能影响**：
- 脚本下载时间：阻塞
- 脚本执行时间：阻塞
- 用户体验：长时间白屏

---

**世界规则 4：CSS 的加载位置影响渲染**

CSS应该放在 `<head>` 中，但会阻塞渲染：

```html
<head>
    <link rel="stylesheet" href="styles.css">  <!-- 阻塞渲染 -->
</head>
```

原因：浏览器需要等待CSSOM（CSS对象模型）构建完成，才能进行渲染，避免FOUC（Flash of Unstyled Content，无样式内容闪烁）。

如果CSS放在 `<body>` 中（不推荐），仍然会阻塞后续内容的渲染。

---

**世界规则 5：脚本的三种加载方式**

```html
<head>
    <!-- 1. 默认（同步）：阻塞HTML解析和渲染 -->
    <script src="script.js"></script>

    <!-- 2. async：异步下载，下载完立即执行 -->
    <script src="script.js" async></script>

    <!-- 3. defer：异步下载，HTML解析完后执行 -->
    <script src="script.js" defer></script>
</head>
```

**执行顺序**：
- 默认：按出现顺序，立即执行
- `async`：下载完就执行，顺序不确定
- `defer`：按出现顺序，在 `DOMContentLoaded` 前执行

**使用建议**：
- `defer`：适合大多数脚本（推荐）
- `async`：适合独立的第三方脚本（如分析工具）
- 默认：避免在 `<head>` 中使用

---

**世界规则 6：推荐的资源加载顺序**

```html
<!DOCTYPE html>
<html>
<head>
    <!-- 1. 字符编码（必须在最前面） -->
    <meta charset="UTF-8">

    <!-- 2. viewport（移动端必备） -->
    <meta name="viewport" content="width=device-width">

    <!-- 3. 标题（必须） -->
    <title>页面标题</title>

    <!-- 4. 关键CSS -->
    <link rel="stylesheet" href="critical.css">

    <!-- 5. 预加载非关键资源 -->
    <link rel="preload" href="font.woff2" as="font" crossorigin>

    <!-- 6. 必须的脚本（使用defer） -->
    <script src="app.js" defer></script>
</head>
<body>
    <!-- 页面内容 -->

    <!-- 7. 非关键脚本（放在底部） -->
    <script src="analytics.js"></script>
</body>
</html>
```

---

**事故档案编号**：DOM-2024-0803
**影响范围**：页面加载性能和用户体验
**根本原因**：误解 head 和 body 的职责边界，资源加载位置不当
**修复成本**：中等（需要调整资源加载位置和策略）

这是DOM世界第3次被记录的秩序分界事故。head 掌管信息，body 掌管内容。违背这一边界，世界的渲染就会陷入混乱。

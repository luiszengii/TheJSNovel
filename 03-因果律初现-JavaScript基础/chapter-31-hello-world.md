《第 31 次记录：Hello World 事故 —— 因果律首次启动》

## 白屏灾难

周一上午 9 点 47 分，你刷新页面，盯着那片刺眼的空白。

这是你的第一个独立项目——一个待办事项管理系统。产品经理上周就在强调：\"这是给重要客户演示的 Demo，一定要做好。\"你信心满满地接下了任务。HTML 结构写得很漂亮，CSS 样式也调得精致，JavaScript 逻辑看起来完美无缺。你甚至提前两天就写完了所有代码。

但现在，距离下午 2 点的客户演示只剩 4 个小时，页面上却只有一片白色，连一个按钮都看不到。

你打开 Chrome DevTools 控制台——没有任何错误。你检查 Network 面板——HTML、CSS、JavaScript 文件都成功加载了，状态码全是 200。你点开 Elements 面板查看 DOM 树——HTML 结构完整，输入框、按钮、列表容器都在那里。你切换到 Styles 面板——CSS 规则都正常应用了。

"这不可能..." 你喃喃自语。你明明看到 HTML 结构在那里，为什么页面上什么都不显示？

你开始怀疑是 CSS 的问题。你打开 `style.css`，检查每一条规则。没问题。你尝试给 body 加一个红色背景：`background: red;`——刷新页面，背景变红了，但内容还是不显示。

你又怀疑是 JavaScript 的问题。你打开 `app.js`，逻辑很简单：

```javascript
const input = document.querySelector('#task-input');
const addBtn = document.querySelector('#add-btn');
const taskList = document.querySelector('#task-list');

addBtn.addEventListener('click', () => {
    const task = input.value.trim();
    if (task) {
        const li = document.createElement('li');
        li.textContent = task;
        taskList.appendChild(li);
        input.value = '';
    }
});
```

逻辑完全正确。你甚至在代码审查时，小组长还夸你写得很规范。

但为什么页面是空白的？

## 诡异的 null

你决定从最基本的地方开始调试。你在 `app.js` 的第一行加了一句：

```javascript
console.log('JavaScript 已加载');
```

刷新页面——控制台输出了 "JavaScript 已加载"。好，说明 JavaScript 确实在执行。

你继续加调试代码：

```javascript
console.log('JavaScript 已加载');
console.log('addBtn:', document.querySelector('#add-btn'));
console.log('input:', document.querySelector('#task-input'));
console.log('taskList:', document.querySelector('#task-list'));
```

刷新页面。控制台输出让你愣住了：

```
JavaScript 已加载
addBtn: null
input: null
taskList: null
```

`null`？全是 `null`？

"这不可能！" 你几乎喊了出来。你立刻切换到 Elements 面板，展开 body 标签——输入框、按钮、列表容器都在那里，ID 也完全正确：`id="add-btn"`、`id="task-input"`、`id="task-list"`。

为什么 `querySelector` 找不到它们？

你开始怀疑是不是选择器写错了。你把 `#add-btn` 改成 `button`，刷新页面——还是 `null`。你尝试 `document.querySelectorAll('*')`，想看看 DOM 里到底有什么元素——输出只有 `<html>`、`<head>` 和几个 meta 标签。

"`<body>` 去哪了？" 你盯着控制台，感觉整个世界都不真实了。

## 时间的陷阱

上午 11 点，你已经尝试了二十几种方案。清空浏览器缓存——无效。换成 Firefox——无效。换成 Safari——无效。检查 HTML 文件编码——UTF-8，没问题。检查文件路径——也没问题。

你甚至怀疑是不是电脑中毒了，杀毒软件扫描了一遍——没有病毒。

同事小李路过你的工位，看到你焦躁地敲着键盘："怎么了？遇到什么问题了？"

"见鬼了，" 你指着屏幕，"querySelector 返回 null，但元素明明在 DOM 里。"

小李凑过来看了一眼你的代码，然后问了一个让你愣住的问题："你的 script 标签怎么放在 head 里？"

你转头看着他："script 标签...不是应该放在 head 里吗？"

小李笑了："你试试把 script 移到 body 底部。"

"这有什么区别吗？" 你困惑地问，但还是照做了。你打开 `index.html`，把 `<script src="app.js"></script>` 从 `<head>` 移到 `</body>` 前面：

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>待办事项</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <h1>我的待办事项</h1>
        <div class="input-group">
            <input id="task-input" type="text" placeholder="输入新任务...">
            <button id="add-btn">添加</button>
        </div>
        <ul id="task-list"></ul>
    </div>

    <script src="app.js"></script>
</body>
</html>
```

保存文件，刷新页面——

页面立刻"活"了过来！输入框出现了，按钮出现了，所有内容都正常显示了！控制台输出：

```
JavaScript 已加载
addBtn: <button id="add-btn">添加</button>
input: <input id="task-input" type="text" placeholder="输入新任务...">
taskList: <ul id="task-list"></ul>
```

所有元素都找到了！

你目瞪口呆地看着屏幕，完全不理解发生了什么。同样的代码，只是把 script 标签从 head 移到 body 底部，问题就解决了？

"为什么会这样？" 你转头问小李。

小李指着你的代码："因为浏览器是从上到下解析 HTML 的。"

## 浏览器的秘密

小李拉了把椅子坐下来，开始给你解释。

"浏览器解析 HTML 的过程是线性的，" 他说，"从第一行开始，一行一行往下读。当浏览器遇到 `<script>` 标签时，它会立即停止解析 HTML，先执行 JavaScript 代码，执行完了再继续解析后面的 HTML。"

他在纸上画了一个时间线：

```
时间线 (script在head中)
0ms:  开始解析 <html>
1ms:  解析 <head>
2ms:  遇到 <script src="app.js"></script>
3ms:  ⚠️ 暂停HTML解析，开始执行 app.js
4ms:  执行 document.querySelector('#add-btn')
5ms:  ❌ 返回 null (因为 <body> 还没被解析)
6ms:  继续解析 <body>
7ms:  解析 <button id="add-btn">
8ms:  按钮终于被创建，但 JavaScript 已经执行完了
```

"你看，" 小李指着时间线的第 5 毫秒，"当 JavaScript 执行 `querySelector` 的时候，浏览器还没有解析到 body 里的内容。在那一刻，DOM 树里根本就没有按钮，所以返回 null。"

你突然明白了。你盯着那个时间线，感觉自己过去的认知被颠覆了："所以...当 script 在 head 里时，body 的内容还不存在？"

"对，" 小李点头，"HTML 解析是有顺序的。script 标签在哪里，JavaScript 就在那个时刻执行。"

他又画了另一个时间线：

```
时间线 (script在body底部)
0ms:  开始解析 <html>
1ms:  解析 <head>
2ms:  解析 <body>
3ms:  解析 <button id="add-btn">
4ms:  按钮已创建，在DOM树中
5ms:  解析 <ul id="task-list">
6ms:  列表已创建，在DOM树中
7ms:  遇到 <script src="app.js"></script>
8ms:  ⚠️ 暂停HTML解析，开始执行 app.js
9ms:  执行 document.querySelector('#add-btn')
10ms: ✅ 返回按钮元素 (因为按钮已经被解析了)
```

"现在按钮已经在 DOM 树里了，" 小李说，"所以 `querySelector` 能找到它。"

你靠在椅背上，脑子里回想着刚才的调试过程。所有的现象都能解释了：为什么 `querySelectorAll('*')` 只能看到 head 里的元素，因为 body 还没被解析；为什么 Elements 面板能看到完整的 DOM 树，因为那是打开 DevTools 时看到的最终状态，而不是 JavaScript 执行时的状态。

"这就是为什么大家都说把 script 放在 body 底部，" 小李站起来，"这是最简单也最可靠的方式。"

## defer 与 async

中午吃饭时，你还在想这个问题。虽然把 script 放在 body 底部解决了问题，但你总觉得这样不太优雅。如果有很多 script 文件，都堆在 body 底部，代码会很乱。

下午，你搜索了 "script标签最佳实践"，看到了两个关键字：`defer` 和 `async`。

MDN 文档说：`defer` 属性告诉浏览器，这个脚本应该延迟到 HTML 解析完成后再执行。

你立刻试了一下。把 script 标签移回 head，但加上 `defer` 属性：

```html
<head>
    <meta charset="UTF-8">
    <title>待办事项</title>
    <link rel="stylesheet" href="style.css">
    <script src="app.js" defer></script>
</head>
```

刷新页面——完美！页面正常显示，功能正常工作。

你又看到了 `async` 属性，文档说它也不会阻塞 HTML 解析，但执行时机不同。你做了一个对比测试：

```html
<!-- 测试 defer -->
<script src="lib.js" defer></script>
<script src="app.js" defer></script>

<!-- 测试 async -->
<script src="analytics.js" async></script>
<script src="ads.js" async></script>
```

你在每个文件里加了 `console.log`，记录执行顺序：

```javascript
// lib.js
console.log('lib.js 执行');

// app.js
console.log('app.js 执行，依赖 lib.js');

// analytics.js
console.log('analytics.js 执行');

// ads.js
console.log('ads.js 执行');
```

刷新页面多次，观察控制台输出。你发现了规律：

**defer 的输出（每次都一样）**：
```
lib.js 执行
app.js 执行，依赖 lib.js
```

**async 的输出（每次都不同）**：
```
// 第一次
analytics.js 执行
ads.js 执行

// 第二次
ads.js 执行
analytics.js 执行

// 第三次
analytics.js 执行
ads.js 执行
```

你终于理解了它们的区别：

- `defer`：脚本按照它们在 HTML 中的顺序执行，保证依赖关系
- `async`：脚本加载完就立即执行，顺序不确定，适合独立的第三方脚本

## DOMContentLoaded 的真相

你还发现了一个有趣的现象。你在代码里加了事件监听：

```javascript
// 测试代码
console.log('1. JavaScript 开始执行');

document.addEventListener('DOMContentLoaded', () => {
    console.log('3. DOMContentLoaded 触发');
});

console.log('2. JavaScript 执行完毕');
```

你分别测试了三种情况：

**情况 1：script 在 body 底部（无 defer/async）**
```
1. JavaScript 开始执行
2. JavaScript 执行完毕
3. DOMContentLoaded 触发
```

**情况 2：script 在 head 中，有 defer**
```
1. JavaScript 开始执行
2. JavaScript 执行完毕
3. DOMContentLoaded 触发
```

**情况 3：script 在 head 中，有 async**
```
1. JavaScript 开始执行
2. JavaScript 执行完毕
// DOMContentLoaded 可能在 JavaScript 执行前或后触发，取决于脚本加载速度
```

你查阅文档，理解了 `DOMContentLoaded` 的时机：

- 普通 script 和 defer script 会阻塞 DOMContentLoaded，必须等它们执行完
- async script 不阻塞 DOMContentLoaded，可能在之前或之后执行

这解释了为什么很多框架都推荐监听 DOMContentLoaded 事件——这个事件触发时，DOM 已经完全解析好了，所有 defer 脚本也执行完了。

## 性能优化的启示

下午 2 点，客户演示顺利完成。产品经理走过来拍了拍你的肩膀："做得不错！"

但你心里清楚，今天遇到的问题暴露了你对浏览器工作原理的无知。晚上回到家，你整理了今天的收获，写了一份技术笔记。

你测试了不同 script 加载方式的性能影响。你创建了一个测试页面，用 Performance 面板录制了加载过程：

```html
<!-- 方案1: 所有script在head中，无defer -->
<head>
    <script src="lib1.js"></script>  <!-- 100ms -->
    <script src="lib2.js"></script>  <!-- 100ms -->
    <script src="app.js"></script>   <!-- 100ms -->
</head>
<!-- 总计: 300ms后才开始解析body，页面白屏 -->

<!-- 方案2: 所有script在head中，有defer -->
<head>
    <script src="lib1.js" defer></script>
    <script src="lib2.js" defer></script>
    <script src="app.js" defer></script>
</head>
<!-- body立即开始解析，script并行加载，HTML解析完成后按顺序执行 -->

<!-- 方案3: 所有script在body底部 -->
<body>
    <!-- 页面内容 -->
    <script src="lib1.js"></script>
    <script src="lib2.js"></script>
    <script src="app.js"></script>
</body>
<!-- body先解析，但script顺序加载，总时间长 -->
```

Performance 面板的时间线清楚地显示了差异：

- **方案 1**：300ms 白屏时间，用户体验差
- **方案 2**：body 立即渲染，script 并行加载，用户体验最好
- **方案 3**：body 立即渲染，但 script 顺序加载，略慢于方案 2

你终于明白了为什么现代前端都推荐使用 `defer`——它结合了性能和正确性的优势。

---

## 技术档案：JavaScript 执行时机与脚本加载策略

**规则 1：HTML 解析是线性的，script 会阻塞解析**

浏览器从上到下解析 HTML。遇到 `<script>` 标签时会暂停解析，执行 JavaScript，执行完后继续解析。

```html
<html>
<head>
    <script>
        // 此时只解析了 <html> 和 <head>
        console.log(document.body);  // null（body 还没被解析）
    </script>
</head>
<body>
    <!-- body 在 script 执行后才开始解析 -->
</body>
</html>
```

**原理解析**：
- 浏览器的 HTML Parser 是单线程的，按顺序处理文档
- `<script>` 可能修改 DOM 结构（如 `document.write()`），所以必须立即执行
- script 执行期间，HTML 解析完全停止，页面保持白屏
- 这种设计保证了 JavaScript 对 DOM 的修改是可预测的

**性能影响**：
- head 中的 script 每执行 100ms，页面白屏增加 100ms
- 多个 script 累计延迟：3 个 100ms 的 script = 300ms 白屏

**规则 2：script 位置决定 DOM 可访问范围**

JavaScript 执行时，只能访问已经解析过的 DOM 元素。script 之后的元素还不存在。

```html
<body>
    <div id="top">已存在</div>

    <script>
        // 此时 #top 已解析，#bottom 还不存在
        console.log(document.querySelector('#top'));     // <div id="top">
        console.log(document.querySelector('#bottom'));  // null
    </script>

    <div id="bottom">还不存在</div>
</body>
```

**时间线演示**：
```
t0: 解析 <body>
t1: 解析 <div id="top">，创建元素节点
t2: 遇到 <script>，暂停解析
t3: 执行 querySelector('#top') → 找到元素 ✅
t4: 执行 querySelector('#bottom') → 返回 null ❌
t5: 继续解析 <div id="bottom">，创建元素节点
```

**常见错误**：
```javascript
// ❌ 错误：script 在 head 中
<head>
    <script>
        const btn = document.querySelector('#btn');  // null
        btn.addEventListener('click', handleClick);  // TypeError: Cannot read property 'addEventListener' of null
    </script>
</head>
<body>
    <button id="btn">Click</button>
</body>

// ✅ 正确：script 在 body 底部
<body>
    <button id="btn">Click</button>
    <script>
        const btn = document.querySelector('#btn');  // <button id="btn">
        btn.addEventListener('click', handleClick);  // 正常工作
    </script>
</body>
```

**规则 3：defer 属性延迟执行到 HTML 解析完成后**

`defer` 告诉浏览器：异步加载脚本，但延迟到 HTML 解析完成后、DOMContentLoaded 之前执行。

```html
<head>
    <!-- 浏览器会: -->
    <!-- 1. 立即开始异步下载 lib.js 和 app.js -->
    <!-- 2. 继续解析 HTML，不阻塞 -->
    <!-- 3. HTML 解析完成后，按顺序执行 lib.js → app.js -->
    <script src="lib.js" defer></script>
    <script src="app.js" defer></script>
</head>
<body>
    <button id="btn">Click</button>
</body>
```

**执行时间线**：
```
t0:  开始解析 HTML
t1:  遇到 <script defer>，启动异步下载，继续解析 ⚡
t2:  解析 <body>
t3:  解析 <button id="btn">
t4:  HTML 解析完成 ✅
t5:  lib.js 下载完成
t6:  执行 lib.js
t7:  app.js 下载完成
t8:  执行 app.js
t9:  触发 DOMContentLoaded
```

**关键特性**：
- **不阻塞 HTML 解析**：script 下载时，HTML 继续解析
- **保证执行顺序**：多个 defer script 按 HTML 中的顺序执行
- **DOMContentLoaded 之前执行**：确保事件触发时脚本已运行
- **仅对外部脚本有效**：内联 script 不支持 defer

**适用场景**：
```html
<!-- ✅ 主应用代码 -->
<script src="app.js" defer></script>

<!-- ✅ 依赖库（按顺序加载） -->
<script src="react.js" defer></script>
<script src="react-dom.js" defer></script>
<script src="app.js" defer></script>

<!-- ✅ 需要操作 DOM 的脚本 -->
<script src="dom-manipulator.js" defer></script>
```

**规则 4：async 属性异步加载并立即执行**

`async` 告诉浏览器：异步加载脚本，加载完成后立即执行，不保证顺序。

```html
<head>
    <!-- async 脚本: -->
    <!-- 1. 异步下载 -->
    <!-- 2. 下载完立即执行（可能在 HTML 解析中途） -->
    <!-- 3. 不保证执行顺序 -->
    <script src="analytics.js" async></script>
    <script src="ads.js" async></script>
</head>
```

**执行时间线（不确定性）**：
```
可能的情况1:
t0: 开始解析 HTML
t1: 启动下载 analytics.js 和 ads.js
t2: analytics.js 下载完成
t3: ⚠️ 暂停 HTML 解析，执行 analytics.js
t4: 继续解析 HTML
t5: ads.js 下载完成
t6: ⚠️ 暂停 HTML 解析，执行 ads.js
t7: 继续解析 HTML

可能的情况2:
t0: 开始解析 HTML
t1: 启动下载 analytics.js 和 ads.js
t2: ads.js 先下载完成
t3: ⚠️ 暂停 HTML 解析，执行 ads.js
t4: 继续解析 HTML
t5: analytics.js 下载完成
t6: ⚠️ 暂停 HTML 解析，执行 analytics.js
```

**关键特性**：
- **不阻塞下载**：script 异步加载
- **会阻塞执行**：下载完成后立即暂停 HTML 解析并执行
- **不保证顺序**：谁先下载完谁先执行
- **不阻塞 DOMContentLoaded**：可能在 DOMContentLoaded 之前或之后执行

**适用场景**：
```html
<!-- ✅ 独立的第三方脚本（不依赖 DOM，不依赖其他脚本） -->
<script src="google-analytics.js" async></script>
<script src="facebook-pixel.js" async></script>

<!-- ❌ 依赖其他脚本的代码（执行顺序不确定） -->
<script src="jquery.js" async></script>
<script src="app.js" async></script>  <!-- 可能在 jquery.js 之前执行，导致错误 -->

<!-- ❌ 需要操作 DOM 的脚本（DOM 可能还没解析完） -->
<script src="dom-manipulator.js" async></script>  <!-- DOM 元素可能还不存在 -->
```

**规则 5：defer vs async vs 普通 script 的对比**

```javascript
// 性能对比测试
// 测试页面：10 个 script，每个 100KB，网络延迟 50ms

// 方案1: 普通 script（body 底部）
<body>
    <div>页面内容</div>
    <script src="1.js"></script>  <!-- 阻塞，等待下载+执行 -->
    <script src="2.js"></script>  <!-- 阻塞，等待下载+执行 -->
    <!-- ...8 个 script... -->
</body>
// 结果：页面快速渲染，但脚本顺序加载
// First Paint: 50ms ✅
// Interactive: 1000ms（10 * 100ms）

// 方案2: defer script（head）
<head>
    <script src="1.js" defer></script>  <!-- 并行下载 -->
    <script src="2.js" defer></script>  <!-- 并行下载 -->
    <!-- ...8 个 script... -->
</head>
// 结果：并行加载，HTML 解析不阻塞，按顺序执行
// First Paint: 50ms ✅
// Interactive: 150ms（最慢的 script 下载时间 + 执行时间）⚡

// 方案3: async script（head）
<head>
    <script src="analytics.js" async></script>
    <script src="ads.js" async></script>
</head>
// 结果：并行加载，加载完立即执行，可能阻塞渲染
// First Paint: 50-200ms（可能被 script 执行打断）
// Interactive: 不确定（取决于 script 下载和执行时机）
```

**对比表格**：
| 特性 | 普通 script | defer | async |
|------|-------------|-------|-------|
| HTML 解析 | ❌ 阻塞 | ✅ 不阻塞 | ✅ 不阻塞 |
| 执行时机 | 立即执行 | HTML 解析完成后 | 下载完立即执行 |
| 执行顺序 | ✅ 保证顺序 | ✅ 保证顺序 | ❌ 不保证顺序 |
| DOMContentLoaded | ⏸️ 阻塞 | ⏸️ 阻塞 | ✅ 不阻塞 |
| 适用场景 | body 底部小脚本 | 主应用代码 | 独立第三方脚本 |

**规则 6：DOMContentLoaded 的触发时机**

`DOMContentLoaded` 事件在 HTML 完全解析完成、所有 defer 脚本执行完成后触发。

```javascript
// 测试 DOMContentLoaded 时机
console.log('1. Script 开始执行');

document.addEventListener('DOMContentLoaded', () => {
    console.log('3. DOMContentLoaded 触发');
    console.log('此时 DOM 已完全解析，defer 脚本已执行');
});

console.log('2. Script 执行完毕');

// 输出顺序:
// 1. Script 开始执行
// 2. Script 执行完毕
// 3. DOMContentLoaded 触发
```

**触发条件**：
1. HTML 文档完全解析完成
2. 所有 defer 脚本执行完成
3. 不等待 async 脚本
4. 不等待图片、样式表等资源加载

**与 load 事件的区别**：
```javascript
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded: DOM 解析完成');
    // 此时 DOM 可操作，但图片可能还没加载
});

window.addEventListener('load', () => {
    console.log('load: 所有资源加载完成');
    // 此时图片、样式表、字体等全部加载完成
});

// 典型时间线:
// t0: HTML 解析完成 → DOMContentLoaded 触发
// t1: 图片加载中...
// t2: 样式表加载中...
// t3: 所有资源加载完成 → load 触发
```

**最佳实践**：
```javascript
// ✅ 推荐：使用 defer + DOMContentLoaded
<head>
    <script src="app.js" defer></script>
</head>

// app.js
document.addEventListener('DOMContentLoaded', () => {
    // 此时 DOM 已就绪，可以安全操作
    const btn = document.querySelector('#btn');
    btn.addEventListener('click', handleClick);
});

// ❌ 不推荐：直接执行（可能 DOM 还没就绪）
const btn = document.querySelector('#btn');  // 可能返回 null
btn.addEventListener('click', handleClick);  // TypeError
```

**规则 7：现代前端的脚本加载最佳实践**

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>最佳实践示例</title>

    <!-- ✅ CSS 放在 head 中（不阻塞解析） -->
    <link rel="stylesheet" href="styles.css">

    <!-- ✅ 关键的第三方库用 defer（需要保证顺序） -->
    <script src="https://cdn.example.com/react.js" defer></script>
    <script src="https://cdn.example.com/react-dom.js" defer></script>

    <!-- ✅ 主应用代码用 defer -->
    <script src="app.js" defer></script>

    <!-- ✅ 独立的分析脚本用 async（不依赖 DOM） -->
    <script src="https://www.google-analytics.com/analytics.js" async></script>

    <!-- ❌ 避免：普通 script 在 head 中 -->
    <!-- <script src="app.js"></script> -->
</head>
<body>
    <div id="root"></div>

    <!-- ❌ 避免：script 堆在 body 底部（除非有特殊原因） -->
    <!-- <script src="lib1.js"></script> -->
    <!-- <script src="lib2.js"></script> -->
</body>
</html>
```

**性能优化建议**：

1. **关键渲染路径优化**：
```html
<!-- 优先加载关键资源 -->
<link rel="preload" href="critical.css" as="style">
<link rel="preload" href="critical.js" as="script">

<!-- 延迟加载非关键资源 -->
<link rel="prefetch" href="non-critical.js">
```

2. **代码分割与懒加载**：
```javascript
// 动态 import，按需加载
document.querySelector('#btn').addEventListener('click', async () => {
    const module = await import('./heavy-module.js');
    module.doSomething();
});
```

3. **避免长任务阻塞主线程**：
```javascript
// ❌ 长任务阻塞渲染
for (let i = 0; i < 1000000; i++) {
    // 耗时操作
}

// ✅ 分片执行，避免阻塞
function processInChunks(data, chunkSize = 100) {
    let index = 0;

    function processChunk() {
        const end = Math.min(index + chunkSize, data.length);
        for (let i = index; i < end; i++) {
            // 处理数据
        }
        index = end;

        if (index < data.length) {
            requestIdleCallback(processChunk);  // 空闲时继续
        }
    }

    processChunk();
}
```

**规则 8：调试脚本加载问题的方法**

使用 Chrome DevTools 的 Performance 和 Network 面板排查脚本加载问题。

```javascript
// 1. 使用 Performance 面板录制页面加载
// 打开 DevTools → Performance → 点击录制 → 刷新页面 → 停止录制

// 在时间线上可以看到:
// - HTML 解析时间（Parse HTML）
// - Script 下载时间（蓝色）
// - Script 执行时间（黄色）
// - 渲染时间（紫色）

// 2. 检查 Script 执行时 DOM 状态
console.log('Script 执行时间:', Date.now());
console.log('document.readyState:', document.readyState);  // loading / interactive / complete
console.log('body 是否存在:', !!document.body);

// 3. 监听关键事件
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded 时间:', Date.now());
});

window.addEventListener('load', () => {
    console.log('load 时间:', Date.now());
});

// 4. 使用 MutationObserver 监控 DOM 变化
const observer = new MutationObserver((mutations) => {
    console.log('DOM 发生变化:', mutations);
});

observer.observe(document.documentElement, {
    childList: true,
    subtree: true
});
```

**常见问题诊断**：

```javascript
// 问题1: querySelector 返回 null
// 原因: script 在元素之前执行
// 解决: 使用 defer 或移到 body 底部

// 问题2: DOMContentLoaded 延迟触发
// 原因: defer 脚本执行时间过长
// 解决: 代码分割，减少关键路径上的脚本

// 问题3: 页面白屏时间长
// 原因: head 中的 script 阻塞 HTML 解析
// 解决: 使用 defer 或 async

// 问题4: 脚本执行顺序错乱
// 原因: 使用了 async
// 解决: 改用 defer 或确保脚本独立
```

---

**记录者注**:

JavaScript 的执行时机是前端开发的基础知识，但很多初学者都会在这里踩坑。关键在于理解浏览器的 HTML 解析是线性的——从上到下、从左到右，遇到 `<script>` 就暂停解析并执行 JavaScript，执行完后继续解析。

这导致了一个基本规则：script 执行时，只能访问它之前的 DOM 元素，之后的元素还不存在。传统的解决方案是把 script 放在 body 底部，但现代前端推荐使用 `defer` 属性——它既保证了脚本的执行顺序，又不阻塞 HTML 解析，还能让脚本并行下载，是性能和正确性的最佳平衡。

`async` 适合独立的第三方脚本（如统计代码），因为它们不依赖 DOM 也不依赖其他脚本。但对于需要操作 DOM 或依赖其他脚本的应用代码，`defer` 是更好的选择。

记住：**HTML 解析是线性的；script 在 head 会阻塞；defer 延迟到解析完成后；async 加载完立即执行；DOMContentLoaded 等待 defer 不等 async；使用 defer 是现代最佳实践**。理解脚本加载时机，就理解了前端性能优化的第一步。

---

**事故档案编号**: JS-2024-1631
**影响范围**: DOM 访问、页面加载、用户体验、性能优化
**根本原因**: script 在 head 中执行时，body 还未被解析，DOM 元素不存在
**修复成本**: 低（使用 defer 属性或移动 script 位置）
**预防措施**: 始终使用 defer 加载应用代码；监控 First Paint 和 Interactive 时间；使用 Performance 面板分析加载过程

这是 JavaScript 世界第 31 次被记录的 Hello World 事故。浏览器从上到下解析 HTML，遇到 script 会暂停解析并执行 JavaScript。如果 script 在 head 中访问 body 元素，会返回 null 因为元素还未被解析。现代解决方案：使用 `defer` 属性让脚本延迟到 HTML 解析完成后执行，既保证了正确性，又实现了并行下载的性能优化。理解 JavaScript 的执行时机，就理解了因果律如何在 DOM 世界中启动。

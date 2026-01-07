《第 32 次记录：执行顺序事故 —— 同步世界的线性因果》

## 白屏灾难现场

深夜十一点半，你盯着浏览器上那个转了五秒钟还在转的加载图标。鼠标悬停在页面上，点击没有任何反应，滚动条无法拖动，连开发者工具都无法打开。整个页面如同凝固在时间中。

这是一个数据分析页面。用户上传 CSV 文件，前端解析数据，生成统计图表。产品经理上周就在吹嘘："我们比竞品快，因为不需要上传服务器，纯前端处理！"但现在，测试环境里上传一个 500 行的文件，页面就卡死了。

五秒后，页面突然"复活"了。图表出现，数据正确，一切正常。但浏览器弹出了一个警告框："页面无响应，是否等待？"更糟的是，你的手机震了一下——产品经理发来消息："明天要给客户演示这个功能，能处理 1000 行数据吧？"

你看着那个 500 行就卡五秒的解析逻辑，手心开始冒汗。1000 行会卡多久？十秒？二十秒？客户会直接关闭浏览器吗？

你检查代码。解析函数很直接：一个 `for` 循环遍历所有行，每行用 `split` 分割字段，累加计算统计数据。没有复杂算法，就是基本的字符串操作。为了调试，你在循环里加了 `console.log`，想看看执行进度：

```javascript
function parseCSV(content) {
    const lines = content.split('\n');
    console.log('开始解析', lines.length, '行数据');

    for (let i = 0; i < lines.length; i++) {
        console.log('正在处理第', i, '行');
        const fields = lines[i].split(',');
        // 解析逻辑...
    }

    console.log('解析完成');
}
```

刷新页面，上传测试文件。控制台一片空白——等了五秒，500 条"正在处理第 X 行"的日志突然全部出现。"为什么日志不是一条条输出？"你困惑地皱起眉头。

更奇怪的是，这五秒里，你添加的 CSS 进度条动画也完全静止了。按理说，动画应该是浏览器负责渲染的，跟 JavaScript 代码无关啊？

窗外传来救护车的警笛声。你靠在椅背上，想起之前看到的一句话："JavaScript 是单线程的。"但你一直以为这只是个理论概念。现在，这个概念变成了一个真实的灾难。

单线程...到底意味着什么？

## 追踪调用栈的秘密

你打开一个空白的测试页面，决定从最基本的代码开始验证。你写了三行最简单的 `console.log`：

```javascript
console.log('第一行');
console.log('第二行');
console.log('第三行');
```

控制台按顺序输出：`第一行 → 第二行 → 第三行`。这很正常。然后你把第二行改成一个耗时循环：

```javascript
console.log('第一行');

// 模拟耗时操作
const start = Date.now();
while (Date.now() - start < 2000) {
    // 什么都不做，只是空转两秒
}

console.log('第三行');
```

刷新页面。浏览器整个界面卡住了两秒——鼠标点击无反应，滚动条冻结。然后两条日志同时出现。"原来如此..."你恍然大悟，循环在执行期间，整个程序都停下来等它。第三行的 `console.log` 必须等循环完成才能执行。

你想到了函数调用。你测试了嵌套调用的执行顺序：

```javascript
console.log('1. 主程序开始');

function A() {
    console.log('2. 函数 A 开始');
    B();
    console.log('4. 函数 A 结束');
}

function B() {
    console.log('3. 函数 B 执行');
}

A();
console.log('5. 主程序结束');
```

输出严格按照数字顺序：`1 → 2 → 3 → 4 → 5`。当主程序调用 `A` 时，主程序暂停，跳到 `A` 内部执行；`A` 调用 `B` 时，`A` 暂停，跳到 `B` 内部执行；`B` 执行完返回 `A`，`A` 继续执行；`A` 执行完返回主程序，主程序继续执行。

"JavaScript 一次只能做一件事。"你喃喃自语。但这个"一次只能做一件事"到底是怎么实现的？

你打开 Chrome DevTools 的 Performance 面板，录制了一次数据解析过程。时间线上显示了一个长达五秒的黄色长条，标注着"Script"。你点击展开，看到了调用栈（Call Stack）的详细信息：

```
parseCSV  ← 最上层（当前执行）
  └── onClick ← 中间层（事件处理）
      └── (anonymous) ← 底层（全局代码）
```

原来浏览器在内部维护了一个"调用栈"——每次调用函数，就把函数压入栈顶；函数执行完毕，就从栈顶弹出。而整个 JavaScript 引擎在任何时刻只能执行栈顶的那个函数。

你试着用 `console.trace()` 来可视化这个调用栈：

```javascript
function first() {
    console.log('first 开始');
    second();
    console.log('first 结束');
}

function second() {
    console.log('second 开始');
    console.trace('当前调用栈');
    console.log('second 结束');
}

first();
```

控制台输出了完整的调用栈信息：

```
second 开始
console.trace: 当前调用栈
    second  @ test.js:9
    first   @ test.js:4
    (anonymous) @ test.js:13
second 结束
first 结束
```

你看着这个输出，突然想到了一个问题：如果调用栈无限增长会怎么样？你写了一个递归函数：

```javascript
function recursion(n) {
    console.log('调用层级:', n);
    recursion(n + 1);  // 无限递归
}

recursion(1);
```

浏览器瞬间崩溃，控制台抛出错误：`Uncaught RangeError: Maximum call stack size exceeded`。调用栈爆了！

"原来调用栈是有大小限制的。"你记下这个发现。Chrome 的调用栈大约能容纳 1 万次左右的函数调用。

## 阻塞操作的真面目

你回到最初的问题：为什么数据解析会卡住整个页面？你测试了用户交互的情况。你写了一个 `prompt` 弹窗：

```javascript
console.log('开始');
const name = prompt('请输入姓名');
console.log('你好,', name);
console.log('结束');
```

页面弹出输入框。你没有立刻输入，而是尝试去点击页面上的其他按钮——完全没反应。你试着滚动页面——滚动条纹丝不动。你试着打开开发者工具——无法打开。整个浏览器页面冻结了，等待你输入。

你在输入框里输入"测试"，点击确定。页面立刻"复活"，所有操作恢复正常，控制台依次输出：

```
开始
你好, 测试
结束
```

"所有代码都在等 `prompt` 完成。"你明白了。JavaScript 引擎在执行 `prompt` 时，整个执行流程停在那里，后面的代码全部等待。这期间任何用户操作都无法响应，因为浏览器的主线程被 `prompt` 占用了。

你突然想到那个五秒卡顿的数据解析：500 行循环在执行时，JavaScript 引擎忙着做计算，无法处理其他任何事情——不能更新 UI，不能响应点击，不能输出日志，甚至不能渲染动画。所有操作都在队列里等待，直到循环结束，引擎才能继续处理其他事情。

"这就是单线程的同步执行。"你写下这句话。但问题是，怎么解决这个阻塞问题？

你搜索了一些资料，发现了几个可能的解决方案：

**方案 1：使用 `setTimeout` 分片执行**

```javascript
function parseCSVAsync(lines, index = 0) {
    const batchSize = 50;  // 每次处理 50 行

    for (let i = index; i < index + batchSize && i < lines.length; i++) {
        // 解析当前行
        const fields = lines[i].split(',');
        // 处理数据...
    }

    if (index + batchSize < lines.length) {
        // 让出控制权，0 毫秒后继续处理下一批
        setTimeout(() => parseCSVAsync(lines, index + batchSize), 0);
    } else {
        console.log('解析完成');
    }
}
```

你测试了这个方案。页面不再卡顿了！数据分批处理，每处理 50 行就通过 `setTimeout` 让出控制权，让浏览器有机会更新 UI、响应用户操作。虽然总处理时间稍微长了一点，但用户体验好了很多——进度条能动了，页面能点击了。

但你注意到一个问题：`setTimeout` 的延迟设置为 0 毫秒，但实际执行时间远远超过 0 毫秒。你用 Performance 面板查看，发现每个批次之间间隔大约 4-10 毫秒。

"为什么 `setTimeout(fn, 0)` 不是立刻执行？"你困惑了。你搜索资料，发现浏览器有一个最小延迟限制——HTML5 标准规定，`setTimeout` 的最小延迟是 4 毫秒。即使你设置 0 毫秒，实际也会延迟至少 4 毫秒。

**方案 2：使用 `requestAnimationFrame` 优化渲染**

```javascript
function parseCSVWithRAF(lines, index = 0) {
    const batchSize = 50;

    for (let i = index; i < index + batchSize && i < lines.length; i++) {
        const fields = lines[i].split(',');
        // 处理数据...
    }

    // 更新进度条
    updateProgress(index / lines.length * 100);

    if (index + batchSize < lines.length) {
        // 在下一帧渲染前继续处理
        requestAnimationFrame(() => parseCSVWithRAF(lines, index + batchSize));
    } else {
        console.log('解析完成');
    }
}
```

你测试了这个方案。进度条的动画变得非常流畅！原来 `requestAnimationFrame` 会在浏览器重绘之前执行回调，确保动画的帧率稳定在 60fps。

**方案 3：使用 Web Worker 真正并行**

同事路过时看到你在调试，说："用 Web Worker 啊，真正的多线程处理。"你查了资料，发现 Web Worker 可以在后台线程运行 JavaScript 代码，完全不阻塞主线程。

```javascript
// 主线程代码
const worker = new Worker('data-worker.js');

worker.postMessage({
    action: 'parse',
    data: csvContent
});

worker.onmessage = function(event) {
    const result = event.data;
    console.log('解析完成，结果:', result);
    renderChart(result);
};
```

```javascript
// data-worker.js
self.onmessage = function(event) {
    const { action, data } = event.data;

    if (action === 'parse') {
        const lines = data.split('\n');
        const result = [];

        // 在后台线程处理，不会阻塞主线程
        for (let i = 0; i < lines.length; i++) {
            const fields = lines[i].split(',');
            result.push(processLine(fields));
        }

        // 处理完成，发送结果回主线程
        self.postMessage(result);
    }
};
```

你测试了 Web Worker 版本。页面完全流畅，用户可以正常滚动、点击按钮，数据分析在后台悄悄完成。这才是真正的"非阻塞"处理！

## 调用栈可视化与调试

你继续深入研究调用栈的机制。你发现 Chrome DevTools 有一个强大的功能：在代码执行时暂停并查看调用栈。

你在解析函数里设置了一个断点：

```javascript
function parseCSV(content) {
    const lines = content.split('\n');
    debugger;  // 执行到这里会暂停

    for (let i = 0; i < lines.length; i++) {
        const fields = lines[i].split(',');
        // 处理...
    }
}
```

刷新页面，触发断点。DevTools 右侧的 Call Stack 面板显示了完整的调用链：

```
parseCSV           ← 当前函数（暂停点）
  onClick          ← 事件处理函数
    dispatchEvent  ← 浏览器事件分发
      (anonymous)  ← 全局代码
```

你可以点击每一层调用栈，查看该层的局部变量、作用域链、闭包信息。这让你清晰地看到了代码是如何一层层调用下来的。

你还发现了一个有趣的现象：调用栈底部总是有一个 `(anonymous)` 或 `(root)`，这是全局执行上下文，是所有代码的起点。

你测试了异步代码的调用栈：

```javascript
function start() {
    console.log('start 开始');
    setTimeout(delayed, 1000);
    console.log('start 结束');
}

function delayed() {
    console.trace('异步调用栈');
}

start();
```

一秒后，控制台输出：

```
console.trace: 异步调用栈
    delayed @ test.js:8
    (anonymous) @ test.js:14
```

你注意到一个重要的细节：`delayed` 的调用栈里没有 `start` 函数！这是因为 `setTimeout` 是异步的，`delayed` 的执行时间是在 `start` 函数早就执行完毕之后。调用栈已经清空了，`delayed` 是作为一个新的任务重新入栈的。

"异步代码的调用栈是独立的。"你记下这个发现。

## 性能分析与优化策略

你打开 Chrome DevTools 的 Performance 面板，录制了一次完整的数据解析过程。时间线上清晰地显示了各个阶段的耗时：

```
Main Thread Timeline:
├── Parse HTML         (50ms)
├── Evaluate Script    (20ms)
├── parseCSV Function  (5000ms)  ← 瓶颈！
│   └── 完全阻塞主线程
└── Render             (10ms)
```

那条长达 5 秒的黄色长条非常刺眼。你点击展开，看到了详细的函数调用树：

```
parseCSV (5000ms)
  └── for loop (4980ms)
      ├── split (2000ms)
      ├── parseFloat (1500ms)
      └── calculations (1480ms)
```

原来瓶颈在字符串的 `split` 操作和数字解析。你尝试优化这部分代码：

```javascript
// 优化前：每行都调用 split
for (let i = 0; i < lines.length; i++) {
    const fields = lines[i].split(',');
    data.push({
        name: fields[0],
        value: parseFloat(fields[1])
    });
}

// 优化后：手动解析，避免创建临时数组
for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const commaIndex = line.indexOf(',');
    const name = line.slice(0, commaIndex);
    const value = parseFloat(line.slice(commaIndex + 1));
    data.push({ name, value });
}
```

优化后，解析时间从 5 秒降到了 3.5 秒。但还是太慢。

你最终选择了 Web Worker 方案，并结合了分批处理：

```javascript
// 主线程：分批发送数据
function parseInBatches(lines) {
    const batchSize = 100;
    const batches = [];

    for (let i = 0; i < lines.length; i += batchSize) {
        batches.push(lines.slice(i, i + batchSize));
    }

    const worker = new Worker('parser-worker.js');
    let completed = 0;

    batches.forEach(batch => {
        worker.postMessage(batch);
    });

    worker.onmessage = function(event) {
        completed++;
        updateProgress(completed / batches.length * 100);

        if (completed === batches.length) {
            console.log('全部完成');
            worker.terminate();
        }
    };
}
```

这个方案完美解决了问题：页面流畅，进度条实时更新，用户体验极佳。

你测试了 1000 行数据——页面没有任何卡顿。你把测试数据量增加到 10000 行——依然流畅。产品经理走过来看了一眼，满意地点头："不错，明天演示就用这个版本。"

## 执行顺序的终极理解

凌晨三点，你靠在椅子上，整理了今天学到的所有知识。你在笔记本上写下了 JavaScript 执行顺序的核心规则：

**规则 1：JavaScript 是严格的单线程同步执行**

```javascript
// 代码按顺序执行，一次只做一件事
console.log('A');  // 1. 执行 A
console.log('B');  // 2. 等 A 完成，执行 B
console.log('C');  // 3. 等 B 完成，执行 C

// 输出严格按顺序：A → B → C
```

这不仅仅是理论——这是 JavaScript 引擎的核心实现机制。浏览器内部只有一个 JavaScript 主线程，所有同步代码都在这个线程上按顺序执行。

**规则 2：函数调用形成调用栈（Call Stack）**

```javascript
function first() {
    console.log('first 开始');
    second();  // 调用 second，first 暂停
    console.log('first 结束');
}

function second() {
    console.log('second 开始');
    third();   // 调用 third，second 暂停
    console.log('second 结束');
}

function third() {
    console.log('third 执行');
}

first();

// 输出顺序：
// first 开始 → second 开始 → third 执行 → second 结束 → first 结束

// 调用栈变化：
// [first]
// [first, second]
// [first, second, third]
// [first, second]  ← third 执行完弹出
// [first]          ← second 执行完弹出
// []               ← first 执行完弹出
```

调用栈是一个"后进先出"（LIFO）的数据结构。最后调用的函数最先执行完毕。Chrome DevTools 的 Call Stack 面板可以实时查看当前的调用栈状态。

**规则 3：耗时操作会阻塞整个主线程**

```javascript
// 阻塞操作：5 秒内页面完全冻结
function blockingTask() {
    const start = Date.now();
    while (Date.now() - start < 5000) {
        // 空循环，占用 CPU
    }
    console.log('任务完成');
}

blockingTask();
console.log('后续代码');  // 必须等 5 秒后才执行

// 阻塞期间：
// - UI 无法更新
// - 用户操作无响应
// - 动画停止
// - setTimeout 回调无法执行
```

这就是为什么数据解析会卡住页面。解决方案是使用异步操作（`setTimeout`、`requestAnimationFrame`、Web Worker）将任务分片或转移到后台线程。

**规则 4：调用栈有大小限制（约 10000 层）**

```javascript
// 递归过深会导致栈溢出
function recursion(n) {
    console.log(n);
    recursion(n + 1);  // 无限递归
}

recursion(1);
// RangeError: Maximum call stack size exceeded
```

Chrome 的调用栈大约能容纳 1 万次左右的函数调用。超过这个限制会抛出 `RangeError`。实际开发中要避免深度递归，或者使用尾递归优化、循环改写等技术。

**规则 5：同步代码优先于所有异步代码执行**

```javascript
console.log('1. 同步代码开始');

setTimeout(() => {
    console.log('3. setTimeout 回调');
}, 0);

console.log('2. 同步代码结束');

// 输出顺序：1 → 2 → 3
// 即使 setTimeout 延迟为 0，也必须等同步代码全部执行完
```

这是因为异步回调要等调用栈清空后才能执行。即使设置 `setTimeout(fn, 0)`，也不是立刻执行，而是在当前同步代码全部执行完毕后才执行。

**规则 6：`setTimeout` 有最小延迟限制（4ms）**

```javascript
// 设置 0 毫秒延迟
setTimeout(() => {
    console.log('实际延迟 > 0');
}, 0);

// 实际延迟至少 4 毫秒（HTML5 标准规定）
```

HTML5 标准规定，嵌套层级超过 5 层的 `setTimeout` 最小延迟为 4 毫秒。这是为了防止过度占用 CPU。

**规则 7：`console.log` 不会阻塞执行，但批量输出会延迟**

```javascript
for (let i = 0; i < 1000; i++) {
    console.log(i);  // 循环执行时不会立刻输出
}
// 循环结束后，1000 条日志一次性显示
```

这是因为 `console.log` 的输出是异步的，浏览器会批量处理日志以避免影响性能。所以你在循环里看到的日志是"批量显示"，而非实时输出。

**规则 8：浏览器主线程负责 JavaScript 执行和 UI 渲染**

```javascript
// JavaScript 执行会阻塞 UI 渲染
function heavyTask() {
    // 耗时 3 秒的计算
    for (let i = 0; i < 3000000000; i++) {}
}

heavyTask();  // 执行期间，页面无法重绘
```

这就是为什么 JavaScript 阻塞会导致动画停止、页面卡顿。浏览器的渲染引擎和 JavaScript 引擎共享主线程，JavaScript 执行时渲染引擎无法工作。

---

## 技术档案：JavaScript 执行顺序核心机制

**规则 1: 单线程顺序执行模型**

JavaScript 引擎使用单线程模型，所有同步代码按照书写顺序依次执行，一次只能执行一个任务。

```javascript
console.log('A');
console.log('B');
console.log('C');

// 执行流程：
// 1. 执行 A → 控制台输出 "A"
// 2. 执行 B → 控制台输出 "B"
// 3. 执行 C → 控制台输出 "C"

// 特性：
// - 顺序性：代码按照编写顺序执行
// - 排他性：前一行未完成，后一行不会开始
// - 阻塞性：耗时操作会阻塞后续所有代码
```

**规则 2: 调用栈机制（Call Stack）**

函数调用形成调用栈，采用"后进先出"（LIFO）的执行顺序。

```javascript
function A() {
    console.log('2. A 开始');
    B();
    console.log('4. A 结束');
}

function B() {
    console.log('3. B 执行');
}

console.log('1. 开始');
A();
console.log('5. 结束');

// 调用栈变化：
// 1. [全局代码]           → 输出 "1. 开始"
// 2. [全局代码, A]        → 输出 "2. A 开始"
// 3. [全局代码, A, B]     → 输出 "3. B 执行"
// 4. [全局代码, A]        → B 执行完弹出，输出 "4. A 结束"
// 5. [全局代码]           → A 执行完弹出，输出 "5. 结束"
// 6. []                   → 全局代码执行完，栈清空

// 查看调用栈：
function debug() {
    console.trace('当前调用栈');
}

A() { B() { debug() } }  // 调用栈：debug → B → A → global
```

**规则 3: 阻塞操作的本质与危害**

耗时同步操作会占用主线程，导致页面无响应。

```javascript
// 阻塞示例：页面冻结 5 秒
function blockingTask() {
    const start = Date.now();
    while (Date.now() - start < 5000) {
        // CPU 空转
    }
}

blockingTask();  // 执行期间：
// - UI 无法更新（按钮点击无效）
// - 无法滚动页面
// - 动画停止
// - 无法打开开发者工具
// - setTimeout 回调无法执行

// 浏览器主线程职责：
// 1. JavaScript 代码执行
// 2. UI 渲染（重绘、重排）
// 3. 事件处理（点击、滚动、输入）
// 4. 定时器回调

// JavaScript 执行时，其他任务全部等待
```

**规则 4: 使用 setTimeout 分片执行避免阻塞**

将耗时任务分片，通过 `setTimeout` 让出控制权，让浏览器有机会处理其他任务。

```javascript
// 优化前：阻塞 5 秒
function processData(data) {
    for (let i = 0; i < data.length; i++) {
        heavyComputation(data[i]);  // 每行耗时 10ms
    }
}

// 优化后：分片执行，不阻塞
function processDataAsync(data, batchSize = 50, index = 0) {
    const end = Math.min(index + batchSize, data.length);

    // 处理当前批次
    for (let i = index; i < end; i++) {
        heavyComputation(data[i]);
    }

    // 更新进度
    const progress = (end / data.length) * 100;
    updateProgressBar(progress);

    // 如果还有数据，继续下一批
    if (end < data.length) {
        setTimeout(() => {
            processDataAsync(data, batchSize, end);
        }, 0);  // 让出控制权
    } else {
        console.log('处理完成');
    }
}

// 效果对比：
// - 优化前：5 秒内页面完全冻结
// - 优化后：总时间稍长（5.2 秒），但页面保持响应
```

**规则 5: 使用 requestAnimationFrame 优化渲染**

`requestAnimationFrame` 在浏览器重绘前执行，确保动画流畅。

```javascript
function processWithRAF(data, index = 0) {
    const batchSize = 50;
    const end = Math.min(index + batchSize, data.length);

    for (let i = index; i < end; i++) {
        heavyComputation(data[i]);
    }

    // 更新 UI（会在下一帧渲染）
    updateProgressBar((end / data.length) * 100);

    if (end < data.length) {
        requestAnimationFrame(() => {
            processWithRAF(data, end);
        });
    }
}

// requestAnimationFrame vs setTimeout:
// - requestAnimationFrame：保证 60fps，与渲染同步
// - setTimeout：不保证帧率，可能导致掉帧
```

**规则 6: 使用 Web Worker 实现真正的并行**

Web Worker 运行在独立线程，不阻塞主线程。

```javascript
// 主线程
const worker = new Worker('worker.js');

worker.postMessage({
    action: 'parse',
    data: largeDataset
});

worker.onmessage = function(event) {
    const result = event.data;
    console.log('Worker 返回结果:', result);
    updateUI(result);
};

// worker.js（独立线程）
self.onmessage = function(event) {
    const { action, data } = event.data;

    if (action === 'parse') {
        // 耗时计算，不阻塞主线程
        const result = heavyComputation(data);
        self.postMessage(result);
    }
};

// Web Worker 限制：
// - 无法访问 DOM
// - 无法访问 window 对象
// - 通过 postMessage 通信
```

**规则 7: 调用栈大小限制与栈溢出**

调用栈有大小限制（Chrome 约 10000 层），超过会抛出 `RangeError`。

```javascript
// 递归过深导致栈溢出
function recursion(n) {
    if (n > 10000) return;
    recursion(n + 1);
}

recursion(1);  // RangeError: Maximum call stack size exceeded

// 解决方案 1：尾递归优化（需浏览器支持）
function tailRecursion(n, acc = 0) {
    if (n === 0) return acc;
    return tailRecursion(n - 1, acc + n);  // 尾调用
}

// 解决方案 2：改用循环
function loop(n) {
    let result = 0;
    for (let i = 1; i <= n; i++) {
        result += i;
    }
    return result;
}

// 解决方案 3：使用 setTimeout 分片
function recursionAsync(n, callback) {
    if (n === 0) {
        callback();
    } else {
        setTimeout(() => {
            // 处理当前层级
            recursionAsync(n - 1, callback);
        }, 0);
    }
}
```

**规则 8: 性能分析与调试技巧**

使用 Chrome DevTools 分析执行顺序和性能瓶颈。

```javascript
// 1. 使用 console.trace 查看调用栈
function debug() {
    console.trace('当前调用栈');
}

// 2. 使用 Performance 面板分析耗时
// 录制 → 执行操作 → 停止录制 → 查看时间线

// 3. 使用 debugger 断点查看执行流程
function parse(data) {
    debugger;  // 暂停执行，查看 Call Stack
    for (let i = 0; i < data.length; i++) {
        process(data[i]);
    }
}

// 4. 测量代码执行时间
console.time('解析数据');
parseData(largeDataset);
console.timeEnd('解析数据');  // 输出：解析数据: 3215.234ms

// 5. 使用 console.count 统计执行次数
function loop() {
    for (let i = 0; i < 100; i++) {
        console.count('循环次数');
    }
}
```

---

**记录者注**:

JavaScript 的单线程同步执行模型是理解整个语言的基础。每一行代码都按照严格的顺序执行，前一行未完成，后一行不会开始。函数调用形成调用栈，采用"后进先出"的执行顺序。耗时操作会阻塞整个主线程，导致页面无响应。

关键在于理解"单线程"的深层含义——浏览器的主线程同时负责 JavaScript 执行和 UI 渲染，JavaScript 代码执行期间，渲染引擎无法工作。这就是为什么耗时同步操作会导致页面卡顿、动画停止、用户操作无响应。

解决阻塞问题的核心思路是"让出控制权"——通过 `setTimeout` 分片执行，通过 `requestAnimationFrame` 优化渲染，通过 Web Worker 将计算转移到后台线程。实际开发中要根据任务特性选择合适的方案：UI 更新用 `requestAnimationFrame`，后台计算用 Web Worker，简单分片用 `setTimeout`。

记住：**JavaScript 是单线程同步执行；函数调用形成调用栈（LIFO）；耗时操作阻塞主线程；使用异步机制让出控制权；Web Worker 实现真正并行；调用栈有大小限制；性能分析使用 DevTools**。理解执行顺序是掌握 JavaScript 异步编程、性能优化、错误调试的基础。

---

**事故档案编号**: JS-2024-1632
**影响范围**: 代码执行流程、性能、用户体验
**根本原因**: 不理解单线程同步执行模型，耗时操作阻塞主线程
**修复成本**: 中等（需学习异步编程、Web Worker、性能优化）
**预防措施**: 避免耗时同步操作，使用分片执行、Web Worker；监控主线程阻塞时间

这是 JavaScript 世界第 32 次被记录的执行顺序事故。JavaScript 采用单线程同步执行模型——代码按顺序执行，一次只能做一件事，函数调用形成调用栈，耗时操作会阻塞后续代码和 UI 渲染。理解同步执行，就理解了 JavaScript 因果律的线性本质——每个结果都由前一个原因直接导致，时间在这里是一条不可逆的单行道。但通过异步机制和多线程技术，我们可以在这条单行道上创造出"并行"的幻觉，让用户体验更加流畅。

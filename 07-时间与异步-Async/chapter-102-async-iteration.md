《第 102 次记录: 流式数据危机 —— 异步迭代的时间流》

---

## 实时监控的性能瓶颈

周一上午九点, 你盯着 CPU 使用率图表, 额头渗出了汗珠。

这是上周刚上线的实时日志监控系统。系统需要从多个服务器持续拉取日志流, 然后在前端展示。产品经理对这个功能很满意, 但运维部门今天早上发来了一个致命的报告:

"页面内存占用持续增长, 运行 2 小时后已经达到 1.2GB, 最终导致浏览器崩溃。"

你打开代码, 看到了上周的实现:

```javascript
async function loadAllLogs(serverId) {
    const logs = [];

    // 获取所有日志文件列表
    const files = await fetchLogFileList(serverId);

    // 加载所有文件
    for (const file of files) {
        const content = await fetchLogFile(serverId, file);
        logs.push(...content);
    }

    return logs;  // 返回所有日志
}

// 使用
const allLogs = await loadAllLogs('server-001');
displayLogs(allLogs);
```

"看起来很合理啊, " 你想, "异步加载, 然后显示。有什么问题?"

但你突然意识到一个严重的问题: **这个系统需要等待所有日志加载完成, 然后一次性处理**。如果日志文件有几百个, 每个文件有几千行... 内存当然会爆炸。

"如果能边加载边处理就好了, " 你喃喃自语, "就像读取文件流一样, 一行行处理, 而不是全部加载到内存..."

---

## Generator 方案的尝试

上午十点, 你想起了上周学习的 Generator 函数。

"Generator 可以暂停执行, 逐步返回值, " 你想, "也许可以用它来解决内存问题?"

你快速写下了新代码:

```javascript
function* loadLogsGenerator(serverId) {
    const files = getLogFileListSync(serverId);  // 同步获取文件列表

    for (const file of files) {
        const content = readLogFileSync(serverId, file);  // 同步读取文件
        yield* content;  // 逐行返回
    }
}

// 使用
const logGen = loadLogsGenerator('server-001');

for (const log of logGen) {
    displayLog(log);  // 边生成边显示
}
```

"这样就不会一次性加载所有日志了, " 你满意地说。

但当你运行代码时, 浏览器直接卡死了。

"什么?!" 你困惑, "为什么会卡死?"

你打开 DevTools, 看到了明显的问题: **所有的文件读取操作都是同步的**, 主线程被完全阻塞。用户界面无法响应, 浏览器显示 "页面无响应"。

"不行, " 你意识到, "文件读取必须是异步的。但 Generator 的 yield 不能处理 Promise..."

你陷入了困境。

---

## 异步 Generator 的发现

上午十一点, 你在 MDN 上搜索 "async generator"。

"等等, " 你的眼睛亮了, "有 `async function*`?"

你看到了文档中的示例:

```javascript
async function* asyncGenerator() {
    yield 1;
    yield 2;
    yield 3;
}
```

"async 和 Generator 可以结合!" 你惊讶, "那 yield 就可以处理 Promise 了?"

你立刻测试:

```javascript
async function* loadLogsAsync(serverId) {
    // 异步获取文件列表
    const files = await fetchLogFileList(serverId);

    for (const file of files) {
        console.log('开始加载文件:', file);

        // 异步读取文件
        const content = await fetchLogFile(serverId, file);

        // 逐行 yield
        for (const log of content) {
            yield log;
        }

        console.log('文件加载完成:', file);
    }
}
```

"现在试试怎么使用, " 你想。

你尝试了普通的 for...of 循环:

```javascript
const logGen = loadLogsAsync('server-001');

for (const log of logGen) {  // 会报错吗?
    displayLog(log);
}
```

浏览器立刻报错:

```
TypeError: logGen is not iterable
```

"什么?!" 你困惑, "async Generator 返回的不是可迭代对象?"

你打印了 `logGen`:

```javascript
console.log(logGen);
// Object [AsyncGenerator] {}
```

"AsyncGenerator?" 你盯着输出, "不是普通的 Generator?"

---

## for-await-of 的顿悟

中午十二点, 你继续查阅 MDN, 找到了关键信息。

"`AsyncGenerator` 对象不能用 `for...of` 遍历, " 你读着文档, "必须使用 `for await...of`。"

你修改代码:

```javascript
async function displayAllLogs(serverId) {
    const logGen = loadLogsAsync(serverId);

    // 使用 for await...of
    for await (const log of logGen) {
        displayLog(log);
    }

    console.log('所有日志加载完成');
}

// 使用
displayAllLogs('server-001');
```

你运行代码, 屏幕上的输出让你兴奋:

```
开始加载文件: 2024-01-01.log
[显示第一个文件的日志...]
文件加载完成: 2024-01-01.log

开始加载文件: 2024-01-02.log
[显示第二个文件的日志...]
文件加载完成: 2024-01-02.log

...
```

"太棒了!" 你说, "日志边加载边显示, 内存占用稳定在 50MB, 完全不会爆炸!"

你打开 Performance 面板, 验证了内存曲线——平稳的锯齿状, 加载一个文件后内存上升, 处理完后立即下降。没有持续增长的趋势。

"这就是流式处理的威力, " 你恍然大悟, "`for await...of` 让我们可以异步地、逐个处理数据, 而不是等待全部加载完成。"

---

## 异步迭代器协议

下午两点, 你开始深入研究 `for await...of` 的机制。

"既然普通 Generator 实现了迭代器协议, " 你想, "异步 Generator 应该实现了异步迭代器协议?"

你测试了一下:

```javascript
async function* test() {
    yield 1;
    yield 2;
}

const gen = test();

console.log(typeof gen.next);  // 'function'
console.log(typeof gen[Symbol.asyncIterator]);  // 'function'

// Symbol.asyncIterator 返回自己
console.log(gen[Symbol.asyncIterator]() === gen);  // true
```

"果然, " 你说, "异步 Generator 实现了 `Symbol.asyncIterator` 方法。"

你又手动调用 `next()` 方法:

```javascript
async function* test() {
    yield 1;
    yield 2;
}

const gen = test();

const result1 = await gen.next();
console.log(result1);  // { value: 1, done: false }

const result2 = await gen.next();
console.log(result2);  // { value: 2, done: false }

const result3 = await gen.next();
console.log(result3);  // { value: undefined, done: true }
```

"等等, " 你注意到一个关键细节, "`gen.next()` 返回的是 Promise! 需要用 `await` 才能拿到结果。"

你画了对比图:

```
普通 Generator:
next() → { value, done }  (立即返回)

异步 Generator:
next() → Promise<{ value, done }>  (返回 Promise, 需要 await)
```

"所以 `for await...of` 的本质, " 你总结, "是自动处理这些 Promise, 等待每个 `next()` 完成, 然后取出 `value`。"

---

## 自定义异步迭代器

下午三点, 你尝试手动实现一个异步迭代器。

"既然知道了协议, " 你想, "应该可以不用 async Generator, 直接实现 `Symbol.asyncIterator` 方法?"

你写下了测试代码:

```javascript
const asyncIterable = {
    async *[Symbol.asyncIterator]() {
        yield 1;
        yield 2;
        yield 3;
    }
};

// 使用
for await (const num of asyncIterable) {
    console.log(num);
}
// 输出: 1, 2, 3
```

"这是简写方式, " 你说, "用 async Generator 方法实现。但也可以手动实现..."

你写下了完整的实现:

```javascript
const asyncIterable = {
    [Symbol.asyncIterator]() {
        let count = 0;

        return {
            async next() {
                if (count < 3) {
                    count++;
                    // 模拟异步操作
                    await new Promise(resolve => setTimeout(resolve, 100));
                    return { value: count, done: false };
                }
                return { value: undefined, done: true };
            }
        };
    }
};

// 使用
for await (const num of asyncIterable) {
    console.log(num);
}
// 每隔 100ms 输出: 1, 2, 3
```

"完美!" 你说, "异步迭代器的核心就是 `next()` 方法返回 `Promise<{value, done}>`。"

你立刻想到了一个实际应用——分页数据加载:

```javascript
class PaginatedAPI {
    constructor(apiUrl) {
        this.apiUrl = apiUrl;
    }

    async *[Symbol.asyncIterator]() {
        let page = 1;
        let hasMore = true;

        while (hasMore) {
            console.log(`加载第 ${page} 页`);

            const response = await fetch(`${this.apiUrl}?page=${page}`);
            const data = await response.json();

            // 逐个 yield 数据项
            for (const item of data.items) {
                yield item;
            }

            hasMore = data.hasMore;
            page++;
        }
    }
}

// 使用
const api = new PaginatedAPI('/api/users');

for await (const user of api) {
    console.log('处理用户:', user.name);
    // 边加载边处理, 不会一次性加载所有页面
}
```

"这就是流式处理的威力, " 你满意地说, "API 自动分页加载, 用户代码只需要简单的 for await...of。"

---

## 异步生成器的实战应用

下午四点, 你开始重构日志监控系统。

"现在我知道了异步迭代的原理, " 你想, "可以写一个更完善的日志流处理系统。"

你写下了新的实现:

```javascript
class LogStream {
    constructor(serverId) {
        this.serverId = serverId;
    }

    async *[Symbol.asyncIterator]() {
        // 获取日志文件列表
        const files = await this.fetchLogFileList();

        for (const file of files) {
            console.log(`📁 加载文件: ${file.name}`);

            // 获取文件流
            const stream = await this.fetchLogStream(file);

            // 逐行处理
            for await (const line of stream) {
                // 解析日志行
                const log = this.parseLogLine(line);

                // 过滤无效日志
                if (log && log.level !== 'debug') {
                    yield log;
                }
            }

            console.log(`✅ 文件完成: ${file.name}`);
        }
    }

    async fetchLogFileList() {
        const response = await fetch(`/api/logs/${this.serverId}/files`);
        return response.json();
    }

    async *fetchLogStream(file) {
        const response = await fetch(`/api/logs/${this.serverId}/${file.name}`);
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();

            if (done) {
                if (buffer) yield buffer;  // 处理最后的残留数据
                break;
            }

            buffer += decoder.decode(value, { stream: true });

            // 按行分割
            const lines = buffer.split('\n');
            buffer = lines.pop();  // 保留不完整的行

            for (const line of lines) {
                if (line.trim()) {
                    yield line;
                }
            }
        }
    }

    parseLogLine(line) {
        try {
            return JSON.parse(line);
        } catch {
            return null;
        }
    }
}

// 使用
async function displayLogs(serverId) {
    const stream = new LogStream(serverId);
    const logContainer = document.querySelector('#logs');

    for await (const log of stream) {
        // 边加载边显示
        const logElement = createLogElement(log);
        logContainer.appendChild(logElement);

        // 限制显示数量, 避免 DOM 节点过多
        if (logContainer.children.length > 1000) {
            logContainer.removeChild(logContainer.firstChild);
        }
    }

    console.log('日志流处理完成');
}

// 启动
displayLogs('server-001');
```

你测试了新系统, 结果让你满意:

- ✅ 内存占用稳定在 50MB (之前 1.2GB)
- ✅ 页面响应流畅, 可以实时交互
- ✅ 支持中断加载 (用户可以随时停止)
- ✅ 支持过滤和转换 (在流中处理, 不占用额外内存)

"这就是异步迭代的力量, " 你说, "把大数据流分解成小块, 逐个处理, 内存占用可控。"

---

## 错误处理与资源清理

下午五点, 你发现了一个潜在的问题。

"如果异步迭代过程中出错了怎么办?" 你想。

你测试了错误场景:

```javascript
async function* errorGenerator() {
    yield 1;
    yield 2;
    throw new Error('异步生成器错误');
    yield 3;  // 不会执行
}

try {
    for await (const num of errorGenerator()) {
        console.log(num);
    }
} catch (error) {
    console.error('捕获到错误:', error.message);
}
```

输出:

```
1
2
捕获到错误: 异步生成器错误
```

"错误会传播到外层, " 你说, "可以用 try...catch 捕获。"

但你又想到了资源清理的问题:

```javascript
async function* fileStream(filename) {
    const file = await openFile(filename);

    try {
        // 读取文件内容
        for (const chunk of file) {
            yield chunk;
        }
    } finally {
        // 确保文件被关闭
        await closeFile(file);
        console.log('文件已关闭');
    }
}
```

"finally 可以确保资源清理, " 你说, "即使迭代中断或出错, 文件也会被关闭。"

你测试了中断场景:

```javascript
const stream = fileStream('large-file.txt');

for await (const chunk of stream) {
    console.log(chunk);

    if (chunk.includes('STOP')) {
        break;  // 提前退出
    }
}

// 输出: 文件已关闭
```

"完美!" 你说, "即使 break 提前退出, finally 也会执行, 资源被正确清理。"

---

## 异步迭代器辅助方法

下午六点, 你发现异步迭代器还有一些辅助方法。

你查阅文档, 发现异步生成器对象有 `return()` 和 `throw()` 方法:

```javascript
async function* test() {
    try {
        yield 1;
        yield 2;
        yield 3;
    } finally {
        console.log('清理资源');
    }
}

const gen = test();

console.log(await gen.next());  // { value: 1, done: false }

// 提前结束
console.log(await gen.return('手动结束'));
// 清理资源
// { value: '手动结束', done: true }

console.log(await gen.next());  // { value: undefined, done: true }
```

"return() 可以提前结束迭代, " 你说, "并触发 finally 清理。"

你又测试了 throw() 方法:

```javascript
async function* test() {
    try {
        yield 1;
        yield 2;
        yield 3;
    } catch (error) {
        console.log('生成器内部捕获:', error.message);
        yield 'error';
    }
}

const gen = test();

console.log(await gen.next());  // { value: 1, done: false }

// 向生成器内部抛入错误
console.log(await gen.throw(new Error('外部错误')));
// 生成器内部捕获: 外部错误
// { value: 'error', done: false }

console.log(await gen.next());  // { value: undefined, done: true }
```

"throw() 可以从外部向生成器内部抛入错误, " 你总结, "内部的 try...catch 可以捕获。"

---

## 你的异步迭代笔记本

晚上八点, 你整理了今天的收获。

你在笔记本上写下标题: "异步迭代 —— 时间流的遍历"

### 核心洞察 #1: 异步 Generator 函数

你写道:

"异步 Generator 结合了 async 和 Generator 的特性:

```javascript
async function* asyncGenerator() {
    // 可以使用 await
    const data = await fetchData();

    // 可以使用 yield
    yield data;

    // yield 也可以直接 yield Promise
    yield fetchMore();
}
```

核心特性:
- `async function*` 定义异步生成器
- 可以在函数内部使用 `await`
- `yield` 表达式可以暂停执行
- 返回 `AsyncGenerator` 对象
- `next()` 方法返回 `Promise<{value, done}>`"

### 核心洞察 #2: for await...of 循环

"for await...of 用于遍历异步可迭代对象:

```javascript
async function process() {
    const asyncIterable = loadDataStream();

    // for await...of 自动处理 Promise
    for await (const item of asyncIterable) {
        console.log(item);
    }
}
```

执行流程:
- 调用 `asyncIterable[Symbol.asyncIterator]()`
- 循环调用 `next()` 并 await 结果
- 取出 `value` 赋值给循环变量
- 直到 `done` 为 `true`"

### 核心洞察 #3: 异步迭代器协议

"异步迭代器协议要求:

```javascript
const asyncIterable = {
    [Symbol.asyncIterator]() {
        return {
            async next() {
                // 返回 Promise<{value, done}>
                return { value: 'data', done: false };
            }
        };
    }
};
```

协议规范:
- 对象必须有 `Symbol.asyncIterator` 方法
- 该方法返回异步迭代器对象
- 迭代器对象必须有 `next()` 方法
- `next()` 返回 `Promise<{value, done}>`"

### 核心洞察 #4: 流式处理优势

"异步迭代适合流式数据处理:

```javascript
class DataStream {
    async *[Symbol.asyncIterator]() {
        let page = 1;

        while (true) {
            const data = await fetchPage(page);

            if (data.length === 0) break;

            for (const item of data) {
                yield item;  // 边加载边处理
            }

            page++;
        }
    }
}
```

优势:
- 内存占用可控 (不需要全部加载)
- 边加载边处理 (提升响应速度)
- 支持中断 (break 或 return)
- 自动资源清理 (finally 块)"

你合上笔记本, 关掉电脑。

"Part 7 完成了, " 你想, "从回调地狱到 Promise, 从 async/await 到 Generator, 最后到异步迭代——这是 JavaScript 异步编程的完整演进历程。异步迭代让我们能够优雅地处理无限数据流, 就像在时间的河流中逐个拾取数据, 而不是等待整条河流干涸。理解异步迭代, 才能真正掌握 JavaScript 中处理大数据流的艺术。"

---

## 知识总结

**规则 1: 异步 Generator 函数的定义**

异步 Generator 使用 `async function*` 定义, 结合了 async 和 Generator 的特性:

```javascript
async function* asyncGenerator() {
    // 可以使用 await
    const data = await fetchData();
    yield data;

    // 可以 yield Promise
    yield fetchMore();

    // 可以使用普通的控制流
    for (let i = 0; i < 5; i++) {
        yield i;
    }
}

const gen = asyncGenerator();

// next() 返回 Promise
const result1 = await gen.next();  // { value: data, done: false }
const result2 = await gen.next();  // { value: Promise, done: false }
```

核心特性:
- `async function*` 定义异步生成器函数
- 可以在函数内部使用 `await` 和 `yield`
- 调用后返回 `AsyncGenerator` 对象
- `next()` 方法返回 `Promise<{value, done}>`
- 自动实现异步迭代器协议

---

**规则 2: for await...of 循环**

for await...of 用于遍历异步可迭代对象:

```javascript
async function* dataGenerator() {
    yield await fetchData1();
    yield await fetchData2();
    yield await fetchData3();
}

// 使用 for await...of
async function process() {
    for await (const data of dataGenerator()) {
        console.log(data);  // 自动 await 每个 Promise
    }
    console.log('处理完成');
}

process();
```

执行流程:
- 调用对象的 `Symbol.asyncIterator` 方法获取迭代器
- 循环调用 `next()` 方法
- await `next()` 返回的 Promise
- 取出 `{value, done}` 中的 `value`
- 直到 `done` 为 `true`

与普通 for...of 的区别:
```javascript
// for...of: 用于同步迭代器
for (const item of syncIterable) {
    console.log(item);
}

// for await...of: 用于异步迭代器
for await (const item of asyncIterable) {
    console.log(item);
}
```

---

**规则 3: 异步迭代器协议**

异步迭代器协议要求对象实现 `Symbol.asyncIterator` 方法:

```javascript
const asyncIterable = {
    [Symbol.asyncIterator]() {
        let count = 0;

        return {
            async next() {
                if (count < 3) {
                    count++;
                    // 模拟异步操作
                    await new Promise(resolve => setTimeout(resolve, 100));
                    return { value: count, done: false };
                }
                return { value: undefined, done: true };
            }
        };
    }
};

// 使用
for await (const num of asyncIterable) {
    console.log(num);  // 每隔 100ms 输出: 1, 2, 3
}
```

协议规范:
- 对象必须有 `[Symbol.asyncIterator]()` 方法
- 该方法返回异步迭代器对象
- 迭代器对象必须有 `next()` 方法
- `next()` 返回 `Promise<{value, done}>`
- 可选实现 `return()` 和 `throw()` 方法

简写形式 (推荐):
```javascript
const asyncIterable = {
    async *[Symbol.asyncIterator]() {
        yield 1;
        yield 2;
        yield 3;
    }
};
```

---

**规则 4: 异步 Generator 的双向通信**

异步 Generator 也支持通过 `next(value)` 传值:

```javascript
async function* asyncProcessor() {
    console.log('处理器启动');

    const input1 = yield '等待第一个输入';
    console.log('收到输入 1:', input1);

    const input2 = yield '等待第二个输入';
    console.log('收到输入 2:', input2);

    return input1 + input2;
}

// 使用
const gen = asyncProcessor();

console.log(await gen.next());       // { value: '等待第一个输入', done: false }
console.log(await gen.next(10));     // 收到输入 1: 10
                                      // { value: '等待第二个输入', done: false }
console.log(await gen.next(20));     // 收到输入 2: 20
                                      // { value: 30, done: true }
```

数据流向:
- `yield value` → `next()` 返回 `Promise<{value, done: false}>`
- `await gen.next(x)` → `yield` 表达式的值变成 `x`
- 第一次 `next()` 的参数无效 (没有对应的 yield 接收)

---

**规则 5: 流式数据处理模式**

异步迭代器适合处理大数据流:

```javascript
class DataStream {
    constructor(apiUrl) {
        this.apiUrl = apiUrl;
    }

    async *[Symbol.asyncIterator]() {
        let page = 1;
        let hasMore = true;

        while (hasMore) {
            console.log(`加载第 ${page} 页`);

            // 异步获取数据
            const response = await fetch(`${this.apiUrl}?page=${page}`);
            const data = await response.json();

            // 逐个 yield 数据项
            for (const item of data.items) {
                yield item;  // 边加载边处理
            }

            hasMore = data.hasMore;
            page++;
        }
    }
}

// 使用
const stream = new DataStream('/api/users');

for await (const user of stream) {
    processUser(user);  // 边加载边处理, 内存占用稳定
}
```

优势:
- **内存可控**: 不需要一次性加载所有数据
- **边加载边处理**: 提升响应速度, 用户体验更好
- **支持中断**: 可以随时 `break` 或 `return` 退出
- **自动分页**: API 自动处理分页逻辑

---

**规则 6: 错误处理与资源清理**

异步迭代器支持完整的错误处理和资源清理:

```javascript
async function* fileStream(filename) {
    const file = await openFile(filename);

    try {
        for (const chunk of file) {
            yield chunk;
        }
    } catch (error) {
        console.error('读取错误:', error);
        throw error;  // 重新抛出错误
    } finally {
        // 确保资源清理
        await closeFile(file);
        console.log('文件已关闭');
    }
}

// 使用
try {
    for await (const chunk of fileStream('large.txt')) {
        console.log(chunk);

        if (chunk.includes('STOP')) {
            break;  // 提前退出
        }
    }
} catch (error) {
    console.error('处理失败:', error);
}

// 输出: 文件已关闭 (即使 break 提前退出, finally 也会执行)
```

错误处理规则:
- 异步生成器内部的错误会传播到外层
- 可以用 `try...catch` 捕获
- `finally` 块确保资源清理
- 即使 `break` 或 `return` 提前退出, `finally` 也会执行

---

**规则 7: return() 和 throw() 方法**

异步生成器对象有 `return()` 和 `throw()` 方法:

```javascript
async function* test() {
    try {
        yield 1;
        yield 2;
        yield 3;
    } catch (error) {
        console.log('内部捕获:', error.message);
        yield 'error';
    } finally {
        console.log('清理资源');
    }
}

// 1. return() 方法: 提前结束
const gen1 = test();
console.log(await gen1.next());  // { value: 1, done: false }
console.log(await gen1.return('手动结束'));
// 清理资源
// { value: '手动结束', done: true }

// 2. throw() 方法: 向内部抛入错误
const gen2 = test();
console.log(await gen2.next());  // { value: 1, done: false }
console.log(await gen2.throw(new Error('外部错误')));
// 内部捕获: 外部错误
// { value: 'error', done: false }
// 清理资源
```

方法说明:
- `return(value)`: 提前结束生成器, 返回指定值, 触发 `finally`
- `throw(error)`: 向生成器内部抛入错误, 可被内部 `try...catch` 捕获
- 两者都会触发 `finally` 块进行资源清理

---

**规则 8: 异步迭代器的实际应用场景**

**场景 1: 分页数据加载**
```javascript
class PaginatedAPI {
    async *[Symbol.asyncIterator]() {
        let page = 1;
        while (true) {
            const data = await fetchPage(page);
            if (data.length === 0) break;

            for (const item of data) {
                yield item;
            }
            page++;
        }
    }
}

for await (const item of new PaginatedAPI()) {
    displayItem(item);  // 边加载边显示
}
```

**场景 2: 实时日志流**
```javascript
class LogStream {
    async *[Symbol.asyncIterator]() {
        const files = await fetchLogFiles();

        for (const file of files) {
            const stream = await fetchFileStream(file);
            for await (const line of stream) {
                yield parseLine(line);
            }
        }
    }
}

for await (const log of new LogStream()) {
    displayLog(log);  // 实时显示日志
}
```

**场景 3: 服务器推送事件**
```javascript
async function* serverEvents(url) {
    const eventSource = new EventSource(url);

    try {
        while (true) {
            const event = await new Promise(resolve => {
                eventSource.onmessage = e => resolve(e.data);
            });
            yield JSON.parse(event);
        }
    } finally {
        eventSource.close();
    }
}

for await (const event of serverEvents('/api/events')) {
    handleEvent(event);  // 处理实时事件
}
```

**场景 4: 文件读取**
```javascript
async function* readFileByChunks(filename) {
    const file = await openFile(filename);

    try {
        while (true) {
            const chunk = await file.read(1024);  // 每次读 1KB
            if (!chunk) break;
            yield chunk;
        }
    } finally {
        await file.close();
    }
}

for await (const chunk of readFileByChunks('large.txt')) {
    processChunk(chunk);  // 分块处理大文件
}
```

使用原则:
- **大数据流** → 异步迭代器 (内存可控)
- **实时数据** → 异步迭代器 (边接收边处理)
- **分页加载** → 异步迭代器 (自动分页)
- **一次性数据** → Promise.all (并行加载)

---

**事故档案编号**: ASYNC-2024-1902
**影响范围**: 异步迭代器, for await...of, 异步 Generator, 流式处理
**根本原因**: 一次性加载所有数据导致内存爆炸, 应使用异步迭代器流式处理
**修复成本**: 中 (需要理解异步迭代协议)

这是 JavaScript 世界第 102 次被记录的异步编程事故。异步 Generator 使用 `async function*` 定义, 结合了 async 和 Generator 的特性。for await...of 循环用于遍历异步可迭代对象, 自动 await 每个 Promise。异步迭代器协议要求对象实现 `Symbol.asyncIterator` 方法, 返回的迭代器对象的 `next()` 方法返回 `Promise<{value, done}>`。异步迭代器适合流式数据处理, 边加载边处理, 内存占用可控。支持完整的错误处理和资源清理机制, `finally` 块确保资源释放。异步 Generator 对象有 `return()` 和 `throw()` 方法用于提前结束和错误注入。理解异步迭代是处理大数据流和实时数据的关键技术。

---

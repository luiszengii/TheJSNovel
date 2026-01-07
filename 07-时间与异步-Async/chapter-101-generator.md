《第 101 次记录: 可暂停的执行 —— Generator 的时间切片》

---

## 奇怪的函数语法

周一上午九点, 你在阅读公司的老代码时, 遇到了一个从未见过的函数语法。

这是一个数据分页加载的模块, 代码风格很陌生:

```javascript
function* fetchPages() {
    let page = 1;

    while (true) {
        const data = yield fetchPageData(page);
        console.log('获取到第', page, '页数据');
        page++;
    }
}
```

"这是什么?" 你盯着函数名前面的星号 `*`, 完全困惑了, "还有这个 `yield` 关键字?"

你试着运行这个函数:

```javascript
const iterator = fetchPages();
console.log(iterator);
```

控制台输出:

```
Object [Generator] {}
```

"Generator?" 你更困惑了, "不是应该返回函数执行结果吗?"

你尝试调用返回的对象:

```javascript
const iterator = fetchPages();
const result = iterator.next();
console.log(result);
```

输出:

```
{ value: Promise {...}, done: false }
```

"什么是 `value` 和 `done`?" 你完全懵了, "这个函数到底在做什么?"

你的同事老陈走过来, 看了一眼屏幕: "哦, 这是 Generator 函数。ES6 的特性, 可以暂停和恢复执行。"

"暂停和恢复?" 你的眼睛亮了, "函数还能暂停?"

"对, " 老陈说, "Generator 是一种特殊的函数, 可以在执行过程中多次暂停和恢复。你应该系统学习一下。"

他离开后, 你决定从头开始理解这个神奇的特性。

---

## 第一个 Generator 函数

上午十点, 你开始从最简单的例子入手。

"先不管复杂的, " 你想, "写一个最简单的 Generator 函数。"

```javascript
function* simpleGenerator() {
    console.log('第一步');
    yield 1;

    console.log('第二步');
    yield 2;

    console.log('第三步');
    yield 3;

    console.log('完成');
    return 'done';
}
```

"这个函数有三个 `yield`, " 你分析, "应该会暂停三次。"

你创建 Generator 对象并测试:

```javascript
const gen = simpleGenerator();
console.log('创建 Generator 对象');

console.log(gen.next());  // 第一次调用
console.log(gen.next());  // 第二次调用
console.log(gen.next());  // 第三次调用
console.log(gen.next());  // 第四次调用
```

输出:

```
创建 Generator 对象
第一步
{ value: 1, done: false }
第二步
{ value: 2, done: false }
第三步
{ value: 3, done: false }
完成
{ value: 'done', done: true }
```

你的眼睛瞪大了。

"天哪!" 你惊呼, "函数真的被暂停了! 每次调用 `next()`, 函数就执行到下一个 `yield` 然后停下来!"

你画了执行流程图:

```
gen.next() → 执行到 yield 1 → 暂停 → 返回 { value: 1, done: false }
gen.next() → 恢复执行 → 执行到 yield 2 → 暂停 → 返回 { value: 2, done: false }
gen.next() → 恢复执行 → 执行到 yield 3 → 暂停 → 返回 { value: 3, done: false }
gen.next() → 恢复执行 → 执行到 return → 结束 → 返回 { value: 'done', done: true }
```

"所以 Generator 函数不是一次性执行完, " 你总结, "而是可以多次暂停和恢复, 每次停在 `yield` 的位置!"

你又注意到一个细节:

```javascript
const gen = simpleGenerator();
console.log('创建了 Generator, 但函数还没开始执行');
console.log('调用 next() 才会开始执行');

gen.next();  // 这时才输出'第一步'
```

"创建 Generator 对象不会执行函数, " 你说, "只有调用 `next()` 才会开始执行!"

---

## yield 的双向通信

上午十一点, 你发现了 `yield` 的另一个特性。

"既然 `yield` 可以向外传递值, " 你想, "那能不能向内传递值?"

你查阅文档, 发现 `next()` 方法可以接受参数:

```javascript
function* dataProcessor() {
    console.log('处理器启动');

    const input1 = yield '等待第一个输入';
    console.log('收到输入 1:', input1);

    const input2 = yield '等待第二个输入';
    console.log('收到输入 2:', input2);

    return input1 + input2;
}

const gen = dataProcessor();

console.log(gen.next());        // 启动, 执行到第一个 yield
console.log(gen.next(10));      // 传入 10
console.log(gen.next(20));      // 传入 20
```

输出:

```
处理器启动
{ value: '等待第一个输入', done: false }
收到输入 1: 10
{ value: '等待第二个输入', done: false }
收到输入 2: 20
{ value: 30, done: true }
```

你盯着输出, 慢慢理解了执行流程:

```
gen.next()
  → 执行到 yield '等待第一个输入'
  → 暂停, 返回 '等待第一个输入'

gen.next(10)
  → 恢复执行, yield 表达式的值变成 10
  → input1 = 10
  → 执行到 yield '等待第二个输入'
  → 暂停, 返回 '等待第二个输入'

gen.next(20)
  → 恢复执行, yield 表达式的值变成 20
  → input2 = 20
  → return 30
  → 结束, 返回 30
```

"所以 `yield` 是双向的!" 你恍然大悟, "不仅可以向外传值, 还可以接收外部传入的值!"

你画了数据流向图:

```
外部                Generator 内部
        ┌────────────────┐
  next()│                │yield value
   ──→  │   暂停/恢复    │  ──→
        │                │
next(x) │                │yield
   ──→  │   x 传入内部   │
        └────────────────┘
```

"这简直是双向通信!" 你说, "Generator 可以暂停等待外部输入, 外部可以通过 `next(value)` 传递数据进去!"

---

## Generator 的实际应用

中午十二点, 你开始思考 Generator 的实际用途。

"既然可以暂停和恢复, " 你想, "应该可以用来控制异步流程..."

你尝试用 Generator 重写之前的注册流程:

```javascript
function* registerFlow(username, password) {
    console.log('开始注册');

    // 验证输入
    const validData = yield validateInput(username, password);
    console.log('输入验证通过');

    // 创建用户
    const user = yield createUser(validData);
    console.log('用户创建成功:', user.id);

    // 发送邮件
    yield sendWelcomeEmail(user.email);
    console.log('欢迎邮件已发送');

    // 创建配置
    const settings = yield createUserSettings(user.id);
    console.log('配置创建完成');

    return { user, settings };
}
```

"代码看起来很清晰, " 你说, "但怎么运行这个 Generator 呢?"

你手动调用 `next()`:

```javascript
const gen = registerFlow('alice', '123456');

gen.next();  // 启动
// 但 Promise 怎么处理?
```

你意识到需要一个执行器来自动处理 Promise:

```javascript
function runGenerator(generatorFunc, ...args) {
    const gen = generatorFunc(...args);

    function step(value) {
        const result = gen.next(value);

        if (result.done) {
            return result.value;  // Generator 完成
        }

        // 如果是 Promise, 等待完成后继续
        if (result.value && typeof result.value.then === 'function') {
            result.value.then(function(resolvedValue) {
                step(resolvedValue);  // 传入 Promise 的结果
            }).catch(function(error) {
                gen.throw(error);  // 将错误传入 Generator
            });
        } else {
            step(result.value);  // 不是 Promise, 直接继续
        }
    }

    step();  // 启动执行
}

// 使用
runGenerator(registerFlow, 'alice', '123456');
```

测试后, 代码按预期执行了!

"所以 Generator + Promise + 执行器, " 你恍然大悟, "就是 async/await 的原理!"

你立刻对比了两者:

```javascript
// Generator 版本 (需要执行器)
function* registerFlow(username, password) {
    const validData = yield validateInput(username, password);
    const user = yield createUser(validData);
    yield sendWelcomeEmail(user.email);
    return user;
}
runGenerator(registerFlow, 'alice', '123456');

// async/await 版本 (内置执行器)
async function registerFlow(username, password) {
    const validData = await validateInput(username, password);
    const user = await createUser(validData);
    await sendWelcomeEmail(user.email);
    return user;
}
registerFlow('alice', '123456');
```

"async/await 就是 Generator 的语法糖!" 你兴奋地说, "它内置了执行器, 所以不需要手动实现 `runGenerator`!"

---

## 无限序列生成器

下午两点, 你发现了 Generator 的另一个强大用途。

"既然 Generator 可以暂停, " 你想, "那能不能创建无限序列?"

你尝试写一个无限的 ID 生成器:

```javascript
function* idGenerator() {
    let id = 1;
    while (true) {
        yield id++;
    }
}

const gen = idGenerator();

console.log(gen.next().value);  // 1
console.log(gen.next().value);  // 2
console.log(gen.next().value);  // 3
console.log(gen.next().value);  // 4
```

"太棒了!" 你说, "虽然是无限循环, 但因为每次只执行到 `yield` 就暂停, 所以不会阻塞!"

你又实现了一个斐波那契数列生成器:

```javascript
function* fibonacci() {
    let [prev, curr] = [0, 1];

    while (true) {
        yield curr;
        [prev, curr] = [curr, prev + curr];
    }
}

const fib = fibonacci();

for (let i = 0; i < 10; i++) {
    console.log(fib.next().value);
}

// 输出: 1, 1, 2, 3, 5, 8, 13, 21, 34, 55
```

"Generator 完美适合生成无限序列!" 你总结, "因为它是惰性计算——只在需要时才生成下一个值。"

你又实现了一个分页数据加载器:

```javascript
function* pageLoader(apiUrl) {
    let page = 1;

    while (true) {
        console.log(`加载第 ${page} 页`);
        const data = yield fetch(`${apiUrl}?page=${page}`).then(r => r.json());

        if (data.length === 0) {
            console.log('没有更多数据了');
            break;
        }

        page++;
    }
}

// 使用
const loader = pageLoader('/api/users');
runGenerator(function*() {
    let result;
    while (!(result = loader.next()).done) {
        const data = yield result.value;
        console.log('处理数据:', data);
    }
});
```

"这样就可以按需加载数据, " 你说, "不会一次性加载所有页面。"

---

## Generator 的迭代器协议

下午三点, 你发现 Generator 对象可以直接用在 `for...of` 循环中。

你测试了一个简单的例子:

```javascript
function* range(start, end) {
    for (let i = start; i <= end; i++) {
        yield i;
    }
}

for (const num of range(1, 5)) {
    console.log(num);
}

// 输出: 1, 2, 3, 4, 5
```

"Generator 自动实现了迭代器协议!" 你说。

你查阅文档, 发现 Generator 对象同时具有 `next()` 方法和 `Symbol.iterator` 方法:

```javascript
function* test() {
    yield 1;
    yield 2;
}

const gen = test();

console.log(typeof gen.next);  // 'function'
console.log(typeof gen[Symbol.iterator]);  // 'function'

// 而且 Symbol.iterator 返回自己
console.log(gen[Symbol.iterator]() === gen);  // true
```

"所以 Generator 本身就是一个可迭代对象, " 你恍然大悟, "这就是为什么可以用 `for...of` 循环!"

你立刻想到了一个应用——自定义可迭代对象:

```javascript
class Tree {
    constructor(value, left = null, right = null) {
        this.value = value;
        this.left = left;
        this.right = right;
    }

    // 使用 Generator 实现中序遍历
    *[Symbol.iterator]() {
        if (this.left) {
            yield* this.left;  // yield* 委托给子树
        }
        yield this.value;
        if (this.right) {
            yield* this.right;
        }
    }
}

// 构建树
const tree = new Tree(
    4,
    new Tree(2, new Tree(1), new Tree(3)),
    new Tree(6, new Tree(5), new Tree(7))
);

// 遍历树
for (const value of tree) {
    console.log(value);
}

// 输出: 1, 2, 3, 4, 5, 6, 7 (中序遍历)
```

"太强大了!" 你说, "`yield*` 可以委托给另一个 Generator, 实现递归遍历!"

---

## yield* 委托机制

下午四点, 你深入研究 `yield*` 的机制。

"如果 `yield` 是暂停并返回值, " 你想, "那 `yield*` 是什么?"

你写了测试代码:

```javascript
function* inner() {
    yield 'a';
    yield 'b';
    return 'inner result';
}

function* outer() {
    yield 1;
    const result = yield* inner();  // 委托给 inner
    console.log('inner 返回:', result);
    yield 2;
}

const gen = outer();

console.log(gen.next());  // { value: 1, done: false }
console.log(gen.next());  // { value: 'a', done: false }
console.log(gen.next());  // { value: 'b', done: false }
console.log(gen.next());  // inner 返回: inner result
                          // { value: 2, done: false }
console.log(gen.next());  // { value: undefined, done: true }
```

"原来 `yield*` 会把控制权完全交给内部 Generator!" 你恍然大悟, "直到内部 Generator 完成, 才恢复外部 Generator 的执行。"

你画了执行流程:

```
outer 启动 → yield 1 → 暂停
恢复 → yield* inner() → 把控制权交给 inner
    inner 启动 → yield 'a' → 暂停
    恢复 → yield 'b' → 暂停
    恢复 → return 'inner result' → 结束
outer 恢复 → result = 'inner result' → yield 2 → 暂停
恢复 → 结束
```

"而且 `yield*` 可以接收内部 Generator 的返回值!" 你说, "这对于递归算法很有用。"

你实现了一个扁平化数组的 Generator:

```javascript
function* flatten(arr) {
    for (const item of arr) {
        if (Array.isArray(item)) {
            yield* flatten(item);  // 递归扁平化
        } else {
            yield item;
        }
    }
}

const nested = [1, [2, [3, 4], 5], 6, [7, 8]];

for (const num of flatten(nested)) {
    console.log(num);
}

// 输出: 1, 2, 3, 4, 5, 6, 7, 8
```

"完美!" 你说, "`yield*` 让递归 Generator 变得优雅。"

---

## Generator 的错误处理

下午五点, 你研究 Generator 的错误处理机制。

"如果 Generator 内部抛出错误呢?" 你测试:

```javascript
function* test() {
    console.log('开始');
    yield 1;
    console.log('继续');
    throw new Error('Generator 内部错误');
    yield 2;  // 不会执行
}

const gen = test();

console.log(gen.next());  // { value: 1, done: false }

try {
    console.log(gen.next());  // 抛出错误
} catch (error) {
    console.log('捕获到:', error.message);
}
```

输出:

```
开始
{ value: 1, done: false }
继续
捕获到: Generator 内部错误
```

"Generator 内部的错误会传递到外部, " 你说, "可以用 `try...catch` 捕获。"

你又发现 Generator 对象有 `throw()` 方法:

```javascript
function* test() {
    try {
        console.log('开始');
        yield 1;
        console.log('继续');
        yield 2;
    } catch (error) {
        console.log('Generator 内部捕获:', error.message);
        yield 'error';
    }
}

const gen = test();

console.log(gen.next());         // { value: 1, done: false }
console.log(gen.throw(new Error('外部错误')));  // 外部抛入错误
console.log(gen.next());         // { value: undefined, done: true }
```

输出:

```
开始
{ value: 1, done: false }
Generator 内部捕获: 外部错误
{ value: 'error', done: false }
{ value: undefined, done: true }
```

"太神奇了!" 你说, "`gen.throw()` 可以从外部向 Generator 内部抛入错误, 让内部的 `try...catch` 捕获!"

你总结了错误处理的双向性:

```
外部              Generator 内部
        ┌─────────────┐
        │             │
throw() │  try...     │  throw error
  ──→   │  catch      │  ──→
        │             │
        └─────────────┘
```

---

## 协程与生成器

下午六点, 你开始思考 Generator 的本质。

"Generator 可以暂停和恢复, " 你想, "还能双向通信... 这不就是协程 (Coroutine) 吗?"

你查阅资料, 发现 Generator 确实是 JavaScript 中实现协程的方式。

"协程是一种轻量级线程, " 你读着文档, "可以在用户态进行切换, 不需要操作系统介入。"

你实现了一个生产者-消费者模型:

```javascript
function* producer() {
    let id = 1;
    while (true) {
        console.log('生产:', id);
        yield id++;
    }
}

function* consumer(gen) {
    while (true) {
        const item = gen.next().value;
        console.log('消费:', item);
        yield;  // 让出控制权
    }
}

// 协作执行
const prod = producer();
const cons = consumer(prod);

for (let i = 0; i < 5; i++) {
    cons.next();
}

// 输出:
// 生产: 1
// 消费: 1
// 生产: 2
// 消费: 2
// 生产: 3
// 消费: 3
// 生产: 4
// 消费: 4
// 生产: 5
// 消费: 5
```

"生产者和消费者轮流执行, " 你说, "通过 Generator 实现了协作式并发!"

你又实现了一个任务调度器:

```javascript
function* task1() {
    console.log('任务 1: 步骤 1');
    yield;
    console.log('任务 1: 步骤 2');
    yield;
    console.log('任务 1: 步骤 3');
}

function* task2() {
    console.log('任务 2: 步骤 1');
    yield;
    console.log('任务 2: 步骤 2');
    yield;
    console.log('任务 2: 步骤 3');
}

function scheduler(tasks) {
    const generators = tasks.map(task => task());

    let allDone = false;
    while (!allDone) {
        allDone = true;
        for (const gen of generators) {
            const result = gen.next();
            if (!result.done) {
                allDone = false;
            }
        }
    }
}

scheduler([task1, task2]);

// 输出:
// 任务 1: 步骤 1
// 任务 2: 步骤 1
// 任务 1: 步骤 2
// 任务 2: 步骤 2
// 任务 1: 步骤 3
// 任务 2: 步骤 3
```

"完美的协作式调度!" 你说, "多个任务轮流执行, 每个任务在 `yield` 处让出控制权。"

---

## 你的 Generator 笔记本

晚上八点, 你整理了今天的收获。

你在笔记本上写下标题: "Generator —— 可暂停的时间切片"

### 核心洞察 #1: Generator 的基本机制

你写道:

"Generator 是可以暂停和恢复的特殊函数:

```javascript
function* gen() {
    console.log('步骤 1');
    yield 1;
    console.log('步骤 2');
    yield 2;
    console.log('步骤 3');
    return 3;
}

const g = gen();  // 创建 Generator 对象, 函数还未执行

g.next();  // { value: 1, done: false } - 执行到第一个 yield
g.next();  // { value: 2, done: false } - 执行到第二个 yield
g.next();  // { value: 3, done: true } - 执行到 return
```

核心特性:
- 函数名前加 `*` 定义 Generator 函数
- 调用 Generator 函数返回 Generator 对象, 不执行函数体
- 调用 `next()` 才开始执行, 执行到 `yield` 暂停
- `yield` 向外传递值, `next(value)` 向内传递值"

### 核心洞察 #2: yield 的双向通信

"yield 不仅可以向外传值, 还能接收外部传入的值:

```javascript
function* dataFlow() {
    const input1 = yield '等待输入 1';
    console.log('收到:', input1);

    const input2 = yield '等待输入 2';
    console.log('收到:', input2);

    return input1 + input2;
}

const gen = dataFlow();

gen.next();      // { value: '等待输入 1', done: false }
gen.next(10);    // 收到: 10, { value: '等待输入 2', done: false }
gen.next(20);    // 收到: 20, { value: 30, done: true }
```

数据流向:
- `yield value` → 向外传递 value
- `next(x)` → yield 表达式的值变成 x
- 双向通信让 Generator 成为强大的协程"

### 核心洞察 #3: Generator 与 async/await

"Generator + Promise + 执行器 = async/await:

```javascript
// Generator 版本
function* flow() {
    const data = yield fetchData();
    const result = yield processData(data);
    return result;
}

// 需要执行器
runGenerator(flow);

// async/await 版本 (内置执行器)
async function flow() {
    const data = await fetchData();
    const result = await processData(data);
    return result;
}
```

async/await 的本质就是 Generator + 自动执行器。"

### 核心洞察 #4: 无限序列与惰性计算

"Generator 适合生成无限序列:

```javascript
function* fibonacci() {
    let [prev, curr] = [0, 1];
    while (true) {
        yield curr;
        [prev, curr] = [curr, prev + curr];
    }
}

const fib = fibonacci();
fib.next().value;  // 1
fib.next().value;  // 1
fib.next().value;  // 2
```

优势:
- 惰性计算, 只在需要时生成下一个值
- 不会一次性占用大量内存
- 可以表示无限序列"

你合上笔记本, 关掉电脑。

"明天要学习异步迭代了, " 你想, "今天终于理解了 Generator 的本质——它是一种可以暂停和恢复的函数, 通过 `yield` 实现时间切片和双向通信。Generator 是 async/await 的基础, 也是 JavaScript 中实现协程的方式。理解 Generator, 才能真正掌握 JavaScript 的异步编程演进历程。"

---

## 知识总结

**规则 1: Generator 函数的定义与调用**

Generator 函数使用 `function*` 定义, 调用后返回 Generator 对象:

```javascript
// 定义 Generator 函数
function* myGenerator() {
    yield 1;
    yield 2;
    return 3;
}

// 调用 Generator 函数
const gen = myGenerator();  // 返回 Generator 对象, 函数还未执行

console.log(gen);  // Object [Generator] {}

// 调用 next() 才开始执行
console.log(gen.next());  // { value: 1, done: false }
console.log(gen.next());  // { value: 2, done: false }
console.log(gen.next());  // { value: 3, done: true }
console.log(gen.next());  // { value: undefined, done: true }
```

核心特性:
- `function*` 定义 Generator 函数 (星号位置可以是 `function *` 或 `function*`)
- 调用 Generator 函数不执行函数体, 返回 Generator 对象
- Generator 对象有 `next()` 方法, 用于控制执行
- `next()` 返回 `{ value, done }` 对象

---

**规则 2: yield 表达式的暂停机制**

yield 暂停函数执行, 并返回值:

```javascript
function* process() {
    console.log('开始');

    yield '步骤 1';
    console.log('步骤 1 完成');

    yield '步骤 2';
    console.log('步骤 2 完成');

    return '完成';
}

const gen = process();

gen.next();  // 输出: 开始
             // 返回: { value: '步骤 1', done: false }

gen.next();  // 输出: 步骤 1 完成
             // 返回: { value: '步骤 2', done: false }

gen.next();  // 输出: 步骤 2 完成
             // 返回: { value: '完成', done: true }
```

执行流程:
1. 调用 `next()` 开始执行函数
2. 执行到 `yield` 表达式, 暂停执行
3. 返回 `{ value: yield 的值, done: false }`
4. 下次调用 `next()`, 从 `yield` 后面继续执行
5. 执行到 `return` 或函数结束, 返回 `{ value: 返回值, done: true }`

---

**规则 3: yield 的双向通信**

yield 不仅可以向外传值, 还能接收 next(value) 传入的值:

```javascript
function* calculator() {
    console.log('计算器启动');

    const x = yield '输入第一个数';
    console.log('收到 x =', x);

    const y = yield '输入第二个数';
    console.log('收到 y =', y);

    const result = x + y;
    return `结果: ${result}`;
}

const gen = calculator();

console.log(gen.next());       // 计算器启动
                               // { value: '输入第一个数', done: false }

console.log(gen.next(10));     // 收到 x = 10
                               // { value: '输入第二个数', done: false }

console.log(gen.next(20));     // 收到 y = 20
                               // { value: '结果: 30', done: true }
```

数据流向:
- `yield value` → `next()` 返回 `{ value, done: false }`
- `next(x)` → `yield` 表达式的值变成 `x`
- 第一次 `next()` 没有对应的 `yield` 接收值, 所以参数无效

---

**规则 4: Generator 对象的三个方法**

Generator 对象有三个核心方法: next(), return(), throw():

```javascript
function* test() {
    try {
        yield 1;
        yield 2;
        yield 3;
    } catch (error) {
        console.log('捕获错误:', error.message);
        yield 'error';
    }
}

// 1. next() - 恢复执行
const gen1 = test();
gen1.next();  // { value: 1, done: false }

// 2. return(value) - 提前结束, 返回 value
const gen2 = test();
gen2.next();          // { value: 1, done: false }
gen2.return('提前结束');  // { value: '提前结束', done: true }
gen2.next();          // { value: undefined, done: true }

// 3. throw(error) - 向内部抛入错误
const gen3 = test();
gen3.next();                      // { value: 1, done: false }
gen3.throw(new Error('外部错误'));  // 捕获错误: 外部错误
                                  // { value: 'error', done: false }
```

方法说明:
- `next(value)`: 恢复执行, 传入值给 yield 表达式
- `return(value)`: 提前结束 Generator, 返回指定值
- `throw(error)`: 向 Generator 内部抛入错误

---

**规则 5: Generator 实现迭代器协议**

Generator 对象自动实现了迭代器协议, 可用于 for...of:

```javascript
function* range(start, end) {
    for (let i = start; i <= end; i++) {
        yield i;
    }
}

// 使用 for...of 迭代
for (const num of range(1, 5)) {
    console.log(num);
}
// 输出: 1, 2, 3, 4, 5

// Generator 对象既是迭代器, 也是可迭代对象
const gen = range(1, 3);
console.log(typeof gen.next);  // 'function' - 迭代器
console.log(typeof gen[Symbol.iterator]);  // 'function' - 可迭代对象
console.log(gen[Symbol.iterator]() === gen);  // true - 返回自己
```

应用: 自定义可迭代对象
```javascript
class Tree {
    constructor(value, left, right) {
        this.value = value;
        this.left = left;
        this.right = right;
    }

    *[Symbol.iterator]() {
        if (this.left) yield* this.left;
        yield this.value;
        if (this.right) yield* this.right;
    }
}

const tree = new Tree(2, new Tree(1), new Tree(3));
console.log([...tree]);  // [1, 2, 3]
```

---

**规则 6: yield* 委托机制**

yield* 将控制权委托给另一个 Generator:

```javascript
function* inner() {
    yield 'a';
    yield 'b';
    return 'inner 完成';
}

function* outer() {
    yield 1;
    const result = yield* inner();  // 委托给 inner
    console.log('inner 返回:', result);
    yield 2;
}

const gen = outer();

console.log(gen.next());  // { value: 1, done: false }
console.log(gen.next());  // { value: 'a', done: false }
console.log(gen.next());  // { value: 'b', done: false }
console.log(gen.next());  // inner 返回: inner 完成
                          // { value: 2, done: false }
```

yield* 特性:
- 委托给另一个 Generator 或可迭代对象
- 完全交出控制权, 直到内部 Generator 完成
- 接收内部 Generator 的返回值
- 适合递归算法

应用: 扁平化数组
```javascript
function* flatten(arr) {
    for (const item of arr) {
        if (Array.isArray(item)) {
            yield* flatten(item);
        } else {
            yield item;
        }
    }
}

console.log([...flatten([1, [2, [3, 4], 5], 6])]);
// [1, 2, 3, 4, 5, 6]
```

---

**规则 7: Generator 与 async/await 的关系**

async/await 是 Generator + Promise + 自动执行器的语法糖:

```javascript
// Generator 版本 (需要手动执行器)
function* fetchUserData(userId) {
    const user = yield fetchUser(userId);
    const orders = yield fetchOrders(user.id);
    return { user, orders };
}

function runGenerator(gen) {
    function step(value) {
        const result = gen.next(value);
        if (result.done) return result.value;

        result.value.then(resolved => step(resolved));
    }
    step();
}

runGenerator(fetchUserData(123));

// async/await 版本 (内置执行器)
async function fetchUserData(userId) {
    const user = await fetchUser(userId);
    const orders = await fetchOrders(user.id);
    return { user, orders };
}

fetchUserData(123);
```

转换规则:
- `function*` → `async function`
- `yield` → `await`
- 手动执行器 → 内置自动执行

---

**规则 8: Generator 的实际应用场景**

**场景 1: 无限序列生成**
```javascript
function* fibonacci() {
    let [prev, curr] = [0, 1];
    while (true) {
        yield curr;
        [prev, curr] = [curr, prev + curr];
    }
}

const fib = fibonacci();
console.log(fib.next().value);  // 1
console.log(fib.next().value);  // 1
console.log(fib.next().value);  // 2
console.log(fib.next().value);  // 3
```

**场景 2: 惰性求值**
```javascript
function* lazyMap(iterable, fn) {
    for (const item of iterable) {
        yield fn(item);
    }
}

const numbers = [1, 2, 3, 4, 5];
const doubled = lazyMap(numbers, x => x * 2);

doubled.next().value;  // 2 - 只计算需要的值
```

**场景 3: 状态机**
```javascript
function* stateMachine() {
    while (true) {
        console.log('状态: idle');
        const action1 = yield;

        console.log('状态: processing', action1);
        const action2 = yield;

        console.log('状态: done', action2);
        yield;
    }
}

const machine = stateMachine();
machine.next();
machine.next('开始');
machine.next('完成');
```

**场景 4: 协程 (生产者-消费者)**
```javascript
function* producer() {
    let id = 1;
    while (true) {
        yield id++;
    }
}

function* consumer(gen) {
    while (true) {
        const item = gen.next().value;
        console.log('消费:', item);
        yield;
    }
}

const prod = producer();
const cons = consumer(prod);

for (let i = 0; i < 3; i++) {
    cons.next();
}
// 消费: 1
// 消费: 2
// 消费: 3
```

---

**事故档案编号**: ASYNC-2024-1901
**影响范围**: Generator 函数, yield 表达式, 迭代器协议, 协程
**根本原因**: 不理解 Generator 的暂停/恢复机制和双向通信, 导致误用或无法发挥其优势
**修复成本**: 中 (需要理解协程概念)

这是 JavaScript 世界第 101 次被记录的异步编程事故。Generator 是一种可以暂停和恢复的特殊函数, 使用 `function*` 定义。调用 Generator 函数返回 Generator 对象, 不执行函数体。调用 `next()` 才开始执行, 执行到 `yield` 暂停。yield 表达式不仅可以向外传值, 还能接收 `next(value)` 传入的值, 实现双向通信。Generator 对象自动实现迭代器协议, 可用于 for...of 循环。yield* 将控制权委托给另一个 Generator, 适合递归算法。async/await 是 Generator + Promise + 自动执行器的语法糖。Generator 适合生成无限序列、惰性求值、状态机和协程等场景。理解 Generator 的暂停/恢复机制和双向通信是掌握 JavaScript 异步编程演进的关键。

---

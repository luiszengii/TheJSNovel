《第 109 次记录: 重复代码灾难 —— 柯里化的参数绑定艺术》

---

## 代码重复的困境

周四上午九点, 你盯着代码评审工具里的警告, 眉头紧锁。

这是团队新人小陈提交的一个 PR, 功能本身没问题——为数据分析平台增加了多种日志记录器。但代码审查工具标红的警告让你不得不暂停合并: "代码重复率 78%, 建议重构"。

你打开 PR, 看到了令人头疼的代码:

```javascript
// logger.js
function logUserAction(userId, action, timestamp) {
    console.log(`[用户操作] 用户 ${userId} 在 ${timestamp} 执行了 ${action}`);
}

function logAdminAction(userId, action, timestamp) {
    console.log(`[管理员操作] 用户 ${userId} 在 ${timestamp} 执行了 ${action}`);
}

function logSystemEvent(userId, action, timestamp) {
    console.log(`[系统事件] 用户 ${userId} 在 ${timestamp} 执行了 ${action}`);
}

function logSecurityAlert(userId, action, timestamp) {
    console.log(`[安全告警] 用户 ${userId} 在 ${timestamp} 执行了 ${action}`);
}
```

"这些函数几乎一模一样, " 你喃喃自语, "只是第一个参数不同..."

你继续往下看, 发现调用代码更加混乱:

```javascript
// 用户点击按钮
onClick() {
    const userId = getUserId();
    const action = '点击了导出按钮';
    const timestamp = Date.now();
    logUserAction(userId, action, timestamp);
}

// 管理员删除用户
onDelete() {
    const userId = getUserId();
    const action = '删除了用户';
    const timestamp = Date.now();
    logAdminAction(userId, action, timestamp);
}

// 每次调用都要传三个参数, 而且 timestamp 每次都是 Date.now()
```

"这也太冗长了, " 你想, "每次调用都要重复获取 userId 和 timestamp, 而且这四个日志函数的区别只是日志级别而已..."

你在评审意见里写下: "代码重复严重, 需要重构。" 然后点击了"需要修改"。

但当你放下鼠标时, 突然意识到一个问题: **我应该怎么重构?**

---

## 重构的第一次尝试

上午十点, 小陈来到你的工位。

"我不太理解应该怎么改, " 他有些困惑, "我试过把共同部分提取成一个函数, 但好像也没少写多少代码..."

你打开他的尝试版本:

```javascript
function log(level, userId, action, timestamp) {
    console.log(`[${level}] 用户 ${userId} 在 ${timestamp} 执行了 ${action}`);
}

// 调用时
log('用户操作', userId, action, timestamp);
log('管理员操作', userId, action, timestamp);
log('系统事件', userId, action, timestamp);
```

"这确实解决了函数重复, " 你说, "但调用时还是要传四个参数, 而且第一个参数 level 每次都是固定的..."

"那能不能把 level 预先绑定到函数上?" 小陈问。

你的手指停在了键盘上。"把参数提前绑定...?"

你突然想起曾经在函数式编程的文章里看到过一个概念——**柯里化 (Currying)**。

---

## 柯里化的发现

上午十一点, 你和小陈一起开始研究柯里化。

"柯里化是什么?" 小陈问。

你在 MDN 上找到了解释:

> **柯里化 (Currying)**: 将一个接受多个参数的函数转换为一系列接受单个参数的函数的技术。

"听起来很抽象, " 小陈说, "能举个例子吗?"

你写下了最简单的柯里化演示:

```javascript
// 普通函数: 接受两个参数
function add(a, b) {
    return a + b;
}

add(1, 2);  // 3

// 柯里化版本: 分两次传参
function curriedAdd(a) {
    return function(b) {
        return a + b;
    };
}

const add1 = curriedAdd(1);  // 先传第一个参数
add1(2);  // 3 - 再传第二个参数
add1(5);  // 6 - 可以复用 add1
```

"等等, " 小陈盯着代码, "curriedAdd(1) 返回的是一个函数?"

"对, " 你说, "这就是柯里化的核心——**把参数分阶段传入**。第一次调用 curriedAdd(1) 时, 它返回一个记住了 a=1 的新函数。"

你画了一个流程图:

```
curriedAdd(1)
  ↓ 返回一个函数, 记住 a=1
function(b) { return 1 + b }
  ↓ 调用这个函数
add1(2)  // 返回 3
add1(5)  // 返回 6
```

"这有什么用?" 小陈困惑, "为什么不直接 add(1, 2)?"

你微笑: "因为有时候你不是一次性拿到所有参数的。"

---

## 应用到日志系统

中午十二点, 你开始用柯里化重构日志系统。

"现在我们的 log 函数接受 4 个参数, " 你说, "但其实 level 是可以预先确定的。我们可以这样写:"

```javascript
// 柯里化的日志函数
function createLogger(level) {
    return function(userId, action, timestamp) {
        console.log(`[${level}] 用户 ${userId} 在 ${timestamp} 执行了 ${action}`);
    };
}

// 创建专门的日志记录器
const logUserAction = createLogger('用户操作');
const logAdminAction = createLogger('管理员操作');
const logSystemEvent = createLogger('系统事件');
const logSecurityAlert = createLogger('安全告警');
```

"太神奇了!" 小陈说, "现在每个日志函数都自动记住了自己的 level!"

你继续演示:

```javascript
// 调用时只需要传三个参数
onClick() {
    const userId = getUserId();
    const action = '点击了导出按钮';
    const timestamp = Date.now();
    logUserAction(userId, action, timestamp);  // level 已经绑定了
}
```

"但我们还能进一步优化, " 你说, "userId 和 timestamp 其实也可以提前绑定。"

你写下了更深层的柯里化:

```javascript
function createLogger(level) {
    return function(userId) {
        return function(action, timestamp) {
            console.log(`[${level}] 用户 ${userId} 在 ${timestamp} 执行了 ${action}`);
        };
    };
}

// 三层柯里化
const logUser = createLogger('用户操作');
const logUser123 = logUser('user-123');

// 现在每次调用只需要两个参数
logUser123('点击了按钮', Date.now());
logUser123('修改了资料', Date.now());
```

"这样就把 level 和 userId 都提前绑定了, " 你解释, "每次调用时只需要传 action 和 timestamp。"

小陈若有所思: "所以柯里化就是把参数分成多层?"

"对, " 你说, "**柯里化让你可以逐步收集参数, 每次调用固定一些参数, 返回一个新函数等待剩余参数**。"

---

## 通用柯里化函数

下午两点, 你开始思考一个问题。

"每次都要手写嵌套函数太麻烦了, " 你想, "能不能写一个通用的柯里化函数?"

你查阅了一些函数式编程库, 发现 Lodash 有一个 `_.curry` 函数。你决定自己实现一个简化版:

```javascript
function curry(fn) {
    return function curried(...args) {
        // 如果参数够了, 就执行原函数
        if (args.length >= fn.length) {
            return fn.apply(this, args);
        }

        // 如果参数不够, 返回一个新函数继续收集参数
        return function(...nextArgs) {
            return curried(...args, ...nextArgs);
        };
    };
}
```

"这个函数做了什么?" 小陈问。

"它接受一个普通函数, " 你解释, "返回一个柯里化版本。这个柯里化版本会检查参数是否足够, 如果够了就执行, 不够就返回一个新函数继续等待参数。"

你演示用法:

```javascript
// 原始函数
function log(level, userId, action, timestamp) {
    console.log(`[${level}] 用户 ${userId} 在 ${timestamp} 执行了 ${action}`);
}

// 自动柯里化
const curriedLog = curry(log);

// 可以分步传参
const logUser = curriedLog('用户操作');
const logUser123 = logUser('user-123');
logUser123('点击按钮', Date.now());

// 也可以一次性传多个参数
curriedLog('管理员操作')('admin-1', '删除用户', Date.now());

// 甚至可以一次性传完
curriedLog('系统事件', 'system', '启动', Date.now());
```

"哇, " 小陈惊叹, "这太灵活了!"

你点头: "这就是柯里化的强大之处——**你可以按需传参, 既可以一次传一个, 也可以一次传多个**。"

---

## 偏函数应用

下午三点, 你注意到一个特殊的使用场景。

团队的前端代码中有大量的事件处理器, 它们都需要传入一个配置对象:

```javascript
button.addEventListener('click', function(event) {
    handleEvent('button-1', 'click', true, event);
});

link.addEventListener('click', function(event) {
    handleEvent('link-1', 'click', true, event);
});

input.addEventListener('change', function(event) {
    handleEvent('input-1', 'change', false, event);
});
```

"每次都要包一个匿名函数, " 你想, "而且前三个参数都是固定的, 只有 event 是运行时传入的..."

你想起了另一个技巧——**偏函数应用 (Partial Application)**。

"偏函数应用和柯里化有什么区别?" 小陈问。

你解释道: "**柯里化是自动的、递归的转换, 每次只接受一个参数。偏函数应用是手动的、一次性的, 可以固定任意数量的参数**。"

你写下对比:

```javascript
// 柯里化: 自动转换, 每次一个参数
const curried = curry(fn);
curried(a)(b)(c);

// 偏函数应用: 手动固定部分参数
const partial = fn.bind(null, a, b);  // 固定前两个参数
partial(c);  // 只传最后一个参数
```

你用偏函数应用重写了事件处理器:

```javascript
function handleEvent(elementId, eventType, shouldLog, event) {
    if (shouldLog) {
        console.log(`元素 ${elementId} 触发了 ${eventType} 事件`);
    }
    // 处理事件...
}

// 使用 bind 创建偏函数
const handleButtonClick = handleEvent.bind(null, 'button-1', 'click', true);
const handleLinkClick = handleEvent.bind(null, 'link-1', 'click', true);
const handleInputChange = handleEvent.bind(null, 'input-1', 'change', false);

// 直接绑定
button.addEventListener('click', handleButtonClick);
link.addEventListener('click', handleLinkClick);
input.addEventListener('change', handleInputChange);
```

"这样就不需要每次都包一个匿名函数了, " 你说, "而且代码更清晰。"

"所以什么时候用柯里化, 什么时候用偏函数?" 小陈问。

"**如果你需要逐步收集参数, 用柯里化。如果你只是想固定一些参数, 用偏函数**。" 你总结道。

---

## 实际应用场景

下午四点, 你开始整理柯里化的常见应用场景。

"柯里化不只是为了减少代码重复, " 你说, "它还有很多实用的场景。"

你写下了几个例子:

### 场景 1: 配置函数工厂

```javascript
// 创建不同配置的 HTTP 请求函数
function request(method, baseUrl, endpoint, data) {
    return fetch(`${baseUrl}${endpoint}`, {
        method,
        body: JSON.stringify(data)
    });
}

const curriedRequest = curry(request);

// 创建不同环境的请求函数
const devRequest = curriedRequest('POST')('https://dev.api.example.com');
const prodRequest = curriedRequest('POST')('https://api.example.com');

// 使用时只需要传 endpoint 和 data
devRequest('/users', { name: 'Alice' });
prodRequest('/users', { name: 'Bob' });
```

### 场景 2: 数据验证器

```javascript
function validate(rule, errorMsg, value) {
    if (!rule(value)) {
        throw new Error(errorMsg);
    }
    return value;
}

const curriedValidate = curry(validate);

// 创建专门的验证器
const validateEmail = curriedValidate(
    (v) => /\S+@\S+\.\S+/.test(v),
    '邮箱格式不正确'
);

const validateAge = curriedValidate(
    (v) => v >= 18 && v <= 120,
    '年龄必须在 18-120 之间'
);

// 使用
try {
    validateEmail('user@example.com');  // ✓
    validateEmail('invalid');  // ✗ 抛出错误

    validateAge(25);  // ✓
    validateAge(150);  // ✗ 抛出错误
} catch (e) {
    console.error(e.message);
}
```

### 场景 3: 映射与过滤

```javascript
// 创建专门的数组处理函数
const map = curry((fn, arr) => arr.map(fn));
const filter = curry((fn, arr) => arr.filter(fn));

// 创建复用的处理函数
const double = map((x) => x * 2);
const filterEven = filter((x) => x % 2 === 0);

// 使用
const numbers = [1, 2, 3, 4, 5];
double(numbers);  // [2, 4, 6, 8, 10]
filterEven(numbers);  // [2, 4]

// 组合使用
const doubleEvens = (arr) => double(filterEven(arr));
doubleEvens(numbers);  // [4, 8]
```

"这样代码的可复用性就大大提高了, " 你说。

---

## 柯里化的性能考虑

下午五点, 小陈提出了一个问题。

"柯里化会不会影响性能?" 他问, "因为它创建了很多中间函数..."

"好问题, " 你说, "我们来测试一下。"

你写下了性能测试:

```javascript
// 原始函数
function add(a, b, c) {
    return a + b + c;
}

// 柯里化版本
const curriedAdd = curry(add);

// 性能测试
console.time('原始函数');
for (let i = 0; i < 1000000; i++) {
    add(1, 2, 3);
}
console.timeEnd('原始函数');  // ~3ms

console.time('柯里化函数');
for (let i = 0; i < 1000000; i++) {
    curriedAdd(1)(2)(3);
}
console.timeEnd('柯里化函数');  // ~25ms
```

"柯里化确实慢了约 8 倍, " 你说, "因为它创建了多个闭包和函数调用。"

"那还能用吗?" 小陈担心。

"可以用, " 你说, "因为:**性能损耗很小, 而且通常不是性能瓶颈**。100 万次调用也只是差 22ms, 在实际应用中几乎感觉不到。"

你继续解释: "而且如果你关心性能, 可以用偏函数应用代替柯里化:"

```javascript
// 偏函数应用性能更好
const add1 = add.bind(null, 1);
const add12 = add1.bind(null, 2);

console.time('偏函数应用');
for (let i = 0; i < 1000000; i++) {
    add12(3);
}
console.timeEnd('偏函数应用');  // ~8ms
```

"所以原则是: " 你总结道:
- **如果需要灵活的参数收集, 用柯里化**
- **如果只是固定部分参数, 用偏函数应用 (bind)**
- **性能敏感的热点路径, 避免过度柯里化**

---

## 你的柯里化笔记本

晚上八点, 你整理了今天的收获。

你在笔记本上写下标题: "柯里化 —— 参数的分阶段绑定"

### 核心洞察 #1: 柯里化的本质

你写道:

"柯里化将一个多参数函数转换为一系列单参数函数:

```javascript
// 原始函数
function add(a, b, c) {
    return a + b + c;
}

// 柯里化版本
function curriedAdd(a) {
    return function(b) {
        return function(c) {
            return a + b + c;
        };
    };
}

// 用法
curriedAdd(1)(2)(3);  // 6

// 或者分步
const add1 = curriedAdd(1);
const add12 = add1(2);
add12(3);  // 6
```

核心特性:
- 参数逐个传入
- 每次调用返回新函数
- 最后一次调用返回结果
- 利用闭包记住之前的参数"

### 核心洞察 #2: 通用柯里化实现

"通用的 curry 函数:

```javascript
function curry(fn) {
    return function curried(...args) {
        // 参数够了, 执行原函数
        if (args.length >= fn.length) {
            return fn.apply(this, args);
        }

        // 参数不够, 返回新函数继续收集
        return function(...nextArgs) {
            return curried(...args, ...nextArgs);
        };
    };
}

// 使用
function log(level, userId, action) {
    console.log(`[${level}] ${userId}: ${action}`);
}

const curriedLog = curry(log);

// 灵活传参
curriedLog('INFO')('user-1')('登录');  // 每次传一个
curriedLog('INFO', 'user-1')('登录');  // 一次传两个
curriedLog('INFO', 'user-1', '登录');  // 一次传完
```

实现原理:
- 检查已收集的参数数量
- 与原函数的参数数量比较 (fn.length)
- 够了就执行, 不够就返回新函数
- 递归地累积参数"

### 核心洞察 #3: 柯里化 vs 偏函数应用

"两者的区别:

```javascript
// 柯里化: 自动转换, 逐个传参
const curried = curry(fn);
curried(a)(b)(c);

// 偏函数应用: 手动固定部分参数
const partial = fn.bind(null, a, b);
partial(c);
```

对比矩阵:

| 特性 | 柯里化 | 偏函数应用 |
|-----|-------|----------|
| 参数传递 | 逐个或分组 | 一次性固定 |
| 灵活性 | 高 | 中 |
| 性能 | 较慢 (~8倍) | 较快 (~2倍) |
| 使用场景 | 需要逐步收集参数 | 只需固定部分参数 |
| 实现方式 | curry 函数 | bind 方法 |

选择原则:
- **逐步收集参数** → 柯里化
- **固定部分参数** → 偏函数应用
- **性能敏感** → 偏函数应用"

### 核心洞察 #4: 实际应用场景

"柯里化的常见用途:

```javascript
// 1. 配置函数工厂
const request = curry((method, baseUrl, endpoint, data) => {
    return fetch(`${baseUrl}${endpoint}`, { method, body: JSON.stringify(data) });
});

const postToApi = request('POST')('https://api.example.com');
postToApi('/users', userData);

// 2. 事件处理器
const handleEvent = curry((elementId, eventType, shouldLog, event) => {
    if (shouldLog) console.log(`${elementId} ${eventType}`);
    // 处理事件
});

const handleButtonClick = handleEvent('btn-1')('click')(true);
button.addEventListener('click', handleButtonClick);

// 3. 数据验证
const validate = curry((rule, errorMsg, value) => {
    if (!rule(value)) throw new Error(errorMsg);
    return value;
});

const validateEmail = validate((v) => /\S+@\S+/.test(v))('邮箱格式错误');
validateEmail('user@example.com');

// 4. 数据转换
const map = curry((fn, arr) => arr.map(fn));
const double = map((x) => x * 2);
double([1, 2, 3]);  // [2, 4, 6]
```

应用价值:
- **减少代码重复**: 提取共同配置
- **提高可复用性**: 创建专用函数
- **延迟计算**: 等待所有参数就绪
- **函数组合**: 更容易组合小函数"

你合上笔记本, 关掉电脑。

"明天要学习 Reference Type 了, " 你想, "今天终于理解了柯里化——它不是什么高深的技巧, 而是一种将参数分阶段绑定的实用模式。通过逐步收集参数, 我们可以创建更灵活、更可复用的函数。理解柯里化, 才能写出更函数式、更优雅的 JavaScript 代码。"

---

## 知识总结

**规则 1: 柯里化的定义**

柯里化是将多参数函数转换为一系列单参数函数的技术:

```javascript
// 原始函数
function add(a, b, c) {
    return a + b + c;
}

add(1, 2, 3);  // 6

// 柯里化版本
function curriedAdd(a) {
    return function(b) {
        return function(c) {
            return a + b + c;
        };
    };
}

curriedAdd(1)(2)(3);  // 6

// 或者分步调用
const step1 = curriedAdd(1);  // 返回一个函数, 记住 a=1
const step2 = step1(2);  // 返回一个函数, 记住 a=1, b=2
const result = step2(3);  // 返回最终结果 6
```

核心特性:
- 每次调用接受一个参数
- 返回一个新函数 (除了最后一次)
- 利用闭包记住之前的参数
- 最后一次调用返回最终结果

---

**规则 2: 通用柯里化函数实现**

可以实现一个通用的 curry 函数来自动柯里化任意函数:

```javascript
function curry(fn) {
    return function curried(...args) {
        // 如果收集到的参数足够, 执行原函数
        if (args.length >= fn.length) {
            return fn.apply(this, args);
        }

        // 否则返回新函数继续收集参数
        return function(...nextArgs) {
            return curried(...args, ...nextArgs);
        };
    };
}

// 使用
function log(level, userId, action) {
    console.log(`[${level}] User ${userId}: ${action}`);
}

const curriedLog = curry(log);

// 灵活的参数传递方式
curriedLog('INFO')('user-1')('登录');  // 每次传一个
curriedLog('INFO', 'user-1')('登录');  // 前两个一起传
curriedLog('INFO')('user-1', '登录');  // 后两个一起传
curriedLog('INFO', 'user-1', '登录');  // 一次性传完
```

实现原理:
- 检查已收集参数数量 (`args.length`)
- 与原函数期望的参数数量比较 (`fn.length`)
- 参数够了就执行原函数
- 不够就返回新函数继续累积参数
- 使用递归的方式不断累积参数

---

**规则 3: 柯里化 vs 偏函数应用**

柯里化和偏函数应用容易混淆, 但它们是不同的技术:

**柯里化 (Currying)**:
```javascript
// 自动转换, 每次传一个或多个参数
const curried = curry(add);
curried(1)(2)(3);  // 6
curried(1, 2)(3);  // 6
curried(1)(2, 3);  // 6
```

**偏函数应用 (Partial Application)**:
```javascript
// 手动固定部分参数, 使用 bind
const add1 = add.bind(null, 1);  // 固定第一个参数
add1(2, 3);  // 6

const add12 = add.bind(null, 1, 2);  // 固定前两个参数
add12(3);  // 6
```

核心区别:

| 特性 | 柯里化 | 偏函数应用 |
|-----|-------|----------|
| 转换方式 | 自动、递归 | 手动、一次性 |
| 参数传递 | 逐个或分组 | 一次性固定多个 |
| 灵活性 | 高 (可以任意组合) | 中 (固定后不可变) |
| 性能 | 较慢 (~8倍开销) | 较快 (~2倍开销) |
| 实现方式 | curry 函数 | bind 方法 |
| 返回值 | 函数 (直到参数够) | 固定参数后的新函数 |

选择原则:
- **需要逐步收集参数, 不确定何时传完** → 柯里化
- **只需固定部分参数, 其余参数一次性传入** → 偏函数应用
- **性能敏感的代码** → 偏函数应用

---

**规则 4: 柯里化的实际应用**

柯里化在实际开发中有多种应用场景:

**场景 1: 配置函数工厂**
```javascript
function request(method, baseUrl, endpoint, data) {
    return fetch(`${baseUrl}${endpoint}`, {
        method,
        body: JSON.stringify(data),
        headers: { 'Content-Type': 'application/json' }
    });
}

const curriedRequest = curry(request);

// 创建不同环境的请求函数
const devPost = curriedRequest('POST')('https://dev.api.example.com');
const prodPost = curriedRequest('POST')('https://api.example.com');

// 使用时只需要传 endpoint 和 data
devPost('/users', { name: 'Alice' });
prodPost('/users', { name: 'Bob' });

// 创建不同方法的请求函数
const devGet = curriedRequest('GET')('https://dev.api.example.com');
devGet('/users', null);
```

**场景 2: 事件处理器**
```javascript
function handleEvent(elementId, eventType, shouldLog, event) {
    if (shouldLog) {
        console.log(`元素 ${elementId} 触发了 ${eventType} 事件`);
    }
    // 处理事件逻辑
    console.log('Event details:', event);
}

const curriedHandle = curry(handleEvent);

// 创建专门的处理器
const handleButtonClick = curriedHandle('btn-submit')('click')(true);
const handleLinkClick = curriedHandle('link-home')('click')(true);
const handleInputChange = curriedHandle('input-email')('change')(false);

// 直接绑定到元素
button.addEventListener('click', handleButtonClick);
link.addEventListener('click', handleLinkClick);
input.addEventListener('change', handleInputChange);
```

**场景 3: 数据验证器**
```javascript
function validate(rule, errorMsg, value) {
    if (!rule(value)) {
        throw new Error(errorMsg);
    }
    return value;
}

const curriedValidate = curry(validate);

// 创建专门的验证器
const validateEmail = curriedValidate(
    (v) => /\S+@\S+\.\S+/.test(v),
    '邮箱格式不正确'
);

const validateAge = curriedValidate(
    (v) => v >= 18 && v <= 120,
    '年龄必须在 18-120 之间'
);

const validatePassword = curriedValidate(
    (v) => v.length >= 8,
    '密码至少 8 位'
);

// 使用验证器
try {
    validateEmail('user@example.com');  // ✓
    validateAge(25);  // ✓
    validatePassword('12345678');  // ✓

    validateEmail('invalid');  // ✗ 抛出错误
} catch (e) {
    console.error(e.message);
}
```

**场景 4: 数据转换管道**
```javascript
// 柯里化的数组处理函数
const map = curry((fn, arr) => arr.map(fn));
const filter = curry((fn, arr) => arr.filter(fn));
const reduce = curry((fn, init, arr) => arr.reduce(fn, init));

// 创建可复用的转换函数
const double = map((x) => x * 2);
const filterEven = filter((x) => x % 2 === 0);
const sum = reduce((acc, x) => acc + x, 0);

// 单独使用
const numbers = [1, 2, 3, 4, 5];
double(numbers);  // [2, 4, 6, 8, 10]
filterEven(numbers);  // [2, 4]
sum(numbers);  // 15

// 组合使用
const sumOfDoubledEvens = (arr) => sum(double(filterEven(arr)));
sumOfDoubledEvens(numbers);  // 12 (2*2 + 4*2 = 12)
```

---

**规则 5: 柯里化的性能考虑**

柯里化会带来性能开销, 需要权衡使用:

```javascript
function add(a, b, c) {
    return a + b + c;
}

const curriedAdd = curry(add);

// 性能测试 (100 万次调用)
console.time('原始函数');
for (let i = 0; i < 1000000; i++) {
    add(1, 2, 3);
}
console.timeEnd('原始函数');  // ~3ms

console.time('柯里化函数');
for (let i = 0; i < 1000000; i++) {
    curriedAdd(1)(2)(3);
}
console.timeEnd('柯里化函数');  // ~25ms

console.time('偏函数应用');
const add1 = add.bind(null, 1);
const add12 = add1.bind(null, 2);
for (let i = 0; i < 1000000; i++) {
    add12(3);
}
console.timeEnd('偏函数应用');  // ~8ms
```

性能特征:
- **原始函数**: 最快, 无额外开销
- **偏函数应用**: 较快, ~2-3 倍开销
- **柯里化**: 较慢, ~8 倍开销

性能开销来源:
- 创建多个闭包
- 多次函数调用
- 参数数组的扩展和合并
- 递归的 curried 函数调用

使用建议:
- **非热点路径**: 柯里化带来的可读性和复用性远大于性能损耗
- **热点路径**: 使用偏函数应用或直接函数调用
- **配置类代码**: 柯里化非常合适 (调用频率低, 可读性重要)
- **循环内部**: 避免柯里化 (调用频率高, 性能敏感)

---

**规则 6: 柯里化的最佳实践**

**推荐做法**:

```javascript
// ✅ 用于配置函数, 减少重复
const createLogger = curry((level, module, message) => {
    console.log(`[${level}][${module}] ${message}`);
});

const infoLogger = createLogger('INFO');
const debugLogger = createLogger('DEBUG');

// ✅ 用于延迟计算, 等待所有参数
const calculateDiscount = curry((rate, threshold, amount) => {
    return amount > threshold ? amount * (1 - rate) : amount;
});

const vipDiscount = calculateDiscount(0.2, 1000);
vipDiscount(1500);  // 1200
vipDiscount(800);  // 800

// ✅ 用于函数组合
const compose = (...fns) => (x) => fns.reduceRight((v, f) => f(v), x);
const pipe = (...fns) => (x) => fns.reduce((v, f) => f(v), x);

const double = (x) => x * 2;
const addOne = (x) => x + 1;
const square = (x) => x * x;

const process = pipe(double, addOne, square);
process(3);  // (3*2+1)^2 = 49
```

**避免的做法**:

```javascript
// ❌ 避免: 过度柯里化简单函数
const add = curry((a, b) => a + b);  // 不如直接 add(a, b)

// ❌ 避免: 在性能敏感的循环中使用
for (let i = 0; i < 1000000; i++) {
    curriedAdd(i)(2)(3);  // 每次都创建闭包
}

// ✅ 改进: 循环外部创建
const add2 = curriedAdd(2);
const add23 = add2(3);
for (let i = 0; i < 1000000; i++) {
    add23(i);  // 复用已柯里化的函数
}

// ❌ 避免: 参数顺序不合理
const divide = curry((a, b) => a / b);
const divideByTwo = divide(2);  // 固定被除数 2
divideByTwo(10);  // 2 / 10 = 0.2 (可能不是期望的)

// ✅ 改进: 常用的固定参数放在前面
const divide = curry((divisor, dividend) => dividend / divisor);
const divideByTwo = divide(2);
divideByTwo(10);  // 10 / 2 = 5 (更符合直觉)
```

参数顺序原则:
- **配置参数在前, 数据参数在后**
- **变化少的参数在前, 变化多的参数在后**
- **可复用的参数在前, 特定的参数在后**

---

**事故档案编号**: MODULE-2024-1909
**影响范围**: 柯里化, 偏函数应用, 闭包, 函数式编程, 参数绑定
**根本原因**: 代码重复严重, 不理解参数分阶段绑定的模式
**修复成本**: 低 (理解柯里化后容易重构)

这是 JavaScript 世界第 109 次被记录的模块系统事故。柯里化是将多参数函数转换为一系列单参数函数的技术, 通过闭包记住之前的参数, 实现参数的分阶段绑定。柯里化和偏函数应用是不同的技术: 柯里化是自动的、递归的转换, 偏函数应用是手动的、一次性的固定。柯里化在配置函数工厂、事件处理器、数据验证、函数组合等场景下非常有用, 但会带来约 8 倍的性能开销。理解柯里化是掌握函数式编程模式的关键一步。

---

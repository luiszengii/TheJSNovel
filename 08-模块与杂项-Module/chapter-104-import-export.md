《第 104 次记录: 依赖迷宫 —— import/export 的隐藏规则》

---

## 重构项目的导入混乱

周一上午九点, 你盯着项目中 47 个报错的文件, 头开始隐隐作痛。

这是公司的老项目重构——把原来用 IIFE 和全局变量组织的代码迁移到 ES6 模块。技术方案很清晰, 代码也改得很顺利, 但当你运行项目时, 控制台里密密麻麻的错误信息让你怀疑人生:

```
Uncaught SyntaxError: The requested module './utils.js' does not provide an export named 'default'
Uncaught ReferenceError: formatDate is not defined
Uncaught TypeError: userService.login is not a function
```

"不可能啊, " 你喃喃自语, "我明明都加了 export 和 import..."

你打开 `utils.js`, 看到自己写的导出:

```javascript
// utils.js
export function formatPrice(price) {
    return '¥' + price.toFixed(2);
}

export function formatDate(date) {
    return date.toLocaleDateString('zh-CN');
}

export const API_URL = 'https://api.example.com';
```

然后是其他文件的导入:

```javascript
// cart.js
import utils from './utils.js';  // 第一个错误在这里

console.log(utils.formatPrice(99.99));  // TypeError: utils is undefined
```

"等等, " 你困惑了, "我导出了 formatPrice, 为什么 import 会失败?"

你又看到另一个文件:

```javascript
// user.js
import { formatPrice, formatDate } from './utils.js';  // 这个没报错

formatPrice(99.99);  // ✓ 正常工作
```

"同样的 utils.js, 为什么有的导入成功, 有的失败?" 你的眉头皱得更紧了。

更诡异的是, 有些文件你明明用了相同的导入方式, 却出现了完全不同的错误:

```javascript
// api.js
export default class API {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    fetch(path) {
        return fetch(this.baseUrl + path);
    }
}

// main.js
import { API } from './api.js';  // 又一个错误

const api = new API('https://api.example.com');  // TypeError: API is not a constructor
```

你盯着这些导入导出代码, 突然意识到一个从未深思过的问题: **export 和 import 有多种形式, 它们到底有什么区别?**

---

## 具名导出与默认导出的冲突

上午十点, 你决定系统地测试每种导入导出组合。

"先从最简单的开始, " 你想, "具名导出 (named export)。"

你创建了一个测试文件:

```javascript
// test-named.js
export const a = 1;
export function test() {
    console.log('test');
}
```

然后尝试不同的导入方式:

```javascript
// 方式 1: 具名导入
import { a, test } from './test-named.js';
console.log(a);  // 1
test();  // 'test'

// 方式 2: 默认导入
import testNamed from './test-named.js';
console.log(testNamed);  // undefined - 为什么?
```

"等等, " 你愣住了, "用默认导入 (default import) 导入具名导出会得到 undefined?"

你打开控制台, 仔细检查:

```javascript
console.log(typeof testNamed);  // 'undefined'
```

"原来如此, " 你恍然大悟, "**具名导出和默认导出是两个完全独立的通道**!"

你立刻测试了相反的情况:

```javascript
// test-default.js
export default function() {
    console.log('default function');
}

// 导入测试
import { default as fn } from './test-default.js';
fn();  // ✓ 可以工作

import defaultFn from './test-default.js';
defaultFn();  // ✓ 也可以工作
```

"所以默认导出可以用具名导入吗?" 你继续测试:

```javascript
import { test } from './test-default.js';
console.log(test);  // undefined - 不存在这个具名导出
```

"明白了, " 你说, "默认导出的名字是固定的 `default`, 具名导入必须明确写成 `{ default as xxx }`。"

你画了对比图:

```
具名导出 (Named Export):
export const a = 1;        导入: import { a } from './module.js';
export function test() {}  导入: import { test } from './module.js';

默认导出 (Default Export):
export default value;      导入: import value from './module.js';
                          或者: import { default as value } from './module.js';
```

"所以我之前的错误是因为混淆了这两种导出方式!" 你重新检查 `cart.js`:

```javascript
// ❌ 错误: utils.js 使用具名导出, 但我用了默认导入
import utils from './utils.js';

// ✅ 正确: 应该用具名导入
import { formatPrice, formatDate } from './utils.js';
```

---

## 默认导出的身份之谜

上午十一点, 你开始深入研究默认导出的特殊性。

"既然默认导出的名字是 `default`, " 你想, "那它到底是什么?"

你写了测试代码:

```javascript
// test-default.js
export default function test() {
    console.log('我是默认导出的函数');
}

// main.js
import fn from './test-default.js';

console.log(fn.name);  // 'test' - 函数还保留了名字
console.log(typeof fn);  // 'function'
```

"有名字的默认导出..." 你若有所思。

你又测试了匿名默认导出:

```javascript
// test-anonymous.js
export default function() {
    console.log('匿名函数');
}

// main.js
import anonymousFn from './test-anonymous.js';

console.log(anonymousFn.name);  // 'default'
```

"等等, " 你惊讶了, "匿名默认导出的函数名变成了 `default`?"

你继续测试其他情况:

```javascript
// 默认导出表达式
export default 42;

// 默认导出对象
export default {
    name: 'config',
    value: 100
};

// 默认导出类
export default class User {
    constructor(name) {
        this.name = name;
    }
}
```

你在导入端测试:

```javascript
import value from './test-number.js';
console.log(value);  // 42

import config from './test-object.js';
console.log(config.name);  // 'config'

import User from './test-class.js';
const user = new User('Alice');
console.log(user.name);  // 'Alice'
```

"所以默认导出可以是任何值, " 你总结, "数字、对象、函数、类... 导入时的名字可以随意指定。"

但你马上遇到了一个新问题:

```javascript
// api.js
export default class API {
    // ...
}

// 另一个文件中
export const API_URL = 'https://api.example.com';
export default class API {  // SyntaxError: Duplicate export of 'default'
    // ...
}
```

"一个模块只能有一个默认导出, " 你说, "但可以有多个具名导出。"

---

## 混合导出的复杂场景

中午十二点, 你发现了一个更复杂的情况——同时使用默认导出和具名导出。

你在项目中看到了这样的代码:

```javascript
// user-service.js
export default class UserService {
    login(username, password) {
        // 登录逻辑
    }
}

export const USER_ROLES = {
    ADMIN: 'admin',
    USER: 'user',
    GUEST: 'guest'
};

export function validateEmail(email) {
    return /\S+@\S+\.\S+/.test(email);
}
```

"一个模块同时有默认导出和具名导出?" 你困惑。

你尝试导入:

```javascript
// 方式 1: 分别导入
import UserService from './user-service.js';
import { USER_ROLES, validateEmail } from './user-service.js';

// 方式 2: 一起导入
import UserService, { USER_ROLES, validateEmail } from './user-service.js';

// 方式 3: 全部作为对象导入
import * as userService from './user-service.js';
console.log(userService.default);  // UserService 类
console.log(userService.USER_ROLES);  // 角色常量
console.log(userService.validateEmail);  // 验证函数
```

"太神奇了, " 你说, "**默认导出和具名导出可以共存, 而且可以一起导入**!"

你画了完整的导入方式对比:

```javascript
// 只导入默认导出
import UserService from './user-service.js';

// 只导入具名导出
import { USER_ROLES, validateEmail } from './user-service.js';

// 混合导入 (默认 + 具名)
import UserService, { USER_ROLES, validateEmail } from './user-service.js';

// 全部导入为命名空间对象
import * as userService from './user-service.js';

// 重命名导入
import { validateEmail as checkEmail } from './user-service.js';

// 仅执行模块, 不导入任何内容
import './user-service.js';
```

但你马上遇到了一个新的陷阱:

```javascript
// config.js
export default {
    apiUrl: 'https://api.example.com',
    timeout: 5000
};

export const ENV = 'production';

// main.js
import * as config from './config.js';

console.log(config.apiUrl);  // undefined - 为什么?
console.log(config.default.apiUrl);  // 'https://api.example.com' - 要用 default 访问
console.log(config.ENV);  // 'production' - 具名导出直接访问
```

"原来用 `import * as` 导入时, " 你恍然大悟, "**默认导出会挂载在 `default` 属性上**!"

---

## 重导出的聚合模式

下午两点, 你开始整理项目的导出结构。

项目中有很多工具函数分散在不同文件中:

```javascript
// utils/format.js
export function formatPrice(price) { /* ... */ }
export function formatDate(date) { /* ... */ }

// utils/validate.js
export function validateEmail(email) { /* ... */ }
export function validatePhone(phone) { /* ... */ }

// utils/transform.js
export function camelToSnake(str) { /* ... */ }
export function snakeToCamel(str) { /* ... */ }
```

"每次使用这些工具函数都要写三个 import, " 你想, "能不能聚合成一个入口?"

你查阅文档, 发现了 **re-export (重导出)** 语法:

```javascript
// utils/index.js
export * from './format.js';
export * from './validate.js';
export * from './transform.js';
```

"太方便了, " 你兴奋地说, "现在可以统一从 utils 导入了:"

```javascript
// 之前: 分散导入
import { formatPrice } from './utils/format.js';
import { validateEmail } from './utils/validate.js';
import { camelToSnake } from './utils/transform.js';

// 现在: 统一导入
import { formatPrice, validateEmail, camelToSnake } from './utils/index.js';
```

但你马上遇到了命名冲突:

```javascript
// utils/format.js
export function format(value) {
    return String(value);
}

// utils/transform.js
export function format(value) {  // 同名函数
    return value.trim();
}

// utils/index.js
export * from './format.js';
export * from './transform.js';  // SyntaxError: Duplicate export of 'format'
```

"重导出不能有同名导出, " 你说, "必须重命名。"

你修改了代码:

```javascript
// utils/index.js
export { format as formatString } from './format.js';
export { format as transformString } from './transform.js';
export * from './validate.js';  // 其他不冲突的可以用 *
```

你又发现了一个问题——重导出默认导出:

```javascript
// components/button.js
export default class Button { /* ... */ }

// components/input.js
export default class Input { /* ... */ }

// components/index.js
export * from './button.js';  // ❌ 不会导出 Button 的默认导出
export * from './input.js';   // ❌ 不会导出 Input 的默认导出
```

"等等, " 你测试后发现, "`export *` 不会重导出默认导出?"

你查阅规范, 确认了这个行为:

```javascript
// components/index.js
// ❌ 错误: export * 跳过默认导出
export * from './button.js';

// ✅ 正确: 明确重导出默认导出
export { default as Button } from './button.js';
export { default as Input } from './input.js';
```

"所以 `export *` 只重导出具名导出, " 你总结, "默认导出必须显式重导出并重命名。"

---

## 动态导入名与模块路径

下午三点, 你遇到了一个调试噩梦。

团队成员提交了一段代码:

```javascript
import { userService } from './services.js';

userService.login('alice', '123456');  // TypeError: userService is undefined
```

你打开 `services.js`:

```javascript
// services.js
export const userService = {
    login(username, password) {
        // ...
    }
};
```

"明明有 userService 导出, 为什么导入是 undefined?" 你困惑不解。

你仔细检查文件路径, 突然发现了问题:

```javascript
// 团队成员写的路径
import { userService } from './services.js';

// 实际的文件名
services/user-service.js  // 文件名是 user-service, 不是 services
```

"路径错误会导致模块找不到, " 你说, "但为什么没有报 `module not found` 错误?"

你创建了一个测试:

```javascript
import { test } from './non-existent.js';  // Error: Cannot find module
```

"奇怪, " 你皱眉, "为什么团队成员的代码没报错?"

你深入排查, 发现项目中有两个文件:

```
services.js          // 空导出文件 (旧文件, 应该删除)
user-service.js      // 实际的服务文件
```

你打开 `services.js`:

```javascript
// services.js (旧文件)
// 空文件, 没有任何导出
```

"原来如此, " 你恍然大悟, "导入的是一个空文件, 所以 userService 是 undefined, 而不是报错!"

你又发现了另一个陷阱——相对路径的细微差异:

```javascript
// 当前文件: /src/components/cart.js

import { formatPrice } from './utils.js';      // 查找: /src/components/utils.js
import { formatPrice } from '../utils.js';     // 查找: /src/utils.js
import { formatPrice } from '../../utils.js';  // 查找: /utils.js (项目根目录)
```

"一个点和两个点的差别可能导致完全不同的模块, " 你说, "而且错误提示往往不明显。"

---

## 导入的只读特性与陷阱

下午四点, 你遇到了一个诡异的 bug。

产品经理报告: "配置修改功能不工作, 点击保存后, 值没有改变。"

你查看代码:

```javascript
// config.js
export let apiUrl = 'https://api.example.com';
export let timeout = 5000;

// settings.js
import { apiUrl, timeout } from './config.js';

function updateSettings() {
    apiUrl = 'https://new-api.example.com';  // 尝试修改
    timeout = 10000;
}

updateSettings();
console.log(apiUrl);  // 期望输出新值
```

你运行代码, 浏览器直接报错:

```
TypeError: Assignment to constant variable
```

"什么?!" 你惊讶了, "apiUrl 明明是 let, 不是 const, 为什么不能赋值?"

你查阅文档, 看到了一个关键说明:

> **导入的绑定是只读的。无论导出时用的是 let、var 还是 const, 导入方都不能重新赋值。**

"所以导入的变量永远是只读的, " 你恍然大悟, "即使导出方用的是 let!"

你测试了其他情况:

```javascript
// config.js
export let count = 0;

export function increment() {
    count++;  // ✓ 导出方可以修改
}

// main.js
import { count, increment } from './config.js';

console.log(count);  // 0

increment();
console.log(count);  // 1 - 可以看到导出方的修改

count = 10;  // ❌ TypeError: 导入方不能赋值
```

"原来导入是 **活动绑定 (live binding)**, " 你说, "不是值的拷贝, 而是对导出变量的引用。"

你画了数据流向图:

```
导出方 (config.js):
let count = 0;  ────────────┐
                            │ 活动绑定
导入方 (main.js):           │
import { count }  ←─────────┘

导出方修改 count:
count++  →  导入方的 count 也变化

导入方修改 count:
count = 10  →  TypeError (只读)
```

但你发现了一个例外——对象属性:

```javascript
// config.js
export const config = {
    apiUrl: 'https://api.example.com',
    timeout: 5000
};

// main.js
import { config } from './config.js';

config = {};  // ❌ TypeError: 不能重新赋值 config 本身

config.apiUrl = 'https://new-api.example.com';  // ✓ 可以修改对象属性
config.timeout = 10000;  // ✓ 可以修改
```

"虽然不能重新赋值导入的变量, " 你总结, "但如果导入的是对象, 可以修改对象的属性。"

你修复了配置修改功能:

```javascript
// config.js
export const config = {
    apiUrl: 'https://api.example.com',
    timeout: 5000
};

// settings.js
import { config } from './config.js';

function updateSettings(newApiUrl, newTimeout) {
    config.apiUrl = newApiUrl;      // ✓ 修改属性
    config.timeout = newTimeout;    // ✓ 修改属性
}
```

---

## 导入提升与执行顺序

下午五点, 你注意到一个奇怪的现象。

你在代码中先使用了一个函数, 然后才导入:

```javascript
// main.js
console.log(formatPrice(99.99));  // 期望报错: formatPrice is not defined

import { formatPrice } from './utils.js';
```

你运行代码, 震惊地发现居然可以工作:

```
¥99.99
```

"等等, " 你盯着代码, "import 在使用之后, 为什么没报错?"

你查阅规范, 发现了 **import 提升 (hoisting)** 规则:

> **import 声明会被提升到模块顶部, 在任何代码执行之前就完成导入。**

你测试了更复杂的情况:

```javascript
// 代码编写顺序
console.log('1');

import { a } from './module-a.js';

console.log('2');

import { b } from './module-b.js';

console.log('3');

// 实际执行顺序
import { a } from './module-a.js';  // 提升到顶部
import { b } from './module-b.js';  // 提升到顶部

console.log('1');
console.log('2');
console.log('3');
```

"所以 import 的位置不影响执行顺序, " 你说, "它们总是最先执行。"

但你发现了一个陷阱——导入的模块会立即执行:

```javascript
// init.js
console.log('init 模块执行');

export const config = {
    initialized: true
};

// main.js
console.log('main 开始');

import { config } from './init.js';

console.log('main 结束');

// 输出顺序:
// init 模块执行    ← import 导致 init.js 立即执行
// main 开始
// main 结束
```

"导入一个模块会立即执行该模块, " 你总结, "而且只执行一次, 后续导入会使用缓存。"

---

## 你的 import/export 笔记本

晚上八点, 你整理了今天的收获。

你在笔记本上写下标题: "import/export —— 依赖的明确通道"

### 核心洞察 #1: 具名导出与默认导出

你写道:

"具名导出和默认导出是两个独立的通道:

```javascript
// 具名导出
export const a = 1;
export function test() {}

// 导入: 必须用 {}
import { a, test } from './module.js';

// 默认导出
export default class User {}

// 导入: 不用 {}, 名字随意
import User from './module.js';
import MyUser from './module.js';  // 名字可以不同

// 混合导出
export default class User {}
export const USER_ROLES = {};

// 混合导入
import User, { USER_ROLES } from './module.js';
```

关键规则:
- 一个模块只能有一个默认导出
- 可以有任意多个具名导出
- 两种导出可以共存
- 导入方式必须匹配导出方式"

### 核心洞察 #2: 重导出与聚合

"重导出可以聚合多个模块:

```javascript
// utils/index.js
export * from './format.js';  // 重导出所有具名导出
export { default as Button } from './button.js';  // 重导出默认导出
export { format as formatString } from './format.js';  // 重命名重导出
```

重导出规则:
- `export *` 只重导出具名导出, 跳过默认导出
- 默认导出必须显式重导出并重命名
- 重导出不能有同名导出, 必须重命名"

### 核心洞察 #3: 导入的只读特性

"导入的绑定是只读的, 但是活动绑定:

```javascript
// module.js
export let count = 0;
export function increment() {
    count++;
}

// main.js
import { count, increment } from './module.js';

console.log(count);  // 0
increment();
console.log(count);  // 1 - 可以看到模块内部的修改

count = 10;  // ❌ TypeError - 不能重新赋值

// 对象属性例外
export const config = { value: 0 };
import { config } from './module.js';
config = {};  // ❌ 不能重新赋值
config.value = 10;  // ✓ 可以修改属性
```

只读规则:
- 导入的变量不能重新赋值
- 但可以看到模块内部的修改
- 对象属性可以修改"

### 核心洞察 #4: import 提升

"import 声明会被提升到模块顶部:

```javascript
// 代码编写顺序
console.log(a);  // 可以访问
import { a } from './module.js';

// 实际执行顺序 (提升后)
import { a } from './module.js';
console.log(a);
```

提升规则:
- import 总是最先执行
- 导入的模块会立即执行
- 可以在 import 前使用导入的变量
- 但导入的是模块导出的最终值"

你合上笔记本, 关掉电脑。

"明天要学习动态导入了, " 你想, "今天终于理解了 import/export 的细节——它们不仅仅是导入导出, 而是模块之间的依赖通道。具名导出和默认导出是两个独立的系统, 导入是只读但活动的绑定, import 会被提升到顶部。理解这些细节, 才能避免导入导出的陷阱。"

---

## 知识总结

**规则 1: 具名导出 (Named Export)**

具名导出可以有多个, 导入时必须使用相同的名字:

```javascript
// module.js
export const API_URL = 'https://api.example.com';
export function fetchData() { /* ... */ }
export class User { /* ... */ }

// 导入: 必须用 {}
import { API_URL, fetchData, User } from './module.js';

// 重命名导入
import { fetchData as getData } from './module.js';

// 导入所有具名导出
import * as module from './module.js';
console.log(module.API_URL);
console.log(module.fetchData);
```

导出时机:
- 声明时导出 (推荐): `export const a = 1;`
- 统一导出: `const a = 1; export { a };`
- 重命名导出: `const internal = 1; export { internal as a };`

---

**规则 2: 默认导出 (Default Export)**

每个模块只能有一个默认导出, 导入时名字可以随意指定:

```javascript
// module.js
export default class User {
    constructor(name) {
        this.name = name;
    }
}

// 或者
class User { /* ... */ }
export default User;

// 或者
export default function() { /* ... */ }

// 导入: 不用 {}, 名字随意
import User from './module.js';
import MyUser from './module.js';  // 名字可以不同
```

默认导出的本质:
- 默认导出的名字是 `default`
- `import User from './m.js'` 等价于 `import { default as User } from './m.js'`
- 可以导出任何值: 数字、对象、函数、类

---

**规则 3: 混合导出**

一个模块可以同时有默认导出和具名导出:

```javascript
// user-service.js
export default class UserService {
    login(username, password) { /* ... */ }
}

export const USER_ROLES = {
    ADMIN: 'admin',
    USER: 'user'
};

export function validateEmail(email) { /* ... */ }
```

混合导入方式:

```javascript
// 方式 1: 分别导入
import UserService from './user-service.js';
import { USER_ROLES, validateEmail } from './user-service.js';

// 方式 2: 一起导入 (推荐)
import UserService, { USER_ROLES, validateEmail } from './user-service.js';

// 方式 3: 全部作为对象导入
import * as userService from './user-service.js';
console.log(userService.default);  // UserService 类
console.log(userService.USER_ROLES);  // 角色常量
```

注意: 用 `import * as` 时, 默认导出挂载在 `default` 属性上

---

**规则 4: 重导出 (Re-export)**

重导出用于聚合多个模块的导出:

```javascript
// utils/index.js

// 重导出所有具名导出
export * from './format.js';
export * from './validate.js';

// 重导出并重命名
export { format as formatString } from './format.js';
export { format as transformString } from './transform.js';

// 重导出默认导出 (必须重命名)
export { default as Button } from './button.js';
export { default as Input } from './input.js';
```

重导出规则:
- `export *` 只重导出具名导出, **不包括默认导出**
- 默认导出必须显式重导出: `export { default as Name } from './m.js'`
- 同名导出会冲突, 必须重命名
- 重导出不会在当前模块创建绑定 (不能在当前模块使用重导出的内容)

---

**规则 5: 导入路径规则**

导入路径必须遵循特定规则:

```javascript
// 相对路径 (必须以 ./ 或 ../ 开头)
import { a } from './module.js';      // 当前目录
import { b } from '../module.js';     // 上级目录
import { c } from '../../module.js';  // 上上级目录

// 绝对路径 (从项目根目录开始)
import { d } from '/src/utils/module.js';

// 包名 (node_modules)
import React from 'react';
import { useState } from 'react';
```

路径陷阱:
- 相对路径的起点是**当前文件所在目录**, 不是项目根目录
- 路径错误会导致 "module not found" 错误
- 导入一个空模块不会报错, 但所有导入的值是 undefined

---

**规则 6: 导入的只读特性 (Read-only Bindings)**

导入的变量是只读的, 不能重新赋值:

```javascript
// module.js
export let count = 0;
export const config = { value: 0 };

export function increment() {
    count++;  // ✓ 模块内部可以修改
}

// main.js
import { count, config, increment } from './module.js';

console.log(count);  // 0

increment();
console.log(count);  // 1 - 可以看到模块内部的修改

count = 10;  // ❌ TypeError: Assignment to constant variable
let count = 10;  // ❌ SyntaxError: Identifier 'count' has already been declared

config = {};  // ❌ TypeError: 不能重新赋值 config 本身
config.value = 10;  // ✓ 可以修改对象的属性
```

只读规则:
- 导入的变量是**活动绑定 (live binding)**, 不是值的拷贝
- 导入方不能重新赋值, 无论导出时用的是 let、var 还是 const
- 但可以看到模块内部对变量的修改
- 如果导入的是对象, 可以修改对象的属性 (但不能替换整个对象)

---

**规则 7: import 提升 (Hoisting)**

import 声明会被提升到模块顶部, 在任何代码执行之前完成导入:

```javascript
// 代码编写顺序
console.log('1');

import { a } from './module-a.js';  // 会被提升

console.log('2');

import { b } from './module-b.js';  // 会被提升

console.log('3');

// 实际执行顺序 (提升后)
import { a } from './module-a.js';
import { b } from './module-b.js';

console.log('1');
console.log('2');
console.log('3');
```

提升特性:
- import 总是最先执行, 在任何代码之前
- 可以在 import 前使用导入的变量 (因为已经提升)
- 导入的模块会立即执行
- 导入路径必须是字符串字面量, 不能是变量

注意: export 不会被提升, 不能在声明前使用导出的变量

---

**规则 8: 仅执行模块 (Side-effect Import)**

可以导入一个模块但不导入任何内容, 仅执行模块代码:

```javascript
// init.js
console.log('初始化全局配置');

window.APP_CONFIG = {
    version: '1.0.0'
};

// main.js
import './init.js';  // 仅执行 init.js, 不导入任何内容

console.log(window.APP_CONFIG.version);  // '1.0.0'
```

使用场景:
- 初始化全局配置
- 注册全局事件监听器
- Polyfill 加载
- CSS 样式导入: `import './styles.css';`

---

**规则 9: 导入导出的最佳实践**

**推荐做法**:

```javascript
// ✅ 声明时导出 (最清晰)
export const API_URL = 'https://api.example.com';
export function fetchData() { /* ... */ }

// ✅ 默认导出用于主要功能
export default class UserService { /* ... */ }

// ✅ 具名导出用于辅助功能
export const USER_ROLES = { /* ... */ };
export function validateEmail() { /* ... */ }

// ✅ 使用 index.js 聚合导出
// utils/index.js
export * from './format.js';
export * from './validate.js';
```

**避免的做法**:

```javascript
// ❌ 避免: 导出后立即导入同一个模块
export { a } from './module.js';
import { a } from './module.js';  // 冗余

// ❌ 避免: 默认导出匿名函数 (不利于调试)
export default function() { /* ... */ }

// ✅ 改进: 给函数命名
export default function processData() { /* ... */ }

// ❌ 避免: 过度使用 export *
export * from './a.js';
export * from './b.js';
export * from './c.js';  // 命名空间污染

// ✅ 改进: 明确导出需要的内容
export { funcA, funcB } from './a.js';
export { funcC } from './b.js';
```

---

**事故档案编号**: MODULE-2024-1904
**影响范围**: import/export 语法, 具名导出, 默认导出, 重导出, 只读绑定
**根本原因**: 混淆具名导出和默认导出, 不理解导入的只读特性
**修复成本**: 低 (理解规则后容易修复)

这是 JavaScript 世界第 104 次被记录的模块系统事故。具名导出和默认导出是两个独立的通道, 导入方式必须匹配导出方式。一个模块只能有一个默认导出, 但可以有任意多个具名导出。重导出可以聚合多个模块, 但 `export *` 不包括默认导出。导入的变量是只读的活动绑定, 不能重新赋值但可以看到模块内部的修改。import 声明会被提升到模块顶部, 在任何代码执行之前完成导入。理解 import/export 的细节是避免模块化陷阱的关键。

---

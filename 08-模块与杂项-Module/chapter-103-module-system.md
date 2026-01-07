《第 103 次记录: 全局污染灾难 —— 模块系统的作用域隔离》

---

## 变量冲突的噩梦

周二上午九点, 你盯着控制台里的错误信息, 完全不敢相信自己的眼睛。

这是一个大型电商项目, 你刚刚把自己负责的购物车模块部署到测试环境。代码在本地运行得很完美, 但一部署到测试环境, 整个网站就崩溃了。

更诡异的是, 错误信息显示: `Uncaught TypeError: initCart is not a function`

"什么?!" 你困惑, "`initCart` 明明是我定义的函数啊!"

你打开测试环境的控制台, 输入 `typeof initCart`:

```javascript
console.log(typeof initCart);  // "number"
```

"number?!" 你震惊了, "我的函数怎么变成了数字?"

你继续检查:

```javascript
console.log(initCart);  // 0
```

"我的 `initCart` 函数被覆盖成了数字 0!" 你喃喃自语。

你打开项目的 HTML 文件, 看到了多个 script 标签:

```html
<!DOCTYPE html>
<html>
<head>
    <title>电商网站</title>
</head>
<body>
    <!-- 第三方统计库 -->
    <script src="analytics.js"></script>

    <!-- 第三方广告库 -->
    <script src="ads.js"></script>

    <!-- 你的购物车模块 -->
    <script src="cart.js"></script>

    <!-- 主应用 -->
    <script src="app.js"></script>
</body>
</html>
```

你打开 `analytics.js`, 搜索 `initCart`:

```javascript
// analytics.js
var initCart = 0;  // 初始化购物车计数

function trackCartInit() {
    initCart++;
    sendAnalytics('cart_init', initCart);
}
```

"天哪!" 你惊呼, "第三方库也定义了一个 `initCart` 变量!"

你的 `cart.js` 代码:

```javascript
// cart.js
function initCart() {
    console.log('购物车初始化');
    // ... 初始化逻辑
}
```

"所有 script 标签共享全局作用域, " 你意识到问题的严重性, "后加载的脚本会覆盖之前的同名变量!"

---

## IIFE 临时方案的尝试

上午十点, 你想起了 IIFE (立即执行函数表达式) 的隔离技巧。

"可以用 IIFE 创建局部作用域, " 你想, "避免污染全局。"

你修改了 `cart.js`:

```javascript
// cart.js
(function() {
    // 私有作用域
    var cartItems = [];

    function initCart() {
        console.log('购物车初始化');
        cartItems = [];
    }

    function addToCart(item) {
        cartItems.push(item);
        console.log('添加商品:', item);
    }

    // 暴露到全局
    window.ShoppingCart = {
        init: initCart,
        add: addToCart
    };
})();
```

你测试了一下:

```javascript
ShoppingCart.init();  // 正常工作
ShoppingCart.add({ id: 1, name: '商品' });  // 正常工作
```

"这样就不会污染全局了, " 你满意地说, "只暴露一个 `ShoppingCart` 对象。"

但你马上发现了新问题。你的购物车模块依赖另一个工具库 `utils.js`:

```javascript
// utils.js
(function() {
    function formatPrice(price) {
        return '¥' + price.toFixed(2);
    }

    window.Utils = {
        formatPrice: formatPrice
    };
})();

// cart.js
(function() {
    function displayCart() {
        // 需要使用 Utils.formatPrice
        var price = 99.99;
        console.log(Utils.formatPrice(price));  // 依赖 Utils
    }

    window.ShoppingCart = {
        display: displayCart
    };
})();
```

"依赖关系不清晰, " 你皱眉, "必须确保 `utils.js` 在 `cart.js` 之前加载, 否则会报错。而且 HTML 里的 script 标签顺序一旦错了, 整个应用就崩溃..."

你在 HTML 中小心翼翼地排列顺序:

```html
<script src="utils.js"></script>      <!-- 必须先加载 -->
<script src="cart.js"></script>       <!-- 依赖 utils -->
<script src="checkout.js"></script>   <!-- 依赖 cart -->
<script src="app.js"></script>        <!-- 依赖所有模块 -->
```

"这太脆弱了, " 你说, "而且依赖关系完全隐藏在代码内部, 维护时很容易出错。"

---

## ES6 模块的救赎

上午十一点, 你的同事老张走了过来。

"为什么不用 ES6 模块?" 他看了一眼你的代码, "现代浏览器都支持了。"

"ES6 模块?" 你困惑, "那是什么?"

"JavaScript 的官方模块系统, " 老张说, "每个文件都是独立的模块, 有自己的作用域, 不会污染全局。"

他打开一个新文件, 快速写下示例:

```javascript
// utils.js
export function formatPrice(price) {
    return '¥' + price.toFixed(2);
}

export function formatDate(date) {
    return date.toLocaleDateString('zh-CN');
}

// cart.js
import { formatPrice } from './utils.js';

let cartItems = [];  // 模块私有变量

export function initCart() {
    console.log('购物车初始化');
    cartItems = [];
}

export function addToCart(item) {
    cartItems.push(item);
    console.log('添加商品:', formatPrice(item.price));
}
```

"等等, " 你盯着代码, "这些变量和函数不会污染全局?"

"不会, " 老张说, "每个模块都有自己的作用域。`cartItems` 是模块私有的, 外部无法访问。只有 `export` 的内容才能被其他模块使用。"

你测试了一下:

```javascript
// app.js
import { initCart, addToCart } from './cart.js';

initCart();
addToCart({ id: 1, name: '商品', price: 99.99 });

console.log(typeof cartItems);  // "undefined" - 模块私有, 无法访问
```

"太神奇了!" 你说, "依赖关系也变得清晰了——import 语句明确声明了依赖!"

但你马上遇到了一个问题。你尝试在 HTML 中加载模块:

```html
<script src="app.js"></script>
```

浏览器报错:

```
Uncaught SyntaxError: Cannot use import statement outside a module
```

"什么?!" 你困惑。

老张解释: "需要在 script 标签上添加 `type="module"`:"

```html
<script type="module" src="app.js"></script>
```

"这样浏览器才会把它当作 ES6 模块处理。"

---

## 模块作用域的真相

中午十二点, 你开始深入研究模块作用域。

"模块到底创建了什么样的作用域?" 你自问。

你写了测试代码:

```javascript
// test-module.js
console.log('模块开始执行');

var a = 1;
let b = 2;
const c = 3;

function test() {
    console.log('test 函数');
}

console.log('模块执行完成');
```

你在另一个模块中尝试访问这些变量:

```javascript
// main.js
import './test-module.js';

console.log(typeof a);  // "undefined"
console.log(typeof b);  // "undefined"
console.log(typeof c);  // "undefined"
console.log(typeof test);  // "undefined"
```

"所有变量都是 undefined!" 你惊讶, "即使是 var 声明的变量也无法被外部访问!"

你又测试了 window 对象:

```javascript
// test-module.js
var a = 1;
console.log(window.a);  // undefined

// 传统 script 标签
<script>
var a = 1;
console.log(window.a);  // 1
</script>
```

"在模块中, `var` 不会挂载到 `window` 上!" 你恍然大悟, "模块有自己的顶层作用域, 完全独立于全局作用域。"

你画了对比图:

```
传统 script 标签:
var a = 1  →  挂载到 window.a
全局污染, 所有脚本共享

ES6 模块:
var a = 1  →  模块私有变量
不挂载到 window, 完全隔离
只有 export 的内容才能被访问
```

"这就是作用域隔离的威力, " 你说, "再也不用担心变量名冲突了!"

---

## import 和 export 的多种形式

下午两点, 你开始学习 import 和 export 的各种语法。

"export 可以导出多个东西, " 你查阅文档, "有多种写法。"

你总结了 export 的方式:

```javascript
// 方式 1: 声明时导出
export const API_URL = 'https://api.example.com';

export function fetchData(id) {
    return fetch(`${API_URL}/data/${id}`);
}

export class User {
    constructor(name) {
        this.name = name;
    }
}

// 方式 2: 统一导出
const API_URL = 'https://api.example.com';

function fetchData(id) {
    return fetch(`${API_URL}/data/${id}`);
}

class User {
    constructor(name) {
        this.name = name;
    }
}

export { API_URL, fetchData, User };

// 方式 3: 重命名导出
const internalUrl = 'https://api.example.com';
export { internalUrl as API_URL };

// 方式 4: 默认导出
export default function() {
    console.log('默认导出的函数');
}
```

你又学习了 import 的方式:

```javascript
// 方式 1: 导入具名导出
import { API_URL, fetchData } from './api.js';

// 方式 2: 导入并重命名
import { API_URL as apiUrl, fetchData as fetch } from './api.js';

// 方式 3: 导入所有
import * as API from './api.js';
console.log(API.API_URL);
console.log(API.fetchData);

// 方式 4: 导入默认导出
import defaultFunc from './api.js';

// 方式 5: 混合导入
import defaultFunc, { API_URL, fetchData } from './api.js';

// 方式 6: 仅执行模块
import './init.js';  // 只执行, 不导入任何内容
```

"这么多种方式!" 你说, "但核心原理都是一样的——显式声明依赖关系。"

---

## 模块只执行一次

下午三点, 你发现了模块的一个重要特性。

"如果多个模块都导入同一个模块, 会执行多次吗?" 你好奇。

你写了测试:

```javascript
// config.js
console.log('config 模块执行');

export const config = {
    apiUrl: 'https://api.example.com'
};

// moduleA.js
import { config } from './config.js';
console.log('moduleA 使用 config');

// moduleB.js
import { config } from './config.js';
console.log('moduleB 使用 config');

// main.js
import './moduleA.js';
import './moduleB.js';
```

你运行代码, 输出:

```
config 模块执行
moduleA 使用 config
moduleB 使用 config
```

"config 模块只执行了一次!" 你惊讶, "即使被多个模块导入。"

你又测试了修改导出对象:

```javascript
// config.js
export const config = {
    count: 0
};

// moduleA.js
import { config } from './config.js';
config.count++;
console.log('moduleA 中 count:', config.count);

// moduleB.js
import { config } from './config.js';
config.count++;
console.log('moduleB 中 count:', config.count);

// main.js
import './moduleA.js';
import './moduleB.js';
```

输出:

```
moduleA 中 count: 1
moduleB 中 count: 2
```

"所有导入共享同一个对象!" 你恍然大悟, "模块是单例的——只执行一次, 然后被缓存。所有 import 都引用同一个实例。"

你画了执行流程图:

```
首次 import config.js:
  → 执行模块代码
  → 缓存导出对象
  → 返回导出对象

后续 import config.js:
  → 直接返回缓存的导出对象
  → 不再执行模块代码
```

"这就是为什么模块适合做单例模式, " 你说, "天然保证只创建一次。"

---

## 循环依赖的陷阱

下午四点, 你遇到了一个棘手的问题。

你的购物车模块需要使用用户模块的数据, 但用户模块又需要访问购物车的统计信息:

```javascript
// cart.js
import { getCurrentUser } from './user.js';

let cartItems = [];

export function addToCart(item) {
    const user = getCurrentUser();
    console.log(`用户 ${user.name} 添加了商品`);
    cartItems.push(item);
}

export function getCartCount() {
    return cartItems.length;
}

// user.js
import { getCartCount } from './cart.js';

let currentUser = null;

export function getCurrentUser() {
    return currentUser;
}

export function initUser(user) {
    currentUser = user;
    console.log(`用户 ${user.name} 已登录, 购物车有 ${getCartCount()} 件商品`);
}
```

你运行代码:

```javascript
// main.js
import { initUser } from './user.js';
import { addToCart } from './cart.js';

initUser({ name: '张三' });
```

控制台输出:

```
Uncaught ReferenceError: Cannot access 'getCurrentUser' before initialization
```

"什么?!" 你困惑, "循环依赖导致错误?"

你仔细分析执行流程:

```
1. main.js 导入 user.js
   → user.js 开始执行
   → user.js 导入 cart.js

2. cart.js 开始执行
   → cart.js 导入 user.js (已经在执行中)
   → cart.js 尝试访问 getCurrentUser
   → 但 getCurrentUser 还没有被定义 (user.js 还没执行完)
   → 错误!
```

"模块在执行过程中就可以被导入, " 你说, "如果还没执行完, 导出的变量可能还是 undefined..."

你重构了代码, 避免循环依赖:

```javascript
// cart.js
let cartItems = [];
let userGetter = null;

// 通过依赖注入避免循环依赖
export function setUserGetter(getter) {
    userGetter = getter;
}

export function addToCart(item) {
    if (userGetter) {
        const user = userGetter();
        console.log(`用户 ${user.name} 添加了商品`);
    }
    cartItems.push(item);
}

export function getCartCount() {
    return cartItems.length;
}

// user.js
import { setUserGetter, getCartCount } from './cart.js';

let currentUser = null;

export function getCurrentUser() {
    return currentUser;
}

export function initUser(user) {
    currentUser = user;
    setUserGetter(getCurrentUser);  // 注入依赖
    console.log(`用户 ${user.name} 已登录, 购物车有 ${getCartCount()} 件商品`);
}
```

"通过依赖注入解耦, " 你满意地说, "避免了循环依赖的陷阱。"

---

## 你的模块系统笔记本

晚上八点, 你整理了今天的收获。

你在笔记本上写下标题: "模块系统 —— 作用域的护城河"

### 核心洞察 #1: 模块的作用域隔离

你写道:

"ES6 模块为每个文件创建独立的作用域:

```javascript
// module.js
var a = 1;        // 模块私有, 不挂载到 window
let b = 2;        // 模块私有
const c = 3;      // 模块私有

function test() { // 模块私有
    console.log('test');
}

// 只有 export 的内容才能被外部访问
export { a };
```

隔离特性:
- 每个模块有独立的顶层作用域
- var 声明不会挂载到 window
- 未 export 的变量完全私有
- 避免全局命名冲突
- 依赖关系清晰可见"

### 核心洞察 #2: 模块的单例特性

"模块只执行一次, 然后被缓存:

```javascript
// config.js
console.log('执行 config 模块');
export const config = { count: 0 };

// moduleA.js
import { config } from './config.js';
config.count++;  // 修改共享对象

// moduleB.js
import { config } from './config.js';
console.log(config.count);  // 1 - 看到 moduleA 的修改
```

单例规则:
- 首次 import 时执行模块并缓存
- 后续 import 返回缓存的导出对象
- 所有 import 共享同一个实例
- 适合实现单例模式"

### 核心洞察 #3: 循环依赖的风险

"循环依赖可能导致访问未初始化的变量:

```javascript
// a.js
import { b } from './b.js';
export const a = 'a';

// b.js
import { a } from './a.js';  // a 可能还未定义
export const b = 'b';
```

解决方案:
- 重构代码避免循环依赖
- 使用依赖注入解耦
- 延迟访问 (函数内访问, 而非模块顶层)
- 提取公共依赖到第三个模块"

### 核心洞察 #4: import 的提升特性

"import 声明会被提升到模块顶部:

```javascript
// 实际执行顺序
console.log(API_URL);  // ✓ 可以访问

import { API_URL } from './config.js';  // import 被提升

// 等价于
import { API_URL } from './config.js';
console.log(API_URL);
```

提升规则:
- import 声明总是最先执行
- 可以在 import 前使用导入的变量
- 但导入的是模块导出的最终值"

你合上笔记本, 关掉电脑。

"明天继续学习动态导入, " 你想, "今天终于理解了模块系统的本质——不仅是语法糖, 更是作用域隔离机制。每个模块都是一座孤岛, 通过 import/export 搭建桥梁。理解模块系统, 才能写出可维护的大型应用。"

---

## 知识总结

**规则 1: 模块的独立作用域**

ES6 模块为每个文件创建独立的顶层作用域:

```javascript
// module.js
var globalVar = 1;      // 模块私有, 不是全局变量
let moduleVar = 2;      // 模块私有
const CONFIG = 3;       // 模块私有

function helper() {     // 模块私有函数
    return 'helper';
}

console.log(window.globalVar);  // undefined - 不挂载到 window

// 只有 export 的内容才能被外部访问
export { globalVar, CONFIG };
```

作用域特性:
- 每个模块有独立的顶层作用域, 不是全局作用域
- `var` 声明的变量不会成为 `window` 的属性
- 未 `export` 的变量和函数完全私有
- 避免全局命名空间污染
- 提供天然的封装机制

对比传统 script 标签:
```javascript
// 传统 script 标签
<script>
var a = 1;
console.log(window.a);  // 1 - 全局变量
</script>

// ES6 模块
<script type="module">
var a = 1;
console.log(window.a);  // undefined - 模块私有
</script>
```

---

**规则 2: export 导出语法**

export 有多种导出方式:

```javascript
// 方式 1: 声明时导出 (推荐)
export const API_URL = 'https://api.example.com';

export function fetchData(id) {
    return fetch(`${API_URL}/data/${id}`);
}

export class User {
    constructor(name) {
        this.name = name;
    }
}

// 方式 2: 统一导出
const API_URL = 'https://api.example.com';
function fetchData(id) { /* ... */ }
class User { /* ... */ }

export { API_URL, fetchData, User };

// 方式 3: 重命名导出
const internalUrl = 'https://api.example.com';
export { internalUrl as API_URL };

// 方式 4: 默认导出 (每个模块只能有一个)
export default function() {
    console.log('默认导出');
}

// 或者
function main() { /* ... */ }
export default main;
```

导出规则:
- 具名导出: 可以有多个, 导入时必须使用相同名称
- 默认导出: 每个模块只能有一个, 导入时可以使用任意名称
- 可以同时使用具名导出和默认导出
- export 必须在模块顶层, 不能在函数或块级作用域内

---

**规则 3: import 导入语法**

import 有多种导入方式:

```javascript
// 方式 1: 导入具名导出
import { API_URL, fetchData } from './api.js';

// 方式 2: 导入并重命名
import { API_URL as apiUrl, fetchData as fetch } from './api.js';

// 方式 3: 导入所有具名导出
import * as API from './api.js';
console.log(API.API_URL);
console.log(API.fetchData);

// 方式 4: 导入默认导出
import defaultFunc from './api.js';

// 方式 5: 混合导入 (默认 + 具名)
import defaultFunc, { API_URL, fetchData } from './api.js';

// 方式 6: 仅执行模块 (不导入任何内容)
import './init.js';
```

导入规则:
- 导入路径必须是字符串字面量, 不能是变量或表达式
- 相对路径必须以 `./` 或 `../` 开头
- 可以省略 `.js` 后缀 (某些环境)
- import 声明会被提升到模块顶部
- import 导入的是只读绑定, 不能重新赋值

---

**规则 4: 模块的单例特性**

模块只执行一次, 然后被缓存:

```javascript
// counter.js
console.log('counter 模块执行');

export let count = 0;

export function increment() {
    count++;
}

// moduleA.js
import { count, increment } from './counter.js';
console.log('moduleA:', count);  // 0
increment();
console.log('moduleA:', count);  // 1

// moduleB.js
import { count, increment } from './counter.js';
console.log('moduleB:', count);  // 1 - 看到 moduleA 的修改
increment();
console.log('moduleB:', count);  // 2

// main.js
import './moduleA.js';
import './moduleB.js';

// 输出:
// counter 模块执行  ← 只执行一次
// moduleA: 0
// moduleA: 1
// moduleB: 1
// moduleB: 2
```

单例特性:
- 模块代码只在首次 import 时执行一次
- 后续 import 返回缓存的导出对象
- 所有导入共享同一个模块实例
- 导出对象的修改对所有导入可见
- 适合实现单例模式和全局状态管理

---

**规则 5: import 的提升特性**

import 声明会被提升到模块顶部:

```javascript
// 代码编写顺序
console.log(API_URL);  // ✓ 可以访问

import { API_URL } from './config.js';

// 实际执行顺序 (import 被提升)
import { API_URL } from './config.js';

console.log(API_URL);
```

提升规则:
- import 声明总是最先执行
- 可以在 import 语句前使用导入的变量
- 但导入的是模块导出的最终值, 不是 undefined

注意: export 不会被提升:
```javascript
// ❌ 错误: 不能在 export 前使用
console.log(value);  // ReferenceError

export const value = 42;
```

---

**规则 6: 循环依赖的处理**

循环依赖可能导致访问未初始化的变量:

```javascript
// a.js
import { b } from './b.js';
console.log('a 中访问 b:', b);
export const a = 'a';

// b.js
import { a } from './a.js';
console.log('b 中访问 a:', a);  // undefined - a 还未定义
export const b = 'b';

// main.js
import './a.js';

// 输出:
// b 中访问 a: undefined
// a 中访问 b: b
```

执行流程:
1. main.js 导入 a.js
2. a.js 开始执行, 导入 b.js
3. b.js 开始执行, 导入 a.js (已经在执行中)
4. b.js 尝试访问 a, 但 a 还未定义 (a.js 还没执行完)
5. b.js 执行完成, 导出 b
6. a.js 继续执行, 访问 b (已定义)

解决方案:

**方案 1: 重构代码避免循环依赖**
```javascript
// 提取公共依赖到第三个模块
// common.js
export const shared = { /* ... */ };

// a.js
import { shared } from './common.js';

// b.js
import { shared } from './common.js';
```

**方案 2: 使用依赖注入**
```javascript
// a.js
let bGetter = null;

export function setBGetter(getter) {
    bGetter = getter;
}

export function useB() {
    if (bGetter) {
        const b = bGetter();
        // 使用 b
    }
}

// b.js
import { setBGetter } from './a.js';

export const b = 'b';

setBGetter(() => b);
```

**方案 3: 延迟访问 (函数内访问)**
```javascript
// a.js
import { getB } from './b.js';

export function useB() {
    const b = getB();  // 在函数内访问, 而非模块顶层
    console.log(b);
}

// b.js
import { useB } from './a.js';

export function getB() {
    return 'b';
}
```

---

**规则 7: 模块的加载方式**

在 HTML 中使用模块:

```html
<!DOCTYPE html>
<html>
<head>
    <title>模块示例</title>
</head>
<body>
    <!-- ✓ 正确: 使用 type="module" -->
    <script type="module" src="main.js"></script>

    <!-- ✓ 正确: 内联模块 -->
    <script type="module">
        import { init } from './app.js';
        init();
    </script>

    <!-- ❌ 错误: 缺少 type="module" -->
    <script src="main.js"></script>
    <!-- 报错: Cannot use import statement outside a module -->
</body>
</html>
```

模块脚本特性:
- 自动使用严格模式 (`'use strict'`)
- 默认延迟执行 (相当于 `defer`)
- 同源限制: 必须遵守 CORS 规则
- 不能使用 `document.write()`
- 顶层 `this` 是 `undefined` (而非 `window`)

---

**规则 8: 导入的只读绑定**

导入的变量是只读绑定, 不能重新赋值:

```javascript
// config.js
export let count = 0;

export function increment() {
    count++;  // ✓ 模块内部可以修改
}

// main.js
import { count, increment } from './config.js';

console.log(count);  // 0

increment();
console.log(count);  // 1 - 可以看到模块内部的修改

// ❌ 错误: 不能在导入方重新赋值
count = 10;  // TypeError: Assignment to constant variable

// ❌ 错误: 不能重新声明
let count = 10;  // SyntaxError: Identifier 'count' has already been declared
```

只读绑定规则:
- import 导入的是活动绑定 (live binding), 不是值的拷贝
- 导入方不能修改导入的变量
- 但可以看到模块内部的修改
- 导入的对象属性可以修改 (对象本身不能重新赋值)

---

**事故档案编号**: MODULE-2024-1903
**影响范围**: 模块系统, 作用域隔离, export/import, 循环依赖
**根本原因**: 多个脚本共享全局作用域导致变量名冲突, 应使用 ES6 模块隔离
**修复成本**: 中 (需要重构为模块化架构)

这是 JavaScript 世界第 103 次被记录的模块系统事故。ES6 模块为每个文件创建独立的顶层作用域, var 声明不会挂载到 window, 避免全局污染。export 有具名导出和默认导出两种方式, import 可以导入具名导出、默认导出或全部导出。模块只执行一次然后被缓存, 所有导入共享同一个实例。import 声明会被提升到模块顶部, 可以在声明前使用导入的变量。循环依赖可能导致访问未初始化的变量, 应该通过重构、依赖注入或延迟访问解决。导入的变量是只读绑定, 不能重新赋值但可以看到模块内部的修改。理解模块系统的作用域隔离是构建大型应用的基础。

---

《第 34 次记录: 变量声明事故 —— 名字先于存在的因果颠倒》

## 白屏灾难现场

周四晚上 9 点 47 分, 你盯着显示器上那三个醒目的数字 —— `3 3 3`。

这是一个在线编程测试平台。用户上传代码后, 平台会在多个测试用例中运行并显示结果。产品经理上周就在强调: "这个功能是核心竞争力, 必须做好。" 你信心满满地接下了任务。功能看起来很简单: 用户提交 JavaScript 代码, 平台创建三个独立的测试环境, 每个环境延迟 100 毫秒执行, 然后收集结果。

但现在, 距离明天的产品演示只剩 12 个小时, 控制台却固执地显示着三个 3。

你的代码看起来完美无缺:

```javascript
for (var i = 0; i < 3; i++) {
    setTimeout(function() {
        console.log('测试环境 ' + i + ' 的结果:');
        runTest(i);
    }, 100);
}
```

应该显示"测试环境 0"、"测试环境 1"、"测试环境 2", 但实际输出全是"测试环境 3"。

"这不可能..." 你喃喃自语。你打开 Chrome DevTools, 在循环体内部加了调试代码:

```javascript
for (var i = 0; i < 3; i++) {
    console.log('循环执行: i = ' + i);  // 立即输出
    setTimeout(function() {
        console.log('延迟输出: i = ' + i);  // 100ms 后输出
    }, 100);
}
```

刷新页面, 控制台显示:

```
循环执行: i = 0
循环执行: i = 1
循环执行: i = 2
延迟输出: i = 3
延迟输出: i = 3
延迟输出: i = 3
```

循环确实执行了三次, 但 100 毫秒后, 三个延迟函数输出的全是 3。

## 调试的迷雾

你开始尝试各种可能的"修复"。

你试图把 `i` 的值打印出来:

```javascript
for (var i = 0; i < 3; i++) {
    console.log('当前 i 值:', i);
    console.log('当前 i 类型:', typeof i);
    setTimeout(function() {
        console.log('回调中的 i:', i);
    }, 100);
}
```

输出:

```
当前 i 值: 0
当前 i 类型: number
当前 i 值: 1
当前 i 类型: number
当前 i 值: 2
当前 i 类型: number
回调中的 i: 3
回调中的 i: 3
回调中的 i: 3
```

循环执行时 `i` 确实是 0、1、2, 但回调执行时全变成了 3。

你修改延迟时间, 从 100 毫秒改到 1000 毫秒。刷新页面, 等待... 一秒后, 三个 3 依次出现。你又试着在 `setTimeout` 外面立即调用函数:

```javascript
for (var i = 0; i < 3; i++) {
    console.log('立即调用: i =', i);  // 立即调用

    setTimeout(function() {
        console.log('延迟调用: i =', i);  // 延迟调用
    }, 100);
}
```

输出:

```
立即调用: i = 0
立即调用: i = 1
立即调用: i = 2
延迟调用: i = 3
延迟调用: i = 3
延迟调用: i = 3
```

立即调用看到正确的值, 延迟调用看到的全是 3。

你甚至怀疑是浏览器的问题, 换了 Chrome、Firefox、Safari, 结果一模一样。你打开 Node.js 环境测试, 还是三个 3。

晚上 11 点, 你快要绝望了。突然, 隔壁工位的同事下班路过, 他看了一眼你的屏幕: "又在加班啊?" 接着他注意到你的代码, 皱了皱眉: "这个 `var`... 算了, 你慢慢调吧。"

等等... `var`?

你猛地睁开眼睛, 手指停在键盘上。为什么他要特别提到 `var`?

## 实验与发现

你打开 MDN 文档, 搜索"var let 区别"。看到一个词让你停住了: "块级作用域" vs "函数作用域"。

你开始做实验。先测试 `var` 在块中的行为:

```javascript
if (true) {
    var x = 10;
    console.log('块内 x:', x);
}
console.log('块外 x:', x);
```

输出:

```
块内 x: 10
块外 x: 10
```

变量 `x` 竟然泄露到了 `if` 块外面！

你换成 `let` 试试:

```javascript
if (true) {
    let y = 20;
    console.log('块内 y:', y);
}
console.log('块外 y:', y);  // 会报错吗?
```

刷新页面 —— 控制台报错了:

```
块内 y: 20
Uncaught ReferenceError: y is not defined
```

`let` 声明的变量确实被限制在了块内！

你继续实验, 测试循环中的行为:

```javascript
// 测试 1: var 在循环中
console.log('=== 测试 var ===');
for (var i = 0; i < 3; i++) {
    console.log('循环中 i:', i);
}
console.log('循环后 i:', i);

// 测试 2: let 在循环中
console.log('=== 测试 let ===');
for (let j = 0; j < 3; j++) {
    console.log('循环中 j:', j);
}
console.log('循环后 j:', j);  // 会报错吗?
```

输出:

```
=== 测试 var ===
循环中 i: 0
循环中 i: 1
循环中 i: 2
循环后 i: 3

=== 测试 let ===
循环中 j: 0
循环中 j: 1
循环中 j: 2
Uncaught ReferenceError: j is not defined
```

`var` 声明的 `i` 在循环后还能访问, 而 `let` 声明的 `j` 不能！

突然, 你灵光一闪。你回到最初的问题, 把 `var` 改成 `let`:

```javascript
for (let i = 0; i < 3; i++) {
    setTimeout(function() {
        console.log('测试环境 ' + i + ' 的结果:');
    }, 100);
}
```

刷新页面。100 毫秒后 ——

```
测试环境 0 的结果:
测试环境 1 的结果:
测试环境 2 的结果:
```

问题解决了！就这么简单？把 `var` 改成 `let`, 问题就解决了？

## 作用域的真相

你坐直身体, 开始系统地研究 `var`、`let`、`const` 的区别。

你打开一个新测试文件, 写下这段代码:

```javascript
// 实验 1: 作用域泄露
function testVarScope() {
    console.log('=== var 作用域测试 ===');

    if (true) {
        var a = 1;
        console.log('if 块内 a:', a);
    }

    console.log('if 块外 a:', a);  // var 会泄露

    for (var i = 0; i < 3; i++) {
        var b = i;
    }

    console.log('循环后 i:', i);  // var 会泄露
    console.log('循环后 b:', b);  // var 会泄露
}

function testLetScope() {
    console.log('=== let 作用域测试 ===');

    if (true) {
        let a = 1;
        console.log('if 块内 a:', a);
    }

    try {
        console.log('if 块外 a:', a);  // let 不会泄露
    } catch (e) {
        console.log('访问块外 a 失败:', e.message);
    }

    for (let i = 0; i < 3; i++) {
        let b = i;
    }

    try {
        console.log('循环后 i:', i);  // let 不会泄露
    } catch (e) {
        console.log('访问循环后 i 失败:', e.message);
    }
}

testVarScope();
testLetScope();
```

输出让你看清了本质:

```
=== var 作用域测试 ===
if 块内 a: 1
if 块外 a: 1
循环后 i: 3
循环后 b: 2

=== let 作用域测试 ===
if 块内 a: 1
访问块外 a 失败: a is not defined
访问循环后 i 失败: i is not defined
```

`var` 的作用域是整个函数, 不是块！所有在块内声明的 `var` 变量都会"泄露"到函数级别。

你继续测试循环中的闭包行为:

```javascript
// 实验 2: 循环中的闭包
console.log('=== var 循环闭包 ===');
var funcs1 = [];
for (var i = 0; i < 3; i++) {
    funcs1.push(function() {
        console.log('var: i =', i);
    });
}
funcs1.forEach(f => f());

console.log('=== let 循环闭包 ===');
var funcs2 = [];
for (let j = 0; j < 3; j++) {
    funcs2.push(function() {
        console.log('let: j =', j);
    });
}
funcs2.forEach(f => f());
```

输出:

```
=== var 循环闭包 ===
var: i = 3
var: i = 3
var: i = 3

=== let 循环闭包 ===
let: j = 0
let: j = 1
let: j = 2
```

终于明白了！`var` 在整个函数中只有一个 `i`, 所有的闭包都引用同一个 `i`。当循环结束时, `i` 变成了 3, 所以所有闭包输出的都是 3。

而 `let` 在每次循环迭代时都会创建一个新的 `j`, 每个闭包捕获的是自己那次迭代的 `j`！

## 暂时性死区的陷阱

你继续探索, 发现了另一个诡异的现象。

```javascript
// 实验 3: 变量提升
console.log('=== var 变量提升 ===');
console.log('访问 a:', a);  // undefined, 不报错
var a = 10;
console.log('赋值后 a:', a);  // 10

console.log('=== let 暂时性死区 ===');
try {
    console.log('访问 b:', b);  // 会报错
    let b = 20;
} catch (e) {
    console.log('访问 b 失败:', e.message);
}
```

输出:

```
=== var 变量提升 ===
访问 a: undefined
赋值后 a: 10

=== let 暂时性死区 ===
访问 b 失败: Cannot access 'b' before initialization
```

`var` 声明的变量会提升到函数顶部, 初始值为 `undefined`。但 `let` 声明的变量在声明之前访问会报错, 这个区域叫"暂时性死区"（Temporal Dead Zone, TDZ）。

你测试了更复杂的场景:

```javascript
// 实验 4: 函数内的变量提升
function testHoisting() {
    console.log('函数开始');
    console.log('访问 x:', x);  // var: undefined

    if (true) {
        console.log('块内访问 x:', x);  // var: undefined
        var x = 10;
        console.log('赋值后 x:', x);  // 10
    }

    console.log('块外访问 x:', x);  // 10
}

testHoisting();
```

输出:

```
函数开始
访问 x: undefined
块内访问 x: undefined
赋值后 x: 10
块外访问 x: 10
```

整个函数内部都能访问 `x`, 即使在声明之前！这是因为 `var x` 被提升到了函数顶部。

## const 的不可变性

你继续研究 `const` 的特性。

```javascript
// 实验 5: const 基本类型
console.log('=== const 基本类型 ===');
const num = 42;
console.log('num:', num);

try {
    num = 43;  // 尝试修改
} catch (e) {
    console.log('修改 num 失败:', e.message);
}

// 实验 6: const 对象
console.log('=== const 对象 ===');
const obj = { count: 0 };
console.log('初始 obj:', obj);

obj.count = 1;  // 修改属性
console.log('修改属性后 obj:', obj);

try {
    obj = { count: 2 };  // 尝试修改引用
} catch (e) {
    console.log('修改引用失败:', e.message);
}

// 实验 7: const 数组
console.log('=== const 数组 ===');
const arr = [1, 2, 3];
console.log('初始 arr:', arr);

arr.push(4);  // 修改内容
console.log('push 后 arr:', arr);

try {
    arr = [1, 2];  // 尝试修改引用
} catch (e) {
    console.log('修改引用失败:', e.message);
}
```

输出:

```
=== const 基本类型 ===
num: 42
修改 num 失败: Assignment to constant variable.

=== const 对象 ===
初始 obj: {count: 0}
修改属性后 obj: {count: 1}
修改引用失败: Assignment to constant variable.

=== const 数组 ===
初始 arr: [1, 2, 3]
push 后 arr: [1, 2, 3, 4]
修改引用失败: Assignment to constant variable.
```

`const` 保证的是引用不可变, 不是内容不可变！对于对象和数组, 可以修改其内容, 但不能修改引用本身。

## 重复声明的陷阱

你发现了 `var` 的另一个问题:

```javascript
// 实验 8: 重复声明
console.log('=== var 重复声明 ===');
var x = 1;
console.log('第一次声明 x:', x);

var x = 2;  // 允许重复声明
console.log('第二次声明 x:', x);

var x = 3;  // 再次重复声明
console.log('第三次声明 x:', x);

console.log('=== let 重复声明 ===');
let y = 1;
console.log('第一次声明 y:', y);

try {
    let y = 2;  // 不允许重复声明
} catch (e) {
    console.log('重复声明 y 失败:', e.message);
}
```

输出:

```
=== var 重复声明 ===
第一次声明 x: 1
第二次声明 x: 2
第三次声明 x: 3

=== let 重复声明 ===
第一次声明 y: 1
重复声明 y 失败: Identifier 'y' has already been declared
```

`var` 允许重复声明, 后面的声明会覆盖前面的。这在大型项目中很容易导致变量被意外覆盖。`let` 和 `const` 不允许重复声明, 能在开发阶段发现这类错误。

## 全局对象属性

你测试了最后一个重要区别:

```javascript
// 实验 9: 全局对象属性
console.log('=== var 全局声明 ===');
var globalVar = 'I am global var';
console.log('window.globalVar:', window.globalVar);  // 浏览器环境

console.log('=== let 全局声明 ===');
let globalLet = 'I am global let';
console.log('window.globalLet:', window.globalLet);  // undefined
```

输出（浏览器环境）:

```
=== var 全局声明 ===
window.globalVar: I am global var

=== let 全局声明 ===
window.globalLet: undefined
```

在全局作用域中, `var` 声明的变量会成为全局对象（浏览器中的 `window`）的属性, 而 `let` 和 `const` 不会。这避免了污染全局对象。

## 修复生产代码

凌晨 1 点, 你终于理解了所有细节。你回到最初的问题, 写下正确的代码:

```javascript
// 原始代码（有问题）:
/*
for (var i = 0; i < 3; i++) {
    setTimeout(function() {
        console.log('测试环境 ' + i + ' 的结果:');
        runTest(i);
    }, 100);
}
*/

// 修复方案 1: 使用 let（推荐）
for (let i = 0; i < 3; i++) {
    setTimeout(function() {
        console.log('测试环境 ' + i + ' 的结果:');
        runTest(i);
    }, 100);
}

// 修复方案 2: 使用 IIFE 创建闭包（兼容旧环境）
for (var i = 0; i < 3; i++) {
    (function(index) {
        setTimeout(function() {
            console.log('测试环境 ' + index + ' 的结果:');
            runTest(index);
        }, 100);
    })(i);
}

// 修复方案 3: 使用 bind 绑定参数
for (var i = 0; i < 3; i++) {
    setTimeout(function(index) {
        console.log('测试环境 ' + index + ' 的结果:');
        runTest(index);
    }.bind(null, i), 100);
}
```

你运行所有测试用例, 全部通过。你保存代码, 提交到代码仓库, 然后靠在椅背上, 长长地舒了一口气。

窗外的天空已经泛起鱼肚白。你关掉电脑, 收拾东西准备回家。明天 —— 不, 是今天的产品演示, 应该不会有问题了。

---

## 技术档案: JavaScript 变量声明的三种方式

**规则 1: var 的函数作用域特性**

`var` 声明的变量是函数作用域（function scope），不是块级作用域（block scope）。这意味着 `var` 声明的变量在整个函数内部都可见，即使在声明之前（变量提升）。

```javascript
// var 的作用域是整个函数
function test() {
    console.log(x);  // undefined（变量提升）

    if (true) {
        var x = 10;  // 声明在 if 块内
        console.log(x);  // 10
    }

    console.log(x);  // 10（泄露到 if 块外）
}

// var 在循环中的行为
for (var i = 0; i < 3; i++) {
    // 循环体
}
console.log(i);  // 3（泄露到循环外）

// var 允许重复声明
var name = 'Alice';
var name = 'Bob';  // 不会报错，后面的覆盖前面的
console.log(name);  // 'Bob'

// var 在全局作用域会成为全局对象属性
var globalVar = 'global';
console.log(window.globalVar);  // 'global'（浏览器环境）
```

**变量提升（Hoisting）机制**：

```javascript
// 实际代码
function example() {
    console.log(a);  // undefined
    var a = 10;
    console.log(a);  // 10
}

// 等价于（变量提升后）
function example() {
    var a;  // 声明被提升到函数顶部
    console.log(a);  // undefined
    a = 10;  // 赋值留在原地
    console.log(a);  // 10
}
```

**规则 2: let 的块级作用域特性**

`let` 声明的变量是块级作用域（block scope），只在最近的 `{}` 块内可见。`let` 有暂时性死区（Temporal Dead Zone, TDZ），在声明之前访问会报错。

```javascript
// let 的作用域是最近的 {} 块
{
    let x = 10;
    console.log(x);  // 10
}
console.log(x);  // ReferenceError: x is not defined

// let 在 if 块中
if (true) {
    let y = 20;
    console.log(y);  // 20
}
console.log(y);  // ReferenceError: y is not defined

// let 在循环中
for (let i = 0; i < 3; i++) {
    console.log(i);  // 0, 1, 2
}
console.log(i);  // ReferenceError: i is not defined

// let 不允许重复声明
let name = 'Alice';
let name = 'Bob';  // SyntaxError: Identifier 'name' has already been declared

// let 在全局作用域不会成为全局对象属性
let globalLet = 'global';
console.log(window.globalLet);  // undefined（浏览器环境）
```

**暂时性死区（TDZ）**：

```javascript
// TDZ 导致错误
console.log(a);  // ReferenceError: Cannot access 'a' before initialization
let a = 10;

// TDZ 的边界
{
    // TDZ 开始
    console.log(b);  // ReferenceError
    // TDZ 仍在继续
    let b = 20;  // TDZ 结束
    console.log(b);  // 20
}

// TDZ 与 typeof
console.log(typeof undeclaredVar);  // 'undefined'（变量未声明）
console.log(typeof declaredVar);    // ReferenceError（TDZ）
let declaredVar;
```

**规则 3: 循环中的 let vs var**

这是最容易出错的场景。`let` 在每次循环迭代时都会创建一个新的变量副本，而 `var` 在整个循环中只有一个变量。

```javascript
// var 循环：所有闭包共享同一个 i
console.log('=== var 循环 ===');
for (var i = 0; i < 3; i++) {
    setTimeout(() => {
        console.log('var i:', i);  // 全部输出 3
    }, 100);
}
// 输出: var i: 3, var i: 3, var i: 3

// let 循环：每次迭代创建新的 i
console.log('=== let 循环 ===');
for (let j = 0; j < 3; j++) {
    setTimeout(() => {
        console.log('let j:', j);  // 分别输出 0, 1, 2
    }, 100);
}
// 输出: let j: 0, let j: 1, let j: 2

// 原理演示
// var 版本等价于:
var i;
for (i = 0; i < 3; i++) {  // 只有一个 i
    setTimeout(() => console.log(i), 100);  // 所有回调引用同一个 i
}
// 循环结束时 i = 3，所以所有回调输出 3

// let 版本等价于:
for (let j = 0; j < 3; j++) {  // 每次迭代创建新的 j
    let _j = j;  // 概念上类似这样
    setTimeout(() => console.log(_j), 100);  // 每个回调有自己的 _j
}
```

**规则 4: const 的不可变性**

`const` 声明的是常量，特性与 `let` 相同（块级作用域、TDZ、不允许重复声明），但增加了引用不可变的限制。注意：引用不可变不等于内容不可变。

```javascript
// const 基本类型：值不可变
const num = 42;
num = 43;  // TypeError: Assignment to constant variable

// const 对象：引用不可变，内容可变
const obj = { count: 0 };
obj.count = 1;        // ✓ 允许修改属性
obj.newProp = 'new';  // ✓ 允许添加属性
delete obj.count;     // ✓ 允许删除属性
obj = { count: 2 };   // ✗ TypeError: 不允许修改引用

// const 数组：引用不可变，内容可变
const arr = [1, 2, 3];
arr.push(4);       // ✓ 允许修改数组
arr[0] = 10;       // ✓ 允许修改元素
arr = [1, 2];      // ✗ TypeError: 不允许修改引用

// const 必须在声明时初始化
const x;           // SyntaxError: Missing initializer in const declaration
const y = 10;      // ✓ 正确
```

**如何真正冻结对象**：

```javascript
// Object.freeze() 冻结对象
const obj = Object.freeze({ count: 0 });
obj.count = 1;  // 严格模式下报错，非严格模式下静默失败
console.log(obj.count);  // 0

// Object.freeze() 是浅冻结
const nested = Object.freeze({
    level1: {
        level2: 'mutable'
    }
});
nested.level1 = {};  // 失败（level1 引用被冻结）
nested.level1.level2 = 'changed';  // ✓ 成功（level2 未被冻结）

// 深度冻结
function deepFreeze(obj) {
    Object.freeze(obj);
    Object.values(obj).forEach(value => {
        if (typeof value === 'object' && value !== null) {
            deepFreeze(value);
        }
    });
    return obj;
}

const deepFrozen = deepFreeze({
    level1: {
        level2: 'immutable'
    }
});
deepFrozen.level1.level2 = 'changed';  // 失败
```

**规则 5: 最佳实践与选择指南**

现代 JavaScript 开发中，应该优先使用 `const`，需要重新赋值时使用 `let`，避免使用 `var`（除非需要兼容非常旧的环境）。

```javascript
// 推荐：优先使用 const
const API_URL = 'https://api.example.com';  // 常量
const config = { port: 3000, host: 'localhost' };  // 配置对象
const users = [];  // 即使内容会变化，引用不变也用 const

// 需要重新赋值时使用 let
let count = 0;
count++;  // 需要修改值

let currentUser = null;
currentUser = fetchUser();  // 需要重新赋值

// 避免使用 var
// var name = 'Alice';  // ✗ 不推荐

// 实际项目示例
function processData(items) {
    const results = [];  // 数组引用不变，用 const

    for (let i = 0; i < items.length; i++) {  // 循环计数器用 let
        const item = items[i];  // 循环内临时变量用 const

        if (item.valid) {
            results.push(item.data);
        }
    }

    return results;
}

// 配置管理示例
const DEFAULT_CONFIG = Object.freeze({  // 真正不可变的配置
    timeout: 5000,
    retries: 3
});

function createRequest(userConfig) {
    const config = { ...DEFAULT_CONFIG, ...userConfig };  // 合并配置
    return fetch(config.url, { timeout: config.timeout });
}
```

**var 的问题总结**：

1. **函数作用域导致意外泄露**：块内声明的变量会泄露到块外
2. **缺少暂时性死区**：声明前可以访问（值为 `undefined`），可能导致逻辑错误
3. **循环中的闭包陷阱**：所有闭包共享同一个变量，导致经典的"打印 3 个 3"问题
4. **允许重复声明**：可能造成变量被意外覆盖
5. **污染全局对象**：全局 `var` 会成为 `window` 属性（浏览器环境）

**规则 6: 调试与诊断**

当遇到变量相关的问题时，可以使用以下方法诊断：

```javascript
// 诊断方法 1：使用 console.trace() 查看调用栈
function debugVariable() {
    let x = 10;
    console.trace('变量 x 的声明位置');
}

// 诊断方法 2：使用 debugger 断点
for (let i = 0; i < 3; i++) {
    debugger;  // 在此处暂停，查看 i 的值
    setTimeout(() => console.log(i), 100);
}

// 诊断方法 3：检查变量是否在全局对象上
console.log('globalVar' in window);  // var 声明：true
console.log('globalLet' in window);  // let 声明：false

// 诊断方法 4：使用 typeof 检测是否在 TDZ
try {
    console.log(typeof myVar);  // var: 'undefined'
    console.log(typeof myLet);  // let: ReferenceError（TDZ）
} catch (e) {
    console.log('变量在 TDZ 中');
}
var myVar;
let myLet;

// 诊断方法 5：Chrome DevTools Scope 面板
// 在 Sources 面板打断点，查看 Scope 部分：
// - Block：块级作用域变量（let/const）
// - Local：函数作用域变量（var）
// - Global：全局变量
```

**常见错误诊断**：

```javascript
// 问题 1：循环中的闭包输出相同值
// 原因：var 导致所有闭包共享同一个变量
// 解决：使用 let 或 IIFE

// 问题 2：变量未定义错误
// 原因：访问 let/const 声明前的暂时性死区
// 解决：确保在声明后访问

// 问题 3：常量被意外修改
// 原因：const 只保证引用不变，不保证内容不变
// 解决：使用 Object.freeze() 或 deepFreeze()

// 问题 4：全局变量冲突
// 原因：var 在全局作用域会污染 window 对象
// 解决：使用 let/const，或使用模块化

// 问题 5：重复声明导致覆盖
// 原因：var 允许重复声明
// 解决：使用 let/const，它们会在重复声明时报错
```

**规则 7: 性能考虑**

变量声明方式对性能的影响微乎其微，但在极端情况下（如深度嵌套的循环）可能有细微差异。

```javascript
// 性能测试：循环中的变量创建
console.time('var loop');
for (var i = 0; i < 1000000; i++) {
    var x = i;
}
console.timeEnd('var loop');

console.time('let loop');
for (let i = 0; i < 1000000; i++) {
    let x = i;
}
console.timeEnd('let loop');

// 实际结果：性能差异不足 5%，可以忽略不计
// 代码可读性和正确性远比这点性能差异重要

// 真正影响性能的是：
// 1. 闭包创建（无论 var 还是 let）
// 2. 大量的作用域链查找
// 3. 全局变量访问（比局部变量慢）
```

**规则 8: 兼容性与迁移**

从 `var` 迁移到 `let`/`const` 需要注意的问题：

```javascript
// 迁移检查清单：

// 1. 检查变量提升依赖
// 旧代码可能依赖 var 的变量提升
console.log(x);  // 使用 var 时：undefined
var x = 10;

// 迁移到 let 会导致错误
console.log(y);  // 使用 let 时：ReferenceError
let y = 10;

// 2. 检查作用域泄露依赖
// 旧代码可能依赖 var 的作用域泄露
for (var i = 0; i < 10; i++) {}
console.log(i);  // 10（可能有代码依赖这个行为）

// 3. 检查全局对象属性访问
// 旧代码可能通过 window.varName 访问全局变量
var globalVar = 'value';
console.log(window.globalVar);  // 'value'

let globalLet = 'value';
console.log(window.globalLet);  // undefined

// 4. 使用 ESLint 规则自动检测
// eslint配置:
// {
//   "rules": {
//     "no-var": "error",
//     "prefer-const": "error"
//   }
// }

// 5. 渐进式迁移策略
// 优先迁移新代码
// 逐步重构旧代码
// 使用工具（如 jscodeshift）批量迁移
```

---

**记录者注**:

JavaScript 的变量声明经历了从 `var` 到 `let`/`const` 的演进。`var` 的函数作用域和变量提升特性在早期 JavaScript 中很常见，但也带来了作用域泄露、循环闭包陷阱、重复声明等问题。ES6 引入的 `let` 和 `const` 提供了块级作用域、暂时性死区、禁止重复声明等特性，使代码更加安全和可预测。

关键在于理解三种声明方式的本质区别：`var` 是函数作用域且有变量提升，`let` 是块级作用域且有暂时性死区，`const` 在 `let` 的基础上增加了引用不可变的限制。循环中的闭包陷阱是 `var` 最经典的问题 —— 所有闭包共享同一个变量，而 `let` 在每次迭代创建新变量，完美解决了这个问题。

记住：**优先使用 const，需要重新赋值时使用 let，避免使用 var；var 是函数作用域会泄露，let/const 是块级作用域；var 有变量提升返回 undefined，let/const 有暂时性死区会报错；循环中 var 所有闭包共享变量，let 每次迭代创建新变量；const 保证引用不变，不保证内容不变**。理解变量声明的作用域和生命周期，就理解了 JavaScript 如何在不同层级绑定名字和值。

---

**事故档案编号**: JS-2024-1634
**影响范围**: 变量作用域、闭包行为、代码维护性、全局对象污染
**根本原因**: var 的函数作用域导致循环中所有闭包共享同一个变量，缺乏块级作用域导致变量意外泄露
**修复成本**: 低（将 var 改为 let/const，注意检查依赖变量提升的代码）
**预防措施**: 使用 ESLint 强制 no-var 和 prefer-const 规则，代码审查关注作用域问题，优先使用 let/const

这是 JavaScript 世界第 34 次被记录的变量声明事故。var 是函数作用域会泄露到块外，循环中的闭包会共享同一个 var 变量导致经典的"打印三个 3"问题。let 是块级作用域每次迭代创建新变量，有暂时性死区在声明前访问会报错。const 是块级作用域的常量声明，引用不可变但内容可变。理解三种声明方式的作用域、提升、重复声明等特性差异，就理解了 JavaScript 如何在不同作用域层级中绑定变量名字和值的关系。

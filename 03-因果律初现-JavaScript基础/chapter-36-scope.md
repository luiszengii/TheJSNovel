《第36次记录:作用域事故 —— 变量可见性的边界》

---

## 事故现场

周四下午,你在调试一个计数器功能时遇到了诡异的bug。

代码很简单:三个按钮,每个按钮显示一个计数器。你用循环创建了事件监听:

```javascript
for (var i = 0; i < 3; i++) {
    document.getElementById('btn' + i).onclick = function() {
        console.log("按钮", i, "被点击")
    }
}
```

你点击第一个按钮,期望输出"按钮 0 被点击",但控制台显示:"按钮 3 被点击"。你点击第二个、第三个按钮,全都输出"按钮 3"。

"为什么都是3?"你盯着代码。循环明明是0到2,但点击时`i`却是3。

你测试了另一个功能:内层函数访问外层变量:

```javascript
function outer() {
    let count = 0

    function increment() {
        count++
        console.log(count)
    }

    return increment
}

const counter = outer()
counter()  // 1
counter()  // 2
```

内层函数能访问并修改外层的`count`。但你试着在外层访问内层变量:

```javascript
function test() {
    if (true) {
        let inner = "内层"
    }
    console.log(inner)  // ReferenceError
}
```

报错了。外层不能访问内层。

你的同事路过:"作用域的问题吧?变量的可见性范围。"

"可见性范围?"你喃喃道。

---

## 深入迷雾

你创建测试文件,开始探索作用域的边界。首先测试全局和局部:

```javascript
const global = "全局变量"

function test() {
    const local = "局部变量"
    console.log(global)  // 能访问
    console.log(local)   // 能访问
}

test()
console.log(global)  // 能访问
console.log(local)   // ReferenceError - 不能访问
```

函数内可以访问外部变量,但外部不能访问函数内的变量。"单向可见。"你写下笔记。

你测试嵌套作用域:

```javascript
const a = "全局a"

function outer() {
    const b = "outer的b"

    function inner() {
        const c = "inner的c"
        console.log(a)  // 全局a
        console.log(b)  // outer的b
        console.log(c)  // inner的c
    }

    inner()
    console.log(c)  // ReferenceError
}

outer()
```

内层函数能访问外层变量,形成一条向外的查找链。"作用域链。"你明白了。

你测试变量遮蔽:

```javascript
let x = "全局"

function test() {
    let x = "函数"  // 遮蔽全局x

    if (true) {
        let x = "块级"  // 遮蔽函数x
        console.log(x)  // "块级"
    }

    console.log(x)  // "函数"
}

test()
console.log(x)  // "全局"
```

同名变量在不同层级独立存在,内层遮蔽外层。你想起那个循环的bug:

```javascript
// 问题代码
for (var i = 0; i < 3; i++) {
    setTimeout(function() {
        console.log(i)  // 循环结束时i=3
    }, 100)
}
// 输出: 3 3 3

// 用let修复
for (let i = 0; i < 3; i++) {
    setTimeout(function() {
        console.log(i)  // 每次迭代的i独立
    }, 100)
}
// 输出: 0 1 2
```

`var`是函数作用域,整个循环共享一个`i`。`let`是块级作用域,每次迭代创建新的`i`。"原来如此!"你恍然大悟。

---

## 真相浮现

你整理了作用域的核心规则。

**作用域类型**

```javascript
// 1. 全局作用域
const global = "全局"

// 2. 函数作用域
function test() {
    var fn = "函数"
}

// 3. 块级作用域(let/const)
{
    let block = "块级"
}
```

**作用域链查找**

```javascript
const a = "全局"

function outer() {
    const b = "outer"

    function inner() {
        const c = "inner"
        console.log(a)  // 向外查找到全局
        console.log(b)  // 向外查找到outer
        console.log(c)  // 当前作用域
    }

    inner()
}
```

**变量遮蔽**

```javascript
let x = "全局"

function test() {
    let x = "函数"  // 遮蔽全局x
    console.log(x)  // "函数"
}

test()
console.log(x)  // "全局" - 各层独立
```

**闭包与作用域**

```javascript
function createCounter() {
    let count = 0  // 外层变量

    return function() {
        count++  // 内层访问外层
        return count
    }
}

const counter = createCounter()
counter()  // 1
counter()  // 2
// count在外层函数执行完后仍存在
```

你把那个按钮监听改成了这样:

```javascript
for (let i = 0; i < 3; i++) {
    document.getElementById('btn' + i).onclick = function() {
        console.log("按钮", i, "被点击")
    }
}
```

测试通过。每个按钮都捕获了正确的`i`值。

---

## 世界法则

**世界规则 1:三种作用域**

```javascript
const global = "全局"  // 全局作用域

function test() {
    var fn = "函数"  // 函数作用域
}

{
    let block = "块级"  // 块级作用域
}
```

**世界规则 2:作用域链**

```javascript
const a = "全局"

function outer() {
    const b = "outer"

    function inner() {
        const c = "inner"
        // 查找顺序: inner → outer → 全局
        console.log(a, b, c)
    }
}
```

**世界规则 3:变量遮蔽**

```javascript
let x = "外层"

function test() {
    let x = "内层"  // 遮蔽外层
    console.log(x)  // "内层"
}
```

**世界规则 4:闭包保持引用**

```javascript
function create() {
    let data = "数据"

    return function() {
        return data  // 保持对外层的引用
    }
}
```

**世界规则 5:最佳实践**

```javascript
// ✅ 使用let/const(块级作用域)
for (let i = 0; i < 3; i++) {}

// ❌ 避免var(函数作用域)
for (var i = 0; i < 3; i++) {}

// ✅ 最小作用域原则
{
    const temp = calculate()
    use(temp)
}
// temp不污染外部
```

---

**事故档案编号**:JS-2024-1636
**影响范围**:变量可见性、闭包行为、内存泄漏
**根本原因**:不理解作用域链和块级作用域
**修复成本**:中等(需要重构变量声明)

这是JavaScript世界第36次被记录的作用域事故。作用域定义了变量的可见性边界——全局作用域、函数作用域、块级作用域形成嵌套结构,内层可以访问外层(作用域链),外层无法访问内层。变量遮蔽让同名变量在不同层级独立存在。闭包是内层函数对外层作用域的引用。理解作用域,就理解了JavaScript如何管理变量的可见性和生命周期。

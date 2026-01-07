《第35次记录:提升事故 —— 时间倒流的幻觉》

---

## 事故现场

周三上午十点,你正在重构一个老项目的代码,突然发现一段让你困惑的代码:

```javascript
function initialize() {
    console.log("配置:", config)
    var config = loadConfig()
    console.log("加载后:", config)
}
```

这段代码能运行,但第一个console.log输出的是`undefined`。"为什么能访问还没声明的变量?"你自言自语。

你继续往下看,发现更奇怪的现象:

```javascript
greet()  // 输出"Hello"

function greet() {
    console.log("Hello")
}
```

函数在声明之前就被调用了,而且成功执行了!但当你看到另一段代码时:

```javascript
sayHi()  // TypeError: sayHi is not a function

var sayHi = function() {
    console.log("Hi")
}
```

这次却报错了。同样是函数,为什么function声明可以提前调用,但function表达式不行?

你的手机响了,是技术主管:"那个refactoring的PR看了吗?有人说你的代码有问题。"

你打开GitHub,看到同事的评论:"为什么在变量声明之前就使用?虽然能运行,但会造成理解困难。"

你盯着那行代码:`console.log(data); var data = fetchData();`

"这...这是提升(Hoisting)?"你想起了在某篇文章里看到过的术语。

---

## 深入迷雾

你创建了一个测试文件,决心搞清楚提升到底是什么。首先测试最简单的变量提升:

```javascript
console.log(x)  // 期望:报错
var x = 10
console.log(x)  // 期望:10
```

刷新页面。第一行输出`undefined`,第二行输出`10`。没有报错!"为什么能访问还没赋值的变量?"

你想起JavaScript的执行过程分为两个阶段:编译阶段和执行阶段。编译阶段会进行变量提升。实际执行相当于:

```javascript
var x  // 声明提升到顶部,值为undefined
console.log(x)  // undefined
x = 10  // 赋值留在原处
console.log(x)  // 10
```

"原来如此!"你恍然大悟。JavaScript把声明提升了,但赋值还在原地。

你测试函数声明:

```javascript
sayHello()  // 能调用!

function sayHello() {
    console.log("Hello")
}
```

成功输出"Hello"。函数声明会整体提升,包括函数体。等价于:

```javascript
function sayHello() {  // 整个函数提升
    console.log("Hello")
}

sayHello()
```

但函数表达式不同:

```javascript
console.log(greet)  // undefined
greet()  // TypeError

var greet = function() {
    console.log("Hi")
}
```

函数表达式只提升变量声明,函数定义不提升。等价于:

```javascript
var greet  // 只提升变量声明
console.log(greet)  // undefined
greet()  // greet是undefined,不是函数,所以TypeError

greet = function() {  // 函数赋值留在原处
    console.log("Hi")
}
```

你又想到了let和const。你测试了一下:

```javascript
console.log(x)  // ReferenceError
let x = 10
```

报错了!let和const也有提升,但在声明之前访问会报错。这个区域叫"暂时性死区(TDZ)"。

你靠在椅背上,终于理解了。提升制造了"时间倒流"的幻觉——代码看起来能先使用后声明,但实际上是JavaScript在编译阶段重新排列了代码。

---

## 真相浮现

你整理了测试代码,把提升的规则总结清楚。

**var变量提升**

```javascript
// 源代码
console.log(x)  // undefined
var x = 10
console.log(x)  // 10

// 实际执行
var x  // 声明提升
console.log(x)  // undefined
x = 10  // 赋值不提升
console.log(x)  // 10
```

**函数声明提升**

```javascript
// 源代码
sayHello()  // "Hello"

function sayHello() {
    console.log("Hello")
}

// 实际执行
function sayHello() {  // 整个函数提升
    console.log("Hello")
}

sayHello()
```

**函数表达式提升**

```javascript
// 源代码
greet()  // TypeError

var greet = function() {
    console.log("Hi")
}

// 实际执行
var greet  // 只提升变量声明
greet()  // greet是undefined,TypeError

greet = function() {
    console.log("Hi")
}
```

**let/const的暂时性死区**

```javascript
console.log(x)  // ReferenceError
let x = 10

// TDZ从块开始到let语句
// 在TDZ中访问变量会报错
```

你把那段重构代码改成了这样:

```javascript
function initialize() {
    const config = loadConfig()  // 先声明后使用
    console.log("配置:", config)
}
```

清晰多了。提升是JavaScript的机制,但依赖提升会让代码难以理解。

---

## 世界法则

**世界规则 1:var变量提升**

```javascript
console.log(x)  // undefined
var x = 10

// 等价于:
var x  // 声明提升
console.log(x)
x = 10  // 赋值不提升
```

**世界规则 2:函数声明提升**

```javascript
greet()  // 可以调用

function greet() {
    console.log("Hello")
}

// 整个函数提升,可先调用后声明
```

**世界规则 3:函数表达式提升**

```javascript
fn()  // TypeError: fn is not a function

var fn = function() {}

// 只提升变量声明,函数定义不提升
```

**世界规则 4:let/const的TDZ**

```javascript
console.log(x)  // ReferenceError
let x = 10

// TDZ:从块开始到let语句
// TDZ中访问变量报错
```

**世界规则 5:最佳实践**

```javascript
// ✅ 推荐:先声明后使用
let x = 10
console.log(x)

function greet() {}
greet()

// ❌ 避免:依赖提升
console.log(x)  // 难以理解
var x = 10
```

---

**事故档案编号**:JS-2024-1635
**影响范围**:代码可读性、调试难度、意外错误
**根本原因**:提升机制导致代码执行顺序与书写顺序不一致
**修复成本**:低(先声明后使用,使用let/const)

这是JavaScript世界第35次被记录的提升事故。提升(Hoisting)是JavaScript的编译阶段行为——var变量声明提升但赋值不提升,函数声明整体提升,函数表达式只提升变量声明,let/const有提升但在TDZ中不可访问。提升制造了"时间倒流"的幻觉,代码执行顺序与书写顺序不同。理解提升,就理解了JavaScript如何在执行前重组代码结构。

《第76次记录：call与apply —— this的临时变身术》

---

## 困惑时刻

周二下午三点，Code Review会议室里，你正在review新同事小林的代码。一切看起来都很正常，直到你看到这一行：

```javascript
const numbers = [5, 2, 9, 1, 7];
const max = Math.max.apply(null, numbers);
```

你停了下来："为什么不直接`Math.max(numbers)`？用`apply`是什么意思？"

小林挠了挠头："我也不太确定，这是我从Stack Overflow上复制的。试了一下能用，就没深究。"

"能用归能用，但我们得理解它为什么这样写。"你说。旁边的老张笑了笑："这是个经典用法，涉及到`this`绑定和参数展开。我给你们讲讲。"

老张在白板上写下：

```javascript
// Math.max的正常用法
Math.max(1, 2, 3); // 3

// 但如果参数在数组里呢？
const arr = [1, 2, 3];
Math.max(arr); // NaN - 错误!

// apply的作用：把数组元素展开成参数
Math.max.apply(null, arr); // 3 - 正确!
```

"原来如此！"小林恍然大悟，"但为什么第一个参数是`null`？"

"好问题，"老张说，"这就要从`call`和`apply`的本质讲起了。"

---

## 理解用法

老张清了清嗓子："JavaScript的每个函数都有两个方法：`call`和`apply`，它们的作用是改变函数执行时的`this`指向。"

```javascript
// call: 逐个传参
func.call(thisArg, arg1, arg2, arg3);

// apply: 数组传参
func.apply(thisArg, [arg1, arg2, arg3]);
```

"看个例子：" 老张继续写：

```javascript
const person = {
    name: 'Alice',
    greet(greeting) {
        console.log(`${greeting}, 我是${this.name}`);
    }
};

person.greet('你好'); // "你好, 我是Alice"

// 现在用call改变this
const anotherPerson = { name: 'Bob' };
person.greet.call(anotherPerson, '嗨'); // "嗨, 我是Bob"

// 用apply也一样
person.greet.apply(anotherPerson, ['嗨']); // "嗨, 我是Bob"
```

"看到了吗？`call`和`apply`的第一个参数是`this`要指向的对象。"老张说，"所以`Math.max.apply(null, arr)`中的`null`表示不需要改变`this`（Math.max内部不使用this）。"

你若有所思："那为什么`Math.max`需要用`apply`？直接传数组不行吗？"

```javascript
Math.max([1, 2, 3]); // NaN - 因为它期望的是多个参数，不是一个数组
```

"对，`Math.max`接收的是多个参数，不是数组。`apply`的作用就是把数组'展开'成多个参数。"老张解释。

小林又问："那现在不是有扩展运算符了吗？可以用`Math.max(...arr)`？"

"完全正确！"老张赞许地点头，"ES6后可以用扩展运算符，更直观：

```javascript
const arr = [1, 2, 3];

// 老方法
Math.max.apply(null, arr);

// 新方法（推荐）
Math.max(...arr);
```

---

## 方法借用

老张接着讲："不过`call`和`apply`还有个重要用途——方法借用。"

```javascript
// 场景：类数组对象想用数组方法
const arrayLike = {
    0: 'a',
    1: 'b',
    2: 'c',
    length: 3
};

// 直接调用会报错
// arrayLike.slice(); // TypeError

// 借用Array的slice方法
const realArray = Array.prototype.slice.call(arrayLike);
console.log(realArray); // ['a', 'b', 'c']
```

"等等，"你打断道，"为什么`Array.prototype.slice.call`能把类数组变成真数组？"

"因为数组方法内部只需要对象有`length`属性和数字索引，"老张解释，"`slice`通过`this`访问元素，用`call`把`this`指向类数组对象，就能正常工作了。"

```javascript
// 更多方法借用的例子
function logArgs() {
    // arguments是类数组对象
    const args = Array.prototype.slice.call(arguments);
    console.log('参数:', args);
}

logArgs(1, 2, 3); // 参数: [1, 2, 3]

// ES6后的现代写法
function logArgsModern() {
    const args = Array.from(arguments); // 或 [...arguments]
    console.log('参数:', args);
}
```

小林点点头："明白了，`call`和`apply`可以让一个对象临时'借用'另一个对象的方法。"

"没错，"老张说，"这就是为什么我把它们叫做'临时夺舍'——临时改变方法执行时的`this`，让它为我所用。"

---

## 上下文控制

老张在白板上总结了`call`和`apply`的核心应用：

**应用1：找出数组最大/最小值**

```javascript
const numbers = [5, 2, 9, 1, 7];

Math.max.apply(null, numbers); // 9
Math.min.apply(null, numbers); // 1

// 现代写法
Math.max(...numbers); // 9
```

**应用2：数组拼接**

```javascript
const arr1 = [1, 2];
const arr2 = [3, 4];

// 老方法
arr1.push.apply(arr1, arr2);
console.log(arr1); // [1, 2, 3, 4]

// 新方法
arr1.push(...arr2);
```

**应用3：类型检测**

```javascript
function getType(value) {
    return Object.prototype.toString.call(value);
}

getType([]); // "[object Array]"
getType({}); // "[object Object]"
getType(null); // "[object Null]"
```

**应用4：构造函数借用（继承）**

```javascript
function Animal(name) {
    this.name = name;
}

function Dog(name, breed) {
    Animal.call(this, name); // 借用Animal的构造函数
    this.breed = breed;
}

const dog = new Dog('旺财', '柴犬');
console.log(dog); // {name: '旺财', breed: '柴犬'}
```

"不过要注意，"老张提醒，"`apply`有参数数量限制，数组太大会报错：

```javascript
// 参数过多会超出栈大小
const huge = new Array(100000);
Math.max.apply(null, huge); // RangeError

// 用扩展运算符也有同样问题
Math.max(...huge); // RangeError

// 解决方案：分批处理或用reduce
const max = huge.reduce((a, b) => Math.max(a, b));
```

Code Review结束后，你对小林说："以后遇到不理解的代码，不要只是复制粘贴。理解原理，才能写出更好的代码。"

小林点头："明白了！而且现在有扩展运算符，很多`apply`的场景都可以替代了。"

---

## call和apply知识

**规则 1: call和apply基础**

```javascript
// call: 逐个传参
func.call(thisArg, arg1, arg2, ...);

// apply: 数组传参
func.apply(thisArg, [arg1, arg2, ...]);

// 区别仅在于传参方式
```

---

**规则 2: this绑定**

```javascript
function greet() {
    console.log(`Hello, ${this.name}`);
}

const person = { name: 'Alice' };

greet.call(person); // "Hello, Alice"
greet.apply(person); // "Hello, Alice"

// 不传thisArg，非严格模式下指向全局对象
greet.call(); // this指向window/global
```

---

**规则 3: 方法借用**

```javascript
// 借用数组方法
const arrayLike = { 0: 'a', 1: 'b', length: 2 };
const arr = Array.prototype.slice.call(arrayLike);

// 借用Object方法做类型检测
Object.prototype.toString.call([]); // "[object Array]"
```

---

**规则 4: 参数限制**

```javascript
// apply有参数数量限制（约10万）
const huge = new Array(200000);
Math.max.apply(null, huge); // RangeError

// 解决方案：reduce
huge.reduce((max, n) => Math.max(max, n), -Infinity);
```

---

**规则 5: 现代替代方案**

```javascript
// 老：apply展开数组
Math.max.apply(null, [1,2,3]);

// 新：扩展运算符
Math.max(...[1,2,3]);

// 老：类数组转数组
Array.prototype.slice.call(arguments);

// 新：Array.from
Array.from(arguments); // 或 [...arguments]
```

---

**规则 6: 使用建议**

- 优先使用扩展运算符（更清晰）
- `call`/`apply`主要用于显式this绑定
- 方法借用时考虑是否有现代替代方案
- 注意参数数量限制

---

**事故档案编号**: FUNC-2024-1876
**影响范围**: this绑定,方法借用,参数展开
**根本原因**: 不理解call/apply用途,盲目复制代码
**修复成本**: 低(理解原理),现代JavaScript有更好替代方案

这是JavaScript世界第76次被记录的this控制事故。`call`和`apply`是函数原型上的方法,用于显式指定函数执行时的`this`和传参。两者区别仅在传参方式:call逐个传参,apply接收参数数组。主要用途:改变this指向、方法借用(如类数组借用数组方法)、参数展开。ES6后扩展运算符和Array.from提供了更直观的替代方案,但理解call/apply对掌握this机制至关重要。

---

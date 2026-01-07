《第 84 次记录: 原生原型 —— 内建血统》

---

## 数组方法的失踪之谜

周六下午两点，你盯着一个奇怪的 bug 已经半小时了。

你正在为公司的数据可视化库写一个数组扩展工具。需求很简单：给数组添加一些自定义方法，让数据处理更方便。你写下了这段代码：

```javascript
const data = [1, 2, 3, 2, 1, 3];

// 添加自定义方法：去重
data.unique = function() {
    return [...new Set(this)];
};

// 添加自定义方法：求和
data.sum = function() {
    return this.reduce((a, b) => a + b, 0);
};

console.log(data.unique()); // [1, 2, 3]
console.log(data.sum()); // 12
```

"完美！" 你满意地说。

但当你用 `Object.keys()` 检查数组属性准备做序列化时，发现了奇怪的输出：

```javascript
console.log(Object.keys(data));
// ['0', '1', '2', '3', '4', '5', 'unique', 'sum']
```

"等等..." 你皱眉，"为什么我定义的 `unique` 和 `sum` 出现了，但数组自带的 `map`、`filter`、`reduce` 没有出现？"

你立刻测试：

```javascript
console.log(typeof data.map); // 'function' - map 方法确实存在
console.log(typeof data.filter); // 'function' - filter 也在
console.log(typeof data.reduce); // 'function' - reduce 也在

// 但它们不在 Object.keys 的结果里？
const keys = Object.keys(data);
console.log(keys.includes('map')); // false
console.log(keys.includes('filter')); // false
console.log(keys.includes('reduce')); // false
```

你突然意识到一个从未思考过的问题：**那些内建方法到底存在哪里？为什么它们"隐形"了？**

"我明明能调用 `data.map()`，" 你自言自语，"但 `Object.keys()` 却看不到它们？"

你决定暂时放下工作，彻底搞清楚这个问题。

---

## 追踪方法的位置

下午两点半，你打开浏览器控制台，开始手动追踪。

"首先，确认这些方法不是数组自己的属性，" 你说：

```javascript
console.log(data.hasOwnProperty('map')); // false
console.log(data.hasOwnProperty('filter')); // false
console.log(data.hasOwnProperty('unique')); // true - 我自己加的
```

"所以 `map` 和 `filter` 不在 `data` 自身上，" 你总结，"那它们在哪？"

你想起了原型链的知识："如果不在对象自身上，就去原型上找！"

```javascript
console.log(Object.getPrototypeOf(data)); // [constructor: Array, ...]
```

控制台显示了一个巨大的对象，里面密密麻麻都是方法名。

"这就是 `Array.prototype`！" 你恍然大悟。

你继续验证：

```javascript
console.log(typeof Array.prototype.map); // 'function' - 找到了！
console.log(typeof Array.prototype.filter); // 'function'
console.log(typeof Array.prototype.reduce); // 'function'

// 确认原型关系
console.log(Object.getPrototypeOf(data) === Array.prototype); // true
```

"所以所有数组都继承自 `Array.prototype`，" 你说，"难怪每个数组都能用 `map`、`filter` 这些方法。"

但你还有一个疑问："为什么 `Object.keys()` 看不到这些原型上的方法？"

你检查了属性描述符：

```javascript
const descriptor1 = Object.getOwnPropertyDescriptor(data, 'unique');
console.log('unique:', descriptor1);
// { value: [Function], writable: true, enumerable: true, configurable: true }

const descriptor2 = Object.getOwnPropertyDescriptor(Array.prototype, 'map');
console.log('map:', descriptor2);
// { value: [Function], writable: true, enumerable: false, configurable: true }
```

"啊哈！" 你拍了下桌子，"`enumerable: false`！"

你终于明白了：**内建方法的 `enumerable` 属性是 `false`，所以它们不会出现在 `Object.keys()` 和 `for...in` 中。**

"这设计太巧妙了，" 你说，"如果内建方法可枚举，遍历数组时就会把所有方法都遍历出来，那就乱套了。"

---

## 原型链的层次结构

下午三点，你好奇心大发，决定探索整个原型链的结构。

"数组的原型链到底有几层？" 你问自己。

你写了个递归函数追踪原型链：

```javascript
function tracePrototypeChain(obj) {
    const chain = [];
    let current = obj;

    while (current !== null) {
        chain.push(current);
        current = Object.getPrototypeOf(current);
    }

    return chain;
}

const arr = [1, 2, 3];
const chain = tracePrototypeChain(arr);

console.log('原型链长度:', chain.length); // 3

chain.forEach((proto, index) => {
    console.log(`层级 ${index}:`, proto.constructor?.name || 'null');
});
// 层级 0: Array
// 层级 1: Array (Array.prototype)
// 层级 2: Object (Object.prototype)
```

"等等，" 你困惑，"层级 0 和层级 1 都是 Array？"

你仔细检查：

```javascript
console.log('层级 0:', arr);
console.log('层级 1:', Object.getPrototypeOf(arr));
console.log('层级 2:', Object.getPrototypeOf(Object.getPrototypeOf(arr)));
console.log('层级 3:', Object.getPrototypeOf(Object.getPrototypeOf(Object.getPrototypeOf(arr))));

// 更清晰的表达
console.log('arr:', arr);
console.log('arr.__proto__:', Object.getPrototypeOf(arr)); // Array.prototype
console.log('arr.__proto__.__proto__:', Object.getPrototypeOf(Object.getPrototypeOf(arr))); // Object.prototype
console.log('arr.__proto__.__proto__.__proto__:', Object.getPrototypeOf(Object.getPrototypeOf(Object.getPrototypeOf(arr)))); // null
```

你在纸上画了个图：

```
[1, 2, 3] (数组实例)
    ↓ [[Prototype]]
Array.prototype (有 push, map, filter, reduce...)
    ↓ [[Prototype]]
Object.prototype (有 toString, hasOwnProperty, valueOf...)
    ↓ [[Prototype]]
null (原型链终点)
```

"原来数组有两层原型！" 你说，"`Array.prototype` 提供数组专用方法，`Object.prototype` 提供通用方法。"

你测试了其他类型：

```javascript
// 字符串
const str = 'hello';
console.log(Object.getPrototypeOf(str) === String.prototype); // true
console.log(Object.getPrototypeOf(String.prototype) === Object.prototype); // true

// 数字
const num = 42;
console.log(Object.getPrototypeOf(num) === Number.prototype); // true
console.log(Object.getPrototypeOf(Number.prototype) === Object.prototype); // true

// 函数
function fn() {}
console.log(Object.getPrototypeOf(fn) === Function.prototype); // true
console.log(Object.getPrototypeOf(Function.prototype) === Object.prototype); // true
```

"所有内建类型都是这个模式，" 你总结，"都继承自 `Object.prototype`。"

---

## Object.prototype 的特殊地位

下午四点，你泡了杯咖啡，继续研究 `Object.prototype`。

"为什么所有类型都继承 `Object.prototype`？" 你好奇。

你检查了 `Object.prototype` 上的方法：

```javascript
console.log(Object.getOwnPropertyNames(Object.prototype));
// ['constructor', 'toString', 'toLocaleString', 'valueOf',
//  'hasOwnProperty', 'isPrototypeOf', 'propertyIsEnumerable', ...]
```

"这些方法太常用了，" 你说，"难怪要让所有对象都继承它们。"

你测试了几个例子：

```javascript
// 数组有 toString，但它覆盖了 Object.prototype.toString
const arr = [1, 2, 3];
console.log(arr.toString()); // '1,2,3' - Array 版本
console.log(Object.prototype.toString.call(arr)); // '[object Array]' - Object 版本

// 普通对象也有 toString
const obj = { name: '张三' };
console.log(obj.toString()); // '[object Object]' - Object 版本

// 自定义对象
function User(name) {
    this.name = name;
}

const user = new User('李四');
console.log(user.toString()); // '[object Object]' - 继承自 Object.prototype
console.log(user.hasOwnProperty('name')); // true - 也是继承的
```

"所以 `Object.prototype` 就像所有对象的'终极祖先'，" 你说，"提供了最基础、最通用的方法。"

你突然想到一个问题："那能往 `Object.prototype` 上添加方法吗？"

```javascript
// 试试看
Object.prototype.sayHello = function() {
    console.log('Hello from', this);
};

const arr2 = [1, 2];
arr2.sayHello(); // Hello from [1, 2]

const str2 = 'test';
str2.sayHello(); // Hello from test

const obj2 = {};
obj2.sayHello(); // Hello from {}
```

"天哪！" 你惊讶，"所有对象都有了 `sayHello` 方法！"

但你马上意识到危险性：

```javascript
for (let key in obj2) {
    console.log(key); // 输出 'sayHello' - 污染了所有对象的遍历
}

// 赶紧删除
delete Object.prototype.sayHello;
```

"绝对不能修改 `Object.prototype`，" 你自言自语，"这会污染整个 JavaScript 环境。"

---

## 基本类型的包装之谜

下午五点，你注意到一个奇怪的现象。

"字符串、数字这些基本类型不是对象，" 你说，"为什么它们也有方法？"

你做了个实验：

```javascript
const str = 'hello';

// 基本类型有方法
console.log(str.toUpperCase()); // 'HELLO'
console.log(str.length); // 5

// 但它是对象吗？
console.log(typeof str); // 'string' - 不是对象

// 那原型在哪？
console.log(Object.getPrototypeOf(str)); // String.prototype
```

"居然能获取原型？" 你困惑。

你尝试给基本类型添加属性：

```javascript
const str2 = 'test';
str2.customProp = 'value';

console.log(str2.customProp); // undefined - 添加失败？
```

"属性消失了？" 你更困惑了。

你查阅了文档，终于明白了：**JavaScript 在访问基本类型的属性时，会临时创建包装对象**。

你写代码验证：

```javascript
const str = 'hello';

// 当你写 str.toUpperCase() 时，JavaScript 实际做的是：
// 1. 创建临时包装对象: const temp = new String('hello');
// 2. 调用方法: temp.toUpperCase();
// 3. 销毁临时对象: temp = null;

// 所以这样是无效的
str.customProp = 'value';
// 实际上是:
// const temp = new String('hello');
// temp.customProp = 'value'; // 在临时对象上设置
// temp = null; // 临时对象被销毁，属性丢失

// 但可以在原型上添加（虽然不推荐）
String.prototype.shout = function() {
    return this.toUpperCase() + '!!!';
};

console.log(str.shout()); // 'HELLO!!!'
console.log('world'.shout()); // 'WORLD!!!' - 所有字符串都有了
```

"原来如此，" 你恍然大悟，"基本类型访问方法时会临时包装，用完就销毁。这就是为什么不能给基本类型添加属性。"

---

## 内建方法的数量统计

下午六点，你的好奇心驱使你统计一下各个内建原型到底有多少方法。

```javascript
function countMethods(prototype, name) {
    const props = Object.getOwnPropertyNames(prototype);
    const methods = props.filter(prop => typeof prototype[prop] === 'function');

    console.log(`${name}:`);
    console.log(`  总属性数: ${props.length}`);
    console.log(`  方法数: ${methods.length}`);
    console.log(`  方法列表: ${methods.slice(0, 10).join(', ')}...`);
    console.log('');
}

countMethods(Array.prototype, 'Array.prototype');
// Array.prototype:
//   总属性数: 38
//   方法数: 37
//   方法列表: constructor, at, concat, copyWithin, fill, find, findIndex, findLast, findLastIndex, flat...

countMethods(String.prototype, 'String.prototype');
// String.prototype:
//   总属性数: 52
//   方法数: 51
//   方法列表: constructor, anchor, at, big, blink, bold, charAt, charCodeAt, codePointAt, concat...

countMethods(Number.prototype, 'Number.prototype');
// Number.prototype:
//   总属性数: 8
//   方法数: 7
//   方法列表: constructor, toExponential, toFixed, toLocaleString, toPrecision, toString, valueOf

countMethods(Object.prototype, 'Object.prototype');
// Object.prototype:
//   总属性数: 12
//   方法数: 11
//   方法列表: constructor, hasOwnProperty, isPrototypeOf, propertyIsEnumerable, toLocaleString, toString, valueOf...

countMethods(Function.prototype, 'Function.prototype');
// Function.prototype:
//   总属性数: 6
//   方法数: 5
//   方法列表: apply, bind, call, toString, constructor
```

"数组有 37 个方法，字符串有 51 个！" 你惊叹，"这就是为什么 JavaScript 的内建类型这么强大。"

---

## 借用内建方法的技巧

晚上七点，你想起白天看到的一个代码片段，使用了一种奇怪的写法。

```javascript
// 别人的代码
function sum() {
    return Array.prototype.reduce.call(arguments, (a, b) => a + b, 0);
}
```

"为什么不直接用 `arguments.reduce()`？" 你疑惑。

你测试了一下：

```javascript
function test() {
    console.log(typeof arguments); // 'object'
    console.log(typeof arguments.reduce); // 'undefined' - 没有 reduce 方法？

    console.log(arguments instanceof Array); // false - 不是数组

    // 查看原型
    console.log(Object.getPrototypeOf(arguments)); // Object.prototype - 不是 Array.prototype！
}

test(1, 2, 3);
```

"原来 `arguments` 虽然像数组，但它的原型是 `Object.prototype`，所以没有数组方法，" 你明白了。

"但可以'借用'数组方法！" 你兴奋地尝试：

```javascript
function sum() {
    // 方法1: 使用 call 借用
    return Array.prototype.reduce.call(arguments, (a, b) => a + b, 0);
}

console.log(sum(1, 2, 3, 4)); // 10

// 类似的用法
function logArguments() {
    // arguments 没有 forEach，借用数组的
    Array.prototype.forEach.call(arguments, (arg, index) => {
        console.log(`参数 ${index}:`, arg);
    });
}

logArguments('a', 'b', 'c');
// 参数 0: a
// 参数 1: b
// 参数 2: c

// ES6 之后可以用展开运算符
function sum2(...args) {
    return args.reduce((a, b) => a + b, 0); // args 是真正的数组
}

console.log(sum2(1, 2, 3, 4)); // 10
```

"这技巧太实用了，" 你说，"可以让类数组对象也能用数组方法。"

---

## 你的原型笔记本

晚上八点，你整理了一天的收获。

你在笔记本上写下标题："JavaScript 的内建原型体系"

### 核心洞察 #1: 原型链的统一结构

你写道：

"所有内建对象都遵循相同的原型链模式：

```
实例 → 类型.prototype → Object.prototype → null
```

例如：
- 数组: `[1,2,3] → Array.prototype → Object.prototype → null`
- 字符串: `'hello' → String.prototype → Object.prototype → null`
- 函数: `function(){} → Function.prototype → Object.prototype → null`

这种统一的结构让 JavaScript 的类型系统既灵活又一致。"

### 核心洞察 #2: 不可枚举的内建方法

"内建方法的 `enumerable: false` 是关键设计：

- 如果内建方法可枚举，`Object.keys()` 和 `for...in` 会把所有原型方法都列出来
- 这会导致遍历对象时出现大量方法名，完全不是我们想要的
- 设置为不可枚举后，遍历只会列出对象自身的数据属性

这就是为什么 `Object.keys([1,2,3])` 只返回 `['0', '1', '2']`，而不包含 `map`、`filter` 等方法。"

### 核心洞察 #3: Object.prototype 的终极地位

"Object.prototype 是几乎所有对象的终极祖先：

- 它提供了最基础、最通用的方法（toString, hasOwnProperty, valueOf等）
- 所有内建类型的原型最终都继承它
- **绝对不要修改 Object.prototype**（除了 polyfill）
- 修改它会污染整个 JavaScript 环境，影响所有对象"

### 核心洞察 #4: 基本类型的临时包装

"JavaScript 的基本类型（string, number, boolean）不是对象，但可以调用方法：

```javascript
'hello'.toUpperCase(); // 临时包装成 String 对象
```

过程：
1. 访问属性时，创建临时包装对象: `new String('hello')`
2. 调用方法: `temp.toUpperCase()`
3. 销毁临时对象

这就是为什么不能给基本类型添加属性——包装对象用完就销毁了。"

### 核心洞察 #5: 方法借用的技巧

"类数组对象（如 `arguments`、DOM NodeList）没有数组方法，但可以借用：

```javascript
Array.prototype.forEach.call(arguments, callback);
Array.prototype.slice.call(arrayLike);
```

原理：数组方法内部只要求 `this` 有 `length` 属性和数字索引，不要求一定是数组。"

你合上笔记本，满意地关上电脑。

"下次再遇到 `Object.keys()` 的困惑，我就知道原因了，" 你说，"原来内建方法藏在 `prototype` 上，而且是不可枚举的。"

---

## 知识总结

**规则 1: 内建对象的原型链层次**

所有内建对象都有原型，形成统一的继承结构：

```javascript
// 数组
[] → Array.prototype → Object.prototype → null

// 字符串
'hello' → String.prototype → Object.prototype → null

// 数字
42 → Number.prototype → Object.prototype → null

// 函数
function(){} → Function.prototype → Object.prototype → null
```

这是 JavaScript 类型系统的基础。每个类型有自己的专用方法，同时继承通用方法。

---

**规则 2: Object.prototype 的终极地位**

几乎所有对象最终都继承 `Object.prototype`，它定义了通用方法：

```javascript
Object.getOwnPropertyNames(Object.prototype);
// ['constructor', 'toString', 'toLocaleString', 'valueOf',
//  'hasOwnProperty', 'isPrototypeOf', 'propertyIsEnumerable', ...]
```

这些方法对所有对象可用。**绝对不要修改 Object.prototype**（除了 polyfill），否则会污染整个环境。

---

**规则 3: 内建方法的不可枚举性**

内建方法的 `enumerable: false`，不会出现在 `Object.keys()` 和 `for...in` 中：

```javascript
const arr = [1, 2, 3];

Object.keys(arr); // ['0', '1', '2'] - 不包含 map, filter 等

const descriptor = Object.getOwnPropertyDescriptor(Array.prototype, 'map');
console.log(descriptor.enumerable); // false
```

这避免了遍历对象时出现大量原型方法。

---

**规则 4: 基本类型的临时包装**

访问基本类型属性时，JavaScript 临时创建包装对象：

```javascript
'hello'.toUpperCase(); // 临时创建 new String('hello')

// 过程:
// 1. const temp = new String('hello');
// 2. temp.toUpperCase();
// 3. temp = null; (销毁)
```

包装对象用完立即销毁，因此不能给基本类型添加属性：

```javascript
const str = 'test';
str.prop = 'value'; // 在临时对象上设置，立即销毁
console.log(str.prop); // undefined
```

---

**规则 5: 内建方法的覆盖与借用**

子类可以覆盖内建方法，也可以借用内建方法：

```javascript
// 覆盖
const arr = [1, 2, 3];
console.log(arr.toString()); // '1,2,3' - Array 覆盖了 Object 版本

// 借用数组方法处理类数组对象
function sum() {
    return Array.prototype.reduce.call(arguments, (a, b) => a + b, 0);
}

sum(1, 2, 3); // 6
```

借用的原理：数组方法内部只要求 `this` 有 `length` 和数字索引，不要求一定是数组。

---

**规则 6: 原生原型的修改风险**

修改内建 `prototype` 会影响全局所有代码：

```javascript
// ❌ 危险！全局污染
Array.prototype.myMethod = function() { ... };

// ✅ 唯一合理场景：polyfill（先检查是否存在）
if (!Array.prototype.includes) {
    Array.prototype.includes = function(searchElement) {
        // polyfill 实现
    };
}
```

除了 polyfill，绝对不要修改内建原型。

---

**事故档案编号**: PROTO-2024-1884
**影响范围**: 原生原型, Array/String/Function.prototype, Object.prototype, 方法借用
**根本原因**: 不了解内建原型体系，导致误修改全局原型或不理解方法的来源
**修复成本**: 低

这是 JavaScript 世界第 84 次被记录的原生原型事故。JavaScript 内建对象（Array, String, Function, Number 等）都有 `prototype`，定义了类型专用方法。所有对象的原型链最终到达 `Object.prototype` 再到 `null`。内建方法的 `enumerable: false` 避免了遍历污染。基本类型访问属性时临时包装成对象，用完销毁。不要修改内建 `prototype`（除了 polyfill）。可以覆盖内建方法或借用它们（`call`/`apply`）。理解原生原型是掌握 JavaScript 类型系统的关键。

---

《第 83 次记录: F.prototype 的特殊地位 —— 构造的约定》

---

## 意外的原型丢失

周一上午九点，你在重构一个插件系统时遇到了奇怪的问题。

```javascript
function Plugin(name) {
    this.name = name;
}

Plugin.prototype.init = function() {
    console.log(`${this.name} 初始化`);
};

Plugin.prototype.destroy = function() {
    console.log(`${this.name} 销毁`);
};

// 创建插件实例
const plugin1 = new Plugin('分析插件');
plugin1.init(); // '分析插件 初始化' - 正常工作

// 后来你想给插件添加更多方法，决定用新对象替换 prototype
Plugin.prototype = {
    init: function() {
        console.log(`${this.name} 初始化`);
    },
    destroy: function() {
        console.log(`${this.name} 销毁`);
    },
    enable: function() {
        console.log(`${this.name} 启用`);
    }
};

// 创建新插件
const plugin2 = new Plugin('日志插件');
plugin2.enable(); // '日志插件 启用' - 正常

// 但是尝试判断类型时...
console.log(plugin2.constructor === Plugin); // false - 什么?!
console.log(plugin2.constructor); // [Function: Object] - 变成 Object 了!
```

"为什么 `constructor` 丢失了？" 你困惑不解，"这会导致类型判断出错。"

---

## constructor 的自动创建

上午十点，老张看到你的问题。

"你覆盖了整个 `prototype` 对象，" 老张说，"丢失了默认的 `constructor` 属性。"

"默认的 `constructor`？" 你问。

"对，" 老张解释，"当你定义一个函数时，JavaScript 会自动做两件事。"

```javascript
function MyFunction() {}

// JavaScript 自动执行：
// 1. 创建一个新对象赋给 MyFunction.prototype
// MyFunction.prototype = {};

// 2. 在这个对象上添加 constructor 属性指回函数本身
// MyFunction.prototype.constructor = MyFunction;

console.log(MyFunction.prototype.constructor === MyFunction); // true
```

"所以 `prototype.constructor` 是自动添加的，" 你说，"如果我替换整个 `prototype`，这个属性就丢了。"

"完全正确，" 老张点头，"这就是为什么很多人在覆盖 `prototype` 后手动恢复 `constructor`。"

```javascript
function Plugin(name) {
    this.name = name;
}

// 正确的做法：覆盖 prototype 后恢复 constructor
Plugin.prototype = {
    constructor: Plugin, // 手动恢复
    init: function() {
        console.log(`${this.name} 初始化`);
    },
    enable: function() {
        console.log(`${this.name} 启用`);
    }
};

const plugin = new Plugin('测试插件');
console.log(plugin.constructor === Plugin); // true - 正常了
```

---

## prototype 的默认值

上午十一点，你开始探索函数的 `prototype` 属性。

"每个函数都有 `prototype` 属性吗？" 你问。

"几乎所有，" 老张说，"除了箭头函数和一些内建函数。"

```javascript
// 普通函数有 prototype
function normalFunc() {}
console.log(normalFunc.prototype); // {constructor: normalFunc}

// 箭头函数没有 prototype
const arrowFunc = () => {};
console.log(arrowFunc.prototype); // undefined

// 不能用箭头函数作为构造函数
try {
    new arrowFunc(); // TypeError: arrowFunc is not a constructor
} catch (e) {
    console.error(e.message);
}

// 内建函数的 prototype
console.log(Array.prototype); // [...各种数组方法]
console.log(Object.prototype); // {...各种对象方法}
```

"所以 `prototype` 是专门给构造函数用的，" 你说。

"对，" 老张说，"只有用 `new` 调用时，`prototype` 才有意义。普通调用时，`prototype` 没有任何作用。"

```javascript
function User(name) {
    this.name = name;
}

User.prototype.greet = function() {
    console.log(`你好，我是 ${this.name}`);
};

// 用 new 调用：实例继承 prototype
const user1 = new User('张三');
user1.greet(); // '你好，我是张三'

// 普通调用：prototype 无效
const user2 = User('李四'); // this 指向 window/undefined
console.log(user2); // undefined
```

---

## prototype 的动态修改

上午十一点半，你测试了修改 `prototype` 的不同方式。

"如果我只是在 `prototype` 上添加方法，" 你说，"已有实例会受影响吗？"

```javascript
function Animal(name) {
    this.name = name;
}

const dog = new Animal('旺财');

// 在 prototype 上添加方法
Animal.prototype.speak = function() {
    console.log(`${this.name} 发出声音`);
};

// 已有实例可以使用新方法
dog.speak(); // '旺财 发出声音'
```

"可以，" 老张说，"因为实例通过引用访问 `prototype`，添加方法会立即生效。"

"那如果我完全替换 `prototype` 呢？" 你继续测试：

```javascript
function Animal(name) {
    this.name = name;
}

const cat = new Animal('喵喵');

// 完全替换 prototype
Animal.prototype = {
    constructor: Animal,
    speak: function() {
        console.log('新的叫声');
    }
};

// 旧实例还指向旧 prototype，没有新方法
console.log(typeof cat.speak); // 'undefined'

// 新实例指向新 prototype
const bird = new Animal('啾啾');
bird.speak(); // '新的叫声'

// 两个实例的原型不同
console.log(Object.getPrototypeOf(cat) === Object.getPrototypeOf(bird)); // false
```

"明白了，" 你说，"添加方法影响所有实例，替换 `prototype` 只影响之后的实例。"

---

## 手动设置 prototype

中午十二点，老张展示了手动设置原型的方法。

"除了用 `new`，" 老张说，"还可以手动设置对象的原型。"

```javascript
function User(name) {
    this.name = name;
}

User.prototype.greet = function() {
    console.log(`你好，我是 ${this.name}`);
};

// 方式 1: Object.create() - 推荐
const user1 = Object.create(User.prototype);
User.call(user1, '张三'); // 手动调用构造函数
user1.greet(); // '你好，我是张三'

// 方式 2: Object.setPrototypeOf() - 性能较差
const user2 = { name: '李四' };
Object.setPrototypeOf(user2, User.prototype);
user2.greet(); // '你好，我是李四'

// 方式 3: __proto__ - 不推荐（兼容性问题）
const user3 = { name: '王五' };
user3.__proto__ = User.prototype;
user3.greet(); // '你好，我是王五'
```

"为什么 `setPrototypeOf` 性能差？" 你问。

"因为修改已有对象的原型会破坏 JavaScript 引擎的优化，" 老张解释，"引擎假设对象的原型是固定的，修改原型会导致去优化。所以最好在创建对象时就确定原型，用 `Object.create()` 或 `new`。"

---

## prototype 的属性覆盖

下午两点，你发现了一个有趣的现象。

"如果我在 `prototype` 上定义的属性，和实例属性同名会怎样？" 你测试：

```javascript
function Counter() {
    this.count = 0; // 实例属性
}

Counter.prototype.count = 100; // 原型属性

const counter = new Counter();

console.log(counter.count); // 0 - 实例属性遮蔽原型属性

delete counter.count; // 删除实例属性
console.log(counter.count); // 100 - 露出原型属性
```

"实例属性优先，" 你总结。

"对，" 老张说，"所以在 `prototype` 上通常只放方法，不放数据。数据应该在构造函数中用 `this` 初始化。"

"为什么？" 你问。

"因为 `prototype` 上的数据是共享的，" 老张警告：

```javascript
function Team(name) {
    this.name = name;
}

Team.prototype.members = []; // 危险！所有实例共享

const team1 = new Team('前端组');
const team2 = new Team('后端组');

team1.members.push('张三');

// team2 的 members 也被修改了！
console.log(team2.members); // ['张三']
console.log(team1.members === team2.members); // true - 同一个数组
```

"应该在构造函数中初始化，" 你说：

```javascript
function Team(name) {
    this.name = name;
    this.members = []; // 每个实例有自己的数组
}

const team1 = new Team('前端组');
const team2 = new Team('后端组');

team1.members.push('张三');

console.log(team2.members); // [] - 不受影响
console.log(team1.members === team2.members); // false - 不同数组
```

---

## prototype 的描述符

下午三点，你研究了 `prototype` 属性本身的特性。

"`prototype` 属性可以被删除或修改吗？" 你问。

"可以看看它的描述符，" 老张说：

```javascript
function MyFunc() {}

const descriptor = Object.getOwnPropertyDescriptor(MyFunc, 'prototype');
console.log(descriptor);
// {
//   value: {constructor: MyFunc},
//   writable: true,      // 可写
//   enumerable: false,   // 不可枚举
//   configurable: false  // 不可配置
// }
```

"不可配置，" 你说，"所以不能删除 `prototype` 属性。"

```javascript
function Func() {}

delete Func.prototype; // 删除失败
console.log(Func.prototype); // 还在

// 但可以修改它的值
Func.prototype = { custom: true };
console.log(Func.prototype); // {custom: true}
```

"对，" 老张说，"`prototype` 属性本身不能删除，但可以替换它指向的对象。"

---

## 内建构造函数的 prototype

下午四点，你开始研究内建对象的 `prototype`。

"JavaScript 内建的构造函数，" 你说，"它们的 `prototype` 是什么样的？"

```javascript
// Array.prototype
console.log(typeof Array.prototype.push); // 'function'
console.log(typeof Array.prototype.map); // 'function'

// String.prototype
console.log(typeof String.prototype.toUpperCase); // 'function'
console.log(typeof String.prototype.slice); // 'function'

// Number.prototype
console.log(typeof Number.prototype.toFixed); // 'function'

// 所有数组都继承 Array.prototype
const arr = [1, 2, 3];
console.log(Object.getPrototypeOf(arr) === Array.prototype); // true

// 所以数组可以使用 Array.prototype 的方法
arr.push(4);
console.log(arr.map(x => x * 2)); // [2, 4, 6, 8]
```

"这就是为什么数组有 `push`、`map` 等方法，" 你恍然大悟，"它们都来自 `Array.prototype`。"

"对，" 老张说，"所有内建类型都是这样工作的。"

```javascript
// 字符串
const str = 'hello';
console.log(Object.getPrototypeOf(str) === String.prototype); // true
str.toUpperCase(); // 调用 String.prototype.toUpperCase

// 数字
const num = 42;
console.log(Object.getPrototypeOf(num) === Number.prototype); // true
num.toFixed(2); // 调用 Number.prototype.toFixed
```

---

## 修改内建 prototype 的风险

下午五点，老张警告你不要随意修改内建的 `prototype`。

"理论上可以给内建的 `prototype` 添加方法，" 老张说，"这叫猴子补丁(monkey patching)，但很危险。"

```javascript
// 给 Array.prototype 添加自定义方法
Array.prototype.last = function() {
    return this[this.length - 1];
};

const arr = [1, 2, 3];
console.log(arr.last()); // 3 - 可以用

// 但这会影响所有数组
const arr2 = ['a', 'b', 'c'];
console.log(arr2.last()); // 'c'
```

"有什么问题吗？" 你问。

"几个问题，" 老张列举：

```javascript
// 问题 1: 污染全局，影响所有代码
Array.prototype.clear = function() {
    this.length = 0;
};
// 现在整个项目的所有数组都有 clear 方法

// 问题 2: 可能与未来标准冲突
// 如果未来 ECMAScript 添加了 Array.prototype.last，你的实现可能不兼容

// 问题 3: 影响 for...in 循环
Array.prototype.myMethod = function() {};

const arr = ['a', 'b'];
for (let key in arr) {
    console.log(key); // '0', '1', 'myMethod' - 方法也被遍历了！
}

// 问题 4: 多个库可能冲突
// 库 A 添加 Array.prototype.remove
// 库 B 也添加 Array.prototype.remove，但实现不同
// 导致冲突
```

"那什么时候可以修改内建 `prototype`？" 你问。

"只有一种情况，" 老张说，"Polyfill —— 为旧浏览器添加新标准的方法。"

```javascript
// Polyfill 示例：为旧浏览器添加 Array.prototype.includes
if (!Array.prototype.includes) {
    Array.prototype.includes = function(searchElement) {
        return this.indexOf(searchElement) !== -1;
    };
}
```

---

## 总结与反思

下午六点，你整理今天学到的知识。

**F.prototype 的核心特性：**
- 函数创建时，JavaScript 自动创建 `prototype` 对象并添加 `constructor` 属性
- `new F()` 时，新对象的 `[[Prototype]]` 指向 `F.prototype`
- `prototype` 属性本身不可配置(不能删除)，但可以修改其值
- 只有构造函数需要 `prototype`，普通调用时无意义

**常见陷阱：**
- 覆盖整个 `prototype` 会丢失 `constructor` 属性
- 在 `prototype` 上放引用类型数据会被所有实例共享
- 修改内建 `prototype` 会影响全局，应避免（除了 polyfill）
- `Object.setPrototypeOf()` 性能差，应该用 `Object.create()` 或 `new`

你保存了文档，明天准备继续学习原生原型系统。

---

## 知识总结

**规则 1: F.prototype 的自动初始化**

定义函数时，JavaScript 自动创建 `prototype` 对象并设置 `constructor`：

```javascript
function F() {}

// 等价于
F.prototype = { constructor: F };
```

`new F()` 创建的实例的 `[[Prototype]]` 会指向 `F.prototype`。这是构造函数继承的基础。

---

**规则 2: constructor 属性的作用与丢失**

`prototype.constructor` 指向构造函数本身，用于类型判断和创建同类对象：

```javascript
const obj = new F();
obj.constructor === F; // true
new obj.constructor(); // 创建同类对象
```

覆盖整个 `prototype` 会丢失 `constructor`，需手动恢复：

```javascript
F.prototype = { /* 新方法 */ }; // 丢失 constructor
F.prototype = { constructor: F, /* 新方法 */ }; // 恢复 constructor
```

---

**规则 3: prototype 的动态性**

在 `prototype` 上**添加**方法会影响所有实例（包括已创建的）：

```javascript
const obj = new F();
F.prototype.newMethod = function() {};
obj.newMethod(); // 可用
```

**替换**整个 `prototype` 只影响之后创建的实例：

```javascript
const obj1 = new F();
F.prototype = { /* 新对象 */ };
const obj2 = new F();
// obj1 和 obj2 的原型不同
```

---

**规则 4: prototype 上的数据共享陷阱**

`prototype` 上的引用类型数据会被所有实例共享：

```javascript
F.prototype.arr = []; // 危险！
const obj1 = new F();
const obj2 = new F();
obj1.arr.push(1);
console.log(obj2.arr); // [1] - 被共享了
```

**原则**：`prototype` 上只放方法和不可变常量，可变数据放在构造函数中用 `this` 初始化。

---

**规则 5: prototype 属性的描述符**

函数的 `prototype` 属性特性：

```javascript
Object.getOwnPropertyDescriptor(F, 'prototype');
// { writable: true, enumerable: false, configurable: false }
```

- `writable: true` - 可以替换 `prototype` 对象
- `configurable: false` - 不能删除 `prototype` 属性
- `enumerable: false` - 不在 `for...in` 中出现

---

**规则 6: 修改内建 prototype 的风险**

修改 `Array.prototype`、`String.prototype` 等会影响全局，产生多种问题：

| 风险 | 说明 | 影响 |
|------|------|------|
| 全局污染 | 影响所有代码 | 高 |
| 标准冲突 | 未来标准可能添加同名方法 | 中 |
| 遍历问题 | 方法出现在 `for...in` 中 | 低 |
| 库冲突 | 多个库可能添加同名方法 | 高 |

**唯一合理场景**：Polyfill（为旧浏览器添加新标准方法，需先检查 `if (!Array.prototype.includes)`）。

---

**事故档案编号**: PROTO-2024-1883
**影响范围**: F.prototype, constructor 属性, 动态修改原型, 内建原型污染
**根本原因**: 不理解 `F.prototype` 的特殊地位和自动行为，导致 constructor 丢失或数据共享问题
**修复成本**: 低（手动恢复 constructor，避免共享数据），需理解 prototype 的约定和限制

这是 JavaScript 世界第 83 次被记录的原型配置事故。函数创建时 JavaScript 自动初始化 `prototype` 为 `{constructor: F}`，`new F()` 时实例的 `[[Prototype]]` 指向 `F.prototype`。覆盖整个 `prototype` 会丢失 `constructor`，需手动恢复。在 `prototype` 上添加方法影响所有实例，替换 `prototype` 只影响后续实例。`prototype` 上的引用类型数据会被共享，应避免。`prototype` 属性本身 `configurable: false` 不能删除，但 `writable: true` 可修改。修改内建 `prototype`（猴子补丁）会全局污染，只在 polyfill 场景合理使用。理解 `F.prototype` 的特殊地位是正确使用构造函数的基础。

---

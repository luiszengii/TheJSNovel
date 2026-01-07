《第 91 次记录: instanceof 判定 —— 血统的追溯》

---

## 类型检查的困惑

周四上午九点，你正在实现一个插件系统的类型验证功能。

系统需要判断传入的对象是否是有效的插件实例。你写下了最直观的检查代码：

```javascript
class Plugin {
    constructor(name) {
        this.name = name;
    }

    init() {
        console.log(`${this.name} 初始化`);
    }
}

class AnalyticsPlugin extends Plugin {
    constructor() {
        super('分析插件');
    }

    trackEvent(event) {
        console.log('追踪事件:', event);
    }
}

function registerPlugin(plugin) {
    if (plugin instanceof Plugin) {
        plugin.init();
        console.log('插件注册成功');
    } else {
        throw new TypeError('必须是 Plugin 实例');
    }
}

const analytics = new AnalyticsPlugin();
registerPlugin(analytics); // 成功
```

"看起来没问题，" 你说，"`instanceof` 能正确识别继承关系。"

但测试小林很快发现了第一个问题：

```javascript
// 用户自己创建的插件对象
const customPlugin = {
    name: '自定义插件',
    init() {
        console.log(`${this.name} 初始化`);
    }
};

try {
    registerPlugin(customPlugin);
} catch (e) {
    console.error(e.message); // '必须是 Plugin 实例'
}
```

"这个对象有所有需要的方法，" 小林说，"但因为不是用 `new Plugin()` 创建的，所以被拒绝了。这样是不是太严格了？"

"确实，" 你皱眉，"有时候我们关心的是对象的能力（有哪些方法），而不是它的血统（是否继承特定类）。"

---

## instanceof 的本质

上午十点，老张过来讲解 `instanceof` 的工作原理。

"`instanceof` 不是检查类型，" 老张说，"而是检查原型链。"

他在白板上画图：

```javascript
const analytics = new AnalyticsPlugin();

// instanceof 检查: analytics 的原型链上是否有 Plugin.prototype
console.log(analytics instanceof AnalyticsPlugin); // true
console.log(analytics instanceof Plugin); // true
console.log(analytics instanceof Object); // true

// 原型链:
// analytics
//   → AnalyticsPlugin.prototype
//     → Plugin.prototype
//       → Object.prototype
//         → null
```

"所以 `obj instanceof Constructor` 的算法是，" 老张解释：

```javascript
function myInstanceof(obj, Constructor) {
    // 获取对象的原型
    let proto = Object.getPrototypeOf(obj);
    
    // 获取构造函数的 prototype 属性
    const prototype = Constructor.prototype;
    
    // 沿着原型链查找
    while (proto !== null) {
        if (proto === prototype) {
            return true; // 找到了
        }
        proto = Object.getPrototypeOf(proto);
    }
    
    return false; // 未找到
}

const plugin = new AnalyticsPlugin();
console.log(myInstanceof(plugin, AnalyticsPlugin)); // true
console.log(myInstanceof(plugin, Plugin)); // true
console.log(myInstanceof(plugin, Object)); // true
```

"明白了，" 你说，"`instanceof` 是在原型链上查找构造函数的 `prototype`。"

---

## instanceof 的边界情况

上午十一点，你开始测试各种边界情况。

"基本类型怎么办？" 你问：

```javascript
console.log(42 instanceof Number); // false
console.log('hello' instanceof String); // false
console.log(true instanceof Boolean); // false

// 但包装对象可以
console.log(new Number(42) instanceof Number); // true
console.log(new String('hello') instanceof String); // true
```

"基本类型不是对象，" 老张说，"所以 `instanceof` 返回 `false`。"

"null 和 undefined 呢？"

```javascript
console.log(null instanceof Object); // false
console.log(undefined instanceof Object); // false
```

"它们也不是对象，" 老张说。

你继续测试函数和数组：

```javascript
function myFunc() {}
console.log(myFunc instanceof Function); // true
console.log(myFunc instanceof Object); // true

const arr = [1, 2, 3];
console.log(arr instanceof Array); // true
console.log(arr instanceof Object); // true

const obj = {};
console.log(obj instanceof Object); // true
console.log(obj instanceof Array); // false
```

"所有函数都是 `Function` 的实例，" 你总结，"所有数组都是 `Array` 的实例，它们最终都是 `Object` 的实例。"

---

## 原型修改导致的问题

中午十二点，你发现了一个诡异的现象。

"如果修改了 `prototype`，" 你说，"`instanceof` 的结果会变吗？"

```javascript
function Animal(name) {
    this.name = name;
}

const dog = new Animal('旺财');

console.log(dog instanceof Animal); // true

// 修改构造函数的 prototype
Animal.prototype = {};

console.log(dog instanceof Animal); // false - 突然变了！
```

"为什么？" 测试小林震惊了。

"因为 `instanceof` 是查找 `Animal.prototype` 是否在原型链上，" 老张解释，"你替换了 `Animal.prototype`，所以旧实例的原型链找不到新的 `Animal.prototype` 了。"

```javascript
// 旧实例的原型链
console.log(Object.getPrototypeOf(dog)); // { constructor: Animal } - 旧的 prototype

// 新的 prototype
console.log(Animal.prototype); // {} - 新的 prototype

// 两者不相等
console.log(Object.getPrototypeOf(dog) === Animal.prototype); // false
```

"所以不要替换整个 `prototype`，" 你说，"否则会破坏已有实例的类型判断。"

---

## Symbol.hasInstance 定制判定

下午两点，你发现可以自定义 `instanceof` 的行为。

"ES6 引入了 `Symbol.hasInstance`，" 老张说，"可以自定义 `instanceof` 的逻辑。"

```javascript
class Plugin {
    constructor(name) {
        this.name = name;
    }

    init() {
        console.log(`${this.name} 初始化`);
    }

    // 自定义 instanceof 行为
    static [Symbol.hasInstance](obj) {
        // 鸭子类型检查：有 init 方法就算是插件
        return obj !== null &&
               typeof obj === 'object' &&
               typeof obj.init === 'function' &&
               typeof obj.name === 'string';
    }
}

// 用 class 创建的实例
const official = new Plugin('官方插件');
console.log(official instanceof Plugin); // true

// 普通对象，但有 init 方法
const custom = {
    name: '自定义插件',
    init() {
        console.log('自定义插件初始化');
    }
};
console.log(custom instanceof Plugin); // true - 鸭子类型

// 缺少方法的对象
const invalid = { name: '无效插件' };
console.log(invalid instanceof Plugin); // false
```

"太强大了！" 你说，"现在 `instanceof` 可以检查对象的能力，而不只是血统。"

"但要注意，" 老张提醒，"过度使用会让类型检查变得不可预测。"

---

## 跨 frame 的问题

下午三点，前端小王遇到了一个奇怪的 bug。

"我的类型检查在 iframe 中失效了，" 小王说：

```javascript
// 主页面
const mainArray = [1, 2, 3];
console.log(mainArray instanceof Array); // true

// iframe 中的数组
const iframe = document.createElement('iframe');
document.body.appendChild(iframe);

const iframeArray = iframe.contentWindow.Array;
const arr = new iframeArray(1, 2, 3);

// 在主页面检查
console.log(arr instanceof Array); // false - 为什么？
console.log(arr instanceof iframe.contentWindow.Array); // true
```

"每个 frame 有自己的全局对象和内建构造函数，" 老张解释，"iframe 中的 `Array` 和主页面的 `Array` 是不同的构造函数。"

```javascript
console.log(Array === iframe.contentWindow.Array); // false

// 它们的 prototype 也不同
console.log(Array.prototype === iframe.contentWindow.Array.prototype); // false
```

"那怎么可靠地检查数组类型？" 小王问。

"用 `Array.isArray()`，" 老张说：

```javascript
console.log(Array.isArray(mainArray)); // true
console.log(Array.isArray(arr)); // true - 跨 frame 也能识别

// 或者用 Object.prototype.toString
console.log(Object.prototype.toString.call(arr)); // '[object Array]'
```

---

## instanceof 的替代方案

下午四点，你总结了类型检查的不同方法。

"不同场景应该用不同的检查方式，" 你说：

```javascript
// 1. 检查基本类型：用 typeof
console.log(typeof 42); // 'number'
console.log(typeof 'hello'); // 'string'
console.log(typeof true); // 'boolean'
console.log(typeof undefined); // 'undefined'
console.log(typeof function() {}); // 'function'

// 注意陷阱
console.log(typeof null); // 'object' - 历史遗留bug
console.log(typeof []); // 'object' - 数组也是 object

// 2. 检查数组：用 Array.isArray
console.log(Array.isArray([])); // true
console.log(Array.isArray({})); // false

// 3. 检查 null：直接比较
console.log(value === null);

// 4. 检查对象的能力：鸭子类型
function canFly(obj) {
    return obj !== null &&
           typeof obj === 'object' &&
           typeof obj.fly === 'function';
}

// 5. 检查构造函数：用 instanceof（单一全局环境）
class Bird {}
const bird = new Bird();
console.log(bird instanceof Bird); // true

// 6. 精确类型检查：用 Object.prototype.toString
function getType(value) {
    return Object.prototype.toString.call(value).slice(8, -1);
}

console.log(getType([])); // 'Array'
console.log(getType({})); // 'Object'
console.log(getType(null)); // 'Null'
console.log(getType(undefined)); // 'Undefined'
console.log(getType(new Date())); // 'Date'
console.log(getType(/regex/)); // 'RegExp'
```

---

## 类型检查的最佳实践

下午五点，老张分享了类型检查的经验。

"类型检查要根据目的选择方法，" 老张说：

```javascript
// 场景 1: 验证参数类型
function processUser(user) {
    // 检查对象的必要属性和方法
    if (!user || typeof user !== 'object') {
        throw new TypeError('user 必须是对象');
    }
    
    if (typeof user.name !== 'string') {
        throw new TypeError('user.name 必须是字符串');
    }
    
    if (typeof user.save !== 'function') {
        throw new TypeError('user 必须有 save 方法');
    }
    
    // 通过检查，可以安全使用
    user.save();
}

// 场景 2: 多态分发
function handleInput(input) {
    if (typeof input === 'string') {
        return parseString(input);
    } else if (Array.isArray(input)) {
        return parseArray(input);
    } else if (input instanceof Date) {
        return parseDate(input);
    } else if (typeof input === 'object' && input !== null) {
        return parseObject(input);
    } else {
        throw new TypeError('不支持的输入类型');
    }
}

// 场景 3: 类型守卫（TypeScript）
function isPlugin(obj) {
    return obj instanceof Plugin ||
           (obj !== null &&
            typeof obj === 'object' &&
            typeof obj.init === 'function' &&
            typeof obj.name === 'string');
}

// 场景 4: 防御性编程
function safeCall(obj, method, ...args) {
    if (obj &&
        typeof obj === 'object' &&
        typeof obj[method] === 'function') {
        return obj[method](...args);
    }
    return undefined;
}
```

---

## 总结与反思

下午六点，你重新审视了插件系统的类型检查。

你决定结合多种方法：

```javascript
class PluginRegistry {
    constructor() {
        this.plugins = [];
    }

    register(plugin) {
        // 多层次检查
        if (!this.isValidPlugin(plugin)) {
            throw new TypeError('无效的插件');
        }

        this.plugins.push(plugin);
        plugin.init();
        console.log(`插件 ${plugin.name} 注册成功`);
    }

    isValidPlugin(plugin) {
        // 1. 基本类型检查
        if (!plugin || typeof plugin !== 'object') {
            return false;
        }

        // 2. 必要属性检查（鸭子类型）
        if (typeof plugin.name !== 'string' || !plugin.name) {
            return false;
        }

        if (typeof plugin.init !== 'function') {
            return false;
        }

        // 3. 可选：instanceof 检查（如果有官方基类）
        // return plugin instanceof Plugin;

        return true;
    }
}

const registry = new PluginRegistry();

// 官方插件
registry.register(new AnalyticsPlugin());

// 自定义插件（鸭子类型）
registry.register({
    name: '自定义插件',
    init() {
        console.log('自定义插件初始化');
    }
});
```

"现在的检查既灵活又安全，" 你说，"能接受任何符合接口的对象，不管它的血统如何。"

---

## 知识总结

**规则 1: instanceof 检查原型链**

`instanceof` 检查对象的原型链上是否有构造函数的 `prototype`：

```javascript
obj instanceof Constructor
// 等价于
Constructor.prototype.isPrototypeOf(obj)
```

遍历原型链，查找 `Constructor.prototype`。

---

**规则 2: 基本类型返回 false**

基本类型不是对象，`instanceof` 总是返回 `false`：

```javascript
42 instanceof Number; // false
'hello' instanceof String; // false
true instanceof Boolean; // false
```

但包装对象可以：`new Number(42) instanceof Number; // true`

---

**规则 3: 原型修改影响判定**

替换构造函数的 `prototype` 会破坏已有实例的 `instanceof` 判定：

```javascript
function F() {}
const obj = new F();
console.log(obj instanceof F); // true

F.prototype = {}; // 替换 prototype
console.log(obj instanceof F); // false - 失效了
```

---

**规则 4: Symbol.hasInstance 自定义判定**

ES6 允许自定义 `instanceof` 行为：

```javascript
class MyClass {
    static [Symbol.hasInstance](obj) {
        return typeof obj.customMethod === 'function';
    }
}

{ customMethod() {} } instanceof MyClass; // true
```

---

**规则 5: 跨 frame 问题**

不同 frame 的内建构造函数是不同的对象：

```javascript
iframeArray instanceof Array; // false
iframeArray instanceof iframe.contentWindow.Array; // true

// 解决方案
Array.isArray(iframeArray); // true - 跨 frame 有效
```

---

**规则 6: 类型检查最佳实践**

根据场景选择检查方法：

| 场景 | 推荐方法 | 示例 |
|------|----------|------|
| 基本类型 | `typeof` | `typeof x === 'string'` |
| 数组 | `Array.isArray()` | `Array.isArray(arr)` |
| null | `=== null` | `x === null` |
| 继承检查 | `instanceof` | `obj instanceof Class` |
| 鸭子类型 | 属性/方法检查 | `typeof obj.method === 'function'` |
| 精确类型 | `toString.call()` | `Object.prototype.toString.call(x)` |

---

**事故档案编号**: PROTO-2024-1891
**影响范围**: instanceof, 类型检查, 原型链, Symbol.hasInstance
**根本原因**: 误解 instanceof 检查原型链而非类型，导致类型检查失效
**修复成本**: 低（使用正确的检查方法），需理解不同方法的适用场景

这是 JavaScript 世界第 91 次被记录的类型判定事故。`instanceof` 检查原型链而非类型，遍历对象的原型链查找构造函数的 `prototype`。基本类型不是对象，返回 `false`。替换 `prototype` 会破坏已有实例的判定。`Symbol.hasInstance` 可自定义判定逻辑，实现鸭子类型检查。跨 frame 时不同全局对象的构造函数不同，应用 `Array.isArray()` 等跨环境方法。类型检查应根据场景选择：基本类型用 `typeof`，数组用 `Array.isArray()`，鸭子类型检查属性/方法，继承关系用 `instanceof`（单一环境），精确类型用 `Object.prototype.toString.call()`。

---

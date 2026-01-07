《第 85 次记录: 无__proto__的孤立对象 —— 纯粹字典》

---

## 意外的属性污染

周三上午九点，你在实现一个配置管理系统时遇到了奇怪的问题。

```javascript
const config = {};

// 用户可以动态设置配置
function setConfig(key, value) {
    config[key] = value;
}

function getConfig(key) {
    return config[key];
}

// 正常使用
setConfig('apiUrl', 'https://api.example.com');
setConfig('timeout', 5000);

console.log(getConfig('apiUrl')); // 'https://api.example.com'
console.log(getConfig('timeout')); // 5000
```

"看起来没问题，" 你说，"但测试小林发现了一个安全漏洞。"

```javascript
// 恶意用户输入
setConfig('toString', 'hacked');
setConfig('hasOwnProperty', 'broken');

// 系统崩溃
console.log(config.toString()); // TypeError: config.toString is not a function

// 更严重的问题
for (let key in config) {
    console.log(key); // 遍历出 'toString', 'hasOwnProperty' 等原型方法
}
```

"为什么会污染到原型方法？" 你困惑不解。

---

## 原型污染的根源

上午十点，老张过来分析问题。

"你的 `config` 对象继承了 `Object.prototype`，" 老张说，"所以它有 `toString`、`hasOwnProperty` 等方法。"

```javascript
const obj = {};

console.log(Object.getPrototypeOf(obj) === Object.prototype); // true

// obj 继承了所有 Object.prototype 的方法
console.log(typeof obj.toString); // 'function'
console.log(typeof obj.hasOwnProperty); // 'function'
console.log(typeof obj.valueOf); // 'function'
```

"当你设置 `config.toString` 时，" 老张继续，"你覆盖了原型方法，但没有隔离开。"

```javascript
const config = {};

config.toString = 'hacked';

// 现在 toString 变成字符串了
console.log(typeof config.toString); // 'string'

// 尝试调用会出错
String(config); // TypeError: Cannot convert object to primitive value
```

"更危险的是原型污染攻击，" 老张警告：

```javascript
// 原型污染攻击示例
const userInput = JSON.parse('{"__proto__": {"isAdmin": true}}');
Object.assign({}, userInput);

// 现在所有对象都有 isAdmin 属性
const normalUser = {};
console.log(normalUser.isAdmin); // true - 被污染了！
```

---

## Object.create(null) 的解决方案

上午十一点，老张展示了解决方案。

"用 `Object.create(null)` 创建没有原型的对象，" 老张说，"它是真正的'纯粹'对象。"

```javascript
const pureConfig = Object.create(null);

// 检查原型
console.log(Object.getPrototypeOf(pureConfig)); // null

// 没有继承任何方法
console.log(pureConfig.toString); // undefined
console.log(pureConfig.hasOwnProperty); // undefined
console.log(pureConfig.valueOf); // undefined

// 但可以正常存储属性
pureConfig.apiUrl = 'https://api.example.com';
pureConfig.timeout = 5000;

console.log(pureConfig.apiUrl); // 'https://api.example.com'
```

"现在可以安全地设置任何属性名，" 你说：

```javascript
const safeConfig = Object.create(null);

// 即使是保留名称也没问题
safeConfig.toString = 'custom value';
safeConfig.hasOwnProperty = 'another value';
safeConfig.constructor = 'safe';

console.log(safeConfig.toString); // 'custom value' - 没有函数调用问题
console.log(typeof safeConfig.toString); // 'string'
```

---

## 纯粹对象的特性

上午十一点半，你开始测试纯粹对象的行为。

"没有原型的对象有什么特殊行为？" 你问。

"首先，它不会出现在 `for...in` 中，" 老张说：

```javascript
const normal = { own: 1 };
const pure = Object.create(null);
pure.own = 1;

// 普通对象
for (let key in normal) {
    console.log(key); // 'own'
    // 如果原型上有属性，也会遍历到
}

// 纯粹对象
for (let key in pure) {
    console.log(key); // 'own' - 只遍历自有属性
}
```

"其次，一些内建方法不能用了，" 老张演示：

```javascript
const pure = Object.create(null);

// 不能用实例方法
try {
    pure.hasOwnProperty('test'); // TypeError: pure.hasOwnProperty is not a function
} catch (e) {
    console.error(e.message);
}

// 要用 Object 的静态方法
console.log(Object.prototype.hasOwnProperty.call(pure, 'test')); // false
// 或者
console.log(Object.hasOwn(pure, 'test')); // false (ES2022)
```

"第三，类型判断会不同，" 老张说：

```javascript
const normal = {};
const pure = Object.create(null);

console.log(normal.toString()); // '[object Object]'
console.log(pure.toString); // undefined - 没有 toString 方法

// 要转字符串需要手动处理
console.log(String(pure)); // TypeError
console.log(Object.prototype.toString.call(pure)); // '[object Object]'
```

---

## 用作字典的优势

中午十二点，你开始重构配置系统。

"纯粹对象最适合用作字典(dictionary)或映射(map)，" 老张说：

```javascript
// config-manager.js - 安全的配置管理器
class ConfigManager {
    constructor() {
        this.config = Object.create(null);
    }

    set(key, value) {
        if (typeof key !== 'string') {
            throw new TypeError('配置键必须是字符串');
        }
        this.config[key] = value;
    }

    get(key) {
        return this.config[key];
    }

    has(key) {
        return Object.hasOwn(this.config, key);
    }

    delete(key) {
        delete this.config[key];
    }

    keys() {
        return Object.keys(this.config);
    }

    entries() {
        return Object.entries(this.config);
    }
}

const manager = new ConfigManager();

// 安全地设置任何键
manager.set('toString', 'safe');
manager.set('constructor', 'safe');
manager.set('__proto__', 'safe');

console.log(manager.get('toString')); // 'safe'
console.log(manager.keys()); // ['toString', 'constructor', '__proto__']
```

"完美，" 你说，"现在不用担心原型污染了。"

---

## 与 Map 的对比

下午两点，前端小王问了一个问题。

"既然 `Object.create(null)` 这么安全，" 小王说，"为什么还需要 `Map`？"

"各有优势，" 老张说：

```javascript
// Object.create(null) 的优势
const dict = Object.create(null);
dict['key1'] = 'value1';
dict['key2'] = 'value2';

// 优势 1: 语法简洁
console.log(dict.key1); // 直接访问
console.log(dict['key2']); // 也可以用括号

// 优势 2: JSON 序列化友好
const json = JSON.stringify(dict);
const restored = JSON.parse(json); // 可以直接恢复

// Map 的优势
const map = new Map();
map.set('key1', 'value1');
map.set('key2', 'value2');

// 优势 1: 键可以是任何类型
const objKey = { id: 1 };
map.set(objKey, 'value'); // 对象作为键
map.set(123, 'value'); // 数字作为键

dict[objKey] = 'value'; // 会转成字符串 '[object Object]'
dict[123] = 'value'; // 会转成字符串 '123'

// 优势 2: 有 size 属性
console.log(map.size); // 3
console.log(Object.keys(dict).length); // 需要计算

// 优势 3: 迭代更方便
for (let [key, value] of map) {
    console.log(key, value);
}

// 优势 4: 性能更好(大量键值对时)
```

"所以选择哪个？" 小王问。

"看场景，" 老张总结：

| 场景 | 推荐 | 理由 |
|------|------|------|
| 简单键值存储 | Object.create(null) | 语法简单，JSON 友好 |
| 需要非字符串键 | Map | 支持任何类型的键 |
| 大量数据(>1000 条) | Map | 性能更好 |
| 需要频繁增删 | Map | delete 操作更快 |
| 需要序列化 | Object.create(null) | JSON 直接支持 |

---

## 原型污染防御

下午三点，老张讲解了原型污染攻击的防御策略。

"原型污染是一种严重的安全漏洞，" 老张警告：

```javascript
// 危险的代码
function merge(target, source) {
    for (let key in source) {
        target[key] = source[key]; // 危险！
    }
}

const obj = {};
const malicious = JSON.parse('{"__proto__": {"isAdmin": true}}');

merge(obj, malicious);

// 污染了所有对象
console.log({}.isAdmin); // true - 全局污染！
```

"如何防御？" 你问。

"方法 1: 使用 `Object.create(null)`，" 老张说：

```javascript
function safeMerge(target, source) {
    const safeTarget = Object.create(null);
    
    for (let key in source) {
        if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
            continue; // 跳过危险键
        }
        safeTarget[key] = source[key];
    }
    
    return safeTarget;
}

const result = safeMerge({}, malicious);
console.log({}.isAdmin); // undefined - 安全
```

"方法 2: 使用 `Object.hasOwn` 检查，" 老张继续：

```javascript
function deepMerge(target, source) {
    for (let key in source) {
        if (!Object.hasOwn(source, key)) {
            continue; // 跳过继承属性
        }
        
        if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
            continue; // 跳过危险键
        }
        
        if (typeof source[key] === 'object' && source[key] !== null) {
            target[key] = deepMerge({}, source[key]); // 递归合并
        } else {
            target[key] = source[key];
        }
    }
    
    return target;
}
```

"方法 3: 使用 `Object.freeze` 冻结原型，" 老张说：

```javascript
// 冻结关键原型
Object.freeze(Object.prototype);
Object.freeze(Array.prototype);
Object.freeze(Function.prototype);

// 现在原型污染攻击失效
const obj = {};
obj.__proto__.isAdmin = true; // 静默失败

console.log({}.isAdmin); // undefined - 原型被保护
```

---

## 性能与兼容性

下午四点，测试小林提出了性能问题。

"纯粹对象的性能如何？" 小林问。

你做了基准测试：

```javascript
// 性能测试
console.time('普通对象');
const normal = {};
for (let i = 0; i < 1000000; i++) {
    normal[`key${i}`] = i;
}
console.timeEnd('普通对象'); // ~150ms

console.time('纯粹对象');
const pure = Object.create(null);
for (let i = 0; i < 1000000; i++) {
    pure[`key${i}`] = i;
}
console.timeEnd('纯粹对象'); // ~140ms

console.time('Map');
const map = new Map();
for (let i = 0; i < 1000000; i++) {
    map.set(`key${i}`, i);
}
console.timeEnd('Map'); // ~180ms
```

"纯粹对象性能最好，" 你说，"因为没有原型链查找开销。"

"但要注意兼容性，" 老张提醒：

```javascript
// 一些 API 需要正常对象
const pure = Object.create(null);
pure.name = '张三';

// Object.keys 可以用
console.log(Object.keys(pure)); // ['name']

// JSON.stringify 可以用
console.log(JSON.stringify(pure)); // '{"name":"张三"}'

// 但一些库可能假设对象有原型
function thirdPartyFunction(obj) {
    return obj.toString(); // 假设有 toString 方法
}

try {
    thirdPartyFunction(pure); // TypeError
} catch (e) {
    console.error('第三方库不兼容纯粹对象');
}
```

---

## 总结与反思

下午五点，你整理了无原型对象的知识。

**核心概念：**
- `Object.create(null)` 创建没有原型的纯粹对象
- 纯粹对象没有继承任何方法，真正的'空白'对象
- 适合用作字典、配置存储、防止原型污染

**常见陷阱：**
- 不能使用实例方法如 `hasOwnProperty`、`toString`
- 需要用 `Object` 的静态方法代替
- 第三方库可能不兼容

**最佳实践：**
- 用作字典或映射时使用 `Object.create(null)`
- 需要非字符串键或频繁操作时使用 `Map`
- 防御原型污染攻击：过滤危险键、使用 `Object.hasOwn`、冻结原型
- 注意第三方库的兼容性

---

## 知识总结

**规则 1: Object.create(null) 的特性**

`Object.create(null)` 创建没有原型链的纯粹对象：

```javascript
const pure = Object.create(null);
console.log(Object.getPrototypeOf(pure)); // null
console.log(pure.toString); // undefined - 没有继承方法
```

纯粹对象没有任何继承属性和方法，是真正的'空白'对象。

---

**规则 2: 纯粹对象的安全性优势**

纯粹对象防止原型污染，可以安全地使用任何属性名：

```javascript
const dict = Object.create(null);
dict.toString = 'safe'; // 不会覆盖原型方法
dict.__proto__ = 'safe'; // 不会污染原型链
dict.constructor = 'safe'; // 完全安全
```

这使得纯粹对象适合存储用户输入或不可信数据。

---

**规则 3: 实例方法不可用**

纯粹对象没有继承 `Object.prototype`，因此实例方法不可用：

```javascript
const pure = Object.create(null);
pure.hasOwnProperty('key'); // TypeError

// 必须使用静态方法
Object.prototype.hasOwnProperty.call(pure, 'key'); // 正确
Object.hasOwn(pure, 'key'); // ES2022+ 推荐
```

需要用 `Object` 的静态方法代替实例方法。

---

**规则 4: Object.create(null) vs Map**

选择依据场景需求：

| 特性 | Object.create(null) | Map |
|------|---------------------|-----|
| 键类型 | 仅字符串/Symbol | 任何类型 |
| 语法 | obj.key, obj['key'] | map.set(key, val) |
| JSON | 原生支持 | 需手动转换 |
| 性能(小规模) | 更快 | 稍慢 |
| 性能(大规模>1000) | 稍慢 | 更快 |
| size 属性 | 无(需 Object.keys().length) | 有(map.size) |

简单字典用 `Object.create(null)`，复杂场景用 `Map`。

---

**规则 5: 原型污染防御策略**

防止原型污染攻击的三种方法：

```javascript
// 方法1: 使用纯粹对象
const safe = Object.create(null);

// 方法2: 过滤危险键
function safeMerge(target, source) {
    for (let key in source) {
        if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
            continue;
        }
        target[key] = source[key];
    }
}

// 方法3: 冻结原型
Object.freeze(Object.prototype);
```

三种方法可以组合使用提供纵深防御。

---

**规则 6: 兼容性与性能考量**

纯粹对象性能优势与兼容性限制：

**性能优势**：
- 无原型链查找开销，属性访问更快
- 内存占用略少(无原型链接)

**兼容性限制**：
- 第三方库可能假设对象有 `toString`、`hasOwnProperty` 等方法
- 一些 API 可能不兼容(如某些 ORM、序列化库)
- 需要额外处理类型转换和方法调用

使用前评估第三方依赖的兼容性。

---

**事故档案编号**: PROTO-2024-1885  
**影响范围**: Object.create(null), 原型污染, 字典对象, 安全防御  
**根本原因**: 普通对象继承 Object.prototype 导致属性名冲突和原型污染风险  
**修复成本**: 低（使用 Object.create(null)），需注意兼容性和方法调用

这是 JavaScript 世界第 85 次被记录的原型系统事故。`Object.create(null)` 创建没有原型的纯粹对象，没有任何继承属性和方法。纯粹对象防止原型污染，可以安全使用任何属性名（包括 `toString`、`__proto__`、`constructor`）。实例方法不可用，需使用 `Object` 静态方法（如 `Object.hasOwn()`）。适合用作字典、配置存储、防止用户输入污染。与 `Map` 对比：纯粹对象语法简洁、JSON 友好，但只支持字符串键；`Map` 支持任何类型键、有 `size` 属性、大规模数据性能更好。原型污染防御策略：使用纯粹对象、过滤危险键、冻结原型。性能更优但需注意第三方库兼容性。

---

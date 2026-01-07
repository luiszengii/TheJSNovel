《第 79 次记录: 属性标志 —— 隐藏的权限系统》

---

## 无法修改的属性

周二上午十点，你正在为公司的权限系统添加新功能。产品经理小刘刚刚提了一个需求: "用户对象需要有一个 `role` 属性，但这个属性一旦设置就不能被修改，防止权限被篡改。"

"没问题，" 你想，"JavaScript 对象很灵活，应该很容易实现。"

你打开代码编辑器，写下了第一版实现:

```javascript
// user-system.js - 用户权限系统
class User {
    constructor(name, role) {
        this.name = name;
        this.role = role;
    }
}

const user = new User('张三', 'admin');
console.log(user.role); // 'admin'
```

"现在怎么让 `role` 不能被修改?" 你思考着。你尝试了最直接的想法:

```javascript
user.role = 'guest'; // 尝试修改
console.log(user.role); // 还是 'guest' - 修改成功了!
```

"这样不行，" 你皱眉，"任何人都能修改 `role` 属性，权限系统就失效了。"

你想起可以用 Object.freeze()，但那会冻结整个对象，连 `name` 都不能改了。你需要更精确的控制 —— 只让 `role` 不可修改，其他属性保持正常。

---

## 老张的提示

下午两点，你去请教技术负责人老张。

"遇到什么问题?" 老张问。

"我想让对象的某个属性不能被修改，但其他属性可以，" 你说，"有什么办法吗?"

老张笑了笑: "你知道 JavaScript 的属性不仅仅有值吗?"

"不仅仅有值?" 你有点困惑。

"对，" 老张打开浏览器控制台，"每个属性除了值之外，还有三个隐藏的标志: `writable`、`enumerable`、`configurable`。这些标志控制着属性的行为。"

他敲了一段代码:

```javascript
const obj = { name: '张三' };

// 查看属性的完整描述符
const descriptor = Object.getOwnPropertyDescriptor(obj, 'name');
console.log(descriptor);
```

控制台输出:

```javascript
{
    value: '张三',
    writable: true,      // 可写
    enumerable: true,    // 可枚举
    configurable: true   // 可配置
}
```

"看到了吗?" 老张指着输出，"普通属性默认所有标志都是 `true`。但你可以用 `Object.defineProperty()` 精确控制这些标志。"

---

## 属性标志详解

下午两点半，老张给你详细讲解这三个标志。

"第一个是 `writable`，" 老张说，"控制属性能否被重新赋值。"

```javascript
const user = {};

// 定义一个不可写的属性
Object.defineProperty(user, 'role', {
    value: 'admin',
    writable: false,      // 不可写
    enumerable: true,
    configurable: true
});

console.log(user.role); // 'admin'

// 尝试修改
user.role = 'guest';
console.log(user.role); // 还是 'admin' - 修改失败!

// 严格模式下会报错
'use strict';
user.role = 'guest'; // TypeError: Cannot assign to read only property
```

"太好了!" 你说，"这正是我需要的。那 `enumerable` 是什么?"

"控制属性是否在 `for...in` 循环和 `Object.keys()` 中出现，" 老张解释:

```javascript
const user = {
    name: '张三',
    age: 25
};

// 添加一个不可枚举的属性
Object.defineProperty(user, 'password', {
    value: 'secret123',
    enumerable: false  // 不可枚举
});

console.log(user.password); // 'secret123' - 可以访问

// 但不会在遍历中出现
for (let key in user) {
    console.log(key); // 只输出 'name' 和 'age'
}

console.log(Object.keys(user)); // ['name', 'age'] - 没有 'password'
```

"所以敏感信息可以用不可枚举属性隐藏起来?" 你恍然大悟。

"对，但要注意，这不是真正的安全措施，" 老张提醒，"只是让属性不那么显眼而已。真正的敏感数据应该用其他方式保护。"

---

## configurable 的影响

下午三点，老张继续讲解第三个标志。

"`configurable` 是最特殊的一个，" 老张说，"它控制两件事: 属性能否被删除，以及属性的标志能否被修改。"

```javascript
const obj = {};

Object.defineProperty(obj, 'id', {
    value: 1001,
    configurable: false  // 不可配置
});

// 尝试删除
delete obj.id;
console.log(obj.id); // 1001 - 删除失败

// 尝试修改标志
Object.defineProperty(obj, 'id', {
    writable: true  // TypeError: Cannot redefine property
});
```

"一旦 `configurable` 设为 `false`，就是一条单行道，" 老张强调，"无法再改回 `true`，也无法修改其他标志。这是一个不可逆的操作。"

"那岂不是很危险?" 你说，"万一设错了就没法改了。"

"所以要慎用，" 老张点头，"但对于那些真正需要保护的核心属性，这是很有用的。比如对象的 `id` 或 `type` 这种不应该被修改或删除的属性。"

你突然想到一个问题: "如果 `configurable: false`，但 `writable: true`，还能修改属性值吗?"

"好问题!" 老张在控制台演示:

```javascript
const obj = {};

Object.defineProperty(obj, 'count', {
    value: 0,
    writable: true,
    configurable: false
});

obj.count = 10; // 可以修改值
console.log(obj.count); // 10

// 但不能修改标志
Object.defineProperty(obj, 'count', {
    enumerable: false  // TypeError: Cannot redefine property
});

// 也不能删除
delete obj.count; // 无效
```

"所以 `configurable: false` 锁定的是属性的'元数据'，不是值本身，" 你总结。

---

## 实际应用

下午四点，你开始重构用户系统，应用学到的知识。

"现在我可以实现产品经理要的功能了，" 你说着写下新代码:

```javascript
// user-system-improved.js - 改进的用户系统
class User {
    constructor(name, role) {
        // 可修改的普通属性
        this.name = name;

        // 不可修改的角色属性
        Object.defineProperty(this, 'role', {
            value: role,
            writable: false,       // 不可写
            enumerable: true,      // 可枚举
            configurable: false    // 不可配置(无法删除)
        });

        // 隐藏的内部 ID
        Object.defineProperty(this, '_internalId', {
            value: Math.random().toString(36),
            writable: false,
            enumerable: false,     // 不可枚举
            configurable: false
        });
    }
}

const user = new User('张三', 'admin');

// 可以修改 name
user.name = '李四';
console.log(user.name); // '李四'

// 无法修改 role
user.role = 'guest';
console.log(user.role); // 'admin' - 修改失败

// 无法删除 role
delete user.role;
console.log(user.role); // 'admin' - 删除失败

// _internalId 不会在遍历中出现
console.log(Object.keys(user)); // ['name', 'role']

// 但可以直接访问
console.log(user._internalId); // 'k9x2m...'
```

"完美!" 你说，"现在 `role` 一旦设置就无法被修改或删除，满足安全需求了。"

---

## 批量定义属性

下午五点，老张又教了你一个技巧。

"如果要定义多个属性，一个一个调用 `defineProperty` 太麻烦，" 老张说，"可以用 `Object.defineProperties()`。"

```javascript
const config = {};

Object.defineProperties(config, {
    apiUrl: {
        value: 'https://api.example.com',
        writable: false,
        configurable: false
    },
    timeout: {
        value: 5000,
        writable: true,     // 可以调整超时时间
        configurable: false
    },
    version: {
        value: '1.0.0',
        writable: false,
        enumerable: false,  // 版本号不显示在遍历中
        configurable: false
    }
});

console.log(config.apiUrl); // 'https://api.example.com'
config.apiUrl = 'http://fake.com'; // 修改无效
console.log(config.apiUrl); // 还是原来的值

config.timeout = 10000; // 可以修改
console.log(config.timeout); // 10000

console.log(Object.keys(config)); // ['apiUrl', 'timeout'] - 没有 version
```

"这样配置对象就很安全了，" 你说，"核心配置无法被篡改。"

---

## 复制属性的陷阱

下午五点半，测试小林发现了一个问题。

"你的用户对象无法被正确复制，" 小林说，"我用 `Object.assign()` 复制时，属性标志都丢失了。"

你测试了一下:

```javascript
const user1 = new User('张三', 'admin');

// 尝试复制
const user2 = Object.assign({}, user1);

// role 在 user2 中变成了可修改的!
user2.role = 'guest';
console.log(user2.role); // 'guest' - 修改成功了

// 查看属性描述符
console.log(Object.getOwnPropertyDescriptor(user2, 'role'));
// { value: 'admin', writable: true, enumerable: true, configurable: true }
```

"怎么会这样?" 你惊讶。

"因为 `Object.assign()` 只复制属性的值，不复制标志，" 老张解释，"如果要保留属性标志，需要手动复制每个属性的描述符。"

```javascript
function cloneWithDescriptors(source) {
    const target = {};

    // 获取所有属性名(包括不可枚举的)
    const keys = Object.getOwnPropertyNames(source);

    keys.forEach(key => {
        // 获取属性描述符
        const descriptor = Object.getOwnPropertyDescriptor(source, key);

        // 用描述符定义新属性
        Object.defineProperty(target, key, descriptor);
    });

    return target;
}

const user1 = new User('张三', 'admin');
const user2 = cloneWithDescriptors(user1);

// 现在 role 保持不可修改
user2.role = 'guest';
console.log(user2.role); // 'admin' - 修改失败
```

"明白了，" 你说，"属性标志是对象的'隐藏信息'，普通复制方法会丢失这些信息。"

---

## 生产环境部署

下午六点，你完成了新的权限系统，准备部署到生产环境。

"等一下，" 老张说，"在生产环境中，属性描述符还有一个重要用途 —— 冻结对象。"

"不是有 `Object.freeze()` 吗?" 你问。

"对，但你知道 `Object.freeze()` 的原理吗?" 老张问，"它其实就是把所有属性的 `writable` 和 `configurable` 都设为 `false`。"

```javascript
const config = {
    apiUrl: 'https://api.example.com',
    timeout: 5000
};

// 冻结对象
Object.freeze(config);

// 等价于
Object.defineProperties(config, {
    apiUrl: {
        writable: false,
        configurable: false
    },
    timeout: {
        writable: false,
        configurable: false
    }
});
```

"但 `freeze` 是浅冻结，" 老张提醒，"嵌套对象不会被冻结。"

```javascript
const config = {
    database: {
        host: 'localhost',
        port: 5432
    }
};

Object.freeze(config);

// 外层属性不能修改
config.database = {}; // 无效

// 但内层属性可以修改!
config.database.host = 'evil.com';
console.log(config.database.host); // 'evil.com' - 修改成功
```

"所以要深度冻结，需要递归处理，" 你说。

"对，" 老张说，"或者在定义每个嵌套对象时，就用 `defineProperty` 正确设置标志。"

---

## 总结与反思

晚上七点，你在笔记本上总结今天学到的知识。

**属性标志的核心概念:**
- 每个属性都有四个特性: `value`、`writable`、`enumerable`、`configurable`
- `writable: false` - 属性不可修改
- `enumerable: false` - 属性不在遍历中出现
- `configurable: false` - 属性不可删除，标志不可改变(不可逆)

**常见陷阱:**
- `Object.assign()` 和展开运算符 `...` 会丢失属性标志
- `configurable: false` 是单行道，无法恢复
- `Object.freeze()` 是浅冻结，不影响嵌套对象
- 严格模式下，违反属性标志会抛出错误; 非严格模式下静默失败

你保存了文档，明天准备给团队做一次分享，讲解属性标志在权限系统、配置管理、对象保护中的应用。

---

## 知识总结

**规则 1: 属性描述符的四个特性**

每个对象属性都有四个特性: `value`(值)、`writable`(可写)、`enumerable`(可枚举)、`configurable`(可配置)。使用 `Object.getOwnPropertyDescriptor(obj, 'key')` 查看，`Object.defineProperty()` 定义。

---

**规则 2: writable 控制属性可写性**

`writable: false` 使属性变为只读，无法通过赋值修改:

```javascript
Object.defineProperty(obj, 'id', {
    value: 1001,
    writable: false
});

obj.id = 2000; // 非严格模式: 静默失败
// 严格模式: TypeError
```

只读属性只能通过 `defineProperty` 修改(前提是 `configurable: true`)。

---

**规则 3: enumerable 控制属性可见性**

`enumerable: false` 使属性不出现在 `for...in`、`Object.keys()`、`Object.values()`、`Object.entries()` 中:

```javascript
Object.defineProperty(obj, '_internal', {
    value: 'secret',
    enumerable: false
});

Object.keys(obj); // 不包含 '_internal'
```

但仍可通过 `obj._internal` 直接访问，也会被 `Object.getOwnPropertyNames()` 列出。

---

**规则 4: configurable 的双重作用**

`configurable: false` 禁止删除属性和修改属性标志(除了 `writable: true → false`):

```javascript
Object.defineProperty(obj, 'id', {
    value: 1001,
    configurable: false
});

delete obj.id; // 无效
Object.defineProperty(obj, 'id', { enumerable: false }); // TypeError
```

这是**不可逆操作** —— 一旦设为 `false` 无法改回 `true`。

---

**规则 5: 属性复制与标志丢失**

| 方法 | 是否保留标志 | 说明 |
|------|------------|------|
| `Object.assign()` | ❌ | 只复制值和 `enumerable: true` 的属性 |
| `{ ...obj }` | ❌ | 同 `Object.assign()`  |
| `JSON.parse(JSON.stringify())` | ❌ | 只保留可序列化的值 |
| 手动复制描述符 | ✅ | 用 `getOwnPropertyDescriptor` + `defineProperty` |

要保留标志，必须手动复制每个属性的描述符。

---

**规则 6: Object.freeze() 的实现原理**

`Object.freeze(obj)` 等价于对所有属性设置 `writable: false` 和 `configurable: false`:

```javascript
Object.freeze(obj);
// 等价于
for (let key of Object.keys(obj)) {
    Object.defineProperty(obj, key, {
        writable: false,
        configurable: false
    });
}
```

注意: 这是**浅冻结** —— 嵌套对象不受影响，需递归冻结才能深度保护。

---

**事故档案编号**: PROTO-2024-1879
**影响范围**: 属性标志, writable, enumerable, configurable, Object.defineProperty, Object.freeze
**根本原因**: 不了解属性标志系统，导致权限控制失效或对象保护不当
**修复成本**: 低(使用 defineProperty 正确设置标志), 需理解标志语义和交互规则

这是 JavaScript 世界第 79 次被记录的属性系统事故。JavaScript 属性除了值之外还有三个标志: `writable`(可写性)、`enumerable`(可枚举性)、`configurable`(可配置性)。`writable: false` 使属性只读，`enumerable: false` 使属性在遍历中隐藏，`configurable: false` 禁止删除和修改标志(不可逆)。普通赋值和 `Object.assign()` 创建的属性默认所有标志为 `true`，但 `defineProperty` 默认为 `false`。`Object.freeze()` 本质是设置所有属性的 `writable` 和 `configurable` 为 `false`，但这是浅冻结。属性复制时标志会丢失，需手动复制描述符。理解属性标志是实现对象保护、权限控制、配置管理的基础。

---

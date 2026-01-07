《第53次记录: 属性描述符之秘 —— 不可变配置的幽灵修改》

---

## 谜题现场

周二下午两点, 你坐在办公桌前, 喝着茶, 翻看着用户反馈。这是个奇怪的bug报告:"应用配置总是被莫名其妙地修改, 明明代码里设置成了只读, 但运行时还是能改。"

你挑了挑眉毛。这听起来不像是普通的bug, 更像是个谜题。你一直喜欢这种技术侦探工作——没有紧迫的deadline, 没有用户投诉的压力, 只是纯粹的好奇心驱使你去找出真相。

你打开项目, 找到配置管理模块。代码是三个月前写的, 当时为了防止配置被意外修改, 你特意设计成了"不可变"模式:

前端同事小陈走过来:"在看配置bug? 我昨天也遇到了, 很奇怪。你看这个config对象, 我明明设置成了常量, 但在某些情况下还是能改。"

"我也在查这个。"你说,"这像是个侦探案件, 得一条线索一条线索地查。"

小陈笑了:"那你这个夏洛克·福尔摩斯, 能破案吗?"

"试试看。"你打开DevTools, 开始你的调查之旅。

阳光从窗外斜射进来, 办公室里很安静。你喜欢这种状态——没有人催促, 可以慢慢地抽丝剥茧, 享受解谜的过程。这就像在读一本推理小说, 每一个线索都让你更接近真相。

你在纸上写下第一条线索:"config对象有时可修改, 有时不可修改。什么情况下可以修改?"

---

## 线索追踪

下午两点半, 你开始系统地收集证据。首先, 复现问题:

```javascript
// 线索1: 配置对象的定义
const config = {
    apiUrl: 'https://api. example. com',
    timeout: 5000,
    debug: false
};

// 尝试修改
config. timeout = 10000;
console. log(config. timeout); // 10000 - 修改成功了!
```

"嗯, 普通对象确实可以修改。"你自言自语, 在笔记上记录。

然后你找到了同事之前写的"防护"代码:

```javascript
// 线索2: 同事尝试的保护措施
const protectedConfig = Object. freeze({
    apiUrl: 'https://api. example. com',
    timeout: 5000
});

protectedConfig. timeout = 10000; // 严格模式下报错, 非严格模式静默失败
console. log(protectedConfig. timeout); // 5000 - 修改失败
```

"freeze确实能保护, 但用户说有些配置还是被改了。"你皱起眉头, 继续查找。

下午三点, 你发现了关键线索。在一个工具函数里, 有人用了`Object. defineProperty`:

```javascript
// 线索3: 神秘的defineProperty调用
const settings = {};

Object. defineProperty(settings, 'version', {
    value: '1. 0. 0',
    writable: false  // 不可写
});

settings. version = '2. 0. 0'; // 尝试修改
console. log(settings. version); // '1. 0. 0' - 修改失败!
```

"有意思!"你眼前一亮。你打开Chrome DevTools, 查看对象的属性描述符:

```javascript
Object. getOwnPropertyDescriptor(settings, 'version');
// {
//   value: '1. 0. 0',
//   writable: false,
//   enumerable: false,
//   configurable: false
// }
```

"原来属性有这么多隐藏的特性!"你兴奋地记录下来。

你继续测试, 发现了更多有趣的事实:

```javascript
// 线索4: writable控制是否可修改值
const obj1 = {};
Object. defineProperty(obj1, 'name', {
    value: 'Alice',
    writable: false
});
obj1. name = 'Bob'; // 静默失败
console. log(obj1. name); // 'Alice'

// 线索5: configurable控制是否可删除/重新定义
const obj2 = {};
Object. defineProperty(obj2, 'age', {
    value: 25,
    configurable: false
});
delete obj2. age; // 删除失败
console. log(obj2. age); // 25
```

"所以`writable`控制能不能改值,`configurable`控制能不能删除属性!"你在笔记上画了个图。

下午三点半, 你找到了bug的根源。原来, 项目里有两种配置方式混用了:

```javascript
// 方式1: 普通赋值(可修改)
config. debug = true;

// 方式2: defineProperty(不可修改)
Object. defineProperty(config, 'apiUrl', {
    value: 'https://api. example. com',
    writable: false
});

// 结果: debug可以改, apiUrl不能改
config. debug = false;  // ✓ 成功
config. apiUrl = 'xxx'; // ✗ 失败
```

"原来如此!"你像福尔摩斯破案一样满意地点点头,"不同的属性有不同的描述符设置, 所以表现不一样。"

---

## 真相大白

下午四点, 你整理出了完整的证据链, 向小陈展示你的发现:

**证据A: 属性描述符的四个特性**

```javascript
const obj = {};

// 普通赋值: 所有描述符都是true
obj. name = 'Alice';
Object. getOwnPropertyDescriptor(obj, 'name');
// {
//   value: 'Alice',
//   writable: true,      // 可修改值
//   enumerable: true,    // 可枚举(for... in能看到)
//   configurable: true   // 可删除/重新定义
// }

// defineProperty: 默认都是false!
Object. defineProperty(obj, 'age', {
    value: 25
});
Object. getOwnPropertyDescriptor(obj, 'age');
// {
//   value: 25,
//   writable: false,     // 不可修改!
//   enumerable: false,   // 不可枚举!
//   configurable: false  // 不可删除!
// }
```

**证据B: writable的作用**

```javascript
const user = {};

// writable: true - 可修改
Object. defineProperty(user, 'name', {
    value: 'Alice',
    writable: true
});
user. name = 'Bob';     // ✓ 成功
console. log(user. name); // 'Bob'

// writable: false - 不可修改
Object. defineProperty(user, 'id', {
    value: 123,
    writable: false
});
user. id = 456;         // ✗ 静默失败(严格模式报错)
console. log(user. id);  // 123
```

**证据C: enumerable的作用**

```javascript
const product = {};

Object. defineProperty(product, 'name', {
    value: 'iPhone',
    enumerable: true  // 可枚举
});

Object. defineProperty(product, 'internalId', {
    value: 'ABC123',
    enumerable: false // 不可枚举
});

for (let key in product) {
    console. log(key); // 只输出'name', 看不到'internalId'
}

Object. keys(product); // ['name'] - 看不到internalId
```

**证据D: configurable的作用**

```javascript
const settings = {};

// configurable: true - 可删除/重新定义
Object. defineProperty(settings, 'theme', {
    value: 'dark',
    configurable: true
});
delete settings. theme; // ✓ 成功删除

// configurable: false - 不可删除/重新定义
Object. defineProperty(settings, 'version', {
    value: '1. 0',
    configurable: false
});
delete settings. version; // ✗ 删除失败
Object. defineProperty(settings, 'version', { value: '2. 0' }); // ✗ 报错!
```

小陈看完, 恍然大悟:"所以项目里的bug是因为有些属性用普通赋值, 有些用defineProperty, 描述符不一致导致的!"

"正是如此!"你说,"解决方案就是统一用defineProperty, 明确设置每个描述符。"

---

## 知识档案

**规则 1: 属性描述符的四大特性**

每个对象属性都有四个描述符特性:

```javascript
{
  value: 值,
  writable: 是否可修改值,
  enumerable: 是否可枚举,
  configurable: 是否可删除/重新定义
}
```

---

**规则 2: 普通赋值 vs defineProperty**

```javascript
const obj = {};

// 普通赋值: 所有描述符默认true
obj. name = 'Alice';
// 等价于:
Object. defineProperty(obj, 'name', {
    value: 'Alice',
    writable: true,
    enumerable: true,
    configurable: true
});

// defineProperty: 所有描述符默认false!
Object. defineProperty(obj, 'age', {
    value: 25
    // writable: false (默认)
    // enumerable: false (默认)
    // configurable: false (默认)
});
```

---

**规则 3: writable控制值的修改**

```javascript
const user = {};

Object. defineProperty(user, 'id', {
    value: 123,
    writable: false
});

user. id = 456; // 非严格模式: 静默失败, 严格模式: TypeError

// 但可以用defineProperty强制修改(如果configurable为true)
Object. defineProperty(user, 'id', {
    value: 456,
    writable: false
}); // 成功修改
```

---

**规则 4: enumerable控制属性可见性**

```javascript
const obj = {};

Object. defineProperty(obj, 'public', {
    value: 1,
    enumerable: true
});

Object. defineProperty(obj, 'private', {
    value: 2,
    enumerable: false
});

for (let key in obj) {
    console. log(key); // 只输出'public'
}

Object. keys(obj);           // ['public']
Object. getOwnPropertyNames(obj); // ['public', 'private']
JSON. stringify(obj);        // {"public": 1} - private不会序列化
```

---

**规则 5: configurable控制属性重新定义**

```javascript
const obj = {};

// configurable: true - 灵活
Object. defineProperty(obj, 'flexible', {
    value: 1,
    writable: false,
    configurable: true
});

delete obj. flexible; // ✓ 可删除

Object. defineProperty(obj, 'flexible', {
    value: 2,
    writable: true // ✓ 可修改描述符
});

// configurable: false - 锁定
Object. defineProperty(obj, 'locked', {
    value: 1,
    configurable: false
});

delete obj. locked; // ✗ 不可删除
Object. defineProperty(obj, 'locked', {
    value: 2 // ✗ TypeError: 不能重新定义
});
```

**例外**: 即使`configurable: false`, 也可以将`writable`从`true`改为`false`(单向修改)。

---

**规则 6: 实用场景**

```javascript
/* 场景1: 常量配置 */
const CONFIG = {};
Object. defineProperty(CONFIG, 'API_URL', {
    value: 'https://api. example. com',
    writable: false,
    enumerable: true,
    configurable: false
});

/* 场景2: 隐藏内部属性 */
class User {
    constructor(name) {
        this. name = name;
        Object. defineProperty(this, '_internalId', {
            value: Math. random(),
            enumerable: false, // for... in看不到
            writable: false
        });
    }
}

/* 场景3: 创建真正的常量 */
function createConstant(obj, key, value) {
    Object. defineProperty(obj, key, {
        value: value,
        writable: false,
        enumerable: true,
        configurable: false
    });
}

const app = {};
createConstant(app, 'VERSION', '1. 0. 0');
app. VERSION = '2. 0. 0'; // 无效
delete app. VERSION;     // 无效
```

---

**事故档案编号**: OBJ-2024-1753
**影响范围**: 配置管理, 对象属性控制
**根本原因**: 不理解属性描述符机制, 混用普通赋值和defineProperty
**修复成本**: 低(统一属性定义方式, 明确设置描述符)

这是JavaScript世界第53次被记录的属性描述符谜案。每个对象属性都有四个隐藏的描述符特性: value(值)、writable(可写)、enumerable(可枚举)、configurable(可配置)。普通赋值默认所有描述符为true, 而`Object. defineProperty`默认所有描述符为false。理解这些特性, 就能精确控制对象属性的行为, 创建真正的不可变配置, 隐藏内部实现细节, 实现更安全的封装。

---

《第55次记录: 对象密封事故 —— 安全需求的过度防护》

---

## 代码审查

周四下午三点, 会议室里, Code Review正在进行。

"这个PR是关于配置管理的安全加固。"前端负责人老张打开投影, 展示代码,"安全团队上周提出要求, 所有敏感配置对象要设为'不可变', 防止被意外修改。"

你坐在会议桌旁, 翻看着PR的改动。代码不多, 主要是给几个配置对象加上了`Object. freeze()`:

后端同事小李举手提问:"我看到测试环境的日志里有些warning, 说是'不能添加属性'。这个freeze是不是限制太严格了?"

老张点点头:"确实, 我也在想这个问题。freeze会让对象完全不可变, 但有些场景我们还是需要修改的, 比如运行时的配置更新。"

"那有没有其他方案?"测试同事小王问,"比如只是防止删除属性, 但允许修改现有属性的值?"

"好问题。"你说,"JavaScript其实提供了三种不同程度的'锁定'对象的方法: preventExtensions、seal、freeze。我们需要根据实际需求选择合适的。"

会议室里安静下来, 大家都看着你。窗外有施工的声音, 但会议室里的气氛很专注, 这是一次高质量的技术讨论。

"让我们一起分析一下这三种方法的区别。"你走到白板前, 拿起马克笔,"首先, 我们的需求到底是什么?"

老张说:"安全团队的要求是: 1) 不能删除现有属性, 2) 不能添加新属性, 3) 敏感配置不能被随意修改。"

"好, 那我们看看每种方法能实现哪些需求。"你开始在白板上画表格。

---

## 方案对比

下午三点十分, 你在白板上写下第一个方法:

"`Object. preventExtensions()` - 最宽松的限制。"你一边写一边解释:

```javascript
// 方法1: preventExtensions - 不能添加, 但能修改和删除
const config = {
    apiUrl: 'https://api. example. com',
    timeout: 5000
};

Object. preventExtensions(config);

config. timeout = 10000;   // ✓ 可以修改
delete config. timeout;    // ✓ 可以删除
config. newProp = 'value'; // ✗ 不能添加新属性

console. log(Object. isExtensible(config)); // false
```

小李看着代码:"所以这个只防止添加新属性, 不防止修改和删除?"

"对。"你点点头,"接下来看`Object. seal()`:"

```javascript
// 方法2: seal - 不能添加或删除, 但能修改
const config = {
    apiUrl: 'https://api. example. com',
    timeout: 5000
};

Object. seal(config);

config. timeout = 10000;   // ✓ 可以修改值
delete config. timeout;    // ✗ 不能删除
config. newProp = 'value'; // ✗ 不能添加

console. log(Object. isSealed(config)); // true
console. log(Object. isExtensible(config)); // false
```

"这个比较接近我们的需求。"老张说,"不能删除, 不能添加, 但可以修改现有属性。"

"没错。"你继续写第三个方法,"最后是`Object. freeze()`:"

```javascript
// 方法3: freeze - 完全不可变
const config = {
    apiUrl: 'https://api. example. com',
    timeout: 5000
};

Object. freeze(config);

config. timeout = 10000;   // ✗ 不能修改
delete config. timeout;    // ✗ 不能删除
config. newProp = 'value'; // ✗ 不能添加

console. log(Object. isFrozen(config)); // true
console. log(Object. isSealed(config)); // true
console. log(Object. isExtensible(config)); // false
```

小王若有所思:"所以freeze是最严格的, 什么都不能改?"

"对。"你说,"但这里有个重要的点——这些方法都是**浅层**的。"

你在白板上写下一个新的例子:

```javascript
// 陷阱: 浅层锁定
const config = {
    server: {
        host: 'localhost',
        port: 3000
    },
    timeout: 5000
};

Object. freeze(config);

config. timeout = 10000;       // ✗ 失败(顶层属性不可变)
config. server. port = 8080;    // ✓ 成功!(嵌套对象可变)

console. log(config. server. port); // 8080
```

会议室里响起惊讶的声音。老张说:"所以即使freeze了, 嵌套对象还是可以改?"

"是的。"你点头,"如果需要深层冻结, 要递归处理所有嵌套对象。"

---

## 达成共识

下午三点半, 你在白板上总结出三种方法的对比:

**对比表格**

| 操作 | preventExtensions | seal | freeze |
|------|-------------------|------|--------|
| 读取属性 | ✓ | ✓ | ✓ |
| 修改属性 | ✓ | ✓ | ✗ |
| 删除属性 | ✓ | ✗ | ✗ |
| 添加属性 | ✗ | ✗ | ✗ |
| 修改描述符 | ✓ | ✗ | ✗ |

**示例对比**

```javascript
// 准备三个相同的对象
const obj1 = { name: 'Alice', age: 25 };
const obj2 = { name: 'Alice', age: 25 };
const obj3 = { name: 'Alice', age: 25 };

// 应用不同的锁定方法
Object. preventExtensions(obj1);
Object. seal(obj2);
Object. freeze(obj3);

// 测试修改属性
obj1. age = 30; // ✓ 成功
obj2. age = 30; // ✓ 成功
obj3. age = 30; // ✗ 失败

// 测试删除属性
delete obj1. age; // ✓ 成功
delete obj2. age; // ✗ 失败
delete obj3. age; // ✗ 失败

// 测试添加属性
obj1. city = 'Beijing'; // ✗ 失败
obj2. city = 'Beijing'; // ✗ 失败
obj3. city = 'Beijing'; // ✗ 失败
```

**深层冻结实现**

```javascript
function deepFreeze(obj) {
    // 1. 冻结对象本身
    Object. freeze(obj);

    // 2. 递归冻结所有属性
    Object. keys(obj). forEach(key => {
        const value = obj[key];
        if (typeof value === 'object' && value !== null) {
            deepFreeze(value);
        }
    });

    return obj;
}

// 使用深层冻结
const config = {
    server: {
        host: 'localhost',
        port: 3000
    }
};

deepFreeze(config);

config. server. port = 8080; // ✗ 失败(深层也被冻结了)
```

老张点点头:"明白了。对于我们的场景, 应该用`seal`, 既能防止结构被破坏, 又保留了修改配置值的灵活性。"

"对。"你说,"freeze太严格了, 会影响运行时配置更新。preventExtensions又太宽松, 不能防止属性被删除。seal刚好符合安全团队的要求。"

小李建议:"那我更新PR, 把freeze改成seal?"

"可以。"老张说,"而且文档里要说明清楚: 这是浅层锁定, 如果需要保护嵌套对象, 要么用深层冻结, 要么重新设计数据结构。"

会议在下午四点结束, 大家对这三种方法有了清晰的理解, 也为项目选择了合适的方案。

---

## 最佳实践

**规则 1: Object. preventExtensions()**

```javascript
const obj = { name: 'Alice' };

Object. preventExtensions(obj);

obj. name = 'Bob';     // ✓ 可以修改
delete obj. name;      // ✓ 可以删除
obj. age = 25;         // ✗ 不能添加

// 检查
Object. isExtensible(obj); // false
```

**用途**: 防止对象被添加新属性, 但允许修改和删除现有属性。

---

**规则 2: Object. seal()**

```javascript
const obj = { name: 'Alice' };

Object. seal(obj);

obj. name = 'Bob';     // ✓ 可以修改
delete obj. name;      // ✗ 不能删除
obj. age = 25;         // ✗ 不能添加

// 检查
Object. isSealed(obj);     // true
Object. isExtensible(obj); // false
```

**用途**: 密封对象, 固定结构但允许修改值。适合配置对象、数据模型。

---

**规则 3: Object. freeze()**

```javascript
const obj = { name: 'Alice' };

Object. freeze(obj);

obj. name = 'Bob';     // ✗ 不能修改
delete obj. name;      // ✗ 不能删除
obj. age = 25;         // ✗ 不能添加

// 检查
Object. isFrozen(obj);     // true
Object. isSealed(obj);     // true
Object. isExtensible(obj); // false
```

**用途**: 完全冻结对象, 创建真正的常量对象。

---

**规则 4: 关系层级**

```
Object. freeze()
    ↓ 包含
Object. seal()
    ↓ 包含
Object. preventExtensions()
```

```javascript
// freeze的对象, 一定是sealed的
Object. isFrozen(obj) === true
→ Object. isSealed(obj) === true
→ Object. isExtensible(obj) === false

// sealed的对象, 一定是不可扩展的
Object. isSealed(obj) === true
→ Object. isExtensible(obj) === false
```

---

**规则 5: 浅层 vs 深层**

```javascript
/* 浅层冻结: 只影响第一层 */
const obj = {
    name: 'Alice',
    address: {
        city: 'Beijing'
    }
};

Object. freeze(obj);

obj. name = 'Bob';           // ✗ 失败
obj. address. city = 'Shanghai'; // ✓ 成功!(嵌套对象可变)

/* 深层冻结: 递归冻结 */
function deepFreeze(obj) {
    Object. freeze(obj);
    Object. keys(obj). forEach(key => {
        const val = obj[key];
        if (typeof val === 'object' && val !== null) {
            deepFreeze(val);
        }
    });
    return obj;
}

const obj2 = {
    name: 'Alice',
    address: { city: 'Beijing' }
};

deepFreeze(obj2);
obj2. address. city = 'Shanghai'; // ✗ 失败
```

---

**规则 6: 严格模式的影响**

```javascript
/* 非严格模式: 静默失败 */
const obj = Object. freeze({ name: 'Alice' });
obj. name = 'Bob'; // 不报错, 但修改无效
console. log(obj. name); // 'Alice'

/* 严格模式: 抛出错误 */
'use strict';
const obj2 = Object. freeze({ name: 'Alice' });
obj2. name = 'Bob'; // TypeError: Cannot assign to read only property
```

---

**规则 7: 选择指南**

```javascript
/* 场景1: 运行时配置(可能需要更新值) */
const config = { timeout: 5000, retries: 3 };
Object. seal(config); // 允许修改值, 但结构固定

/* 场景2: 常量定义(完全不变) */
const CONSTANTS = { PI: 3. 14159, E: 2. 71828 };
Object. freeze(CONSTANTS); // 完全不可变

/* 场景3: 防止原型污染 */
const base = { toString: () => 'safe' };
Object. freeze(base); // 防止被修改

/* 场景4: 插件系统(允许扩展) */
const plugin = { name: 'MyPlugin' };
// 不锁定, 允许用户添加自定义属性
```

**决策树**:
- 需要修改值? → 不用freeze, 考虑seal或preventExtensions
- 需要添加属性? → 不锁定, 或只用seal/freeze保护关键部分
- 完全不变? → freeze (+ 考虑是否需要深层冻结)
- 只防止添加? → preventExtensions

---

**事故档案编号**: OBJ-2024-1755
**影响范围**: 对象不可变性, 安全配置管理
**根本原因**: 不理解三种锁定方法的区别, 过度使用freeze导致灵活性丧失
**修复成本**: 低(替换为合适的锁定方法)

这是JavaScript世界第55次被记录的对象密封事故。JavaScript提供了三种不同程度的对象锁定方法: preventExtensions(不可扩展)、seal(密封)、freeze(冻结)。它们的限制程度依次增强, 应根据实际需求选择。所有这些方法都是浅层的, 如果需要深层保护, 必须递归处理嵌套对象。理解它们的差异, 选择合适的工具, 既能满足安全需求, 又能保持必要的灵活性。

---

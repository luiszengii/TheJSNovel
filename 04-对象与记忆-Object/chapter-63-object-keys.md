《第 63 次记录: Object. keys 系列 —— 枚举的边界》

---

## Code Review 疑问

周五下午两点, 团队进行每周例行 Code Review。 会议室里, 六个人围坐在投影屏幕前。

轮到审查新人小林的代码时, 屏幕上出现了一段对象遍历的代码:

```javascript
// utils.js - 对象工具函数
function cloneObject(obj) {
    const result = {};
    for (const key in obj) {
        result[key] = obj[key];
    }
    return result;
}

function getObjectSize(obj) {
    return Object.keys(obj).length;
}

function mergeObjects(obj1, obj2) {
    const result = {};
    Object.entries(obj1).forEach(([key, value]) => {
        result[key] = value;
    });
    Object.entries(obj2).forEach(([key, value]) => {
        result[key] = value;
    });
    return result;
}
```

"小林, 这三个函数都是遍历对象的," 老张看着代码说,"你为什么用三种不同的方法?`for...in`、`Object.keys()`、`Object.entries()` 有什么区别?"

小林挠了挠头, 有些不好意思:"我也不太清楚... 网上搜的时候看到不同的写法, 就都用了。 它们应该是一样的吧?"

"不完全一样," 你插话道,"我记得 `for...in` 会遍历原型链上的属性, 但 `Object.keys()` 不会。 "

"对, 但这只是区别之一," 老张说,"我们来详细测试一下, 看看它们到底有什么不同。 "

---

## 测试对比

下午两点半, 老张打开浏览器控制台, 开始演示。

"首先, 我们创建一个测试对象," 老张输入代码:

```javascript
const parent = {
    inherited:'继承属性'
};

const obj = Object.create(parent);
obj.own = '自有属性';
obj.enumerable = '可枚举';

// 添加不可枚举属性
Object.defineProperty(obj, 'nonEnumerable', {
    value:'不可枚举',
    enumerable:false
});

// 添加 Symbol 属性
const sym = Symbol('symbol');
obj[sym] = 'Symbol 属性';

console.log('对象结构:', obj);
```

控制台输出显示了对象的结构。 老张继续说:"现在我们用不同方法遍历这个对象。 "

```javascript
// 方法 1:for...in
console.log('=== for...in ===');
for (const key in obj) {
    console.log(key, obj[key]);
}
// 输出:
// own 自有属性
// enumerable 可枚举
// inherited 继承属性  ← 注意!包含继承的属性

// 方法 2:Object.keys()
console.log('=== Object.keys() ===');
Object.keys(obj).forEach(key => {
    console.log(key, obj[key]);
});
// 输出:
// own 自有属性
// enumerable 可枚举
// (不包含 inherited)

// 方法 3:Object.entries()
console.log('=== Object.entries() ===');
Object.entries(obj).forEach(([key, value]) => {
    console.log(key, value);
});
// 输出:
// own 自有属性
// enumerable 可枚举

// 方法 4:Object.values()
console.log('=== Object.values() ===');
Object.values(obj).forEach(value => {
    console.log(value);
});
// 输出:
// 自有属性
// 可枚举
```

"看到区别了吗?" 老张问,"只有 `for...in` 遍历到了 `inherited` 属性, 因为它会遍历原型链。 "

小林点点头:"那不可枚举属性和 Symbol 属性呢? 为什么都没有遍历到?"

"好问题," 老张说,"这就涉及到属性的特性(property descriptor)了。 "

---

## 属性特性

下午三点, 老张开始讲解属性特性。

"每个属性都有四个特性," 老张在白板上写下:

```
属性特性 (Property Descriptor):
1.value:属性值
2.writable:是否可写
3.enumerable:是否可枚举 ← 关键!
4.configurable:是否可配置
```

"只有 `enumerable:true` 的属性才会被 `for...in`、`Object.keys()` 等方法遍历到," 老张解释。

他在控制台演示:

```javascript
// 查看属性特性
console.log(Object.getOwnPropertyDescriptor(obj, 'own'));
// {value:"自有属性", writable:true, enumerable:true, configurable:true}

console.log(Object.getOwnPropertyDescriptor(obj, 'nonEnumerable'));
// {value:"不可枚举", writable:false, enumerable:false, configurable:false}
```

"那如何遍历不可枚举属性?" 前端组的小王问。

"用 `Object.getOwnPropertyNames()`," 老张说:

```javascript
console.log('=== Object.getOwnPropertyNames() ===');
Object.getOwnPropertyNames(obj).forEach(key => {
    console.log(key, obj[key]);
});
// 输出:
// own 自有属性
// enumerable 可枚举
// nonEnumerable 不可枚举  ← 包含了!
```

"那 Symbol 属性呢?" 小林追问。

"Symbol 属性需要专门的方法," 老张继续演示:

```javascript
console.log('=== Object.getOwnPropertySymbols() ===');
Object.getOwnPropertySymbols(obj).forEach(sym => {
    console.log(sym, obj[sym]);
});
// 输出:
// Symbol(symbol) Symbol 属性
```

"所以," 你总结道,"如果要完整遍历一个对象的所有自有属性, 需要组合使用 `getOwnPropertyNames()` 和 `getOwnPropertySymbols()`?"

"完全正确," 老张赞许地点头。

---

## 实际问题

下午三点半, 讨论转向实际应用场景。

"回到小林的代码," 老张说,"你的 `cloneObject` 函数用了 `for...in`, 这可能会复制原型链上的属性, 这是你想要的吗?"

小林思考了一下:"不是... 我只想复制对象自己的属性。 "

"那就应该加一个检查," 你建议:

```javascript
// 修复版本 1:使用 hasOwnProperty
function cloneObject(obj) {
    const result = {};
    for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
            result[key] = obj[key];
        }
    }
    return result;
}

// 修复版本 2:使用 Object.keys (更简洁)
function cloneObject(obj) {
    const result = {};
    Object.keys(obj).forEach(key => {
        result[key] = obj[key];
    });
    return result;
}

// 修复版本 3:使用 Object.entries (推荐)
function cloneObject(obj) {
    return Object.fromEntries(Object.entries(obj));
}
```

"三种写法都可以," 老张说,"但版本 3 最简洁。 不过要注意, 这些都是浅拷贝。 "

小王突然想到一个问题:"我们项目里有个函数, 用 `Object.keys().length` 判断对象是否为空, 这样对吗?"

```javascript
function isEmpty(obj) {
    return Object.keys(obj).length === 0;
}

const obj1 = {};
const obj2 = Object.create({a:1});

console.log(isEmpty(obj1)); // true
console.log(isEmpty(obj2)); // true ← 但 obj2 可以访问 obj2.a
```

"这个判断不完全准确," 你说,"如果对象有继承的属性, 这个函数会返回 `true`, 但对象其实不是空的。 "

"如何更准确地判断?" 小王问。

老张给出了改进方案:

```javascript
function isReallyEmpty(obj) {
    // 检查自有可枚举属性
    if (Object.keys(obj).length > 0) return false;

    // 检查自有不可枚举属性
    if (Object.getOwnPropertyNames(obj).length > 0) return false;

    // 检查 Symbol 属性
    if (Object.getOwnPropertySymbols(obj).length > 0) return false;

    return true;
}

// 或者简化版本(只检查自有属性)
function hasOwnProperties(obj) {
    return Object.getOwnPropertyNames(obj).length > 0 ||
           Object.getOwnPropertySymbols(obj).length > 0;
}
```

---

## 方法总结

下午四点, 老张在白板上画出完整的对比表。

"让我们总结一下所有的对象遍历方法," 老张说。

**对象遍历方法对比表:**

| 方法 | 自有属性 | 继承属性 | 不可枚举 | Symbol | 返回值 |
|------|---------|---------|---------|--------|--------|
| `for...in` | ✅ | ✅ | ❌ | ❌ | 键(遍历) |
| `Object.keys()` | ✅ | ❌ | ❌ | ❌ | 键数组 |
| `Object.values()` | ✅ | ❌ | ❌ | ❌ | 值数组 |
| `Object.entries()` | ✅ | ❌ | ❌ | ❌ | 键值对数组 |
| `Object.getOwnPropertyNames()` | ✅ | ❌ | ✅ | ❌ | 键数组 |
| `Object.getOwnPropertySymbols()` | ✅ | ❌ | ✅ | ✅ | Symbol 数组 |

"根据不同场景选择不同方法," 老张指着表格说:

```
使用场景推荐:
- 遍历对象键值对 → Object.entries()
- 只需要键 → Object.keys()
- 只需要值 → Object.values()
- 需要包含继承属性 → for...in + hasOwnProperty 过滤
- 需要不可枚举属性 → Object.getOwnPropertyNames()
- 需要 Symbol 属性 → Object.getOwnPropertySymbols()
- 完整克隆 → 组合使用多种方法
```

---

## 性能对比

下午四点半, 测试组的小陈提出了性能问题。

"这些方法的性能有区别吗?" 小陈问,"我们有个接口会处理上千个对象。 "

"有区别, 但通常不大," 老张说,"让我们测试一下。 "

```javascript
// 准备测试数据
const testObj = {};
for (let i = 0;i < 1000;i++) {
    testObj[`key${i}`] = i;
}

// 测试 1:for...in
console.time('for...in');
for (const key in testObj) {
    if (testObj.hasOwnProperty(key)) {
        const value = testObj[key];
    }
}
console.timeEnd('for...in');

// 测试 2:Object.keys()
console.time('Object.keys');
Object.keys(testObj).forEach(key => {
    const value = testObj[key];
});
console.timeEnd('Object.keys');

// 测试 3:Object.entries()
console.time('Object.entries');
Object.entries(testObj).forEach(([key, value]) => {
    // 使用 key 和 value
});
console.timeEnd('Object.entries');
```

结果显示:

```
for...in:2.1ms
Object.keys:1.8ms
Object.entries:1.9ms
```

"差别很小," 老张说,"除非你的对象非常大, 或者在极高频率的循环中使用, 否则不用太担心性能。 选择最符合语义和需求的方法更重要。 "

---

## 代码重构

下午五点, 小林开始根据讨论结果重构代码。

"我明白了," 小林说着修改代码:

```javascript
// utils-refactored.js - 重构后的工具函数

/**
 * 克隆对象(浅拷贝, 只复制自有可枚举属性)
 */
function cloneObject(obj) {
    return Object.fromEntries(Object.entries(obj));
}

/**
 * 获取对象自有可枚举属性数量
 */
function getObjectSize(obj) {
    return Object.keys(obj).length;
}

/**
 * 合并对象(后者覆盖前者)
 */
function mergeObjects(obj1, obj2) {
    return { ...obj1, ...obj2 };
}

/**
 * 检查对象是否为空(只检查自有可枚举属性)
 */
function isEmpty(obj) {
    return Object.keys(obj).length === 0;
}

/**
 * 深度克隆对象(包含所有自有属性)
 */
function deepCloneAll(obj) {
    const result = {};

    // 复制字符串键属性(包括不可枚举)
    Object.getOwnPropertyNames(obj).forEach(key => {
        const descriptor = Object.getOwnPropertyDescriptor(obj, key);
        Object.defineProperty(result, key, descriptor);
    });

    // 复制 Symbol 键属性
    Object.getOwnPropertySymbols(obj).forEach(sym => {
        const descriptor = Object.getOwnPropertyDescriptor(obj, sym);
        Object.defineProperty(result, sym, descriptor);
    });

    return result;
}

/**
 * 遍历对象所有自有属性(包括 Symbol)
 */
function forEachProperty(obj, callback) {
    // 遍历字符串键
    Object.getOwnPropertyNames(obj).forEach(key => {
        callback(key, obj[key]);
    });

    // 遍历 Symbol 键
    Object.getOwnPropertySymbols(obj).forEach(sym => {
        callback(sym, obj[sym]);
    });
}
```

"现在每个函数都有明确的语义和注释," 小林说,"而且我知道该用哪个方法了。 "

老张审查了代码, 满意地点头:"很好。 记住这个原则: 选择方法时, 首先考虑语义是否清晰, 其次考虑是否满足需求, 最后才考虑性能。 "

---

## 复盘与收获

下午五点半, Code Review 结束。 小林留下来整理笔记。

"今天学到好多," 小林对你说,"原来对象遍历有这么多细节。 "

"是啊," 你说,"JavaScript 的对象系统比表面看起来复杂得多。 属性有自有和继承之分, 有可枚举和不可枚举之分, 还有 Symbol 属性, 每种遍历方法的行为都不同。 "

"我把今天的内容总结一下," 小林打开笔记本电脑:

```
对象遍历核心要点:

1.属性来源:自有 vs 继承
2.属性特性:可枚举 vs 不可枚举
3.属性键:字符串 vs Symbol
4.方法选择:根据需求选择合适的方法
5.性能考虑:通常不是瓶颈, 语义优先

常见陷阱:
- for...in 会遍历继承属性, 通常需要 hasOwnProperty 过滤
- Object.keys() 只返回可枚举属性
- Symbol 属性需要专门方法获取
- 浅拷贝 vs 深拷贝要区分清楚
```

"写得很好," 你赞许道,"以后遇到对象遍历, 就知道该怎么选择了。 "

晚上回家的路上, 你回想今天的 Code Review。 一个简单的对象遍历问题, 引出了属性特性、原型链、枚举性等一系列知识点。

你在手机备忘录里写下:**"基础知识的细节往往被忽视, 但正是这些细节决定了代码的正确性和健壮性。 "**

---

## 知识总结

**规则 1: Object. keys/values/entries**

`Object.keys()` 返回自有可枚举属性的键数组,`Object.values()` 返回值数组,`Object.entries()` 返回键值对数组。 三者都不包含继承属性、不可枚举属性和 Symbol 属性。

---

**规则 2: for... in 循环特性**

`for...in` 遍历对象的可枚举属性, 包括继承的属性, 但不包括 Symbol 属性。 使用时通常需要 `hasOwnProperty()` 过滤继承属性:

```javascript
for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
        // 只处理自有属性
    }
}
```

---

**规则 3: 获取不可枚举属性**

`Object.getOwnPropertyNames()` 返回所有自有属性(包括不可枚举), 但不包括 Symbol 属性。 这是获取完整属性列表的关键方法。

---

**规则 4: Symbol 属性处理**

Symbol 属性不会被常规遍历方法发现, 需要使用 `Object.getOwnPropertySymbols()` 获取。 完整遍历对象需要组合使用:

```javascript
const allKeys = [
    ...Object.getOwnPropertyNames(obj),
    ...Object.getOwnPropertySymbols(obj)
];
```

---

**规则 5: 方法选择指南**

| 需求 | 推荐方法 | 理由 |
|------|---------|------|
| 遍历键值对 | Object. entries() | 语义清晰 |
| 只需要键 | Object. keys() | 性能好 |
| 只需要值 | Object. values() | 避免访问键 |
| 包含继承属性 | for... in + hasOwnProperty | 唯一选择 |
| 包含不可枚举 | getOwnPropertyNames() | 完整性 |
| 包含 Symbol | getOwnPropertySymbols() | 专用方法 |

根据实际需求选择, 语义和正确性优先于性能。

---

**规则 6: 属性特性(Descriptor)**

每个属性都有 4 个特性:`value`、`writable`、`enumerable`、`configurable`。 只有 `enumerable:true` 的属性才会被 `Object.keys()` 和 `for...in` 遍历。 使用 `Object.getOwnPropertyDescriptor()` 查看, 使用 `Object.defineProperty()` 定义。

---

**事故档案编号**: OBJ-2024-1863
**影响范围**: Object. keys, Object. values, Object. entries, for... in, 属性枚举, 原型链遍历
**根本原因**: 不理解不同遍历方法的差异, 混用导致逻辑错误(遍历到继承属性或遗漏 Symbol 属性)
**修复成本**: 低(选择正确方法), 需理解属性特性和原型链机制

这是 JavaScript 世界第 63 次被记录的对象枚举事故。 对象遍历方法分三类:`Object.keys/values/entries` 只返回自有可枚举属性,`for...in` 包含继承属性,`getOwnPropertyNames/Symbols` 包含不可枚举或 Symbol 属性。 属性有三个维度: 来源(自有 vs 继承)、枚举性(enumerable)、键类型(字符串 vs Symbol)。 常见陷阱:`for...in` 需 `hasOwnProperty` 过滤,`Object.keys()` 不包含 Symbol, 浅拷贝不复制不可枚举属性。 方法选择: 日常用 `Object.entries()`, 需继承用 `for...in`, 需完整用 `getOwnPropertyNames` + `getOwnPropertySymbols`。 理解属性特性和遍历方法差异是正确操作对象的基础。

---

《第 61 次记录：Map 与 Set —— 键的自由》

---

## 性能告警

周三上午十点，监控系统突然发出警报。你打开性能监控面板，看到一条刺眼的红色曲线。

```
[WARNING] 性能异常
模块:用户数据查询
响应时间:10ms → 500ms (增长 50 倍)
影响用户:所有活跃用户
趋势:持续恶化
```

"怎么会这样？"你皱起眉头。昨天刚上线的用户数据优化功能，本来是为了提升性能，现在反而变慢了 50 倍？

你立刻打开最近的代码提交记录，找到了昨天的改动：

```javascript
// user-cache.js - 用户数据缓存（昨天的改动）
class UserCache {
    constructor() {
        this.cache = {}; // 用对象存储缓存
    }

    set(userId, userData) {
        this.cache[userId] = userData;
    }

    get(userId) {
        return this.cache[userId];
    }

    has(userId) {
        return userId in this.cache;
    }
}
```

"代码看起来没问题啊，"你自言自语，"用对象做缓存是常见做法。"

但监控数据不会撒谎。你决定在本地环境重现问题，写了一个性能测试：

```javascript
const cache = new UserCache();

// 模拟 10 万个用户
console.time('写入 10 万条数据');
for (let i = 0;i < 100000;i++) {
    cache.set(i, { id:i, name:`User${i}` });
}
console.timeEnd('写入 10 万条数据');

// 查询测试
console.time('查询 1 万次');
for (let i = 0;i < 10000;i++) {
    cache.get(Math.floor(Math.random() * 100000));
}
console.timeEnd('查询 1 万次');
```

输出结果让你震惊：

```
写入 10 万条数据:245ms
查询 1 万次:428ms
```

"查询比写入还慢？"你不敢相信，"这不科学啊，对象属性访问应该是 O(1) 的。"

---

## 深入调查

上午十一点，你开始逐步排查问题。

首先，你检查了缓存对象的大小：

```javascript
console.log(Object.keys(cache.cache).length); // 100000
```

10 万个属性的对象，这本身就可能有性能问题。但更诡异的是，你发现了一个奇怪的现象：

```javascript
// 测试不同类型的键
const testObj = {};

testObj[123] = 'number key';
testObj['123'] = 'string key';

console.log(testObj[123]); // 'string key' - 什么？
console.log(testObj['123']); // 'string key'
console.log(Object.keys(testObj)); // ['123'] - 只有一个键！
```

"天啊，"你恍然大悟，"对象的键会被转换成字符串！数字 `123` 和字符串 `'123'` 是同一个键！"

你立刻想到用户 ID 的问题。在你们的系统里，用户 ID 是数字类型，但存入对象后都被转换成了字符串。这意味着：

```javascript
cache.set(12345, userData); // 键被转换成 '12345'
cache.get(12345);            // 查找时又转换一次
```

每次查找都需要类型转换，而且对于大对象，JavaScript 引擎的哈希表性能会下降。

---

## 老张的建议

你找到老张，描述了问题。老张听完后说："用对象做缓存有两个致命问题。第一，键只能是字符串或 Symbol。第二，大对象的性能会下降。"

"那怎么办？"你问。

"用 `Map`，"老张说，"ES6 引入的 Map 专门用于存储键值对，性能比对象好得多，而且键可以是任意类型。"

老张给你演示：

```javascript
class UserCacheMap {
    constructor() {
        this.cache = new Map(); // 使用 Map
    }

    set(userId, userData) {
        this.cache.set(userId, userData);
    }

    get(userId) {
        return this.cache.get(userId);
    }

    has(userId) {
        return this.cache.has(userId);
    }

    delete(userId) {
        return this.cache.delete(userId);
    }

    clear() {
        this.cache.clear();
    }

    get size() {
        return this.cache.size;
    }
}
```

"Map 的 API 更语义化，"老张说，"`set`、`get`、`has`、`delete`、`clear`，一目了然。而且它有 `size` 属性，不需要用 `Object.keys().length`。"

---

## 性能对比

中午十二点，你开始做详细的性能对比测试。

```javascript
// 测试 1:写入性能
function testWrite(iterations) {
    // 对象方式
    console.time('Object 写入');
    const obj = {};
    for (let i = 0;i < iterations;i++) {
        obj[i] = { id:i, name:`User${i}` };
    }
    console.timeEnd('Object 写入');

    // Map 方式
    console.time('Map 写入');
    const map = new Map();
    for (let i = 0;i < iterations;i++) {
        map.set(i, { id:i, name:`User${i}` });
    }
    console.timeEnd('Map 写入');
}

testWrite(100000);
```

结果：

```
Object 写入:245ms
Map 写入:156ms  // 快了 36%
```

```javascript
// 测试 2:查询性能
function testRead(dataSize, queryCount) {
    const obj = {};
    const map = new Map();

    // 准备数据
    for (let i = 0;i < dataSize;i++) {
        obj[i] = { id:i };
        map.set(i, { id:i });
    }

    // 对象查询
    console.time('Object 查询');
    for (let i = 0;i < queryCount;i++) {
        obj[Math.floor(Math.random() * dataSize)];
    }
    console.timeEnd('Object 查询');

    // Map 查询
    console.time('Map 查询');
    for (let i = 0;i < queryCount;i++) {
        map.get(Math.floor(Math.random() * dataSize));
    }
    console.timeEnd('Map 查询');
}

testRead(100000, 10000);
```

结果：

```
Object 查询:428ms
Map 查询:89ms  // 快了 79%！
```

"差距太明显了！"你惊呼，"Map 的查询速度是对象的将近 5 倍！"

---

## Map 的独特优势

下午两点，老张继续给你讲解 Map 的其他优势。

"Map 最大的优势是键可以是任意类型，"老张说着打开控制台：

```javascript
const map = new Map();

// 数字键
map.set(1, 'number key');
map.set('1', 'string key');
console.log(map.get(1)); // 'number key'
console.log(map.get('1')); // 'string key' - 完全独立！

// 对象键
const objKey1 = {id:1};
const objKey2 = {id:1};
map.set(objKey1, 'first object');
map.set(objKey2, 'second object');
console.log(map.get(objKey1)); // 'first object'
console.log(map.get(objKey2)); // 'second object' - 不同的对象

// 函数键
const funcKey = function() {};
map.set(funcKey, 'function key');
console.log(map.get(funcKey)); // 'function key'

// NaN 键（特殊情况）
map.set(NaN, 'NaN key');
console.log(map.get(NaN)); // 'NaN key' - 在 Map 中 NaN === NaN
```

"在普通对象里，`NaN` 作为键是灾难，"老张补充道：

```javascript
const obj = {};
obj[NaN] = 'value';
console.log(obj[NaN]); // 'value'
console.log(obj['NaN']); // 'value' - 被转成了字符串 'NaN'
```

"而且 Map 会保持插入顺序，"老张继续演示：

```javascript
const map = new Map();
map.set('c', 3);
map.set('a', 1);
map.set('b', 2);

for (const [key, value] of map) {
    console.log(key, value);
}
// 输出顺序:c 3, a 1, b 2 - 按插入顺序

// 对比对象
const obj = { c:3, a:1, b:2 };
for (const key in obj) {
    console.log(key, obj[key]);
}
// 输出顺序可能不一样（数字键会被排序）
```

---

## Set 的应用

下午三点，老张提到了 Set："Map 是键值对集合，Set 是值的集合，最大特点是自动去重。"

```javascript
// 数组去重的传统方式
const arr = [1, 2, 3, 2, 1, 4, 3, 5];
const unique = [...new Set(arr)];
console.log(unique); // [1, 2, 3, 4, 5]

// 对比传统方法
function uniqueOldWay(arr) {
    const result = [];
    for (const item of arr) {
        if (!result.includes(item)) {
            result.push(item);
        }
    }
    return result;
}
// 这个方法是 O(n²)，Set 是 O(n)
```

你想到了一个实际应用场景：

```javascript
// 用户访问记录去重
class UserActivityTracker {
    constructor() {
        this.activeUsers = new Set();
    }

    recordActivity(userId) {
        this.activeUsers.add(userId);
    }

    getActiveUserCount() {
        return this.activeUsers.size;
    }

    isUserActive(userId) {
        return this.activeUsers.has(userId);
    }

    clearInactiveUsers() {
        this.activeUsers.clear();
    }
}

const tracker = new UserActivityTracker();
tracker.recordActivity(1001);
tracker.recordActivity(1002);
tracker.recordActivity(1001); // 重复，不会增加

console.log(tracker.getActiveUserCount()); // 2
console.log(tracker.isUserActive(1001)); // true
```

"Set 的 `has()` 方法查找效率是 O(1)，"老张说，"比数组的 `includes()` (O(n)) 快得多。"

---

## 紧急修复

下午四点，你开始重构缓存系统。

```javascript
// user-cache-fixed.js - 使用 Map 的版本
class UserCache {
    constructor() {
        this.cache = new Map();
        this.maxSize = 10000; // 限制缓存大小
    }

    set(userId, userData) {
        // 如果缓存已满，删除最早的条目
        if (this.cache.size >= this.maxSize) {
            const firstKey = this.cache.keys().next().value;
            this.cache.delete(firstKey);
        }

        this.cache.set(userId, userData);
    }

    get(userId) {
        return this.cache.get(userId);
    }

    has(userId) {
        return this.cache.has(userId);
    }

    delete(userId) {
        return this.cache.delete(userId);
    }

    clear() {
        this.cache.clear();
    }

    get size() {
        return this.cache.size;
    }

    // 遍历所有缓存
    *entries() {
        yield* this.cache.entries();
    }
}
```

你在本地进行了完整的性能测试：

```javascript
const cache = new UserCache();

console.time('新版本 - 写入 10 万条');
for (let i = 0;i < 100000;i++) {
    cache.set(i, { id:i, name:`User${i}` });
}
console.timeEnd('新版本 - 写入 10 万条');

console.time('新版本 - 查询 1 万次');
for (let i = 0;i < 10000;i++) {
    cache.get(Math.floor(Math.random() * 100000));
}
console.timeEnd('新版本 - 查询 1 万次');
```

结果：

```
新版本 - 写入 10 万条:158ms  (旧版 245ms)
新版本 - 查询 1 万次:87ms   (旧版 428ms)
```

"性能提升了 5 倍，完美！"你兴奋地说。

---

## 部署验证

下午五点，代码审查通过，你开始部署到生产环境。

部署完成后，你紧张地盯着监控面板。几分钟后，性能曲线开始下降，从 500ms 快速回落到正常水平。

```
[INFO] 性能恢复
模块:用户数据查询
响应时间:500ms → 12ms
改善:97.6%
状态:正常
```

"成功了！"你长舒一口气。

运维组长老王发来消息："用户查询速度明显变快了，干得好！"

技术负责人老李也在群里说："这个改动不仅解决了性能问题，还让代码更清晰了。Map 的 API 比对象操作更语义化。以后涉及大量键值对存储的场景，优先考虑 Map。"

---

## 知识总结

晚上七点，你在团队 wiki 上写下了今天的总结。

**Map vs Object 对比表：**

| 特性 | Map | Object |
|------|-----|--------|
| 键类型 | 任意类型 | 字符串/Symbol |
| 键顺序 | 插入顺序 | 部分有序（数字键排序） |
| 大小 | `size` 属性 | `Object.keys().length` |
| 性能（大数据） | 优秀 | 较差 |
| 遍历 | `for...of` | `for...in` / `Object.keys()` |
| 默认键 | 无 | 继承原型链的键 |

**Set 的典型应用：**
- 数组去重
- 成员唯一性检查
- 交集、并集、差集运算
- 高性能的存在性判断

你保存了文档，准备明天的技术分享会上给大家讲解 Map 和 Set 的最佳实践。

---

## Map 与 Set 知识

**规则 1: Map 与 Object 的核心区别**

Map 的键可以是任意类型（对象、函数、基本类型），Object 的键只能是字符串或 Symbol。Map 保持插入顺序，大数据场景下性能更优。

---

**规则 2: Map 的基本 API**

```javascript
const map = new Map();
map.set(key, value)     // 设置键值对
map.get(key)            // 获取值
map.has(key)            // 检查是否存在
map.delete(key)         // 删除键值对
map.clear()             // 清空所有
map.size                // 获取大小
map.keys()              // 键的迭代器
map.values()            // 值的迭代器
map.entries()           // 键值对迭代器
```

所有方法都返回有意义的值，链式调用友好。

---

**规则 3: Set 用于唯一值集合**

Set 自动去重，成员值唯一。常用于数组去重、成员判断等场景：

```javascript
const set = new Set([1, 2, 2, 3]);
set.size              // 3
set.has(2)            // true
set.add(4)            // 添加成员
set.delete(1)         // 删除成员
[...set]              // 转为数组 [2, 3, 4]
```

`has()` 方法的时间复杂度是 O(1)，比数组 `includes()` 的 O(n) 快得多。

---

**规则 4: 性能优势**

| 操作 | Map/Set | Object/Array | 性能差异 |
|------|---------|--------------|----------|
| 写入 | O(1) | O(1) | Map 快 30-50% |
| 查询 | O(1) | O(1) ~ O(n) | Map 快 2-5 倍 |
| 删除 | O(1) | O(n) | Map 明显更快 |
| 大小 | O(1) | O(n) | Map 直接获取 |

大数据量（>1000 条）时，Map/Set 优势明显。

---

**规则 5: 遍历方式**

Map 和 Set 都实现了 Iterable 协议，支持多种遍历：

```javascript
// Map 遍历
for (const [key, value] of map) { }
for (const key of map.keys()) { }
for (const value of map.values()) { }

// Set 遍历
for (const value of set) { }
set.forEach(value => { })
```

注意：Map 的 `forEach` 参数顺序是 `(value, key, map)`，与数组不同。

---

**规则 6: 使用场景选择**

| 场景 | 推荐 | 原因 |
|------|------|------|
| 简单配置对象 | Object | 字面量语法简洁 |
| 频繁增删键值对 | Map | 性能更好 |
| 键是非字符串 | Map | 唯一选择 |
| 需要 JSON 序列化 | Object | Map 不支持 JSON |
| 数组去重 | Set | 自动去重 |
| 成员唯一性 | Set | O(1) 查找 |

总结：数据量大、键类型复杂、频繁操作时优先用 Map/Set。

---

**事故档案编号**: OBJ-2024-1861
**影响范围**: Map, Set, 性能优化, 键值对存储, 数据去重
**根本原因**: 使用 Object 存储大量键值对导致性能下降，键类型转换成字符串限制了灵活性
**修复成本**: 低（改用 Map），性能提升 2-5 倍

这是 JavaScript 世界第 61 次被记录的数据结构选择事故。Map 是 ES6 引入的键值对集合，键可以是任意类型，保持插入顺序，大数据场景性能优于 Object。Set 是唯一值集合，自动去重，`has()` 方法 O(1) 时间复杂度。Map 提供 `set/get/has/delete/clear` 等语义化 API，`size` 属性直接获取大小。Set 常用于数组去重、成员判断。性能对比：大数据量时 Map 查询比 Object 快 2-5 倍，Set 的 `has()` 比数组 `includes()` 快得多。使用建议：数据量大、键类型复杂、频繁操作时优先 Map/Set；简单配置或需要 JSON 序列化时用 Object。

---

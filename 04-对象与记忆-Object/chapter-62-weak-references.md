《第 62 次记录： WeakMap 与 WeakSet —— 弱引用的世界》

---

## 内存告警

周四下午三点, 运维监控系统突然发出红色警报。 你正在测试新功能, 看到大屏幕上跳出刺眼的提示。

```
[CRITICAL] 内存异常
应用:用户管理后台 (SPA)
当前内存:1.2GB (持续增长)
运行时长:2 小时 15 分钟
用户反馈:页面卡顿、浏览器崩溃
状态:需立即处理
```

"怎么会这样?" 你皱起眉头,"单页应用运行两个多小时就占用 1.2GB 内存?"

你打开浏览器开发者工具, 切换到 Memory 标签, 手动触发了一次垃圾回收。 令你震惊的是, 内存占用几乎没有下降。

"这说明有大量对象无法被回收," 你自言自语,"典型的内存泄漏。 "

你立刻检查最近的代码改动, 发现上周刚上线了一个用户行为追踪功能。 这个功能会记录用户在页面上的所有操作, 用于后续的数据分析。

---

## 追踪问题

下午三点半, 你找到了上周上线的追踪代码:

```javascript
// user-tracker.js - 用户行为追踪
class UserTracker {
    constructor() {
        this.userData = new Map(); // 存储用户数据
        this.clickHistory = new Map(); // 存储点击历史
    }

    trackUser(userId, userElement) {
        // 用 DOM 元素作为键, 存储用户信息
        this.userData.set(userElement, {
            userId:userId,
            loginTime:Date.now()
        });
    }

    trackClick(element, eventData) {
        // 记录每个 DOM 元素的点击事件
        if (!this.clickHistory.has(element)) {
            this.clickHistory.set(element, []);
        }
        this.clickHistory.get(element).push({
            timestamp:Date.now(),
            ...eventData
        });
    }

    getUserData(element) {
        return this.userData.get(element);
    }
}

const tracker = new UserTracker();
```

代码看起来很简单, 就是用 Map 存储 DOM 元素和相关数据的映射关系。 你决定在本地重现问题。

你写了一个测试页面, 模拟用户在单页应用中不断切换界面的场景:

```javascript
// 模拟页面切换
function simulatePageSwitch() {
    const container = document.getElementById('app');

    // 清空旧内容
    container.innerHTML = '';

    // 创建新的用户卡片
    for (let i = 0;i < 100;i++) {
        const card = document.createElement('div');
        card.className = 'user-card';
        card.textContent = `用户 ${i}`;

        // 追踪这个元素
        tracker.trackUser(i, card);

        // 添加点击监听
        card.addEventListener('click', () => {
            tracker.trackClick(card, { cardId:i });
        });

        container.appendChild(card);
    }
}

// 模拟用户不断切换页面
setInterval(simulatePageSwitch, 3000);
```

你打开 Chrome 的 Memory Profiler, 运行这段代码, 然后每隔 30 秒拍一次内存快照。 结果让你倒吸一口凉气:

```
快照 1 (0 分钟): 15MB
快照 2 (30 秒): 45MB
快照 3 (1 分钟): 78MB
快照 4 (1.5 分钟): 112MB
快照 5 (2 分钟): 145MB
```

"内存在疯狂增长!" 你惊呼,"每次切换页面都会创建 100 个新元素, 但旧元素从 DOM 中移除后, 内存并没有释放。 "

---

## 老张的分析

下午四点, 你紧急叫来老张。 老张看了代码后, 立刻指出了问题。

"你用 Map 存储 DOM 元素作为键," 老张说,"这是强引用。 即使元素从 DOM 树中移除了, 只要 Map 还引用着它, 垃圾回收器就无法回收。 "

"强引用?" 你有点困惑。

老张在白板上画了一张图:

```
DOM 树:
  <div id="app">
    <div class="user-card">用户 0</div>  ←─┐
    <div class="user-card">用户 1</div>  ←─┤
    ...                                   │
  </div>                                   │
                                          │
tracker.userData (Map):               │
  element1 (强引用) ──────────────────────┘
  element2 (强引用) ──────────────────────┐
  ...                                    │
                                          │
当 innerHTML = '' 后:                 │
  DOM 树中元素被移除                      │
  但 Map 仍然持有引用 ─────────────────────┘
  垃圾回收器无法回收这些元素
```

"看到了吗?" 老张指着图,"JavaScript 的垃圾回收机制是基于可达性的。 如果一个对象从根对象(window、document 等)出发, 通过引用链可以访问到, 它就是可达的, 就不会被回收。 "

"所以每次页面切换," 你恍然大悟,"旧的 DOM 元素虽然从 DOM 树移除了, 但 Map 里还保留着引用, 导致这些元素和相关数据都无法被回收?"

"完全正确," 老张点头,"这就是内存泄漏的根本原因。 "

---

## WeakMap 的解法

下午四点半, 老张给你介绍了 WeakMap。

"WeakMap 和 Map 很相似," 老张说,"但有两个关键区别。 第一, WeakMap 的键必须是对象。 第二, WeakMap 对键的引用是弱引用。 "

"弱引用是什么意思?" 你问。

"弱引用不会阻止垃圾回收," 老张解释,"如果一个对象只被弱引用持有, 没有其他强引用指向它, 垃圾回收器就可以回收这个对象。 "

老张在控制台演示:

```javascript
// 强引用示例 (Map)
let obj1 = { name:'张三' };
const map = new Map();
map.set(obj1, '数据');

obj1 = null; // 试图释放对象
// 但 obj1 对应的对象仍然存活, 因为 map 持有强引用
console.log(map.size); // 1

// 弱引用示例 (WeakMap)
let obj2 = { name:'李四' };
const weakMap = new WeakMap();
weakMap.set(obj2, '数据');

obj2 = null; // 释放对象
// obj2 对应的对象可以被垃圾回收
// 下次 GC 时, weakMap 中的条目会自动消失
```

"所以如果我用 WeakMap 替换 Map," 你若有所思,"当 DOM 元素从 DOM 树移除后, 只要我代码中没有其他地方引用这些元素, 它们就能被自动回收?"

"正是如此," 老张赞许地点头,"这正是 WeakMap 的设计目的 —— 存储对象的元数据, 而不影响对象的生命周期。 "

---

## 紧急修复

下午五点, 你开始重构追踪系统:

```javascript
// user-tracker-fixed.js - 使用 WeakMap 的版本
class UserTracker {
    constructor() {
        this.userData = new WeakMap(); // 改用 WeakMap
        this.clickHistory = new WeakMap(); // 改用 WeakMap
    }

    trackUser(userId, userElement) {
        // WeakMap 的键必须是对象
        this.userData.set(userElement, {
            userId:userId,
            loginTime:Date.now()
        });
    }

    trackClick(element, eventData) {
        if (!this.clickHistory.has(element)) {
            this.clickHistory.set(element, []);
        }
        this.clickHistory.get(element).push({
            timestamp:Date.now(),
            ...eventData
        });
    }

    getUserData(element) {
        return this.userData.get(element);
    }

    // WeakMap 没有 size、keys()、values() 等方法
    // 无法遍历, 这是为了配合垃圾回收机制
}
```

你在测试环境重新运行模拟测试, 这次打开 Memory Profiler 持续监控:

```
快照 1 (0 分钟): 15MB
快照 2 (30 秒): 18MB ← 没有暴涨!
快照 3 (1 分钟): 16MB ← 内存被回收了!
快照 4 (1.5 分钟): 17MB
快照 5 (2 分钟): 15MB ← 保持稳定
```

"完美!" 你兴奋地说,"内存不再持续增长了。 旧的 DOM 元素和数据都被正确回收。 "

---

## WeakSet 的应用

下午五点半, 老张继续给你讲解 WeakSet。

"WeakSet 和 WeakMap 类似," 老张说,"区别是 WeakSet 只存储对象本身, 不存储键值对。 它常用于标记对象。 "

老张给你演示了一个常见应用场景:

```javascript
// 防止重复处理
class TaskProcessor {
    constructor() {
        this.processedTasks = new WeakSet();
    }

    process(task) {
        // 检查是否已处理过
        if (this.processedTasks.has(task)) {
            console.log('任务已处理, 跳过');
            return;
        }

        // 处理任务
        console.log('处理任务:', task.name);
        this.doProcess(task);

        // 标记为已处理
        this.processedTasks.add(task);
    }

    doProcess(task) {
        // 实际处理逻辑
    }
}

const processor = new TaskProcessor();
const task1 = { name:'数据导入' };

processor.process(task1); // 处理任务:数据导入
processor.process(task1); // 任务已处理, 跳过

// 当 task1 不再被其他地方引用时, 会自动从 WeakSet 中移除
```

"这比用 Set 好在哪里?" 你问。

"如果用 Set," 老张解释,"即使任务对象在其他地方都不再使用, Set 仍然持有强引用, 导致这些任务对象永远无法被回收。 而 WeakSet 不会有这个问题。 "

你想到了另一个应用场景:

```javascript
// DOM 元素访问追踪
class ElementTracker {
    constructor() {
        this.visitedElements = new WeakSet();
    }

    markVisited(element) {
        this.visitedElements.add(element);
    }

    hasVisited(element) {
        return this.visitedElements.has(element);
    }
}

const tracker = new ElementTracker();

document.querySelectorAll('.card').forEach(card => {
    card.addEventListener('click', () => {
        if (!tracker.hasVisited(card)) {
            console.log('首次访问该卡片');
            tracker.markVisited(card);
        }
    });
});

// 当卡片从 DOM 移除时, WeakSet 中的记录会自动清除
```

"妙啊," 你赞叹,"用 WeakSet 追踪访问状态, 既简单又不会造成内存泄漏。 "

---

## 部署验证

下午六点, 代码审查通过, 你开始部署到生产环境。

部署完成后, 你紧张地盯着监控面板。 运维老王也在旁边观察。

"上线了," 老王说,"我们让它跑一段时间, 看看内存情况。 "

十分钟后:

```
内存使用:45MB (稳定)
运行时长:10 分钟
```

三十分钟后:

```
内存使用:52MB (稳定)
运行时长:30 分钟
```

一小时后:

```
内存使用:48MB (稳定)
运行时长:1 小时
```

两小时后:

```
内存使用:50MB (稳定)
运行时长:2 小时
状态:正常 ← 之前这个时候已经 1.2GB 了!
```

"成功了!" 老王兴奋地说,"内存保持在 50MB 左右, 非常健康。 "

用户反馈也开始涌入客服系统:

```
用户 A:"后台不卡了, 太好了!"
用户 B:"之前用一会儿就崩溃, 现在很流畅。 "
用户 C:"感觉页面响应速度变快了。 "
```

技术负责人老李在群里说:"这次修复做得很好。 WeakMap 和 WeakSet 是为这种场景专门设计的, 以后涉及 DOM 元素或临时对象的映射关系, 都应该考虑使用弱引用。 "

---

## 深入理解

晚上七点, 你回到工位, 整理今天学到的知识。

你在笔记本上写下 WeakMap 和 Map 的对比:

**WeakMap vs Map 对比表:**

| 特性 | WeakMap | Map |
|------|---------|-----|
| 键类型 | 必须是对象 | 任意类型 |
| 引用类型 | 弱引用 | 强引用 |
| 垃圾回收 | 自动清除 | 阻止回收 |
| 可遍历 | 否 (无 size/keys) | 是 |
| 序列化 | 不支持 | 支持 |
| 使用场景 | DOM 元数据、私有数据 | 一般键值对存储 |

**WeakSet vs Set 对比表:**

| 特性 | WeakSet | Set |
|------|---------|-----|
| 值类型 | 必须是对象 | 任意类型 |
| 引用类型 | 弱引用 | 强引用 |
| 垃圾回收 | 自动清除 | 阻止回收 |
| 可遍历 | 否 (无 size/values) | 是 |
| 使用场景 | 对象标记、访问追踪 | 唯一值集合 |

你又补充了一些实际应用场景:

**WeakMap 典型应用:**
- DOM 元素关联数据(事件处理器、用户数据等)
- 对象私有数据存储
- 对象缓存(自动清理)
- 对象实例与配置的映射

**WeakSet 典型应用:**
- 标记已处理的对象
- 追踪对象访问状态
- 防止循环引用
- 临时对象集合

你保存了文档, 决定明天的技术分享会上给大家详细讲解内存管理和弱引用的最佳实践。

---

## 知识总结

**规则 1: 强引用 vs 弱引用**

强引用会阻止垃圾回收, 弱引用不会。 WeakMap 和 WeakSet 使用弱引用, 当对象只被弱引用持有时, 可以被垃圾回收器回收。 这是防止内存泄漏的关键机制。

---

**规则 2: WeakMap 的限制**

WeakMap 的键必须是对象(不能是原始值), 不支持遍历(无 size、keys()、values()、entries()), 无法序列化。 这些限制都是为了配合垃圾回收机制而设计的。

---

**规则 3: WeakMap 的典型场景**

```javascript
// 场景 1:DOM 元素元数据
const metadata = new WeakMap();
metadata.set(element, { clicks:0, lastVisit:Date.now() });

// 场景 2:私有数据存储
const privateData = new WeakMap();
class User {
    constructor(name) {
        privateData.set(this, { password:'secret' });
    }
}

// 场景 3:对象缓存
const cache = new WeakMap();
function expensiveOperation(obj) {
    if (cache.has(obj)) return cache.get(obj);
    const result = /* 计算结果 */;
    cache.set(obj, result);
    return result;
}
```

元素/对象销毁时, 相关数据自动清除, 无需手动管理。

---

**规则 4: WeakSet 的应用**

WeakSet 用于标记和追踪对象, 不存储额外数据。 常见场景: 防止重复处理、追踪访问状态、循环引用检测。

```javascript
const processed = new WeakSet();

function process(obj) {
    if (processed.has(obj)) return;
    // 处理逻辑
    processed.add(obj);
}
```

对象销毁时, 标记自动清除。

---

**规则 5: 内存泄漏的预防**

| 场景 | 错误做法 | 正确做法 |
|------|---------|---------|
| DOM 元素数据 | Map 存储元素 | WeakMap 存储元素 |
| 对象标记 | Set 存储对象 | WeakSet 存储对象 |
| 事件监听器 | 未移除监听 | removeEventListener |
| 全局变量 | 大量全局引用 | 限制作用域 |

使用 WeakMap/WeakSet 是避免 DOM 相关内存泄漏的最佳实践。

---

**规则 6: 垃圾回收机制**

JavaScript 使用可达性(reachability)算法进行垃圾回收。 从根对象(window、document)出发, 通过引用链可达的对象会被保留, 不可达的对象会被回收。 WeakMap/WeakSet 的弱引用不计入可达性判断。

---

**事故档案编号**: OBJ-2024-1862
**影响范围**: WeakMap, WeakSet, 内存泄漏, 垃圾回收, DOM 元素引用
**根本原因**: 使用 Map 存储 DOM 元素导致强引用阻止垃圾回收, 造成严重内存泄漏
**修复成本**: 低(改用 WeakMap/WeakSet), 内存从 1.2GB 降至 50MB

这是 JavaScript 世界第 62 次被记录的内存管理事故。 WeakMap 和 WeakSet 使用弱引用, 不阻止垃圾回收。 WeakMap 键必须是对象, 用于存储对象元数据(DOM 数据、私有属性、缓存)。 WeakSet 用于对象标记和追踪。 两者都不支持遍历和序列化, 这是配合垃圾回收的设计。 强引用会阻止对象回收导致内存泄漏, 弱引用允许自动清理。 使用场景: DOM 元素关联数据优先 WeakMap, 对象标记优先 WeakSet。 理解强弱引用差异是避免内存泄漏的关键。

---

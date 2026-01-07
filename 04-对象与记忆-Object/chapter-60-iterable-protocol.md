《第 60 次记录：Iterable 协议 —— 可遍历的资格》

---

## 周末实验

周六下午两点，阳光透过窗户洒在键盘上。你决定利用周末时间研究一个有趣的问题：如何让自定义对象支持 `for...of` 循环。

这个想法来源于上周的一次代码审查。当时你看到老张写了一个 `Range` 类，可以像 Python 那样生成数字序列，但只能用 `forEach` 遍历。你当时就想：为什么数组可以用 `for...of`，自定义对象就不行呢？

你泡了一杯咖啡，打开电脑，开始实验。

首先，你尝试最直接的方式：

```javascript
class Range {
    constructor(start, end) {
        this.start = start;
        this.end = end;
    }
}

const range = new Range(1, 5);

// 尝试遍历
for (const num of range) {
    console.log(num);
}
```

控制台立刻报错：

```
TypeError:range is not iterable
```

"不可遍历（not iterable）？"你喃喃自语，"那什么才是可遍历的呢？"

你测试了几个内置类型：

```javascript
// 数组 - 可以
for (const item of [1, 2, 3]) {
    console.log(item); // 1, 2, 3
}

// 字符串 - 可以
for (const char of "abc") {
    console.log(char); // a, b, c
}

// Map - 可以
for (const [key, value] of new Map([['a', 1], ['b', 2]])) {
    console.log(key, value); // a 1, b 2
}

// 普通对象 - 不可以
for (const item of {a:1, b:2}) {
    console.log(item); // TypeError:object is not iterable
}
```

"有意思，"你若有所思，"数组、字符串、Map 都支持 `for...of`，但普通对象不支持。它们之间有什么共同点？"

---

## 探索协议

下午两点半，你开始查阅 MDN 文档。很快找到了答案：**Iterable 协议**。

文档说，一个对象要成为可遍历对象（iterable），必须实现 `Symbol.iterator` 方法。这个方法返回一个迭代器（iterator）对象。

"Symbol. iterator？"你好奇地打开控制台，检查数组：

```javascript
const arr = [1, 2, 3];

console.log(typeof arr[Symbol.iterator]); // "function"

// 手动调用迭代器
const iterator = arr[Symbol.iterator]();
console.log(iterator.next()); // {value:1, done:false}
console.log(iterator.next()); // {value:2, done:false}
console.log(iterator.next()); // {value:3, done:false}
console.log(iterator.next()); // {value:undefined, done:true}
```

"原来如此！"你恍然大悟，"`for...of` 循环底层就是不断调用 `next()` 方法，直到 `done` 为 `true`。"

你画了一张流程图：

```
for...of 循环的工作原理:
1.调用对象的 [Symbol.iterator]() 获取迭代器
2.反复调用迭代器的 next() 方法
3.每次 next() 返回 {value:值, done:布尔值}
4.当 done 为 true 时停止循环
```

"那我只需要给 `Range` 类实现这个协议就行了！"你兴奋地开始写代码。

---

## 实现迭代器

下午三点，你开始给 `Range` 类添加迭代器：

```javascript
class Range {
    constructor(start, end) {
        this.start = start;
        this.end = end;
    }

    [Symbol.iterator]() {
        let current = this.start;
        const end = this.end;

        return {
            next() {
                if (current <= end) {
                    return { value:current++, done:false };
                } else {
                    return { value:undefined, done:true };
                }
            }
        };
    }
}

const range = new Range(1, 5);

for (const num of range) {
    console.log(num);
}
// 输出:1, 2, 3, 4, 5
```

"成功了！"你激动地站起来。自定义对象真的可以用 `for...of` 遍历了！

但你很快发现了一个有趣的现象：

```javascript
// 多次遍历
for (const num of range) {
    console.log(num); // 1, 2, 3, 4, 5
}

for (const num of range) {
    console.log(num); // 1, 2, 3, 4, 5 - 又从头开始了
}
```

"每次 `for...of` 都会重新调用 `[Symbol.iterator]()`，所以可以多次遍历，"你记下笔记，"这和手动创建迭代器不同。"

你测试了手动迭代器的行为：

```javascript
const iterator = range[Symbol.iterator]();

console.log(iterator.next()); // {value:1, done:false}
console.log(iterator.next()); // {value:2, done:false}
console.log(iterator.next()); // {value:3, done:false}
console.log(iterator.next()); // {value:4, done:false}
console.log(iterator.next()); // {value:5, done:false}
console.log(iterator.next()); // {value:undefined, done:true}

// 已经消耗完毕，再调用只会返回 done:true
console.log(iterator.next()); // {value:undefined, done:true}
```

"迭代器是一次性的，"你总结道，"但 iterable 对象可以多次创建新的迭代器。"

---

## Generator 简化

下午四点，你在文档里看到了 Generator 函数，据说可以更简洁地实现迭代器。

"Generator？"你好奇地尝试：

```javascript
class Range {
    constructor(start, end) {
        this.start = start;
        this.end = end;
    }

    *[Symbol.iterator]() {
        for (let i = this.start;i <= this.end;i++) {
            yield i;
        }
    }
}

const range = new Range(1, 5);

for (const num of range) {
    console.log(num); // 1, 2, 3, 4, 5
}
```

"天啊，只需要加个星号 `*` 和 `yield` 关键字，代码简洁了一半！"你惊叹道。

你测试了 Generator 的其他用法：

```javascript
// 无限序列
class InfiniteSequence {
    constructor(start = 0) {
        this.start = start;
    }

    *[Symbol.iterator]() {
        let i = this.start;
        while (true) {
            yield i++;
        }
    }
}

const seq = new InfiniteSequence(1);
const iterator = seq[Symbol.iterator]();

console.log(iterator.next()); // {value:1, done:false}
console.log(iterator.next()); // {value:2, done:false}
console.log(iterator.next()); // {value:3, done:false}
// 可以无限生成
```

"无限序列！"你兴奋地说，"这在传统迭代器里需要很复杂的逻辑，Generator 几行就搞定了。"

你又尝试了斐波那契数列：

```javascript
class Fibonacci {
    *[Symbol.iterator]() {
        let [prev, curr] = [0, 1];
        while (true) {
            yield curr;
            [prev, curr] = [curr, prev + curr];
        }
    }
}

const fib = new Fibonacci();
const fibIterator = fib[Symbol.iterator]();

// 获取前 10 个斐波那契数
for (let i = 0;i < 10;i++) {
    console.log(fibIterator.next().value);
}
// 输出:1, 1, 2, 3, 5, 8, 13, 21, 34, 55
```

"太优雅了，"你赞叹，"Generator 把复杂的状态管理变得如此简单。"

---

## 实际应用

下午五点，你开始思考实际项目中如何使用这个特性。

你想起上周写的分页数据获取类，当时用的是回调函数，很不优雅。现在可以用迭代器改写：

```javascript
class PagedData {
    constructor(data, pageSize = 10) {
        this.data = data;
        this.pageSize = pageSize;
    }

    *[Symbol.iterator]() {
        for (let i = 0;i < this.data.length;i += this.pageSize) {
            yield this.data.slice(i, i + this.pageSize);
        }
    }
}

// 使用
const allData = Array.from({length:25}, (_, i) => i + 1);
const paged = new PagedData(allData, 10);

for (const page of paged) {
    console.log('页面数据:', page);
}
// 输出:
// 页面数据:[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
// 页面数据:[11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
// 页面数据:[21, 22, 23, 24, 25]
```

"完美！"你满意地点头，"现在分页逻辑清晰多了。"

你还实现了一个树遍历器：

```javascript
class TreeNode {
    constructor(value, children = []) {
        this.value = value;
        this.children = children;
    }

    // 深度优先遍历
    *[Symbol.iterator]() {
        yield this.value;
        for (const child of this.children) {
            yield* child; // 递归 yield 子节点
        }
    }
}

// 创建树结构
const tree = new TreeNode('root', [
    new TreeNode('child1', [
        new TreeNode('grandchild1'),
        new TreeNode('grandchild2')
    ]),
    new TreeNode('child2')
]);

// 遍历整棵树
for (const node of tree) {
    console.log(node);
}
// 输出:root, child1, grandchild1, grandchild2, child2
```

"用 `yield*` 委托给子迭代器，太巧妙了！"你感叹道。

---

## 展开运算符

傍晚六点，你突然想到：既然 `for...of` 依赖 Iterable 协议，那展开运算符和 `Array.from()` 是不是也一样？

```javascript
const range = new Range(1, 5);

// 展开运算符
const arr1 = [...range];
console.log(arr1); // [1, 2, 3, 4, 5]

// Array.from
const arr2 = Array.from(range);
console.log(arr2); // [1, 2, 3, 4, 5]

// 解构赋值
const [first, second, ...rest] = range;
console.log(first, second, rest); // 1, 2, [3, 4, 5]
```

"果然！"你兴奋地记录，"所有依赖遍历的语法特性都用 Iterable 协议。"

你测试了更多场景：

```javascript
// Set 构造函数
const set = new Set(range);
console.log(set); // Set(5) {1, 2, 3, 4, 5}

// Promise.all
const promises = [...range].map(n => Promise.resolve(n * 2));
Promise.all(promises).then(results => {
    console.log(results); // [2, 4, 6, 8, 10]
});

// Math.max
const max = Math.max(...range);
console.log(max); // 5
```

"Iterable 协议的威力远超我想象，"你在笔记本上写下，"它是 JavaScript 中很多高级特性的基础。"

---

## 周末收获

晚上八点，你合上笔记本，整理了一天的学习成果。

你在博客草稿里写下总结：

**今天学到的核心概念：**

1.**Iterable 协议**：对象只需实现 `Symbol.iterator` 方法，返回迭代器对象，就能被 `for...of` 遍历
2.**Iterator 协议**：迭代器对象必须有 `next()` 方法，返回 `{value, done}` 格式的对象
3.**Generator 函数**：用 `function*` 和 `yield` 简化迭代器实现，让代码更简洁优雅
4.**应用场景**：分页数据、树遍历、无限序列、惰性求值等都可以用迭代器优雅实现

你看着窗外的夜色，感觉很充实。周末的实验不仅解决了当初的疑惑，还打开了一扇新的大门。

"下周一要把这个分享给团队，"你想，"尤其是那个分页数据的例子，应该能帮到大家。"

---

## Iterable 协议知识

**规则 1: Iterable 协议定义**

一个对象要成为可遍历对象（iterable），必须实现 `Symbol.iterator` 方法。该方法返回一个迭代器对象，迭代器对象必须有 `next()` 方法，返回 `{value:任意值, done:布尔值}` 格式。

---

**规则 2: Iterator 协议要求**

迭代器的 `next()` 方法每次调用返回一个对象：
- `value`: 当前迭代的值（可以是任意类型）
- `done`: 布尔值，`true` 表示迭代完成，`false` 表示还有值

当 `done` 为 `true` 时，`value` 通常为 `undefined`，此时迭代器已消耗完毕。

---

**规则 3: 内置 Iterable 对象**

JavaScript 内置的可遍历对象包括：

| 类型 | 说明 | 示例 |
|------|------|------|
| Array | 数组 | `[1, 2, 3]` |
| String | 字符串 | `"abc"` |
| Map | 键值对集合 | `new Map([['a', 1]])` |
| Set | 唯一值集合 | `new Set([1, 2, 3])` |
| TypedArray | 类型化数组 | `new Uint8Array([1, 2])` |
| arguments | 函数参数对象 | `function() { arguments }` |
| NodeList | DOM 节点列表 | `document.querySelectorAll('div')` |

注意：普通对象 `{}` 不是可遍历对象。

---

**规则 4: Generator 函数简化**

Generator 函数（`function*`）是实现迭代器的简洁方式，使用 `yield` 关键字产生值：

```javascript
*[Symbol.iterator]() {
    yield 1;
    yield 2;
    yield 3;
}
```

相当于手动实现迭代器返回 `{value:1, done:false}` 等，代码更简洁且支持复杂的控制流。

---

**规则 5: 依赖 Iterable 的语法**

以下语法特性都依赖 Iterable 协议：

```javascript
for...of 循环
展开运算符 [...]
解构赋值 [a, b] = iterable
Array.from()
Set/Map 构造函数
Promise.all/race
yield*
```

只要对象实现了 Iterable 协议，就能使用所有这些特性。

---

**规则 6: Iterable vs Iterator 区别**

- **Iterable**（可遍历对象）：有 `[Symbol.iterator]()` 方法的对象，可以多次创建迭代器
- **Iterator**（迭代器）：有 `next()` 方法的对象，是一次性消耗的

一个对象可以同时是 Iterable 和 Iterator：

```javascript
const obj = {
    [Symbol.iterator]() {
        return this;
    },
    next() {
        // 迭代逻辑
    }
};
```

---

**事故档案编号**: OBJ-2024-1860
**影响范围**: Iterable 协议, Iterator 协议, Generator 函数, for... of 循环, 自定义遍历
**根本原因**: 不理解 Symbol. iterator 机制，无法让自定义对象支持遍历操作
**修复成本**: 低（实现协议即可），Generator 函数可大幅简化代码

这是 JavaScript 世界第 60 次被记录的对象协议事故。Iterable 协议要求对象实现 `[Symbol.iterator]()` 方法，返回迭代器对象。迭代器对象必须有 `next()` 方法，返回 `{value, done}` 格式。Generator 函数（`function*` 和 `yield`）可简化迭代器实现。内置可遍历对象包括 Array、String、Map、Set 等，但普通对象不可遍历。所有依赖遍历的语法（`for...of`、展开运算符、解构、`Array.from()` 等）都基于 Iterable 协议。理解协议机制，可以让自定义对象拥有与内置对象相同的遍历能力。

---

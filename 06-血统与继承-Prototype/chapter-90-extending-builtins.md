《第 90 次记录: 扩展内建类 —— 继承的陷阱》

---

## 自定义数组的需求

周三上午九点，你接到了一个看似简单的需求。

产品经理走到你的工位旁："我们需要一个特殊的数组类，能够自动记录所有的修改操作，用于实现撤销/重做功能。"

"听起来不难，" 你说，"继承 `Array` 类，重写 `push`、`pop` 等方法就行了。"

你很快写出了第一版实现：

```javascript
class HistoryArray extends Array {
    constructor(...items) {
        super(...items);
        this.history = []; // 记录操作历史
    }

    push(...items) {
        this.history.push({
            operation: 'push',
            items: items,
            timestamp: Date.now()
        });
        return super.push(...items);
    }

    pop() {
        const item = super.pop();
        this.history.push({
            operation: 'pop',
            item: item,
            timestamp: Date.now()
        });
        return item;
    }

    undo() {
        if (this.history.length === 0) {
            return;
        }

        const lastOp = this.history.pop();
        if (lastOp.operation === 'push') {
            // 撤销 push: 移除最后添加的元素
            for (let i = 0; i < lastOp.items.length; i++) {
                super.pop();
            }
        } else if (lastOp.operation === 'pop') {
            // 撤销 pop: 恢复被删除的元素
            super.push(lastOp.item);
        }
    }
}
```

你测试了基本功能：

```javascript
const arr = new HistoryArray(1, 2, 3);
console.log(arr); // HistoryArray [1, 2, 3]

arr.push(4);
arr.push(5);
console.log(arr); // HistoryArray [1, 2, 3, 4, 5]

arr.pop();
console.log(arr); // HistoryArray [1, 2, 3, 4]

arr.undo(); // 撤销 pop
console.log(arr); // HistoryArray [1, 2, 3, 4, 5]

arr.undo(); // 撤销 push(5)
console.log(arr); // HistoryArray [1, 2, 3, 4]
```

"完美！" 你满意地说，"ES6 的 `extends` 语法让继承内建类变得如此简单。"

---

## 隐藏的陷阱

上午十点，测试小林发现了第一个问题。

"你的 `HistoryArray` 有个 bug，" 小林说，"看这个测试："

```javascript
const arr = new HistoryArray(1, 2, 3);

// 使用 map 方法
const doubled = arr.map(x => x * 2);

console.log(doubled); // HistoryArray [2, 4, 6]
console.log(doubled.history); // undefined - 历史记录丢失了！
```

"什么？" 你困惑了，"`map` 返回的也是 `HistoryArray` 实例，但 `history` 属性没有了？"

你检查了类型：

```javascript
console.log(doubled instanceof HistoryArray); // true
console.log(doubled instanceof Array); // true
console.log(doubled.constructor === HistoryArray); // true
```

"类型是对的，但实例没有被正确初始化，" 你意识到问题，"`map` 方法内部创建了新数组，但没有调用我们的 `constructor`。"

老张走过来看了看代码。

"这是继承内建类的常见陷阱，" 老张说，"内建方法返回新实例时，会尝试创建相同类型的对象，但不会调用你的构造函数逻辑。"

"那怎么办？" 你问。

"需要重写 `Symbol.species`，" 老张说：

```javascript
class HistoryArray extends Array {
    constructor(...items) {
        super(...items);
        this.history = [];
    }

    // 指定派生对象的构造函数
    static get [Symbol.species]() {
        return Array; // 返回普通 Array，而不是 HistoryArray
    }

    // 或者，如果想返回 HistoryArray，需要自己处理初始化
    map(fn) {
        const result = super.map(fn);
        // result 是 HistoryArray 实例，但 history 未初始化
        if (!result.history) {
            result.history = [];
        }
        return result;
    }
}
```

"但这样需要重写所有返回新数组的方法，" 你皱眉，"`map`、`filter`、`slice`、`concat` 等等，太多了。"

"对，" 老张说，"这就是为什么继承内建类很棘手。"

---

## Symbol.species 的作用

上午十一点，你深入研究了 `Symbol.species` 的机制。

"`Symbol.species` 决定了派生对象的构造函数，" 你总结：

```javascript
class MyArray extends Array {
    // 默认行为：返回派生类本身
    static get [Symbol.species]() {
        return MyArray;
    }
}

const arr = new MyArray(1, 2, 3);
const mapped = arr.map(x => x * 2);

console.log(mapped instanceof MyArray); // true
console.log(mapped.constructor === MyArray); // true

// 如果修改 Symbol.species
class SafeArray extends Array {
    static get [Symbol.species]() {
        return Array; // 返回普通 Array
    }
}

const safe = new SafeArray(1, 2, 3);
const safeMapped = safe.map(x => x * 2);

console.log(safeMapped instanceof SafeArray); // false
console.log(safeMapped instanceof Array); // true
console.log(safeMapped.constructor === Array); // true
```

"所以如果我想让 `map` 返回普通数组，" 你说，"就设置 `Symbol.species` 返回 `Array`。但如果想返回自定义类，就需要手动初始化。"

---

## 方法的意外行为

中午十二点，你又发现了一个问题。

```javascript
class DebugArray extends Array {
    constructor(...items) {
        super(...items);
        console.log('DebugArray 构造函数被调用');
    }

    push(...items) {
        console.log(`准备添加: ${items}`);
        return super.push(...items);
    }
}

const arr = new DebugArray(1, 2, 3);
// 'DebugArray 构造函数被调用'

// 使用 concat
const arr2 = arr.concat([4, 5]);
// 没有输出！concat 没有调用我们的 push

console.log(arr2); // DebugArray [1, 2, 3, 4, 5]
console.log(arr2 instanceof DebugArray); // true
```

"内建方法不会调用我们重写的方法，" 你发现，"`concat` 直接操作底层数组，不走我们的 `push`。"

测试小林补充："还有 `sort` 方法，也有奇怪的行为："

```javascript
class WeirdArray extends Array {
    constructor(...items) {
        super(...items);
        this.sortCount = 0;
    }

    // 尝试重写 sort
    sort(compareFn) {
        this.sortCount++;
        console.log(`第 ${this.sortCount} 次排序`);
        return super.sort(compareFn);
    }
}

const arr = new WeirdArray(3, 1, 2);
arr.sort();
// '第 1 次排序'

console.log(arr); // WeirdArray [1, 2, 3]
console.log(arr.sortCount); // 1

// 但是从其他方法返回的实例
const arr2 = arr.map(x => x);
arr2.sort();
// 没有输出！sortCount 未定义

console.log(arr2.sortCount); // undefined
```

---

## 长度属性的诡异行为

下午两点，你遇到了最诡异的问题。

```javascript
class Stack extends Array {
    constructor() {
        super();
        this.maxSize = 5;
    }

    push(item) {
        if (this.length >= this.maxSize) {
            throw new Error(`栈已满，最大容量 ${this.maxSize}`);
        }
        return super.push(item);
    }
}

const stack = new Stack();

stack.push(1);
stack.push(2);
stack.push(3);

console.log(stack); // Stack [1, 2, 3]

// 直接修改 length
stack.length = 10; // 绕过了 maxSize 限制！

console.log(stack.length); // 10
console.log(stack); // Stack [1, 2, 3, empty × 7]
```

"length 属性可以直接修改，" 你震惊了，"完全绕过了我们的容量检查！"

"而且更糟糕的是，" 小林说，"还可以用索引直接赋值："

```javascript
stack[99] = 'hacked';
console.log(stack.length); // 100 - length 自动增长
console.log(stack.maxSize); // 5 - maxSize 形同虚设
```

"这样的话，我们的容量限制根本没用，" 你沮丧地说。

---

## 组合优于继承

下午三点，老张建议你重新设计。

"继承内建类的问题太多了，" 老张说，"不如用组合方式实现。"

```javascript
// 不继承 Array，而是内部包含一个数组
class HistoryArray {
    constructor(...items) {
        this._array = [...items]; // 私有数组
        this._history = [];
    }

    get length() {
        return this._array.length;
    }

    push(...items) {
        this._history.push({
            operation: 'push',
            items: items,
            timestamp: Date.now()
        });
        return this._array.push(...items);
    }

    pop() {
        const item = this._array.pop();
        this._history.push({
            operation: 'pop',
            item: item,
            timestamp: Date.now()
        });
        return item;
    }

    map(fn) {
        // 完全控制返回值
        return new HistoryArray(...this._array.map(fn));
    }

    filter(fn) {
        return new HistoryArray(...this._array.filter(fn));
    }

    // 代理数组的迭代器
    [Symbol.iterator]() {
        return this._array[Symbol.iterator]();
    }

    // 支持索引访问
    get(index) {
        return this._array[index];
    }

    set(index, value) {
        this._history.push({
            operation: 'set',
            index: index,
            oldValue: this._array[index],
            newValue: value,
            timestamp: Date.now()
        });
        this._array[index] = value;
    }

    undo() {
        if (this._history.length === 0) {
            return;
        }

        const lastOp = this._history.pop();
        if (lastOp.operation === 'push') {
            for (let i = 0; i < lastOp.items.length; i++) {
                this._array.pop();
            }
        } else if (lastOp.operation === 'pop') {
            this._array.push(lastOp.item);
        } else if (lastOp.operation === 'set') {
            this._array[lastOp.index] = lastOp.oldValue;
        }
    }

    toArray() {
        return [...this._array];
    }
}
```

你测试了新的实现：

```javascript
const arr = new HistoryArray(1, 2, 3);

arr.push(4);
arr.push(5);

const mapped = arr.map(x => x * 2);
console.log(mapped instanceof HistoryArray); // true
console.log(mapped._history); // [] - 新实例有自己的历史

arr.set(0, 100);
console.log(arr.get(0)); // 100

arr.undo(); // 撤销 set
console.log(arr.get(0)); // 1

// 可以正常迭代
for (const item of arr) {
    console.log(item);
}
```

"现在完全在我们的控制之下了，" 你说，"没有内建类的诡异行为。"

---

## 什么时候可以继承内建类

下午四点，你总结了继承内建类的适用场景。

"并不是说不能继承内建类，" 老张说，"但要知道什么时候适合。"

**适合继承的场景：**

```javascript
// 场景 1: 只添加新方法，不修改现有行为
class MyArray extends Array {
    first() {
        return this[0];
    }

    last() {
        return this[this.length - 1];
    }

    random() {
        return this[Math.floor(Math.random() * this.length)];
    }
}

const arr = new MyArray(1, 2, 3, 4, 5);
console.log(arr.first()); // 1
console.log(arr.last()); // 5
console.log(arr.random()); // 随机元素

// 内建方法正常工作
const filtered = arr.filter(x => x > 2);
console.log(filtered instanceof MyArray); // true
```

**不适合继承的场景：**

1. 需要严格控制数据修改
2. 需要拦截所有操作
3. 需要保证数据一致性
4. 需要自定义序列化

"这些场景应该用组合，" 老张说。

---

## Proxy 的替代方案

下午五点，老张展示了另一种方案。

"如果想拦截所有操作，" 老张说，"可以用 `Proxy`："

```javascript
function createRestrictedArray(maxSize) {
    const arr = [];
    
    return new Proxy(arr, {
        set(target, property, value) {
            if (property === 'length') {
                if (value > maxSize) {
                    throw new Error(`长度不能超过 ${maxSize}`);
                }
            } else if (property === String(parseInt(property))) {
                // 是数字索引
                if (parseInt(property) >= maxSize) {
                    throw new Error(`索引不能超过 ${maxSize - 1}`);
                }
            }
            
            return Reflect.set(target, property, value);
        }
    });
}

const arr = createRestrictedArray(5);

arr.push(1, 2, 3);
console.log(arr); // [1, 2, 3]

try {
    arr.push(4, 5, 6); // 会触发 length = 6
} catch (e) {
    console.error(e.message); // '长度不能超过 5'
}

try {
    arr[10] = 'hacked';
} catch (e) {
    console.error(e.message); // '索引不能超过 4'
}
```

"Proxy 可以拦截几乎所有操作，" 老张说，"但性能开销比直接继承大。"

---

## 总结与反思

下午六点，你重新审视了需求，决定采用组合方案。

你在技术文档中写下教训：

**继承内建类的问题：**
1. 派生方法返回新实例时，不调用构造函数
2. 内建方法不调用重写的方法
3. `length` 和索引访问无法拦截
4. `Symbol.species` 机制复杂且容易出错

**推荐方案：**
1. **简单扩展**：只添加辅助方法 → 继承内建类
2. **复杂逻辑**：需要控制数据修改 → 组合模式
3. **完全拦截**：需要拦截所有操作 → Proxy 模式

**组合模式的优势：**
- 完全控制内部行为
- 明确的 API 边界
- 更好的封装性
- 避免内建类的诡异行为

"组合优于继承，" 你关上笔记本，"这句话在 JavaScript 的内建类上尤其正确。"

---

## 知识总结

**规则 1: 内建方法不调用重写的方法**

继承内建类并重写方法时，内建方法不会调用你的重写版本：

```javascript
class MyArray extends Array {
    push(item) {
        console.log('自定义 push');
        return super.push(item);
    }
}

const arr = new MyArray(1, 2);
arr.concat([3]); // concat 不调用我们的 push
```

内建方法直接操作底层数据结构。

---

**规则 2: Symbol.species 控制派生实例**

`Symbol.species` 决定派生方法返回的实例类型：

```javascript
class MyArray extends Array {
    static get [Symbol.species]() {
        return Array; // map/filter 返回普通 Array
    }
}

const arr = new MyArray(1, 2, 3);
const mapped = arr.map(x => x * 2);
console.log(mapped instanceof Array); // true
console.log(mapped instanceof MyArray); // false
```

默认返回派生类本身，但派生实例未完整初始化。

---

**规则 3: length 和索引无法完全控制**

继承 Array 时，无法完全控制 `length` 属性和索引访问：

```javascript
class LimitedArray extends Array {
    push(item) {
        if (this.length >= 10) throw new Error('已满');
        return super.push(item);
    }
}

const arr = new LimitedArray();
arr.length = 100; // 绕过限制
arr[50] = 'hacked'; // 绕过 push
```

---

**规则 4: 组合优于继承内建类**

对于复杂逻辑，用组合模式而非继承：

```javascript
class CustomArray {
    constructor() {
        this._arr = []; // 内部包含数组
    }

    push(item) {
        // 完全控制行为
        this._arr.push(item);
    }

    // 代理需要的方法
}
```

组合提供更好的控制和封装。

---

**规则 5: 继承适用于简单扩展**

只添加辅助方法时，继承内建类是安全的：

```javascript
class MyArray extends Array {
    first() { return this[0]; }
    last() { return this[this.length - 1]; }
}
```

不修改现有行为，不会遇到陷阱。

---

**规则 6: Proxy 实现完全拦截**

需要拦截所有操作时，用 Proxy：

```javascript
const arr = new Proxy([], {
    set(target, prop, value) {
        // 拦截所有赋值操作
        return Reflect.set(target, prop, value);
    }
});
```

Proxy 能拦截 `length` 和索引访问，但有性能开销。

---

**事故档案编号**: PROTO-2024-1890
**影响范围**: 内建类继承, Symbol.species, 组合模式, Proxy
**根本原因**: 继承内建类时不了解其特殊行为，导致重写方法失效
**修复成本**: 中（重构为组合），需理解内建类的限制

这是 JavaScript 世界第 90 次被记录的内建类继承事故。继承内建类（Array, Error, Map 等）有诸多陷阱：内建方法不调用重写的方法，派生方法返回的实例未完整初始化，`length` 和索引访问无法拦截。`Symbol.species` 控制派生实例类型但机制复杂。简单扩展（只添加辅助方法）可以继承，复杂逻辑应用组合模式。组合提供完全控制、明确 API、更好封装。Proxy 可拦截所有操作但有性能开销。组合优于继承，在内建类上尤其正确。

---

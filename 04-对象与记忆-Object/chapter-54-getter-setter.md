《第54次记录: Getter/Setter魔法 —— 周末的响应式实验》

---

## 周末好奇

周六上午十点, 你坐在家里的书桌前, 窗外阳光明媚。一杯热咖啡, 一台笔记本, 没有工作的压力, 只有周末的闲适。

昨晚你看了一篇关于Vue响应式原理的文章, 被它的巧妙设计深深吸引。"数据一改, 视图就自动更新, 这是怎么做到的?"你一直在想这个问题。

今天是周末, 没有deadline, 没有需求, 没有code review。你决定做个小实验, 自己动手实现一个迷你版的响应式系统, 纯粹是为了满足好奇心。

"试试看能不能做出来。"你兴奋地打开代码编辑器, 新建了一个文件`reactive. js`。

窗外传来鸟叫声, 咖啡的香气弥漫在房间里。这种周末的编程时光, 没有任何压力, 只有纯粹的创造乐趣, 是你最喜欢的状态。

你从最简单的场景开始: 一个用户对象, 当姓名改变时, 自动更新页面上的显示。

"先看看getter和setter是什么。"你打开MDN文档, 一边看一边在纸上画图。咖啡慢慢变凉, 但你完全沉浸在这个小实验里, 享受着探索的快乐。

这不是工作, 这是周末的技术娱乐。没有人催你, 没有bug要修, 没有用户投诉。你可以慢慢实验, 失败了也无所谓, 成功了就会很有成就感。

"来, 试试第一个版本。"你开始敲代码。

---

## 动手实验

上午十点半, 你写下了第一个实验:

```javascript
// 实验1: 最基础的getter和setter
const user = {
    firstName: 'Zhang',
    lastName: 'San',

    // getter: 读取fullName时自动计算
    get fullName() {
        console. log('正在计算fullName...');
        return `${this. firstName} ${this. lastName}`;
    },

    // setter: 设置fullName时自动拆分
    set fullName(value) {
        console. log('正在设置fullName...');
        const parts = value. split(' ');
        this. firstName = parts[0];
        this. lastName = parts[1];
    }
};

console. log(user. fullName); // '正在计算fullName...' → 'Zhang San'
user. fullName = 'Li Si';    // '正在设置fullName...'
console. log(user. firstName); // 'Li'
console. log(user. lastName);  // 'Si'
```

"哇, 成功了!"你兴奋地看着控制台输出。getter让你可以像访问普通属性一样访问计算属性, setter让你可以在赋值时执行自定义逻辑。

"有意思, 接下来试试数据验证。"你端起咖啡, 喝了一口, 继续实验:

```javascript
// 实验2: 用setter做数据验证
class User {
    constructor(age) {
        this._age = age; // 内部存储, 用下划线标识
    }

    get age() {
        return this._age;
    }

    set age(value) {
        if (typeof value !== 'number') {
            throw new TypeError('年龄必须是数字');
        }
        if (value < 0 || value > 150) {
            throw new RangeError('年龄必须在0-150之间');
        }
        this._age = value;
    }
}

const person = new User(25);
console. log(person. age); // 25
person. age = 30;         // ✓ 成功
// person. age = 'abc';   // ✗ TypeError
// person. age = -5;      // ✗ RangeError
```

"太棒了! 这样就能保证数据的有效性。"你在笔记本上记录下这个模式。

上午十一点, 你开始挑战更有趣的东西: 响应式系统。"当数据改变时, 自动执行某些操作, 就像Vue那样。"

```javascript
// 实验3: 简单的响应式系统
function reactive(obj, callback) {
    return new Proxy(obj, {
        get(target, property) {
            console. log(`读取属性: ${property}`);
            return target[property];
        },
        set(target, property, value) {
            console. log(`设置属性: ${property} = ${value}`);
            target[property] = value;
            callback(property, value); // 数据变化时执行回调
            return true;
        }
    });
}

const data = reactive({ count: 0 }, (prop, val) => {
    console. log(`数据变化! ${prop} 的新值是 ${val}`);
    document. querySelector('#display'). textContent = val;
});

data. count = 10;
// 输出:
// 设置属性: count = 10
// 数据变化! count 的新值是 10
// (页面自动更新)
```

"成功了!"你站起来伸了个懒腰, 看着屏幕上运行的代码, 满意地笑了。

中午十二点, 你决定再优化一下, 加上计算属性的支持:

```javascript
// 实验4: 带计算属性的响应式
class Reactive {
    constructor(data) {
        this._data = data;
        this._computed = {};
    }

    defineComputed(key, getter) {
        Object. defineProperty(this, key, {
            get() {
                // 缓存计算结果
                if (! this._computed[key]) {
                    this._computed[key] = getter. call(this);
                }
                return this._computed[key];
            },
            enumerable: true
        });
    }

    set(key, value) {
        this._data[key] = value;
        this._computed = {}; // 清空缓存, 重新计算
        console. log(`${key} 更新为 ${value}`);
    }

    get(key) {
        return this._data[key];
    }
}

const store = new Reactive({
    price: 100,
    quantity: 2
});

store. defineComputed('total', function() {
    console. log('计算total...');
    return this. get('price') * this. get('quantity');
});

console. log(store. total); // '计算total...' → 200
console. log(store. total); // 200 (使用缓存, 不重新计算)

store. set('quantity', 3);
console. log(store. total); // '计算total...' → 300 (重新计算)
```

"完美!"你看着运行结果, 觉得特别有成就感。这不是为了工作, 纯粹是为了学习和探索, 但这种感觉比完成工作任务更让人愉悦。

---

## 实验收获

下午两点, 你整理了一上午的实验成果, 总结出getter/setter的几种典型用法:

**用法1: 计算属性**

```javascript
const rectangle = {
    width: 10,
    height: 5,

    get area() {
        return this. width * this. height; // 动态计算
    }
};

console. log(rectangle. area); // 50
rectangle. width = 20;
console. log(rectangle. area); // 100 (自动更新)
```

**用法2: 数据验证**

```javascript
class Product {
    constructor(price) {
        this._price = price;
    }

    get price() {
        return this._price;
    }

    set price(value) {
        if (value < 0) {
            throw new Error('价格不能为负数');
        }
        this._price = value;
        console. log(`价格已更新为 ${value}`);
    }
}
```

**用法3: 属性别名**

```javascript
class Person {
    constructor(firstName, lastName) {
        this. firstName = firstName;
        this. lastName = lastName;
    }

    // 提供友好的别名
    get name() {
        return this. fullName;
    }

    get fullName() {
        return `${this. firstName} ${this. lastName}`;
    }

    set name(value) {
        this. fullName = value;
    }

    set fullName(value) {
        [this. firstName, this. lastName] = value. split(' ');
    }
}
```

**用法4: 响应式数据(简化版)**

```javascript
function reactive(data) {
    const listeners = [];

    return new Proxy(data, {
        set(target, key, value) {
            target[key] = value;
            // 通知所有监听器
            listeners. forEach(fn => fn(key, value));
            return true;
        }
    });

    // 返回订阅函数
    return {
        data: proxy,
        watch(fn) {
            listeners. push(fn);
        }
    };
}
```

---

## 技术笔记

**规则 1: getter基础语法**

```javascript
const obj = {
    // 数据属性
    _value: 42,

    // 访问器属性(getter)
    get value() {
        console. log('getter被调用');
        return this._value;
    }
};

obj. value;  // 'getter被调用' → 42
obj. value(); // ✗ TypeError: obj. value不是函数
```

getter看起来像属性, 但实际上是函数。

---

**规则 2: setter基础语法**

```javascript
const obj = {
    _value: 0,

    get value() {
        return this._value;
    },

    set value(newValue) {
        console. log(`setter被调用, 新值: ${newValue}`);
        this._value = newValue;
    }
};

obj. value = 10; // 'setter被调用, 新值: 10'
console. log(obj. value); // 10
```

setter在赋值时自动调用, 可以执行验证、转换等操作。

---

**规则 3: getter/setter与普通属性的区别**

```javascript
const obj = {
    // 普通属性
    name: 'Alice',

    // 访问器属性
    get greeting() {
        return `Hello, ${this. name}`;
    }
};

// 描述符不同
Object. getOwnPropertyDescriptor(obj, 'name');
// {
//   value: 'Alice',
//   writable: true,
//   enumerable: true,
//   configurable: true
// }

Object. getOwnPropertyDescriptor(obj, 'greeting');
// {
//   get: [Function: get greeting],
//   set: undefined,
//   enumerable: true,
//   configurable: true
// }
```

访问器属性没有`value`和`writable`, 有`get`和`set`。

---

**规则 4: 用Object. defineProperty定义getter/setter**

```javascript
const obj = { _count: 0 };

Object. defineProperty(obj, 'count', {
    get() {
        console. log('读取count');
        return this._count;
    },
    set(value) {
        console. log('设置count');
        this._count = value;
    },
    enumerable: true,
    configurable: true
});

obj. count = 10; // '设置count'
console. log(obj. count); // '读取count' → 10
```

---

**规则 5: 计算属性模式**

```javascript
class Circle {
    constructor(radius) {
        this. radius = radius;
    }

    // 计算属性: 面积
    get area() {
        return Math. PI * this. radius ** 2;
    }

    // 计算属性: 周长
    get circumference() {
        return 2 * Math. PI * this. radius;
    }

    // 反向计算: 根据面积设置半径
    set area(value) {
        this. radius = Math. sqrt(value / Math. PI);
    }
}

const circle = new Circle(5);
console. log(circle. area);          // 78. 54
console. log(circle. circumference); // 31. 42

circle. area = 100; // 根据面积反算半径
console. log(circle. radius); // 5. 64
```

---

**规则 6: 数据验证模式**

```javascript
class BankAccount {
    constructor(balance) {
        this._balance = balance;
    }

    get balance() {
        return this._balance;
    }

    set balance(amount) {
        // 验证1: 类型检查
        if (typeof amount !== 'number') {
            throw new TypeError('余额必须是数字');
        }

        // 验证2: 范围检查
        if (amount < 0) {
            throw new RangeError('余额不能为负');
        }

        // 验证3: 业务逻辑
        if (amount > 1000000) {
            console. warn('大额余额, 需要审核');
        }

        this._balance = amount;
    }
}
```

---

**规则 7: 缓存计算结果**

```javascript
class DataProcessor {
    constructor(data) {
        this._data = data;
        this._cache = null;
    }

    get processedData() {
        // 如果有缓存, 直接返回
        if (this._cache) {
            console. log('使用缓存');
            return this._cache;
        }

        // 否则计算并缓存
        console. log('计算中...');
        this._cache = this._data. map(x => x * 2);
        return this._cache;
    }

    // 数据更新时清空缓存
    updateData(newData) {
        this._data = newData;
        this._cache = null; // 清空缓存
    }
}

const processor = new DataProcessor([1, 2, 3]);
console. log(processor. processedData); // '计算中...' → [2, 4, 6]
console. log(processor. processedData); // '使用缓存' → [2, 4, 6]
```

---

**事故档案编号**: OBJ-2024-1754
**影响范围**: 数据封装, 计算属性, 响应式系统
**根本原因**: 探索getter/setter的魔法, 理解访问器属性的强大功能
**修复成本**: 无(周末实验, 纯学习)

这是JavaScript世界第54次被记录的getter/setter探索。getter/setter是JavaScript的访问器属性, 让你可以在读取或设置属性时执行自定义逻辑。getter用于计算属性、延迟加载、缓存优化; setter用于数据验证、转换、触发副作用。理解并善用getter/setter, 是构建响应式系统、实现优雅API设计的关键。周末的小实验, 让你领略到了这个看似简单的特性背后的强大魔法。

---

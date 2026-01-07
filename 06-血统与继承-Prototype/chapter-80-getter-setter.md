《第 80 次记录: getter / setter —— 访问的拦截》

---

## 数据验证的需求

周三上午九点，产品经理小刘又来找你了。

"上次的用户系统做得不错，" 小刘说，"但我发现了一个问题。用户可以把年龄设置成负数或者 200 岁，这明显不合理。我们需要对输入数据进行验证。"

"没问题，" 你说，"我可以写一个 `setAge` 方法来验证。"

```javascript
// user.js - 用户类
class User {
    constructor(name, age) {
        this.name = name;
        this._age = age;
    }

    setAge(age) {
        if (age < 0 || age > 150) {
            throw new Error('年龄必须在 0-150 之间');
        }
        this._age = age;
    }

    getAge() {
        return this._age;
    }
}

const user = new User('张三', 25);
user.setAge(30); // 正常
console.log(user.getAge()); // 30
```

"这样可以工作，" 你说，"但问题是..."

你还没说完，前端小王就指出了问题: "但是其他开发者可能忘记用 `setAge`，直接修改 `user._age`，验证就失效了。"

```javascript
user._age = -10; // 直接修改，绕过验证
console.log(user.getAge()); // -10 - 验证失效!
```

"对，" 你皱眉，"怎么才能强制所有人都走验证逻辑呢?"

---

## getter 和 setter 登场

上午十点，老张听说了你的困扰。

"你需要的是访问器属性，" 老张说，"getter 和 setter 可以让你在读写属性时插入自定义逻辑。"

"访问器属性?" 你有点陌生。

"对，" 老张打开浏览器控制台，"属性有两种类型: 数据属性和访问器属性。你一直用的是数据属性，现在来看访问器属性。"

他写下演示代码:

```javascript
const user = {
    firstName: '三',
    lastName: '张',

    // getter - 读取 fullName 时调用
    get fullName() {
        return this.lastName + this.firstName;
    },

    // setter - 设置 fullName 时调用
    set fullName(value) {
        [this.lastName, this.firstName] = value.split('');
    }
};

console.log(user.fullName); // '张三' - 调用 getter
user.fullName = '李四';      // 调用 setter
console.log(user.firstName); // '四'
console.log(user.lastName);  // '李'
```

"看到了吗?" 老张指着代码，"`fullName` 看起来像普通属性，但读写时会调用对应的函数。这就是访问器属性的魔法。"

"太聪明了!" 你说，"这样就可以在读写时插入验证逻辑，而且使用方式和普通属性一样。"

---

## 重构年龄验证

上午十一点，你开始用 getter/setter 重构用户类。

```javascript
// user-improved.js - 改进的用户类
class User {
    constructor(name, age) {
        this.name = name;
        this._age = age; // 用下划线表示内部存储
    }

    // getter - 读取 age 时调用
    get age() {
        return this._age;
    }

    // setter - 设置 age 时调用
    set age(value) {
        if (typeof value !== 'number') {
            throw new TypeError('年龄必须是数字');
        }
        if (value < 0 || value > 150) {
            throw new RangeError('年龄必须在 0-150 之间');
        }
        this._age = value;
    }
}

const user = new User('张三', 25);

// 使用起来像普通属性
console.log(user.age); // 25 - 调用 getter

user.age = 30; // 调用 setter，验证通过
console.log(user.age); // 30

// 无效数据会被拒绝
try {
    user.age = -10; // RangeError: 年龄必须在 0-150 之间
} catch (e) {
    console.error(e.message);
}

try {
    user.age = '三十'; // TypeError: 年龄必须是数字
} catch (e) {
    console.error(e.message);
}
```

"完美!" 你说，"现在所有对 `age` 的读写都会经过验证，无法绕过。"

"但有个问题，" 前端小王指出，"其他人还是可以直接修改 `_age` 属性啊。"

```javascript
user._age = -10; // 还是可以绕过验证
```

"对，" 老张说，"按惯例，下划线开头的属性表示'私有'，不应该从外部访问。但这只是约定，不是强制的。真正的私有字段要用 `#` 前缀，后面章节会讲到。"

---

## defineProperty 定义访问器

上午十一点半，老张展示了另一种定义 getter/setter 的方式。

"除了在类或对象字面量中定义，" 老张说，"还可以用 `Object.defineProperty()` 动态添加访问器。"

```javascript
const config = {
    _timeout: 5000
};

Object.defineProperty(config, 'timeout', {
    get() {
        console.log('读取 timeout');
        return this._timeout;
    },
    set(value) {
        if (value < 1000) {
            throw new Error('超时不能小于 1000ms');
        }
        console.log(`设置 timeout 为 ${value}`);
        this._timeout = value;
    },
    enumerable: true,
    configurable: true
});

console.log(config.timeout); // 读取 timeout \n 5000
config.timeout = 10000;      // 设置 timeout 为 10000
```

"这种方式的好处是可以精确控制属性标志，" 老张解释，"比如设置 `enumerable: false` 让属性不出现在遍历中。"

你想到一个问题: "访问器属性和数据属性有什么区别?"

"核心区别是，" 老张说，"数据属性有 `value` 和 `writable`，访问器属性有 `get` 和 `set`。两者不能共存。"

```javascript
// 数据属性的描述符
{
    value: 123,
    writable: true,
    enumerable: true,
    configurable: true
}

// 访问器属性的描述符
{
    get: function() { ... },
    set: function(value) { ... },
    enumerable: true,
    configurable: true
}
```

---

## 计算属性的应用

中午十二点，你发现 getter 还有另一个强大的用途 —— 计算属性。

"我们的矩形类需要一个 `area` 属性，" 前端小王说，"表示矩形的面积。"

"如果用数据属性，" 你分析，"每次修改 `width` 或 `height` 都要手动更新 `area`，很容易出错。但如果用 getter，`area` 可以自动计算。"

```javascript
// rectangle.js - 矩形类
class Rectangle {
    constructor(width, height) {
        this.width = width;
        this.height = height;
    }

    // area 是计算属性，不需要存储
    get area() {
        return this.width * this.height;
    }

    get perimeter() {
        return 2 * (this.width + this.height);
    }
}

const rect = new Rectangle(10, 5);

console.log(rect.area);      // 50
console.log(rect.perimeter); // 30

// 修改尺寸，area 自动更新
rect.width = 20;
console.log(rect.area); // 100 - 自动重新计算
```

"这样 `area` 永远是准确的，" 你说，"不会出现数据不一致的问题。"

"而且不占用额外的存储空间，" 老张补充，"只在需要时才计算。这是一种延迟计算(lazy evaluation)的思想。"

---

## 只读属性的实现

下午两点，你遇到了一个新需求。

"订单对象的 `totalPrice` 属性应该是只读的，" 产品经理说，"不能让用户手动修改总价，必须根据商品价格自动计算。"

"用 getter 就可以实现只读属性，" 你说:

```javascript
// order.js - 订单类
class Order {
    constructor() {
        this.items = [];
    }

    addItem(name, price, quantity) {
        this.items.push({ name, price, quantity });
    }

    // 只提供 getter，不提供 setter
    get totalPrice() {
        return this.items.reduce((sum, item) => {
            return sum + item.price * item.quantity;
        }, 0);
    }
}

const order = new Order();
order.addItem('苹果', 5, 3);
order.addItem('香蕉', 3, 5);

console.log(order.totalPrice); // 30

// 尝试修改会静默失败(非严格模式)
order.totalPrice = 100;
console.log(order.totalPrice); // 还是 30

// 严格模式下会报错
'use strict';
order.totalPrice = 100; // TypeError: Cannot set property totalPrice
```

"完美，" 前端小王说，"`totalPrice` 看起来像普通属性，但其实是计算出来的，而且无法被修改。"

---

## 性能陷阱

下午三点，测试小林发现了一个性能问题。

"你的订单类在大量商品时很慢，" 小林说，"每次读取 `totalPrice` 都要重新计算所有商品价格。"

你测试了一下:

```javascript
const order = new Order();

// 添加 10000 个商品
for (let i = 0; i < 10000; i++) {
    order.addItem(`商品${i}`, Math.random() * 100, 1);
}

console.time('计算总价');
for (let i = 0; i < 1000; i++) {
    const price = order.totalPrice; // 每次都重新计算
}
console.timeEnd('计算总价'); // 计算总价: 2500ms
```

"确实很慢，" 你说，"每次读取都要遍历 10000 个商品。"

"可以用缓存优化，" 老张建议:

```javascript
// order-cached.js - 带缓存的订单类
class Order {
    constructor() {
        this.items = [];
        this._totalPriceCache = null;  // 缓存
        this._cacheValid = false;      // 缓存是否有效
    }

    addItem(name, price, quantity) {
        this.items.push({ name, price, quantity });
        this._cacheValid = false; // 数据变化，缓存失效
    }

    get totalPrice() {
        if (!this._cacheValid) {
            // 缓存失效，重新计算
            this._totalPriceCache = this.items.reduce((sum, item) => {
                return sum + item.price * item.quantity;
            }, 0);
            this._cacheValid = true;
        }
        return this._totalPriceCache;
    }
}

const order = new Order();

for (let i = 0; i < 10000; i++) {
    order.addItem(`商品${i}`, Math.random() * 100, 1);
}

console.time('计算总价(缓存)');
for (let i = 0; i < 1000; i++) {
    const price = order.totalPrice; // 只计算一次
}
console.timeEnd('计算总价(缓存)'); // 计算总价(缓存): 5ms
```

"性能提升了 500 倍!" 小林惊叹。

"但要注意，" 老张提醒，"缓存会增加代码复杂度，而且必须在数据变化时正确失效缓存。只有在计算开销很大时才值得用缓存。"

---

## setter 的副作用

下午四点，你发现 setter 还可以触发副作用。

"用户名修改时，我们需要记录日志，" 你说，"setter 正好可以做这件事。"

```javascript
// user-with-logging.js - 带日志的用户类
class User {
    constructor(name) {
        this._name = name;
        this.nameChangeHistory = [];
    }

    get name() {
        return this._name;
    }

    set name(value) {
        if (!value || value.trim().length === 0) {
            throw new Error('用户名不能为空');
        }

        const oldName = this._name;
        this._name = value;

        // 副作用: 记录变更历史
        this.nameChangeHistory.push({
            oldName,
            newName: value,
            timestamp: new Date()
        });

        console.log(`用户名从 '${oldName}' 改为 '${value}'`);
    }
}

const user = new User('张三');
user.name = '李四'; // 用户名从 '张三' 改为 '李四'
user.name = '王五'; // 用户名从 '李四' 改为 '王五'

console.log(user.nameChangeHistory);
// [
//   { oldName: '张三', newName: '李四', timestamp: ... },
//   { oldName: '李四', newName: '王五', timestamp: ... }
// ]
```

"这样所有的名字修改都会自动记录，" 你说，"实现了审计功能。"

"但要小心，" 老张警告，"setter 中的副作用可能导致意外的行为。比如触发事件、修改其他属性、发送网络请求等，这些都会增加代码的复杂性和不可预测性。"

---

## 兼容性问题

下午五点，运维老王提出了一个问题。

"我们的系统需要序列化用户对象到 JSON，" 老王说，"但 getter/setter 在序列化时会有问题吗?"

你测试了一下:

```javascript
const user = new User('张三', 25);

const json = JSON.stringify(user);
console.log(json);
// {"name":"张三","_age":25}

// 反序列化
const restored = JSON.parse(json);
console.log(restored.age); // undefined - getter 丢失了!
```

"`JSON.stringify()` 只序列化数据属性，" 老张解释，"访问器属性会被忽略。而且反序列化后得到的是普通对象，不是 `User` 实例，所以没有 getter/setter。"

"怎么解决?" 你问。

"如果需要序列化，" 老张说，"可以自定义 `toJSON()` 方法，或者用类的静态方法来恢复对象。"

```javascript
class User {
    constructor(name, age) {
        this.name = name;
        this._age = age;
    }

    get age() {
        return this._age;
    }

    set age(value) {
        if (value < 0 || value > 150) {
            throw new RangeError('年龄必须在 0-150 之间');
        }
        this._age = value;
    }

    // 自定义序列化
    toJSON() {
        return {
            name: this.name,
            age: this.age // 读取 getter 的值
        };
    }

    // 静态方法: 从 JSON 恢复
    static fromJSON(json) {
        return new User(json.name, json.age);
    }
}

const user1 = new User('张三', 25);
const json = JSON.stringify(user1);
console.log(json); // {"name":"张三","age":25}

const user2 = User.fromJSON(JSON.parse(json));
console.log(user2.age); // 25 - getter 恢复了
user2.age = 30; // setter 也恢复了
```

---

## 总结与反思

下午六点，你整理今天学到的知识。

**getter/setter 的核心价值:**
- 让属性访问可以插入自定义逻辑(验证、计算、日志等)
- 使用方式与普通属性一致，对外部透明
- 可以实现只读属性、计算属性、延迟计算等模式

**常见陷阱:**
- getter 中的计算开销可能很大，需要考虑缓存
- setter 中的副作用可能导致代码难以理解和调试
- 访问器属性不会被 `JSON.stringify()` 序列化
- 下划线前缀只是约定，不是真正的私有

**最佳实践:**
- 用 getter 实现计算属性和只读属性
- 用 setter 实现数据验证和格式化
- 避免在 getter/setter 中执行耗时操作
- 避免在 getter/setter 中产生意外的副作用

你保存了文档，明天准备继续学习原型系统。

---

## 知识总结

**规则 1: 访问器属性 vs 数据属性**

属性有两种类型: 数据属性(data property)和访问器属性(accessor property)，两者描述符不同且互斥:

```javascript
// 数据属性描述符
{ value: 123, writable: true, enumerable: true, configurable: true }

// 访问器属性描述符
{ get: function() {...}, set: function(v) {...}, enumerable: true, configurable: true }
```

访问器属性没有 `value` 和 `writable`，数据属性没有 `get` 和 `set`。

---

**规则 2: getter 定义和调用**

`get` 方法在读取属性时自动调用，返回值就是属性值:

```javascript
const obj = {
    get prop() {
        return '计算结果';
    }
};

console.log(obj.prop); // '计算结果' - 调用 getter
```

典型用途: 计算属性、只读属性、延迟计算。

---

**规则 3: setter 定义和调用**

`set` 方法在赋值属性时自动调用，参数是要设置的值:

```javascript
const obj = {
    _value: 0,
    set prop(val) {
        if (val < 0) throw new Error('不能为负数');
        this._value = val;
    }
};

obj.prop = 10; // 调用 setter
```

典型用途: 数据验证、格式化、触发副作用(日志、事件等)。

---

**规则 4: 只读属性的实现**

只提供 `get` 不提供 `set` 即为只读属性:

```javascript
class Circle {
    constructor(radius) {
        this.radius = radius;
    }

    get area() {
        return Math.PI * this.radius ** 2;
    }
    // 没有 setter
}

const circle = new Circle(5);
circle.area = 100; // 非严格模式: 静默失败
// 严格模式: TypeError
```

尝试修改只读属性在非严格模式下静默失败，严格模式下抛出 `TypeError`。

---

**规则 5: 性能考虑与缓存**

getter 中的计算会在每次读取时执行，高频访问可能成为性能瓶颈:

```javascript
class Expensive {
    get result() {
        return this.data.reduce(...); // 每次读取都计算
    }
}
```

解决方案: 缓存结果，在数据变化时失效缓存。平衡计算开销和缓存复杂度。

---

**规则 6: JSON 序列化问题**

`JSON.stringify()` 会忽略访问器属性，只序列化数据属性:

```javascript
const obj = {
    _value: 10,
    get value() { return this._value; }
};

JSON.stringify(obj); // '{"_value":10}' - value 被忽略
```

解决方案: 实现 `toJSON()` 方法自定义序列化，或用静态方法 `fromJSON()` 恢复对象。

---

**事故档案编号**: PROTO-2024-1880
**影响范围**: getter/setter, 访问器属性, 数据验证, 计算属性, JSON 序列化
**根本原因**: 不了解访问器属性机制，导致验证失效、性能问题或序列化错误
**修复成本**: 低(使用 getter/setter 实现数据保护), 需理解访问器语义和性能影响

这是 JavaScript 世界第 80 次被记录的属性访问事故。访问器属性通过 `get`/`set` 方法拦截属性读写，使用方式与数据属性一致但内部执行自定义逻辑。`get` 方法实现计算属性、只读属性和延迟计算，`set` 方法实现数据验证、格式化和副作用触发。访问器属性和数据属性互斥，描述符不同。性能注意: getter 中的计算每次读取都执行，高频访问需考虑缓存。JSON 序列化会忽略访问器属性，需实现 `toJSON()` 方法。下划线前缀(_prop)只是私有约定，不是语言级别的访问控制。理解访问器属性是实现数据封装、验证和计算的基础。

---

《第 107 次记录: 元编程的标准答案 —— Reflect 的统一接口》

---

## Proxy 的隐藏陷阱

周四上午九点, 你盯着昨天写的 Proxy 代码, 发现了一个奇怪的 bug。

这是你实现的一个响应式对象, 用于自动追踪数据变化。代码在大多数情况下都工作正常, 但有一个边缘案例让你困惑不解:

```javascript
const obj = {
    _value: 0,
    get value() {
        return this._value;
    },
    set value(v) {
        this._value = v;
    }
};

const proxy = new Proxy(obj, {
    get(target, prop) {
        console.log('读取:', prop);
        return target[prop];  // 直接返回属性
    },
    set(target, prop, value) {
        console.log('设置:', prop);
        target[prop] = value;
        return true;
    }
});

console.log(proxy.value);  // 期望输出 0
```

你运行代码, 控制台输出:

```
读取: value
0
```

"看起来没问题啊, " 你想。

但当你测试继承的场景时, 问题出现了:

```javascript
const child = Object.create(proxy);

console.log(child.value);  // 期望通过原型链读取 proxy.value
```

输出:

```
读取: value
undefined
```

"什么?!" 你惊讶, "为什么是 undefined?"

你调试了半小时, 终于发现问题所在: **getter 函数中的 `this` 指向错了**。当你直接返回 `target[prop]` 时, getter 内部的 `this` 指向的是原始对象 `target`, 而非代理对象 `proxy`。

"那应该怎么写?" 你困惑, "有没有一种标准的方式来正确处理这些操作?"

---

## Reflect 的登场

上午十点, 你在搜索解决方案时, 看到了一个陌生的 API: **Reflect**。

> **Reflect**: 一个内置对象, 提供拦截 JavaScript 操作的方法。这些方法与 Proxy 的 handler 方法相同。

"Reflect?" 你困惑, "这和 Proxy 有什么关系?"

你看到了文档中的解释:

```javascript
const proxy = new Proxy(obj, {
    get(target, prop, receiver) {
        console.log('读取:', prop);
        // ❌ 错误写法
        return target[prop];

        // ✅ 正确写法: 使用 Reflect
        return Reflect.get(target, prop, receiver);
    }
});
```

"什么是 `receiver`?" 你继续阅读文档:

> **receiver 参数**: 表示操作的接收者 (通常是代理对象本身或继承代理的对象)。使用 Reflect 并传入 receiver 可以确保 getter/setter 中的 `this` 指向正确。

你立刻修改了代码:

```javascript
const obj = {
    _value: 0,
    get value() {
        console.log('getter 内部的 this:', this === proxy);
        return this._value;
    }
};

const proxy = new Proxy(obj, {
    get(target, prop, receiver) {
        console.log('读取:', prop);
        return Reflect.get(target, prop, receiver);  // 传入 receiver
    }
});

console.log(proxy.value);
```

输出:

```
读取: value
getter 内部的 this: true
0
```

"成功了!" 你兴奋, "使用 `Reflect.get()` 并传入 `receiver`, getter 内部的 `this` 就指向了代理对象!"

你又测试了继承场景:

```javascript
const child = Object.create(proxy);
console.log(child.value);
```

输出:

```
读取: value
getter 内部的 this: false  (this 指向 child, 而非 proxy)
0
```

"完美!" 你说, "**Reflect 提供了正确处理 this 指向的标准方法**。"

---

## Reflect 的 13 种方法

上午十一点, 你开始系统学习 Reflect API。

"既然 Proxy 有 13 种拦截器, " 你想, "Reflect 应该也有对应的方法?"

你查阅文档, 发现 Reflect 确实提供了 13 种方法, 与 Proxy 的拦截器一一对应:

```javascript
// 1. Reflect.get(target, prop, receiver)
// 对应 Proxy 的 get 陷阱
const value = Reflect.get(obj, 'name');

// 2. Reflect.set(target, prop, value, receiver)
// 对应 Proxy 的 set 陷阱
const success = Reflect.set(obj, 'name', 'Alice');

// 3. Reflect.has(target, prop)
// 对应 Proxy 的 has 陷阱
const exists = Reflect.has(obj, 'name');

// 4. Reflect.deleteProperty(target, prop)
// 对应 Proxy 的 deleteProperty 陷阱
const deleted = Reflect.deleteProperty(obj, 'name');

// 5. Reflect.ownKeys(target)
// 对应 Proxy 的 ownKeys 陷阱
const keys = Reflect.ownKeys(obj);

// 6. Reflect.getOwnPropertyDescriptor(target, prop)
// 对应 Proxy 的 getOwnPropertyDescriptor 陷阱
const descriptor = Reflect.getOwnPropertyDescriptor(obj, 'name');

// 7. Reflect.defineProperty(target, prop, descriptor)
// 对应 Proxy 的 defineProperty 陷阱
const defined = Reflect.defineProperty(obj, 'name', { value: 'Alice' });

// 8. Reflect.preventExtensions(target)
// 对应 Proxy 的 preventExtensions 陷阱
const prevented = Reflect.preventExtensions(obj);

// 9. Reflect.getPrototypeOf(target)
// 对应 Proxy 的 getPrototypeOf 陷阱
const proto = Reflect.getPrototypeOf(obj);

// 10. Reflect.setPrototypeOf(target, proto)
// 对应 Proxy 的 setPrototypeOf 陷阱
const set = Reflect.setPrototypeOf(obj, null);

// 11. Reflect.isExtensible(target)
// 对应 Proxy 的 isExtensible 陷阱
const extensible = Reflect.isExtensible(obj);

// 12. Reflect.apply(fn, thisArg, args)
// 对应 Proxy 的 apply 陷阱
const result = Reflect.apply(Math.max, null, [1, 2, 3]);

// 13. Reflect.construct(Fn, args)
// 对应 Proxy 的 construct 陷阱
const instance = Reflect.construct(Date, [2024, 0, 1]);
```

"每个 Reflect 方法都对应一个 Proxy 陷阱, " 你总结, "**Reflect 提供了 JavaScript 元操作的标准 API**。"

你注意到一个关键特性: **Reflect 方法返回布尔值或结果, 而非抛出异常**。

```javascript
// Object 方法: 失败时抛出异常
try {
    Object.defineProperty(obj, 'name', { value: 'Alice' });
} catch (e) {
    console.error('定义失败');
}

// Reflect 方法: 失败时返回 false
const success = Reflect.defineProperty(obj, 'name', { value: 'Alice' });
if (!success) {
    console.error('定义失败');
}
```

"Reflect 更加函数式, " 你说, "不依赖异常处理, 而是通过返回值表示成功或失败。"

---

## Reflect 与 Object 的对比

中午十二点, 你开始对比 Reflect 和传统 Object 方法的区别。

"很多 Reflect 方法和 Object 方法功能相同, " 你想, "为什么要重复提供?"

你测试了几个对比:

```javascript
const obj = { name: 'Alice', age: 25 };

// 1. 属性读取
console.log(obj.name);  // 传统方式
console.log(obj['name']);  // 传统方式
console.log(Reflect.get(obj, 'name'));  // Reflect 方式

// 2. 属性设置
obj.age = 26;  // 传统方式
Reflect.set(obj, 'age', 26);  // Reflect 方式

// 3. 检查属性存在
console.log('name' in obj);  // 传统方式
console.log(Reflect.has(obj, 'name'));  // Reflect 方式

// 4. 删除属性
delete obj.age;  // 传统方式
Reflect.deleteProperty(obj, 'age');  // Reflect 方式

// 5. 获取属性列表
console.log(Object.keys(obj));  // Object 方法
console.log(Reflect.ownKeys(obj));  // Reflect 方法
```

"看起来功能相同, " 你说, "但有一些关键区别。"

你总结了主要差异:

### 差异 1: 返回值更合理

```javascript
const obj = {};

// Object.defineProperty: 返回对象本身
const result1 = Object.defineProperty(obj, 'name', {
    value: 'Alice',
    writable: false
});
console.log(result1 === obj);  // true

// Reflect.defineProperty: 返回布尔值表示是否成功
const result2 = Reflect.defineProperty(obj, 'age', {
    value: 25,
    writable: false
});
console.log(result2);  // true (表示成功)
```

### 差异 2: 函数式风格

```javascript
const obj = { name: 'Alice' };

// 传统方式: 操作符风格
delete obj.name;

// Reflect 方式: 函数式风格
Reflect.deleteProperty(obj, 'name');

// 函数式风格的好处: 可以传递给其他函数
const operations = [
    (obj, prop) => Reflect.deleteProperty(obj, prop),
    (obj, prop) => Reflect.has(obj, prop)
];
```

### 差异 3: 更完整的功能

```javascript
// Reflect.ownKeys() 返回所有属性, 包括 Symbol
const obj = {
    name: 'Alice',
    [Symbol('id')]: 123
};

console.log(Object.keys(obj));  // ['name'] - 只有字符串键
console.log(Reflect.ownKeys(obj));  // ['name', Symbol(id)] - 包括 Symbol
```

"Reflect 是对旧有 Object 方法的改进和统一, " 你恍然大悟, "**提供了更一致、更函数式的元编程 API**。"

---

## Reflect 与 Proxy 的完美搭档

下午两点, 你开始用 Reflect 重构昨天的 Proxy 代码。

"既然 Reflect 和 Proxy 一一对应, " 你想, "那在 Proxy 的 handler 中使用 Reflect 应该是最佳实践。"

你重写了响应式系统:

```javascript
function reactive(target) {
    return new Proxy(target, {
        get(target, prop, receiver) {
            console.log('读取:', prop);
            // 使用 Reflect 保持正确的 this
            return Reflect.get(target, prop, receiver);
        },

        set(target, prop, value, receiver) {
            console.log('设置:', prop, '=', value);
            // 使用 Reflect 进行设置
            const result = Reflect.set(target, prop, value, receiver);
            // 返回布尔值表示是否成功
            return result;
        },

        deleteProperty(target, prop) {
            console.log('删除:', prop);
            // 使用 Reflect 删除属性
            return Reflect.deleteProperty(target, prop);
        },

        has(target, prop) {
            console.log('检查:', prop);
            // 使用 Reflect 检查属性
            return Reflect.has(target, prop);
        }
    });
}

// 测试
const obj = {
    _value: 0,
    get value() {
        return this._value;
    },
    set value(v) {
        this._value = v;
    }
};

const proxy = reactive(obj);

console.log(proxy.value);  // 0, this 指向正确
proxy.value = 100;  // 设置成功
console.log('value' in proxy);  // true
delete proxy._value;  // 删除成功
```

"使用 Reflect 的好处太明显了, " 你总结:

1. **正确的 this 指向**: receiver 参数确保 getter/setter 中的 this 指向代理对象
2. **统一的返回值**: 布尔值表示成功或失败, 而非抛出异常
3. **默认行为**: 提供了操作的默认实现, 简化代理逻辑
4. **函数式风格**: 所有操作都是函数调用, 更易组合

你又实现了一个只读代理:

```javascript
function readonly(target) {
    return new Proxy(target, {
        get(target, prop, receiver) {
            return Reflect.get(target, prop, receiver);
        },

        set(target, prop, value, receiver) {
            console.warn(`属性 ${prop} 是只读的`);
            return false;  // 设置失败
        },

        deleteProperty(target, prop) {
            console.warn(`属性 ${prop} 不可删除`);
            return false;  // 删除失败
        }
    });
}

const obj = { name: 'Alice', age: 25 };
const readonlyObj = readonly(obj);

console.log(readonlyObj.name);  // 'Alice' - 读取成功
readonlyObj.age = 26;  // 属性 age 是只读的
delete readonlyObj.name;  // 属性 name 不可删除
```

---

## Reflect.apply 与函数调用

下午三点, 你研究 `Reflect.apply()` 的用途。

"既然可以直接调用函数, " 你想, "为什么需要 `Reflect.apply()`?"

你查阅文档, 发现 `Reflect.apply()` 的优势:

```javascript
function greet(greeting, name) {
    return `${greeting}, ${name}!`;
}

// 方式 1: 直接调用
console.log(greet('Hello', 'Alice'));  // 'Hello, Alice!'

// 方式 2: Function.prototype.apply
console.log(greet.apply(null, ['Hi', 'Bob']));  // 'Hi, Bob!'

// 方式 3: Reflect.apply
console.log(Reflect.apply(greet, null, ['Hey', 'Charlie']));  // 'Hey, Charlie!'
```

"看起来功能相同, " 你说, "但 Reflect.apply 有什么优势?"

你发现了关键区别:

### 优势 1: 不依赖 Function.prototype

```javascript
// 如果函数的 apply 方法被修改
function fn() {
    return 'result';
}

fn.apply = function() {
    return 'hacked';
};

console.log(fn.apply(null, []));  // 'hacked' - 被修改了
console.log(Reflect.apply(fn, null, []));  // 'result' - 不受影响
```

### 优势 2: 更安全

```javascript
// 如果对象没有 apply 方法
const notAFunction = { value: 42 };

try {
    notAFunction.apply(null, []);  // TypeError
} catch (e) {
    console.error('不是函数');
}

// Reflect.apply 会立即检查
try {
    Reflect.apply(notAFunction, null, []);  // TypeError
} catch (e) {
    console.error('不是函数');
}
```

### 优势 3: 配合 Proxy 使用

```javascript
function createLogger(fn, name) {
    return new Proxy(fn, {
        apply(target, thisArg, args) {
            console.log(`[${name}] 调用, 参数:`, args);
            // 使用 Reflect.apply 调用原函数
            const result = Reflect.apply(target, thisArg, args);
            console.log(`[${name}] 返回:`, result);
            return result;
        }
    });
}

const add = createLogger((a, b) => a + b, 'add');

console.log(add(1, 2));
// [add] 调用, 参数: [1, 2]
// [add] 返回: 3
// 3
```

"Reflect.apply 在代理函数调用时非常有用, " 你总结。

---

## Reflect.construct 与构造函数

下午四点, 你研究 `Reflect.construct()` 的特殊用途。

"这个方法可以用来创建实例, " 你想, "和 `new` 有什么区别?"

你测试了基本用法:

```javascript
class User {
    constructor(name, age) {
        this.name = name;
        this.age = age;
    }
}

// 方式 1: new 操作符
const user1 = new User('Alice', 25);

// 方式 2: Reflect.construct
const user2 = Reflect.construct(User, ['Bob', 26]);

console.log(user1);  // User { name: 'Alice', age: 25 }
console.log(user2);  // User { name: 'Bob', age: 26 }
```

"功能相同, " 你说, "但 Reflect.construct 有一个特殊用途——改变原型。"

你发现了第三个参数:

```javascript
class Animal {
    constructor(name) {
        this.name = name;
    }
    speak() {
        return `${this.name} makes a sound`;
    }
}

class Dog {
    constructor(name) {
        this.name = name;
    }
    bark() {
        return `${this.name} barks`;
    }
}

// 使用 Animal 的构造函数, 但原型是 Dog.prototype
const instance = Reflect.construct(Animal, ['Buddy'], Dog);

console.log(instance.name);  // 'Buddy' - 来自 Animal 构造函数
console.log(instance instanceof Dog);  // true - 原型是 Dog
console.log(instance instanceof Animal);  // false

// instance 有 Dog 的方法
console.log(instance.bark());  // 'Buddy barks'
```

"太神奇了!" 你说, "**Reflect.construct 可以分离构造函数和原型**!"

你又用它实现了一个代理构造函数:

```javascript
class User {
    constructor(name, age) {
        this.name = name;
        this.age = age;
    }
}

const UserProxy = new Proxy(User, {
    construct(target, args) {
        console.log('创建用户:', args);

        // 参数验证
        if (args.length < 2) {
            throw new Error('参数不足');
        }

        if (typeof args[0] !== 'string') {
            throw new Error('name 必须是字符串');
        }

        if (typeof args[1] !== 'number' || args[1] < 0) {
            throw new Error('age 必须是非负数');
        }

        // 使用 Reflect.construct 创建实例
        return Reflect.construct(target, args);
    }
});

const user = new UserProxy('Alice', 25);  // 成功

try {
    new UserProxy('Bob', -5);  // Error: age 必须是非负数
} catch (e) {
    console.error(e.message);
}
```

---

## Reflect 的最佳实践

下午五点, 你总结了 Reflect 的使用场景。

"什么时候应该用 Reflect?" 你自问。

你整理了最佳实践:

### 实践 1: Proxy handler 中始终使用 Reflect

```javascript
// ❌ 不推荐: 直接操作 target
const proxy = new Proxy(obj, {
    get(target, prop) {
        return target[prop];
    }
});

// ✅ 推荐: 使用 Reflect
const proxy = new Proxy(obj, {
    get(target, prop, receiver) {
        return Reflect.get(target, prop, receiver);
    }
});
```

### 实践 2: 需要布尔返回值时使用 Reflect

```javascript
// ❌ 不推荐: 依赖异常
try {
    Object.defineProperty(obj, 'prop', { value: 'v' });
    console.log('成功');
} catch (e) {
    console.log('失败');
}

// ✅ 推荐: 使用布尔返回值
if (Reflect.defineProperty(obj, 'prop', { value: 'v' })) {
    console.log('成功');
} else {
    console.log('失败');
}
```

### 实践 3: 函数式编程场景

```javascript
// Reflect 方法可以作为参数传递
const operations = [
    Reflect.has,
    Reflect.get,
    Reflect.set
];

// 可以组合使用
const hasName = obj => Reflect.has(obj, 'name');
const getName = obj => Reflect.get(obj, 'name');
```

### 实践 4: 需要完整属性列表时

```javascript
// ✅ 使用 Reflect.ownKeys 获取包括 Symbol 的所有属性
const allKeys = Reflect.ownKeys(obj);

// 而非
const keys = Object.keys(obj);  // 不包括 Symbol
```

---

## 你的 Reflect 笔记本

晚上八点, 你整理了今天的收获。

你在笔记本上写下标题: "Reflect —— JavaScript 元编程的标准 API"

### 核心洞察 #1: Reflect 的设计目标

你写道:

"Reflect 提供了 JavaScript 元操作的标准 API:

```javascript
// 13 种 Reflect 方法, 对应 Proxy 的 13 种陷阱
Reflect.get(target, prop, receiver)
Reflect.set(target, prop, value, receiver)
Reflect.has(target, prop)
Reflect.deleteProperty(target, prop)
Reflect.ownKeys(target)
Reflect.getOwnPropertyDescriptor(target, prop)
Reflect.defineProperty(target, prop, descriptor)
Reflect.preventExtensions(target)
Reflect.getPrototypeOf(target)
Reflect.setPrototypeOf(target, proto)
Reflect.isExtensible(target)
Reflect.apply(fn, thisArg, args)
Reflect.construct(Fn, args, newTarget)
```

设计目标:
- 统一元编程 API
- 函数式风格 (操作变成函数调用)
- 更合理的返回值 (布尔值而非异常)
- 与 Proxy 配合使用"

### 核心洞察 #2: Reflect 与 Proxy 的配合

"Reflect 是 Proxy 的最佳搭档:

```javascript
const proxy = new Proxy(target, {
    get(target, prop, receiver) {
        // ✓ 使用 Reflect 保持正确的 this
        return Reflect.get(target, prop, receiver);
    },

    set(target, prop, value, receiver) {
        // ✓ 使用 Reflect 获取布尔返回值
        return Reflect.set(target, prop, value, receiver);
    }
});
```

关键优势:
- receiver 参数确保 getter/setter 的 this 指向正确
- 提供操作的默认实现
- 返回布尔值表示成功或失败
- 简化 Proxy handler 的逻辑"

### 核心洞察 #3: Reflect 与 Object 的区别

"Reflect 改进了 Object 的元编程方法:

差异对比:
1. 返回值更合理 (布尔值 vs 对象/异常)
2. 函数式风格 (函数调用 vs 操作符)
3. 更完整的功能 (Reflect.ownKeys 包括 Symbol)
4. receiver 参数 (正确的 this 指向)

```javascript
// Object.defineProperty: 返回对象, 失败抛异常
Object.defineProperty(obj, 'p', { value: 'v' });

// Reflect.defineProperty: 返回布尔值
const success = Reflect.defineProperty(obj, 'p', { value: 'v' });
```"

### 核心洞察 #4: Reflect.construct 的特殊用途

"Reflect.construct 可以分离构造函数和原型:

```javascript
// 使用 Animal 构造函数, 但原型是 Dog.prototype
const instance = Reflect.construct(Animal, ['Buddy'], Dog);

console.log(instance instanceof Dog);  // true
console.log(instance instanceof Animal);  // false
```

应用场景:
- 继承实现
- 构造函数代理
- 自定义实例化逻辑"

你合上笔记本, 关掉电脑。

"明天要学习 eval 的陷阱了, " 你想, "今天终于理解了 Reflect 的价值——它不是可有可无的工具, 而是现代 JavaScript 元编程的标准答案。通过与 Proxy 配合使用, Reflect 提供了安全、一致、函数式的元操作 API。理解 Reflect, 才能写出正确的 Proxy 代理, 实现强大的元编程功能。"

---

## 知识总结

**规则 1: Reflect 的基本概念**

Reflect 是一个内置对象, 提供拦截 JavaScript 操作的方法:

```javascript
// Reflect 不是构造函数, 不能用 new 调用
typeof Reflect;  // 'object'

// Reflect 的所有方法都是静态方法
Reflect.get(obj, 'name');
Reflect.set(obj, 'name', 'Alice');
Reflect.has(obj, 'name');
```

核心特性:
- 提供 13 种方法, 对应 Proxy 的 13 种陷阱
- 所有方法都是静态方法
- 函数式风格, 操作变成函数调用
- 返回布尔值或结果, 而非抛出异常

---

**规则 2: Reflect 的 13 种方法**

Reflect 提供的方法与 Proxy 陷阱一一对应:

```javascript
const obj = { name: 'Alice', age: 25 };

// 1. Reflect.get(target, prop, receiver)
// 读取属性, 等价于 target[prop]
const name = Reflect.get(obj, 'name');  // 'Alice'

// 2. Reflect.set(target, prop, value, receiver)
// 设置属性, 等价于 target[prop] = value
const success = Reflect.set(obj, 'age', 26);  // true

// 3. Reflect.has(target, prop)
// 检查属性存在, 等价于 prop in target
const exists = Reflect.has(obj, 'name');  // true

// 4. Reflect.deleteProperty(target, prop)
// 删除属性, 等价于 delete target[prop]
const deleted = Reflect.deleteProperty(obj, 'age');  // true

// 5. Reflect.ownKeys(target)
// 返回所有属性键 (包括 Symbol), 等价于 Object.getOwnPropertyNames + Object.getOwnPropertySymbols
const keys = Reflect.ownKeys(obj);  // ['name']

// 6. Reflect.getOwnPropertyDescriptor(target, prop)
// 获取属性描述符
const descriptor = Reflect.getOwnPropertyDescriptor(obj, 'name');

// 7. Reflect.defineProperty(target, prop, descriptor)
// 定义属性, 返回布尔值
const defined = Reflect.defineProperty(obj, 'salary', {
    value: 50000,
    writable: true
});  // true

// 8. Reflect.preventExtensions(target)
// 阻止对象扩展
const prevented = Reflect.preventExtensions(obj);  // true

// 9. Reflect.getPrototypeOf(target)
// 获取原型
const proto = Reflect.getPrototypeOf(obj);  // Object.prototype

// 10. Reflect.setPrototypeOf(target, proto)
// 设置原型
const set = Reflect.setPrototypeOf(obj, null);  // true

// 11. Reflect.isExtensible(target)
// 检查对象是否可扩展
const extensible = Reflect.isExtensible(obj);  // true 或 false

// 12. Reflect.apply(fn, thisArg, args)
// 调用函数
function greet(name) {
    return `Hello, ${name}`;
}
const result = Reflect.apply(greet, null, ['Alice']);  // 'Hello, Alice'

// 13. Reflect.construct(Fn, args, newTarget)
// 调用构造函数
class User {
    constructor(name) {
        this.name = name;
    }
}
const user = Reflect.construct(User, ['Alice']);  // User { name: 'Alice' }
```

---

**规则 3: Reflect 与 Object 的区别**

Reflect 改进了 Object 的元编程方法:

**差异 1: 返回值更合理**

```javascript
const obj = {};

// Object.defineProperty: 成功返回对象, 失败抛异常
try {
    Object.defineProperty(obj, 'name', { value: 'Alice' });
    console.log('成功');
} catch (e) {
    console.log('失败');
}

// Reflect.defineProperty: 返回布尔值
const success = Reflect.defineProperty(obj, 'name', { value: 'Alice' });
if (success) {
    console.log('成功');
} else {
    console.log('失败');
}
```

**差异 2: 函数式风格**

```javascript
const obj = { name: 'Alice' };

// 传统方式: 操作符
delete obj.name;
'name' in obj;

// Reflect 方式: 函数调用
Reflect.deleteProperty(obj, 'name');
Reflect.has(obj, 'name');

// 好处: 可以作为参数传递
const hasName = (obj) => Reflect.has(obj, 'name');
```

**差异 3: 更完整的功能**

```javascript
const obj = {
    name: 'Alice',
    [Symbol('id')]: 123
};

// Object.keys: 只返回字符串键
console.log(Object.keys(obj));  // ['name']

// Reflect.ownKeys: 返回所有键 (包括 Symbol)
console.log(Reflect.ownKeys(obj));  // ['name', Symbol(id)]
```

**差异 4: receiver 参数**

```javascript
const obj = {
    _value: 0,
    get value() {
        return this._value;
    }
};

const proxy = new Proxy(obj, {
    get(target, prop, receiver) {
        // 传入 receiver 确保 this 指向正确
        return Reflect.get(target, prop, receiver);
    }
});
```

---

**规则 4: Reflect 与 Proxy 的配合**

Reflect 是 Proxy 的最佳搭档:

```javascript
const obj = {
    _value: 0,
    get value() {
        console.log('getter 中的 this:', this === proxy);
        return this._value;
    },
    set value(v) {
        this._value = v;
    }
};

const proxy = new Proxy(obj, {
    get(target, prop, receiver) {
        console.log('读取:', prop);
        // ✓ 使用 Reflect 保持正确的 this
        return Reflect.get(target, prop, receiver);
    },

    set(target, prop, value, receiver) {
        console.log('设置:', prop, '=', value);
        // ✓ 使用 Reflect 获取布尔返回值
        return Reflect.set(target, prop, value, receiver);
    },

    deleteProperty(target, prop) {
        console.log('删除:', prop);
        // ✓ 使用 Reflect 删除属性
        return Reflect.deleteProperty(target, prop);
    }
});

console.log(proxy.value);  // getter 中的 this: true
proxy.value = 100;  // 设置成功
delete proxy._value;  // 删除成功
```

关键优势:
- **receiver 参数**: 确保 getter/setter 中的 this 指向代理对象
- **默认行为**: 提供操作的标准实现
- **布尔返回值**: 清晰表示操作成功或失败
- **简化逻辑**: 不需要手动实现复杂的操作逻辑

---

**规则 5: receiver 参数的作用**

receiver 参数确保 this 指向正确:

```javascript
const obj = {
    _value: 0,
    get value() {
        return this._value;
    }
};

// ❌ 错误: 不传 receiver, this 指向错误
const wrongProxy = new Proxy(obj, {
    get(target, prop) {
        return target[prop];  // getter 中 this 指向 target
    }
});

const child1 = Object.create(wrongProxy);
console.log(child1.value);  // undefined (this 指向 target, 而非 child1)

// ✅ 正确: 传入 receiver, this 指向正确
const correctProxy = new Proxy(obj, {
    get(target, prop, receiver) {
        return Reflect.get(target, prop, receiver);  // receiver 是代理对象或继承者
    }
});

const child2 = Object.create(correctProxy);
console.log(child2.value);  // 0 (this 指向 child2)
```

receiver 的作用:
- get 陷阱: receiver 是读取操作的接收者 (代理对象或继承代理的对象)
- set 陷阱: receiver 是赋值操作的接收者
- Reflect 方法使用 receiver 确保 this 指向正确

---

**规则 6: Reflect.apply 的用途**

Reflect.apply 提供安全的函数调用:

```javascript
function greet(greeting, name) {
    return `${greeting}, ${name}!`;
}

// 方式 1: 直接调用
console.log(greet('Hello', 'Alice'));  // 'Hello, Alice!'

// 方式 2: Function.prototype.apply
console.log(greet.apply(null, ['Hi', 'Bob']));  // 'Hi, Bob!'

// 方式 3: Reflect.apply
console.log(Reflect.apply(greet, null, ['Hey', 'Charlie']));  // 'Hey, Charlie!'
```

**Reflect.apply 的优势**:

1. **不依赖 Function.prototype**:
```javascript
function fn() {
    return 'result';
}

// 如果 apply 方法被修改
fn.apply = function() {
    return 'hacked';
};

console.log(fn.apply(null, []));  // 'hacked'
console.log(Reflect.apply(fn, null, []));  // 'result' (不受影响)
```

2. **配合 Proxy 使用**:
```javascript
function createLogger(fn, name) {
    return new Proxy(fn, {
        apply(target, thisArg, args) {
            console.log(`[${name}] 调用, 参数:`, args);
            const result = Reflect.apply(target, thisArg, args);
            console.log(`[${name}] 返回:`, result);
            return result;
        }
    });
}

const add = createLogger((a, b) => a + b, 'add');
console.log(add(1, 2));
// [add] 调用, 参数: [1, 2]
// [add] 返回: 3
// 3
```

---

**规则 7: Reflect.construct 的特殊用途**

Reflect.construct 可以分离构造函数和原型:

```javascript
class Animal {
    constructor(name) {
        this.name = name;
    }
    speak() {
        return `${this.name} makes a sound`;
    }
}

class Dog {
    constructor(name) {
        this.name = name;
    }
    bark() {
        return `${this.name} barks`;
    }
}

// 基本用法
const animal = Reflect.construct(Animal, ['Buddy']);
console.log(animal.name);  // 'Buddy'
console.log(animal instanceof Animal);  // true

// 高级用法: 第三个参数改变原型
const instance = Reflect.construct(Animal, ['Max'], Dog);

console.log(instance.name);  // 'Max' (来自 Animal 构造函数)
console.log(instance instanceof Dog);  // true (原型是 Dog.prototype)
console.log(instance instanceof Animal);  // false

// instance 有 Dog 的方法, 没有 Animal 的方法
console.log(instance.bark());  // 'Max barks'
console.log(typeof instance.speak);  // 'undefined'
```

应用场景:
- 实现复杂的继承关系
- 代理构造函数
- 自定义实例化逻辑

---

**规则 8: Reflect 的最佳实践**

**实践 1: Proxy handler 中始终使用 Reflect**

```javascript
// ✅ 推荐
const proxy = new Proxy(target, {
    get(target, prop, receiver) {
        return Reflect.get(target, prop, receiver);
    },
    set(target, prop, value, receiver) {
        return Reflect.set(target, prop, value, receiver);
    }
});
```

**实践 2: 需要布尔返回值时使用 Reflect**

```javascript
// ✅ 推荐: 函数式风格, 清晰的布尔返回值
if (Reflect.defineProperty(obj, 'prop', { value: 'v' })) {
    console.log('成功');
} else {
    console.log('失败');
}
```

**实践 3: 需要完整属性列表时使用 Reflect.ownKeys**

```javascript
const obj = {
    name: 'Alice',
    [Symbol('id')]: 123
};

// ✅ Reflect.ownKeys 包括 Symbol
const allKeys = Reflect.ownKeys(obj);  // ['name', Symbol(id)]
```

**实践 4: 函数式编程场景**

```javascript
// Reflect 方法可以作为参数传递
const operations = [
    Reflect.has,
    Reflect.get,
    Reflect.set
];

// 可以组合使用
const hasName = obj => Reflect.has(obj, 'name');
const getName = obj => Reflect.get(obj, 'name');
```

---

**事故档案编号**: MODULE-2024-1907
**影响范围**: Reflect, Proxy, 元编程, this 指向, receiver 参数
**根本原因**: 不理解 Reflect 与 Proxy 的配合关系, this 指向错误
**修复成本**: 低 (理解 receiver 参数后容易修复)

这是 JavaScript 世界第 107 次被记录的模块系统事故。Reflect 是一个内置对象, 提供拦截 JavaScript 操作的方法, 与 Proxy 的陷阱一一对应。Reflect 提供 13 种静态方法, 所有方法都是函数式风格, 返回布尔值或结果而非抛出异常。Reflect 是 Proxy 的最佳搭档, receiver 参数确保 getter/setter 中的 this 指向正确。Reflect 改进了 Object 的元编程方法, 提供更合理的返回值、函数式风格和更完整的功能。理解 Reflect 是正确使用 Proxy 和实现元编程的关键。

---

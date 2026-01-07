《第 106 次记录: 对象访问的监听者 —— Proxy 的拦截世界》

---

## 奇怪的表单验证 bug

周三上午九点, 你盯着用户提交的 bug 报告, 完全不明白发生了什么。

这是公司新上线的用户注册表单。你用了最新的 Vue 3 框架, 实现了实时验证功能——用户输入邮箱时, 系统会立即检查格式; 输入密码时, 会实时显示强度等级。在开发环境中, 一切都运行得很完美。

但上线第一天, 就有用户投诉: "为什么我输入了邮箱, 验证提示却不出现?"

你打开生产环境的控制台, 尝试重现问题。奇怪的是, 你无法稳定复现——有时验证正常工作, 有时又完全失效。

你查看代码, 看到了表单数据的定义:

```javascript
const formData = {
    email: '',
    password: '',
    age: 0
};

// 监听邮箱变化
function validateEmail() {
    if (formData.email.includes('@')) {
        console.log('邮箱格式正确');
    }
}
```

"这有什么问题吗?" 你困惑, "数据改变时应该触发验证..."

但问题是, **数据改变时, JavaScript 并不会自动通知你**。你需要手动在每个赋值处调用验证函数:

```javascript
formData.email = 'user@example.com';
validateEmail();  // 必须手动调用

formData.password = '123456';
validatePassword();  // 又要手动调用
```

"这太麻烦了, " 你想, "而且很容易忘记。如果能监听对象的所有访问和修改就好了..."

你突然想起 Vue 3 的响应式系统文档里提到的一个词: **Proxy**。

---

## Proxy 的发现

上午十点, 你打开 MDN, 搜索 "JavaScript Proxy"。

> **Proxy 对象**: 用于创建一个对象的代理, 从而实现基本操作的拦截和自定义 (如属性查找、赋值、枚举、函数调用等)。

"代理?" 你盯着定义, "拦截对象操作?"

你看到了一个示例:

```javascript
const handler = {
    get: function(target, prop) {
        console.log('读取属性:', prop);
        return target[prop];
    },
    set: function(target, prop, value) {
        console.log('设置属性:', prop, '=', value);
        target[prop] = value;
        return true;
    }
};

const obj = { name: 'Alice' };
const proxy = new Proxy(obj, handler);

proxy.name;  // 输出: 读取属性: name
proxy.age = 25;  // 输出: 设置属性: age = 25
```

你在控制台中测试, 输出让你兴奋:

```
读取属性: name
设置属性: age = 25
```

"太神奇了!" 你说, "**每次访问或修改对象时, Proxy 都能拦截到**!"

你立刻想到了表单验证的应用场景。你修改代码:

```javascript
const formData = {
    email: '',
    password: '',
    age: 0
};

const formProxy = new Proxy(formData, {
    set: function(target, prop, value) {
        console.log(`检测到 ${prop} 被设置为:`, value);

        // 设置新值
        target[prop] = value;

        // 自动触发验证
        if (prop === 'email') {
            validateEmail(value);
        } else if (prop === 'password') {
            validatePassword(value);
        }

        return true;
    }
});

// 现在只需要修改值, 验证会自动触发
formProxy.email = 'user@example.com';  // 自动验证
formProxy.password = '123456';  // 自动验证
```

测试后, 验证功能完美工作了!

"这就是 Vue 3 响应式系统的原理, " 你恍然大悟, "**Proxy 让对象变成了可观察的**!"

---

## 拦截器的 13 种陷阱

中午十二点, 你开始深入研究 Proxy 的能力。

"既然可以拦截 get 和 set, " 你想, "还能拦截什么操作?"

你查阅文档, 发现 Proxy 支持 **13 种拦截器 (trap)**:

```javascript
const handler = {
    // 1. 属性读取
    get: function(target, prop, receiver) {
        console.log('读取:', prop);
        return target[prop];
    },

    // 2. 属性设置
    set: function(target, prop, value, receiver) {
        console.log('设置:', prop, '=', value);
        target[prop] = value;
        return true;
    },

    // 3. in 操作符
    has: function(target, prop) {
        console.log('检查属性存在:', prop);
        return prop in target;
    },

    // 4. delete 操作符
    deleteProperty: function(target, prop) {
        console.log('删除属性:', prop);
        delete target[prop];
        return true;
    },

    // 5. Object.keys() / for...in
    ownKeys: function(target) {
        console.log('枚举属性');
        return Object.keys(target);
    },

    // 6. Object.getOwnPropertyDescriptor()
    getOwnPropertyDescriptor: function(target, prop) {
        console.log('获取属性描述符:', prop);
        return Object.getOwnPropertyDescriptor(target, prop);
    },

    // 7. Object.defineProperty()
    defineProperty: function(target, prop, descriptor) {
        console.log('定义属性:', prop);
        return Object.defineProperty(target, prop, descriptor);
    },

    // 8. Object.preventExtensions()
    preventExtensions: function(target) {
        console.log('阻止扩展');
        Object.preventExtensions(target);
        return true;
    },

    // 9. Object.getPrototypeOf()
    getPrototypeOf: function(target) {
        console.log('获取原型');
        return Object.getPrototypeOf(target);
    },

    // 10. Object.setPrototypeOf()
    setPrototypeOf: function(target, proto) {
        console.log('设置原型');
        Object.setPrototypeOf(target, proto);
        return true;
    },

    // 11. Object.isExtensible()
    isExtensible: function(target) {
        console.log('检查是否可扩展');
        return Object.isExtensible(target);
    },

    // 12. 函数调用 (如果代理的是函数)
    apply: function(target, thisArg, args) {
        console.log('调用函数, 参数:', args);
        return target.apply(thisArg, args);
    },

    // 13. new 操作符 (如果代理的是构造函数)
    construct: function(target, args) {
        console.log('new 调用, 参数:', args);
        return new target(...args);
    }
};
```

"13 种拦截器!" 你惊讶, "几乎可以拦截所有对象操作!"

你测试了几个常用的陷阱:

```javascript
const obj = { name: 'Alice', age: 25 };

const proxy = new Proxy(obj, {
    get(target, prop) {
        if (prop in target) {
            return target[prop];
        } else {
            throw new Error(`属性 ${prop} 不存在`);
        }
    },

    has(target, prop) {
        console.log(`检查 ${prop} 是否存在`);
        return prop in target;
    },

    deleteProperty(target, prop) {
        if (prop === 'name') {
            throw new Error('name 属性不可删除');
        }
        delete target[prop];
        return true;
    }
});

// 测试
console.log(proxy.name);  // 'Alice'
console.log('age' in proxy);  // 检查 age 是否存在 → true

try {
    console.log(proxy.salary);  // Error: 属性 salary 不存在
} catch (e) {
    console.error(e.message);
}

try {
    delete proxy.name;  // Error: name 属性不可删除
} catch (e) {
    console.error(e.message);
}
```

"这样就可以实现严格的对象访问控制, " 你说, "**Proxy 让对象变得更安全**。"

---

## 数据验证与访问日志

下午两点, 你开始构建实际应用。

"既然可以拦截 set, " 你想, "那可以在赋值时进行数据验证。"

你实现了一个验证代理:

```javascript
function createValidator(schema) {
    return new Proxy({}, {
        set(target, prop, value) {
            // 检查属性是否在 schema 中定义
            if (!(prop in schema)) {
                throw new Error(`未知属性: ${prop}`);
            }

            const rule = schema[prop];

            // 类型验证
            if (rule.type && typeof value !== rule.type) {
                throw new Error(`${prop} 类型必须是 ${rule.type}`);
            }

            // 范围验证
            if (rule.min !== undefined && value < rule.min) {
                throw new Error(`${prop} 不能小于 ${rule.min}`);
            }

            if (rule.max !== undefined && value > rule.max) {
                throw new Error(`${prop} 不能大于 ${rule.max}`);
            }

            // 正则验证
            if (rule.pattern && !rule.pattern.test(value)) {
                throw new Error(`${prop} 格式不正确`);
            }

            // 验证通过, 设置值
            target[prop] = value;
            return true;
        }
    });
}

// 使用
const user = createValidator({
    name: { type: 'string' },
    age: { type: 'number', min: 0, max: 120 },
    email: {
        type: 'string',
        pattern: /^[\w-]+(\.[\w-]+)*@[\w-]+(\.[\w-]+)+$/
    }
});

user.name = 'Alice';  // ✓ 正常
user.age = 25;  // ✓ 正常
user.email = 'alice@example.com';  // ✓ 正常

try {
    user.age = 150;  // ❌ Error: age 不能大于 120
} catch (e) {
    console.error(e.message);
}

try {
    user.email = 'invalid-email';  // ❌ Error: email 格式不正确
} catch (e) {
    console.error(e.message);
}
```

"完美的数据验证!" 你满意地说。

你又实现了一个访问日志代理, 用于调试:

```javascript
function createLogger(target, name) {
    return new Proxy(target, {
        get(target, prop) {
            console.log(`[${name}] 读取属性: ${prop}`);
            return target[prop];
        },

        set(target, prop, value) {
            console.log(`[${name}] 设置属性: ${prop} = ${JSON.stringify(value)}`);
            target[prop] = value;
            return true;
        },

        deleteProperty(target, prop) {
            console.log(`[${name}] 删除属性: ${prop}`);
            delete target[prop];
            return true;
        },

        apply(target, thisArg, args) {
            console.log(`[${name}] 调用函数, 参数:`, args);
            const result = target.apply(thisArg, args);
            console.log(`[${name}] 返回值:`, result);
            return result;
        }
    });
}

// 测试
const obj = createLogger({ name: 'Alice', age: 25 }, 'User');

obj.name;  // [User] 读取属性: name
obj.age = 26;  // [User] 设置属性: age = 26
delete obj.age;  // [User] 删除属性: age

const fn = createLogger(function(a, b) {
    return a + b;
}, 'add');

fn(1, 2);  // [add] 调用函数, 参数: [1, 2]
           // [add] 返回值: 3
```

"这样就可以追踪所有对象操作了, " 你说, "调试时非常有用。"

---

## 响应式系统的实现

下午四点, 你尝试实现一个简化版的响应式系统。

"Vue 3 的响应式系统就是基于 Proxy, " 你想, "我能自己实现一个吗?"

你写下了核心代码:

```javascript
// 当前活动的副作用函数
let activeEffect = null;

// 依赖收集的数据结构
const targetMap = new WeakMap();

// 依赖收集
function track(target, prop) {
    if (!activeEffect) return;

    let depsMap = targetMap.get(target);
    if (!depsMap) {
        depsMap = new Map();
        targetMap.set(target, depsMap);
    }

    let dep = depsMap.get(prop);
    if (!dep) {
        dep = new Set();
        depsMap.set(prop, dep);
    }

    dep.add(activeEffect);
}

// 依赖触发
function trigger(target, prop) {
    const depsMap = targetMap.get(target);
    if (!depsMap) return;

    const dep = depsMap.get(prop);
    if (!dep) return;

    dep.forEach(effect => effect());
}

// 创建响应式对象
function reactive(target) {
    return new Proxy(target, {
        get(target, prop, receiver) {
            track(target, prop);  // 收集依赖
            return Reflect.get(target, prop, receiver);
        },

        set(target, prop, value, receiver) {
            const result = Reflect.set(target, prop, value, receiver);
            trigger(target, prop);  // 触发更新
            return result;
        }
    });
}

// 副作用函数
function effect(fn) {
    activeEffect = fn;
    fn();  // 立即执行一次, 收集依赖
    activeEffect = null;
}

// 使用
const state = reactive({
    count: 0,
    message: 'Hello'
});

// 注册副作用
effect(() => {
    console.log('count 变化了:', state.count);
});

// 注册另一个副作用
effect(() => {
    console.log('message 变化了:', state.message);
});

// 测试
state.count++;  // 输出: count 变化了: 1
state.count++;  // 输出: count 变化了: 2
state.message = 'Hi';  // 输出: message 变化了: Hi
```

你运行代码, 看到了完美的响应式效果:

```
count 变化了: 0
message 变化了: Hello
count 变化了: 1
count 变化了: 2
message 变化了: Hi
```

"太棒了!" 你兴奋地说, "**Proxy 让我们可以拦截属性访问, 实现自动的依赖收集和更新**!"

你又测试了嵌套对象:

```javascript
const state = reactive({
    user: {
        name: 'Alice',
        profile: {
            age: 25
        }
    }
});

effect(() => {
    console.log('用户名:', state.user.name);
});

effect(() => {
    console.log('年龄:', state.user.profile.age);
});

state.user.name = 'Bob';  // 输出: 用户名: Bob
state.user.profile.age = 26;  // 输出: 年龄: 26
```

"嵌套对象也能正常工作, " 你说, "这就是现代前端框架的核心机制。"

---

## Proxy 的性能考量

下午五点, 你开始思考 Proxy 的性能问题。

"既然每次访问都要经过 Proxy, " 你想, "会不会有性能损耗?"

你写了性能测试代码:

```javascript
const obj = { count: 0 };
const proxy = new Proxy(obj, {
    get(target, prop) {
        return target[prop];
    },
    set(target, prop, value) {
        target[prop] = value;
        return true;
    }
});

// 测试直接访问
console.time('直接访问');
for (let i = 0; i < 1000000; i++) {
    obj.count++;
}
console.timeEnd('直接访问');

// 重置
obj.count = 0;

// 测试 Proxy 访问
console.time('Proxy 访问');
for (let i = 0; i < 1000000; i++) {
    proxy.count++;
}
console.timeEnd('Proxy 访问');
```

输出:

```
直接访问: 3.2ms
Proxy 访问: 18.7ms
```

"Proxy 确实有性能损耗, " 你说, "大约是直接访问的 6 倍。"

但你又测试了实际应用场景:

```javascript
const state = reactive({
    user: { name: 'Alice', age: 25 },
    posts: [],
    settings: {}
});

console.time('实际应用');
for (let i = 0; i < 10000; i++) {
    state.user.name;
    state.user.age++;
    state.posts.push({ id: i });
}
console.timeEnd('实际应用');
```

输出:

```
实际应用: 12.3ms
```

"在实际应用中, 10000 次操作只需要 12ms, " 你总结, "**对于 UI 应用来说, Proxy 的性能完全可以接受**。而且响应式带来的开发效率提升远远超过这点性能损耗。"

---

## Proxy 的限制与陷阱

下午六点, 你发现了 Proxy 的一些限制。

"等等, " 你在测试时遇到了问题, "为什么这个代理不工作?"

```javascript
const obj = { name: 'Alice' };
const proxy = new Proxy(obj, {
    get(target, prop) {
        console.log('读取:', prop);
        return target[prop];
    }
});

const result = proxy === obj;  // false
console.log(result);
```

"Proxy 创建的是一个新对象, " 你恍然大悟, "不是修改原对象。"

你又发现了另一个问题:

```javascript
const arr = [1, 2, 3];
const proxy = new Proxy(arr, {
    get(target, prop) {
        console.log('读取:', prop);
        return target[prop];
    }
});

console.log(proxy.length);  // 读取: length → 3
proxy.push(4);  // 读取: length, 读取: push, 读取: length
```

"数组操作会触发多次拦截, " 你说, "因为 push 内部会读取 length。"

你还发现了 this 的问题:

```javascript
const obj = {
    name: 'Alice',
    greet() {
        return `Hello, ${this.name}`;
    }
};

const proxy = new Proxy(obj, {
    get(target, prop) {
        return target[prop];
    }
});

console.log(obj.greet());  // 'Hello, Alice'
console.log(proxy.greet());  // 'Hello, undefined'
```

"this 指向错了!" 你发现问题, "需要用 Reflect 保持正确的 this 指向。"

你修复了代码:

```javascript
const proxy = new Proxy(obj, {
    get(target, prop, receiver) {
        return Reflect.get(target, prop, receiver);  // 使用 Reflect
    }
});

console.log(proxy.greet());  // 'Hello, Alice' ✓
```

"Reflect 可以保持正确的 this 指向, " 你总结。

---

## 你的 Proxy 笔记本

晚上八点, 你整理了今天的收获。

你在笔记本上写下标题: "Proxy —— 对象访问的监听者"

### 核心洞察 #1: Proxy 的基本机制

你写道:

"Proxy 创建对象的代理, 拦截所有操作:

```javascript
const proxy = new Proxy(target, handler);

// target: 被代理的对象
// handler: 拦截器对象, 定义拦截行为

const handler = {
    get(target, prop, receiver) {
        console.log('读取:', prop);
        return target[prop];
    },
    set(target, prop, value, receiver) {
        console.log('设置:', prop);
        target[prop] = value;
        return true;
    }
};
```

核心特性:
- Proxy 创建新对象, 不修改原对象
- 支持 13 种拦截器 (trap)
- 可以拦截几乎所有对象操作
- 必须配合 Reflect 使用以保持正确的 this"

### 核心洞察 #2: 13 种拦截器

"Proxy 支持的拦截器:

```javascript
const handler = {
    // 属性操作
    get(target, prop, receiver) {},
    set(target, prop, value, receiver) {},
    has(target, prop) {},
    deleteProperty(target, prop) {},

    // 属性描述符
    ownKeys(target) {},
    getOwnPropertyDescriptor(target, prop) {},
    defineProperty(target, prop, descriptor) {},

    // 原型操作
    getPrototypeOf(target) {},
    setPrototypeOf(target, proto) {},

    // 扩展性
    preventExtensions(target) {},
    isExtensible(target) {},

    // 函数操作
    apply(target, thisArg, args) {},
    construct(target, args) {}
};
```

常用场景:
- get/set: 数据验证、响应式系统
- has: 访问控制
- deleteProperty: 属性保护
- apply: 函数调用拦截"

### 核心洞察 #3: 响应式系统实现

"Proxy 实现响应式系统:

```javascript
function reactive(target) {
    return new Proxy(target, {
        get(target, prop, receiver) {
            track(target, prop);  // 依赖收集
            return Reflect.get(target, prop, receiver);
        },
        set(target, prop, value, receiver) {
            const result = Reflect.set(target, prop, value, receiver);
            trigger(target, prop);  // 触发更新
            return result;
        }
    });
}

// 副作用函数
effect(() => {
    console.log(state.count);  // 读取时收集依赖
});

state.count++;  // 设置时触发更新
```

原理:
- get 时收集依赖 (谁在读取)
- set 时触发更新 (通知所有依赖)
- 使用 WeakMap/Map/Set 管理依赖关系
- Vue 3 的响应式系统核心"

### 核心洞察 #4: 性能与限制

"Proxy 的性能考虑:

性能特点:
- 比直接访问慢 5-6 倍
- 对 UI 应用影响很小
- 响应式带来的开发效率远超性能损耗

限制:
- Proxy 创建新对象, 不是修改原对象
- 数组操作会触发多次拦截
- 必须用 Reflect 保持正确的 this
- 不支持私有字段 (#field) 的拦截"

你合上笔记本, 关掉电脑。

"明天要学习 Reflect 了, " 你想, "今天终于理解了 Proxy 的威力——它是现代前端框架响应式系统的基石。通过拦截对象操作, 我们可以实现数据验证、访问日志、响应式系统等强大功能。理解 Proxy, 才能真正理解 Vue 3、Mobx 等框架的核心机制。"

---

## 知识总结

**规则 1: Proxy 的基本语法**

Proxy 用于创建对象的代理, 拦截基本操作:

```javascript
const proxy = new Proxy(target, handler);

// target: 被代理的对象 (可以是任何对象, 包括数组、函数)
// handler: 拦截器对象, 定义拦截行为

const obj = { name: 'Alice', age: 25 };

const proxy = new Proxy(obj, {
    get(target, prop, receiver) {
        console.log('读取属性:', prop);
        return target[prop];
    },

    set(target, prop, value, receiver) {
        console.log('设置属性:', prop, '=', value);
        target[prop] = value;
        return true;  // 必须返回 true 表示设置成功
    }
});

proxy.name;  // 输出: 读取属性: name
proxy.age = 26;  // 输出: 设置属性: age = 26
```

核心特性:
- Proxy 创建的是新对象, 不修改原对象
- 所有操作都通过代理对象进行
- 拦截器返回值决定操作的结果
- 原对象依然可以直接访问, 不受代理影响

---

**规则 2: 13 种拦截器 (Trap)**

Proxy 支持拦截 13 种对象操作:

```javascript
const handler = {
    // 1. 属性读取: obj.prop, obj[prop]
    get(target, prop, receiver) {
        return target[prop];
    },

    // 2. 属性设置: obj.prop = value
    set(target, prop, value, receiver) {
        target[prop] = value;
        return true;
    },

    // 3. in 操作符: 'prop' in obj
    has(target, prop) {
        return prop in target;
    },

    // 4. delete 操作符: delete obj.prop
    deleteProperty(target, prop) {
        delete target[prop];
        return true;
    },

    // 5. Object.keys(), for...in 枚举
    ownKeys(target) {
        return Object.keys(target);
    },

    // 6. Object.getOwnPropertyDescriptor()
    getOwnPropertyDescriptor(target, prop) {
        return Object.getOwnPropertyDescriptor(target, prop);
    },

    // 7. Object.defineProperty()
    defineProperty(target, prop, descriptor) {
        return Object.defineProperty(target, prop, descriptor);
    },

    // 8. Object.preventExtensions()
    preventExtensions(target) {
        Object.preventExtensions(target);
        return true;
    },

    // 9. Object.getPrototypeOf()
    getPrototypeOf(target) {
        return Object.getPrototypeOf(target);
    },

    // 10. Object.setPrototypeOf()
    setPrototypeOf(target, proto) {
        Object.setPrototypeOf(target, proto);
        return true;
    },

    // 11. Object.isExtensible()
    isExtensible(target) {
        return Object.isExtensible(target);
    },

    // 12. 函数调用: fn(), fn.call(), fn.apply()
    apply(target, thisArg, args) {
        return target.apply(thisArg, args);
    },

    // 13. new 操作符: new Fn()
    construct(target, args) {
        return new target(...args);
    }
};
```

最常用的拦截器:
- **get/set**: 属性访问控制, 响应式系统
- **has**: 访问权限控制 (`'password' in obj`)
- **deleteProperty**: 属性保护, 防止删除
- **apply**: 函数调用拦截, 日志记录
- **construct**: 构造函数拦截, 参数验证

---

**规则 3: get 和 set 拦截器详解**

get 和 set 是最常用的拦截器:

```javascript
const handler = {
    // get 拦截属性读取
    get(target, prop, receiver) {
        // target: 原始对象
        // prop: 属性名 (字符串或 Symbol)
        // receiver: 代理对象本身 (或继承代理的对象)

        console.log('读取:', prop);

        // 必须返回属性值
        return target[prop];
    },

    // set 拦截属性设置
    set(target, prop, value, receiver) {
        // target: 原始对象
        // prop: 属性名
        // value: 新值
        // receiver: 代理对象本身

        console.log('设置:', prop, '=', value);

        // 设置属性
        target[prop] = value;

        // 必须返回 true 表示成功, 否则严格模式下报错
        return true;
    }
};

const proxy = new Proxy({ name: 'Alice' }, handler);

proxy.name;  // 触发 get
proxy.age = 25;  // 触发 set
```

常见应用:
- **数据验证**: set 中验证数据合法性
- **默认值**: get 中提供默认值
- **访问控制**: get/set 中检查权限
- **响应式系统**: 依赖收集和触发更新

---

**规则 4: 数据验证应用**

使用 Proxy 实现强类型数据验证:

```javascript
function createValidator(schema) {
    return new Proxy({}, {
        set(target, prop, value) {
            // 检查属性是否在 schema 中定义
            if (!(prop in schema)) {
                throw new Error(`未知属性: ${prop}`);
            }

            const rule = schema[prop];

            // 类型验证
            if (rule.type && typeof value !== rule.type) {
                throw new Error(`${prop} 类型必须是 ${rule.type}, 得到 ${typeof value}`);
            }

            // 范围验证
            if (rule.min !== undefined && value < rule.min) {
                throw new Error(`${prop} 不能小于 ${rule.min}`);
            }

            if (rule.max !== undefined && value > rule.max) {
                throw new Error(`${prop} 不能大于 ${rule.max}`);
            }

            // 正则验证
            if (rule.pattern && !rule.pattern.test(value)) {
                throw new Error(`${prop} 格式不正确`);
            }

            // 自定义验证
            if (rule.validator && !rule.validator(value)) {
                throw new Error(`${prop} 验证失败`);
            }

            // 验证通过, 设置值
            target[prop] = value;
            return true;
        }
    });
}

// 使用
const user = createValidator({
    name: {
        type: 'string'
    },
    age: {
        type: 'number',
        min: 0,
        max: 120
    },
    email: {
        type: 'string',
        pattern: /^[\w-]+(\.[\w-]+)*@[\w-]+(\.[\w-]+)+$/
    },
    password: {
        type: 'string',
        validator: (value) => value.length >= 8
    }
});

user.name = 'Alice';  // ✓
user.age = 25;  // ✓
user.email = 'alice@example.com';  // ✓
user.password = '12345678';  // ✓

user.age = 150;  // ❌ Error: age 不能大于 120
user.email = 'invalid';  // ❌ Error: email 格式不正确
user.password = '123';  // ❌ Error: password 验证失败
user.unknown = 'value';  // ❌ Error: 未知属性: unknown
```

---

**规则 5: 访问日志与调试**

使用 Proxy 实现对象操作的完整日志:

```javascript
function createLogger(target, name) {
    return new Proxy(target, {
        get(target, prop) {
            console.log(`[${name}] 读取属性: ${prop} = ${JSON.stringify(target[prop])}`);
            return target[prop];
        },

        set(target, prop, value) {
            console.log(`[${name}] 设置属性: ${prop} = ${JSON.stringify(value)}`);
            target[prop] = value;
            return true;
        },

        deleteProperty(target, prop) {
            console.log(`[${name}] 删除属性: ${prop}`);
            delete target[prop];
            return true;
        },

        has(target, prop) {
            console.log(`[${name}] 检查属性存在: ${prop}`);
            return prop in target;
        },

        apply(target, thisArg, args) {
            console.log(`[${name}] 调用函数, 参数: ${JSON.stringify(args)}`);
            const result = target.apply(thisArg, args);
            console.log(`[${name}] 返回值: ${JSON.stringify(result)}`);
            return result;
        }
    });
}

// 测试对象
const user = createLogger({ name: 'Alice', age: 25 }, 'User');

user.name;  // [User] 读取属性: name = "Alice"
user.age = 26;  // [User] 设置属性: age = 26
delete user.age;  // [User] 删除属性: age
'name' in user;  // [User] 检查属性存在: name

// 测试函数
const add = createLogger((a, b) => a + b, 'add');

add(1, 2);  // [add] 调用函数, 参数: [1,2]
            // [add] 返回值: 3
```

应用场景:
- 调试复杂对象操作
- 追踪数据流
- 性能分析
- 安全审计

---

**规则 6: 响应式系统实现**

Proxy 是 Vue 3 响应式系统的核心:

```javascript
// 当前活动的副作用函数
let activeEffect = null;

// 依赖收集的数据结构: WeakMap<target, Map<prop, Set<effect>>>
const targetMap = new WeakMap();

// 依赖收集
function track(target, prop) {
    if (!activeEffect) return;

    let depsMap = targetMap.get(target);
    if (!depsMap) {
        depsMap = new Map();
        targetMap.set(target, depsMap);
    }

    let dep = depsMap.get(prop);
    if (!dep) {
        dep = new Set();
        depsMap.set(prop, dep);
    }

    dep.add(activeEffect);
}

// 依赖触发
function trigger(target, prop) {
    const depsMap = targetMap.get(target);
    if (!depsMap) return;

    const dep = depsMap.get(prop);
    if (!dep) return;

    dep.forEach(effect => effect());
}

// 创建响应式对象
function reactive(target) {
    return new Proxy(target, {
        get(target, prop, receiver) {
            track(target, prop);  // 收集依赖
            return Reflect.get(target, prop, receiver);
        },

        set(target, prop, value, receiver) {
            const result = Reflect.set(target, prop, value, receiver);
            trigger(target, prop);  // 触发更新
            return result;
        }
    });
}

// 副作用函数
function effect(fn) {
    activeEffect = fn;
    fn();  // 立即执行一次, 收集依赖
    activeEffect = null;
}

// 使用
const state = reactive({
    count: 0,
    message: 'Hello'
});

// 注册副作用 (类似 Vue 的 computed 或 watch)
effect(() => {
    console.log('count 的双倍:', state.count * 2);
});

effect(() => {
    console.log('消息:', state.message);
});

// 输出:
// count 的双倍: 0
// 消息: Hello

state.count++;  // 触发第一个副作用 → count 的双倍: 2
state.message = 'Hi';  // 触发第二个副作用 → 消息: Hi
```

核心原理:
- **get 时**: 收集依赖 (记录哪些副作用函数读取了这个属性)
- **set 时**: 触发更新 (执行所有依赖这个属性的副作用函数)
- **WeakMap**: 防止内存泄漏, 对象被回收时依赖关系自动清理
- **Set**: 确保同一个副作用函数不会重复收集

---

**规则 7: Reflect 的配合使用**

Proxy 必须配合 Reflect 使用以保持正确的 this 指向:

```javascript
const obj = {
    name: 'Alice',
    greet() {
        return `Hello, ${this.name}`;
    }
};

// ❌ 错误: 不使用 Reflect, this 指向错误
const wrongProxy = new Proxy(obj, {
    get(target, prop) {
        return target[prop];  // 直接返回, this 指向 target
    }
});

console.log(wrongProxy.greet());  // 'Hello, undefined'

// ✅ 正确: 使用 Reflect, this 指向正确
const correctProxy = new Proxy(obj, {
    get(target, prop, receiver) {
        return Reflect.get(target, prop, receiver);  // receiver 是代理对象
    }
});

console.log(correctProxy.greet());  // 'Hello, Alice'
```

Reflect 的作用:
- **保持 this 指向**: receiver 参数传递给 Reflect, 确保 this 指向代理对象
- **标准化操作**: Reflect 方法与 Proxy 陷阱一一对应
- **函数式风格**: Reflect 操作返回布尔值而非抛出异常
- **默认行为**: Reflect 提供操作的默认实现

常用 Reflect 方法:
```javascript
Reflect.get(target, prop, receiver)
Reflect.set(target, prop, value, receiver)
Reflect.has(target, prop)
Reflect.deleteProperty(target, prop)
Reflect.ownKeys(target)
Reflect.apply(fn, thisArg, args)
Reflect.construct(Fn, args)
```

---

**规则 8: Proxy 的性能与限制**

**性能特点**:

```javascript
const obj = { count: 0 };
const proxy = new Proxy(obj, {
    get(target, prop) {
        return target[prop];
    },
    set(target, prop, value) {
        target[prop] = value;
        return true;
    }
});

// 性能测试
console.time('直接访问');
for (let i = 0; i < 1000000; i++) {
    obj.count++;
}
console.timeEnd('直接访问');  // ~3ms

obj.count = 0;

console.time('Proxy 访问');
for (let i = 0; i < 1000000; i++) {
    proxy.count++;
}
console.timeEnd('Proxy 访问');  // ~18ms
```

性能结论:
- Proxy 比直接访问慢 5-6 倍
- 对于 UI 应用, 影响很小 (10000 次操作约 12ms)
- 响应式带来的开发效率远超性能损耗

**使用限制**:

1. **Proxy 是新对象**:
```javascript
const obj = { name: 'Alice' };
const proxy = new Proxy(obj, {});

console.log(proxy === obj);  // false
```

2. **数组操作触发多次拦截**:
```javascript
const arr = [1, 2, 3];
const proxy = new Proxy(arr, {
    get(target, prop) {
        console.log('读取:', prop);
        return target[prop];
    }
});

proxy.push(4);
// 读取: push
// 读取: length
// 读取: 3
// 读取: length
```

3. **私有字段无法拦截**:
```javascript
class User {
    #password = '123456';

    getPassword() {
        return this.#password;
    }
}

const user = new User();
const proxy = new Proxy(user, {
    get(target, prop) {
        console.log('读取:', prop);
        return target[prop];
    }
});

proxy.getPassword();  // TypeError: 无法访问私有字段
```

4. **内建对象需要特殊处理**:
```javascript
const map = new Map([['key', 'value']]);
const proxy = new Proxy(map, {});

proxy.get('key');  // TypeError: Method Map.prototype.get called on incompatible receiver
```

---

**事故档案编号**: MODULE-2024-1906
**影响范围**: Proxy, 拦截器, 响应式系统, 数据验证, 访问日志
**根本原因**: 不理解 Proxy 的拦截机制, 无法实现响应式系统或数据验证
**修复成本**: 中 (需要理解 13 种拦截器和 Reflect 配合使用)

这是 JavaScript 世界第 106 次被记录的模块系统事故。Proxy 用于创建对象的代理, 拦截基本操作。支持 13 种拦截器 (trap), 包括 get/set/has/deleteProperty 等。最常用的是 get 和 set 拦截器, 用于数据验证、访问日志、响应式系统。Proxy 是 Vue 3 响应式系统的核心, 通过 get 时收集依赖、set 时触发更新实现自动响应。必须配合 Reflect 使用以保持正确的 this 指向。性能比直接访问慢 5-6 倍, 但对 UI 应用影响很小。理解 Proxy 是掌握现代前端框架响应式系统的关键。

---

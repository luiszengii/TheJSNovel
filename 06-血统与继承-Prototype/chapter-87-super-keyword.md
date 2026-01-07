《第 87 次记录: super 时机 —— 继承的枷锁》

---

## 表单验证的困惑

周五上午九点，你盯着屏幕上报错已经十分钟了。

昨晚你加班到很晚，实现了一个复杂的表单验证系统。需求很明确：有一个基础的 `FormField` 类，然后继承出 `EmailField`、`PasswordField` 等各种字段类型。每个字段都有自己独特的验证逻辑，但也要复用基类的通用功能。

你觉得这个设计很优雅，用 ES6 的 `class` 和 `extends` 实现继承，代码结构清晰。但今天早上测试时，控制台抛出了一个让你完全摸不着头脑的错误：

```
ReferenceError: Must call super constructor in derived class before accessing 'this' or returning from derived constructor
```

"在访问 `this` 之前必须调用 super 构造函数？" 你困惑地自言自语，"我明明调用了啊..."

你翻开昨晚写的代码，仔细检查：

```javascript
class FormField {
    constructor(name, value) {
        this.name = name;
        this.value = value;
        this.errors = [];
    }

    validate() {
        return this.errors.length === 0;
    }

    addError(message) {
        this.errors.push(message);
    }
}

class EmailField extends FormField {
    constructor(name, value) {
        // 我想先验证邮箱格式再调用父类
        if (!value.includes('@')) {
            this.errors.push('邮箱格式错误'); // ← 这行报错
        }
        
        super(name, value); // 我确实调用了 super
    }
}
```

"看起来没问题啊，" 你皱眉，"`super(name, value)` 就在构造函数里，为什么说我没调用？"

你尝试创建一个 `EmailField` 实例：

```javascript
const email = new EmailField('user_email', 'invalid-email');
```

错误再次出现。你注意到错误信息说的是"在访问 `this` **之前**"，突然意识到问题可能不是"没调用 `super`"，而是"调用 `super` 的时机"。

"难道 `super()` 必须在第一行？" 你疑惑。但那样的话，怎么在父类初始化之前做邮箱格式验证呢？这不是先有鸡还是先有蛋的问题吗？

你决定先把 `super()` 移到第一行试试：

```javascript
class EmailField extends FormField {
    constructor(name, value) {
        super(name, value); // 先调用 super
        
        if (!this.value.includes('@')) {
            this.errors.push('邮箱格式错误'); // 现在可以访问 this 了
        }
    }
}
```

这次没报错了。邮箱字段创建成功，验证也正常工作。

"所以问题是 `super()` 的调用顺序，" 你若有所思，"但为什么会有这个限制？这背后的原理是什么？"

---

## 深入 super 的本质

上午十点，你去找老张请教。他正在喝咖啡，看到你困惑的表情笑了。

"遇到 `super` 的坑了？" 老张说，"这是很多人第一次用 ES6 类继承时都会踩的坑。"

"为什么 `super()` 必须在使用 `this` 之前调用？" 你直接问，"这太不灵活了。"

"你想想构造函数是怎么工作的，" 老张反问，"当你 `new EmailField()` 时，JavaScript 需要创建一个对象，对吧？"

"对，" 你点头，"创建一个新对象，然后把 `this` 指向这个对象。"

"在普通的类中确实是这样，" 老张说，"但在派生类中——也就是用 `extends` 继承的类——规则不一样了。"

他打开浏览器控制台，边写边解释：

```javascript
// 普通类：JavaScript 自动创建 this
class BaseClass {
    constructor(name) {
        // 进入构造函数时，this 已经被创建
        // 相当于 const this = {}; (伪代码)
        this.name = name;
    }
}

// 派生类：this 必须由父类创建
class DerivedClass extends BaseClass {
    constructor(name, age) {
        // 进入构造函数时，this 还不存在
        // 必须调用 super() 让父类创建 this
        super(name); // 这行代码创建了 this
        
        // 现在 this 存在了，可以使用
        this.age = age;
    }
}
```

"等等，" 你打断他，"你是说派生类的 `this` 是由父类创建的？"

"完全正确，" 老张说，"这是 ES6 类继承的核心机制。派生类不会自动创建 `this`，而是通过 `super()` 调用父类构造函数，由父类创建 `this` 对象。"

"为什么要这样设计？" 你追问。

"为了支持内建类的继承，" 老张说，"比如你想继承 `Array` 类："

```javascript
class MyArray extends Array {
    constructor(...items) {
        super(...items); // Array 的构造函数创建特殊的数组对象
        
        // 现在 this 是一个真正的数组，有 length 等特殊行为
    }
    
    first() {
        return this[0];
    }
}

const arr = new MyArray(1, 2, 3);
console.log(arr.length); // 3 - 数组的特殊行为
console.log(arr.first()); // 1
```

"明白了，" 你恍然大悟，"如果派生类自己创建 `this`，就只是个普通对象，没有父类的特殊行为。所以必须由父类来创建。"

"正是如此，" 老张点头，"所以在派生类的构造函数中，`super()` 之前不能访问 `this`，因为 `this` 还不存在。"

---

## this 不存在的世界

上午十一点，你开始做实验，想更深入理解这个机制。

"如果我在 `super()` 之前访问 `this` 会怎样？" 你问自己。

```javascript
class Base {
    constructor(value) {
        this.value = value;
    }
}

class Derived extends Base {
    constructor(value) {
        console.log(this); // 尝试在 super() 之前访问 this
        super(value);
    }
}

try {
    new Derived(42);
} catch (e) {
    console.error(e.message);
    // ReferenceError: Must call super constructor before accessing 'this'
}
```

错误信息非常明确：在调用 super 之前访问 `this` 是引用错误，因为 `this` 根本不存在。

"那我可以在 `super()` 之前做一些不涉及 `this` 的操作吗？" 你想到。

```javascript
class EmailField extends FormField {
    constructor(name, value) {
        // 可以：参数验证和转换
        if (typeof value !== 'string') {
            throw new TypeError('邮箱必须是字符串');
        }
        
        // 可以：不涉及 this 的局部变量
        const normalizedValue = value.toLowerCase().trim();
        
        // 可以：抛出错误
        if (!normalizedValue.includes('@')) {
            throw new Error('邮箱格式错误');
        }
        
        // 现在调用 super，由父类创建 this
        super(name, normalizedValue);
        
        // super() 之后可以访问 this
        this.domain = normalizedValue.split('@')[1];
    }
}
```

你测试了这段代码：

```javascript
try {
    const email1 = new EmailField('email', 'test@example.com');
    console.log(email1.domain); // 'example.com'
    console.log(email1.value); // 'test@example.com'
} catch (e) {
    console.error('验证失败：', e.message);
}

try {
    const email2 = new EmailField('email', 'invalid');
} catch (e) {
    console.error('验证失败：', e.message); // '邮箱格式错误'
}
```

"完美！" 你说，"在 `super()` 之前可以做不涉及 `this` 的验证和数据转换，这样既满足了需求，又遵守了 JavaScript 的规则。"

---

## 忘记 super 的灾难

中午十二点，测试小林拿着一个 bug 报告找到你。

"看这个，" 小林指着代码说，"这个派生类的构造函数为什么会报错？"

```javascript
class User {
    constructor(name) {
        this.name = name;
        this.createdAt = new Date();
    }
}

class Admin extends User {
    constructor(name, permissions) {
        // 小林忘记调用 super()
        this.permissions = permissions;
        this.isAdmin = true;
    }
}

try {
    const admin = new Admin('张三', ['read', 'write']);
} catch (e) {
    console.error(e.message);
    // ReferenceError: Must call super constructor in derived class
}
```

"他忘记调用 `super()` 了，" 你指出。

"但为什么不能自动调用呢？" 小林问，"如果派生类的构造函数什么都不做，不是应该自动调用父类吗？"

"确实是这样，" 你说，"如果派生类没有定义 `constructor`，JavaScript 会自动添加一个默认的。"

你演示给小林看：

```javascript
class User {
    constructor(name) {
        this.name = name;
    }
}

// 没有 constructor
class Admin1 extends User {
    // JavaScript 自动添加：
    // constructor(...args) {
    //     super(...args);
    // }
}

const admin1 = new Admin1('张三');
console.log(admin1.name); // '张三'

// 有 constructor 但忘记 super
class Admin2 extends User {
    constructor(name, permissions) {
        // 有构造函数就必须手动调用 super
        this.permissions = permissions; // 错误！
    }
}

try {
    const admin2 = new Admin2('李四', ['read']);
} catch (e) {
    console.error('必须调用 super:', e.message);
}
```

"明白了，" 小林说，"如果不写 `constructor`，系统会自动调用 `super`；但一旦自己写了 `constructor`，就必须手动调用 `super`。"

"对，" 你说，"而且必须在使用 `this` 之前调用。"

---

## super 调用父类方法

下午两点，你在重构代码时发现 `super` 还有另一个用途。

你正在实现一个动物类的继承体系，狗类需要扩展父类的 `eat` 方法：

```javascript
class Animal {
    constructor(name) {
        this.name = name;
        this.energy = 100;
    }

    eat() {
        this.energy += 20;
        console.log(`${this.name} 正在进食，能量 +20`);
    }

    sleep() {
        this.energy += 30;
        console.log(`${this.name} 正在睡觉，能量 +30`);
    }
}

class Dog extends Animal {
    constructor(name, breed) {
        super(name);
        this.breed = breed;
    }

    eat() {
        // 想保留父类的 eat 逻辑，并添加狗特有的行为
        super.eat(); // 调用父类的 eat 方法
        
        // 添加狗特有的行为
        console.log(`(${this.breed} 摇着尾巴吃得很开心)`);
        this.happiness = (this.happiness || 0) + 10;
    }

    bark() {
        this.energy -= 5;
        console.log(`${this.name} 汪汪叫！`);
    }
}
```

你测试了这个实现：

```javascript
const dog = new Dog('旺财', '哈士奇');

dog.eat();
// '旺财 正在进食，能量 +20'
// '(哈士奇 摇着尾巴吃得很开心)'

console.log(dog.energy); // 120
console.log(dog.happiness); // 10

dog.bark();
// '旺财 汪汪叫！'

console.log(dog.energy); // 115
```

"太好了，" 你说，"`super.method()` 可以调用父类的方法，这样我就能扩展而不是完全覆盖父类的行为。"

---

## super 在静态方法中

下午三点，你发现 `super` 还可以在静态方法中使用。

你正在实现一个日志系统，子类需要调用父类的静态方法：

```javascript
class Logger {
    static level = 'INFO';
    
    static log(message) {
        console.log(`[${this.level}] ${new Date().toISOString()} - ${message}`);
    }
}

class ErrorLogger extends Logger {
    static level = 'ERROR';
    
    static log(message) {
        // 调用父类的静态方法
        super.log(message);
        
        // 添加错误特有的处理
        console.log('  ↑ 错误已记录到监控系统');
    }
}

ErrorLogger.log('数据库连接失败');
// '[ERROR] 2024-01-19T10:30:00.000Z - 数据库连接失败'
// '  ↑ 错误已记录到监控系统'
```

"原来 `super` 在静态方法中指向父类，" 你恍然大悟，"这样静态方法也能继承和扩展了。"

---

## super 的 this 绑定

下午四点，你研究了一个微妙的问题：`super.method()` 调用时，`this` 指向谁？

```javascript
class Counter {
    constructor() {
        this.count = 0;
    }

    increment() {
        this.count++;
        console.log(`Counter: ${this.count}`);
    }
}

class DoubleCounter extends Counter {
    increment() {
        // 调用两次父类的 increment
        super.increment(); // 第一次
        super.increment(); // 第二次
        
        console.log(`DoubleCounter 完成了双倍增长`);
    }
}

const counter = new DoubleCounter();
counter.increment();
// Counter: 1
// Counter: 2
// DoubleCounter 完成了双倍增长

console.log(counter.count); // 2
```

"注意，" 你自言自语，"`super.increment()` 中的 `this.count` 指向的是 `DoubleCounter` 的实例，而不是 `Counter` 的实例。"

你又做了一个实验来确认：

```javascript
class Base {
    constructor() {
        this.value = 0;
    }

    getValue() {
        return this.value; // this 指向调用者
    }
}

class Derived extends Base {
    constructor() {
        super();
        this.value = 10; // 覆盖 value
    }

    test() {
        console.log('super.getValue():', super.getValue()); // this 是 Derived 实例
        console.log('this.value:', this.value);
    }
}

const obj = new Derived();
obj.test();
// super.getValue(): 10
// this.value: 10
```

"明白了，" 你总结，"`super.method()` 调用的是父类的方法，但方法内的 `this` 仍然指向当前实例。"

---

## 构造函数返回对象的特殊情况

下午五点，老张来找你，展示了一个特殊情况。

"如果构造函数显式返回一个对象会怎样？" 老张问。

你想了想："普通构造函数返回对象的话，`new` 操作符会使用那个对象而不是 `this`。"

"对，" 老张说，"在派生类中也是一样，但有个有趣的现象："

```javascript
class Base {
    constructor() {
        this.baseProp = 'base';
        
        // 返回一个完全不同的对象
        return { custom: 'object' };
    }
}

class Derived extends Base {
    constructor() {
        super(); // 调用 Base，但 Base 返回了自定义对象
        
        // 这里的 this 是什么？
        console.log(this); // { custom: 'object' }
        
        this.derivedProp = 'derived';
    }
}

const obj = new Derived();
console.log(obj); // { custom: 'object', derivedProp: 'derived' }
console.log(obj.baseProp); // undefined
```

"看到了吗？" 老张说，"`super()` 返回的对象成为了派生类的 `this`。"

"所以如果父类构造函数返回自定义对象，" 你说，"派生类就在那个对象上添加属性，而不是在父类创建的 `this` 上。"

"对，" 老张说，"这是一个少见但需要注意的边界情况。"

---

## 总结与反思

下午六点，你整理了今天学到的关于 `super` 的知识。

你在笔记本上写下要点：

**super() 的核心规则：**
1. 派生类的 `this` 必须由父类创建
2. 必须在使用 `this` 之前调用 `super()`
3. `super()` 之前可以做不涉及 `this` 的操作
4. 如果不写 `constructor`，系统自动添加 `super(...args)`
5. 一旦写了 `constructor`，必须手动调用 `super()`

**super 的其他用途：**
- `super.method()` 调用父类的实例方法
- `super.staticMethod()` 调用父类的静态方法
- `super.method()` 中的 `this` 指向当前实例

**设计原理：**
- 支持内建类（如 `Array`）的继承
- 保证父类的特殊行为能正确继承
- 明确的初始化顺序，避免未初始化状态

"现在终于理解为什么会有这些限制了，" 你说，"不是 JavaScript 故意刁难，而是为了保证继承机制的正确性。"

你重新审视早上的 `EmailField` 代码，现在它的结构清晰合理：

```javascript
class EmailField extends FormField {
    constructor(name, value) {
        // 1. super() 之前：参数验证和转换
        if (typeof value !== 'string') {
            throw new TypeError('邮箱必须是字符串');
        }
        const normalizedValue = value.toLowerCase().trim();
        if (!normalizedValue.includes('@')) {
            throw new Error('邮箱格式错误');
        }
        
        // 2. 调用 super()：父类创建 this
        super(name, normalizedValue);
        
        // 3. super() 之后：初始化子类特有属性
        this.domain = normalizedValue.split('@')[1];
        this.localPart = normalizedValue.split('@')[0];
    }

    validate() {
        // 调用父类方法并扩展
        if (!super.validate()) {
            return false;
        }
        
        // 添加邮箱特有的验证
        const domainParts = this.domain.split('.');
        return domainParts.length >= 2 && domainParts.every(part => part.length > 0);
    }
}
```

"完美，" 你满意地关上笔记本，"既遵守了 JavaScript 的规则，又实现了所有需求。"

---

## 知识总结

**规则 1: super() 创建派生类的 this**

在派生类中，`this` 不是自动创建的，必须通过 `super()` 调用父类构造函数来创建：

```javascript
class Derived extends Base {
    constructor() {
        // this 还不存在
        super(); // 父类创建 this
        // 现在 this 存在了
        this.prop = 'value';
    }
}
```

这保证了父类的特殊行为（如 `Array` 的 length）能正确继承。

---

**规则 2: super() 必须在 this 使用前调用**

在派生类构造函数中，任何访问 `this` 的操作都必须在 `super()` 之后：

```javascript
class Derived extends Base {
    constructor(value) {
        this.value = value; // ❌ ReferenceError
        super();
        this.value = value; // ✅ 正确
    }
}
```

因为 `super()` 之前 `this` 根本不存在。

---

**规则 3: super() 前可做不涉及 this 的操作**

`super()` 之前可以进行参数验证、转换等不访问 `this` 的操作：

```javascript
class EmailField extends FormField {
    constructor(name, value) {
        if (!value.includes('@')) {
            throw new Error('格式错误'); // ✅ 不涉及 this
        }
        const normalized = value.toLowerCase(); // ✅ 局部变量
        
        super(name, normalized);
        this.domain = normalized.split('@')[1]; // ✅ super 之后
    }
}
```

---

**规则 4: 无 constructor 时的默认 super**

如果派生类没有定义 `constructor`，JavaScript 自动添加默认构造函数：

```javascript
class Derived extends Base {
    // 自动添加：
    // constructor(...args) {
    //     super(...args);
    // }
}
```

一旦自定义 `constructor`，就必须手动调用 `super()`。

---

**规则 5: super.method() 调用父类方法**

`super.method()` 调用父类的方法，但 `this` 仍指向当前实例：

```javascript
class Derived extends Base {
    method() {
        super.method(); // 调用父类方法
        // super.method() 中的 this 是 Derived 实例
    }
}
```

这允许扩展而非完全覆盖父类行为。

---

**规则 6: super 在静态方法中的使用**

静态方法中 `super` 指向父类，用于调用父类静态方法：

```javascript
class Base {
    static method() { console.log('Base'); }
}

class Derived extends Base {
    static method() {
        super.method(); // 调用 Base.method()
        console.log('Derived');
    }
}
```

---

**事故档案编号**: PROTO-2024-1887  
**影响范围**: super 关键字, 派生类构造函数, this 初始化顺序  
**根本原因**: 不理解派生类的 this 由父类创建，导致 super() 调用时机错误  
**修复成本**: 低（调整 super 位置），但需深刻理解继承机制

这是 JavaScript 世界第 87 次被记录的 super 时机事故。派生类的 `this` 不是自动创建的，而是通过 `super()` 调用父类构造函数创建。必须在访问 `this` 之前调用 `super()`，否则抛出 ReferenceError。`super()` 之前可以进行参数验证、类型转换等不涉及 `this` 的操作。如果派生类没有 `constructor`，JavaScript 自动添加 `constructor(...args) { super(...args); }`。一旦自定义构造函数，必须手动调用 `super()`。`super.method()` 调用父类方法，`this` 指向当前实例，允许扩展父类行为。静态方法中 `super` 指向父类，用于调用父类静态成员。这些限制不是刁难，而是为了支持内建类继承和保证初始化顺序的正确性。

---

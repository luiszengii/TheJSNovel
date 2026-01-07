《第 88 次记录: 静态成员 —— 类的共享财产》

---

## 重复的配置代码

周一上午九点，你盯着重构列表上的第一项任务，感到有些烦躁。

过去三个月，你们团队开发了一个复杂的数据处理系统。系统中有十几个不同的数据处理器类：`UserProcessor`、`OrderProcessor`、`ProductProcessor` 等等。每个处理器都需要访问相同的配置信息：数据库连接、API 密钥、日志级别等。

最初的实现方式是在每个处理器实例中都保存一份配置副本：

```javascript
class UserProcessor {
    constructor(config) {
        this.config = config; // 每个实例都有配置副本
        this.processedCount = 0;
    }

    process(user) {
        console.log(`使用 ${this.config.apiKey} 处理用户`);
        this.processedCount++;
    }
}

class OrderProcessor {
    constructor(config) {
        this.config = config; // 又一份配置副本
        this.processedCount = 0;
    }

    process(order) {
        console.log(`使用 ${this.config.apiKey} 处理订单`);
        this.processedCount++;
    }
}

// 使用时
const config = {
    apiKey: 'abc123',
    dbHost: 'localhost',
    logLevel: 'info'
};

const userProc1 = new UserProcessor(config);
const userProc2 = new UserProcessor(config);
const orderProc1 = new OrderProcessor(config);
const orderProc2 = new OrderProcessor(config);
```

现在你需要创建上百个处理器实例来处理大量数据，内存监控显示每个实例都存储了一份完整的配置对象副本。虽然每份配置只有几 KB，但上百个实例累积起来就是几 MB 的内存浪费。

"配置信息应该是所有处理器共享的，" 你自言自语，"不需要每个实例都保存一份。"

你想起在其他语言中见过"静态变量"的概念——属于类本身而不是实例的变量。但在 JavaScript 的构造函数时代，实现这个功能总是有点别扭：

```javascript
function UserProcessor(config) {
    this.processedCount = 0;
}

// 把配置放在构造函数上，不是实例上
UserProcessor.config = null;

UserProcessor.setConfig = function(config) {
    UserProcessor.config = config;
};
```

"这种写法看起来怪怪的，" 你皱眉，"而且很容易和实例方法混淆。ES6 的 `class` 有更好的方式吗？"

---

## 静态成员的发现

上午十点，你翻开 ES6 类的文档，发现了 `static` 关键字。

"原来有专门的语法，" 你眼前一亮，"这样代码会清晰很多。"

你开始重构第一个处理器类：

```javascript
class UserProcessor {
    // 静态属性：属于类本身
    static config = null;
    static totalInstances = 0;

    constructor() {
        this.processedCount = 0; // 实例属性
        UserProcessor.totalInstances++; // 访问静态属性
    }

    // 静态方法：属于类本身
    static setConfig(config) {
        UserProcessor.config = config;
        console.log('配置已更新:', config);
    }

    static getConfig() {
        return UserProcessor.config;
    }

    // 实例方法：属于每个实例
    process(user) {
        if (!UserProcessor.config) {
            throw new Error('请先设置配置');
        }

        console.log(`使用 API key ${UserProcessor.config.apiKey} 处理用户 ${user.name}`);
        this.processedCount++;
    }
}
```

你测试了新的实现：

```javascript
// 设置类级别的配置
UserProcessor.setConfig({
    apiKey: 'abc123',
    dbHost: 'localhost',
    logLevel: 'info'
});

// 创建多个实例，它们共享同一份配置
const proc1 = new UserProcessor();
const proc2 = new UserProcessor();
const proc3 = new UserProcessor();

console.log(UserProcessor.totalInstances); // 3

proc1.process({ name: '张三' });
proc2.process({ name: '李四' });

// 每个实例有自己的 processedCount
console.log(proc1.processedCount); // 1
console.log(proc2.processedCount); // 1

// 但共享同一个 config
console.log(proc1.constructor.config === proc2.constructor.config); // true
```

"完美！" 你说，"所有实例共享同一份配置，内存使用大幅降低，而且代码结构更清晰了。"

---

## 静态与实例的区别

上午十一点，测试小林拿着一段代码来问你。

"我不太理解静态成员和实例成员的区别，" 小林说，"看这段代码："

```javascript
class Counter {
    static totalCount = 0; // 静态属性

    constructor(name) {
        this.name = name;
        this.count = 0; // 实例属性
        Counter.totalCount++;
    }

    increment() {
        this.count++;
        Counter.totalCount++;
    }

    static getTotalCount() {
        return Counter.totalCount;
    }
}

const c1 = new Counter('计数器1');
const c2 = new Counter('计数器2');

c1.increment();
c1.increment();
c2.increment();

console.log(c1.count); // ?
console.log(c2.count); // ?
console.log(Counter.totalCount); // ?
```

"你觉得输出是什么？" 你反问。

小林想了想："第一个是 2，第二个是 1，第三个... 应该也是 3？"

"完全正确，" 你说，"让我解释一下内存布局："

你在白板上画图：

```
Counter 类对象
├── totalCount: 5 (静态属性，类级别)
└── getTotalCount: function (静态方法，类级别)

c1 实例对象
├── name: '计数器1'
├── count: 2 (实例属性，c1 特有)
└── [[Prototype]] → Counter.prototype
                    └── increment: function

c2 实例对象
├── name: '计数器2'
├── count: 1 (实例属性，c2 特有)
└── [[Prototype]] → Counter.prototype
                    └── increment: function
```

"看到了吗？" 你指着图说，"`totalCount` 只有一份，存在类对象上。所有实例通过 `Counter.totalCount` 访问同一个值。"

"但 `count` 是实例属性，" 小林说，"每个实例有自己独立的值。"

"对，" 你点头，"这就是静态和实例的本质区别。"

---

## 静态方法中的 this

中午十二点，你在实现一个工厂方法时遇到了疑惑。

```javascript
class User {
    static userCount = 0;

    constructor(name, age) {
        this.name = name;
        this.age = age;
        User.userCount++;
    }

    static createAdmin(name) {
        // 静态方法中的 this 指向谁？
        console.log(this); // ?

        const admin = new User(name, 0);
        admin.role = 'admin';
        return admin;
    }

    static getTotalCount() {
        return this.userCount; // 这里的 this 是什么？
    }
}
```

你测试了一下：

```javascript
const admin = User.createAdmin('管理员');
console.log(admin.name); // '管理员'
console.log(admin.role); // 'admin'

console.log(User.getTotalCount()); // 1
```

"原来静态方法中的 `this` 指向类本身，" 你恍然大悟，"所以 `this.userCount` 等价于 `User.userCount`。"

老张路过，看到你在研究这个问题。

"注意继承的情况，" 老张提醒：

```javascript
class User {
    static type = 'User';

    static getType() {
        return this.type; // this 会随调用者变化
    }
}

class Admin extends User {
    static type = 'Admin';
}

console.log(User.getType()); // 'User'
console.log(Admin.getType()); // 'Admin' - this 指向 Admin
```

"哇，" 你说，"静态方法中的 `this` 是动态绑定的，取决于谁调用它。"

---

## 静态成员的继承

下午两点，你发现静态成员也可以被继承。

```javascript
class Animal {
    static planet = '地球';
    static totalAnimals = 0;

    constructor(name) {
        this.name = name;
        this.constructor.totalAnimals++; // 使用 this.constructor 访问类
    }

    static getInfo() {
        return `动物生活在${this.planet}`;
    }
}

class Dog extends Animal {
    static totalAnimals = 0; // 子类可以覆盖静态属性

    constructor(name, breed) {
        super(name);
        this.breed = breed;
    }

    static getInfo() {
        return super.getInfo() + '，狗是人类的好朋友';
    }
}

// 测试继承
console.log(Animal.planet); // '地球'
console.log(Dog.planet); // '地球' - 继承自父类

console.log(Animal.getInfo()); // '动物生活在地球'
console.log(Dog.getInfo()); // '动物生活在地球，狗是人类的好朋友'

const dog1 = new Dog('旺财', '哈士奇');
const dog2 = new Dog('小黑', '柯基');
const cat = new Animal('喵喵');

console.log(Animal.totalAnimals); // 1 - 只有猫
console.log(Dog.totalAnimals); // 2 - 两只狗
```

"子类继承了父类的静态成员，" 你总结，"而且可以覆盖它们，还可以用 `super` 调用父类的静态方法。"

---

## 静态块的应用

下午三点，你发现 ES2022 引入了静态初始化块。

"如果静态属性需要复杂的初始化逻辑怎么办？" 你想到一个问题。

```javascript
class DatabaseConnection {
    static connection = null;
    static isInitialized = false;

    // 静态初始化块
    static {
        console.log('开始初始化数据库连接...');

        try {
            // 复杂的初始化逻辑
            const config = this.loadConfig();
            this.connection = this.createConnection(config);
            this.isInitialized = true;
            console.log('数据库连接初始化成功');
        } catch (error) {
            console.error('数据库连接初始化失败:', error);
            this.isInitialized = false;
        }
    }

    static loadConfig() {
        return {
            host: 'localhost',
            port: 5432,
            database: 'myapp'
        };
    }

    static createConnection(config) {
        return {
            config,
            status: 'connected',
            query: (sql) => console.log('执行查询:', sql)
        };
    }

    static query(sql) {
        if (!this.isInitialized) {
            throw new Error('数据库未初始化');
        }
        return this.connection.query(sql);
    }
}

// 类加载时自动执行静态块
// '开始初始化数据库连接...'
// '数据库连接初始化成功'

DatabaseConnection.query('SELECT * FROM users');
```

"静态块在类定义时执行，" 你说，"可以进行复杂的初始化，而不需要在类外部写初始化代码。"

---

## 实际应用：单例模式

下午四点，你用静态成员实现了一个单例模式。

```javascript
class ConfigManager {
    static instance = null;

    constructor() {
        if (ConfigManager.instance) {
            throw new Error('ConfigManager 是单例，请使用 getInstance()');
        }

        this.config = {};
        ConfigManager.instance = this;
    }

    static getInstance() {
        if (!ConfigManager.instance) {
            ConfigManager.instance = new ConfigManager();
        }
        return ConfigManager.instance;
    }

    set(key, value) {
        this.config[key] = value;
    }

    get(key) {
        return this.config[key];
    }
}

// 使用单例
const config1 = ConfigManager.getInstance();
config1.set('apiKey', 'abc123');

const config2 = ConfigManager.getInstance();
console.log(config2.get('apiKey')); // 'abc123'

console.log(config1 === config2); // true - 同一个实例

// 不能直接 new
try {
    const config3 = new ConfigManager(); // 抛出错误
} catch (e) {
    console.error(e.message);
}
```

"静态成员非常适合实现单例模式，" 你说，"确保类只有一个实例。"

---

## 静态成员的注意事项

下午五点，老张过来和你讨论静态成员的最佳实践。

"静态成员很好用，" 老张说，"但要注意几个坑。"

"第一个坑：实例方法访问静态成员，" 老张说：

```javascript
class Counter {
    static total = 0;

    constructor() {
        this.count = 0;
    }

    increment() {
        this.count++;

        // 错误：this.total 访问不到静态属性
        // this.total++; // undefined++

        // 正确：通过类名或 this.constructor
        Counter.total++; // 推荐
        // 或 this.constructor.total++; // 也可以
    }
}
```

"第二个坑：继承时的静态属性共享，" 老张继续：

```javascript
class Animal {
    static instances = []; // 危险！引用类型

    constructor(name) {
        this.name = name;
        this.constructor.instances.push(this);
    }
}

class Dog extends Animal {}
class Cat extends Animal {}

new Dog('旺财');
new Cat('喵喵');

// 所有动物都在同一个数组里
console.log(Animal.instances.length); // 2
console.log(Dog.instances === Cat.instances); // true - 共享同一个数组
```

"如果想让每个子类有自己的 `instances`，" 老张说，"需要在每个子类中重新定义："

```javascript
class Dog extends Animal {
    static instances = []; // 子类自己的数组
}

class Cat extends Animal {
    static instances = []; // 子类自己的数组
}

new Dog('旺财');
new Cat('喵喵');

console.log(Dog.instances.length); // 1
console.log(Cat.instances.length); // 1
console.log(Dog.instances === Cat.instances); // false - 不同数组
```

---

## 总结与反思

下午六点，你整理了静态成员的知识。

**核心概念：**
- 静态成员属于类本身，不是实例
- 用 `static` 关键字定义
- 所有实例共享同一份静态成员
- 适合存储配置、计数器、工厂方法等

**访问方式：**
- 静态成员：`ClassName.member` 或静态方法内 `this.member`
- 实例访问静态成员：`this.constructor.member`
- 静态方法内 `this` 指向类本身（或子类）

**继承行为：**
- 子类继承父类静态成员
- 可以覆盖父类静态成员
- 引用类型静态属性会被共享（需注意）
- 静态方法中可用 `super` 调用父类静态方法

**最佳实践：**
- 配置信息用静态属性存储
- 工厂方法用静态方法实现
- 避免静态属性存储可变的引用类型
- 单例模式用静态成员实现

---

## 知识总结

**规则 1: 静态成员属于类而非实例**

静态成员用 `static` 关键字定义，属于类本身：

```javascript
class MyClass {
    static staticProp = 'value'; // 静态属性
    instanceProp = 'value'; // 实例属性

    static staticMethod() {} // 静态方法
    instanceMethod() {} // 实例方法
}

MyClass.staticProp; // 通过类访问
new MyClass().instanceProp; // 通过实例访问
```

所有实例共享同一份静态成员。

---

**规则 2: 静态方法中的 this 指向类**

静态方法内 `this` 指向类本身（或调用的子类）：

```javascript
class Base {
    static name = 'Base';
    static getName() {
        return this.name; // this 是类
    }
}

class Derived extends Base {
    static name = 'Derived';
}

Base.getName(); // 'Base'
Derived.getName(); // 'Derived' - this 指向 Derived
```

---

**规则 3: 实例访问静态成员**

实例方法中通过 `ClassName` 或 `this.constructor` 访问静态成员：

```javascript
class Counter {
    static total = 0;

    increment() {
        Counter.total++; // 推荐
        // 或 this.constructor.total++;
    }
}
```

不能用 `this.total` 访问静态属性。

---

**规则 4: 静态成员的继承**

子类继承父类的静态成员，可以覆盖：

```javascript
class Animal {
    static type = 'Animal';
    static getInfo() { return this.type; }
}

class Dog extends Animal {
    static type = 'Dog'; // 覆盖
    static getInfo() {
        return super.getInfo() + '!'; // 调用父类静态方法
    }
}
```

---

**规则 5: 静态属性共享陷阱**

引用类型的静态属性会被子类共享：

```javascript
class Base {
    static arr = []; // 危险！
}

class A extends Base {}
class B extends Base {}

A.arr.push(1);
console.log(B.arr); // [1] - 共享同一个数组
```

每个子类需要重新定义自己的静态属性。

---

**规则 6: 静态初始化块**

ES2022 静态块用于复杂初始化：

```javascript
class Config {
    static settings;

    static {
        // 类加载时执行
        this.settings = this.loadSettings();
    }

    static loadSettings() { /* 复杂逻辑 */ }
}
```

---

**事故档案编号**: PROTO-2024-1888
**影响范围**: 静态属性, 静态方法, 类级别成员, 内存优化
**根本原因**: 混淆静态成员和实例成员，导致内存浪费或访问错误
**修复成本**: 低（添加 static 关键字），理解类与实例的区别

这是 JavaScript 世界第 88 次被记录的静态成员事故。静态成员用 `static` 关键字定义，属于类本身而非实例，所有实例共享。通过类名访问（`ClassName.member`），静态方法内 `this` 指向类。实例方法通过 `this.constructor.member` 访问静态成员。子类继承父类静态成员，可以覆盖，静态方法中可用 `super` 调用父类。引用类型静态属性会被子类共享，需在子类中重新定义。适用场景：配置信息、计数器、工厂方法、单例模式。静态初始化块（ES2022）用于复杂初始化逻辑。

---

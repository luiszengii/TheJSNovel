《第 89 次记录: 私有字段 —— 真正的封装》

---

## 暴露的内部状态

周二上午九点，你收到了一封来自安全团队的邮件，标题是"严重安全隐患：用户密码哈希可被外部访问"。

你的心跳加速，立即打开邮件。安全工程师附上了一段测试代码：

```javascript
class User {
    constructor(username, password) {
        this.username = username;
        this._passwordHash = this.hashPassword(password);
        this._loginAttempts = 0;
        this._isLocked = false;
    }

    hashPassword(password) {
        // 简化的哈希函数
        return `hash_${password}_${Date.now()}`;
    }

    login(password) {
        if (this._isLocked) {
            throw new Error('账户已锁定');
        }

        if (this.hashPassword(password) === this._passwordHash) {
            this._loginAttempts = 0;
            return true;
        }

        this._loginAttempts++;
        if (this._loginAttempts >= 3) {
            this._isLocked = true;
        }
        return false;
    }
}
```

邮件中写道："虽然使用了下划线前缀表示'私有'，但这只是命名约定，任何人都可以直接访问和修改这些属性："

```javascript
const user = new User('alice', 'secret123');

// 直接访问"私有"属性
console.log(user._passwordHash); // 暴露了密码哈希
console.log(user._loginAttempts); // 0

// 甚至可以修改
user._loginAttempts = 0; // 重置登录尝试次数
user._isLocked = false; // 解锁账户
user._passwordHash = 'hacked'; // 修改密码哈希
```

"下划线只是君子协定，" 邮件继续写道，"恶意用户可以轻易绕过所有安全机制。我们需要真正的私有属性。"

你感到后背发凉。这个 `User` 类在生产环境已经运行了半年，处理着几十万用户的认证。虽然还没有发现实际的安全事故，但这个漏洞确实存在。

"JavaScript 有真正的私有属性吗？" 你立即开始搜索。

---

## 私有字段的发现

上午十点，你找到了 ES2022 引入的私有字段特性。

"用 `#` 前缀！" 你眼前一亮，"这不是注释，而是语法级别的私有标记。"

你立即开始重构 `User` 类：

```javascript
class User {
    // 私有字段声明（必须在类体顶部）
    #passwordHash;
    #loginAttempts = 0;
    #isLocked = false;

    constructor(username, password) {
        this.username = username; // 公有字段
        this.#passwordHash = this.#hashPassword(password);
    }

    // 私有方法
    #hashPassword(password) {
        return `hash_${password}_${Date.now()}`;
    }

    login(password) {
        if (this.#isLocked) {
            throw new Error('账户已锁定');
        }

        if (this.#hashPassword(password) === this.#passwordHash) {
            this.#loginAttempts = 0;
            return true;
        }

        this.#loginAttempts++;
        if (this.#loginAttempts >= 3) {
            this.#isLocked = true;
        }
        return false;
    }

    // 提供受控的访问接口
    isLocked() {
        return this.#isLocked;
    }

    getLoginAttempts() {
        return this.#loginAttempts;
    }
}
```

你迫不及待地测试安全性：

```javascript
const user = new User('alice', 'secret123');

// 尝试访问私有字段
try {
    console.log(user.#passwordHash); // 语法错误！
} catch (e) {
    console.error('无法访问私有字段');
}

// 甚至无法通过括号访问
console.log(user['#passwordHash']); // undefined
console.log(user._passwordHash); // undefined

// 也无法通过 Object.keys 看到
console.log(Object.keys(user)); // ['username']
console.log(Object.getOwnPropertyNames(user)); // ['username']

// 只能通过公有方法访问
console.log(user.isLocked()); // false
console.log(user.getLoginAttempts()); // 0
```

"太完美了！" 你激动地说，"私有字段在类外部完全不可访问，这才是真正的封装。"

---

## 私有字段的硬性规则

上午十一点，你在测试过程中遇到了一些限制。

"私有字段必须先声明，" 你发现第一个规则：

```javascript
class Test {
    constructor() {
        this.#value = 42; // SyntaxError: Private field '#value' must be declared
    }
}

// 正确的做法
class Test {
    #value; // 必须先声明

    constructor() {
        this.#value = 42; // 现在可以了
    }
}
```

"私有字段不能在类外部动态添加，" 你发现第二个规则：

```javascript
class Box {
    #content;

    setContent(value) {
        this.#content = value;
    }
}

const box = new Box();
box.#newField = 'test'; // SyntaxError: 类外部无法访问私有字段
```

"私有字段名是严格区分大小写的，" 你发现第三个规则：

```javascript
class Case {
    #Value; // 大写 V
    #value; // 小写 v - 这是两个不同的字段

    constructor() {
        this.#Value = 1;
        this.#value = 2;
    }

    getValues() {
        return [this.#Value, this.#value]; // [1, 2]
    }
}
```

老张走过来看你在研究私有字段。

"还有一个重要的限制，" 老张说，"私有字段不能被继承或覆盖。"

```javascript
class Parent {
    #secret = 'parent secret';

    getSecret() {
        return this.#secret;
    }
}

class Child extends Parent {
    #secret = 'child secret'; // 这是完全不同的私有字段

    getChildSecret() {
        return this.#secret; // 访问子类自己的 #secret
    }

    testParentSecret() {
        // 无法访问父类的 #secret
        // return super.#secret; // SyntaxError
        
        // 只能通过父类的公有方法访问
        return this.getSecret(); // 调用父类方法，访问父类的 #secret
    }
}

const child = new Child();
console.log(child.getSecret()); // 'parent secret' - 父类的
console.log(child.getChildSecret()); // 'child secret' - 子类的
console.log(child.testParentSecret()); // 'parent secret'
```

"所以父子类的 `#secret` 是两个完全独立的字段，" 你理解了，"即使名字相同。"

---

## in 操作符检查私有字段

中午十二点，你发现了一个有用的特性。

"怎么判断对象是否有某个私有字段？" 你想到一个问题。

```javascript
class Box {
    #content;

    constructor(content) {
        this.#content = content;
    }

    // 检查另一个对象是否是 Box 实例
    static isBox(obj) {
        return #content in obj; // ES2022: 私有字段 in 检查
    }

    // 安全的合并方法
    mergeFrom(other) {
        if (#content in other) {
            // other 也有 #content 私有字段，是同类
            const temp = other.#content;
            this.#content = this.#content + ' + ' + temp;
        } else {
            throw new TypeError('只能合并 Box 实例');
        }
    }
}

const box1 = new Box('内容1');
const box2 = new Box('内容2');
const fake = { content: '假的' };

console.log(Box.isBox(box1)); // true
console.log(Box.isBox(fake)); // false

box1.mergeFrom(box2); // 成功
// box1.mergeFrom(fake); // TypeError
```

"太聪明了，" 你说，"用 `in` 操作符可以安全地检查私有字段的存在，而不会抛出错误。"

---

## 私有方法的威力

下午两点，你开始重构一个包含复杂内部逻辑的类。

之前的代码用下划线表示"私有"方法，但外部仍然可以调用：

```javascript
class PaymentProcessor {
    constructor(apiKey) {
        this._apiKey = apiKey;
    }

    processPayment(amount) {
        const token = this._generateToken();
        const signature = this._signRequest(token, amount);
        return this._sendRequest(token, signature, amount);
    }

    _generateToken() {
        return Math.random().toString(36).substring(7);
    }

    _signRequest(token, amount) {
        return `sign_${token}_${amount}_${this._apiKey}`;
    }

    _sendRequest(token, signature, amount) {
        console.log('发送支付请求:', { token, signature, amount });
        return { success: true, transactionId: token };
    }
}

const processor = new Processor('key123');

// 问题：外部可以调用"私有"方法
processor._generateToken(); // 可以调用
processor._signRequest('fake', 100); // 可以调用
```

现在用私有方法重构：

```javascript
class PaymentProcessor {
    #apiKey;

    constructor(apiKey) {
        this.#apiKey = apiKey;
    }

    processPayment(amount) {
        const token = this.#generateToken();
        const signature = this.#signRequest(token, amount);
        return this.#sendRequest(token, signature, amount);
    }

    // 私有方法：外部完全不可访问
    #generateToken() {
        return Math.random().toString(36).substring(7);
    }

    #signRequest(token, amount) {
        return `sign_${token}_${amount}_${this.#apiKey}`;
    }

    #sendRequest(token, signature, amount) {
        console.log('发送支付请求:', { token, signature, amount });
        return { success: true, transactionId: token };
    }
}

const processor = new PaymentProcessor('key123');

// 公有方法正常工作
const result = processor.processPayment(100);
console.log(result); // { success: true, transactionId: '...' }

// 私有方法完全不可访问
try {
    processor.#generateToken(); // SyntaxError
} catch (e) {
    console.error('私有方法不可访问');
}
```

"现在内部实现完全隐藏了，" 你满意地说，"外部只能通过 `processPayment` 公有接口使用，无法绕过安全检查。"

---

## 私有字段与闭包的对比

下午三点，前端小王问了一个问题。

"之前我们用闭包实现私有属性，" 小王说，"和私有字段有什么区别？"

"好问题，" 你说，"让我对比一下。"

```javascript
// 方式 1: 闭包实现私有
function createUser(username, password) {
    // 私有变量：在闭包中
    let passwordHash = hashPassword(password);
    let loginAttempts = 0;

    return {
        username: username, // 公有属性

        login(pwd) {
            if (hashPassword(pwd) === passwordHash) {
                loginAttempts = 0;
                return true;
            }
            loginAttempts++;
            return false;
        },

        getAttempts() {
            return loginAttempts;
        }
    };

    function hashPassword(pwd) {
        return `hash_${pwd}`;
    }
}

// 方式 2: 私有字段
class User {
    #passwordHash;
    #loginAttempts = 0;

    constructor(username, password) {
        this.username = username;
        this.#passwordHash = this.#hashPassword(password);
    }

    login(password) {
        if (this.#hashPassword(password) === this.#passwordHash) {
            this.#loginAttempts = 0;
            return true;
        }
        this.#loginAttempts++;
        return false;
    }

    getAttempts() {
        return this.#loginAttempts;
    }

    #hashPassword(password) {
        return `hash_${password}`;
    }
}
```

"两种方式的对比：" 你列出表格：

| 特性 | 闭包 | 私有字段 |
|------|------|----------|
| 语法 | 函数 + return | class + # |
| 性能 | 每个实例有独立方法副本 | 所有实例共享方法 |
| 内存 | 较高（闭包保存环境） | 较低（共享原型方法） |
| 继承 | 不支持 extends | 支持继承 |
| instanceof | 不支持 | 支持 |
| 语义 | 需要理解闭包 | 语法清晰明确 |
| 兼容性 | 所有浏览器 | 需要现代浏览器 |

"闭包方式每个对象都有独立的方法，" 你说，"而私有字段的方法在原型上共享，内存效率更高。"

---

## 私有静态字段

下午四点，你发现私有字段也可以是静态的。

```javascript
class Database {
    // 私有静态字段：整个类共享
    static #connections = [];
    static #maxConnections = 10;

    #connectionId;

    constructor() {
        if (Database.#connections.length >= Database.#maxConnections) {
            throw new Error(`最多只能有 ${Database.#maxConnections} 个连接`);
        }

        this.#connectionId = Math.random().toString(36);
        Database.#connections.push(this);
    }

    close() {
        const index = Database.#connections.indexOf(this);
        if (index > -1) {
            Database.#connections.splice(index, 1);
        }
    }

    // 私有静态方法
    static #validateConnection(conn) {
        return Database.#connections.includes(conn);
    }

    // 公有静态方法
    static getActiveConnections() {
        return Database.#connections.length;
    }

    isActive() {
        return Database.#validateConnection(this);
    }
}

const db1 = new Database();
const db2 = new Database();

console.log(Database.getActiveConnections()); // 2

db1.close();
console.log(Database.getActiveConnections()); // 1

// 私有静态字段完全不可访问
// Database.#connections; // SyntaxError
// Database.#maxConnections; // SyntaxError
```

"私有静态字段对于实现单例模式或连接池特别有用，" 你说。

---

## WeakMap 替代方案

下午五点，老张给你看了一个在私有字段出现之前的解决方案。

"如果需要兼容旧浏览器，" 老张说，"可以用 `WeakMap` 模拟私有字段。"

```javascript
const privateData = new WeakMap();

class User {
    constructor(username, password) {
        this.username = username;

        // 用 WeakMap 存储私有数据
        privateData.set(this, {
            passwordHash: this.hashPassword(password),
            loginAttempts: 0,
            isLocked: false
        });
    }

    hashPassword(password) {
        return `hash_${password}`;
    }

    login(password) {
        const data = privateData.get(this);

        if (data.isLocked) {
            throw new Error('账户已锁定');
        }

        if (this.hashPassword(password) === data.passwordHash) {
            data.loginAttempts = 0;
            return true;
        }

        data.loginAttempts++;
        if (data.loginAttempts >= 3) {
            data.isLocked = true;
        }
        return false;
    }

    isLocked() {
        return privateData.get(this).isLocked;
    }
}

const user = new User('alice', 'secret');

// 外部无法访问 privateData.get(user)
// 因为 privateData 变量在模块作用域中
console.log(user.username); // 'alice' - 公有
console.log(user.passwordHash); // undefined - 私有
```

"WeakMap 的优势是兼容性好，" 老张说，"劣势是需要额外管理 WeakMap 变量，而且语法不如私有字段清晰。"

---

## 总结与反思

下午六点，你完成了 `User` 类的安全重构，发送邮件给安全团队。

你在重构报告中写道：

**重构前的问题：**
- 下划线前缀只是命名约定，不是真正的私有
- 敏感数据可被外部访问和修改
- 安全机制可被轻易绕过

**重构后的改进：**
- 使用 `#` 私有字段，语法级别的封装
- 敏感数据在类外部完全不可访问
- 只能通过公有方法的受控接口访问

**私有字段的优势：**
- 真正的私有性，语法保证
- 清晰的 API 边界
- 更好的封装和安全性
- 支持私有方法和私有静态成员

**注意事项：**
- 私有字段必须先声明
- 不能继承或覆盖
- 父子类的同名私有字段是独立的
- 用 `#field in obj` 检查存在性

"现在的代码既安全又清晰，" 你关上笔记本，"JavaScript 终于有了真正的私有属性。"

---

## 知识总结

**规则 1: # 前缀定义私有字段**

私有字段用 `#` 前缀定义，在类外部完全不可访问：

```javascript
class Box {
    #content; // 私有字段声明

    constructor(value) {
        this.#content = value; // 类内部可访问
    }
}

const box = new Box('secret');
box.#content; // SyntaxError
```

---

**规则 2: 私有字段必须先声明**

私有字段必须在类体顶部声明，不能动态添加：

```javascript
class Test {
    #field; // 必须先声明

    constructor() {
        this.#field = 'value'; // ✅
        this.#newField = 'value'; // ❌ SyntaxError
    }
}
```

---

**规则 3: 私有字段不能继承**

父类和子类的同名私有字段是完全独立的：

```javascript
class Parent {
    #secret = 'parent';
}

class Child extends Parent {
    #secret = 'child'; // 独立的私有字段
}
```

子类无法直接访问父类的私有字段。

---

**规则 4: 用 in 检查私有字段**

`#field in obj` 检查对象是否有私有字段：

```javascript
class Box {
    #content;

    static isBox(obj) {
        return #content in obj; // true/false
    }
}
```

这是检查对象类型的安全方式。

---

**规则 5: 私有方法和私有静态成员**

私有方法和私有静态字段/方法也用 `#` 前缀：

```javascript
class Database {
    static #pool = []; // 私有静态字段

    #connectionId; // 私有实例字段

    #connect() { /* 私有方法 */ }

    static #validatePool() { /* 私有静态方法 */ }
}
```

---

**规则 6: 私有字段 vs 闭包 vs WeakMap**

三种私有化方案对比：

| 方案 | 优势 | 劣势 |
|------|------|------|
| `#` 私有字段 | 语法清晰，共享方法，支持继承 | 需现代浏览器 |
| 闭包 | 兼容性好，真正私有 | 每实例有方法副本，不支持继承 |
| WeakMap | 兼容性好，支持继承 | 语法繁琐，需管理 WeakMap |

优先使用私有字段，需兼容性时用 WeakMap。

---

**事故档案编号**: PROTO-2024-1889
**影响范围**: 私有字段, 数据封装, 安全性, # 语法
**根本原因**: 使用下划线约定表示私有，实际可被外部访问导致安全漏洞
**修复成本**: 中（重构为私有字段），需现代浏览器支持

这是 JavaScript 世界第 89 次被记录的封装安全事故。JavaScript 的 `#` 私有字段提供语法级别的真正私有性，在类外部完全不可访问。私有字段必须在类体顶部声明，不能动态添加。父子类的同名私有字段是独立的，子类无法访问父类私有字段。用 `#field in obj` 安全检查私有字段存在性。支持私有方法和私有静态成员。相比闭包和 WeakMap，私有字段语法清晰、性能更好、支持继承。下划线前缀只是命名约定，不提供真正的私有性，应避免在安全敏感场景使用。

---

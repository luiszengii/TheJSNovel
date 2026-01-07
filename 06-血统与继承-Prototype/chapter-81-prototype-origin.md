《第 81 次记录: 原型的诞生 —— 继承的起点》

---

## 神秘的方法来源

周四上午十点，你在调试一个对象时发现了一个奇怪的现象。

```javascript
const user = {
    name: '张三',
    age: 25
};

console.log(user.toString()); // '[object Object]'
```

"等等，" 你困惑地说，"我从来没有给 `user` 定义过 `toString` 方法，它是从哪来的？"

你检查了对象的属性：

```javascript
console.log(Object.keys(user)); // ['name', 'age'] - 没有 toString

console.log(user.hasOwnProperty('toString')); // false

// 但确实可以调用
console.log(typeof user.toString); // 'function'
```

"明明不是自有属性，却能访问到，" 你自言自语，"这是 JavaScript 的黑魔法吗？"

前端小王恰好路过，看到你的疑惑，笑着说："这不是黑魔法，这是原型。"

"原型？" 你更困惑了。

---

## 追踪方法的源头

上午十点半，老张过来给你解释。

"每个对象都有一个隐藏的链接，" 老张说，"指向另一个对象，叫做原型(prototype)。当你访问对象没有的属性时，JavaScript 会自动去原型上查找。"

"怎么查看这个原型？" 你问。

"有两种方式，" 老张在控制台演示：

```javascript
const user = { name: '张三' };

// 方式 1: __proto__ 访问器属性
console.log(user.__proto__);

// 方式 2: Object.getPrototypeOf() 方法（推荐）
console.log(Object.getPrototypeOf(user));

// 两者是同一个对象
console.log(user.__proto__ === Object.getPrototypeOf(user)); // true
```

控制台输出了一个包含许多方法的对象：

```javascript
{
    constructor: ƒ Object()
    hasOwnProperty: ƒ hasOwnProperty()
    toString: ƒ toString()
    valueOf: ƒ valueOf()
    // ... 更多方法
}
```

"看到了吗？" 老张指着输出，"`toString` 就在这里！所有通过 `{}` 或 `new Object()` 创建的对象，原型都指向这个 `Object.prototype`。"

你恍然大悟："所以 `user.toString()` 实际上是调用了 `user.__proto__.toString()`？"

"完全正确，" 老张点头。

---

## 原型的作用

上午十一点，老张继续解释原型的意义。

"想象你要创建 100 个用户对象，" 老张说，"每个用户都需要 `greet` 方法。"

```javascript
// 方式 1: 每个对象都有自己的 greet 方法
function createUser1(name) {
    return {
        name: name,
        greet: function() {
            console.log(`你好，我是 ${this.name}`);
        }
    };
}

const users1 = [];
for (let i = 0; i < 100; i++) {
    users1.push(createUser1(`用户${i}`));
}
```

"这样有什么问题？" 你问。

"内存浪费，" 老张说，"100 个用户对象，就有 100 个独立的 `greet` 函数，虽然它们功能完全一样。"

```javascript
console.log(users1[0].greet === users1[1].greet); // false - 不同的函数
```

"如果用原型，" 老张继续演示：

```javascript
// 方式 2: 把 greet 放在原型上
function createUser2(name) {
    const user = Object.create(userPrototype);
    user.name = name;
    return user;
}

const userPrototype = {
    greet: function() {
        console.log(`你好，我是 ${this.name}`);
    }
};

const users2 = [];
for (let i = 0; i < 100; i++) {
    users2.push(createUser2(`用户${i}`));
}

// 所有用户共享同一个 greet 方法
console.log(users2[0].greet === users2[1].greet); // true - 同一个函数
```

"这样只有一个 `greet` 函数，" 你说，"被 100 个用户共享。"

"对，" 老张说，"这就是原型存在的核心价值 —— 方法共享，节省内存。"

---

## Object.create 的魔法

上午十一点半，你开始研究 `Object.create()`。

"`Object.create()` 做了什么？" 你问。

"它创建一个新对象，并把新对象的原型设置为你传入的对象，" 老张解释：

```javascript
const parent = {
    greet: function() {
        console.log('你好');
    }
};

const child = Object.create(parent);

// child 的原型是 parent
console.log(Object.getPrototypeOf(child) === parent); // true

// child 可以访问 parent 的方法
child.greet(); // '你好'

// 但 greet 不是 child 自己的属性
console.log(child.hasOwnProperty('greet')); // false
```

"相当于手动设置了对象的原型，" 你说。

"对，" 老张继续，"在 `Object.create` 出现之前，JavaScript 程序员用构造函数和 `new` 来实现原型继承。"

---

## 构造函数与原型

中午十二点，老张开始讲解构造函数模式。

"JavaScript 最传统的创建对象方式是构造函数，" 老张说：

```javascript
// 构造函数（约定用大写开头）
function User(name, age) {
    this.name = name;
    this.age = age;
}

// 在构造函数的 prototype 上添加方法
User.prototype.greet = function() {
    console.log(`你好，我是 ${this.name}`);
};

User.prototype.getAge = function() {
    return this.age;
};

// 用 new 创建实例
const user1 = new User('张三', 25);
const user2 = new User('李四', 30);

user1.greet(); // '你好，我是张三'
user2.greet(); // '你好，我是李四'

// 两个实例共享原型方法
console.log(user1.greet === user2.greet); // true
```

"所以 `new` 操作符做了什么？" 你问。

"四件事，" 老张说着在纸上写下：

```javascript
function User(name, age) {
    // 1. 创建一个新对象
    // const this = {};

    // 2. 设置新对象的原型为 User.prototype
    // Object.setPrototypeOf(this, User.prototype);

    // 3. 执行构造函数，this 指向新对象
    this.name = name;
    this.age = age;

    // 4. 返回 this（除非构造函数显式返回对象）
    // return this;
}
```

"明白了，" 你说，"`new` 自动把新对象的原型指向了 `User.prototype`。"

---

## 原型与实例的关系

下午两点，你开始探索原型和实例之间的关系。

"每个函数都有 `prototype` 属性吗？" 你问。

"对，" 老张说，"但要注意区分两个概念：函数的 `prototype` 属性，和对象的 `[[Prototype]]` 内部槽。"

```javascript
function User(name) {
    this.name = name;
}

// 函数的 prototype 属性（给 new 用的）
console.log(User.prototype); // {constructor: ƒ User()}

// 函数自己的原型（函数也是对象）
console.log(Object.getPrototypeOf(User)); // ƒ () { [native code] }

const user = new User('张三');

// 实例的原型
console.log(Object.getPrototypeOf(user)); // {constructor: ƒ User()}

// 实例的原型 === 构造函数的 prototype
console.log(Object.getPrototypeOf(user) === User.prototype); // true
```

"有点绕，" 你说。

"画个图就清楚了，" 老张在纸上画：

```
User 函数对象
├── prototype 属性 ──────────┐
│                           │
│                           ▼
│                    User.prototype 对象
│                    ├── constructor: User
│                    ├── greet: function
│                    └── [[Prototype]]: Object.prototype
│
└── [[Prototype]] ─────────────> Function.prototype


user 实例对象
├── name: '张三'
└── [[Prototype]] ──────────> User.prototype 对象
```

"所以，" 你总结，"函数有 `prototype` 属性，对象有 `[[Prototype]]` 内部槽（通过 `__proto__` 或 `getPrototypeOf` 访问）。"

"完全正确，" 老张说。

---

## constructor 属性

下午三点，你注意到原型对象上有个 `constructor` 属性。

```javascript
function User(name) {
    this.name = name;
}

console.log(User.prototype.constructor === User); // true

const user = new User('张三');
console.log(user.constructor === User); // true
```

"`constructor` 有什么用？" 你问。

"它指回构造函数本身，" 老张说，"可以用来创建同类型的新对象。"

```javascript
const user1 = new User('张三');

// 用 constructor 创建同类型对象
const user2 = new user1.constructor('李四');

console.log(user2 instanceof User); // true
```

"但要小心，" 老张警告，"如果你覆盖了整个 `prototype` 对象，`constructor` 就丢失了。"

```javascript
function User(name) {
    this.name = name;
}

// 错误的做法：直接覆盖 prototype
User.prototype = {
    greet: function() {
        console.log(`你好，我是 ${this.name}`);
    }
};

const user = new User('张三');
console.log(user.constructor === User); // false - constructor 丢失了
console.log(user.constructor === Object); // true - 回退到 Object
```

"怎么修复？" 你问。

"手动恢复 `constructor`，" 老张说：

```javascript
User.prototype = {
    constructor: User, // 恢复 constructor
    greet: function() {
        console.log(`你好，我是 ${this.name}`);
    }
};

const user = new User('张三');
console.log(user.constructor === User); // true
```

---

## 动态修改原型

下午四点，测试小林提出了一个问题。

"如果我在创建实例后修改原型，实例会受影响吗？" 小林问。

你测试了一下：

```javascript
function User(name) {
    this.name = name;
}

const user1 = new User('张三');

// 在原型上添加新方法
User.prototype.greet = function() {
    console.log(`你好，我是 ${this.name}`);
};

// 已创建的实例可以访问新方法！
user1.greet(); // '你好，我是张三'

const user2 = new User('李四');
user2.greet(); // '你好，我是李四'
```

"太神奇了，" 小林说，"`user1` 创建时原型上还没有 `greet` 方法，但后来添加了就能用。"

"因为原型是活的，" 老张解释，"实例通过引用访问原型，而不是复制原型。所以原型的任何变化都会立即反映到所有实例上。"

"这是好事还是坏事？" 你问。

"看场景，" 老张说，"好处是可以动态扩展功能，坏处是可能造成意外的影响。比如修改内建对象的原型（猴子补丁），可能影响所有代码。"

---

## 原型的重新赋值

下午五点，你发现了一个陷阱。

"如果我完全替换 `prototype`，已有实例会怎样？" 你问。

```javascript
function User(name) {
    this.name = name;
}

User.prototype.greet = function() {
    console.log('旧的 greet');
};

const user1 = new User('张三');
user1.greet(); // '旧的 greet'

// 完全替换 prototype
User.prototype = {
    constructor: User,
    greet: function() {
        console.log('新的 greet');
    }
};

// 旧实例还是指向旧原型！
user1.greet(); // 还是'旧的 greet'

// 新实例指向新原型
const user2 = new User('李四');
user2.greet(); // '新的 greet'

// 两个实例的原型不同
console.log(Object.getPrototypeOf(user1) === Object.getPrototypeOf(user2)); // false
```

"原来实例保存的是创建时的原型引用，" 你恍然大悟，"替换 `prototype` 不影响已有实例。"

"对，" 老张说，"所以如果要让所有实例受益，应该在原型上添加或修改方法，而不是替换整个原型。"

---

## 实际应用场景

下午五点半，你开始思考原型的实际应用。

"原型最适合什么场景？" 你问。

"需要创建大量相似对象的场景，" 老张说，"比如游戏中的角色、DOM 节点、数据模型等。"

```javascript
// 游戏角色系统
function Character(name, hp) {
    this.name = name;
    this.hp = hp;
}

Character.prototype.attack = function(target) {
    console.log(`${this.name} 攻击了 ${target.name}`);
    target.hp -= 10;
};

Character.prototype.heal = function() {
    this.hp += 20;
    console.log(`${this.name} 恢复了生命值`);
};

// 创建 1000 个角色，它们共享方法
const characters = [];
for (let i = 0; i < 1000; i++) {
    characters.push(new Character(`角色${i}`, 100));
}

// 所有角色共享同一个 attack 和 heal 方法
console.log(characters[0].attack === characters[999].attack); // true
```

"这样内存效率很高，" 你说。

"对，" 老张点头，"但要注意，原型上只适合放方法和常量，不要放会变化的数据。"

```javascript
// 错误示例
function User(name) {
    this.name = name;
}

User.prototype.friends = []; // 危险！共享数组

const user1 = new User('张三');
const user2 = new User('李四');

user1.friends.push('王五');

// user2 的 friends 也被修改了！
console.log(user2.friends); // ['王五']
```

"因为所有实例共享同一个数组，" 你说，"所以应该把会变化的数据放在实例自己身上。"

---

## 总结与反思

晚上六点，你整理今天学到的知识。

**原型系统的核心概念：**
- 每个对象都有一个原型（`[[Prototype]]`）
- 访问对象没有的属性时，会自动去原型上查找
- 原型的主要价值是方法共享，节省内存
- 构造函数的 `prototype` 属性会成为实例的原型

**常见陷阱：**
- 函数的 `prototype` ≠ 函数自己的原型
- 在原型上放引用类型数据（数组、对象）会被所有实例共享
- 完全替换 `prototype` 不会影响已创建的实例
- 覆盖 `prototype` 会丢失 `constructor` 属性

你保存了文档，明天准备深入学习原型链的查找机制。

---

## 知识总结

**规则 1: 对象的原型链接**

每个对象都有一个内部槽 `[[Prototype]]`（通过 `__proto__` 访问器或 `Object.getPrototypeOf()` 获取），指向另一个对象：

```javascript
const obj = {};
console.log(obj.__proto__ === Object.prototype); // true
console.log(Object.getPrototypeOf(obj) === Object.prototype); // true
```

访问对象没有的属性时，JavaScript 自动沿原型链查找。这是继承的基础机制。

---

**规则 2: 构造函数与 prototype 属性**

函数的 `prototype` 属性是一个对象，用 `new` 创建实例时，实例的 `[[Prototype]]` 会指向构造函数的 `prototype`：

```javascript
function User(name) {
    this.name = name;
}

const user = new User('张三');
console.log(Object.getPrototypeOf(user) === User.prototype); // true
```

注意：函数的 `prototype` 属性 ≠ 函数自己的 `[[Prototype]]`。

---

**规则 3: new 操作符的四步机制**

`new` 操作符创建实例时执行四步：

1. 创建空对象 `{}`
2. 设置对象的 `[[Prototype]]` 为构造函数的 `prototype`
3. 执行构造函数，`this` 指向新对象
4. 返回 `this`（除非构造函数显式返回对象）

这是 JavaScript 实现类式继承的核心机制。

---

**规则 4: constructor 属性的作用与丢失**

原型对象默认有 `constructor` 属性指向构造函数：

```javascript
function User(name) { this.name = name; }
console.log(User.prototype.constructor === User); // true
```

覆盖整个 `prototype` 对象会丢失 `constructor`：

```javascript
User.prototype = { greet: function() {} };
console.log(User.prototype.constructor === User); // false - 丢失了
```

解决方案：手动恢复 `constructor: User` 属性。

---

**规则 5: 原型的动态性**

原型的修改会立即影响所有实例（因为实例通过引用访问原型）：

```javascript
function User(name) { this.name = name; }
const user = new User('张三');

User.prototype.greet = function() { console.log('你好'); };
user.greet(); // 立即可用
```

但**完全替换** `prototype` 不影响已有实例（它们仍指向旧原型）。

---

**规则 6: 原型上的数据共享陷阱**

原型上的引用类型数据会被所有实例共享：

```javascript
function User(name) { this.name = name; }
User.prototype.friends = []; // 危险！

const user1 = new User('张三');
const user2 = new User('李四');
user1.friends.push('王五');
console.log(user2.friends); // ['王五'] - 被共享了
```

**原则**：原型上只放方法和不变的常量，可变数据放在实例自己身上（构造函数中用 `this.prop` 定义）。

---

**事故档案编号**: PROTO-2024-1881
**影响范围**: 原型链, prototype 属性, `__proto__`, Object.create, new 操作符, constructor
**根本原因**: 不理解原型机制，导致方法重复创建、数据意外共享或原型链断裂
**修复成本**: 低（正确使用原型），需理解构造函数、prototype 和 `[[Prototype]]` 的关系

这是 JavaScript 世界第 81 次被记录的原型系统事故。JavaScript 的继承基于原型链：每个对象都有 `[[Prototype]]` 内部槽（通过 `__proto__` 或 `getPrototypeOf()` 访问）指向原型对象。构造函数的 `prototype` 属性会成为 `new` 创建的实例的原型。原型的核心价值是方法共享，节省内存。`new` 操作符创建对象并设置原型链接。原型是动态的，修改会影响所有实例，但完全替换 `prototype` 不影响已有实例。原型上不应放引用类型数据（会被共享），只放方法和常量。覆盖 `prototype` 会丢失 `constructor` 属性，需手动恢复。理解原型是掌握 JavaScript 继承的基础。

---

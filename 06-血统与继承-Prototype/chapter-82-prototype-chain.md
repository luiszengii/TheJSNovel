《第 82 次记录: 原型链查找 —— 血统追溯》

---

## 属性覆盖的诡异事故

周五下午五点，你接到了产品经理的紧急电话。

"线上的宠物系统出问题了！" 她的语气很急促，"用户给狗狗设置自定义叫声后，现在所有狗都在用同一个叫声！"

你快速打开生产环境的监控平台。用户活动日志显示，确实有异常——当用户 A 给他的哈士奇设置了自定义叫声"嗷呜嗷呜"后，用户 B 的金毛、用户 C 的柯基，甚至其他品种的狗都开始发出同样的声音。

"这不可能..."你打开代码仓库，找到宠物系统的核心逻辑：

```javascript
function Animal(name) {
    this.name = name;
}

Animal.prototype.speak = function() {
    console.log(`${this.name} 发出声音`);
};

function Dog(name, breed) {
    Animal.call(this, name);
    this.breed = breed;
}

Dog.prototype = Object.create(Animal.prototype);
Dog.prototype.constructor = Dog;

Dog.prototype.speak = function() {
    console.log(`${this.name} 汪汪叫`);
};
```

"逻辑看起来没问题啊，"你皱眉，"每个 Dog 实例应该是独立的..."

然后你看到了用户自定义叫声的功能代码——你的同事小王上周刚提交的：

```javascript
// 用户自定义叫声功能
function setCustomSound(dog, sound) {
    Dog.prototype.speak = function() {
        console.log(`${this.name} ${sound}`);
    };
}
```

"天哪！"你的手指敲击着桌面，"他直接修改了 `Dog.prototype.speak`！这会影响所有狗的实例！"

你立刻在本地复现了问题：

```javascript
const dog1 = new Dog('旺财', '哈士奇');
const dog2 = new Dog('小黑', '金毛');

dog1.speak(); // '旺财 汪汪叫'
dog2.speak(); // '小黑 汪汪叫'

// 用户给 dog1 设置自定义叫声
setCustomSound(dog1, '嗷呜嗷呜');

dog1.speak(); // '旺财 嗷呜嗷呜'
dog2.speak(); // '小黑 嗷呜嗷呜' - 竟然也变了！
```

"问题找到了，"你自言自语，"但正确的做法是什么？应该在实例上设置方法，而不是原型上..."

你尝试修改：

```javascript
function setCustomSound(dog, sound) {
    // 在实例上设置方法，而非原型
    dog.speak = function() {
        console.log(`${this.name} ${sound}`);
    };
}

const dog1 = new Dog('旺财', '哈士奇');
const dog2 = new Dog('小黑', '金毛');

setCustomSound(dog1, '嗷呜嗷呜');

dog1.speak(); // '旺财 嗷呜嗷呜' - dog1 用自定义叫声
dog2.speak(); // '小黑 汪汪叫' - dog2 不受影响
```

测试通过了。但你突然意识到一个更深层的问题：**为什么实例上的方法能覆盖原型上的方法？JavaScript 是怎么决定调用哪个方法的？**

"之前只是知道'实例属性优先'这个结论，"你想，"但从来没真正理解过底层机制..."

你看了看表，已经五点半了。紧急修复可以等周一再提交，现在你决定彻底搞清楚这个属性查找的规则。

---

## 追踪查找路径

周五晚上六点，你泡了杯咖啡，打开浏览器控制台，开始手动追踪属性的查找过程。

"我要搞清楚 JavaScript 到底是怎么找到 `dog.speak` 的，"你自言自语。

你先创建了一个测试对象：

```javascript
function Animal(name) {
    this.name = name;
}

Animal.prototype.speak = function() {
    console.log(`${this.name} 发出声音`);
};

function Dog(name, breed) {
    Animal.call(this, name);
    this.breed = breed;
}

Dog.prototype = Object.create(Animal.prototype);
Dog.prototype.constructor = Dog;

Dog.prototype.speak = function() {
    console.log(`${this.name} 汪汪叫`);
};

const dog = new Dog('旺财', '哈士奇');
```

"现在 `dog` 对象有三个地方可能有 `speak` 方法，"你分析：

```javascript
// 位置 1: 实例自己（目前没有）
console.log(dog.hasOwnProperty('speak')); // false

// 位置 2: Dog.prototype
console.log(Dog.prototype.hasOwnProperty('speak')); // true

// 位置 3: Animal.prototype
console.log(Animal.prototype.hasOwnProperty('speak')); // true
```

"有两个 `speak` 方法！"你惊讶，"但 `dog.speak()` 调用的是哪个？"

你测试了一下：

```javascript
dog.speak(); // '旺财 汪汪叫' - 用的是 Dog.prototype 的方法
```

"所以更近的原型优先，"你说，"但如果我给实例添加方法呢？"

```javascript
dog.speak = function() {
    console.log(`${this.name} 不想叫`);
};

dog.speak(); // '旺财 不想叫' - 实例方法覆盖了原型方法
```

"实例方法优先级最高，"你总结，"但原型上的方法还在吗？"

你继续测试：

```javascript
console.log(dog.hasOwnProperty('speak')); // true - 实例有
console.log(Dog.prototype.hasOwnProperty('speak')); // true - 原型也有
console.log(Animal.prototype.hasOwnProperty('speak')); // true - 更上层也有
```

"所有层都有 `speak`！"你兴奋起来，"那如果我删除实例的方法..."

```javascript
delete dog.speak;
dog.speak(); // '旺财 汪汪叫' - 恢复到 Dog.prototype 的方法
```

"等等..."你的手指停在键盘上，"删除一层就露出下一层？"

你继续删除：

```javascript
delete Dog.prototype.speak;
dog.speak(); // '旺财 发出声音' - 又恢复到 Animal.prototype 的方法！
```

"天哪！"你拍了下桌子，"这就像剥洋葱——删除外层就露出内层！"

你靠在椅背上，突然意识到：**JavaScript 的属性查找是一个逐层向上的过程，从实例自身开始，找不到就去原型找,还找不到就去原型的原型找，直到找到或到达 `null`。**

"原来如此，"你喃喃自语，"这就是'原型链'的真正含义——一条从实例到 `null` 的查找链条。"

---

## 手动实现查找算法

晚上七点，你决定亲手写一个函数来模拟 JavaScript 的属性查找过程。

"如果我能用代码复现这个查找逻辑，"你想，"就能彻底理解它了。"

你开始写代码：

```javascript
function findProperty(obj, propName) {
    let current = obj;
    let depth = 0;

    console.log(`\n=== 查找属性: ${propName} ===`);

    while (current !== null) {
        const layerName = current.constructor?.name || 'Object';
        console.log(`第 ${depth} 层: ${layerName}`);

        // 检查当前层是否有这个属性
        if (current.hasOwnProperty(propName)) {
            console.log(`  ✓ 找到了! ${propName} 在这一层`);
            return current[propName];
        }

        console.log(`  ✗ 没有 ${propName}, 继续向上查找`);

        // 移动到下一层原型
        current = Object.getPrototypeOf(current);
        depth++;
    }

    console.log('到达原型链顶端 (null), 属性不存在');
    return undefined;
}
```

你用之前的 `dog` 对象测试：

```javascript
const dog = new Dog('旺财', '哈士奇');

// 测试 1: 查找实例自有属性
findProperty(dog, 'name');
```

控制台输出：

```
=== 查找属性: name ===
第 0 层: Dog
  ✓ 找到了! name 在这一层
```

"完美！"你说，"现在测试原型上的属性：

```javascript
// 测试 2: 查找原型上的方法
findProperty(dog, 'speak');
```

输出：

```
=== 查找属性: speak ===
第 0 层: Dog
  ✗ 没有 speak, 继续向上查找
第 1 层: Object
  ✓ 找到了! speak 在这一层
```

"它在 `Dog.prototype` 上找到了，"你说，"那继承更远的属性呢？"

```javascript
// 测试 3: 查找 Object.prototype 上的方法
findProperty(dog, 'toString');
```

输出：

```
=== 查找属性: toString ===
第 0 层: Dog
  ✗ 没有 toString, 继续向上查找
第 1 层: Object
  ✗ 没有 toString, 继续向上查找
第 2 层: Object
  ✗ 没有 toString, 继续向上查找
第 3 层: Object
  ✓ 找到了! toString 在这一层
```

"查了四层才找到！"你惊叹，"这条链还挺长..."

你画了一张图来可视化整个结构：

```
dog 实例
├── name: '旺财'
├── breed: '哈士奇'
└── [[Prototype]] ────> Dog.prototype
                        ├── constructor: Dog
                        ├── speak: function
                        └── [[Prototype]] ────> Animal.prototype
                                                ├── speak: function
                                                └── [[Prototype]] ────> Object.prototype
                                                                        ├── toString: function
                                                                        ├── hasOwnProperty: function
                                                                        └── [[Prototype]] ────> null
```

"现在一切都清晰了，"你满意地说，"原型链就是一个单向链表，每个节点通过 `[[Prototype]]` 指向下一个节点，查找时从头到尾逐个检查。"

---

## 遮蔽效应的发现

晚上八点，你突然想起一个细节。

"之前删除实例属性后，原型方法就露出来了，"你想，"这叫什么？"

你查阅了文档，找到了一个术语：**属性遮蔽（Shadowing）**。

"下层的同名属性会遮蔽上层的，"你总结，"就像月食——月亮遮住了太阳，但太阳还在，只是被挡住了。"

你做了更多实验：

```javascript
const proto = { x: 1, y: 2 };
const obj = Object.create(proto);

console.log(obj.x); // 1 - 继承自 proto

// 在实例上添加同名属性
obj.x = 100;

console.log(obj.x); // 100 - 实例属性遮蔽了原型属性
console.log(proto.x); // 1 - 原型属性没变

// 删除实例属性
delete obj.x;
console.log(obj.x); // 1 - 原型属性重新可见
```

"遮蔽是可逆的，"你说，"删除下层属性就能恢复上层属性的可见性。"

但你突然想到一个问题："如果原型上的属性是只读的呢？"

你尝试：

```javascript
const proto2 = {};
Object.defineProperty(proto2, 'x', {
    value: 1,
    writable: false, // 只读
    configurable: true
});

const obj2 = Object.create(proto2);

// 尝试在实例上设置同名属性
obj2.x = 2;

console.log(obj2.x); // 1 - 设置失败，还是原型的值
console.log(obj2.hasOwnProperty('x')); // false - 实例上没有创建属性
```

"什么？！"你惊讶，"不能遮蔽只读属性？"

你切换到严格模式测试：

```javascript
'use strict';
obj2.x = 2; // TypeError: Cannot assign to read only property 'x'
```

"严格模式下直接报错了，"你说，"这是个重要的陷阱..."

你继续探索，发现还有另一种情况：

```javascript
const proto3 = {
    set value(val) {
        console.log('setter 被调用:', val);
        this._value = val;
    },
    get value() {
        return this._value;
    }
};

const obj3 = Object.create(proto3);

obj3.value = 100; // setter 被调用: 100
console.log(obj3.hasOwnProperty('value')); // false - 没有 value 属性
console.log(obj3.hasOwnProperty('_value')); // true - setter 创建了 _value
```

"原型上的 setter 会拦截赋值！"你恍然大悟，"赋值操作不一定会创建实例属性。"

你在笔记本上写下三种遮蔽的特殊情况：

1. **普通属性**：可以自由遮蔽
2. **只读属性**：不能通过赋值遮蔽（除非用 `defineProperty`）
3. **Setter 属性**：赋值会调用 setter，不创建实例属性

"JavaScript 的每个细节都藏着陷阱，"你感叹。

---

## in 操作符与 hasOwnProperty 的差异

晚上九点，你开始研究如何检测属性是在实例上还是原型上。

"之前一直用 `in` 和 `hasOwnProperty`，"你想，"但它们有什么区别？"

你写了个测试：

```javascript
function Animal(name) {
    this.name = name;
}

Animal.prototype.speak = function() {
    console.log('动物叫');
};

const dog = new Animal('旺财');

// in 操作符：检查整个原型链
console.log('name' in dog); // true - 在实例上
console.log('speak' in dog); // true - 在原型上
console.log('toString' in dog); // true - 在 Object.prototype 上
console.log('fly' in dog); // false - 根本不存在

// hasOwnProperty: 只检查自有属性
console.log(dog.hasOwnProperty('name')); // true
console.log(dog.hasOwnProperty('speak')); // false - 不是自有属性
console.log(dog.hasOwnProperty('toString')); // false
```

"原来如此，"你总结，"`in` 检查整个原型链，`hasOwnProperty` 只检查实例自身。"

你突然想起白天的 bug："所以如果要判断属性是实例自己的还是继承的，必须用 `hasOwnProperty`。"

你测试了遍历对象的常见陷阱：

```javascript
const obj = Object.create({ inherited: 1 });
obj.own = 2;

console.log('使用 for...in 遍历:');
for (let key in obj) {
    console.log(key); // 'own', 'inherited' - 包含继承属性
}

console.log('\n使用 hasOwnProperty 过滤:');
for (let key in obj) {
    if (obj.hasOwnProperty(key)) {
        console.log(key); // 'own' - 只有自有属性
    }
}

console.log('\n使用 Object.keys():');
console.log(Object.keys(obj)); // ['own'] - 只返回自有可枚举属性
```

"难怪有时候 `for...in` 会遍历出意外的属性，"你说，"原来是包含了继承属性。"

---

## 原型链的终点与纯数据对象

晚上十点，你好奇原型链的尽头是什么。

"所有原型链都以 `Object.prototype` 结束吗？"你问自己。

你测试了普通对象：

```javascript
const normal = {};
console.log(Object.getPrototypeOf(normal)); // Object.prototype
console.log(Object.getPrototypeOf(Object.prototype)); // null - 终点
```

"大部分对象确实以 `Object.prototype` 结束，"你说，"但有例外吗？"

你想起 `Object.create(null)` 这个用法：

```javascript
// 创建没有原型的对象
const bare = Object.create(null);
console.log(Object.getPrototypeOf(bare)); // null - 直接是 null

// bare 对象没有任何继承的方法
console.log(bare.toString); // undefined - 没有 toString
console.log(bare.hasOwnProperty); // undefined - 没有 hasOwnProperty

// 但可以自己添加属性
bare.name = '张三';
console.log(bare.name); // '张三'
```

"为什么要创建没有原型的对象？"你疑惑。

你查阅了文档和博客，找到了答案：**用作纯粹的数据字典，避免原型污染攻击。**

"如果用普通对象做 Map，"你理解了，"可能会有意外的继承属性："

```javascript
const normalMap = {};
normalMap['key1'] = 'value1';

// 危险：继承的属性也会被检测到
console.log('toString' in normalMap); // true - 继承的
console.log('constructor' in normalMap); // true - 继承的

// 如果用户输入 '__proto__' 作为键...
normalMap['__proto__'] = 'evil'; // 原型污染！
```

"而用 `Object.create(null)` 就安全了：

```javascript
const safeMap = Object.create(null);
safeMap['key1'] = 'value1';

console.log('toString' in safeMap); // false - 干净
console.log('constructor' in safeMap); // false - 干净

safeMap['__proto__'] = 'safe'; // 只是普通属性，不会污染原型
console.log(safeMap['__proto__']); // 'safe'
```

"原来这就是为什么 `Map` 和 `Set` 比普通对象更安全，"你恍然大悟。

---

## 你的原型链笔记本

晚上十一点，你整理了今天的收获。

你在笔记本上写下标题："原型链查找 —— 血统追溯的规则"

### 核心洞察 #1: 逐层向上的查找机制

你写道：

"访问 `obj.prop` 时，JavaScript 执行以下步骤：

1. 检查 `obj` 自身是否有 `prop`（用 `hasOwnProperty` 判断）
2. 如果没有，获取 `obj` 的原型，检查原型对象
3. 重复步骤 2，沿原型链向上查找
4. 直到找到属性或到达 `null`（返回 `undefined`）

这就像剥洋葱——外层没有就看内层，一层一层向内查找。"

### 核心洞察 #2: 属性遮蔽（Shadowing）

"下层对象的同名属性会遮蔽上层原型的属性：

```javascript
obj.prop = 'A';
Object.getPrototypeOf(obj).prop = 'B';
console.log(obj.prop); // 'A' - 实例属性遮蔽原型属性
```

删除实例属性后，原型属性重新可见：

```javascript
delete obj.prop;
console.log(obj.prop); // 'B' - 露出原型属性
```

但有三种特殊情况：
1. **只读属性**：`writable: false` 的原型属性不能被赋值遮蔽
2. **Setter 属性**：赋值会调用 setter，不创建实例属性
3. **强制定义**：可用 `Object.defineProperty()` 强制遮蔽只读属性"

### 核心洞察 #3: in 操作符 vs hasOwnProperty

"`in` 操作符检查整个原型链，`hasOwnProperty()` 只检查自有属性：

```javascript
'name' in dog; // true - 可能在实例或原型上
dog.hasOwnProperty('name'); // true/false - 只检查实例
```

遍历对象时，`for...in` 包含继承属性，需用 `hasOwnProperty` 过滤：

```javascript
for (let key in obj) {
    if (obj.hasOwnProperty(key)) {
        // 只处理自有属性
    }
}
```

或直接用 `Object.keys(obj)`，它只返回自有可枚举属性。"

### 核心洞察 #4: 原型链的终点与纯数据对象

"大部分对象的原型链：`实例 → 类型.prototype → Object.prototype → null`

但可以创建没有原型的对象：

```javascript
const bare = Object.create(null); // 原型直接是 null
```

用途：
- 纯数据字典，不会有意外的继承属性
- 防止原型污染攻击
- 需要干净的键值对存储

这就是为什么现代 JavaScript 推荐用 `Map` 而非普通对象做字典。"

你合上笔记本，看了看表，已经快午夜了。

"明天要赶紧修复线上的 bug，"你想，"但今天彻底理解了原型链，以后不会再犯这种错误了。"

你保存了代码，关上电脑，准备休息。窗外的城市灯火渐渐熄灭，但你对 JavaScript 的理解又深了一层。

---

## 知识总结

**规则 1: 原型链查找算法**

访问 `obj.prop` 时，JavaScript 执行以下步骤：

1. 检查 `obj` 自身是否有 `prop` 属性（用 `hasOwnProperty` 判断）
2. 如果没有，获取 `obj` 的 `[[Prototype]]`，检查原型对象
3. 重复步骤 2，沿原型链向上查找
4. 直到找到属性或到达 `null`（返回 `undefined`）

这是 JavaScript 继承的核心机制。查找是逐层向上的，找到即停止。

---

**规则 2: 属性遮蔽（Shadowing）**

下层对象的同名属性会遮蔽上层原型的属性：

```javascript
obj.prop = 'A';
Object.getPrototypeOf(obj).prop = 'B';
console.log(obj.prop); // 'A' - 实例属性遮蔽原型属性
```

删除实例属性后，原型属性重新可见：

```javascript
delete obj.prop;
console.log(obj.prop); // 'B' - 露出原型属性
```

遮蔽是可逆的——删除下层属性就能恢复上层属性的可见性。

---

**规则 3: 只读属性不能被遮蔽**

如果原型上的属性是 `writable: false`，实例不能通过赋值创建同名属性：

```javascript
const proto = {};
Object.defineProperty(proto, 'x', { value: 1, writable: false });

const obj = Object.create(proto);
obj.x = 2; // 非严格模式: 静默失败; 严格模式: TypeError

console.log(obj.x); // 1 - 赋值失败
console.log(obj.hasOwnProperty('x')); // false - 未创建实例属性
```

但可以用 `Object.defineProperty()` 强制定义实例属性：

```javascript
Object.defineProperty(obj, 'x', { value: 2, writable: true });
console.log(obj.x); // 2 - 成功遮蔽
```

---

**规则 4: setter 会拦截赋值**

如果原型上有同名 setter，给实例赋值会调用 setter，而不是创建实例属性：

```javascript
const proto = {
    set x(val) { this._x = val; },
    get x() { return this._x; }
};

const obj = Object.create(proto);
obj.x = 10; // 调用 setter

console.log(obj.hasOwnProperty('x')); // false - 没有 x 属性
console.log(obj.hasOwnProperty('_x')); // true - setter 创建了 _x
```

赋值操作不一定会创建实例属性，可能被 setter 拦截。

---

**规则 5: in 操作符 vs hasOwnProperty**

`in` 操作符检查整个原型链，`hasOwnProperty()` 只检查自有属性：

```javascript
const proto = { inherited: 1 };
const obj = Object.create(proto);
obj.own = 2;

'own' in obj; // true
'inherited' in obj; // true - in 检查原型链

obj.hasOwnProperty('own'); // true
obj.hasOwnProperty('inherited'); // false - 只检查自有
```

遍历对象时，`for...in` 会包含继承属性，需用 `hasOwnProperty` 过滤：

```javascript
for (let key in obj) {
    if (obj.hasOwnProperty(key)) {
        // 只处理自有属性
    }
}
```

或直接用 `Object.keys(obj)`，它只返回自有可枚举属性。

---

**规则 6: 原型链的终点与纯数据对象**

大部分对象的原型链终点是 `Object.prototype → null`：

```javascript
const normal = {};
Object.getPrototypeOf(normal); // Object.prototype
Object.getPrototypeOf(Object.prototype); // null
```

但可以创建没有原型的对象：

```javascript
const bare = Object.create(null);
Object.getPrototypeOf(bare); // null - 直接是 null

bare.toString; // undefined - 没有继承任何方法
bare.hasOwnProperty; // undefined
```

用途：
- 纯数据字典，不会有意外的继承属性
- 防止原型污染攻击（避免 `__proto__` 等特殊键）
- 需要干净的键值对存储

这就是为什么现代 JavaScript 推荐用 `Map` 而非普通对象做字典。

---

**事故档案编号**: PROTO-2024-1882
**影响范围**: 原型链查找, 属性遮蔽, in 操作符, hasOwnProperty, 原型污染
**根本原因**: 不理解原型链查找机制，导致属性覆盖错误、意外继承或原型污染攻击
**修复成本**: 低（理解查找规则），需掌握遮蔽、只读属性、setter 等特殊情况

这是 JavaScript 世界第 82 次被记录的原型链查找事故。原型链查找从对象自身开始，逐层向上直到 `null`。下层属性遮蔽上层同名属性，删除下层属性后上层属性重新可见。只读属性（`writable: false`）不能被赋值遮蔽，但可用 `defineProperty` 强制覆盖。原型上的 setter 会拦截赋值，不创建实例属性。`in` 操作符检查整个原型链，`hasOwnProperty` 只检查自有属性。`Object.create(null)` 创建没有原型的纯数据对象，防止原型污染。理解原型链查找是掌握 JavaScript 继承和避免原型相关 bug 的基础。

---

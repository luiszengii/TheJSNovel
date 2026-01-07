《第47次记录: 对象引用之谜 —— 购物车的幽灵商品》

---

## 紧急事故

周五晚上八点, 办公室里只剩下你和值班的运维小王。窗外夜色已深, 你本该在回家路上, 却因为一个紧急bug被困在工位上。

产品经理在钉钉上连发三条消息:"购物车出大问题了! 用户A加购商品, 结果用户B的购物车也出现了同样的商品! 客服电话都被打爆了!"

你的手心开始出汗。这是新上线的购物车优化功能, 测试环境明明一切正常, 怎么到了生产环境就出问题了?

你快速打开监控系统, 在错误日志里发现了大量用户投诉:"我没买过这个商品, 为什么在我的购物车里?"、"购物车里突然多了别人的东西!"

"这不可能..."你喃喃自语。你明明在下午五点做过最后一轮测试, 购物车的增删改查都正常。你甚至还用两个不同的测试账号验证过, 完全没问题。

运维小王走过来看了一眼你的屏幕:"老王, 没事吧? 我看服务器负载正常啊, 不像是性能问题。"

"不是性能问题, 是数据问题。"你皱着眉头, 手指敲击着键盘,"有用户的购物车数据串了。"

你打开代码, 定位到购物车模块。这个模块你昨天才优化过, 把原来每次都从数据库读取的逻辑改成了内存缓存, 为了提高性能。代码看起来很简单, 应该不会有问题才对。

但事实是, 问题就在这里。你尝试在本地复现, 开了两个浏览器窗口, 模拟两个用户同时操作购物车。第一次测试, 正常。第二次测试, 正常。第三次...

突然, 你在窗口A添加的商品出现在了窗口B的购物车里!

"见鬼了..."你的后背开始冒冷汗。这个bug是间歇性的, 不是每次都能复现, 这是最可怕的。

钉钉又响了, 产品经理:"老王, 老板在问情况, 能不能在九点前修复? 九点有一波晚高峰流量, 再出问题影响太大了。"

你看了看时间: 8: 17。只剩40分钟。

---

## 追踪线索

晚上八点二十, 你决定先看看出问题的代码。你打开购物车服务的核心模块, 这是你昨天优化过的部分:

```javascript
// 购物车缓存 - 优化后的代码
const cartCache = {};

function getCart(userId) {
    if (! cartCache[userId]) {
        // 如果缓存里没有, 创建一个默认购物车
        cartCache[userId] = {
            items: [],
            totalPrice: 0
        };
    }
    return cartCache[userId];
}

function addToCart(userId, product) {
    const cart = getCart(userId);
    cart. items. push(product);
    cart. totalPrice += product. price;
}
```

"逻辑很清楚啊, 每个用户都有自己的cart对象, 存在`cartCache[userId]`里。"你自言自语。

但突然, 你想起来什么。你迅速在控制台里输入了一段测试代码:

```javascript
const userA = getCart('user_123');
const userB = getCart('user_123');

console. log(userA === userB); // true
```

"咦?"你盯着这个`true`, 心里有些不安。同一个用户ID获取到的是同一个对象, 这是对的。

你继续测试:

```javascript
const userA = getCart('user_123');
const userB = getCart('user_456'); // 不同用户

userA. items. push({ name: '商品A', price: 100 });

console. log(userA. items); // [{ name: '商品A', price: 100 }]
console. log(userB. items); // []
```

"看起来没问题..."你的眉头皱得更深了。

这时, 运维小王端着咖啡走过来:"找到原因了吗?"

"还没, 邪门了。"你摇摇头,"逻辑上是对的, 但生产环境就是出问题。"

你突然想到, 也许问题不在`getCart`, 而在缓存的初始化。你仔细看了看代码, 发现了一个细节: 你在另一个文件里定义了默认购物车模板:

```javascript
// cart-template. js
const defaultCart = {
    items: [],
    totalPrice: 0
};

export default defaultCart;
```

然后在`getCart`里使用这个模板:

```javascript
import defaultCart from './cart-template. js';

const cartCache = {};

function getCart(userId) {
    if (! cartCache[userId]) {
        cartCache[userId] = defaultCart; // 直接赋值!
    }
    return cartCache[userId];
}
```

你盯着这行代码看了整整一分钟。大脑里突然闪过一个念头:"等等... 这里直接赋值了`defaultCart`..."

你飞快地在控制台里验证:

```javascript
import defaultCart from './cart-template. js';

const userA = defaultCart;
const userB = defaultCart;

userA. items. push({ name: '商品A' });

console. log(userB. items); // [{ name: '商品A' }] !!!
```

输出结果让你倒吸一口凉气:`userB`的购物车里也有商品A!

"原来如此..."你终于明白了。你一直以为给每个用户分配的是一个"新的"购物车对象, 但实际上, 所有用户共享的都是同一个`defaultCart`对象的引用!

当用户A第一次访问购物车时,`cartCache['userA'] = defaultCart`, 这不是复制, 而是引用赋值。用户B第一次访问时,`cartCache['userB'] = defaultCart`, 又是同一个引用。结果所有新用户的购物车都指向同一个对象!

你的脸烧了起来, 这是JavaScript最基础的知识点, 你竟然在关键代码里犯了这个错误。

晚上八点四十五, 距离晚高峰还有15分钟。你迅速修复代码。

---

## 定位根因

你终于明白了问题的根源。JavaScript的对象赋值是引用传递, 而不是值传递。你写下了错误的代码和正确的修复:

**❌ 错误: 直接赋值对象引用**

```javascript
const defaultCart = {
    items: [],
    totalPrice: 0
};

function getCart(userId) {
    if (! cartCache[userId]) {
        cartCache[userId] = defaultCart; // 所有用户共享同一个对象!
    }
    return cartCache[userId];
}

// 结果
const userA = getCart('user_123');
const userB = getCart('user_456');
// userA和userB都指向同一个defaultCart对象
// 修改其中一个, 另一个也会变化!
```

**✅ 正确: 创建新对象**

```javascript
function getCart(userId) {
    if (! cartCache[userId]) {
        // 方式1: 使用对象字面量创建新对象
        cartCache[userId] = {
            items: [],
            totalPrice: 0
        };
    }
    return cartCache[userId];
}

// 或者方式2: 浅拷贝
function getCart(userId) {
    if (! cartCache[userId]) {
        cartCache[userId] = { ... defaultCart }; // 创建新对象
        cartCache[userId]. items = [... defaultCart. items]; // 数组也要拷贝
    }
    return cartCache[userId];
}
```

你还整理了引用vs值的对比:

```javascript
/* 基本类型: 值传递 */
let a = 10;
let b = a;
b = 20;
console. log(a); // 10 - a不受b的影响

/* 对象类型: 引用传递 */
let obj1 = { value: 10 };
let obj2 = obj1; // obj2和obj1指向同一个对象
obj2. value = 20;
console. log(obj1. value); // 20 - obj1被修改了!

/* 数组也是引用类型 */
let arr1 = [1, 2, 3];
let arr2 = arr1;
arr2. push(4);
console. log(arr1); // [1, 2, 3, 4] - arr1也变了!
```

晚上八点五十, 你提交了修复代码, 运维小王快速部署上线。你刷新监控页面, 购物车bug的报警数量开始下降, 直到归零。

产品经理发来消息:"好了! 新的bug报告停了, 看起来修复生效了。辛苦了!"

你长长地舒了一口气, 靠在椅子上, 手还在微微颤抖。

---

## 引用机制

**规则 1: 对象赋值是引用传递**

```javascript
/* 对象赋值传递的是引用, 不是副本 */
const original = { name: 'JavaScript' };
const reference = original; // reference指向original

reference. name = 'TypeScript';
console. log(original. name); // 'TypeScript' - 原对象被修改了!

/* 原理 */
// original和reference都指向内存中同一个对象
// 修改其中任何一个, 都会影响另一个
```

---

**规则 2: 基本类型vs引用类型**

```javascript
/* 基本类型(值传递): number, string, boolean, null, undefined, symbol, bigint */
let x = 10;
let y = x; // 复制值
y = 20;
console. log(x); // 10 - x不变

/* 引用类型(引用传递): object, array, function */
let obj1 = { count: 10 };
let obj2 = obj1; // 复制引用
obj2. count = 20;
console. log(obj1. count); // 20 - obj1改变了!
```

**判断规则**:
- 基本类型: 赋值时复制值, 互不影响
- 引用类型: 赋值时复制引用, 指向同一对象

---

**规则 3: 创建对象副本的方法**

```javascript
const original = { a: 1, b: 2 };

/* 方式1: 对象展开(浅拷贝) */
const copy1 = { ... original };

/* 方式2: Object. assign(浅拷贝) */
const copy2 = Object. assign({}, original);

/* 注意: 嵌套对象仍是引用 */
const nested = { user: { name: 'Alice' } };
const copy = { ... nested };
copy. user. name = 'Bob';
console. log(nested. user. name); // 'Bob' - 嵌套对象被修改了!

/* 深拷贝: 需要递归处理 */
const deepCopy = JSON. parse(JSON. stringify(nested)); // 简单场景
// 注意: 无法拷贝函数、undefined、Symbol等
```

---

**规则 4: 数组也是引用类型**

```javascript
/* 数组赋值 */
const arr1 = [1, 2, 3];
const arr2 = arr1; // 引用赋值
arr2. push(4);
console. log(arr1); // [1, 2, 3, 4]

/* 创建数组副本 */
const original = [1, 2, 3];

// 方式1: 展开运算符
const copy1 = [... original];

// 方式2: slice()
const copy2 = original. slice();

// 方式3: Array. from()
const copy3 = Array. from(original);

/* 嵌套数组注意 */
const nested = [[1, 2], [3, 4]];
const copy = [... nested];
copy[0]. push(5);
console. log(nested[0]); // [1, 2, 5] - 嵌套数组被修改!
```

---

**规则 5: 函数参数传递**

```javascript
/* 基本类型作为参数 */
function changeValue(x) {
    x = 100;
}
let num = 10;
changeValue(num);
console. log(num); // 10 - 不变

/* 对象作为参数 */
function changeObject(obj) {
    obj. value = 100; // 修改对象属性
}
const myObj = { value: 10 };
changeObject(myObj);
console. log(myObj. value); // 100 - 改变了!

/* 重新赋值参数不影响原对象 */
function replaceObject(obj) {
    obj = { value: 100 }; // 重新赋值, 不影响外部
}
const myObj2 = { value: 10 };
replaceObject(myObj2);
console. log(myObj2. value); // 10 - 不变
```

**规则总结**:
- 参数传递对象时, 传递的是引用
- 修改对象属性会影响原对象
- 重新赋值参数不影响原对象

---

**规则 6: 比较操作符的行为**

```javascript
/* 基本类型: 比较值 */
const a = 10;
const b = 10;
console. log(a === b); // true

/* 引用类型: 比较引用 */
const obj1 = { value: 10 };
const obj2 = { value: 10 };
const obj3 = obj1;

console. log(obj1 === obj2); // false - 不同对象
console. log(obj1 === obj3); // true - 同一个对象

/* 数组同理 */
const arr1 = [1, 2, 3];
const arr2 = [1, 2, 3];
console. log(arr1 === arr2); // false - 不同数组

/* 比较内容需要手动实现 */
function deepEqual(a, b) {
    return JSON. stringify(a) === JSON. stringify(b);
}
console. log(deepEqual([1, 2], [1, 2])); // true
```

---

**事故档案编号**: OBJ-2024-1747
**影响范围**: 生产环境购物车模块, 影响所有新用户
**根本原因**: 对象引用赋值导致多个用户共享同一购物车对象
**修复成本**: 低(理解引用vs值的区别后, 修复只需修改一行代码)

这是JavaScript世界第47次被记录的对象引用事故。JavaScript的对象赋值传递的是引用, 而不是值的副本。当多个变量指向同一个对象时, 修改其中一个会影响所有引用。基本类型(number, string, boolean)是值传递, 对象类型(object, array, function)是引用传递——理解这个区别, 是避免购物车幽灵商品的关键。

---

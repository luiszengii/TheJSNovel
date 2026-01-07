《第 37 次记录: 数据类型事故 —— 值的八重分类与类型系统陷阱》

## 用户系统的幽灵重复

周一早上 9 点 23 分, 你盯着用户管理系统的后台数据, 感觉哪里不对劲。

运营部门昨天报告了一个奇怪的问题: 系统显示有 347 个用户注册, 但实际用户列表里只有 289 人。你以为是数据库查询的问题, 但 SQL 日志显示查询结果确实是 347 条记录。

你打开控制台, 写了一段简单的去重代码:

```javascript
const users = await fetchAllUsers();
const uniqueUsers = [...new Set(users)];

console.log('原始用户数:', users.length);        // 347
console.log('去重后用户数:', uniqueUsers.length); // 347
```

去重前后数量完全一样？`Set` 应该会自动去重啊。你困惑地检查数据:

```javascript
console.log(users[0]);  // { id: 1, name: "Alice", email: "alice@example.com" }
console.log(users[1]);  // { id: 1, name: "Alice", email: "alice@example.com" }

console.log(users[0] === users[1]);  // false
```

两个用户对象的内容完全一样, 但比较结果是 `false`？你以为是引用问题, 于是改成比较 ID:

```javascript
const uniqueIds = [...new Set(users.map(u => u.id))];
console.log('唯一ID数量:', uniqueIds.length);  // 289
```

这次对了！289 个唯一 ID。"所以是对象比较的问题..."你喃喃自语。但为什么内容相同的对象不相等？

## 类型判断的第一道迷雾

你决定从最基础的地方开始调查。你打开一个空白的测试页面:

```javascript
// 测试基本类型比较
const num1 = 42;
const num2 = 42;
console.log('数字比较:', num1 === num2);  // true

const str1 = "hello";
const str2 = "hello";
console.log('字符串比较:', str1 === str2);  // true

// 测试对象比较
const obj1 = { value: 42 };
const obj2 = { value: 42 };
console.log('对象比较:', obj1 === obj2);  // false ← 为什么不同?

// 测试数组比较
const arr1 = [1, 2, 3];
const arr2 = [1, 2, 3];
console.log('数组比较:', arr1 === arr2);  // false ← 数组也不相等?
```

数字和字符串比较返回 `true`, 对象和数组返回 `false`。你想起之前看过的文档: "基本类型比较值, 引用类型比较引用。"但什么是基本类型? 什么是引用类型?

你用 `typeof` 运算符检查类型:

```javascript
console.log('=== typeof 检查 ===');
console.log(typeof 42);         // "number"
console.log(typeof "hello");    // "string"
console.log(typeof true);       // "boolean"
console.log(typeof undefined);  // "undefined"
console.log(typeof {});         // "object"
console.log(typeof []);         // "object" ← 数组也是 "object"?
console.log(typeof function(){}); // "function"
console.log(typeof Symbol('id')); // "symbol"
console.log(typeof 42n);        // "bigint"
```

等等, `typeof null` 呢? 你加上这一行:

```javascript
console.log(typeof null);  // "object" ← 什么?!
```

`typeof null` 返回 `"object"`? 你以为自己眼花了, 刷新页面重新执行 —— 结果还是 `"object"`。

"这是 bug 吗?"你立刻搜索, 找到了 MDN 的解释: **这是 JavaScript 的历史遗留 bug, 从 1995 年第一版就存在, 无法修复**。

原来 JavaScript 最初的实现中, 值的底层表示使用类型标签, `null` 的标签恰好是 0x00, 和 `object` 的标签相同, 导致 `typeof null` 被错误识别。虽然这是 bug, 但因为太多旧代码依赖这个行为, 修复会破坏兼容性, 所以 TC39 委员会决定永久保留这个 bug。

## typeof 的两个致命缺陷

你继续测试 `typeof`, 发现了第二个问题:

```javascript
console.log('=== typeof 无法区分数组 ===');

const obj = { name: "Alice" };
const arr = [1, 2, 3];

console.log(typeof obj);  // "object"
console.log(typeof arr);  // "object" ← 无法区分数组和对象
```

`typeof` 对数组和普通对象都返回 `"object"`, 无法区分。你想起 `Array.isArray`:

```javascript
console.log('=== Array.isArray 判断 ===');
console.log(Array.isArray(obj));  // false
console.log(Array.isArray(arr));  // true
```

好, 数组可以用 `Array.isArray` 判断。那 `null` 怎么办?

```javascript
console.log('=== null 的正确判断 ===');
console.log(null === null);  // true
console.log(typeof null === "object" && null === null);  // true

// 更简洁的方式
const value = null;
if (value === null) {
    console.log('这是 null');
}
```

直接用 `=== null` 判断即可。你记下这两个陷阱:

**typeof 的两个 bug**:
1. `typeof null` 返回 `"object"` (历史 bug, 永久保留)
2. `typeof []` 返回 `"object"` (无法区分数组和对象)

## 八种数据类型的完整图谱

你打开 JavaScript 文档, 系统学习了类型系统。JavaScript 有 **8 种数据类型**:

**7 种基本类型 (Primitive Types)**:
1. **Number** - 数字 (包括整数和浮点数)
2. **String** - 字符串
3. **Boolean** - 布尔值 (`true` / `false`)
4. **Undefined** - 未定义 (变量声明但未赋值)
5. **Null** - 空值 (有意的空对象引用)
6. **Symbol** - 符号 (ES6, 唯一标识符)
7. **BigInt** - 大整数 (ES2020, 超出安全范围的整数)

**1 种引用类型 (Reference Type)**:
8. **Object** - 对象 (包括 Object, Array, Function, Date, RegExp 等)

你写代码验证每种类型:

```javascript
console.log('=== 八种数据类型示例 ===');

// 基本类型
const num = 42;
const str = "hello";
const bool = true;
const undef = undefined;
const nul = null;
const sym = Symbol('id');
const bigint = 9007199254740991n;

// 引用类型
const obj = { name: "Alice" };
const arr = [1, 2, 3];
const func = function() {};
const date = new Date();
const regex = /abc/;

// 所有引用类型的 typeof 都是 "object"
console.log(typeof obj);   // "object"
console.log(typeof arr);   // "object"
console.log(typeof func);  // "function" ← 例外! 函数被特殊标记
console.log(typeof date);  // "object"
console.log(typeof regex); // "object"
```

等等, `typeof function() {}` 返回 `"function"`? 你以为函数不是对象? 但文档明确说 **函数也是对象**:

```javascript
console.log('=== 函数也是对象 ===');
const myFunc = function() {};

myFunc.customProperty = "I am property";
console.log(myFunc.customProperty);  // "I am property"

console.log(myFunc instanceof Object);  // true ← 函数确实是对象
```

原来 `typeof` 对函数做了特殊处理, 返回 `"function"` 而不是 `"object"`, 这是为了方便区分。但本质上函数仍然是对象。

## 基本类型的不可变性

你测试基本类型的特性:

```javascript
console.log('=== 基本类型: 不可变 ===');

let str = "hello";
console.log('原始字符串:', str);  // "hello"

// 尝试修改字符串
str[0] = "H";
console.log('尝试修改后:', str);  // "hello" ← 没有变化

// 字符串方法返回新字符串
const upper = str.toUpperCase();
console.log('toUpperCase 返回:', upper);  // "HELLO"
console.log('原始字符串:', str);          // "hello" ← 原字符串不变
```

字符串是不可变的! 任何 "修改" 操作都会创建新字符串, 原字符串不变。你测试其他基本类型:

```javascript
console.log('=== 数字也不可变 ===');

let num = 42;
num++;  // 看起来修改了
console.log(num);  // 43

// 但实际上是创建了新值, 然后重新赋值给 num
// 等价于: num = num + 1
```

**基本类型的核心特性: 值不可变, 只能创建新值**。

## 引用类型的可变性

你对比引用类型:

```javascript
console.log('=== 引用类型: 可变 ===');

const obj = { count: 0 };
console.log('初始对象:', obj);  // { count: 0 }

// 修改属性
obj.count = 1;
console.log('修改后:', obj);  // { count: 1 } ← 对象本身被修改

// 添加属性
obj.newProp = "new";
console.log('添加属性后:', obj);  // { count: 1, newProp: "new" }

// 删除属性
delete obj.newProp;
console.log('删除属性后:', obj);  // { count: 1 }
```

对象是可变的, 可以修改、添加、删除属性。你测试数组:

```javascript
console.log('=== 数组也是可变的 ===');

const arr = [1, 2, 3];
console.log('初始数组:', arr);  // [1, 2, 3]

arr.push(4);
console.log('push 后:', arr);  // [1, 2, 3, 4]

arr[0] = 10;
console.log('修改元素后:', arr);  // [10, 2, 3, 4]
```

## 值比较 vs 引用比较的本质

你回到最初的问题: 为什么内容相同的对象不相等?

```javascript
console.log('=== 基本类型: 值比较 ===');

let a = 10;
let b = 10;
console.log('a === b:', a === b);  // true ← 值相同就相等

let c = 10;
let d = c;
d = 20;
console.log('a:', a);  // 10 ← a 不受影响
console.log('c:', c);  // 10 ← c 不受影响
console.log('d:', d);  // 20
```

基本类型赋值会 **复制值**, 两个变量互不影响。你画了一个图:

```
内存模型 (基本类型):
┌─────────┬─────────┐
│ 变量名  │   值    │
├─────────┼─────────┤
│   a     │   10    │
│   b     │   10    │  ← 两个独立的 10
│   c     │   10    │
│   d     │   20    │
└─────────┴─────────┘
```

然后测试引用类型:

```javascript
console.log('=== 引用类型: 引用比较 ===');

let obj1 = { count: 0 };
let obj2 = { count: 0 };
console.log('obj1 === obj2:', obj1 === obj2);  // false ← 内容相同但引用不同

let obj3 = obj1;  // 共享引用
console.log('obj1 === obj3:', obj1 === obj3);  // true ← 引用相同就相等

obj3.count = 1;
console.log('obj1.count:', obj1.count);  // 1 ← obj1 被修改了!
console.log('obj3.count:', obj3.count);  // 1
```

引用类型赋值会 **复制引用**, 两个变量指向同一个对象。你画了第二个图:

```
内存模型 (引用类型):
┌─────────┬─────────┐        ┌──────────────────┐
│ 变量名  │  引用   │───────▶│    实际对象      │
├─────────┼─────────┤        ├──────────────────┤
│  obj1   │  0x1234 │───────▶│ { count: 1 }     │
│  obj2   │  0x5678 │───┐    └──────────────────┘
│  obj3   │  0x1234 │───┼───▶┌──────────────────┐
└─────────┴─────────┘   └───▶│ { count: 0 }     │
                              └──────────────────┘
obj1 和 obj3 指向同一个对象 (0x1234)
obj2 指向不同对象 (0x5678), 虽然内容相同
```

**这就是为什么内容相同的对象不相等** —— 因为比较的是引用地址, 不是内容。

## 特殊值: NaN 的怪异行为

你想起 `Number` 类型有一些特殊值。你测试 `NaN`:

```javascript
console.log('=== NaN: Not a Number ===');

const result = 0 / 0;
console.log('0 / 0 =', result);  // NaN

console.log('typeof NaN:', typeof result);  // "number" ← NaN 是 number 类型

// NaN 的怪异特性
console.log('NaN === NaN:', NaN === NaN);  // false ← NaN 不等于自己!
console.log('result === result:', result === result);  // false

// 正确判断 NaN
console.log('Number.isNaN(NaN):', Number.isNaN(NaN));  // true
console.log('Number.isNaN(result):', Number.isNaN(result));  // true
```

`NaN === NaN` 返回 `false`! 这是 IEEE 754 浮点数标准规定的行为。你测试了为什么会产生 `NaN`:

```javascript
console.log('=== 产生 NaN 的场景 ===');

console.log(0 / 0);           // NaN (不定式)
console.log(Math.sqrt(-1));   // NaN (负数开平方)
console.log(parseInt("abc")); // NaN (无法解析)
console.log("hello" * 2);     // NaN (非法运算)
```

你写了一个安全的 NaN 检查函数:

```javascript
function isNaNSafe(value) {
    // 方法 1: 使用 Number.isNaN (推荐)
    return Number.isNaN(value);

    // 方法 2: 利用 NaN !== NaN 的特性
    // return value !== value;
}

console.log(isNaNSafe(NaN));     // true
console.log(isNaNSafe(42));      // false
console.log(isNaNSafe("hello")); // false
```

## 特殊值: Infinity 与 -Infinity

你继续测试无穷大:

```javascript
console.log('=== Infinity: 无穷大 ===');

console.log(1 / 0);   // Infinity
console.log(-1 / 0);  // -Infinity
console.log(Math.pow(10, 1000));  // Infinity (超出最大值)

console.log('typeof Infinity:', typeof Infinity);  // "number"

// Infinity 的运算
console.log('Infinity + 1:', Infinity + 1);  // Infinity
console.log('Infinity * 2:', Infinity * 2);  // Infinity
console.log('Infinity - Infinity:', Infinity - Infinity);  // NaN
console.log('1 / Infinity:', 1 / Infinity);  // 0

// 判断是否为无穷大
console.log('Number.isFinite(42):', Number.isFinite(42));        // true
console.log('Number.isFinite(Infinity):', Number.isFinite(Infinity));  // false
console.log('Number.isFinite(NaN):', Number.isFinite(NaN));      // false
```

## undefined vs null: 两种 "空"

你对比 `undefined` 和 `null` 的区别:

```javascript
console.log('=== undefined vs null ===');

// undefined: 变量声明但未赋值
let a;
console.log('声明未赋值:', a);  // undefined
console.log('typeof undefined:', typeof a);  // "undefined"

// null: 有意的空对象引用
let b = null;
console.log('显式赋值 null:', b);  // null
console.log('typeof null:', typeof b);  // "object" ← 历史 bug

// 相等性比较
console.log('undefined == null:', undefined == null);   // true (宽松相等)
console.log('undefined === null:', undefined === null); // false (严格不等)

// 使用场景
function findUser(id) {
    // 找到返回对象, 找不到返回 null (有意的空)
    return id === 1 ? { name: "Alice" } : null;
}

let user;  // undefined (未初始化)
user = findUser(2);  // null (显式的空)
```

## Symbol: 唯一的标识符

你测试 ES6 引入的 `Symbol` 类型:

```javascript
console.log('=== Symbol: 唯一标识符 ===');

const sym1 = Symbol('id');
const sym2 = Symbol('id');

console.log('sym1 === sym2:', sym1 === sym2);  // false ← 每个 Symbol 都唯一

console.log('typeof sym1:', typeof sym1);  // "symbol"

// Symbol 作为对象属性
const obj = {
    [sym1]: "value1",
    [sym2]: "value2",
    name: "Alice"
};

console.log('obj:', obj);  // { name: "Alice", [Symbol(id)]: "value1", [Symbol(id)]: "value2" }
console.log('obj[sym1]:', obj[sym1]);  // "value1"
console.log('obj[sym2]:', obj[sym2]);  // "value2"

// Symbol 属性不会被 for...in 遍历
console.log('=== Symbol 属性隐藏 ===');
for (let key in obj) {
    console.log('key:', key);  // 只输出 "name", 不输出 Symbol 属性
}

// 获取 Symbol 属性
console.log('Object.getOwnPropertySymbols:', Object.getOwnPropertySymbols(obj));
```

## BigInt: 超出安全范围的整数

你测试 ES2020 引入的 `BigInt` 类型:

```javascript
console.log('=== BigInt: 大整数 ===');

// JavaScript 的安全整数范围
console.log('最大安全整数:', Number.MAX_SAFE_INTEGER);  // 9007199254740991
console.log('最小安全整数:', Number.MIN_SAFE_INTEGER);  // -9007199254740991

// 超出安全范围的问题
const bigNum = 9007199254740992;
console.log('bigNum:', bigNum);        // 9007199254740992
console.log('bigNum + 1:', bigNum + 1);  // 9007199254740992 ← 无法正确表示
console.log('bigNum + 2:', bigNum + 2);  // 9007199254740994 ← 跳过了 ...993

// BigInt 解决方案
const bigint1 = 9007199254740991n;  // 后缀 n
const bigint2 = BigInt("9007199254740992");

console.log('typeof bigint1:', typeof bigint1);  // "bigint"

console.log('bigint1 + 1n:', bigint1 + 1n);  // 9007199254740992n ← 正确
console.log('bigint2 + 1n:', bigint2 + 1n);  // 9007199254740993n ← 正确

// BigInt 不能与 Number 混合运算
try {
    console.log(bigint1 + 1);  // TypeError
} catch (e) {
    console.log('错误:', e.message);  // "Cannot mix BigInt and other types"
}

// 需要显式转换
console.log('bigint1 + BigInt(1):', bigint1 + BigInt(1));  // 正确
```

## 类型判断的完整方案

晚上, 你整理了类型判断的最佳实践:

```javascript
// ========== 类型判断工具函数 ==========

// 1. typeof: 判断基本类型 (有 2 个 bug)
function getBasicType(value) {
    const type = typeof value;

    // 修复 typeof null === "object" 的 bug
    if (type === "object" && value === null) {
        return "null";
    }

    return type;
}

console.log('=== 测试 getBasicType ===');
console.log(getBasicType(42));        // "number"
console.log(getBasicType("hello"));   // "string"
console.log(getBasicType(null));      // "null" ← 修复了 typeof bug
console.log(getBasicType([]));        // "object" (无法区分数组)

// 2. Array.isArray: 判断数组
console.log('=== 测试 Array.isArray ===');
console.log(Array.isArray([]));       // true
console.log(Array.isArray({}));       // false
console.log(Array.isArray("123"));    // false

// 3. instanceof: 判断对象类型 (可能跨 iframe 失败)
console.log('=== 测试 instanceof ===');
console.log([] instanceof Array);     // true
console.log({} instanceof Object);    // true
console.log([] instanceof Object);    // true (数组也是对象)

// 4. Object.prototype.toString: 精确判断 (最可靠)
function getExactType(value) {
    return Object.prototype.toString.call(value).slice(8, -1);
}

console.log('=== 测试 Object.prototype.toString ===');
console.log(getExactType(42));        // "Number"
console.log(getExactType("hello"));   // "String"
console.log(getExactType(true));      // "Boolean"
console.log(getExactType(null));      // "Null" ← 能正确识别
console.log(getExactType(undefined)); // "Undefined"
console.log(getExactType([]));        // "Array" ← 能区分数组
console.log(getExactType({}));        // "Object"
console.log(getExactType(function(){})); // "Function"
console.log(getExactType(new Date())); // "Date"
console.log(getExactType(/abc/));     // "RegExp"
console.log(getExactType(Symbol()));  // "Symbol"
console.log(getExactType(42n));       // "BigInt"

// 5. 综合类型检查函数
function getType(value) {
    // null 特殊处理
    if (value === null) return "null";

    // 基本类型
    const type = typeof value;
    if (type !== "object") return type;

    // 引用类型: 使用 Object.prototype.toString
    return Object.prototype.toString.call(value).slice(8, -1).toLowerCase();
}

console.log('=== 测试综合函数 getType ===');
console.log(getType(42));        // "number"
console.log(getType(null));      // "null"
console.log(getType([]));        // "array"
console.log(getType({}));        // "object"
console.log(getType(new Date())); // "date"
```

## 解决用户去重问题

你回到最初的问题: 如何比较对象内容? 你写了几种解决方案:

```javascript
// ========== 解决用户去重问题 ==========

const users = [
    { id: 1, name: "Alice", email: "alice@example.com" },
    { id: 1, name: "Alice", email: "alice@example.com" },  // 重复
    { id: 2, name: "Bob", email: "bob@example.com" },
    { id: 1, name: "Alice", email: "alice@example.com" },  // 重复
    { id: 3, name: "Charlie", email: "charlie@example.com" }
];

// 方案 1: 使用唯一标识符 (推荐)
const uniqueUsers1 = Array.from(
    new Map(users.map(u => [u.id, u])).values()
);

console.log('方案1 - 唯一用户数:', uniqueUsers1.length);  // 3

// 方案 2: JSON.stringify 比较 (简单但有局限)
const uniqueUsers2 = users.filter((user, index, self) =>
    index === self.findIndex(u =>
        JSON.stringify(u) === JSON.stringify(user)
    )
);

console.log('方案2 - 唯一用户数:', uniqueUsers2.length);  // 3

// 方案 3: 深度比较函数 (完整但复杂)
function deepEqual(obj1, obj2) {
    if (obj1 === obj2) return true;

    if (typeof obj1 !== "object" || typeof obj2 !== "object" ||
        obj1 === null || obj2 === null) {
        return false;
    }

    const keys1 = Object.keys(obj1);
    const keys2 = Object.keys(obj2);

    if (keys1.length !== keys2.length) return false;

    for (let key of keys1) {
        if (!keys2.includes(key)) return false;
        if (!deepEqual(obj1[key], obj2[key])) return false;
    }

    return true;
}

const uniqueUsers3 = users.filter((user, index, self) =>
    index === self.findIndex(u => deepEqual(u, user))
);

console.log('方案3 - 唯一用户数:', uniqueUsers3.length);  // 3

// 测试深度比较
console.log('=== 测试 deepEqual ===');
console.log(deepEqual(
    { id: 1, name: "Alice" },
    { id: 1, name: "Alice" }
));  // true

console.log(deepEqual(
    { id: 1, info: { age: 25 } },
    { id: 1, info: { age: 25 } }
));  // true

console.log(deepEqual(
    { id: 1, name: "Alice" },
    { id: 2, name: "Bob" }
));  // false
```

你选择了方案 1 (使用唯一 ID), 因为它最简单且性能最好。重复用户问题解决了, 运营部门的数据也对上了。

---

## 技术档案: JavaScript 数据类型系统完全指南

**规则 1: JavaScript 的八种数据类型**

JavaScript 有 8 种数据类型: 7 种基本类型和 1 种引用类型。

```javascript
// ========== 基本类型 (Primitive Types) ==========

// 1. Number - 数字 (整数和浮点数)
const integer = 42;
const float = 3.14;
const negative = -10;
const scientific = 1e6;  // 1000000
console.log(typeof integer);  // "number"

// Number 特殊值
const notANumber = NaN;        // Not a Number
const infinity = Infinity;     // 无穷大
const negInfinity = -Infinity; // 负无穷大

// 2. String - 字符串
const str1 = "hello";
const str2 = 'world';
const str3 = `template ${str1}`;  // 模板字符串
console.log(typeof str1);  // "string"

// 3. Boolean - 布尔值
const isTrue = true;
const isFalse = false;
console.log(typeof isTrue);  // "boolean"

// 4. Undefined - 未定义
let notAssigned;
console.log(notAssigned);       // undefined
console.log(typeof notAssigned); // "undefined"

// 5. Null - 空值
const empty = null;
console.log(empty);        // null
console.log(typeof empty); // "object" ← 历史 bug

// 6. Symbol - 符号 (ES6)
const sym = Symbol('description');
console.log(typeof sym);  // "symbol"

// 每个 Symbol 都唯一
console.log(Symbol('id') === Symbol('id'));  // false

// 7. BigInt - 大整数 (ES2020)
const bigint = 9007199254740991n;  // 后缀 n
console.log(typeof bigint);  // "bigint"

// ========== 引用类型 (Reference Type) ==========

// 8. Object - 对象
const obj = { name: "Alice" };
const arr = [1, 2, 3];
const func = function() {};
const date = new Date();
const regex = /abc/;

console.log(typeof obj);   // "object"
console.log(typeof arr);   // "object"
console.log(typeof func);  // "function" ← 特殊处理
console.log(typeof date);  // "object"
console.log(typeof regex); // "object"
```

**关键特征**:
- **基本类型**: 值不可变, 存储在栈内存, 按值传递
- **引用类型**: 内容可变, 存储在堆内存, 按引用传递

---

**规则 2: 基本类型 vs 引用类型的本质区别**

基本类型和引用类型在存储、赋值、比较上有本质区别。

```javascript
// ========== 基本类型: 值拷贝 ==========

let a = 10;
let b = a;  // 复制值

b = 20;

console.log('a:', a);  // 10 ← a 不受影响
console.log('b:', b);  // 20

// 内存模型:
// ┌─────────┬─────────┐
// │ 变量名  │   值    │
// ├─────────┼─────────┤
// │   a     │   10    │  ← 独立的值
// │   b     │   20    │  ← 独立的值
// └─────────┴─────────┘

// 基本类型比较: 比较值
console.log(10 === 10);  // true
console.log("hello" === "hello");  // true

// ========== 引用类型: 引用拷贝 ==========

let obj1 = { count: 0 };
let obj2 = obj1;  // 复制引用, 不是值

obj2.count = 1;

console.log('obj1.count:', obj1.count);  // 1 ← obj1 被修改了
console.log('obj2.count:', obj2.count);  // 1

// 内存模型:
// ┌─────────┬─────────┐        ┌──────────────────┐
// │ 变量名  │  引用   │───────▶│    实际对象      │
// ├─────────┼─────────┤        ├──────────────────┤
// │  obj1   │  0x1234 │───────▶│ { count: 1 }     │
// │  obj2   │  0x1234 │───────▶│                  │
// └─────────┴─────────┘        └──────────────────┘
// obj1 和 obj2 指向同一个对象

// 引用类型比较: 比较引用地址
const objA = { value: 42 };
const objB = { value: 42 };
console.log(objA === objB);  // false ← 内容相同但引用不同

const objC = objA;
console.log(objA === objC);  // true ← 引用相同

// ========== 函数参数传递 ==========

function modifyPrimitive(num) {
    num = 100;  // 只修改局部副本
}

let x = 10;
modifyPrimitive(x);
console.log(x);  // 10 ← x 不变

function modifyObject(obj) {
    obj.value = 100;  // 修改引用指向的对象
}

let myObj = { value: 10 };
modifyObject(myObj);
console.log(myObj.value);  // 100 ← myObj 被修改
```

**核心原理**:
- **基本类型赋值**: 复制值, 两个变量独立
- **引用类型赋值**: 复制引用, 两个变量共享对象
- **比较行为**: 基本类型比较值, 引用类型比较引用地址

---

**规则 3: typeof 运算符的两个历史 bug**

`typeof` 是最常用的类型判断方法, 但有两个已知 bug。

```javascript
// ========== Bug 1: typeof null === "object" ==========

console.log(typeof null);  // "object" ← 错误! 应该是 "null"

// 原因: JavaScript 最初实现中, 值的类型标签使用低 3 位表示
// - 000: object
// - 001: int
// - 010: double
// - 100: string
// - 110: boolean
// null 的机器码是全 0 (0x00), 所以被误判为 object

// 正确判断 null
if (value === null) {
    console.log('这是 null');
}

// ========== Bug 2: typeof [] === "object" ==========

console.log(typeof []);  // "object" ← 无法区分数组和对象
console.log(typeof {});  // "object"

// 正确判断数组
if (Array.isArray(value)) {
    console.log('这是数组');
}

// ========== typeof 的正确返回值 ==========

console.log(typeof 42);         // "number"
console.log(typeof "hello");    // "string"
console.log(typeof true);       // "boolean"
console.log(typeof undefined);  // "undefined"
console.log(typeof Symbol());   // "symbol"
console.log(typeof 42n);        // "bigint"
console.log(typeof {});         // "object"
console.log(typeof []);         // "object" ← bug
console.log(typeof null);       // "object" ← bug
console.log(typeof function(){}); // "function" ← 特殊处理

// ========== 修复 typeof 的函数 ==========

function getType(value) {
    // 修复 null bug
    if (value === null) return "null";

    const type = typeof value;

    // 修复数组 bug
    if (type === "object" && Array.isArray(value)) {
        return "array";
    }

    return type;
}

console.log(getType(null));    // "null" ← 修复
console.log(getType([]));      // "array" ← 修复
console.log(getType({}));      // "object"
```

**为什么不修复这些 bug?**
- **向后兼容**: 太多旧代码依赖这些行为, 修复会破坏兼容性
- **TC39 决定**: 永久保留这些 bug, 用其他方法弥补

---

**规则 4: Number 类型的三个特殊值**

`Number` 类型有三个特殊值: `NaN`, `Infinity`, `-Infinity`。

```javascript
// ========== NaN: Not a Number ==========

const nan = 0 / 0;
console.log(nan);  // NaN

// NaN 的怪异特性
console.log(typeof NaN);  // "number" ← NaN 是 number 类型
console.log(NaN === NaN);  // false ← NaN 不等于自己
console.log(NaN !== NaN);  // true

// 产生 NaN 的场景
console.log(0 / 0);           // NaN (不定式)
console.log(Math.sqrt(-1));   // NaN (负数开平方)
console.log(parseInt("abc")); // NaN (解析失败)
console.log("text" * 2);      // NaN (非法运算)

// 正确判断 NaN
console.log(Number.isNaN(NaN));     // true
console.log(Number.isNaN("text"));  // false
console.log(Number.isNaN(42));      // false

// 全局 isNaN vs Number.isNaN
console.log(isNaN("text"));         // true ← 会先转换, 不推荐
console.log(Number.isNaN("text"));  // false ← 不转换, 推荐

// 利用 NaN !== NaN 判断
function isNaNValue(value) {
    return value !== value;
}
console.log(isNaNValue(NaN));  // true

// ========== Infinity: 无穷大 ==========

console.log(1 / 0);   // Infinity
console.log(-1 / 0);  // -Infinity
console.log(Math.pow(10, 1000));  // Infinity (超出最大值)

console.log(typeof Infinity);  // "number"

// Infinity 的运算
console.log(Infinity + 1);  // Infinity
console.log(Infinity * 2);  // Infinity
console.log(Infinity / 2);  // Infinity
console.log(Infinity - Infinity);  // NaN
console.log(1 / Infinity);  // 0

// 判断是否为有限数
console.log(Number.isFinite(42));        // true
console.log(Number.isFinite(Infinity));  // false
console.log(Number.isFinite(NaN));       // false

// Number 的范围
console.log(Number.MAX_VALUE);           // 1.7976931348623157e+308
console.log(Number.MIN_VALUE);           // 5e-324
console.log(Number.MAX_SAFE_INTEGER);    // 9007199254740991
console.log(Number.MIN_SAFE_INTEGER);    // -9007199254740991

// 超出安全范围的问题
const big = 9007199254740992;
console.log(big);        // 9007199254740992
console.log(big + 1);    // 9007199254740992 ← 无法正确表示
console.log(big + 2);    // 9007199254740994 ← 跳过了 ...993
```

**关键点**:
- **NaN**: 唯一不等于自己的值, 用 `Number.isNaN()` 判断
- **Infinity**: 表示超出范围的数值, 用 `Number.isFinite()` 判断
- **安全整数范围**: `-(2^53 - 1)` 到 `2^53 - 1`, 超出使用 `BigInt`

---

**规则 5: undefined vs null 的语义区别**

`undefined` 和 `null` 都表示 "空", 但语义不同。

```javascript
// ========== undefined: 未定义 ==========

// 场景 1: 变量声明但未赋值
let a;
console.log(a);  // undefined

// 场景 2: 访问不存在的属性
const obj = { name: "Alice" };
console.log(obj.age);  // undefined

// 场景 3: 函数无返回值
function doNothing() {}
console.log(doNothing());  // undefined

// 场景 4: 函数参数未传递
function greet(name) {
    console.log(name);  // undefined (未传参)
}
greet();

// typeof undefined
console.log(typeof undefined);  // "undefined"

// ========== null: 有意的空值 ==========

// 场景 1: 显式表示 "无对象"
let user = null;  // 目前没有用户

// 场景 2: 清空对象引用
let obj = { data: "..." };
obj = null;  // 清空引用, 帮助垃圾回收

// 场景 3: 函数返回 "未找到"
function findUser(id) {
    if (id === 1) return { name: "Alice" };
    return null;  // 明确表示 "未找到"
}

// typeof null (bug)
console.log(typeof null);  // "object"

// ========== 比较行为 ==========

console.log(undefined == null);   // true (宽松相等)
console.log(undefined === null);  // false (严格不等)

console.log(null == 0);   // false
console.log(null >= 0);   // true ← 比较时转换为 0
console.log(null > 0);    // false

console.log(undefined == 0);  // false
console.log(undefined >= 0);  // false

// ========== 最佳实践 ==========

// ✅ 推荐: 使用 null 表示 "有意的空"
let data = null;  // 数据还未加载
fetchData().then(result => {
    data = result;  // 加载完成
});

// ❌ 不推荐: 使用 undefined 表示空
let data = undefined;  // 语义不明确

// 函数返回值: 有意的空用 null, 无返回值用 undefined
function getValue(key) {
    if (key === "name") return "Alice";
    return null;  // 明确表示 "没有值"
}

function doSomething() {
    console.log("done");
    // 没有 return, 返回 undefined
}
```

**语义区别**:
- **undefined**: 系统级别的 "空", 表示 "未定义/未初始化"
- **null**: 程序级别的 "空", 表示 "有意的空对象引用"
- **使用建议**: 主动使用 `null`, 让 `undefined` 自然出现

---

**规则 6: Symbol 类型的唯一性与隐藏性**

`Symbol` 是 ES6 引入的新基本类型, 用于创建唯一标识符。

```javascript
// ========== Symbol 的唯一性 ==========

const sym1 = Symbol('description');
const sym2 = Symbol('description');

console.log(sym1 === sym2);  // false ← 每个 Symbol 都唯一
console.log(typeof sym1);    // "symbol"

// 即使描述相同, Symbol 也不相等
const id1 = Symbol('id');
const id2 = Symbol('id');
console.log(id1 === id2);  // false

// ========== Symbol 作为对象属性 ==========

const uniqueKey = Symbol('key');

const obj = {
    name: "Alice",
    [uniqueKey]: "hidden value"  // Symbol 属性
};

console.log(obj.name);        // "Alice"
console.log(obj[uniqueKey]);  // "hidden value"
console.log(obj["key"]);      // undefined ← Symbol 不能用字符串访问

// ========== Symbol 属性的隐藏性 ==========

const secret = Symbol('secret');
const user = {
    name: "Alice",
    age: 25,
    [secret]: "password123"
};

// for...in 不遍历 Symbol 属性
console.log('=== for...in ===');
for (let key in user) {
    console.log(key);  // 只输出: "name", "age"
}

// Object.keys 不包含 Symbol
console.log('Object.keys:', Object.keys(user));  // ["name", "age"]

// JSON.stringify 忽略 Symbol
console.log('JSON:', JSON.stringify(user));  // {"name":"Alice","age":25}

// 获取 Symbol 属性
console.log('Symbol 属性:', Object.getOwnPropertySymbols(user));  // [Symbol(secret)]

// 获取所有属性 (包括 Symbol)
console.log('所有属性:', Reflect.ownKeys(user));  // ["name", "age", Symbol(secret)]

// ========== 全局 Symbol 注册表 ==========

// Symbol.for: 在全局注册表中创建/获取 Symbol
const global1 = Symbol.for('app.id');
const global2 = Symbol.for('app.id');

console.log(global1 === global2);  // true ← 相同描述返回同一个 Symbol

// Symbol.keyFor: 获取全局 Symbol 的描述
console.log(Symbol.keyFor(global1));  // "app.id"
console.log(Symbol.keyFor(sym1));     // undefined (非全局 Symbol)

// ========== Symbol 的实际应用 ==========

// 应用 1: 防止属性名冲突
const library1 = Symbol('id');
const library2 = Symbol('id');

const user = {
    [library1]: "lib1-id",
    [library2]: "lib2-id"
};
// 两个库都可以安全使用 'id' 属性

// 应用 2: 定义对象的私有属性
const _privateData = Symbol('privateData');

class User {
    constructor(name) {
        this.name = name;
        this[_privateData] = { password: "secret" };
    }

    getPrivate() {
        return this[_privateData];
    }
}

const alice = new User("Alice");
console.log(alice.name);            // "Alice"
console.log(alice._privateData);    // undefined
console.log(alice[_privateData]);   // { password: "secret" }

// 应用 3: 定义类的内部方法
const _calculate = Symbol('calculate');

class Calculator {
    [_calculate](a, b) {
        return a + b;
    }

    add(a, b) {
        return this[_calculate](a, b);
    }
}
```

**关键特性**:
- **唯一性**: 每个 `Symbol()` 创建的值都唯一
- **隐藏性**: Symbol 属性不被 `for...in`, `Object.keys`, `JSON.stringify` 遍历
- **全局注册**: `Symbol.for()` 可创建全局 Symbol
- **实际应用**: 防止属性名冲突, 创建私有属性, 定义内部方法

---

**规则 7: BigInt 类型与安全整数范围**

`BigInt` 是 ES2020 引入的新基本类型, 用于表示任意精度的整数。

```javascript
// ========== JavaScript 的安全整数范围 ==========

console.log(Number.MAX_SAFE_INTEGER);  // 9007199254740991 (2^53 - 1)
console.log(Number.MIN_SAFE_INTEGER);  // -9007199254740991

// 超出安全范围的问题
const big = 9007199254740992;  // 2^53
console.log(big);        // 9007199254740992
console.log(big + 1);    // 9007199254740992 ← 错误! 应该是 ...993
console.log(big + 2);    // 9007199254740994 ← 跳过了 ...993

// 原理: IEEE 754 双精度浮点数的精度限制
// 尾数部分只有 52 位, 加上隐藏的 1 位, 共 53 位
// 超过 2^53 无法精确表示所有整数

// ========== BigInt 的创建 ==========

// 方式 1: 字面量 (推荐)
const bigint1 = 9007199254740991n;  // 后缀 n
const bigint2 = 123456789012345678901234567890n;

// 方式 2: BigInt 构造函数
const bigint3 = BigInt("9007199254740992");
const bigint4 = BigInt(123);  // 从 Number 转换

console.log(typeof bigint1);  // "bigint"

// ========== BigInt 的运算 ==========

const a = 9007199254740991n;
const b = 2n;

console.log(a + b);  // 9007199254740993n ← 正确
console.log(a * b);  // 18014398509481982n
console.log(a - b);  // 9007199254740989n
console.log(a / b);  // 4503599627370495n ← 整数除法
console.log(a % b);  // 1n

// 负数
console.log(-123n);  // -123n

// 指数运算
console.log(2n ** 100n);  // 1267650600228229401496703205376n

// ========== BigInt 与 Number 的混合运算 (禁止) ==========

try {
    console.log(1n + 1);  // TypeError
} catch (e) {
    console.log('错误:', e.message);  // "Cannot mix BigInt and other types"
}

try {
    console.log(Math.sqrt(4n));  // TypeError
} catch (e) {
    console.log('错误:', e.message);
}

// 需要显式转换
console.log(1n + BigInt(1));  // 2n ← 正确
console.log(Number(2n) + 1);  // 3 ← 正确 (注意精度损失)

// ========== BigInt 的比较 ==========

console.log(1n === 1);    // false (严格不等, 类型不同)
console.log(1n == 1);     // true (宽松相等, 值相同)
console.log(1n < 2);      // true (大小比较正常)
console.log(10n > 5);     // true

// ========== BigInt 的限制 ==========

// 限制 1: 不能使用 Math 对象
// console.log(Math.sqrt(4n));  // TypeError
// console.log(Math.max(1n, 2n));  // TypeError

// 限制 2: 不能与 Number 混合运算
// console.log(1n + 1.5);  // TypeError

// 限制 3: JSON.stringify 不支持
try {
    JSON.stringify({ value: 123n });
} catch (e) {
    console.log('错误:', e.message);  // "Do not know how to serialize a BigInt"
}

// 解决方案: 自定义 toJSON
BigInt.prototype.toJSON = function() {
    return this.toString();
};
console.log(JSON.stringify({ value: 123n }));  // {"value":"123"}

// 限制 4: 除法是整数除法
console.log(5n / 2n);  // 2n ← 向零取整, 不是 2.5

// ========== BigInt 的实际应用 ==========

// 应用 1: 大整数计算
function factorial(n) {
    let result = 1n;
    for (let i = 1n; i <= n; i++) {
        result *= i;
    }
    return result;
}

console.log(factorial(20n));  // 2432902008176640000n ← 准确
console.log(factorial(100n)); // 巨大的数字, Number 无法表示

// 应用 2: 密码学
const prime = 2n ** 521n - 1n;  // 梅森素数
console.log(prime.toString().length);  // 157 位数字

// 应用 3: 时间戳 (纳秒级)
const nanoTimestamp = BigInt(Date.now()) * 1000000n;
console.log(nanoTimestamp);  // 纳秒级时间戳

// 应用 4: 货币计算 (避免浮点数精度问题)
const price = 1999n;  // 19.99 元 (单位: 分)
const quantity = 3n;
const total = price * quantity;  // 5997 分 = 59.97 元
console.log(total);  // 5997n
```

**关键点**:
- **精度**: BigInt 可表示任意精度的整数
- **安全范围**: Number 只能精确表示 `-(2^53 - 1)` 到 `2^53 - 1`
- **类型隔离**: BigInt 不能与 Number 混合运算, 必须显式转换
- **应用场景**: 大整数计算, 密码学, 高精度时间戳, 货币计算

---

**规则 8: 类型判断的四种方法与最佳实践**

JavaScript 有四种类型判断方法, 各有优缺点。

```javascript
// ========== 方法 1: typeof (基本类型) ==========

console.log(typeof 42);         // "number"
console.log(typeof "hello");    // "string"
console.log(typeof true);       // "boolean"
console.log(typeof undefined);  // "undefined"
console.log(typeof Symbol());   // "symbol"
console.log(typeof 42n);        // "bigint"
console.log(typeof function(){}); // "function"

// typeof 的问题
console.log(typeof null);       // "object" ← bug 1
console.log(typeof []);         // "object" ← bug 2
console.log(typeof {});         // "object"

// 优点: 快速, 简单, 适合基本类型
// 缺点: 无法区分 null/数组/对象

// ========== 方法 2: instanceof (对象类型) ==========

console.log([] instanceof Array);    // true
console.log({} instanceof Object);   // true
console.log([] instanceof Object);   // true (数组也是对象)
console.log(new Date() instanceof Date);  // true
console.log(/abc/ instanceof RegExp);     // true

// instanceof 原理: 检查原型链
console.log([].__proto__ === Array.prototype);  // true
console.log(Array.prototype instanceof Object); // true

// instanceof 的问题
console.log(42 instanceof Number);  // false ← 基本类型返回 false
console.log("hello" instanceof String);  // false

// 包装对象才返回 true
console.log(new Number(42) instanceof Number);  // true
console.log(new String("hello") instanceof String);  // true

// 跨 iframe 问题
const iframe = document.createElement('iframe');
document.body.appendChild(iframe);
const iframeArray = iframe.contentWindow.Array;
const arr = new iframeArray();

console.log(arr instanceof Array);  // false ← 不同 Array 构造函数
console.log(arr instanceof iframeArray);  // true

// 优点: 可判断对象类型, 检查继承关系
// 缺点: 无法判断基本类型, 跨 iframe 失败

// ========== 方法 3: Array.isArray (数组专用) ==========

console.log(Array.isArray([]));       // true
console.log(Array.isArray({}));       // false
console.log(Array.isArray("123"));    // false
console.log(Array.isArray(null));     // false

// 跨 iframe 也正常工作
console.log(Array.isArray(arr));  // true ← 解决了 instanceof 的问题

// 优点: 专门判断数组, 可靠, 跨 iframe 工作
// 缺点: 只能判断数组

// ========== 方法 4: Object.prototype.toString (精确判断) ==========

function getType(value) {
    return Object.prototype.toString.call(value).slice(8, -1);
}

console.log(getType(42));         // "Number"
console.log(getType("hello"));    // "String"
console.log(getType(true));       // "Boolean"
console.log(getType(null));       // "Null" ← 修复了 typeof bug
console.log(getType(undefined));  // "Undefined"
console.log(getType(Symbol()));   // "Symbol"
console.log(getType(42n));        // "BigInt"
console.log(getType([]));         // "Array" ← 修复了 typeof bug
console.log(getType({}));         // "Object"
console.log(getType(function(){})); // "Function"
console.log(getType(new Date())); // "Date"
console.log(getType(/abc/));      // "RegExp"
console.log(getType(new Map()));  // "Map"
console.log(getType(new Set()));  // "Set"

// 原理: 内部 [[Class]] 属性
// "[object Array]" → slice(8, -1) → "Array"

// 优点: 最可靠, 精确, 统一接口, 跨 iframe 工作
// 缺点: 稍慢, 语法繁琐

// ========== 综合判断函数 (最佳实践) ==========

function getValueType(value) {
    // 快速路径: null
    if (value === null) return "null";

    // 快速路径: 基本类型
    const primitiveType = typeof value;
    if (primitiveType !== "object") {
        return primitiveType;
    }

    // 精确路径: 引用类型
    const objectType = Object.prototype.toString.call(value).slice(8, -1).toLowerCase();
    return objectType;
}

console.log('=== 综合判断测试 ===');
console.log(getValueType(42));        // "number"
console.log(getValueType(null));      // "null" ← 修复
console.log(getValueType([]));        // "array" ← 修复
console.log(getValueType({}));        // "object"
console.log(getValueType(new Date())); // "date"
console.log(getValueType(/abc/));     // "regexp"

// ========== 类型判断最佳实践矩阵 ==========

/*
场景                       | 推荐方法
--------------------------|------------------------------------------
判断基本类型              | typeof (注意 null bug)
判断是否为数组            | Array.isArray
判断对象类型              | instanceof (同 iframe)
判断对象类型 (跨 iframe)  | Object.prototype.toString
统一类型判断接口          | Object.prototype.toString
性能要求极高              | typeof (基本类型) + instanceof (对象)

具体类型判断:
- null: value === null
- undefined: value === undefined 或 typeof value === "undefined"
- 数组: Array.isArray(value)
- NaN: Number.isNaN(value)
- 有限数: Number.isFinite(value)
- 整数: Number.isInteger(value)
- 安全整数: Number.isSafeInteger(value)
*/

// ========== 实用工具函数集 ==========

// 是否为基本类型
function isPrimitive(value) {
    return value === null || typeof value !== "object";
}

// 是否为引用类型
function isObject(value) {
    return value !== null && typeof value === "object";
}

// 是否为纯对象 (plain object)
function isPlainObject(value) {
    if (Object.prototype.toString.call(value) !== "[object Object]") {
        return false;
    }

    const proto = Object.getPrototypeOf(value);
    return proto === null || proto === Object.prototype;
}

console.log('=== 工具函数测试 ===');
console.log(isPrimitive(42));       // true
console.log(isPrimitive({}));       // false
console.log(isObject({}));          // true
console.log(isObject([]));          // true
console.log(isObject(null));        // false (特殊处理)
console.log(isPlainObject({}));     // true
console.log(isPlainObject([]));     // false
console.log(isPlainObject(new Date())); // false
```

**最佳实践总结**:
1. **基本类型**: 使用 `typeof`, 注意 `null` bug
2. **数组**: 使用 `Array.isArray`
3. **对象类型**: 使用 `instanceof` (同 iframe) 或 `Object.prototype.toString` (跨 iframe)
4. **统一接口**: 使用 `Object.prototype.toString`
5. **特殊值**: `null` 用 `===`, `NaN` 用 `Number.isNaN`, `Infinity` 用 `Number.isFinite`

---

**记录者注**:

JavaScript 的数据类型系统包含 8 种类型: 7 种基本类型 (Number, String, Boolean, Undefined, Null, Symbol, BigInt) 和 1 种引用类型 (Object)。基本类型和引用类型在存储方式、赋值行为、比较行为上有本质区别。

关键在于理解值比较与引用比较的区别: 基本类型比较值, 引用类型比较引用地址。这解释了为什么内容相同的对象不相等 (`{a:1} !== {a:1}`), 为什么修改对象副本会影响原对象。

类型判断有四种方法: `typeof` (基本类型, 有 2 个 bug), `instanceof` (对象类型), `Array.isArray` (数组专用), `Object.prototype.toString` (精确判断)。理解每种方法的优缺点和适用场景, 选择合适的判断方式。

特殊值需要特别注意: `NaN` 不等于自己, `typeof null` 返回 `"object"`, `BigInt` 不能与 `Number` 混合运算。理解这些特殊行为, 避免类型判断的陷阱。

记住: **8 种类型 (7 基本 + 1 引用); 基本类型值比较, 引用类型引用比较; typeof 有 2 个 bug (null 和 array); NaN !== NaN, 用 Number.isNaN 判断; BigInt 超出安全范围, 不能与 Number 混用; 类型判断用 typeof/instanceof/Array.isArray/Object.prototype.toString**。理解数据类型系统, 就理解了 JavaScript 如何分类和存储不同的值, 以及如何正确判断和比较它们。

---

**事故档案编号**: JS-2024-1637
**影响范围**: 类型判断、值比较、类型转换、对象去重
**根本原因**: 不理解基本类型和引用类型的区别, 不理解值比较和引用比较的本质差异
**修复成本**: 低 (使用正确的类型判断方法, 理解比较行为)
**预防措施**: 系统学习 JavaScript 类型系统, 使用 TypeScript 强类型检查, 代码审查关注类型判断和比较逻辑

这是 JavaScript 世界第 37 次被记录的数据类型事故。JavaScript 有 8 种数据类型——7 种基本类型 (Number, String, Boolean, Undefined, Null, Symbol, BigInt) 和 1 种引用类型 (Object)。基本类型存储值, 按值比较; 引用类型存储引用, 按引用地址比较。`typeof` 有 2 个历史 bug (`null` 和数组), 需要使用 `Array.isArray`, `instanceof`, `Object.prototype.toString` 等方法精确判断。理解数据类型系统, 就理解了 JavaScript 如何分类存储值, 如何比较值, 以及如何正确判断类型避免陷阱。

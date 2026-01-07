《第 111 次记录: 订单ID的碰撞谜案 —— BigInt 的超越极限之路》

---

## 生产告警

周一早上九点半, 你的手机响了。

这是运营团队的紧急电话。"订单系统出问题了!" 对方的声音带着焦虑, "有两个用户反馈他们的订单被合并了, 明明是不同的订单, 现在看起来像同一个。"

你快速打开笔记本, 登录生产环境的监控系统。订单服务的错误率在最近一小时内突然上升了 3%——这是一个危险的信号。

你调出最近创建的订单记录, 看到了让你困惑的一幕:

```javascript
// 订单数据库记录
{
  orderId: 9007199254740992,
  userId: 12345,
  amount: 299.99
}

{
  orderId: 9007199254740992,  // ❌ 与上一个订单ID相同!
  userId: 67890,
  amount: 599.99
}
```

"这不可能..." 你喃喃自语, "订单ID是用雪花算法生成的, 理论上不会重复。"

你检查了订单ID生成服务, 日志显示生成的ID确实不同:

```
[INFO] Generated Order ID: 9007199254740991
[INFO] Generated Order ID: 9007199254740993
```

"生成的ID明明是 991 和 993, 为什么存储后都变成了 992?" 你皱起了眉头。

你又发现了另一个诡异的现象。用户的账户余额计算也出现了问题:

```javascript
// 用户充值记录
const balance = 0;
const deposit1 = 0.1;  // 充值 0.1 元
const deposit2 = 0.2;  // 充值 0.2 元

const total = balance + deposit1 + deposit2;
console.log(total);  // 期望: 0.3, 实际: 0.30000000000000004
```

"0.1 + 0.2 怎么会等于 0.30000000000000004?" 你感到头皮发麻, "这会导致财务对账失败!"

产品经理走到你身边: "什么时候能修复? 财务部门已经收到多个用户投诉了。"

"我需要时间调查, " 你说, "这不是普通的 bug, 可能涉及到 JavaScript 数字系统的根本限制。"

---

## 数字极限的发现

上午十点, 你开始系统地测试 JavaScript 的数字行为。

你首先测试了大整数的精度:

```javascript
console.log(9007199254740992);  // 输出: 9007199254740992
console.log(9007199254740993);  // 输出: 9007199254740992 ❌
```

"等等..." 你惊讶地坐直了身体, "9007199254740993 被舍入成了 9007199254740992?"

你继续测试:

```javascript
console.log(9007199254740991 + 1);  // 9007199254740992
console.log(9007199254740992 + 1);  // 9007199254740992 ❌ 应该是 993!
console.log(9007199254740993 + 1);  // 9007199254740994
```

"这完全不符合数学规则!" 你说, "9007199254740992 加 1 居然还是 9007199254740992?"

你打开 MDN 文档, 搜索 "JavaScript 数字精度"。一段话让你恍然大悟:

> **Number.MAX_SAFE_INTEGER**: JavaScript 中最大的安全整数是 2^53 - 1, 即 9007199254740991。超过这个值的整数无法精确表示。

"所以 9007199254740992 已经超过了安全整数范围, " 你理解了, "JavaScript 无法精确表示这个数字!"

你测试了这个常量:

```javascript
console.log(Number.MAX_SAFE_INTEGER);  // 9007199254740991
console.log(Number.MAX_SAFE_INTEGER + 1);  // 9007199254740992
console.log(Number.MAX_SAFE_INTEGER + 2);  // 9007199254740992 ❌
console.log(Number.MAX_SAFE_INTEGER + 3);  // 9007199254740994
```

"这就是订单ID碰撞的原因!" 你兴奋地说, "雪花算法生成的ID都在 16 位以上, 早就超过了 2^53 的限制!"

你又测试了小数精度:

```javascript
console.log(0.1 + 0.2);  // 0.30000000000000004
console.log(0.1 + 0.2 === 0.3);  // false
console.log(0.3 - 0.2);  // 0.09999999999999998
console.log(0.3 - 0.1);  // 0.19999999999999998
```

"JavaScript 连简单的小数加法都算不准, " 你想, "这是因为 IEEE 754 浮点数标准的限制。"

---

## BigInt 的发现

中午十二点, 你在 Stack Overflow 上搜索"JavaScript 大整数", 看到了一个陌生的语法:

```javascript
const bigNum = 9007199254740993n;  // 注意末尾的 n
console.log(bigNum);  // 9007199254740993n
console.log(typeof bigNum);  // 'bigint'
```

"BigInt?" 你困惑, "这是什么?"

你查阅 MDN, 发现这是 ES2020 引入的新数据类型:

> **BigInt**: 可以表示任意大的整数, 不受 2^53 - 1 的限制。

你立刻开始测试:

```javascript
// 创建 BigInt
const big1 = 9007199254740993n;
const big2 = BigInt(9007199254740993);
const big3 = BigInt("9007199254740993");

console.log(big1);  // 9007199254740993n
console.log(big2);  // 9007199254740993n
console.log(big3);  // 9007199254740993n

// BigInt 运算
console.log(big1 + 1n);  // 9007199254740994n ✓
console.log(big1 + 2n);  // 9007199254740995n ✓
console.log(big1 * 2n);  // 18014398509481986n ✓
```

"完美!" 你兴奋, "BigInt 可以精确表示任意大的整数!"

你测试了超大数字:

```javascript
const huge = 12345678901234567890123456789n;
console.log(huge);  // 12345678901234567890123456789n

console.log(huge + 1n);  // 12345678901234567890123456790n
console.log(huge * 2n);  // 24691357802469135780246913578n

// 对比 Number 的行为
const hugeNum = 12345678901234567890123456789;
console.log(hugeNum);  // 1.2345678901234568e+28 ❌ 精度丢失
```

"Number 类型完全无法表示这种超大整数, " 你总结, "但 BigInt 可以!"

---

## BigInt 的限制与陷阱

下午两点, 你开始深入测试 BigInt 的特性。

你很快发现了第一个陷阱——BigInt 和 Number 不能混用:

```javascript
const bigNum = 100n;
const normalNum = 50;

try {
    console.log(bigNum + normalNum);  // ❌ TypeError
} catch (e) {
    console.error('错误:', e.message);
    // TypeError: Cannot mix BigInt and other types
}
```

"BigInt 和 Number 是完全独立的类型, " 你意识到, "不能直接运算。"

你需要显式转换:

```javascript
const bigNum = 100n;
const normalNum = 50;

// 方案 1: 将 Number 转换为 BigInt
console.log(bigNum + BigInt(normalNum));  // 150n

// 方案 2: 将 BigInt 转换为 Number (危险!)
console.log(Number(bigNum) + normalNum);  // 150

// 但超过安全范围的 BigInt 转 Number 会丢失精度
const huge = 9007199254740993n;
console.log(Number(huge));  // 9007199254740992 ❌ 精度丢失
```

你又发现了第二个陷阱——JSON 序列化问题:

```javascript
const order = {
    orderId: 9007199254740993n,
    amount: 299.99
};

try {
    const json = JSON.stringify(order);  // ❌ TypeError
} catch (e) {
    console.error('错误:', e.message);
    // TypeError: Do not know how to serialize a BigInt
}
```

"JSON.stringify 不支持 BigInt!" 你惊讶, "这会导致 API 返回失败!"

你找到了解决方案:

```javascript
// 方案 1: 自定义序列化
BigInt.prototype.toJSON = function() {
    return this.toString();
};

const order = {
    orderId: 9007199254740993n,
    amount: 299.99
};

const json = JSON.stringify(order);
console.log(json);  // {"orderId":"9007199254740993","amount":299.99}

// 方案 2: 使用 replacer 函数
const json2 = JSON.stringify(order, (key, value) => {
    return typeof value === 'bigint' ? value.toString() : value;
});
console.log(json2);  // {"orderId":"9007199254740993","amount":299.99}
```

你又测试了第三个陷阱——除法行为:

```javascript
// Number 的除法返回浮点数
console.log(10 / 3);  // 3.3333333333333335

// BigInt 的除法会舍弃小数部分
console.log(10n / 3n);  // 3n ⚠️ 注意: 直接舍弃小数
console.log(10n / 4n);  // 2n
console.log(11n / 4n);  // 2n
```

"BigInt 的除法是整数除法, " 你理解了, "会直接舍弃小数部分, 不是四舍五入!"

你继续测试了比较操作:

```javascript
// 相等比较
console.log(100n === 100);  // false (类型不同)
console.log(100n == 100);  // true (值相同, 类型转换)

// 大小比较
console.log(100n > 99);  // true
console.log(100n < 101);  // true

// 排序
const mixed = [5n, 2, 8n, 1, 10n];
mixed.sort();
console.log(mixed);  // [1, 2, 5n, 8n, 10n] ⚠️ 混合类型可以排序
```

---

## 修复生产问题

下午四点, 你开始修复订单系统的 bug。

你首先修改了订单ID的生成和存储:

```javascript
// ❌ 旧代码: 使用 Number 存储订单ID
class OrderService {
    async createOrder(userId, items) {
        const orderId = generateSnowflakeId();  // 返回大整数

        await db.insert('orders', {
            order_id: orderId,  // ❌ Number 类型, 精度丢失
            user_id: userId,
            items: items
        });

        return orderId;
    }
}

// ✅ 新代码: 使用 BigInt 和字符串
class OrderService {
    async createOrder(userId, items) {
        const orderId = generateSnowflakeIdAsBigInt();  // 返回 BigInt

        await db.insert('orders', {
            order_id: orderId.toString(),  // 存储为字符串
            user_id: userId,
            items: items
        });

        return orderId;
    }

    async getOrder(orderId) {
        // 从数据库读取时转换回 BigInt
        const row = await db.query('SELECT * FROM orders WHERE order_id = ?', [orderId.toString()]);

        return {
            ...row,
            orderId: BigInt(row.order_id)  // 转换回 BigInt
        };
    }
}
```

你又修复了金额计算问题:

```javascript
// ❌ 旧代码: 直接用浮点数计算
function calculateTotal(items) {
    return items.reduce((sum, item) => sum + item.price, 0);
}

const total = calculateTotal([
    { price: 0.1 },
    { price: 0.2 }
]);
console.log(total);  // 0.30000000000000004 ❌

// ✅ 新代码: 用整数计算 (以分为单位)
function calculateTotal(items) {
    // 将元转换为分 (乘以 100)
    const totalCents = items.reduce((sum, item) => {
        return sum + Math.round(item.price * 100);
    }, 0);

    // 转换回元
    return totalCents / 100;
}

const total = calculateTotal([
    { price: 0.1 },
    { price: 0.2 }
]);
console.log(total);  // 0.3 ✓

// 或者使用专门的货币库
import { Money } from 'money-lib';

const amount1 = new Money(0.1, 'CNY');
const amount2 = new Money(0.2, 'CNY');
const total = amount1.add(amount2);
console.log(total.toString());  // '0.30 CNY' ✓
```

你还修改了 API 返回格式:

```javascript
// ❌ 旧代码: 直接返回 BigInt (JSON.stringify 失败)
app.get('/api/orders/:id', async (req, res) => {
    const order = await orderService.getOrder(BigInt(req.params.id));
    res.json(order);  // ❌ TypeError: Do not know how to serialize a BigInt
});

// ✅ 新代码: 将 BigInt 转换为字符串
app.get('/api/orders/:id', async (req, res) => {
    const order = await orderService.getOrder(BigInt(req.params.id));

    // 方案 1: 手动转换
    res.json({
        ...order,
        orderId: order.orderId.toString()
    });

    // 方案 2: 使用全局 toJSON
    BigInt.prototype.toJSON = function() {
        return this.toString();
    };
    res.json(order);
});
```

---

## BigInt 的实际应用

下午五点, 你整理了 BigInt 的使用场景。

**场景 1: 数据库主键和雪花ID**

```javascript
// Twitter 雪花算法生成的ID超过了 2^53
const snowflakeId = 1234567890123456789n;

// 数据库操作
await db.query(
    'INSERT INTO users (id, name) VALUES (?, ?)',
    [snowflakeId.toString(), 'Alice']
);

// API 返回
res.json({
    userId: snowflakeId.toString(),  // 以字符串形式返回
    name: 'Alice'
});

// 前端接收
const response = await fetch('/api/user/1234567890123456789');
const user = await response.json();
const userId = BigInt(user.userId);  // 转换回 BigInt
```

**场景 2: 加密和哈希计算**

```javascript
// RSA 密钥生成需要大整数运算
function modPow(base, exponent, modulus) {
    let result = 1n;
    base = base % modulus;

    while (exponent > 0n) {
        if (exponent % 2n === 1n) {
            result = (result * base) % modulus;
        }
        exponent = exponent >> 1n;
        base = (base * base) % modulus;
    }

    return result;
}

// 计算 2^1000 mod 997
const result = modPow(2n, 1000n, 997n);
console.log(result);  // 816n
```

**场景 3: 精确的数学计算**

```javascript
// 阶乘计算
function factorial(n) {
    let result = 1n;
    for (let i = 2n; i <= n; i++) {
        result *= i;
    }
    return result;
}

console.log(factorial(30n));
// 265252859812191058636308480000000n

// 用 Number 计算会溢出
function factorialNumber(n) {
    let result = 1;
    for (let i = 2; i <= n; i++) {
        result *= i;
    }
    return result;
}

console.log(factorialNumber(30));
// 2.6525285981219103e+32 ❌ 精度丢失
```

**场景 4: 时间戳计算**

```javascript
// 纳秒级时间戳
const nowNanoseconds = BigInt(Date.now()) * 1000000n + BigInt(performance.now() * 1000000);
console.log(nowNanoseconds);
// 1704096000000000000n

// 计算时间差 (纳秒)
const start = process.hrtime.bigint();
// ... 执行一些操作
const end = process.hrtime.bigint();
const duration = end - start;
console.log(`执行时间: ${duration} 纳秒`);
```

---

## 你的 BigInt 笔记本

晚上八点, 你整理了今天的收获。

你在笔记本上写下标题: "BigInt —— 超越 2^53 的精确整数"

### 核心洞察 #1: Number 的精度限制

你写道:

"JavaScript 的 Number 类型基于 IEEE 754 双精度浮点数, 有明确的精度限制:

```javascript
// 安全整数范围
console.log(Number.MAX_SAFE_INTEGER);  // 9007199254740991 (2^53 - 1)
console.log(Number.MIN_SAFE_INTEGER);  // -9007199254740991 (-(2^53 - 1))

// 超过安全范围的整数无法精确表示
console.log(9007199254740992 + 1);  // 9007199254740992 ❌
console.log(9007199254740992 + 2);  // 9007199254740992 ❌
console.log(9007199254740992 + 3);  // 9007199254740994

// 小数精度问题
console.log(0.1 + 0.2);  // 0.30000000000000004
console.log(0.3 - 0.2);  // 0.09999999999999998
```

精度限制的根本原因:
- Number 使用 64 位存储: 1 位符号 + 11 位指数 + 52 位尾数
- 整数部分只有 53 位精度 (包含隐藏位)
- 超过 2^53 的整数会丢失精度
- 浮点数使用二进制表示, 无法精确表示十进制小数"

### 核心洞察 #2: BigInt 的创建和运算

"BigInt 提供任意精度的整数运算:

```javascript
// 创建 BigInt
const big1 = 9007199254740993n;  // 字面量语法 (推荐)
const big2 = BigInt(9007199254740993);  // 构造函数
const big3 = BigInt('9007199254740993');  // 从字符串创建

// 基本运算
console.log(100n + 50n);  // 150n
console.log(100n - 50n);  // 50n
console.log(100n * 2n);  // 200n
console.log(100n / 3n);  // 33n (整数除法, 舍弃小数)
console.log(100n % 3n);  // 1n
console.log(100n ** 2n);  // 10000n

// 位运算
console.log(5n & 3n);  // 1n (按位与)
console.log(5n | 3n);  // 7n (按位或)
console.log(5n ^ 3n);  // 6n (按位异或)
console.log(5n << 2n);  // 20n (左移)
console.log(20n >> 2n);  // 5n (右移)

// 一元运算
console.log(-100n);  // -100n
console.log(+100n);  // TypeError: Cannot convert a BigInt value to a number
```

BigInt 运算规则:
- 所有运算符两侧都必须是 BigInt
- 除法是整数除法, 直接舍弃小数
- 不支持一元加号 (+)
- 支持所有位运算符"

### 核心洞察 #3: BigInt 与 Number 的转换

"BigInt 和 Number 不能混用, 需要显式转换:

```javascript
const bigNum = 100n;
const normalNum = 50;

// ❌ 不能混合运算
try {
    console.log(bigNum + normalNum);  // TypeError
} catch (e) {
    console.error(e.message);
}

// ✅ 显式转换 Number → BigInt
console.log(bigNum + BigInt(normalNum));  // 150n

// ✅ 显式转换 BigInt → Number (危险!)
console.log(Number(bigNum) + normalNum);  // 150

// ⚠️ 超过安全范围会丢失精度
const huge = 9007199254740993n;
console.log(Number(huge));  // 9007199254740992 ❌

// 比较运算
console.log(100n === 100);  // false (类型不同)
console.log(100n == 100);  // true (值相同)
console.log(100n > 99);  // true (类型转换)
console.log(100n < 101);  // true

// 类型检查
console.log(typeof 100n);  // 'bigint'
console.log(100n instanceof BigInt);  // false
```

转换注意事项:
- Number → BigInt: 安全, 但会丢失小数部分
- BigInt → Number: 危险, 超过 2^53 会丢失精度
- 相等比较: === 检查类型, == 允许类型转换
- 大小比较: 允许类型转换"

### 核心洞察 #4: BigInt 的限制和陷阱

"BigInt 有多个使用限制:

```javascript
// 陷阱 1: JSON 序列化失败
const order = { orderId: 9007199254740993n };
try {
    JSON.stringify(order);  // TypeError
} catch (e) {
    console.error(e.message);
}

// 解决方案: 转换为字符串
BigInt.prototype.toJSON = function() {
    return this.toString();
};
JSON.stringify(order);  // '{"orderId":"9007199254740993"}'

// 陷阱 2: Math 函数不支持 BigInt
try {
    Math.max(100n, 200n);  // TypeError
} catch (e) {
    console.error(e.message);
}

// 解决方案: 自己实现
function maxBigInt(...values) {
    return values.reduce((max, val) => val > max ? val : max);
}
console.log(maxBigInt(100n, 200n, 150n));  // 200n

// 陷阱 3: 除法行为不同
console.log(10 / 3);  // 3.3333333333333335 (浮点数)
console.log(10n / 3n);  // 3n (整数, 舍弃小数)

// 陷阱 4: 不支持小数
try {
    BigInt(3.14);  // RangeError
} catch (e) {
    console.error(e.message);
}

// 陷阱 5: 数组方法需要注意
const arr = [1, 2n, 3];
arr.sort();  // [1, 2n, 3] (混合类型可以排序)

arr.reduce((sum, val) => sum + val, 0);  // TypeError (混合运算)
arr.reduce((sum, val) => sum + val, 0n);  // TypeError (Number 加 BigInt)
```

主要限制:
- JSON.stringify 不支持 (需要自定义 toJSON)
- Math 函数不支持 (需要自己实现)
- 除法是整数除法 (舍弃小数)
- 不支持小数输入
- 不能与 Number 混合运算"

你合上笔记本, 关掉电脑。

"今天终于理解了 BigInt 的价值, " 你想, "JavaScript 的 Number 类型虽然灵活, 但在处理大整数时有明确的精度限制。BigInt 提供了任意精度的整数运算, 是处理数据库ID、加密计算、精确数学运算的正确选择。理解 Number 和 BigInt 的区别, 才能在需要精确整数的场景中避免精度丢失的陷阱。"

---

## 知识总结

**规则 1: Number 的精度限制**

JavaScript 的 Number 类型基于 IEEE 754 双精度浮点数:

```javascript
// 安全整数范围
console.log(Number.MAX_SAFE_INTEGER);  // 9007199254740991 (2^53 - 1)
console.log(Number.MIN_SAFE_INTEGER);  // -9007199254740991

// 超过安全范围的整数无法精确表示
console.log(9007199254740991 + 1);  // 9007199254740992 ✓
console.log(9007199254740992 + 1);  // 9007199254740992 ❌ 应该是 993!
console.log(9007199254740993 + 1);  // 9007199254740994 ✓

// 检查安全性
console.log(Number.isSafeInteger(9007199254740991));  // true
console.log(Number.isSafeInteger(9007199254740992));  // false
console.log(Number.isSafeInteger(9007199254740993));  // false

// 浮点数精度问题
console.log(0.1 + 0.2);  // 0.30000000000000004
console.log(0.1 + 0.2 === 0.3);  // false
console.log(0.3 - 0.2);  // 0.09999999999999998
```

精度限制原因:
- Number 使用 64 位存储: 1 位符号 + 11 位指数 + 52 位尾数
- 整数精度: 53 位 (包含隐藏位), 即 -2^53 到 2^53
- 超过 2^53 的整数会发生舍入, 无法精确表示
- 浮点数使用二进制表示, 无法精确表示大部分十进制小数

---

**规则 2: BigInt 的创建和基本运算**

BigInt 提供任意精度的整数运算:

```javascript
// 创建 BigInt
const big1 = 9007199254740993n;  // 字面量语法 (推荐)
const big2 = BigInt(9007199254740993);  // 构造函数
const big3 = BigInt('9007199254740993');  // 从字符串创建
const big4 = BigInt('0x1FFFFFFFFFFFFF1');  // 从十六进制创建

// 不能从小数创建
try {
    BigInt(3.14);  // RangeError: The number 3.14 cannot be converted to a BigInt
} catch (e) {
    console.error(e.message);
}

// 基本算术运算
console.log(100n + 50n);  // 150n
console.log(100n - 50n);  // 50n
console.log(100n * 2n);  // 200n
console.log(100n / 3n);  // 33n (整数除法, 舍弃小数)
console.log(100n % 3n);  // 1n
console.log(2n ** 100n);  // 1267650600228229401496703205376n

// 位运算
console.log(5n & 3n);  // 1n (按位与)
console.log(5n | 3n);  // 7n (按位或)
console.log(5n ^ 3n);  // 6n (按位异或)
console.log(~5n);  // -6n (按位非)
console.log(5n << 2n);  // 20n (左移)
console.log(20n >> 2n);  // 5n (算术右移)

// 一元运算
console.log(-100n);  // -100n (取负)
console.log(+100n);  // TypeError: Cannot convert a BigInt value to a number
```

BigInt 运算规则:
- 所有运算符两侧都必须是 BigInt (不能混用 Number)
- 除法是整数除法, 直接舍弃小数部分 (不是四舍五入)
- 不支持一元加号 (+), 会抛出 TypeError
- 支持所有位运算符
- 可以表示任意大的整数, 不受 2^53 限制

---

**规则 3: BigInt 与 Number 的转换和比较**

BigInt 和 Number 是独立类型, 不能混用:

```javascript
const bigNum = 100n;
const normalNum = 50;

// ❌ 不能混合运算
try {
    console.log(bigNum + normalNum);  // TypeError: Cannot mix BigInt and other types
    console.log(bigNum * normalNum);  // TypeError
    console.log(Math.max(bigNum, normalNum));  // TypeError
} catch (e) {
    console.error(e.message);
}

// ✅ Number → BigInt (安全)
console.log(bigNum + BigInt(normalNum));  // 150n
console.log(BigInt(123.99));  // 123n (舍弃小数)

// ✅ BigInt → Number (危险! 可能丢失精度)
console.log(Number(bigNum) + normalNum);  // 150
console.log(Number(100n));  // 100

// ⚠️ 超过安全范围会丢失精度
const huge = 9007199254740993n;
console.log(Number(huge));  // 9007199254740992 ❌ 精度丢失

// 比较运算
console.log(100n === 100);  // false (严格相等: 类型不同)
console.log(100n == 100);  // true (宽松相等: 值相同)
console.log(100n === BigInt(100));  // true (类型和值都相同)

// 大小比较 (允许类型转换)
console.log(100n > 99);  // true
console.log(100n < 101);  // true
console.log(50n >= 50);  // true

// 类型检查
console.log(typeof 100n);  // 'bigint'
console.log(100n instanceof BigInt);  // false (BigInt 不是构造函数)

// 数组排序 (混合类型)
const mixed = [5n, 2, 8n, 1, 10n];
mixed.sort((a, b) => Number(a) - Number(b));
console.log(mixed);  // [1, 2, 5n, 8n, 10n]
```

转换和比较规则:
- **Number → BigInt**: 安全, 但会丢失小数部分 (直接舍弃)
- **BigInt → Number**: 危险, 超过 2^53 会丢失精度
- **严格相等 (===)**: 类型不同返回 false
- **宽松相等 (==)**: 允许类型转换, 比较数值
- **大小比较**: 允许类型转换, 可以混合比较
- **typeof**: 返回 'bigint'

---

**规则 4: BigInt 的序列化和JSON处理**

BigInt 不能直接被 JSON 序列化:

```javascript
const order = {
    orderId: 9007199254740993n,
    userId: 12345,
    amount: 299.99
};

// ❌ 直接序列化失败
try {
    JSON.stringify(order);
    // TypeError: Do not know how to serialize a BigInt
} catch (e) {
    console.error(e.message);
}

// ✅ 解决方案 1: 自定义 toJSON 方法
BigInt.prototype.toJSON = function() {
    return this.toString();
};

console.log(JSON.stringify(order));
// '{"orderId":"9007199254740993","userId":12345,"amount":299.99}'

// ✅ 解决方案 2: 使用 replacer 函数
const json = JSON.stringify(order, (key, value) => {
    return typeof value === 'bigint' ? value.toString() : value;
});
console.log(json);
// '{"orderId":"9007199254740993","userId":12345,"amount":299.99}'

// ✅ 解决方案 3: 手动转换
const serializable = {
    ...order,
    orderId: order.orderId.toString()
};
console.log(JSON.stringify(serializable));

// 反序列化: 需要手动转换回 BigInt
const parsed = JSON.parse(json);
const orderWithBigInt = {
    ...parsed,
    orderId: BigInt(parsed.orderId)
};
console.log(orderWithBigInt.orderId);  // 9007199254740993n
```

JSON 处理最佳实践:
- API 返回时将 BigInt 转换为字符串
- 前端接收后根据需要转换回 BigInt
- 数据库存储时使用字符串或 BIGINT 类型
- 避免在 JSON 中直接传输 BigInt

---

**规则 5: BigInt 的限制和陷阱**

BigInt 有多个使用限制:

```javascript
// 限制 1: Math 函数不支持
try {
    Math.max(100n, 200n);  // TypeError
    Math.sqrt(100n);  // TypeError
    Math.abs(-100n);  // TypeError
} catch (e) {
    console.error(e.message);
}

// 解决方案: 自己实现
function maxBigInt(...values) {
    return values.reduce((max, val) => val > max ? val : max);
}

function absBigInt(value) {
    return value < 0n ? -value : value;
}

// 限制 2: 除法是整数除法
console.log(10 / 3);  // 3.3333333333333335 (Number: 浮点数)
console.log(10n / 3n);  // 3n (BigInt: 整数, 舍弃小数)
console.log(10n / 4n);  // 2n (不是四舍五入)
console.log(11n / 4n);  // 2n

// 限制 3: 不能与数组方法直接配合
const numbers = [1n, 2n, 3n, 4n, 5n];

// ❌ reduce 需要初始值类型匹配
try {
    numbers.reduce((sum, val) => sum + val, 0);  // TypeError
} catch (e) {
    console.error(e.message);
}

// ✅ 初始值也必须是 BigInt
const sum = numbers.reduce((sum, val) => sum + val, 0n);
console.log(sum);  // 15n

// 限制 4: 不支持小数
try {
    const decimal = 3.14n;  // SyntaxError
    BigInt(3.14);  // RangeError
} catch (e) {
    console.error(e.message);
}

// 限制 5: 不支持一元加号
try {
    const positive = +100n;  // TypeError
} catch (e) {
    console.error(e.message);
}

// 限制 6: 数组 indexOf 和 includes 使用严格相等
const arr = [1n, 2n, 3n];
console.log(arr.indexOf(2));  // -1 (严格相等, 类型不匹配)
console.log(arr.includes(2));  // false
console.log(arr.indexOf(2n));  // 1 ✓
console.log(arr.includes(2n));  // true ✓
```

主要限制:
- **Math 函数**: 不支持 BigInt, 需要自己实现
- **除法**: 整数除法, 直接舍弃小数 (不是四舍五入)
- **数组方法**: 初始值类型必须匹配
- **小数**: 不支持小数字面量和小数输入
- **一元加号**: 抛出 TypeError
- **JSON**: 需要手动序列化和反序列化
- **数组查找**: 使用严格相等 (===)

---

**规则 6: BigInt 的实际应用场景**

BigInt 的主要应用场景:

**场景 1: 数据库主键和雪花ID**

```javascript
// Twitter 雪花算法生成的ID (64位)
const snowflakeId = 1234567890123456789n;

// 数据库操作 (存储为字符串或 BIGINT)
await db.query(
    'INSERT INTO users (id, name) VALUES (?, ?)',
    [snowflakeId.toString(), 'Alice']
);

// API 返回 (转换为字符串)
app.get('/api/user/:id', async (req, res) => {
    const userId = BigInt(req.params.id);
    const user = await db.findUser(userId.toString());
    res.json({
        userId: userId.toString(),  // 字符串形式返回
        name: user.name
    });
});

// 前端处理
const response = await fetch('/api/user/1234567890123456789');
const user = await response.json();
const userId = BigInt(user.userId);  // 转换回 BigInt
```

**场景 2: 加密和哈希计算**

```javascript
// RSA 密钥生成中的大整数运算
function modPow(base, exponent, modulus) {
    let result = 1n;
    base = base % modulus;

    while (exponent > 0n) {
        if (exponent % 2n === 1n) {
            result = (result * base) % modulus;
        }
        exponent = exponent >> 1n;
        base = (base * base) % modulus;
    }

    return result;
}

// 计算 2^1000 mod 997 (RSA中常见的模幂运算)
const result = modPow(2n, 1000n, 997n);
console.log(result);  // 816n

// 大整数乘法 (密码学中常用)
const p = 32416190071n;
const q = 32416189979n;
const n = p * q;  // RSA模数
console.log(n);  // 1050808632188764909n
```

**场景 3: 精确的数学计算**

```javascript
// 阶乘计算 (Number 会溢出)
function factorial(n) {
    if (n === 0n || n === 1n) return 1n;
    let result = 1n;
    for (let i = 2n; i <= n; i++) {
        result *= i;
    }
    return result;
}

console.log(factorial(30n));
// 265252859812191058636308480000000n

// 用 Number 计算会丢失精度
function factorialNumber(n) {
    let result = 1;
    for (let i = 2; i <= n; i++) {
        result *= i;
    }
    return result;
}

console.log(factorialNumber(30));
// 2.6525285981219103e+32 ❌ 精度丢失

// 斐波那契数列 (大数)
function fibonacci(n) {
    if (n <= 1n) return n;
    let a = 0n, b = 1n;
    for (let i = 2n; i <= n; i++) {
        [a, b] = [b, a + b];
    }
    return b;
}

console.log(fibonacci(100n));
// 354224848179261915075n
```

**场景 4: 时间戳和纳秒计算**

```javascript
// 纳秒级时间戳 (超过 Number 精度)
const nowNanoseconds = BigInt(Date.now()) * 1000000n;
console.log(nowNanoseconds);
// 1704096000000000000n

// Node.js 高精度时间
const start = process.hrtime.bigint();
// ... 执行一些操作
const end = process.hrtime.bigint();
const durationNs = end - start;
console.log(`执行时间: ${durationNs} 纳秒`);
console.log(`执行时间: ${Number(durationNs) / 1000000} 毫秒`);

// 微秒级定时器
function delayMicroseconds(us) {
    const start = process.hrtime.bigint();
    const target = start + BigInt(us) * 1000n;
    while (process.hrtime.bigint() < target) {
        // 忙等待
    }
}

delayMicroseconds(100);  // 延迟 100 微秒
```

**场景 5: 金额计算 (整数运算避免精度问题)**

```javascript
// ❌ 直接用浮点数 (精度问题)
const price1 = 0.1;
const price2 = 0.2;
console.log(price1 + price2);  // 0.30000000000000004

// ✅ 用整数 (以分为单位)
const priceCents1 = 10n;  // 0.1元 = 10分
const priceCents2 = 20n;  // 0.2元 = 20分
const totalCents = priceCents1 + priceCents2;
console.log(Number(totalCents) / 100);  // 0.3

// 完整的金额类
class Money {
    constructor(cents) {
        this.cents = BigInt(cents);
    }

    add(other) {
        return new Money(this.cents + other.cents);
    }

    multiply(factor) {
        return new Money(this.cents * BigInt(factor));
    }

    toString() {
        return `${Number(this.cents) / 100} 元`;
    }
}

const amount1 = new Money(10);  // 0.1元
const amount2 = new Money(20);  // 0.2元
const total = amount1.add(amount2);
console.log(total.toString());  // '0.3 元'
```

---

**事故档案编号**: MODULE-2024-1911
**影响范围**: BigInt, Number 精度, 大整数运算, JSON 序列化, 数据库ID
**根本原因**: 不理解 JavaScript Number 的精度限制 (2^53), 导致大整数精度丢失
**修复成本**: 中 (需要修改数据库schema、API序列化、前端处理)

这是 JavaScript 世界第 111 次被记录的模块系统事故。JavaScript 的 Number 类型基于 IEEE 754 双精度浮点数, 整数精度限制在 2^53 - 1 (9007199254740991)。超过这个范围的整数无法精确表示, 会发生舍入错误。BigInt 是 ES2020 引入的新类型, 提供任意精度的整数运算, 不受 2^53 限制。BigInt 和 Number 不能混用, 需要显式转换。BigInt 不支持 JSON 序列化, 需要转换为字符串。BigInt 的除法是整数除法, 直接舍弃小数。主要应用场景: 数据库雪花ID、加密计算、精确数学运算、纳秒时间戳、金额整数计算。理解 Number 和 BigInt 的区别是避免大整数精度丢失的关键。

---

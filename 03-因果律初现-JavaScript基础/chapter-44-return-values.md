《第44次记录:返回值事故 —— 函数的输出与副作用》

---

## 事故现场

周三下午,数据分析部门发来紧急消息:"导出的报表数据都是undefined,客户在等。"

你打开报表生成系统,找到数据处理函数:

```javascript
function calculateTotal(orders) {
    let total = 0
    orders.forEach(order => {
        total += order.amount
    })
    console.log('总金额:', total)
}

const orders = [
    { id: 1, amount: 100 },
    { id: 2, amount: 200 },
    { id: 3, amount: 300 }
]

const result = calculateTotal(orders)
console.log('返回值:', result)  // undefined
```

控制台输出"总金额: 600",但`result`是`undefined`。你盯着代码看了五秒钟,突然意识到——函数没有`return`语句!

你快速加上return:

```javascript
function calculateTotal(orders) {
    let total = 0
    orders.forEach(order => {
        total += order.amount
    })
    return total  // 加上return
}
```

但数据部门又发来消息:"折扣计算函数返回的好像不对,有时候是对象,有时候是数字。"你找到那个函数:

```javascript
function applyDiscount(price, discountRate) {
    if (discountRate > 1 || discountRate < 0) {
        console.log('折扣率无效')
        return  // 提前return,但没有返回值!
    }
    return price * discountRate
}

console.log(applyDiscount(100, 0.8))  // 80
console.log(applyDiscount(100, 1.5))  // undefined
```

无效折扣率时返回`undefined`,导致后续计算出错。

你的手机震动了——技术主管打来电话:"报表系统怎么回事?客户说数据乱七八糟的,有的是数字,有的显示undefined,有的根本不显示。"

窗外的天色已经暗了下来。办公室里只剩下你和几个加班的同事。你盯着屏幕上那些函数,手心开始冒汗。

---

## 深入迷雾

你创建了一个测试文件,决心搞清楚return的每一个细节。首先测试没有return的函数:

```javascript
function greet(name) {
    console.log('Hello, ' + name)
    // 没有return
}

const result = greet('Alice')
console.log('返回值:', result)  // undefined
```

没有return语句,函数返回`undefined`。"所有函数都有返回值,没写return就是undefined。"你写下笔记。

你测试提前return的场景:

```javascript
function validate(value) {
    if (!value) {
        console.log('值为空')
        return  // 提前返回,但没有值
    }

    if (value < 0) {
        return false  // 提前返回false
    }

    return true  // 正常返回true
}

console.log(validate(null))  // undefined
console.log(validate(-5))  // false
console.log(validate(10))  // true
```

"提前return可以减少嵌套,但要记得返回明确的值。"你明白了。

你想起报表系统需要返回多个值。你测试了返回对象:

```javascript
function getUserInfo(id) {
    return {
        id: id,
        name: 'Alice',
        age: 25,
        email: 'alice@example.com'
    }
}

const user = getUserInfo(1)
console.log(user.name, user.age)
```

返回对象可以包含多个字段。你还发现了解构赋值的便捷写法:

```javascript
function getCoordinates() {
    return { x: 100, y: 200 }
}

const { x, y } = getCoordinates()
console.log(x, y)  // 100 200
```

你还测试了返回数组:

```javascript
function getRange() {
    return [0, 100]
}

const [min, max] = getRange()
console.log(min, max)  // 0 100
```

你想起同事说过"纯函数"这个概念。你测试了纯函数和有副作用的函数:

```javascript
// 纯函数:无副作用
function add(a, b) {
    return a + b  // 只返回计算结果
}

console.log(add(2, 3))  // 5
console.log(add(2, 3))  // 5 - 相同输入,相同输出

// 有副作用:修改外部状态
let count = 0
function increment() {
    count++  // 修改外部变量
    return count
}

console.log(increment())  // 1
console.log(increment())  // 2 - 相同输入,不同输出!
```

"纯函数可预测,易测试,无副作用。"你明白了为什么要尽量使用纯函数——它们更可靠,更容易理解和维护。

你还发现了高阶函数——返回函数的函数:

```javascript
function createMultiplier(factor) {
    return function(number) {
        return number * factor
    }
}

const double = createMultiplier(2)
const triple = createMultiplier(3)

console.log(double(5))  // 10
console.log(triple(5))  // 15
```

"函数可以返回函数。"你感叹JavaScript的灵活性。

---

## 真相浮现

你整理了return语句和函数输出的最佳实践。

**问题代码:缺少return**

```javascript
// 危险:忘记return
function calculateTotal(items) {
    let sum = 0
    items.forEach(item => sum += item)
    // 忘记return!
}

const total = calculateTotal([1,2,3])
console.log(total)  // undefined

// 正确:明确return
function calculateTotal(items) {
    let sum = 0
    items.forEach(item => sum += item)
    return sum  // 返回计算结果
}
```

**提前return最佳实践**

```javascript
// 好:提前return,减少嵌套
function processOrder(order) {
    if (!order) return { success: false, error: 'Order is null' }
    if (!order.items) return { success: false, error: 'No items' }
    if (order.total <= 0) return { success: false, error: 'Invalid total' }

    // 主逻辑
    return { success: true, data: order }
}
```

**返回多个值**

```javascript
// 返回对象:适合命名字段
function getUserStats(id) {
    return {
        id: id,
        totalOrders: 10,
        totalSpent: 5000,
        level: 'VIP'
    }
}

const { totalOrders, level } = getUserStats(1)

// 返回数组:适合位置相关
function getRange() {
    return [0, 100]
}

const [min, max] = getRange()
```

你把报表系统的函数全部改成了纯函数:

```javascript
// 纯函数:无副作用
function calculateTotal(orders) {
    return orders.reduce((sum, order) => sum + order.amount, 0)
}

function applyDiscount(price, discountRate) {
    if (discountRate > 1 || discountRate < 0) {
        return { success: false, error: '折扣率无效' }
    }
    return { success: true, value: price * discountRate }
}

function generateReport(orders) {
    const total = calculateTotal(orders)
    const discountResult = applyDiscount(total, 0.9)

    if (!discountResult.success) {
        return { error: discountResult.error }
    }

    return {
        total: total,
        discounted: discountResult.value,
        count: orders.length
    }
}
```

测试通过。所有函数都有明确的返回值,报表数据正确无误。

---

## 世界法则

**世界规则 1:return返回值**

```javascript
function add(a, b) {
    return a + b  // 明确返回
}

function noReturn() {
    console.log('执行')
    // 没有return → 返回undefined
}
```

**世界规则 2:提前return**

```javascript
// 好:减少嵌套
function validate(data) {
    if (!data) return false
    if (data.length === 0) return false
    return true
}

// 差:嵌套过深
function validate(data) {
    if (data) {
        if (data.length > 0) {
            return true
        }
    }
    return false
}
```

**世界规则 3:返回多个值**

```javascript
// 对象:命名字段
function getUser() {
    return { name: 'Alice', age: 25 }
}

// 数组:位置相关
function getCoords() {
    return [100, 200]
}

const { name, age } = getUser()
const [x, y] = getCoords()
```

**世界规则 4:纯函数优先**

```javascript
// ✅ 纯函数:可预测,易测试
function add(a, b) {
    return a + b
}

// ❌ 副作用:不可预测
let count = 0
function increment() {
    count++
    return count
}
```

**世界规则 5:返回函数(高阶函数)**

```javascript
function createFormatter(prefix) {
    return function(text) {
        return prefix + text
    }
}

const addHello = createFormatter('Hello, ')
console.log(addHello('World'))  // "Hello, World"
```

---

**事故档案编号**:JS-2024-1644
**影响范围**:数据处理、可预测性、可测试性
**根本原因**:忘记return或不理解副作用的危害
**修复成本**:低(添加return,使用纯函数)

这是JavaScript世界第44次被记录的返回值事故。return明确函数输出,没有return返回undefined。提前return可减少嵌套,提高可读性。返回对象或数组可返回多个值,配合解构赋值更简洁。纯函数无副作用、可预测、易测试,优于有副作用的函数。高阶函数可返回函数,实现更灵活的抽象。理解返回值,就理解了JavaScript函数的输出机制和函数式编程理念。

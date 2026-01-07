《第46次记录:调试技巧事故 —— 追踪错误的艺术》

---

## 事故现场

周五晚上八点,你刚准备下班,手机突然响了。是技术主管的电话。

"生产环境出问题了。"他的声音很紧张,"购物车结算金额不对,用户投诉说价格计算错误,现在有几十个工单。必须立刻修复。"

你的心一沉。生产环境的bug,意味着真实用户正在受影响,每一分钟的延迟都可能造成经济损失和口碑伤害。

你快速打开电脑,找到购物车计算函数:

```javascript
function calculateTotal(items) {
    console.log("开始计算")
    let total = 0
    console.log("初始total:", total)
    for (let i = 0; i < items.length; i++) {
        console.log("处理商品", i)
        console.log("商品信息:", items[i])
        total += items[i].price * items[i].quantity
        console.log("当前total:", total)
        if (items[i].discount) {
            console.log("有折扣:", items[i].discount)
            total -= items[i].discount
            console.log("折扣后total:", total)
        }
    }
    console.log("最终total:", total)
    return total
}
```

代码里已经有一堆`console.log`了——这是之前调试时加的,但现在看起来完全找不到重点。你在测试环境运行这个函数,控制台被刷屏了,密密麻麻的输出让你眼花缭乱。

客服群又弹出消息:"用户说金额跳来跳去,有时对有时不对。"产品经理发来私信:"多久能修好?我要给客户一个答复。"

你盯着满屏的`console.log`,手心开始冒汗。这种盲目打日志的方式效率太低了,你需要更好的调试方法。

---

## 深入迷雾

你深吸一口气,决定换一种方式。你听说过`debugger`和Chrome DevTools,但从来没认真用过。现在是时候学了。

你在关键位置加了一行`debugger`:

```javascript
function calculateTotal(items) {
    let total = 0
    debugger  // 浏览器会在这里暂停
    for (let i = 0; i < items.length; i++) {
        total += items[i].price * items[i].quantity
        if (items[i].discount) {
            total -= items[i].discount
        }
    }
    return total
}
```

你刷新页面,浏览器立刻暂停了。DevTools自动打开,Sources面板显示代码停在`debugger`那一行。

右侧面板显示了大量信息:
- **Call Stack** (调用栈):显示函数调用链
- **Scope** (作用域):显示当前所有变量的值
- **Watch** (监视):可以添加表达式监视

你看到`items`数组的内容,`total`现在是0。你按下F10(Step Over),代码跳到下一行。你再按一次,进入循环。你看到`i`是0,`items[0]`的内容清晰可见。

"这比console.log清楚多了!"你继续按F10单步执行,观察每一步的变量变化。当执行到`total -= items[i].discount`时,你突然发现问题——`items[i].discount`是字符串`"50"`,不是数字!

```javascript
total = 100
items[i].discount = "50"
total -= "50"  // 100 - "50" = 50,但这里有类型转换!
```

你在Watch面板添加了表达式`typeof items[i].discount`,显示`"string"

`。"原来是类型错误!"你恍然大悟。

你测试了条件断点——在循环里的某一行右键,选择"Add conditional breakpoint",输入`i === 2`。现在调试器只在第3个商品时才暂停,大大提高了效率。

你还发现了`console.table()`:

```javascript
console.table(items)
```

控制台显示了一个格式清晰的表格,每个商品的字段一目了然,比`console.log`清楚太多了。

你学会了错误处理:

```javascript
function safeCalculate(items) {
    try {
        let total = 0
        for (let i = 0; i < items.length; i++) {
            const price = Number(items[i].price)
            const quantity = Number(items[i].quantity)
            const discount = Number(items[i].discount || 0)

            if (isNaN(price) || isNaN(quantity)) {
                throw new Error(`商品${i}的价格或数量无效`)
            }

            total += price * quantity - discount
        }
        return total
    } catch (err) {
        console.error('计算错误:', err.message)
        console.error('堆栈:', err.stack)
        return null  // 返回null表示计算失败
    }
}
```

"try-catch能捕获错误,防止程序崩溃。"你写下笔记。

---

## 真相浮现

你整理了有效的调试技巧和工具使用方法。

**问题代码:过度使用console.log**

```javascript
// 糟糕:满屏日志
function calculate(items) {
    console.log("开始")
    console.log("items:", items)
    let total = 0
    console.log("total:", total)
    for (let i = 0; i < items.length; i++) {
        console.log("i:", i)
        console.log("item:", items[i])
        total += items[i].price
        console.log("total now:", total)
    }
    console.log("结束")
    return total
}

// 好:使用debugger和DevTools
function calculate(items) {
    let total = 0
    debugger  // 暂停,查看所有变量
    for (let i = 0; i < items.length; i++) {
        total += items[i].price
    }
    return total
}
```

**有效的console方法**

```javascript
// 表格展示
console.table([
    { name: 'Alice', age: 25 },
    { name: 'Bob', age: 30 }
])

// 性能测试
console.time('operation')
expensiveFunction()
console.timeEnd('operation')  // "operation: 123.45ms"

// 分组
console.group('用户信息')
console.log('姓名:', user.name)
console.log('年龄:', user.age)
console.groupEnd()

// 样式
console.log('%c重要提示', 'color: red; font-size: 20px')
```

**debugger最佳实践**

```javascript
function processData(data) {
    // 在关键位置添加debugger
    debugger  // F10单步执行,F11进入函数,Shift+F11跳出

    const result = data.map(item => {
        // 条件断点:在DevTools中设置
        // 例如只在item.price > 100时暂停
        return item.price * 1.1
    })

    return result
}
```

你把购物车计算函数完全重写了:

```javascript
function calculateTotal(items) {
    try {
        let total = 0

        for (let i = 0; i < items.length; i++) {
            const item = items[i]

            // 类型转换和验证
            const price = Number(item.price)
            const quantity = Number(item.quantity)
            const discount = Number(item.discount || 0)

            // 数据验证
            if (isNaN(price) || price < 0) {
                throw new Error(`商品${i}价格无效: ${item.price}`)
            }
            if (isNaN(quantity) || quantity <= 0) {
                throw new Error(`商品${i}数量无效: ${item.quantity}`)
            }
            if (isNaN(discount) || discount < 0) {
                throw new Error(`商品${i}折扣无效: ${item.discount}`)
            }

            total += price * quantity - discount
        }

        return total
    } catch (err) {
        console.error('[购物车] 计算错误:', err.message)
        console.error('[购物车] 堆栈:', err.stack)
        return null
    }
}
```

测试通过。所有类型错误都被捕获和修复,计算结果正确无误。

---

## 世界法则

**世界规则 1:console方法大全**

```javascript
// 基础输出
console.log('普通')     // 普通日志
console.warn('警告')    // 黄色警告
console.error('错误')   // 红色错误

// 格式化输出
console.table(arrayOfObjects)  // 表格展示
console.log('%c样式', 'color: red')  // 样式

// 性能测试
console.time('名称')
// 代码
console.timeEnd('名称')  // 输出耗时

// 分组
console.group('组名')
console.log('内容')
console.groupEnd()
```

**世界规则 2:debugger与单步调试**

```javascript
function debug() {
    const x = 10
    debugger  // 浏览器暂停在这里
    const y = x * 2
    return y
}

// DevTools快捷键
// F8: 继续执行
// F10: Step Over (跳过函数)
// F11: Step Into (进入函数)
// Shift+F11: Step Out (跳出函数)
```

**世界规则 3:断点类型**

```javascript
// 1. 代码断点
debugger

// 2. 条件断点(在DevTools中设置)
// 只在i===50时暂停

// 3. DOM断点
// 元素修改/属性修改/节点删除时暂停

// 4. XHR断点
// 特定URL请求时暂停

// 5. 事件监听断点
// 特定事件触发时暂停
```

**世界规则 4:错误处理**

```javascript
try {
    riskyOperation()
} catch (err) {
    console.error('错误:', err.message)
    console.error('类型:', err.name)
    console.error('堆栈:', err.stack)
} finally {
    cleanup()  // 总是执行
}

// 自定义错误
throw new Error('自定义错误信息')
```

**世界规则 5:系统化调试流程**

```javascript
// 1. 复现问题
// 2. 理解错误信息
// 3. 添加断点
// 4. 单步执行
// 5. 检查变量
// 6. 验证假设
// 7. 修复问题
// 8. 测试验证

// ❌ 避免
// - 随机修改代码
// - 忽略错误信息
// - 过度依赖console.log
// - 不测试修复结果
```

---

**事故档案编号**:JS-2024-1646
**影响范围**:开发效率、错误定位、生产环境稳定性
**根本原因**:不熟悉调试工具,依赖低效的console.log
**修复成本**:低(学习DevTools,建立系统化调试流程)

这是JavaScript世界第46次被记录的调试技巧事故。console提供多种输出方法——log/warn/error用于基础输出,table用于数据展示,time用于性能测试。debugger语句暂停执行,配合DevTools的单步调试(F10/F11)可精确追踪问题。断点有代码、条件、DOM、XHR、事件等类型。try-catch捕获错误并提供错误信息(message/name/stack)。系统化调试流程:复现→理解→断点→单步→检查→验证→修复→测试。Chrome DevTools提供Sources/Console/Network/Performance等强大工具。理解调试技巧,就理解了JavaScript开发者如何高效定位和解决问题,从低效的日志输出进化到专业的系统化调试。

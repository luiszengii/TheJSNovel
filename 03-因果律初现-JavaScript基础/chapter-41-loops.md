《第41次记录:循环控制事故 —— 重复执行的节奏》

---

## 事故现场

周四下午两点,你点击了"开始导入"按钮,然后整个浏览器标签页就卡住了。

进度条停在3%,再也没动过。页面标题旁边出现了那个令人不安的符号——一个旋转的小圆圈。你等了三十秒,一分钟,两分钟...页面完全无响应,鼠标点击任何地方都没反应。

"又崩了?"旁边的同事看了一眼你的屏幕,"批量导入功能?"你点点头,按下F5强制刷新页面。Chrome弹出警告:"该页面无响应,是否等待?"

数据部门的主管发来消息:"客户的5000条数据什么时候能导入完?他们在等。"你看了一眼时间,已经是第三次尝试了。

你打开Chrome DevTools,切到Console标签,屏幕上密密麻麻全是输出:

```
处理中: 第42条
处理中: 第42条
处理中: 第42条
处理中: 第42条
```

同一条数据,输出了上百遍!你的心跳加快了——无限循环。

你快速打开代码文件,找到批量导入的函数:

```javascript
function importData(dataList) {
    let index = 0
    while (index < dataList.length) {
        console.log('处理中: 第' + index + '条')
        processItem(dataList[index])
        // ...其他逻辑
    }
    console.log('导入完成')
}
```

代码看起来很正常,但你盯着看了五秒钟,手掌突然握紧了鼠标——这个while循环里没有`index++`!循环变量永远不会增加,条件永远为真,循环永远不会结束。

窗外传来救护车的鸣笛声。你的电脑风扇开始呼呼作响,CPU占用率飙到100%。

---

## 深入迷雾

你强制关闭了浏览器标签页,创建了一个测试文件来理解循环的运作机制。首先测试最基本的for循环:

```javascript
console.log('for循环:')
for (let i = 0; i < 3; i++) {
    console.log('  i =', i)
}
console.log('循环结束')
```

输出正常:`i = 0`、`i = 1`、`i = 2`,然后结束。"for循环有三个部分:初始化、条件、更新。"你写下笔记。

你复现那个无限循环的bug:

```javascript
let index = 0
while (index < 3) {
    console.log('index =', index)
    // 忘记index++!
}
```

你刚按下回车,控制台就开始疯狂输出`index = 0`。你快速按下Ctrl+C终止脚本。"while循环里必须手动更新条件,否则永远不会结束。"

你想起还有do-while循环:

```javascript
let count = 0
do {
    console.log('count =', count)
    count++
} while (count < 3)
```

输出了三次,但你注意到一个关键区别——即使条件一开始就为假,do-while也会至少执行一次:

```javascript
do {
    console.log('至少执行一次')
} while (false)
// 输出: "至少执行一次"
```

你测试了break和continue:

```javascript
for (let i = 0; i < 10; i++) {
    if (i === 5) {
        console.log('遇到5,break退出')
        break
    }
    if (i % 2 === 0) {
        continue  // 跳过偶数
    }
    console.log('i =', i)
}
```

输出了`1`、`3`,然后显示"遇到5,break退出"。"break彻底退出循环,continue只是跳过当次。"你明白了。

你还发现了for-of和for-in的区别:

```javascript
const users = ['Alice', 'Bob', 'Charlie']

console.log('for-of遍历值:')
for (const name of users) {
    console.log('  ', name)  // Alice, Bob, Charlie
}

console.log('for-in遍历索引:')
for (const index in users) {
    console.log('  ', index)  // "0", "1", "2"
}
```

for-of遍历数组元素,for-in遍历索引(而且是字符串!)。你还测试了数组方法:

```javascript
users.forEach((name, index) => {
    console.log(index, name)
})
```

"forEach更简洁,而且不会出现忘记更新索引的问题。"你若有所思。

---

## 真相浮现

你整理了循环控制的所有形式和规则。

**问题代码:忘记更新循环变量**

```javascript
// 危险:无限循环
let index = 0
while (index < data.length) {
    process(data[index])
    // 忘记index++!
}

// 正确:确保循环会结束
let index = 0
while (index < data.length) {
    process(data[index])
    index++  // 更新变量
}
```

**三种基本循环**

```javascript
// for: 已知次数,结构清晰
for (let i = 0; i < 5; i++) {
    console.log(i)
}

// while: 未知次数,先判断后执行
let count = 0
while (count < 5) {
    console.log(count)
    count++  // 必须更新!
}

// do-while: 至少执行一次
do {
    console.log('至少执行一次')
} while (condition)
```

**控制语句**

```javascript
// break: 退出循环
for (let i = 0; i < 10; i++) {
    if (i === 5) break  // 循环到此结束
}

// continue: 跳过当次,继续下次
for (let i = 0; i < 10; i++) {
    if (i % 2 === 0) continue  // 跳过偶数
    console.log(i)  // 只输出奇数
}
```

你把批量导入功能改成了这样:

```javascript
function importData(dataList) {
    for (let i = 0; i < dataList.length; i++) {
        console.log(`处理中: 第${i+1}/${dataList.length}条`)
        processItem(dataList[i])
    }
    console.log('导入完成')
}
```

使用for循环,结构更清晰,也不会忘记更新索引。测试通过,5000条数据顺利导入。

---

## 世界法则

**世界规则 1:for循环结构**

```javascript
for (初始化; 条件; 更新) {
    // 循环体
}

// 三个部分都是可选的,但分号不能省
for (let i = 0; i < 5; i++) {
    console.log(i)
}
```

**世界规则 2:while vs do-while**

```javascript
// while: 先判断,可能不执行
while (condition) {
    // 必须有让condition变false的逻辑
}

// do-while: 先执行,至少一次
do {
    // 至少执行一次
} while (condition)
```

**世界规则 3:break vs continue**

```javascript
// break: 退出整个循环
for (let i = 0; i < 10; i++) {
    if (i === 5) break  // 到5就结束
}

// continue: 跳过当次,继续下次
for (let i = 0; i < 10; i++) {
    if (i % 2 === 0) continue  // 跳过偶数
    console.log(i)  // 1, 3, 5, 7, 9
}
```

**世界规则 4:遍历数组**

```javascript
const arr = [10, 20, 30]

// for-of: 遍历值
for (const value of arr) {
    console.log(value)  // 10, 20, 30
}

// for-in: 遍历索引(不推荐用于数组)
for (const index in arr) {
    console.log(index)  // "0", "1", "2" (字符串)
}

// forEach: 最常用
arr.forEach((value, index) => {
    console.log(index, value)
})
```

**世界规则 5:避免无限循环**

```javascript
// ❌ 危险
let i = 0
while (i < 10) {
    console.log(i)
    // 忘记i++,无限循环!
}

// ✅ 安全
let i = 0
while (i < 10) {
    console.log(i)
    i++  // 确保条件会变false
}

// ✅ 更安全: 用for循环
for (let i = 0; i < 10; i++) {
    console.log(i)
}
```

---

**事故档案编号**:JS-2024-1641
**影响范围**:批量处理、数组遍历、系统性能
**根本原因**:忘记更新循环变量导致无限循环
**修复成本**:低(添加更新语句,改用for循环)

这是JavaScript世界第41次被记录的循环控制事故。for循环用于已知次数(初始化+条件+更新),while用于未知次数(需手动更新变量),do-while至少执行一次。break退出整个循环,continue跳过当次。for-of遍历值,forEach最常用。始终确保循环有结束条件,避免无限循环。理解循环控制,就理解了JavaScript如何有节奏地重复执行代码。

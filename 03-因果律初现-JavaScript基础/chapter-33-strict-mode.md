《第33次记录:严格模式事故 —— 规则的强制执行》

---

## 事故现场

周五下午四点,你正准备提交代码下班,QA发来一条消息:"用户反馈表单提交后数据丢失。"

你打开测试页面,填写表单,点击提交——数据确实丢了。你打开控制台,没有报错。你检查代码,表单验证函数看起来正常:

```javascript
function validateForm() {
    usrName = document.getElementById('username').value
    if (usrName === '') {
        alert('请输入用户名')
        return false
    }
    return true
}
```

你测试了几次,发现一个诡异的现象:第一次提交失败,第二次却成功了。你在函数开头加了`console.log(usrName)`,输出显示第一次是`undefined`,第二次才有值。

"怎么会这样?"你盯着代码看了五分钟,突然注意到第二行:`usrName = ...`——你忘记加`let`了。

这意味着什么?你打开浏览器控制台,输入`window.usrName`,显示了用户名。"天啊,我创建了一个全局变量。"第一次调用时`usrName`还不存在,所以是`undefined`;第二次调用时全局变量已经存在了,所以有值。

但JavaScript为什么不报错?这是个明显的错误——未声明的变量赋值,却被默默地创建成了全局变量。

你的同事路过,看了一眼你的屏幕:"加个`'use strict'`试试。"

你在文件开头加了一行`'use strict'`,刷新页面,控制台立刻报错:`Uncaught ReferenceError: usrName is not defined`

"这才对啊!"你松了口气,但也困惑:"严格模式到底改变了什么?"

---

## 深入迷雾

你创建了一个测试文件,开始探索严格模式的效果。首先测试变量声明:

```javascript
// 不加严格模式
function test1() {
    x = 10
    console.log(x)  // 10,自动创建全局变量
}
test1()
console.log(window.x)  // 10,全局变量被污染

// 加严格模式
function test2() {
    'use strict'
    y = 20
    console.log(y)
}
test2()  // ReferenceError: y is not defined
```

严格模式强制要求变量声明。你松了口气,但随即想到:还有哪些隐藏的坑?

你测试了删除属性:

```javascript
const obj = {}
Object.defineProperty(obj, 'id', {
    value: 123,
    configurable: false  // 不可配置
})

// 普通模式
delete obj.id  // 返回false,但不报错
console.log(obj.id)  // 123,还在

// 严格模式
'use strict'
delete obj.id  // TypeError: Cannot delete property 'id'
```

普通模式静默失败,严格模式明确报错。"这才是正确的行为。"你想。

你测试了`this`绑定:

```javascript
// 普通模式
function showThis() {
    console.log(this)  // Window对象
}
showThis()

// 严格模式
function showThisStrict() {
    'use strict'
    console.log(this)  // undefined
}
showThisStrict()
```

普通函数调用时,普通模式的`this`指向全局对象,严格模式是`undefined`。你想起之前踩过的坑:在普通模式下,你以为`this.something`会报错,结果默默在window上创建了属性。

你还发现了更多限制。重复参数名:

```javascript
// 普通模式:允许
function sum(a, a, c) {
    return a + a + c  // 第二个a覆盖第一个
}

// 严格模式:语法错误
'use strict'
function sumStrict(a, a, c) {  // SyntaxError
    return a + a + c
}
```

八进制字面量:

```javascript
// 普通模式
const num = 010  // 8

// 严格模式
'use strict'
const num = 010  // SyntaxError
```

你靠在椅背上,终于明白了。JavaScript的普通模式太"宽容"了,很多错误都被默默忽略。严格模式把这些错误暴露出来,强制你写更安全的代码。

---

## 真相浮现

你整理了测试代码,总结了严格模式的关键改变。

**问题代码:隐式全局变量**

```javascript
function validate() {
    userName = getValue()  // 忘记let,创建全局变量
    return userName !== ''
}

// 普通模式:成功,但污染全局
// 严格模式:ReferenceError
```

**启用严格模式**

```javascript
// 方式1:全局严格
'use strict'

// 方式2:函数严格
function test() {
    'use strict'
    // 函数内严格模式
}

// 方式3:ES6模块自动严格
// .mjs或type="module"
```

**关键变化:this绑定**

```javascript
// 普通模式
function test() {
    console.log(this)  // Window
}

// 严格模式
function test() {
    'use strict'
    console.log(this)  // undefined
}
```

**关键变化:静默失败变显式错误**

```javascript
'use strict'

const obj = {}
Object.defineProperty(obj, 'x', { value: 1, writable: false })

obj.x = 2  // TypeError: Cannot assign to read only property
delete obj.x  // TypeError: Cannot delete property
```

你把表单验证函数改成了这样:

```javascript
'use strict'

function validateForm() {
    const userName = document.getElementById('username').value
    if (userName === '') {
        alert('请输入用户名')
        return false
    }
    return true
}
```

重新测试,一切正常。严格模式暴露了错误,你修复了bug。

---

## 世界法则

**世界规则 1:启用严格模式**

```javascript
// 全局严格
'use strict'

// 函数严格
function test() {
    'use strict'
}

// ES6模块自动严格
```

**世界规则 2:变量声明强制**

```javascript
'use strict'

x = 10  // ReferenceError: x is not defined
let y = 20  // 正确
```

**世界规则 3:this绑定差异**

```javascript
// 普通模式:this默认为Window
// 严格模式:this为undefined

'use strict'
function test() {
    console.log(this)  // undefined
}
```

**世界规则 4:静默失败变显式错误**

```javascript
'use strict'

// 删除不可配置属性
delete obj.id  // TypeError

// 修改只读属性
obj.name = "new"  // TypeError

// 扩展不可扩展对象
Object.preventExtensions(obj)
obj.newProp = "value"  // TypeError
```

**世界规则 5:禁止的语法**

```javascript
'use strict'

const num = 010  // SyntaxError: 八进制
with (obj) {}    // SyntaxError: with语句
function f(a,a) {}  // SyntaxError: 重复参数
```

---

**事故档案编号**:JS-2024-1633
**影响范围**:代码质量、错误检测、调试效率
**根本原因**:普通模式的静默失败隐藏了潜在错误
**修复成本**:低(添加'use strict',修复报错)

这是JavaScript世界第33次被记录的严格模式事故。严格模式是JavaScript的"安全模式",将静默失败转为显式错误——未声明变量报错,修改只读属性报错,删除不可配置属性报错。它禁止了危险的语法,改变了this绑定规则,隔离了eval作用域。理解严格模式,就理解了JavaScript如何通过强制规则来预防错误和提升代码质量。

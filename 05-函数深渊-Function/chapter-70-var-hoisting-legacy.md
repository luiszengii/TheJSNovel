《第70次记录：var的遗留事故 —— 函数级作用域的幽灵》

---

## 简单修改

周三下午三点,你接手了一个老项目的维护工作。项目是两年前的代码,用的还是ES5风格,到处都是`var`声明。技术负责人说:"很简单的一个需求,用户权限检查模块加一个状态验证,半小时就能搞定。"

你打开`auth.js`文件,看到了熟悉的老式代码风格:

```javascript
// auth.js - 用户权限检查模块(老代码,ES5风格)
function checkUserPermission(userId) {
    if (!userId) {
        console.log('用户ID不能为空');
        return false;
    }

    // 查询用户信息
    var user = getUserFromDatabase(userId);
    if (!user) {
        console.log('用户不存在');
        return false;
    }

    // 检查权限
    var hasPermission = checkPermissionTable(user.role);
    return hasPermission;
}
```

需求很简单:在检查权限之前,先验证用户账号状态,如果账号被禁用就直接返回false。你快速加了几行代码:

```javascript
function checkUserPermission(userId) {
    if (!userId) {
        console.log('用户ID不能为空');
        return false;
    }

    // 查询用户信息
    var user = getUserFromDatabase(userId);
    if (!user) {
        console.log('用户不存在');
        return false;
    }

    // 新增:检查账号状态
    if (user.status === 'disabled') {
        console.log('用户账号已被禁用,userId:', userId);
        var userId = user.id; // 保存完整的用户ID供日志记录
        logSecurityEvent('ACCESS_DENIED', userId);
        return false;
    }

    // 检查权限
    var hasPermission = checkPermissionTable(user.role);
    return hasPermission;
}
```

你看了看代码,觉得没问题。保存,提交,推送到测试环境。"半小时搞定。"你满意地点点头,准备继续下一个任务。

十分钟后,QA同事小李在群里@你:"你的代码在测试环境报错了,'userId is not defined',是不是漏了什么?"

你愣了一下:"不可能啊,userId是函数参数,怎么会undefined?"你打开测试环境的日志:

```
[ERROR] ReferenceError: Cannot access 'userId' before initialization
    at checkUserPermission (auth.js:18)
    at Object.<anonymous> (test.js:45)
```

"行18...那是我新加的代码。"你皱起眉头。明明`userId`是函数参数,为什么会'before initialization'?你明明在函数开头就用了`userId`,没有报错啊。

---

## 测试失败

下午三点半,你在本地环境快速复现了问题:

```javascript
// 简化版复现
function testFunction(userId) {
    console.log('参数userId:', userId); // 这行正常

    if (true) {
        console.log('块内userId:', userId); // 这行报错!
        var userId = 'new-value';
    }
}

testFunction('user-123');
// 输出:
// 参数userId: user-123
// [ERROR] ReferenceError: Cannot access 'userId' before initialization
```

"什么?!"你盯着屏幕,完全困惑了。"第一行能正常打印userId,第二行在if块里就报错了?而且我明明在if块里重新声明了userId,为什么说'before initialization'?"

你尝试去掉if块里的`var`声明:

```javascript
function testFunction(userId) {
    console.log('参数userId:', userId); // 正常

    if (true) {
        console.log('块内userId:', userId); // 正常
    }
}

testFunction('user-123');
// 输出:
// 参数userId: user-123
// 块内userId: user-123
```

"不加var就没问题..."你若有所思。

然后你又尝试把if块去掉,直接在函数体里重复声明:

```javascript
function testFunction(userId) {
    console.log('第一次:', userId); // 正常

    var userId = 'new-value';
    console.log('第二次:', userId); // 正常,输出'new-value'
}

testFunction('user-123');
// 输出:
// 第一次: user-123
// 第二次: new-value
```

"直接在函数体里重复声明var没问题...所以问题出在if块里?"你开始意识到,这可能和作用域有关。

你决定用现代的调试手段,在Chrome DevTools里打断点:

```javascript
function checkUserPermission(userId) {
    debugger; // 断点1: 函数入口

    if (!userId) {
        return false;
    }

    var user = { status: 'disabled', id: 'user-456' };

    if (user.status === 'disabled') {
        debugger; // 断点2: 进入if块
        console.log('userId:', userId); // 这里报错
        var userId = user.id;
    }

    return true;
}

checkUserPermission('user-123');
```

在断点1,你检查作用域:`userId`的值是`'user-123'`,没问题。

但在断点2,当你尝试访问`userId`时,DevTools显示:`userId: <value unavailable>`。

"Value unavailable?"你困惑地看着调试器。"参数明明在外层作用域,为什么在if块里变成不可用了?"

---

## 定位原因

下午四点,你决定系统地研究这个问题。首先,你查了MDN关于`var`的文档,看到了一个关键词:**提升(Hoisting)**。

"var声明会被提升到函数作用域顶部..."你读着文档,突然灵光一闪。"等等,`var userId`在if块里声明,会被提升到整个函数的顶部,覆盖了参数`userId`?"

你立刻写了个验证代码:

```javascript
// 原始代码
function checkUserPermission(userId) {
    console.log('1. 参数:', userId);

    if (true) {
        console.log('2. 块内(声明前):', userId); // 报错行
        var userId = 'new-value';
        console.log('3. 块内(声明后):', userId);
    }

    console.log('4. 块外:', userId);
}

// JavaScript引擎实际理解的代码(提升后)
function checkUserPermission(userId) {
    var userId; // var声明提升到函数顶部,覆盖了参数!

    console.log('1. 参数:', userId); // undefined(已被提升的var覆盖)

    if (true) {
        console.log('2. 块内(声明前):', userId); // undefined
        userId = 'new-value'; // 赋值保留在原位置
        console.log('3. 块内(声明后):', userId); // 'new-value'
    }

    console.log('4. 块外:', userId); // 'new-value'
}
```

"原来如此!"你恍然大悟。"if块里的`var userId`声明被提升到函数顶部,创建了一个新的函数级变量`userId`,遮蔽了参数`userId`。而在赋值之前访问这个变量,它的值是undefined。"

但等等,你想起刚才的报错信息是'Cannot access before initialization',不是undefined。你又仔细看了遍代码和错误信息。

"不对,我记错了。"你重新运行测试,发现错误信息其实是在测试环境(用了Babel转译)产生的。在纯ES5环境里,不会报错,只是undefined。

你尝试用`let`替代`var`:

```javascript
function checkUserPermission(userId) {
    console.log('1. 参数:', userId); // 正常: 'user-123'

    if (true) {
        console.log('2. 块内(声明前):', userId); // ReferenceError!
        let userId = 'new-value';
        console.log('3. 块内(声明后):', userId);
    }
}

checkUserPermission('user-123');
```

"用let就真的报错了!因为let有暂时性死区(Temporal Dead Zone)。"你记起了这个概念。

你画了个对比图:

```
var的提升行为:

function test(param) {          function test(param) {
    console.log(param);    →         var param; // 提升,覆盖参数
                                      console.log(param); // undefined
    if (true) {
        var param = 'new';            if (true) {
    }                                     param = 'new'; // 赋值保留
}                                     }
                                 }


let的块级作用域:

function test(param) {          function test(param) {
    console.log(param);    →         console.log(param); // 正常

    if (true) {                       if (true) {
        let param = 'new';                // TDZ开始
    }                                     let param = 'new'; // 新作用域
}                                     }
                                 }
```

---

## var机制

下午五点,你整理了关于var、let、const的核心知识,写进了笔记:

**规则 1: var的提升机制(Hoisting)**

`var`声明会被提升到函数作用域(或全局作用域)的顶部,但赋值保留在原位置。

```javascript
// 代码写法
function example() {
    console.log(x); // undefined (不报错!)
    var x = 10;
    console.log(x); // 10
}

// 引擎实际执行(提升后)
function example() {
    var x; // 声明提升到顶部,初始值undefined
    console.log(x); // undefined
    x = 10; // 赋值保留在原位置
    console.log(x); // 10
}
```

**关键点**:
- 声明提升,赋值不提升
- 提升到函数作用域顶部,不是块作用域
- 访问未赋值的var变量,结果是undefined,不报错

---

**规则 2: var的函数作用域**

`var`声明的变量限制在函数作用域内,不是块级作用域:

```javascript
function testScope() {
    if (true) {
        var x = 10; // var声明,函数作用域
    }
    console.log(x); // 10 - 可以访问!(不在if块内也能访问)

    for (var i = 0; i < 3; i++) {
        var y = i; // var声明,函数作用域
    }
    console.log(i); // 3 - 循环变量泄露到外部
    console.log(y); // 2 - 循环内变量泄露到外部
}

// 对比let/const的块级作用域
function testBlockScope() {
    if (true) {
        let x = 10; // 块级作用域
    }
    console.log(x); // ReferenceError: x is not defined

    for (let i = 0; i < 3; i++) {
        let y = i;
    }
    console.log(i); // ReferenceError: i is not defined
    console.log(y); // ReferenceError: y is not defined
}
```

**作用域对比**:
- `var`: 函数作用域或全局作用域
- `let`/`const`: 块级作用域(花括号`{}`包围的区域)

---

**规则 3: var的重复声明**

`var`允许在同一作用域内重复声明同一个变量,后者不会报错:

```javascript
function testRedeclare() {
    var x = 10;
    console.log(x); // 10

    var x = 20; // 不报错,只是重新赋值
    console.log(x); // 20

    var x; // 不报错,也不改变值
    console.log(x); // 20 (没有赋值,保持原值)
}

// 对比let/const
function testLetRedeclare() {
    let x = 10;
    let x = 20; // SyntaxError: Identifier 'x' has already been declared
}
```

**风险**:重复声明容易导致意外覆盖,难以发现bug。

---

**规则 4: 暂时性死区(Temporal Dead Zone, TDZ)**

`let`和`const`有暂时性死区——在块级作用域内,变量声明之前不能访问:

```javascript
function testTDZ() {
    // TDZ开始
    console.log(x); // ReferenceError: Cannot access 'x' before initialization
    let x = 10; // TDZ结束
    console.log(x); // 10
}

// 嵌套作用域的TDZ
function testNestedTDZ(param) {
    console.log(param); // 正常访问外层参数

    if (true) {
        // TDZ开始:这个块内重新声明了param
        console.log(param); // ReferenceError! 访问的是块内的param,但还未初始化
        let param = 'new'; // TDZ结束
        console.log(param); // 'new'
    }

    console.log(param); // 外层参数,正常
}
```

**TDZ的意义**:
- 强制在声明之前不能使用变量
- 避免var的提升带来的困惑
- 让代码更符合直觉

---

**规则 5: 全局作用域的差异**

在全局作用域,`var`会创建全局对象的属性,`let`/`const`不会:

```javascript
// 浏览器环境
var globalVar = 'var';
let globalLet = 'let';
const globalConst = 'const';

console.log(window.globalVar); // 'var' - var创建了window属性
console.log(window.globalLet); // undefined - let不创建window属性
console.log(window.globalConst); // undefined - const不创建window属性

// 都可以直接访问
console.log(globalVar); // 'var'
console.log(globalLet); // 'let'
console.log(globalConst); // 'const'
```

**风险**:
- `var`污染全局对象(window/global)
- 可能意外覆盖内置属性
- `let`/`const`更安全,不污染全局对象

---

**规则 6: 迁移指南:从var到let/const**

现代JavaScript开发应避免使用`var`,迁移步骤:

**步骤1: 识别var的使用场景**

```javascript
// 场景1: 循环变量
for (var i = 0; i < 10; i++) {
    // ...
}
// ✓ 改为let
for (let i = 0; i < 10; i++) {
    // ...
}

// 场景2: 条件声明
if (condition) {
    var temp = getValue();
    process(temp);
}
// ✓ 改为let或const
if (condition) {
    const temp = getValue(); // 如果不需要重新赋值
    process(temp);
}

// 场景3: 函数内变量
function example() {
    var result = compute();
    return result;
}
// ✓ 改为const(如果不需要重新赋值)
function example() {
    const result = compute();
    return result;
}
```

**步骤2: 处理提升依赖**

```javascript
// 老代码依赖提升
function oldCode() {
    console.log(x); // undefined
    var x = 10;
}

// 修复方式1: 调整代码顺序
function newCode1() {
    let x = 10;
    console.log(x); // 10
}

// 修复方式2: 保留提升行为(如果确实需要)
function newCode2() {
    let x; // 显式声明在前
    console.log(x); // undefined
    x = 10;
}
```

**步骤3: 选择let还是const**

```javascript
// 规则:默认用const,需要重新赋值才用let

// ✓ 好习惯
const userName = getUserName(); // 不需要修改,用const
let counter = 0; // 需要递增,用let

// ✗ 不推荐
let userName = getUserName(); // 如果不会重新赋值,应该用const
var counter = 0; // 不要再用var
```

**步骤4: ESLint规则**

```json
{
  "rules": {
    "no-var": "error",
    "prefer-const": "warn"
  }
}
```

**完整迁移示例**:

```javascript
// 老代码(ES5风格)
function processUsers() {
    var users = getUsers();

    for (var i = 0; i < users.length; i++) {
        var user = users[i];
        if (user.active) {
            var result = processUser(user);
            logResult(result);
        }
    }

    console.log('处理完成,共' + i + '个用户'); // 依赖循环变量泄露
}

// 新代码(ES6+风格)
function processUsers() {
    const users = getUsers(); // 不修改,用const

    for (let i = 0; i < users.length; i++) { // 循环变量用let
        const user = users[i]; // 不修改,用const
        if (user.active) {
            const result = processUser(user); // 不修改,用const
            logResult(result);
        }
    }

    // 不能再访问i,需要单独计数
    console.log(`处理完成,共${users.length}个用户`);
}

// 更现代的写法
function processUsers() {
    const users = getUsers();
    const activeUsers = users.filter(user => user.active);

    activeUsers.forEach(user => {
        const result = processUser(user);
        logResult(result);
    });

    console.log(`处理完成,共${activeUsers.length}个用户`);
}
```

---

下午五点半,你把修复后的代码推送到测试环境:

```javascript
// 修复后的代码
function checkUserPermission(userId) {
    if (!userId) {
        console.log('用户ID不能为空');
        return false;
    }

    const user = getUserFromDatabase(userId); // var → const
    if (!user) {
        console.log('用户不存在');
        return false;
    }

    // 检查账号状态
    if (user.status === 'disabled') {
        console.log('用户账号已被禁用,userId:', userId);
        const fullUserId = user.id; // 重命名变量,避免遮蔽参数
        logSecurityEvent('ACCESS_DENIED', fullUserId);
        return false;
    }

    const hasPermission = checkPermissionTable(user.role); // var → const
    return hasPermission;
}
```

五分钟后,QA反馈:"测试通过!没问题了。"

你松了口气,但也意识到,这个"半小时的简单需求"因为一个var的陷阱,花了整整两个半小时。

"老代码迁移真是步步惊心。"你在笔记本上记录下这次教训,"以后接手老项目,第一件事就是开启ESLint的`no-var`规则,避免再踩这个坑。"

---

**事故档案编号**: FUNC-2024-1870
**影响范围**: var提升,函数作用域,块级作用域,暂时性死区
**根本原因**: 不理解var的提升机制和函数作用域,在块内重复声明var导致遮蔽外层变量
**修复成本**: 低(改用let/const),但需要理解作用域机制,全局迁移需要谨慎测试

这是JavaScript世界第70次被记录的var遗留事故。var是JavaScript早期的变量声明方式,有三大特性:声明提升(hoisting)、函数作用域、允许重复声明。这些特性在现代开发中容易导致bug:提升让变量在声明前可访问(值为undefined),函数作用域让块内变量泄露到外部,重复声明容易意外覆盖。ES6引入的let和const解决了这些问题:块级作用域、暂时性死区(TDZ)防止声明前访问、不允许重复声明。现代JavaScript开发应完全避免使用var,默认使用const,需要重新赋值时使用let。理解var的历史遗留问题,是维护老代码和编写健壮代码的基础。

---

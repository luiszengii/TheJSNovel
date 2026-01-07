《第40次记录:条件判断事故 —— 分支的抉择》

---

## 事故现场

周一早上九点,你刚打开电脑,就看到客服群里炸开了锅。

"紧急！有用户反馈说普通用户能看到管理员菜单。""安全漏洞吗?""我这边也有好几个类似投诉。"消息一条接一条刷屏。你的手机也开始震动——技术主管打来电话:"权限系统出问题了,立刻排查。"

你的心一沉。权限系统是核心模块,如果真有漏洞,后果不堪设想。你快速登录测试账号,用普通用户身份进入系统。

页面正常显示,看起来没什么问题。但当你点击用户中心时,屏幕上出现了不该出现的东西——"用户管理"、"系统配置"、"数据导出"——这些都是管理员才能看到的功能!

"怎么会这样..."你喃喃道,立刻打开代码仓库,找到权限验证的代码:

```javascript
function checkPermission(user) {
    if (user.role === 'admin')
        showAdminMenu()
        enableAdminFeatures()
    console.log('权限检查完成')
}
```

代码看起来很简单,逻辑清晰。但你盯着看了十秒钟,突然意识到一个可怕的事实——这个if语句没有花括号!

你快速在控制台测试:

```javascript
const normalUser = { role: 'user' }
checkPermission(normalUser)
```

控制台输出"权限检查完成",但管理员菜单依然显示出来了。你的额头开始冒汗。

客服群又弹出消息:"客户说要投诉到监管部门,这是严重的数据安全问题。"技术主管又发来消息:"多久能修复?"

你盯着那行代码,手指悬在键盘上方。问题找到了,但你需要搞清楚为什么会出错。

---

## 深入迷雾

你创建了一个测试文件,决心搞清楚条件判断的每一个细节。首先复现那个bug:

```javascript
function test1(user) {
    if (user.role === 'admin')
        console.log('显示管理员菜单')
        console.log('启用管理员功能')  // 这行总是执行!
}

test1({ role: 'user' })
```

两行都输出了。"原来如此!"你明白了——没有花括号时,if只控制紧跟的第一行语句。第二行`console.log`不属于if,会无条件执行。

你加上花括号再测试:

```javascript
function test2(user) {
    if (user.role === 'admin') {
        console.log('显示管理员菜单')
        console.log('启用管理员功能')
    }
}

test2({ role: 'user' })
```

这次什么都没输出。"花括号才能包含多条语句。"你写下笔记。

你想起还有else if的场景。你测试了成绩评级:

```javascript
function getGrade(score) {
    if (score >= 90) {
        return '优秀'
    } else if (score >= 60) {
        return '及格'
    } else {
        return '不及格'
    }
}

console.log(getGrade(85))  // "及格"
console.log(getGrade(45))  // "不及格"
```

if-else链从上到下检查,匹配第一个为真的条件。你想到权限系统还用了switch:

```javascript
function getDayType(day) {
    switch (day) {
        case 1:
        case 2:
        case 3:
        case 4:
        case 5:
            return '工作日'
        case 6:
        case 7:
            return '周末'
    }
}

console.log(getDayType(3))  // "工作日"
```

多个case可以共享同一个处理逻辑。但你想起之前踩过的坑——忘记break:

```javascript
function testSwitch(value) {
    let result = ''
    switch (value) {
        case 1:
            result += 'case 1, '
        case 2:
            result += 'case 2, '
            break
    }
    return result
}

console.log(testSwitch(1))  // "case 1, case 2, "
```

没有break,代码会"穿透"到下一个case!你还发现switch使用严格匹配:

```javascript
const num = '1'
switch (num) {
    case 1:
        console.log('数字1')
        break
    case '1':
        console.log('字符串1')
        break
}
// 输出: "字符串1"
```

switch使用`===`比较,类型不同不会匹配。你靠在椅背上,整理思路。条件判断有三种形式——if用于简单分支,switch用于多分支(要记得break),三元运算符用于简单赋值。花括号虽然可选,但为了安全必须加。

---

## 真相浮现

你整理了条件判断的规则和常见陷阱。

**问题代码:缺少花括号**

```javascript
// 危险:只有第一行属于if
if (user.role === 'admin')
    showAdminMenu()
    enableAdminFeatures()  // 总是执行!

// 安全:花括号包含所有语句
if (user.role === 'admin') {
    showAdminMenu()
    enableAdminFeatures()
}
```

**if-else链**

```javascript
if (score >= 90) {
    console.log('优秀')
} else if (score >= 60) {
    console.log('及格')
} else {
    console.log('不及格')
}
```

**switch结构**

```javascript
// 需要break防穿透
switch (status) {
    case 'pending':
        showPending()
        break  // 必须!
    case 'approved':
    case 'completed':  // 多个case共享逻辑
        showSuccess()
        break
    default:
        showError()
}

// switch使用===严格匹配
switch ('1') {
    case 1:  // 不匹配
        break
    case '1':  // 匹配
        break
}
```

你把权限验证系统改成了这样:

```javascript
function checkPermission(user) {
    if (user.role === 'admin') {
        showAdminMenu()
        enableAdminFeatures()
    } else if (user.role === 'moderator') {
        showModeratorMenu()
    } else {
        showUserMenu()
    }
    console.log('权限检查完成')
}
```

重新测试,普通用户只能看到普通菜单了。

---

## 世界法则

**世界规则 1:始终使用花括号**

```javascript
// ❌ 危险:容易出错
if (condition)
    statement1
    statement2  // 不属于if!

// ✅ 安全:清晰明确
if (condition) {
    statement1
    statement2
}
```

**世界规则 2:if-else链**

```javascript
if (condition1) {
    // 分支1
} else if (condition2) {
    // 分支2
} else {
    // 默认分支
}

// 从上到下检查,匹配第一个为真的条件
```

**世界规则 3:switch结构**

```javascript
switch (value) {
    case 1:
        // 处理
        break  // 必须break!
    case 2:
    case 3:
        // 多个case共享逻辑
        break
    default:
        // 默认处理
}

// 使用===严格匹配
// 忘记break会穿透到下一个case
```

**世界规则 4:三元运算符**

```javascript
// 简单赋值
const type = age >= 18 ? '成年' : '未成年'

// 嵌套(不推荐,可读性差)
const level = score >= 90 ? '优秀' : score >= 60 ? '及格' : '不及格'

// 推荐:复杂逻辑用if-else
```

**世界规则 5:短路求值**

```javascript
// && : 左为假,不求右
obj && obj.method()  // obj存在才调用

// || : 左为真,不求右
const name = user.name || '匿名'  // 提供默认值
```

---

**事故档案编号**:JS-2024-1640
**影响范围**:程序逻辑、权限验证、分支执行
**根本原因**:忘记花括号导致多条语句意外执行
**修复成本**:低(添加花括号和break)

这是JavaScript世界第40次被记录的条件判断事故。if-else用于分支逻辑,switch用于多分支匹配(需break防穿透,使用===严格匹配),三元运算符用于简单赋值。始终使用花括号包裹条件语句块,避免意外执行。理解条件判断,就理解了JavaScript如何根据条件选择不同的执行路径。

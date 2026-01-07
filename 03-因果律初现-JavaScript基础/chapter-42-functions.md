《第 42 次记录：函数封装事故 —— 代码复用的封装陷阱与参数传递迷局》

## 重复代码的噩梦

周五上午 10 点 23 分，产品经理在 Slack 上 @了你："登录成功提示要加用户名，格式改成 '欢迎回来，{用户名}！登录成功'。下午 3 点客户要演示，务必完成。"

"小改动，很快。" 你回复。你按下 Cmd+Shift+F，在整个项目中搜索 "登录成功" —— VSCode 显示 **37 处匹配结果**。

"37 处？！" 你的手指停在键盘上。你打开第一个文件 `auth.js`，看到了这样的代码：

```javascript
// 首页登录逻辑
if (response.status === 200) {
    console.log('登录成功');
    showNotification('登录成功');
    trackEvent('user_login', '登录成功');
    updateUserStatus('登录成功');
}

// 商品页登录逻辑
if (loginFromProduct) {
    console.log('登录成功');
    showNotification('登录成功');
    trackEvent('user_login', '登录成功');
    updateUserStatus('登录成功');
}

// 购物车登录逻辑
if (loginFromCart) {
    console.log('登录成功');
    showNotification('登录成功');
    trackEvent('user_login', '登录成功');
    updateUserStatus('登录成功');
}
```

完全相同的四行代码，在一个文件里就重复了三次。你皱了皱眉，打开第二个文件 `checkout.js`，第三个文件 `profile.js`... 到处都是这样的重复逻辑。

你开始手动修改第一处：

```javascript
console.log(`欢迎回来，${username}！登录成功`);
showNotification(`欢迎回来，${username}！登录成功`);
trackEvent('user_login', `欢迎回来，${username}！登录成功`);
updateUserStatus(`欢迎回来，${username}！登录成功`);
```

复制，粘贴，改字符串... 你的手指机械地重复着。十五分钟后，你改完了第 8 处，手指开始酸痛，眼睛开始干涩。你看了一眼进度 —— 还有 29 处没改。

同事老张路过，看了一眼你的屏幕："你在做什么？"

"改登录提示的文案。" 你疲惫地说。

"37 处都要手动改？" 老张皱眉，"为什么不写个函数？封装一次，到处调用。下次改文案只要改一个地方。"

你愣住了。"对啊... 为什么不用函数封装？"

但你的手已经改了 8 处。如果现在停下来写函数，这 8 处要重新改一遍。产品经理又发来消息："客户提前到了，2 点就要演示！"

你盯着屏幕，手指悬在键盘上方。继续手动改完剩下 29 处？还是停下来重构成函数？时间不够了...

## 函数的第一次尝试

你决定赌一把 —— 停下来写函数。你创建了一个新文件 `utils/auth.js`：

```javascript
function handleLoginSuccess(username) {
    const message = `欢迎回来，${username}！登录成功`;
    console.log(message);
    showNotification(message);
    trackEvent('user_login', message);
    updateUserStatus(message);
}
```

"就这样！" 你松了口气。你开始替换所有重复代码：

```javascript
// 之前：四行重复
console.log('登录成功');
showNotification('登录成功');
trackEvent('user_login', '登录成功');
updateUserStatus('登录成功');

// 现在：一行调用
handleLoginSuccess(currentUser.name);
```

你快速替换了 10 处、20 处、30 处... 进度条在你心中飞速上升。但在第 23 处时，你遇到了问题：

```javascript
// checkout.js
if (guestLogin) {
    handleLoginSuccess(username);  // 这里的 username 是 undefined！
}
```

控制台报错了：`欢迎回来，undefined！登录成功`。你检查代码，发现这个页面的用户名变量叫 `guestName`，不是 `username`。

"参数名不一致..." 你喃喃自语。你继续往下改，又发现了新问题：

```javascript
// profile.js
handleLoginSuccess();  // 忘记传参数了
// 输出："欢迎回来，undefined！登录成功"
```

还有的地方需要不同的提示：

```javascript
// admin.js
// 管理员登录要显示："管理员 {name} 登录成功"
// 但现在函数写死了格式
handleLoginSuccess('Admin');  // 输出："欢迎回来，Admin！登录成功" (错误)
```

你开始怀疑自己的设计。函数确实减少了重复，但参数处理、默认值、不同场景... 你意识到自己对函数的理解太浅了。

## 参数传递的陷阱

你打开一个测试文件，开始系统地研究函数参数。你写下最基本的测试：

```javascript
function test(a, b, c) {
    console.log('参数 a:', a);
    console.log('参数 b:', b);
    console.log('参数 c:', c);
}

console.log('=== 测试 1: 正常传参 ===');
test(1, 2, 3);
// 参数 a: 1
// 参数 b: 2
// 参数 c: 3

console.log('=== 测试 2: 参数不足 ===');
test(1, 2);
// 参数 a: 1
// 参数 b: 2
// 参数 c: undefined ← 缺失的参数是 undefined

console.log('=== 测试 3: 参数过多 ===');
test(1, 2, 3, 4, 5);
// 参数 a: 1
// 参数 b: 2
// 参数 c: 3
// 4 和 5 去哪了？被忽略了！
```

"参数少了是 undefined，多了被忽略。" 你记下笔记。这解释了为什么 `handleLoginSuccess()` 会输出 undefined。

你想起 ES6 有默认参数，于是改进了函数：

```javascript
function handleLoginSuccess(username = '游客') {
    const message = `欢迎回来，${username}！登录成功`;
    console.log(message);
    showNotification(message);
    trackEvent('user_login', message);
    updateUserStatus(message);
}

handleLoginSuccess();  // "欢迎回来，游客！登录成功" ← 有默认值了！
handleLoginSuccess('Alice');  // "欢迎回来，Alice！登录成功"
```

"默认参数解决了缺失参数的问题。" 但你又想到一个问题：如果需要传递可选的第二参数呢？

```javascript
function greet(name = '游客', greeting = 'Hello') {
    console.log(`${greeting}, ${name}!`);
}

greet();  // "Hello, 游客!"
greet('Alice');  // "Hello, Alice!"
greet('Bob', 'Hi');  // "Hi, Bob!"

// 但如果只想改 greeting，不改 name 呢？
greet(undefined, 'Hey');  // "Hey, 游客!" ← 必须传 undefined 占位
```

你测试了对象参数的方式：

```javascript
function greetWithOptions({ name = '游客', greeting = 'Hello' } = {}) {
    console.log(`${greeting}, ${name}!`);
}

greetWithOptions();  // "Hello, 游客!"
greetWithOptions({ name: 'Alice' });  // "Hello, Alice!"
greetWithOptions({ greeting: 'Hi' });  // "Hi, 游客!" ← 可以只传部分参数
greetWithOptions({ greeting: 'Hey', name: 'Bob' });  // "Hey, Bob!"
```

"对象参数更灵活，可以任意选择传哪些参数。" 你恍然大悟。

你继续测试剩余参数：

```javascript
function sum(...numbers) {
    console.log('numbers 是什么？', numbers);  // 是一个数组
    console.log('numbers 是数组吗？', Array.isArray(numbers));  // true

    let total = 0;
    for (let num of numbers) {
        total += num;
    }
    return total;
}

console.log(sum(1, 2, 3));  // numbers: [1, 2, 3], 返回: 6
console.log(sum(1, 2, 3, 4, 5));  // numbers: [1, 2, 3, 4, 5], 返回: 15
console.log(sum());  // numbers: [], 返回: 0
```

"剩余参数用 `...` 收集所有参数成数组，可以接收任意数量的参数。" 你写下笔记。

## 函数声明与表达式的区别

你想起老张说过函数有多种写法。你测试了函数声明和函数表达式：

```javascript
console.log('=== 测试函数声明提升 ===');

greet('Alice');  // "Hello, Alice" ← 在定义前调用成功了！

function greet(name) {
    console.log('Hello, ' + name);
}

console.log('=== 测试函数表达式提升 ===');

sayHi('Bob');  // TypeError: sayHi is not a function ← 报错了

const sayHi = function(name) {
    console.log('Hi, ' + name);
};
```

你困惑地检查报错信息。为什么 `greet` 可以在定义前调用，但 `sayHi` 不行？

你打开 Chrome DevTools，设置断点调试：

```javascript
console.log('1. 脚本开始执行');
console.log('sayHi 是什么？', typeof sayHi);  // "undefined"

greet('Test');  // 成功！函数已存在

function greet(name) {
    console.log('Hello, ' + name);
}

console.log('2. 到达 sayHi 定义之前');
console.log('sayHi 是什么？', typeof sayHi);  // "undefined"

const sayHi = function(name) {
    console.log('Hi, ' + name);
};

console.log('3. 到达 sayHi 定义之后');
console.log('sayHi 是什么？', typeof sayHi);  // "function"
```

输出让你看清了真相：

```
1. 脚本开始执行
sayHi 是什么？ undefined
Hello, Test
2. 到达 sayHi 定义之前
sayHi 是什么？ undefined
3. 到达 sayHi 定义之后
sayHi 是什么？ function
```

"函数声明会提升到作用域顶部，整个函数定义都提升了。但函数表达式只提升变量声明（const sayHi），赋值在原位置。" 你终于明白了。

你测试了更复杂的情况：

```javascript
console.log('=== 测试条件中的函数声明 ===');

if (true) {
    function test() {
        console.log('函数 1');
    }
}

test();  // 在某些环境下可能报错，在某些环境下输出 "函数 1"
// 原因：函数声明在块级作用域中的行为不一致

console.log('=== 测试条件中的函数表达式 ===');

if (true) {
    const test2 = function() {
        console.log('函数 2');
    };
}

test2();  // ReferenceError: test2 is not defined
// 原因：const 是块级作用域，test2 在 if 块外不可见
```

"函数声明在块中可能有兼容性问题，函数表达式更安全。" 你记下这个陷阱。

## 箭头函数的简洁与陷阱

你看到代码库里有很多箭头函数，决定深入研究：

```javascript
console.log('=== 箭头函数的不同形式 ===');

// 完整形式
const add1 = (a, b) => {
    return a + b;
};
console.log(add1(1, 2));  // 3

// 简化：单个表达式，省略 return 和花括号
const add2 = (a, b) => a + b;
console.log(add2(1, 2));  // 3

// 简化：单个参数，省略括号
const double = x => x * 2;
console.log(double(5));  // 10

// 错误：没有参数必须保留括号
const greet = () => console.log('Hello');
greet();  // "Hello"

// 陷阱：返回对象字面量必须加括号
const createUser1 = name => { name: name };  // ❌ 错误！被当成代码块
console.log(createUser1('Alice'));  // undefined

const createUser2 = name => ({ name: name });  // ✅ 正确
console.log(createUser2('Alice'));  // { name: 'Alice' }
```

你发现了一个隐藏的陷阱 —— 返回对象字面量时，花括号会被当成代码块而不是对象，必须用括号包裹。

你继续测试箭头函数在数组方法中的应用：

```javascript
const numbers = [1, 2, 3, 4, 5];

// 传统写法
const doubled1 = numbers.map(function(x) {
    return x * 2;
});
console.log(doubled1);  // [2, 4, 6, 8, 10]

// 箭头函数写法
const doubled2 = numbers.map(x => x * 2);
console.log(doubled2);  // [2, 4, 6, 8, 10]

// 更复杂的操作
const users = [
    { name: 'Alice', age: 25 },
    { name: 'Bob', age: 30 },
    { name: 'Charlie', age: 35 }
];

// 筛选年龄 >= 30 的用户
const adults = users.filter(user => user.age >= 30);
console.log(adults);  // [{ name: 'Bob', age: 30 }, { name: 'Charlie', age: 35 }]

// 提取所有名字
const names = users.map(user => user.name);
console.log(names);  // ['Alice', 'Bob', 'Charlie']

// 链式调用
const result = users
    .filter(user => user.age >= 30)
    .map(user => user.name)
    .join(', ');
console.log(result);  // "Bob, Charlie"
```

"箭头函数在数组方法中特别简洁。" 你对这种写法越来越熟悉。

## return 语句的细节

你测试了 return 语句的各种情况：

```javascript
console.log('=== 测试 return 基本行为 ===');

function add(a, b) {
    return a + b;
    console.log('这行永远不会执行');  // ← return 后的代码不执行
}
console.log(add(1, 2));  // 3

console.log('=== 测试没有 return ===');

function noReturn() {
    console.log('执行了');
}
const result = noReturn();  // "执行了"
console.log('返回值:', result);  // undefined ← 没有 return 返回 undefined

console.log('=== 测试空 return ===');

function emptyReturn() {
    console.log('执行了');
    return;  // 空 return
    console.log('这行不会执行');
}
const result2 = emptyReturn();  // "执行了"
console.log('返回值:', result2);  // undefined

console.log('=== 测试提前 return ===');

function checkAge(age) {
    if (age < 18) {
        return '未成年';  // 提前返回
    }

    if (age < 60) {
        return '成年';  // 提前返回
    }

    return '老年';  // 最后的返回
}

console.log(checkAge(15));  // "未成年"
console.log(checkAge(30));  // "成年"
console.log(checkAge(70));  // "老年"
```

你发现了 `return` 的自动分号插入陷阱：

```javascript
console.log('=== return 自动分号插入陷阱 ===');

function createUser1() {
    return  // ← 这里自动插入了分号！
    {
        name: 'Alice',
        age: 25
    };
}
console.log(createUser1());  // undefined ← 返回 undefined 而非对象

function createUser2() {
    return {  // ✅ 正确：花括号和 return 在同一行
        name: 'Alice',
        age: 25
    };
}
console.log(createUser2());  // { name: 'Alice', age: 25 }
```

"return 后换行会自动插入分号，导致返回 undefined！" 你把这个陷阱标记为重点。

## 函数作为一等公民

你测试了函数作为值的特性：

```javascript
console.log('=== 函数赋值给变量 ===');

const greet = function(name) {
    console.log(`Hello, ${name}!`);
};

greet('Alice');  // "Hello, Alice!"

console.log('=== 函数作为参数传递 ===');

function execute(callback) {
    console.log('准备执行回调...');
    callback();
    console.log('回调执行完毕');
}

execute(function() {
    console.log('我是回调函数');
});
// 输出：
// "准备执行回调..."
// "我是回调函数"
// "回调执行完毕"

console.log('=== 函数作为返回值 ===');

function createMultiplier(factor) {
    return function(num) {
        return num * factor;
    };
}

const double = createMultiplier(2);
const triple = createMultiplier(3);

console.log(double(5));  // 10
console.log(triple(5));  // 15
console.log(double(10));  // 20
console.log(triple(10));  // 30
```

你意识到 `createMultiplier` 每次调用都返回一个新函数，这个新函数 "记住" 了 `factor` 的值。"这就是闭包吗？" 你想起之前听说过这个概念。

你测试了数组中存储函数：

```javascript
console.log('=== 函数存储在数组中 ===');

const operations = [
    x => x + 1,
    x => x * 2,
    x => x - 3,
    x => x / 4
];

let value = 10;
console.log('初始值:', value);  // 10

for (let operation of operations) {
    value = operation(value);
    console.log('当前值:', value);
}
// 输出：
// 初始值: 10
// 当前值: 11  (10 + 1)
// 当前值: 22  (11 * 2)
// 当前值: 19  (22 - 3)
// 当前值: 4.75  (19 / 4)
```

你还测试了对象中存储函数：

```javascript
console.log('=== 函数作为对象方法 ===');

const calculator = {
    value: 0,

    add: function(num) {
        this.value += num;
        return this;  // 返回 this 支持链式调用
    },

    subtract(num) {  // ES6 简写语法
        this.value -= num;
        return this;
    },

    multiply: num => {  // ❌ 箭头函数没有自己的 this
        this.value *= num;  // 这里的 this 不是 calculator
        return this;
    },

    getResult() {
        return this.value;
    }
};

calculator.add(10).subtract(3);
console.log(calculator.getResult());  // 7

calculator.multiply(2);  // 箭头函数的 this 有问题
console.log(calculator.getResult());  // 预期 14，实际可能不是
```

你发现箭头函数在对象方法中有陷阱 —— 它没有自己的 `this`。

## 参数传递：值传递的真相

你想起之前对引用类型的困惑，决定测试函数参数传递：

```javascript
console.log('=== 基本类型参数传递 ===');

function changeNumber(num) {
    console.log('函数内修改前:', num);  // 10
    num = 100;
    console.log('函数内修改后:', num);  // 100
}

let x = 10;
changeNumber(x);
console.log('函数外的 x:', x);  // 10 ← x 没有变化

console.log('=== 对象参数传递 ===');

function changeObject(obj) {
    console.log('函数内修改前:', obj);  // { count: 0 }
    obj.count = 100;  // 修改对象属性
    console.log('函数内修改后:', obj);  // { count: 100 }
}

let myObj = { count: 0 };
changeObject(myObj);
console.log('函数外的 myObj:', myObj);  // { count: 100 } ← myObj 被修改了！

console.log('=== 重新赋值对象参数 ===');

function replaceObject(obj) {
    console.log('函数内修改前:', obj);  // { count: 0 }
    obj = { count: 999 };  // 重新赋值
    console.log('函数内修改后:', obj);  // { count: 999 }
}

let myObj2 = { count: 0 };
replaceObject(myObj2);
console.log('函数外的 myObj2:', myObj2);  // { count: 0 } ← myObj2 没有变化
```

你终于理解了参数传递的本质：

- 基本类型：传递值的副本，修改不影响原变量
- 引用类型：传递引用的副本，通过引用修改对象会影响原对象
- 重新赋值参数：不会影响原变量，因为只是改变了局部参数的指向

你画了一个图来理解：

```
基本类型传递:
┌─────────┐     复制值     ┌─────────┐
│ x = 10  │────────────────▶│ num = 10│ (函数参数)
└─────────┘                 └─────────┘
修改 num 不影响 x

引用类型传递:
┌─────────┐     复制引用    ┌─────────┐       ┌──────────────┐
│  myObj  │────────────────▶│   obj   │──────▶│ { count: 0 } │ (实际对象)
└─────────┘                 └─────────┘       └──────────────┘
                                ▲
                                └── 都指向同一个对象
修改 obj.count 会影响 myObj.count

重新赋值参数:
┌─────────┐                 ┌─────────┐       ┌──────────────┐
│  myObj  │────────────────▶│   obj   │──────▶│ { count: 0 } │ (原对象)
└─────────┘                 └─────────┘       └──────────────┘
                                │
                                │ obj = { count: 999 }
                                ▼
                            ┌──────────────┐
                            │{ count: 999 }│ (新对象)
                            └──────────────┘
重新赋值只改变 obj 的指向，不影响 myObj
```

## 修复生产代码

下午 1 点 30 分，你终于理解了函数的所有细节。你重新设计了登录函数：

```javascript
// utils/auth.js

// 主函数：处理登录成功
function handleLoginSuccess(username, options = {}) {
    const {
        role = 'user',  // 默认角色
        customMessage = null,  // 自定义消息
        silent = false  // 静默模式
    } = options;

    // 根据角色生成不同消息
    let message;
    if (customMessage) {
        message = customMessage;
    } else if (role === 'admin') {
        message = `管理员 ${username} 登录成功`;
    } else if (role === 'guest') {
        message = `游客 ${username || '未命名'} 登录成功`;
    } else {
        message = `欢迎回来，${username}！登录成功`;
    }

    // 执行登录后的操作
    if (!silent) {
        console.log(message);
        showNotification(message);
    }
    trackEvent('user_login', { username, role, message });
    updateUserStatus(message);

    return { success: true, message };
}

// 便捷函数：管理员登录
const handleAdminLogin = (username) => {
    return handleLoginSuccess(username, { role: 'admin' });
};

// 便捷函数：游客登录
const handleGuestLogin = (username = '游客') => {
    return handleLoginSuccess(username, { role: 'guest' });
};

// 便捷函数：静默登录
const handleSilentLogin = (username) => {
    return handleLoginSuccess(username, { silent: true });
};
```

你开始替换所有 37 处重复代码：

```javascript
// 之前：首页登录（4 行重复）
console.log('登录成功');
showNotification('登录成功');
trackEvent('user_login', '登录成功');
updateUserStatus('登录成功');

// 现在：首页登录（1 行调用）
handleLoginSuccess(currentUser.name);

// 之前：管理员登录（4 行重复 + 特殊逻辑）
const msg = `管理员 ${adminName} 登录成功`;
console.log(msg);
showNotification(msg);
trackEvent('user_login', msg);
updateUserStatus(msg);

// 现在：管理员登录（1 行调用）
handleAdminLogin(adminName);

// 之前：游客登录（4 行重复）
console.log('游客登录成功');
showNotification('游客登录成功');
trackEvent('user_login', '游客登录成功');
updateUserStatus('游客登录成功');

// 现在：游客登录（1 行调用）
handleGuestLogin();

// 之前：后台静默登录（2 行）
trackEvent('user_login', '登录成功');
updateUserStatus('登录成功');

// 现在：静默登录（1 行调用）
handleSilentLogin(currentUser.name);
```

45 分钟后，你完成了所有替换。你运行测试：

```javascript
// 测试用例
console.log('=== 测试普通用户登录 ===');
handleLoginSuccess('Alice');
// 输出: "欢迎回来，Alice！登录成功"

console.log('=== 测试管理员登录 ===');
handleAdminLogin('Bob');
// 输出: "管理员 Bob 登录成功"

console.log('=== 测试游客登录 ===');
handleGuestLogin();
// 输出: "游客 游客 登录成功"

console.log('=== 测试静默登录 ===');
handleSilentLogin('Charlie');
// 没有控制台输出，只记录日志

console.log('=== 测试自定义消息 ===');
handleLoginSuccess('David', {
    customMessage: '特殊活动登录成功！'
});
// 输出: "特殊活动登录成功！"
```

所有测试通过！下午 2 点 15 分，客户提前到了，你信心满满地打开演示环境。产品经理看着演示页面，满意地点头："登录提示很好。对了，能不能把'登录成功'改成'登录完成'？"

你笑了："没问题，只要改一个地方。" 你打开 `utils/auth.js`，把所有 `登录成功` 改成 `登录完成`，刷新页面 —— 37 处全部更新了。

"搞定。" 你说。产品经理惊讶地看着你："这么快？"

"因为我用了函数封装。" 你解释道。如果没有重构，你现在还在手动修改第 20 处...

---

## 技术档案：JavaScript 函数完全指南

**规则 1：函数的三种定义方式与提升行为**

JavaScript 有三种定义函数的方式，它们在提升行为、语法、使用场景上各不相同。

```javascript
// ========== 方式 1: 函数声明 (Function Declaration) ==========

// 特性：整个函数定义会提升到作用域顶部
console.log(greet('Alice'));  // "Hello, Alice" ← 在定义前调用成功

function greet(name) {
    return `Hello, ${name}`;
}

// 提升后的等价代码：
/*
function greet(name) {
    return `Hello, ${name}`;
}
console.log(greet('Alice'));
*/

// ========== 方式 2: 函数表达式 (Function Expression) ==========

// 特性：只提升变量声明，赋值在原位置
console.log(sayHi);  // undefined ← 变量存在但未赋值
console.log(sayHi('Bob'));  // TypeError: sayHi is not a function

const sayHi = function(name) {
    return `Hi, ${name}`;
};

console.log(sayHi('Bob'));  // "Hi, Bob" ← 定义后才能调用

// 提升后的等价代码：
/*
const sayHi;  // 提升了变量声明
console.log(sayHi);  // undefined
sayHi = function(name) { ... };  // 赋值在原位置
*/

// ========== 方式 3: 箭头函数 (Arrow Function) ==========

// 特性：简洁语法，没有自己的 this/arguments/super
const add = (a, b) => a + b;

// 单参数可省略括号
const double = x => x * 2;

// 无参数必须保留括号
const greet = () => console.log('Hello');

// 多行代码需要花括号和 return
const calculate = (a, b) => {
    const sum = a + b;
    return sum * 2;
};

// 返回对象字面量必须加括号
const createUser = name => ({ name: name });  // ✅ 正确
const createUser2 = name => { name: name };   // ❌ 错误：当成代码块

// ========== 三种方式对比 ==========

// 使用场景：
// - 函数声明：需要提升、独立函数定义
// - 函数表达式：赋值给变量、作为参数、需要命名表达式
// - 箭头函数：简洁回调、数组方法、不需要 this 绑定

// 块级作用域陷阱：
if (true) {
    function test1() { return 1; }  // 在块中可能有兼容性问题
}

if (true) {
    const test2 = function() { return 2; };  // ✅ 推荐：行为一致
}
```

**规则 2：参数机制 —— 默认值、剩余参数、解构**

函数参数支持默认值、剩余参数、解构赋值等高级特性，参数不足时为 undefined，多余参数被忽略。

```javascript
// ========== 基本参数行为 ==========

function test(a, b, c) {
    console.log('a:', a, 'b:', b, 'c:', c);
}

test(1, 2, 3);  // a: 1 b: 2 c: 3 (正常)
test(1, 2);     // a: 1 b: 2 c: undefined (少了是 undefined)
test(1, 2, 3, 4, 5);  // a: 1 b: 2 c: 3 (多了被忽略)

// ========== 默认参数 (Default Parameters) ==========

function greet(name = '游客', greeting = 'Hello') {
    return `${greeting}, ${name}!`;
}

greet();  // "Hello, 游客!"
greet('Alice');  // "Hello, Alice!"
greet('Bob', 'Hi');  // "Hi, Bob!"
greet(undefined, 'Hey');  // "Hey, 游客!" ← 传 undefined 使用默认值

// 默认参数可以引用之前的参数
function createUser(name, role = 'user', id = `${role}_${Date.now()}`) {
    return { name, role, id };
}

console.log(createUser('Alice'));
// { name: 'Alice', role: 'user', id: 'user_1234567890' }

// ========== 剩余参数 (Rest Parameters) ==========

function sum(...numbers) {
    console.log('numbers:', numbers);  // 是一个数组
    console.log('是数组吗？', Array.isArray(numbers));  // true

    return numbers.reduce((total, num) => total + num, 0);
}

console.log(sum(1, 2, 3));  // numbers: [1, 2, 3], 返回: 6
console.log(sum(1, 2, 3, 4, 5));  // numbers: [1, 2, 3, 4, 5], 返回: 15
console.log(sum());  // numbers: [], 返回: 0

// 剩余参数必须是最后一个参数
function format(prefix, ...items) {
    return items.map(item => `${prefix}: ${item}`);
}

console.log(format('Item', 'A', 'B', 'C'));
// ["Item: A", "Item: B", "Item: C"]

// ========== 解构参数 (Destructuring Parameters) ==========

// 对象解构参数
function greetUser({ name, age = 18, role = 'user' } = {}) {
    console.log(`${name} (${age}岁) - ${role}`);
}

greetUser({ name: 'Alice', age: 25 });  // "Alice (25岁) - user"
greetUser({ name: 'Bob' });  // "Bob (18岁) - user"
greetUser({});  // "undefined (18岁) - user"
greetUser();  // "undefined (18岁) - user" (默认值 {})

// 数组解构参数
function sum([a, b, c = 0]) {
    return a + b + c;
}

console.log(sum([1, 2, 3]));  // 6
console.log(sum([1, 2]));  // 3 (c 使用默认值 0)

// ========== arguments 对象 (传统方式) ==========

function oldStyleSum() {
    console.log('arguments:', arguments);  // 类数组对象
    console.log('是数组吗？', Array.isArray(arguments));  // false

    let total = 0;
    for (let i = 0; i < arguments.length; i++) {
        total += arguments[i];
    }
    return total;
}

console.log(oldStyleSum(1, 2, 3, 4));  // 10

// 箭头函数没有 arguments
const arrowSum = () => {
    console.log(arguments);  // ReferenceError: arguments is not defined
};
```

**规则 3：return 语句与自动分号插入陷阱**

return 语句返回值并立即退出函数，没有 return 或空 return 返回 undefined。return 后换行会自动插入分号。

```javascript
// ========== return 基本行为 ==========

function add(a, b) {
    return a + b;
    console.log('永远不会执行');  // ← return 后的代码不执行
}

console.log(add(1, 2));  // 3

// ========== 没有 return ==========

function noReturn() {
    console.log('执行了');
}

const result = noReturn();  // "执行了"
console.log(result);  // undefined

// ========== 空 return ==========

function emptyReturn() {
    console.log('执行了');
    return;  // 空 return
    console.log('不会执行');
}

console.log(emptyReturn());  // undefined

// ========== 提前 return (Guard Clauses) ==========

function checkAge(age) {
    if (age < 0) {
        return '无效年龄';  // 提前返回
    }

    if (age < 18) {
        return '未成年';
    }

    if (age < 60) {
        return '成年';
    }

    return '老年';
}

console.log(checkAge(-1));  // "无效年龄"
console.log(checkAge(15));  // "未成年"
console.log(checkAge(30));  // "成年"
console.log(checkAge(70));  // "老年"

// ========== 自动分号插入陷阱 (ASI) ==========

function createUser1() {
    return  // ← 这里自动插入分号！
    {
        name: 'Alice',
        age: 25
    };
}
console.log(createUser1());  // undefined ← 返回 undefined

function createUser2() {
    return {  // ✅ 正确：花括号和 return 在同一行
        name: 'Alice',
        age: 25
    };
}
console.log(createUser2());  // { name: 'Alice', age: 25 }

// 箭头函数返回对象也有类似陷阱
const createUser3 = () => {  // ❌ 花括号被当成函数体
    name: 'Alice'
};
console.log(createUser3());  // undefined

const createUser4 = () => ({  // ✅ 正确：用括号包裹对象
    name: 'Alice'
});
console.log(createUser4());  // { name: 'Alice' }

// ========== 多个 return ==========

function findFirst(arr, condition) {
    for (let item of arr) {
        if (condition(item)) {
            return item;  // 找到就立即返回
        }
    }
    return null;  // 没找到返回 null
}

const numbers = [1, 2, 3, 4, 5];
console.log(findFirst(numbers, x => x > 3));  // 4
console.log(findFirst(numbers, x => x > 10));  // null
```

**规则 4：函数作为一等公民 —— 高阶函数与闭包入门**

函数是一等公民，可以赋值给变量、作为参数传递、作为返回值、存储在数据结构中。

```javascript
// ========== 函数赋值给变量 ==========

const greet = function(name) {
    return `Hello, ${name}!`;
};

console.log(greet('Alice'));  // "Hello, Alice!"
console.log(typeof greet);  // "function"

// ========== 函数作为参数传递 (回调函数) ==========

function execute(callback) {
    console.log('准备执行回调...');
    const result = callback();
    console.log('回调执行完毕');
    return result;
}

execute(function() {
    console.log('我是回调函数');
    return 42;
});
// 输出：
// "准备执行回调..."
// "我是回调函数"
// "回调执行完毕"

// 实际应用：数组方法
const numbers = [1, 2, 3, 4, 5];

const doubled = numbers.map(function(x) {
    return x * 2;
});
console.log(doubled);  // [2, 4, 6, 8, 10]

const evens = numbers.filter(function(x) {
    return x % 2 === 0;
});
console.log(evens);  // [2, 4]

// ========== 函数作为返回值 (函数工厂) ==========

function createMultiplier(factor) {
    return function(num) {
        return num * factor;
    };
}

const double = createMultiplier(2);
const triple = createMultiplier(3);

console.log(double(5));  // 10
console.log(triple(5));  // 15
console.log(double(10));  // 20
console.log(triple(10));  // 30

// createMultiplier 每次调用返回一个新函数
// 返回的函数 "记住" 了 factor 的值 (闭包)

// ========== 函数存储在数据结构中 ==========

// 数组中的函数
const operations = [
    x => x + 1,
    x => x * 2,
    x => x - 3,
    x => x / 4
];

let value = 10;
for (let operation of operations) {
    value = operation(value);
}
console.log(value);  // 4.75 ((((10 + 1) * 2) - 3) / 4)

// 对象中的函数 (方法)
const calculator = {
    value: 0,

    add(num) {
        this.value += num;
        return this;  // 返回 this 支持链式调用
    },

    subtract(num) {
        this.value -= num;
        return this;
    },

    multiply(num) {
        this.value *= num;
        return this;
    },

    getResult() {
        return this.value;
    }
};

calculator.add(10).subtract(3).multiply(2);
console.log(calculator.getResult());  // 14

// ========== 高阶函数 (Higher-Order Functions) ==========

// 高阶函数：接受函数作为参数或返回函数的函数

// 示例 1: 函数组合
function compose(f, g) {
    return function(x) {
        return f(g(x));
    };
}

const addOne = x => x + 1;
const double = x => x * 2;

const addOneThenDouble = compose(double, addOne);
console.log(addOneThenDouble(5));  // 12 ((5 + 1) * 2)

// 示例 2: 偏函数应用
function partial(fn, ...fixedArgs) {
    return function(...remainingArgs) {
        return fn(...fixedArgs, ...remainingArgs);
    };
}

function greet(greeting, name) {
    return `${greeting}, ${name}!`;
}

const sayHello = partial(greet, 'Hello');
console.log(sayHello('Alice'));  // "Hello, Alice!"
console.log(sayHello('Bob'));  // "Hello, Bob!"

// ========== 闭包入门 ==========

function createCounter() {
    let count = 0;  // 私有变量

    return {
        increment() {
            count++;
            return count;
        },
        decrement() {
            count--;
            return count;
        },
        getCount() {
            return count;
        }
    };
}

const counter = createCounter();
console.log(counter.increment());  // 1
console.log(counter.increment());  // 2
console.log(counter.decrement());  // 1
console.log(counter.getCount());  // 1
console.log(counter.count);  // undefined (无法直接访问)
```

**规则 5：参数传递机制 —— 值传递的本质**

JavaScript 所有参数都是值传递。基本类型传值副本，引用类型传引用副本（引用的值）。

```javascript
// ========== 基本类型参数传递 ==========

function changeNumber(num) {
    console.log('函数内修改前:', num);  // 10
    num = 100;  // 修改的是副本
    console.log('函数内修改后:', num);  // 100
}

let x = 10;
changeNumber(x);
console.log('函数外的 x:', x);  // 10 ← x 没有变化

// 原理：传递的是 x 的值的副本
/*
内存模型:
┌─────────┐     复制值     ┌─────────┐
│ x = 10  │────────────────▶│ num = 10│
└─────────┘                 └─────────┘
修改 num 不影响 x
*/

// ========== 引用类型参数传递 (关键) ==========

function changeObject(obj) {
    console.log('函数内修改前:', obj);  // { count: 0 }
    obj.count = 100;  // 通过引用修改对象
    console.log('函数内修改后:', obj);  // { count: 100 }
}

let myObj = { count: 0 };
changeObject(myObj);
console.log('函数外的 myObj:', myObj);  // { count: 100 } ← myObj 被修改了

// 原理：传递的是引用的副本，但副本指向同一个对象
/*
内存模型:
┌─────────┐     复制引用    ┌─────────┐       ┌──────────────┐
│  myObj  │────────────────▶│   obj   │──────▶│ { count: 0 } │
└─────────┘                 └─────────┘       └──────────────┘
                                ▲
                                └── 都指向同一个对象
修改 obj.count 实际上修改的是同一个对象
*/

// ========== 重新赋值参数 (陷阱) ==========

function replaceObject(obj) {
    console.log('函数内修改前:', obj);  // { count: 0 }
    obj = { count: 999 };  // 重新赋值参数
    console.log('函数内修改后:', obj);  // { count: 999 }
}

let myObj2 = { count: 0 };
replaceObject(myObj2);
console.log('函数外的 myObj2:', myObj2);  // { count: 0 } ← myObj2 没有变化

// 原理：重新赋值只改变局部参数的指向，不影响原变量
/*
内存模型:
┌─────────┐                 ┌─────────┐       ┌──────────────┐
│ myObj2  │────────────────▶│   obj   │──────▶│ { count: 0 } │ (原对象)
└─────────┘                 └─────────┘       └──────────────┘
                                │
                                │ obj = { count: 999 }
                                ▼
                            ┌──────────────┐
                            │{ count: 999 }│ (新对象)
                            └──────────────┘
重新赋值只改变 obj 的指向，myObj2 仍指向原对象
*/

// ========== 数组参数传递 ==========

function modifyArray(arr) {
    arr.push(4);  // 修改数组内容
    console.log('函数内:', arr);  // [1, 2, 3, 4]
}

let myArr = [1, 2, 3];
modifyArray(myArr);
console.log('函数外:', myArr);  // [1, 2, 3, 4] ← 数组被修改了

function replaceArray(arr) {
    arr = [10, 20, 30];  // 重新赋值
    console.log('函数内:', arr);  // [10, 20, 30]
}

let myArr2 = [1, 2, 3];
replaceArray(myArr2);
console.log('函数外:', myArr2);  // [1, 2, 3] ← 数组没有变化

// ========== 如何避免修改原对象 ==========

// 方法 1: 在函数内创建副本
function safeModify(obj) {
    const copy = { ...obj };  // 浅拷贝
    copy.count = 100;
    return copy;
}

let original = { count: 0 };
let modified = safeModify(original);
console.log(original);  // { count: 0 } ← 原对象未变
console.log(modified);  // { count: 100 } ← 新对象

// 方法 2: 使用 Object.freeze 防止修改
const frozen = Object.freeze({ count: 0 });

function tryModify(obj) {
    obj.count = 100;  // 严格模式下报错，非严格模式静默失败
}

tryModify(frozen);
console.log(frozen);  // { count: 0 } ← 未被修改

// 方法 3: 在调用时传递副本
function unsafeModify(obj) {
    obj.count = 100;
}

let data = { count: 0 };
unsafeModify({ ...data });  // 传递副本
console.log(data);  // { count: 0 } ← 原对象未变
```

**规则 6：箭头函数的特殊性 —— this、arguments、new**

箭头函数没有自己的 this、arguments、super、new.target，不能用作构造函数。

```javascript
// ========== 箭头函数没有 this ==========

const obj = {
    value: 42,

    // 普通函数：有自己的 this
    regularMethod: function() {
        console.log('regularMethod this:', this);  // obj
        console.log('value:', this.value);  // 42
    },

    // 箭头函数：没有自己的 this，继承外层作用域的 this
    arrowMethod: () => {
        console.log('arrowMethod this:', this);  // window (浏览器) 或 undefined (严格模式)
        console.log('value:', this.value);  // undefined
    }
};

obj.regularMethod();  // 正常工作
obj.arrowMethod();  // this 不是 obj

// ========== 箭头函数在回调中的优势 ==========

function Timer() {
    this.seconds = 0;

    // 使用普通函数 (有问题)
    setInterval(function() {
        this.seconds++;  // this 不是 Timer 实例
        console.log(this.seconds);  // NaN (this.seconds 是 undefined)
    }, 1000);
}

// 解决方案 1: 使用箭头函数
function Timer() {
    this.seconds = 0;

    setInterval(() => {
        this.seconds++;  // this 继承自 Timer，指向实例
        console.log(this.seconds);  // 1, 2, 3...
    }, 1000);
}

// 解决方案 2: 保存 this (传统方式)
function Timer() {
    this.seconds = 0;
    const self = this;  // 保存 this

    setInterval(function() {
        self.seconds++;
        console.log(self.seconds);
    }, 1000);
}

// ========== 箭头函数没有 arguments ==========

function regularFunction() {
    console.log('arguments:', arguments);  // Arguments [1, 2, 3]
    console.log('是数组吗？', Array.isArray(arguments));  // false
}
regularFunction(1, 2, 3);

const arrowFunction = () => {
    console.log('arguments:', arguments);  // ReferenceError: arguments is not defined
};
arrowFunction(1, 2, 3);

// 箭头函数使用剩余参数代替 arguments
const arrowWithRest = (...args) => {
    console.log('args:', args);  // [1, 2, 3]
    console.log('是数组吗？', Array.isArray(args));  // true
};
arrowWithRest(1, 2, 3);

// ========== 箭头函数不能用 new ==========

const ArrowConstructor = () => {
    this.value = 42;
};

try {
    const instance = new ArrowConstructor();  // TypeError
} catch (e) {
    console.log(e.message);  // "ArrowConstructor is not a constructor"
}

// 普通函数可以用 new
function RegularConstructor() {
    this.value = 42;
}
const instance = new RegularConstructor();
console.log(instance.value);  // 42

// ========== 箭头函数使用场景 ==========

// ✅ 推荐：数组方法回调
const numbers = [1, 2, 3, 4, 5];
const doubled = numbers.map(x => x * 2);
const evens = numbers.filter(x => x % 2 === 0);

// ✅ 推荐：简短的工具函数
const add = (a, b) => a + b;
const isEven = x => x % 2 === 0;

// ✅ 推荐：需要继承外层 this 的回调
setTimeout(() => {
    console.log('this 继承自外层');
}, 1000);

// ❌ 不推荐：对象方法 (需要访问 this)
const obj = {
    value: 42,
    getValue: () => this.value  // ❌ this 不是 obj
};

// ❌ 不推荐：事件处理器 (this 通常需要指向元素)
button.addEventListener('click', () => {
    console.log(this);  // ❌ 不是 button 元素
});

// ❌ 不推荐：原型方法
MyClass.prototype.method = () => {
    console.log(this);  // ❌ 不是实例
};
```

**规则 7：函数命名与调试最佳实践**

函数命名影响代码可读性、调试体验、堆栈追踪质量。使用命名函数表达式、避免匿名函数。

```javascript
// ========== 匿名函数 vs 命名函数 ==========

// 匿名函数 (不推荐)
const add1 = function(a, b) {
    return a + b;
};

// 命名函数表达式 (推荐)
const add2 = function add(a, b) {
    return a + b;
};

// 调试时的区别：
console.log(add1);  // [Function: add1]
console.log(add2);  // [Function: add]

// 堆栈追踪中的区别：
function testError1() {
    const fn = function() {
        throw new Error('Error');
    };
    fn();
}

function testError2() {
    const fn = function namedFn() {
        throw new Error('Error');
    };
    fn();
}

try {
    testError1();
} catch (e) {
    console.log(e.stack);
    // at fn (...)  ← 匿名函数，名字来自变量
}

try {
    testError2();
} catch (e) {
    console.log(e.stack);
    // at namedFn (...)  ← 命名函数，名字更清晰
}

// ========== 命名函数表达式的递归 ==========

const factorial = function fact(n) {
    if (n <= 1) return 1;
    return n * fact(n - 1);  // 函数内可以使用名字 fact
};

console.log(factorial(5));  // 120
console.log(fact);  // ReferenceError: fact is not defined (外部不可见)

// ========== 函数命名约定 ==========

// ✅ 动词开头，描述动作
function calculateTotal(items) { ... }
function getUserById(id) { ... }
function isValid(value) { ... }
function hasPermission(user, action) { ... }

// ✅ 布尔返回值：is/has/can 开头
function isLoggedIn() { return true; }
function hasAccess() { return false; }
function canEdit() { return true; }

// ✅ 获取数据：get 开头
function getUser() { ... }
function getConfig() { ... }

// ✅ 设置数据：set 开头
function setTheme(theme) { ... }
function setLanguage(lang) { ... }

// ✅ 处理事件：handle/on 开头
function handleClick(event) { ... }
function onSubmit(data) { ... }

// ❌ 避免：单字母、缩写、不明确的名字
function f(x) { ... }  // 太简短
function calc(a, b) { ... }  // 缩写不清晰
function doStuff() { ... }  // 不明确

// ========== 调试辅助技巧 ==========

// 技巧 1: console.log 函数名
function debuggableFunction() {
    console.log('debuggableFunction 被调用');
    // 函数逻辑
}

// 技巧 2: 使用 console.trace 追踪调用栈
function deepFunction() {
    console.trace('调用栈追踪');
}

function middleFunction() {
    deepFunction();
}

function topFunction() {
    middleFunction();
}

topFunction();
// 输出完整调用栈: topFunction → middleFunction → deepFunction

// 技巧 3: 使用 debugger 断点
function complexFunction(data) {
    debugger;  // 在此处暂停，可在 DevTools 中检查
    const result = process(data);
    return result;
}

// 技巧 4: 函数性能测量
function measurePerformance(fn, ...args) {
    const start = performance.now();
    const result = fn(...args);
    const end = performance.now();
    console.log(`${fn.name} 执行时间: ${end - start}ms`);
    return result;
}

function slowFunction() {
    let sum = 0;
    for (let i = 0; i < 1000000; i++) {
        sum += i;
    }
    return sum;
}

measurePerformance(slowFunction);  // "slowFunction 执行时间: 5.234ms"
```

**规则 8：函数设计原则 —— 单一职责、纯函数、副作用**

遵循单一职责原则、优先使用纯函数、明确标识和隔离副作用。

```javascript
// ========== 单一职责原则 (SRP) ==========

// ❌ 违反 SRP：一个函数做太多事
function processUserBad(user) {
    // 验证用户
    if (!user.email) throw new Error('缺少邮箱');

    // 格式化数据
    user.name = user.name.trim();
    user.email = user.email.toLowerCase();

    // 保存数据库
    db.save(user);

    // 发送邮件
    sendEmail(user.email, '欢迎');

    // 记录日志
    log('用户已创建');
}

// ✅ 遵循 SRP：每个函数只做一件事
function validateUser(user) {
    if (!user.email) throw new Error('缺少邮箱');
    if (!user.name) throw new Error('缺少姓名');
}

function normalizeUser(user) {
    return {
        ...user,
        name: user.name.trim(),
        email: user.email.toLowerCase()
    };
}

function saveUser(user) {
    return db.save(user);
}

function notifyUser(user) {
    return sendEmail(user.email, '欢迎');
}

function processUserGood(user) {
    validateUser(user);
    const normalized = normalizeUser(user);
    const saved = saveUser(normalized);
    notifyUser(saved);
    log('用户已创建');
    return saved;
}

// ========== 纯函数 (Pure Functions) ==========

// 纯函数：相同输入总是返回相同输出，没有副作用

// ✅ 纯函数示例
function add(a, b) {
    return a + b;  // 只依赖参数，没有副作用
}

function double(x) {
    return x * 2;  // 可预测，可测试
}

function filter(array, predicate) {
    const result = [];
    for (let item of array) {
        if (predicate(item)) {
            result.push(item);
        }
    }
    return result;  // 不修改原数组，返回新数组
}

// ❌ 非纯函数示例
let count = 0;
function increment() {
    count++;  // 副作用：修改外部状态
    return count;
}

function getCurrentTime() {
    return new Date();  // 非确定性：每次返回不同值
}

function push(array, item) {
    array.push(item);  // 副作用：修改参数
    return array;
}

// ========== 副作用 (Side Effects) ==========

// 副作用：修改外部状态、I/O 操作、网络请求、DOM 操作等

// 策略 1: 隔离副作用
function calculateTotal(items) {
    // 纯函数部分：计算
    return items.reduce((sum, item) => sum + item.price, 0);
}

function displayTotal(items) {
    // 副作用部分：DOM 操作
    const total = calculateTotal(items);
    document.getElementById('total').textContent = total;
}

// 策略 2: 明确标识副作用
function getUserPure(id) {
    // 纯函数：返回获取用户的配置
    return {
        method: 'GET',
        url: `/api/users/${id}`
    };
}

async function getUserWithEffect(id) {
    // 有副作用：实际执行网络请求
    const config = getUserPure(id);
    return await fetch(config.url);
}

// 策略 3: 使用函数式方法避免副作用
const numbers = [1, 2, 3, 4, 5];

// ❌ 有副作用：修改原数组
function doubleArrayBad(arr) {
    for (let i = 0; i < arr.length; i++) {
        arr[i] *= 2;
    }
    return arr;
}

// ✅ 无副作用：返回新数组
function doubleArrayGood(arr) {
    return arr.map(x => x * 2);
}

console.log(doubleArrayGood(numbers));  // [2, 4, 6, 8, 10]
console.log(numbers);  // [1, 2, 3, 4, 5] (原数组未变)

// ========== 实际应用：重构有副作用的代码 ==========

// 之前：副作用多，难以测试
let totalPrice = 0;
function addToCart(item) {
    totalPrice += item.price;  // 副作用 1
    updateCartUI();  // 副作用 2
    saveToLocalStorage();  // 副作用 3
}

// 之后：分离纯函数和副作用
function calculateNewTotal(currentTotal, item) {
    return currentTotal + item.price;  // 纯函数
}

function addToCartRefactored(item, currentTotal) {
    // 纯函数部分
    const newTotal = calculateNewTotal(currentTotal, item);

    // 副作用集中处理
    performSideEffects(newTotal);

    return newTotal;
}

function performSideEffects(total) {
    updateCartUI(total);
    saveToLocalStorage(total);
}
```

---

**记录者注**:

JavaScript 的函数系统是代码复用的核心机制。函数有三种定义方式——函数声明（提升整个定义）、函数表达式（只提升变量）、箭头函数（简洁语法无 this）。参数机制支持默认值、剩余参数、解构，参数不足时为 undefined，多余参数被忽略。return 语句返回值并退出，return 后换行会自动插入分号导致返回 undefined。

关键在于理解函数作为一等公民的特性——可赋值、可传参、可返回、可存储。参数传递是值传递，基本类型传值副本（修改不影响原变量），引用类型传引用副本（通过引用修改对象会影响原对象，但重新赋值参数不影响原变量）。箭头函数没有自己的 this/arguments/new.target，不能用作构造函数，适合简短回调和需要继承外层 this 的场景，但不适合对象方法和事件处理器。

函数设计应遵循单一职责原则、优先使用纯函数、明确标识和隔离副作用。纯函数相同输入总是返回相同输出且无副作用，可预测、可测试、可复用。副作用包括修改外部状态、I/O 操作、网络请求、DOM 操作，应隔离在单独的函数中。命名函数表达式优于匿名函数，提供更好的堆栈追踪和调试体验。

记住：**函数有三种定义方式（声明/表达式/箭头），提升行为不同；参数支持默认值/剩余参数/解构；return 后换行自动插入分号；参数传递是值传递（基本类型传值副本，引用类型传引用副本）；箭头函数无 this/arguments/new；函数是一等公民可赋值/传参/返回；遵循单一职责、纯函数、副作用隔离原则；使用命名函数表达式提升调试体验**。理解函数机制，就理解了 JavaScript 如何封装逻辑、消除重复、构建可复用的代码模块。

---

**事故档案编号**: JS-2024-1642
**影响范围**: 代码复用、可维护性、开发效率、生产力
**根本原因**: 不理解函数封装机制和参数处理导致大量重复代码，不理解提升行为和参数传递机制导致 bug，不理解箭头函数特性导致 this 问题
**修复成本**: 中等（需要重构现有代码，学习函数最佳实践，理解纯函数和副作用隔离）
**预防措施**: 遵循 DRY 原则（Don't Repeat Yourself），识别重复代码及时提取函数，使用命名函数表达式，优先纯函数设计，隔离副作用，代码审查关注函数设计质量

这是 JavaScript 世界第 42 次被记录的函数封装事故。函数是代码复用的基本单元——三种定义方式（函数声明提升整个定义，函数表达式只提升变量，箭头函数简洁无 this），参数机制支持默认值/剩余参数/解构，参数不足是 undefined 多余被忽略，return 返回值并退出（后换行自动插入分号陷阱），参数传递是值传递（基本类型传值副本，引用类型传引用副本但重新赋值不影响原变量），箭头函数无 this/arguments/new 不能作构造函数，函数是一等公民可赋值传参返回存储，遵循单一职责纯函数副作用隔离原则。理解函数基础和最佳实践，就理解了 JavaScript 如何封装逻辑消除重复构建可维护代码。

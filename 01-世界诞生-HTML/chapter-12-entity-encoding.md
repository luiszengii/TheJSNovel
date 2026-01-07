《第12次记录:字符编码陷阱 —— 实体的双重世界》

---

## 事故现场

周二晚上八点,你刚吃完晚饭准备下班,手机突然响了。是公司安全部门的号码。

"你负责的博客系统出现安全漏洞。"对方的声音很严肃,"有用户报告看到了不应该出现的弹窗。我们检测到XSS攻击特征,立刻停止服务,马上回公司处理。"

你的心跳突然加速。XSS攻击——跨站脚本攻击,最常见也最危险的Web安全漏洞之一。这意味着攻击者可以在用户浏览器中执行任意JavaScript代码,窃取cookie、劫持会话、钓鱼欺诈...

你快速打开电脑,远程登录服务器。窗外已经完全黑了,只有街灯在雨夜中投下昏黄的光。

你打开用户提交的文章内容,看到数据库里赫然写着:

```html
文章标题:<script>alert('XSS攻击成功')</script>
```

"糟了。"你喃喃自语。当这段内容被直接插入到页面时,`<script>`标签会被浏览器执行。你想起三天前上线这个功能时,产品经理催得很紧,你为了赶进度跳过了输入验证。

你快速检查显示代码:

```javascript
document.getElementById('article').innerHTML = articleContent;
```

直接用`innerHTML`插入用户输入——这是最基本的安全错误。

九点,技术总监打来电话:"安全部门说有十几个用户反馈异常。这个漏洞影响范围有多大?需要多久修复?"

"我在排查,"你的声音有些发抖,"最快也要一个小时。"

"抓紧时间,这是P0级安全事故。"电话挂断了。

你盯着屏幕,手心开始冒汗。你需要转义这些特殊字符,但具体怎么转义?`<`和`>`要转成什么?

你试着写了个简单的转义函数:

```javascript
function escapeHTML(str) {
    return str.replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
```

刷新测试页面,显示变成了:`&lt;script&gt;alert('XSS攻击成功')&lt;/script&gt;`

"为什么显示的是`&lt;`而不是`<`?"你困惑了。明明想让它显示尖括号,现在却显示了奇怪的符号。

晚上九点半,你盯着这些`&lt;`、`&gt;`、`&amp;`——它们到底是什么?为什么浏览器有时把它们当成字符,有时又当成符号?

---

## 深入迷雾

你决定从最基础的概念开始理解。你创建了一个测试页面:

```html
<div id="test1"><</div>
<div id="test2">&lt;</div>
```

浏览器报错——test1无法解析,但test2正常显示了`<`符号。

你用JavaScript验证:

```javascript
console.log(document.getElementById('test2').textContent);  // "<"
console.log(document.getElementById('test2').innerHTML);    // "&lt;"
```

"`textContent`显示的是`<`,但`innerHTML`里存的是`&lt;`?"你突然有些明白了,"所以`&lt;`是HTML源码里的写法,浏览器渲染时会把它变成`<`符号?"

晚上十点,你测试了更多字符:

```javascript
// 五个必须转义的字符
console.log('<'.charCodeAt(0));   // 60
console.log('&lt;'.length);       // 4
console.log('&'.length);          // 1
```

"`&lt;`在HTML源码里是4个字符,但渲染后是1个符号。"你记下笔记。

安全部门发来消息:"你们还有一个表单也可能受影响,用户可以输入个人简介。赶紧检查。"

你的压力更大了。你快速测试了未转义的危险:

```javascript
// 用户输入恶意代码
const userInput = '<img src=x onerror="alert(document.cookie)">';
element.innerHTML = userInput;  // 执行了!cookie被窃取
```

"所有用户输入都必须转义。"你开始意识到问题的严重性。

你试着用`textContent`代替`innerHTML`:

```javascript
element.textContent = '<script>alert(1)</script>';
console.log(element.innerHTML);  // "&lt;script&gt;alert(1)&lt;/script&gt;"
```

"`textContent`会自动转义!"你发现了一个重要特性,"它把我输入的尖括号自动转成了`&lt;`和`&gt;`。"

晚上十点半,技术总监又发来消息:"进展如何?"

你回复:"找到问题了,正在修复。"

你试着写一个完整的转义函数,但遇到了新问题——如果用户输入的本身就包含`&lt;`怎么办?

```javascript
// 用户输入:"&lt;script&gt;"
const input = '&lt;script&gt;';

// 如果只转义< >
input.replace(/</g, '&lt;').replace(/>/g, '&gt;');  // 保持不变

// 然后用innerHTML插入
element.innerHTML = input;  // 被反转义回<script>,代码执行!
```

"必须先转义`&`符号!"你终于明白了转义顺序的重要性。

---

## 真相浮现

你重写了转义函数,这次按正确的顺序:

```javascript
// ❌ 错误:只转义< >,忘记&
function badEscape(text) {
    return text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ✅ 正确:& 必须第一个转义
function escapeHTML(text) {
    return text
        .replace(/&/g, '&amp;')   // 第一个!
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;');
}
```

你测试了所有用户提交的内容——全部成功转义,没有代码被执行。

你还发现了更简单的方法:

```javascript
// 利用textContent自动转义
function escapeHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 测试
const dangerous = '<script>alert("XSS")</script>';
const safe = escapeHTML(dangerous);
console.log(safe);  // "&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;"
```

你修改了所有用户内容显示的代码:

```javascript
// ✅ 方案1:使用textContent(推荐)
element.textContent = userInput;

// ✅ 方案2:手动转义后使用innerHTML
element.innerHTML = escapeHTML(userInput);
```

晚上十一点,你部署了修复代码,运行了安全扫描——没有发现XSS漏洞。

你给技术总监发了条消息:"已修复,正在测试。"

几分钟后,总监回复:"安全部门确认修复有效,明天早会需要你写一份事故报告。"

你靠在椅子上,长长地呼出一口气。窗外的雨还在下,但你的心终于放下了。

---

## 世界法则

**世界规则 1: 五个必须转义的字符**

| 字符 | 实体 | 原因 |
|-----|------|------|
| `<` | `&lt;` | 标签开始 |
| `>` | `&gt;` | 标签结束 |
| `&` | `&amp;` | 实体开始 |
| `"` | `&quot;` | 属性引号 |
| `'` | `&#x27;` | 属性引号 |

```javascript
function escapeHTML(text) {
    return text
        .replace(/&/g, '&amp;')   // 必须第一个
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;');
}
```

**世界规则 2: 实体的两种形式**

```html
<!-- 命名实体 -->
&lt;   <!-- < -->
&gt;   <!-- > -->
&nbsp; <!-- 不换行空格 -->
&copy; <!-- © -->

<!-- 数字实体 -->
&#60;   <!-- <,十进制 -->
&#x3C;  <!-- <,十六进制 -->
&#169;  <!-- ©,十进制 -->
```

**等价关系**: `&lt;` === `&#60;` === `&#x3C;` (都显示为`<`)

**世界规则 3: 转义顺序很重要**

```javascript
// ❌ 错误:先转义< >,后转义&
function wrong(text) {
    return text
        .replace(/</g, '&lt;')   // 产生&lt;
        .replace(/&/g, '&amp;'); // 把&lt;变成&amp;lt;
}

// ✅ 正确:& 必须第一个
function correct(text) {
    return text
        .replace(/&/g, '&amp;')  // 第一个
        .replace(/</g, '&lt;');
}
```

**世界规则 4: textContent自动转义**

```javascript
const element = document.getElementById('content');

// textContent:自动转义,安全
element.textContent = '<script>alert(1)</script>';
// 页面显示:<script>alert(1)</script>
// 不执行代码

// innerHTML:不转义,危险
element.innerHTML = '<script>alert(1)</script>';
// 执行代码 ❌
```

**最佳实践**:
```javascript
// ✅ 显示用户输入:用textContent
element.textContent = userInput;

// ✅ 插入可信HTML:用innerHTML + 转义
element.innerHTML = escapeHTML(userInput);

// ❌ 永远不要
element.innerHTML = userInput;  // 危险!
```

**世界规则 5: 特殊实体**

```html
<!-- 不换行空格 -->
<p>A&nbsp;&nbsp;&nbsp;B</p>  <!-- A   B -->

<!-- 普通空格会折叠 -->
<p>A     B</p>  <!-- A B -->

<!-- 版权和符号 -->
&copy; 2024  <!-- © 2024 -->
&reg;        <!-- ® -->
&trade;      <!-- ™ -->
```

**世界规则 6: 防御XSS攻击**

```javascript
// 攻击示例
const userInput = '<img src=x onerror="alert(document.cookie)">';
element.innerHTML = userInput;  // cookie被窃取!

// 防御方案1:textContent
element.textContent = userInput;  // 安全

// 防御方案2:手动转义
element.innerHTML = escapeHTML(userInput);  // 安全

// 防御方案3:DOMPurify库(推荐)
element.innerHTML = DOMPurify.sanitize(userInput);
```

**完整安全示例**:
```javascript
class SafeDisplay {
    static escape(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    static show(element, userInput) {
        // 方案1:纯文本
        element.textContent = userInput;

        // 方案2:允许部分HTML
        element.innerHTML = this.escape(userInput);
    }
}

// 使用
const dangerous = '<script>alert("XSS")</script>';
SafeDisplay.show(element, dangerous);  // 安全显示
```

---

**事故档案编号**: DOM-2024-0812
**影响范围**: 用户输入处理、XSS防御、内容显示
**根本原因**: 未转义HTML特殊字符,导致恶意代码执行
**修复成本**: 中等(审查所有用户输入点,添加转义)

这是DOM世界第12次被记录的字符编码陷阱。特殊字符生活在双重世界中——在源码里它们是实体(`&lt;`),在渲染后它们是符号(`<`)。混淆这两个世界,安全的边界就会被撕裂,恶意代码就会趁虚而入。
